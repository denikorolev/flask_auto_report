# app/utils/ocr_processing.py
import time
import requests
from typing import Tuple
from flask import current_app
import io
from PIL import Image, ImageOps
from app.utils.logger import logger

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    logger.info("HEIC/HEIF support enabled (pillow-heif).")
except Exception as e:
    logger.warning(f"HEIC/HEIF support not enabled (pillow-heif missing?): {e}")

class OcrProvider:
    def extract_text(self, *, content: bytes, filename: str) -> Tuple[str, str]:
        """Return (text, method)."""
        raise NotImplementedError


class AzureReadProvider(OcrProvider):
    """
    Azure Computer Vision Read (v3.2). Бинарный POST + poll по Operation-Location.
    """
    def __init__(self, endpoint: str, key: str, timeout: int = 60):
        self.endpoint = endpoint.rstrip("/")
        self.key = key
        self.timeout = timeout

    def extract_text(self, *, content: bytes, filename: str) -> Tuple[str, str]:
        url = f"{self.endpoint}/vision/v3.2/read/analyze"
        headers = {"Ocp-Apim-Subscription-Key": self.key, "Content-Type": "application/octet-stream"}

        resp = requests.post(url, headers=headers, data=content, timeout=30)
        resp.raise_for_status()

        op_loc = resp.headers.get("Operation-Location")
        if not op_loc:
            raise RuntimeError("Azure Read: Operation-Location header missing")

        # Poll
        t0 = time.time()
        while True:
            r = requests.get(op_loc, headers={"Ocp-Apim-Subscription-Key": self.key}, timeout=15)
            r.raise_for_status()
            data = r.json()
            status = (data.get("status") or "").lower()
            if status in ("succeeded", "failed"):
                if status == "failed":
                    raise RuntimeError(f"Azure Read failed: {data}")
                lines = []
                for res in data.get("analyzeResult", {}).get("readResults", []):
                    for l in res.get("lines", []):
                        lines.append(l.get("text", ""))
                return ("\n".join(lines), "azure_read")
            if time.time() - t0 > self.timeout:
                raise TimeoutError("Azure Read timeout")
            time.sleep(1.2)

def compress_image(file_bytes: bytes, filename: str, target_kb: int = 3900) -> bytes:
    """
    Адаптивное сжатие под лимит Azure F0 (~4 МБ):
      1) PNG -> JPEG (RGB)
      2) JPEG: понижаем quality с 90 до min_quality
      3) Если всё ещё > target: уменьшаем разрешение (до 3 шагов по ~10%)

    Логирование:
      - исходный размер
      - формат и применённые шаги
      - итоговый размер/качество/шаги даунскейла
      - ошибки

    Поведение при ошибках:
      - Если исходный размер ≤ target — возвращаем как есть.
      - Если исходный размер > target и в процессе сжатия произошла ошибка — возбуждаем RuntimeError.
      - Если после всех попыток размер всё ещё > target — возбуждаем RuntimeError.
    """
    original_size = len(file_bytes)
    target_bytes = target_kb * 1024

    # Быстрый выход: уже в лимите — ничего не делаем
    if original_size <= target_bytes:
        logger.info(
            f"(OCR compress) '{filename}' уже в лимите: {original_size/1024:.1f} KB "
            f"(target {target_kb} KB)"
        )
        return file_bytes

    try:
        logger.info(
            f"(OCR compress) Начало сжатия '{filename}': {original_size/1024:.1f} KB, "
            f"target {target_kb} KB"
        )

        img = Image.open(io.BytesIO(file_bytes))
        # Нормализуем ориентацию по EXIF (смартфоны часто пишут ориентацию тегом)
        img = ImageOps.exif_transpose(img)
        fmt = (img.format or "JPEG").upper()

        steps = {
            "converted_to_jpeg": False,
            "quality_start": 90,
            "quality_end": None,
            "downscale_steps": 0,
            "final_w": None,
            "final_h": None,
            "subsampling": "4:2:0",  # фактическая передача идёт как код 2 (см. ниже)
        }

        # PNG -> JPEG (альфа не нужна для OCR, JPEG компактнее)
        if fmt in {"PNG", "HEIF", "HEIC", "WEBP"}:
            img = img.convert("RGB")
            fmt = "JPEG"
            steps["converted_to_jpeg"] = True

        # На всякий случай — работаем в RGB перед JPEG-сохранением
        img = img.convert("RGB")

        buf = io.BytesIO()
        quality = steps["quality_start"]
        min_quality = 55          # ниже — растёт риск ухудшения OCR
        subsampling = 2           # Pillow: 0=4:4:4, 1=4:2:2, 2=4:2:0 (лучший выигрыш по размеру)
        scale = 1.0               # текущий масштаб

        def save_try() -> int:
            """Пробуем сохранить и возвращаем получившийся размер в байтах."""
            buf.seek(0); buf.truncate()
            img.save(
                buf,
                format="JPEG",
                quality=quality,
                optimize=True,
                progressive=True,
                subsampling=subsampling
            )
            return buf.tell()

        size = save_try()
        logger.info(
            f"(OCR compress) '{filename}': попытка quality={quality}, subsampling=4:2:0 "
            f"-> {size/1024:.1f} KB"
        )

        # 1) Понижаем качество ступенями до min_quality
        while size > target_bytes and quality > min_quality:
            quality -= 5
            size = save_try()
            logger.info(f"(OCR compress) '{filename}': quality={quality} -> {size/1024:.1f} KB")

        # 2) Если всё ещё велик — уменьшаем разрешение (до 3 шагов)
        while size > target_bytes and steps["downscale_steps"] < 3:
            steps["downscale_steps"] += 1
            scale *= 0.9
            new_w = max(600, int(img.width * scale))
            new_h = max(600, int(img.height * scale))
            img = img.resize((new_w, new_h), resample=Image.LANCZOS)
            steps["final_w"] = new_w
            steps["final_h"] = new_h

            # После ресайза пробуем с качеством в «разумной зоне» (70–85), дальше снова снижаем при необходимости
            quality = min(85, max(quality, 70))
            size = save_try()
            logger.info(
                f"(OCR compress) '{filename}': downscale#{steps['downscale_steps']} -> "
                f"{new_w}x{new_h}, quality={quality} -> {size/1024:.1f} KB"
            )

            while size > target_bytes and quality > min_quality:
                quality -= 5
                size = save_try()
                logger.info(
                    f"(OCR compress) '{filename}': quality={quality} -> {size/1024:.1f} KB "
                    f"(после downscale)"
                )

        steps["quality_end"] = quality

        if size > target_bytes:
            # Не удалось уложиться — критично для F0; отдаём ошибку вверх по стеку
            raise RuntimeError(
                f"Не удалось ужать '{filename}' до {target_kb} KB (получилось {size/1024:.1f} KB)"
            )

        logger.info(
            "(OCR compress) Успех: '%s' %s->JPEG, итог %.1f KB (было %.1f KB), "
            "quality %s, downscale_steps=%d, final_size=%dx%d",
            filename,
            "PNG" if steps["converted_to_jpeg"] else fmt,
            size/1024,
            original_size/1024,
            steps["quality_end"],
            steps["downscale_steps"],
            steps["final_w"] or img.width,
            steps["final_h"] or img.height,
        )
        return buf.getvalue()

    except Exception as e:
        # Ошибка во время нужного сжатия — фатально для бесплатного тарифа; поднимем наверх
        logger.exception(f"(OCR compress) Ошибка при сжатии '{filename}': {e}")
        raise


def get_ocr_provider() -> OcrProvider:
    provider = (current_app.config.get("OCR_PROVIDER") or "azure").lower()
    if provider == "azure":
        return AzureReadProvider(
            endpoint=current_app.config["AZURE_VISION_ENDPOINT"],
            key=current_app.config["AZURE_VISION_KEY"],
        )
    raise ValueError(f"OCR provider '{provider}' is not configured")


def is_multipage_tiff(file_bytes: bytes) -> bool:
    try:
        with Image.open(io.BytesIO(file_bytes)) as im:
            frames = getattr(im, "n_frames", 1)
            return frames > 1
    except Exception:
        return False