// ..utils/utils_module.js


/**
 * Универсальный поллер статуса Celery-задачи.
 * 
 * @param {string} task_id - ID Celery-задачи
 * @param {Object} options - Параметры
 * @param {number} [options.maxAttempts=20] - Максимальное количество попыток
 * @param {number} [options.interval=9000] - Интервал между попытками (мс)
 * @param {function} [options.onProgress] - Коллбек прогресса (progress, attempt, maxAttempts)
 * @param {function} [options.onSuccess] - Коллбек при успехе (result)
 * @param {function} [options.onError] - Коллбек при ошибке (errorMessage, data)
 * @param {function} [options.onTimeout] - Коллбек при таймауте
 */
export function pollTaskStatus(task_id, {
    maxAttempts = 20,
    interval = 9000,
    onProgress = () => {},
    onSuccess = () => {},
    onError = () => {},
    onTimeout = () => {},
} = {}, attempt = 0) {
    const progress = Math.min((attempt / maxAttempts) * 100, 99);
    onProgress(progress, attempt, maxAttempts);

    sendRequest({
        url: `/tasks_status/task_status/${task_id}`,
        method: "GET",
        loader: false
    }).then(data => {
        if (!data) {
            onError("Ошибка при получении статуса задачи.", data);
            return;
        }

        const status = (data.status || "").toLowerCase();

        if (status === "pending" || status === "started") {
            if (attempt < maxAttempts) {
                setTimeout(() => pollTaskStatus(task_id, {
                    maxAttempts, interval, onProgress, onSuccess, onError, onTimeout
                }, attempt + 1), interval);
            } else {
                onTimeout();
            }
        } else if (status === "success") {
            onProgress(100, attempt, maxAttempts);
            onSuccess(data.result);
        } else if (status === "error") {
            let details = data.details || "";
            if (details.toLowerCase().includes("revoked") || details.toLowerCase().includes("terminated")) {
                onError("Слишком много запросов на сервер. Пожалуйста, попробуйте позже.", data);
            } else {
                onError("Ошибка: " + details, data);
            }
        } else {
            onError("Ошибка: " + (data.details || "Неизвестный статус"), data);
        }
    }).catch(err => {
        onError("Ошибка связи с сервером", err);
    });
}



/**
 * Универсальная функция для обновления прогресс-бара.
 * @param {Object} opts
 * @param {string|HTMLElement} opts.bar - id или DOM-элемент самого прогресс-бара (div.dynamics-progress-bar)
 * @param {string|HTMLElement} [opts.label] - id или DOM-элемент label (span)
 * @param {string|HTMLElement} [opts.text] - id или DOM-элемент подписи (p)
 * @param {number} percent - значение от 0 до 100
 * @param {string} [statusText] - надпись для подписи (по желанию)
 */
export function updateProgressBar({ bar, label, text }, percent, statusText = null) {
    const barElem = typeof bar === "string" ? document.getElementById(bar) : bar;
    const labelElem = label ? (typeof label === "string" ? document.getElementById(label) : label) : null;
    const textElem = text ? (typeof text === "string" ? document.getElementById(text) : text) : null;

    if (!barElem) return;
    // Ширина через style или через CSS-переменную, зависит от реализации
    barElem.style.width = `${Math.min(percent, 100)}%`;
    if (labelElem) labelElem.textContent = `${Math.round(percent)}%`;
    if (textElem && statusText !== null) textElem.textContent = statusText;
}