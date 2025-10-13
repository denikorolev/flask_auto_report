// app/static/js/utils/dynamicsDropZone.js
import { pollTaskStatus } from "/static/js/utils/utils_module.js";

// ==== ВСПОМОГАТЕЛЬНЫЕ ====
const formatMB = (bytes) => (bytes / (1024 * 1024)).toFixed(2);

function ensureHeader(preview) {
    let h = preview.querySelector("#dropzone-files-header");
    if (!h) {
        h = document.createElement("h4");
        h.id = "dropzone-files-header";
        h.textContent = "Файлы для распознавания:";
        preview.appendChild(h);
    }
    return h;
}

function ensureList(preview) {
    let list = preview.querySelector("#dropzone-files-list");
    if (!list) {
        list = document.createElement("ol");
        list.id = "dropzone-files-list";
        list.style.marginTop = "8px";
        preview.appendChild(list);
    }
    return list;
}


function createRemoveButton() {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "dz-remove";
    btn.title = "Убрать из списка";
    btn.textContent = "✖"; // можно заменить на '×'
    btn.style.marginLeft = "8px";
    btn.style.cursor = "pointer";
    btn.style.border = "none";
    btn.style.background = "transparent";
    btn.style.fontSize = "14px";
    return btn;
}

// ==== КОНТРОЛЛЕР ОЧЕРЕДИ (общая логика для dnd / input / paste) ====
class OcrStagingController {
    /**
     * @param {HTMLElement} preview
     * @param {HTMLTextAreaElement} textarea
     * @param {string} ocrUrl
     * @param {HTMLInputElement|null} preparationCheckbox 
     */
    constructor(preview, textarea, ocrUrl = "/openai_api/ocr_extract_text", preparationCheckbox = null) {
        this.preview = preview;
        this.textarea = textarea;
        this.ocrUrl = ocrUrl;
        this.preparationCheckbox = preparationCheckbox; // чекбокс автоподготовки при помощи ИИ

        /** @type {File[]} */
        this.queue = [];
        this._abort = new AbortController(); // для общей отмены (кнопкой отмены)
        this.processingIndex = null;
        this.hint = document.getElementById("DropZoneInstructions"); // текст инструкции в дропзоне
        this._updatePrepBoxVisibility();
        this.statusByKey = new Map(); // key -> status text
    }

    _getKey(file) {
        // lastModified нужен, чтобы отличать файлы с одинаковым именем и размером
        return `${file?.name}|${file?.size}|${file?.lastModified || 0}`;
    }

    _getKeyByIndex(idx) {
        const f = this.queue[idx];
        return f ? this._getKey(f) : null;
    }

    getItemStatus(idx) {
        const key = this._getKeyByIndex(idx);
        return key ? (this.statusByKey.get(key) || "") : "";
    }

    isAutoPrepareEnabled() {
        try {
            return !!this.preparationCheckbox?.checked;
        } catch {
            return false;
        }
    }

    /**
     * Показ/скрытие чекбокса автоподготовки по числу файлов в очереди.
     * Прячем, если файлов > 1. Показываем, если 0 или 1.
     */
    _updatePrepBoxVisibility() {
        const prepBox = this.preparationCheckbox;
        // wrapper с id=DropZoneCheckboxWrapper у тебя есть в макросе
        const wrapper = document.getElementById("DropZoneCheckboxWrapper") 
                    || prepBox.closest("#DropZoneCheckboxWrapper")
                    || prepBox.parentElement;
        if (!prepBox || !wrapper) return;

        if (this.queue.length > 1) {
            // при множественных файлах автоочистка недоступна
            wrapper.style.display = "none";
            prepBox.checked = false; // на всякий
        } else {
            // один или ноль — доступно
            wrapper.style.display = "flex"; // у тебя там flex
        }
    }

    render() {
        // полностью очищаем контейнер
        this.preview.innerHTML = "";

        if (!this.queue.length) return;

        // сначала вставляем заголовок
        ensureHeader(this.preview);
        // затем список
        const list = ensureList(this.preview);

        list.innerHTML = "";

        for (let i = 0; i < this.queue.length; i++) {
            const f = this.queue[i];
            const li = document.createElement("li");
            li.dataset.idx = String(i);
            li.className = "dz-item";
            li.style.display = "flex";
            li.style.alignItems = "center";

            const info = document.createElement("span");
            info.className = "dz-info";
            info.textContent = `${i + 1}. ${f.name} (${formatMB(f.size)} MB)`;

            const status = document.createElement("span");
            status.className = "dz-status";
            status.style.marginLeft = "6px";
            const saved = this.getItemStatus(i);
            if (saved) status.textContent = ` — ${saved}`;

            const removeBtn = createRemoveButton();
            removeBtn.style.marginLeft = "8px";

            if (this.processingIndex === i) {
                li.style.opacity = "0.85";
                removeBtn.disabled = true;
                removeBtn.style.opacity = "0.4";
                removeBtn.title = "Файл сейчас обрабатывается";
            }

            li.appendChild(info);
            li.appendChild(status);
            li.appendChild(removeBtn);
            list.appendChild(li);
        }
    }

    setItemStatus(idx, statusText) {
        const key = this._getKeyByIndex(idx);
        if (key) {
            this.statusByKey.set(key, statusText);
        }

        const list = ensureList(this.preview);
        const li = list.querySelector(`li[data-idx="${idx}"]`);
        if (!li) return;

        const status = li.querySelector(".dz-status");
        if (status) {
            status.textContent = ` — ${statusText}`;
        } else {
            // на редкий случай, если узел не найден
            const fallback = document.createElement("span");
            fallback.className = "dz-status";
            fallback.style.marginLeft = "6px";
            fallback.textContent = ` — ${statusText}`;
            li.appendChild(fallback);
        }
    }

    // методы для скрыть/показать инструкцию в дропзоне
    _hideHint() {
        if (this.hint) this.hint.classList.add("hide");
    }
    _showHint() {
        if (this.hint) this.hint.classList.remove("hide");
        // также сбросим чекбокс автоподготовки
        if (this.preparationCheckbox) this.preparationCheckbox.checked = false;
    }


    /**
     * Добавить файлы в очередь (универсально для dnd / input / paste)
     * @param {FileList|File[]} files
     */
    addFiles(files) {
        if (!files) return;

        // Превращаем в массив и фильтруем только поддерживаемые типы
        const incoming = Array.from(files).filter(f =>
            f.type?.startsWith("image/") || f.type === "application/pdf"
        );
        if (!incoming.length) return;

        // убрать дубликаты по имени+размеру и отсечь >10 МБ
        const existingKey = new Set(this.queue.map(f => `${f.name}|${f.size}`));
        const MAX_SIZE = 10 * 1024 * 1024; // 10 MB

        for (const f of incoming) {
            if (f.size > MAX_SIZE) {
                if (window.toastr?.warning) {
                    window.toastr.warning("Файл слишком большой (макс. 10 МБ): " + f.name);
                } else {
                    alert("Файл слишком большой (макс. 10 МБ): " + f.name);
                }
                continue; // пропускаем файл
            }
            const key = `${f.name}|${f.size}`;
            if (!existingKey.has(key)) this.queue.push(f);
        }

        if (this.queue.length) this._hideHint(); // прячем подсказку
        this._updatePrepBoxVisibility(); // обновляем видимость чекбокса автоподготовки
        this.render();
    }

    /**
     * Добавить изображение из буфера обмена (blob)
     */
    addClipboardImage(blob) {
        if (!blob || !blob.size) return;
        const file = new File([blob], `clipboard_${Date.now()}.png`, { type: blob.type || "image/png" });
        this.addFiles([file]);
    }

    /**
     * Удалить файл из очереди по индексу
     */
    removeAt(index) {
        if (index < 0 || index >= this.queue.length) return;

        if (this.processingIndex === index) {
            if (window.toastr?.warning) {
                window.toastr.warning("Нельзя удалить файл во время распознавания. Нажмите «Отменить» или дождитесь окончания.");
            } else {
                alert("Нельзя удалить файл во время распознавания. Нажмите «Отменить» или дождитесь окончания.");
            }
            return;
        }
        const key = this._getKeyByIndex(index);
        if (key) this.statusByKey.delete(key);

        this.queue.splice(index, 1);
        // если удалили элемент до текущего processingIndex, сместим индекс
        if (this.processingIndex !== null && index < this.processingIndex) {
            this.processingIndex -= 1;
        }
        this._updatePrepBoxVisibility(); // обновляем видимость чекбокса автоподготовки
        this.render();
    }

    clearAll({ resetTextarea = true } = {}) {
        // Отменяем любые текущие опросы
        try { this._abort.abort(); } catch (_) {}
        this._abort = new AbortController();

        // Сбрасываем состояние очереди и индексы,чистим превью
        this.queue = [];
        this.processingIndex = null;
        this.preview.innerHTML = "";
        this.statusByKey.clear();
        this._updatePrepBoxVisibility(); // обновляем видимость чекбокса автоподготовки

        // Чистим textarea при необходимости
        if (resetTextarea && this.textarea) {
            this.textarea.value = "";
        }
        this._showHint();
    }

    cancelAll() {
        // Гасим текущие запросы
        try { this._abort.abort(); } catch (_) {}
        this._abort = new AbortController();
        this.processingIndex = null;

        const list = ensureList(this.preview);

        for (let i = 0; i < this.queue.length; i++) {
            const currentStatus = this.getItemStatus(i) || "";

            // финальные статусы, которые не трогаем
            const isFinal = /(✅|❌|⚠️)/u
                .test(currentStatus);

            if (!isFinal) {
                this.setItemStatus(i, "Отменено");
            }

            // параллельно разблокируем кнопку удаления у соответствующего li
            const li = list.querySelector(`li[data-idx="${i}"]`);
            if (li) {
                const removeBtn = li.querySelector(".dz-remove");
                if (removeBtn) {
                    removeBtn.disabled = false;
                    removeBtn.style.opacity = "1";
                    removeBtn.title = "Убрать из списка";
                }
            }
        }

        // перерисуем, чтобы всё стало консистентно
        this.render();
    }


    async _processSingle(file, idx) {
        // 1) Пытаемся сразу обработать PDF с текстовым слоем (это делает backend)
        console.log("Started _processSingle");
        const formData = new FormData();
        const autoPrepare = this.isAutoPrepareEnabled(); // чекбокс автоподготовки отправляем на сервер
        formData.append("file", file);
        formData.append("auto_prepare", autoPrepare); 

        let OCRRequestData;
        try {
            OCRRequestData = await sendRequest({
                url: this.ocrUrl,
                data: formData,
                loader: false
            });
        } catch (e) {
            console.error("[dropzone] sendRequest threw before JSON was returned:", e);
            this.setItemStatus(idx, "Ошибка сети/клиента при отправке.");
            throw e;
        }

        const data = OCRRequestData; 

        if (!data) throw new Error("Пустой ответ сервера");

        // Случай: PDF с текстовым слоем — сервер сразу вернёт text
        if (data.status === "success" && data.text) {
            console.log("PDF с текстовым слоем");
            const text = data.text || data.result.text || data.result || "не удалось идентифицировать ответ сервера";
            if (text) {
                const sep = this.textarea.value.trim() ? "\n\n" : "";
                this.textarea.value = `${this.textarea.value}${sep}${text}`;
            }
            this.setItemStatus(idx, "✅");
            return;
        }

        // Случай OCR: задача в очереди
        const taskId = data.task_id;
        if (data.status === "success" && taskId) {
            console.log("OCR задача поставлена в очередь, ждём результат...");
            const abortController = new AbortController();
            const externalSignal = this._abort.signal;

            // Если уже отменили — бросаем
            if (externalSignal.aborted) {
                throw new Error("cancelled");
            }
            const onAbort = () => {
                try { abortController.abort(); } catch (_) {}
            };
            externalSignal.addEventListener("abort", onAbort, { once: true });

            let maxAttemptsVar = 12;
            let intervalVar = 2000;

            // Если включена автоподготовка, стоит увеличить таймауты
            if (autoPrepare) {
                maxAttemptsVar = 18; 
                intervalVar = 4000; 
            }

            return await new Promise((resolve, reject) => {
                pollTaskStatus(taskId, {
                    maxAttempts: maxAttemptsVar,
                    interval: intervalVar,
                    onProgress: (progress) => {
                        const p = Math.min(Math.max(Math.floor(progress), 0), 99);
                        this.setItemStatus(idx, `Распознаём… ${p}%`);
                    },
                    onSuccess: (result) => {
                        let finalText = "";
                        if (typeof result === "string") finalText = result;
                        else if (result && typeof result === "object") finalText = result.text || result.data || "не удалось подобрать ключ к ответу сервера";
                        if (!finalText) {
                            this.setItemStatus(idx, "⚠️");
                            resolve();
                            return;
                        }
                        const sep = this.textarea.value.trim() ? "\n\n" : "";
                        this.textarea.value = `${this.textarea.value}${sep}${finalText}`;
                        this.setItemStatus(idx, "✅");
                        resolve();
                    },
                    onError: (errMsg) => {
                        this.setItemStatus(idx, `Ошибка: ${errMsg || "Неизвестная ошибка"}`);
                        reject(new Error(errMsg || "❌"));
                    },
                    onTimeout: () => {
                        this.setItemStatus(idx, "❌");
                        reject(new Error("timeout"));
                    },
                    abortController,
                    excludeResult: false
                });
            });
        }

        // Иначе — это ошибка
        throw new Error(data.message || "Неизвестная ошибка");
    }

    /**
     * Отправить ВСЁ по кнопке «Распознать»
     * — последовательно, чтобы не душить квоты/бэкенд
     */
    async sendAll() {
        if (!this.queue.length) {
            toastr.info?.("Нет файлов для распознавания.") || alert("Нет файлов для распознавания.");
            return;
        }
        for (let i = 0; i < this.queue.length; i++) {
            if (this._abort.signal.aborted) break;

            // помечаем текущий обрабатываемый индекс (для запрета удаления)
            this.processingIndex = i;
            this.render(); // обновим кнопки удаления у элементов

            this.setItemStatus(i, "Отправка…");
            try {
                await this._processSingle(this.queue[i], i);
            } catch (err) {
                console.error("OCR _processSingle failed:", err);
                if (String(err?.message || "").toLowerCase().includes("cancelled")) {
                    this.setItemStatus(i, "Отменено.");
                    break;
                }
            } finally {
                // снимаем «занятость» после обработки элемента
                this.processingIndex = null;
                this.render(); // вернём доступность крестиков
            }
        }
    }м
}

// ==== DnD-ОБЁРТКА (ТОЛЬКО РАБОТА С СОБЫТИЯМИ DND/PASTE) ====
// Ничего не отправляет — только добавляет в OcrStagingController.
export function setupDynamicsDropZone() {
    console.log("dynamicsDropZone started");

    const ocrUrl = "/openai_api/ocr_extract_text";
    const dropZone = document.getElementById("DropZone");
    const preview = document.getElementById("DropZonePreview");
    const textarea = document.getElementById("DropZoneTextarea");

    // элементы из макроса:
    const addBtn = document.getElementById("DropZoneButtonAdd");
    const hiddenInput = document.getElementById("aiGeneratorFileInput");
    const recognizeBtn = document.getElementById("DropZoneButtonRecognize");
    const clearBtn = document.getElementById("DropZoneButtonClear");  
    const cancelBtn = document.getElementById("ai-generator-cancel-button");
    const preparationCheckbox = document.getElementById("DropZonePreparationCheckbox");

    if (!dropZone || !preview || !textarea || !recognizeBtn || !addBtn || !hiddenInput || !cancelBtn || !clearBtn || !preparationCheckbox) {
        console.error("setupDynamicsDropZone: один из элементов не найден");
        return { detach: () => {}, controller: null };
    }

    // общий контроллер
    const controller = new OcrStagingController(preview, textarea, ocrUrl, preparationCheckbox);

    // --- Удаление по клику на ❌ (делегирование на контейнер preview)
    const onPreviewClick = (e) => {
        const btn = e.target.closest(".dz-remove");
        if (!btn) return;
        const li = btn.closest("li[data-idx]");
        if (!li) return;

        const idx = Number(li.dataset.idx);
        if (Number.isNaN(idx)) return;

        controller.removeAt(idx);
    };
    preview.addEventListener("click", onPreviewClick);

    // --- DnD ---
    const dragOverHandler = (e) => {
        e.preventDefault();
        dropZone.classList.add("dragover");
    };
    const dragLeaveHandler = (e) => {
        e.preventDefault();
        dropZone.classList.remove("dragover");
    };
    const dropHandler = (e) => {
        e.preventDefault(); 
        dropZone.classList.remove("dragover");
        const files = e.dataTransfer?.files;
        if (files && files.length) {
            controller.addFiles(files);
        }
    };
    // --- Paste (только images) ---
    const pasteHandler = (e) => {
        const items = e.clipboardData?.items || [];
        for (const item of items) {
            if (item.type.includes("image/")) {
                const blob = item.getAsFile();
                if (blob && blob.size) {
                    controller.addClipboardImage(blob);
                    e.preventDefault();
                    break;
                }
            }
        }
    };

    dropZone.addEventListener("dragover", dragOverHandler);
    dropZone.addEventListener("dragleave", dragLeaveHandler);
    dropZone.addEventListener("drop", dropHandler);
    dropZone.addEventListener("paste", pasteHandler);

    // --- Скрытый input + «Добавить файл» ---
    const onAddClick = (e) => {
        e.preventDefault();
        hiddenInput.click();
    };
    const onInputChange = (e) => {
        const files = e.target.files;
        if (files?.length) controller.addFiles(files);
        hiddenInput.value = ""; // чтобы можно было выбрать тот же файл повторно
    };
    addBtn.addEventListener("click", onAddClick);
    hiddenInput.addEventListener("change", onInputChange);

    // --- Кнопки ---
    const onRecognizeClick = (e) => {
        e.preventDefault();
        controller.sendAll();
    };
    recognizeBtn.addEventListener("click", onRecognizeClick);

    const onCancelClick = (e) => {
        e.preventDefault();
        controller.cancelAll();
    };
    cancelBtn.addEventListener("click", onCancelClick);

    // --- Очистить (дропзона + textarea) ---
    const onClearClick = (e) => {
        e.preventDefault();
        controller.clearAll({ resetTextarea: true });
        // Можно ещё убрать класс dragover на всякий
        dropZone.classList.remove("dragover");
        // Сбросить <input type="file">, чтобы позволить повторно выбрать тот же файл
        if (hiddenInput) hiddenInput.value = "";
        // Немного UX
        if (window.toastr?.info) window.toastr.info("Очищено.");
    };
    clearBtn.addEventListener("click", onClearClick);

    const detach = () => {
        preview.removeEventListener("click", onPreviewClick);
        dropZone.removeEventListener("dragover", dragOverHandler);
        dropZone.removeEventListener("dragleave", dragLeaveHandler);
        dropZone.removeEventListener("drop", dropHandler);
        dropZone.removeEventListener("paste", pasteHandler);
        addBtn.removeEventListener("click", onAddClick);
        hiddenInput.removeEventListener("change", onInputChange);
        recognizeBtn.removeEventListener("click", onRecognizeClick);
        clearBtn.removeEventListener("click", onClearClick);
        cancelBtn.removeEventListener("click", onCancelClick);
    };

    return { detach, controller };
}
