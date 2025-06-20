// static/js/utils/dynamicsDropZone.js

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
        ocrUrl = "/working_with_reports/ocr_extract_text"
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
export function handleFileUpload(file, preview, textarea) {
    if (!file) return;
    preview.innerHTML = "";

    // Image preview
    if (file.type.startsWith("image/")) {
        const img = document.createElement("img");
        img.style.maxWidth = "200px";
        img.style.maxHeight = "200px";
        preview.appendChild(img);

        const reader = new FileReader();
        reader.onload = function (e) {
            img.src = e.target.result;
        };
        reader.readAsDataURL(file);
    } else if (file.type === "application/pdf") {
        preview.textContent = "PDF файл загружен: " + file.name;
    } else {
        preview.textContent = "Неподдерживаемый тип файла: " + file.type;
        return;
    }

    // upload to OCR
    const formData = new FormData();
    formData.append("file", file);

    sendRequest({
        url: "/openai_api/ocr_extract_text",
        method: "POST",
        data: formData,
        responseType: "json",
        loader: true
    }).then(data => {
        if (data && data.status === "success" && data.text) {
            if (data.message && data.message.includes("PDF files are not supported")) {
                preview.textContent = data.message; 
            } else if (data.text) {
                textarea.value = data.text;
            }
        } else {
            preview.textContent = "Ошибка распознавания: " + (data?.message || "Unknown error");
        }
    });
}



/**
 * Вставка из буфера обмена: сначала ищет текст, если нет — image/png/jpeg.
 * Если ничего не найдено — сообщает пользователю.
 * @param {HTMLTextAreaElement} textarea
 * @param {HTMLElement} preview
 */
export async function handlePasteFromClipboard(textarea, preview) {
    const ocrUrl = "/working_with_reports/ocr_extract_text";
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