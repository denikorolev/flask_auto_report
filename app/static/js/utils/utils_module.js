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
    abortController = null,
    excludeResult = false
} = {}, attempt = 0) {

    if (abortController?.signal?.aborted) {
        onError("Запрос отменён пользователем.");
        return;
    }
    const progress = Math.min((attempt / maxAttempts) * 100, 99);
    onProgress(progress, attempt, maxAttempts);
    const url = `/tasks_status/task_status/${task_id}?exclude_result=${excludeResult}`;

    sendRequest({
        url: url,
        method: "GET",
        loader: false
    }).then(data => {
        if (!data) {
            onError("Ошибка при получении статуса задачи.", data);
            return;
        }
        if (abortController && abortController.signal.aborted) {
            onError("Запрос отменён пользователем.");
            return;
        }

        const status = (data.status || "").toLowerCase();

        if (status === "pending" || status === "started") {
            if (attempt < maxAttempts) {
                setTimeout(() => pollTaskStatus(task_id, {
                    maxAttempts, 
                    interval, 
                    onProgress, 
                    onSuccess, 
                    onError, 
                    onTimeout, 
                    abortController, 
                    excludeResult
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
        if (!abortController?.signal?.aborted) {
            onError("Ошибка связи с сервером", err);
        }
    });
}


