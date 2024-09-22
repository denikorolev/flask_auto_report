/**
 * Sends a JSON or FormData request to the server.
 * 
 * @param {Object} options - Options for the request.
 * @param {string} options.url - The URL for the request.
 * @param {string} [options.method="POST"] - The HTTP method (default is POST).
 * @param {Object|FormData} options.data - The data to be sent in the request body.
 * @returns {Promise<Object>} - The response data as a JSON object.
 */
function sendRequest({ url, method = "POST", data = {} }) {
    const fetchOptions = {
        method: method,
        headers: {}
    };

    // Проверяем, является ли data объектом FormData
    if (data instanceof FormData) {
        fetchOptions.body = data;  // FormData автоматически ставит заголовки
    } else {
        fetchOptions.headers["Content-Type"] = "application/json";
        fetchOptions.body = JSON.stringify(data);  // Преобразуем данные в JSON для обычных запросов
    }

    return fetch(url, fetchOptions)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();  // Парсим ответ как JSON
        })
        .then(data => {
            // Логируем ответ сервера для отладки
            console.log("Server response:", data);

            // Проверяем наличие поля 'status'
            if (data.hasOwnProperty('status')) {
                // Если статус не 'success', выбрасываем ошибку
                if (data.status !== "success") {
                    throw new Error(data.message || "Request failed");
                }
            }

            // Возвращаем данные
            return data;
        })
        .catch(error => {
            console.error("Error:", error);
            throw error;
        });
}
