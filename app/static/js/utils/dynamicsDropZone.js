// static/js/utils/dynamicsDropZone.js

import { pollTaskStatus } from "/static/js/utils/utils_module.js";

// форматтер размеров
const formatMB = (bytes) => (bytes / (1024 * 1024)).toFixed(2);


/**
 * Рендер превью для "отложенного" файла (без отправки на сервер).
 * Показываем имя и размер. Минимально — без нумерации и списка (добавим на след. шагах).
 */
function renderStagedPreview(preview, file) {
    preview.innerHTML = "";
    const p = document.createElement("p");
    p.textContent = `${file.name} (${formatMB(file.size)} MB)`;
    preview.appendChild(p);
}


/**
 * Универсальная dropzone для drag&drop и paste файлов (jpeg/png/pdf),
 * с предпросмотром и отправкой на OCR endpoint.
 * @param {string} dropZoneId - id drop-зоны (div)
 * @param {string} previewId - id блока для предпросмотра
 * @param {string} textareaId - id textarea куда кидать текст после OCR
 * @param {string} [ocrUrl="/working_with_reports/ocr_extract_text"] - endpoint для OCR
 * @returns {Function} detach - функция для снятия обработчиков
 */
export function setupDynamicsDropZone({
        dropZoneId,
        previewId,
        textareaId,
        ocrUrl = "/openai_api/ocr_extract_text"
    }) {
        console.log("dynamicsDropZone started")
    const dropZone = document.getElementById(dropZoneId);
    const preview = document.getElementById(previewId);
    const textarea = document.getElementById(textareaId);

    if (!dropZone || !preview || !textarea) {
        console.warn("setupDynamicsDropZone: один из элементов не найден");
        return () => {};
    }

    const dragOverHandler = e => {
        e.preventDefault();
        dropZone.classList.add("dragover");
    };

    const dragLeaveHandler = e => {
        e.preventDefault();
        dropZone.classList.remove("dragover");
    };

    const dropHandler = e => {
        e.preventDefault();
        dropZone.classList.remove("dragover");
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileUpload(files[0], preview, textarea, ocrUrl);
        }
    };

    const pasteFileHandler = e => {
        const items = e.clipboardData.items;
        for (let item of items) {
            if (item.type.indexOf("image") !== -1) {
                const file = item.getAsFile();
                handleFileUpload(file, preview, textarea, ocrUrl);
                e.preventDefault();
            }
        }
    };

    dropZone.addEventListener("dragover", dragOverHandler);
    dropZone.addEventListener("dragleave", dragLeaveHandler);
    dropZone.addEventListener("drop", dropHandler);
    dropZone.addEventListener("paste", pasteFileHandler);

    // Вернуть функцию для снятия обработчиков
    return () => {
        dropZone.removeEventListener("dragover", dragOverHandler);
        dropZone.removeEventListener("dragleave", dragLeaveHandler);
        dropZone.removeEventListener("drop", dropHandler);
        dropZone.removeEventListener("paste", pasteFileHandler);
    };
}


/**
 * Предпросмотр + отправка файла на OCR
 * @param {File} file 
 * @param {HTMLElement} preview 
 * @param {HTMLTextAreaElement} textarea 
 * @param {string} ocrUrl
 */
export function handleFileUpload(file, preview, textarea, ocrUrl) {
    if (!file) return;
    preview.innerHTML = "";
    // определяем имя и размер файла
    const fileName = file.name || "uploaded_file";
    const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2);

    // Image preview
    if (file.type.startsWith("image/") || file.type === "application/pdf") {
        const fTitle = document.createElement("h5");
        const f = document.createElement("p");
        f.textContent = ` ${fileName} (${fileSizeMB} MB)`;
        preview.appendChild(f);

        const reader = new FileReader();
        reader.onload = function (e) {
            img.src = e.target.result;
        };
        reader.readAsDataURL(file);
    } else {
        preview.textContent = "Неподдерживаемый тип файла: " + file.type;
        return;
    }

    // upload to OCR
    const formData = new FormData();
    formData.append("file", file);

    sendRequest({
        url: ocrUrl,
        data: formData,
        responseType: "json",
        loader: true
    }).then(data => {
        if (!data) {
            preview.textContent = "Ошибка распознавания: пустой ответ сервера.";
            return;
        }
        if (data.status === "success" && data.text) {
            // PDF с текстовым слоем: получили текст сразу
            textarea.value = data.text;
            preview.textContent = "Текст извлечён из PDF без OCR.";
            return;
        }
        if (data.status === "success" && (data.data || data.task_id)) {
            preview.textContent = "Файл отправлен на OCR. Ожидайте…";

            const abortController = new AbortController();
            const cancelBtn = document.getElementById("aiGeneratorCancelButton");

            if (cancelBtn) {
                // добавляем обработчик отмены (можно навешивать и другие слушатели без проблем)
                cancelBtn.addEventListener("click", () => {
                    abortController.abort();
                    preview.textContent = "Распознавание отменено пользователем.";
                });
            }


            pollTaskStatus(data.task_id, {
                maxAttempts: 25,
                interval: 6000,
                onProgress: (progress) => {
                    // обновляем текстово: 0–99%
                    const p = Math.min(Math.max(Math.floor(progress), 0), 99);
                    preview.textContent = `Распознаём… ${p}%`;
                },
                onSuccess: (result) => {
                    // result может быть строкой, либо объектом {text: "..."}
                    let finalText = "";
                    if (typeof result === "string") {
                        finalText = result;
                    } else if (result && typeof result === "object") {
                        finalText = result.result || result.data || result.text || ""; // нужно будет определиться точно какой будет ключ
                    }
                    if (!finalText) {
                        preview.textContent = "Готово, но пустой результат OCR.";
                        return;
                    }
                    textarea.value = finalText;
                    preview.textContent = "OCR завершён.";
                },
                onError: (errMsg) => {
                    preview.textContent = (errMsg || "Ошибка при распознавании файла.");
                },
                onTimeout: () => {
                    preview.textContent = "Превышено время ожидания OCR. Попробуйте позже.";
                },
                abortController, // держим для совместимости/возможной отмены
                excludeResult: false // хотим получить результат сразу
            });
            return;
        }
        // Иначе — ошибка
        preview.textContent = "Ошибка распознавания: " + (data.message || "Unknown error");
    });
}



/**
 * Вставка из буфера обмена: сначала ищет текст, если нет — image/png/jpeg.
 * Если ничего не найдено — сообщает пользователю.
 * @param {HTMLTextAreaElement} textarea
 * @param {HTMLElement} preview
 */
export async function handlePasteFromClipboard(textarea, preview) {
    const ocrUrl = "/openai_api/ocr_extract_text";
    textarea.value = "";
    if (preview) preview.innerHTML = "";
    try {
        const items = await navigator.clipboard.read();
        if (!items || !items.length) {
            alert("Буфер обмена пуст или не содержит поддерживаемых данных.");
            return;
        }
        let found = false;
        // Сначала ищем текст
        for (const item of items) {
            if (item.types.includes('text/plain')) {
                const textBlob = await item.getType('text/plain');
                const text = await textBlob.text();
                if (text && text.trim()) {
                    textarea.value = text;
                    found = true;
                    break;
                }
            }
        }
        // Если текст не найден — ищем картинку
        if (!found) {
            for (const item of items) {
                if (item.types.includes('image/png') || item.types.includes('image/jpeg')) {
                    const blob = await item.getType(item.types[0]);
                    if (blob && blob.size > 0) {
                        const file = new File([blob], "clipboard_image.png", { type: blob.type });
                        handleFileUpload(file, preview, textarea, ocrUrl);
                        found = true;
                        break;
                    }
                }
            }
        }
        if (!found) {
            alert("Буфер обмена пуст или не содержит поддерживаемых данных (текст или изображение).");
        }
    } catch (e) {
        alert("Не удалось получить доступ к буферу обмена: " + e.message);
        console.error(e);
    }
}