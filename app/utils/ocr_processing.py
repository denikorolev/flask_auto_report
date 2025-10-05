# app/utils/ocr_processing.py
import time
import requests
from typing import Tuple
from flask import current_app

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

def get_ocr_provider() -> OcrProvider:
    provider = (current_app.config.get("OCR_PROVIDER") or "azure").lower()
    if provider == "azure":
        return AzureReadProvider(
            endpoint=current_app.config["AZURE_VISION_ENDPOINT"],
            key=current_app.config["AZURE_VISION_KEY"],
        )
    raise ValueError(f"OCR provider '{provider}' is not configured")