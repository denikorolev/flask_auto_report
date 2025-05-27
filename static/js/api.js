// api.js

/**
 * Отправляет JSON или FormData-запрос на сервер.
 * 
 * @param {Object} options - Параметры запроса.
 * @param {string} options.url - URL для запроса.
 * @param {string} [options.method="POST"] - HTTP-метод запроса (по умолчанию POST).
 * @param {Object|FormData} options.data - Данные, которые отправляются в теле запроса.
 * @param {string} [options.responseType="json"] - Ожидаемый тип ответа ("json" или "blob").
 * @param {boolean} [options.loader=true] - Показывать ли индикатор загрузки.
 * @returns {Promise<Object|Blob|null>} - Возвращает промис с JSON-ответом, Blob-данными или null в случае ошибки.
 */
function sendRequest({ url, method = "POST", data = {}, responseType = "json", loader = true }) {
    if (!csrfToken) {
        alert("CSRF token not found! The request cannot be sent.");
        console.error("CSRF token is missing. Make sure it's defined globally.");
        return Promise.reject(new Error("CSRF token is missing")); // Прерываем выполнение запроса
    }

    if (loader) {
        showLoader(); // Показываем индикатор загрузки
    }

    const fetchOptions = {
        method: method,
        headers: {
            "X-CSRFToken": csrfToken
        }
    };

    if (method !== "GET" && method !== "HEAD") {
        if (data instanceof FormData) {
            fetchOptions.body = data;
        } else {
            fetchOptions.headers["Content-Type"] = "application/json";
            fetchOptions.body = JSON.stringify(data);
        }
    }

    return fetch(url, fetchOptions)
        .then(response => {
            if (!response.ok) {
                const contentType = response.headers.get("content-type");
                
                if (contentType && contentType.includes("application/json")) {
                    return response.json().then(errorData => {
                        throw new Error(errorData.message || `HTTP error! Status: ${response.status}`);
                    });
                } else {
                    return response.text().then(errorText => {
                        console.error("Server returned non-JSON response:", errorText);
                        throw new Error(`Unexpected response format (status: ${response.status})`);
                    });
                }
            }
            return responseType === "blob" ? response.blob() : response.json();
        })
        .then(data => {
            if (responseType === "json") {
                if (!data) {
                    console.error("Ошибка: получены пустые данные от сервера.");
                    alert("Ошибка: пустой ответ от сервера.");
                    throw new Error("Empty response from server");
                }
        
                let alertMessage = data.message || "Request completed successfully.";
        
                if (data.notifications?.length) {
                    alertMessage += `\n\nNotifications:\n${data.notifications.join('\n')}`;
                }
        
                if (data.status === "success") {
                    toastr.success(alertMessage);
                } else if (data.status === "warning") {
                    toastr.warning(alertMessage);
                } else {
                    alert(alertMessage || "Request failed");
                    throw new Error(data.message || "Request failed");
                }
            }
            return data;
        })
        .catch(error => {
            alert(error.message);
            console.error("Error:", error);
            return null; // Не бросаем ошибку, чтобы `finally` отработал
        })
        .finally(() => {
            hideLoader(); // Скрываем индикатор загрузки после завершения запроса
        });
}


