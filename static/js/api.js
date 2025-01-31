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

    if (data instanceof FormData) {
        fetchOptions.body = data;
    } else {
        fetchOptions.headers["Content-Type"] = "application/json";
        fetchOptions.body = JSON.stringify(data);
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
            if (responseType === "json" && data.status) {
                if (data.status !== "success") {
                    alert(data.message || "Request failed");
                    throw new Error(data.message || "Request failed");
                }

                let alertMessage = data.message || "Request completed successfully.";
                if (data.notifications?.length) {
                    alertMessage += `\n\nNotifications:\n${data.notifications.join('\n')}`;
                }
                toastr.success(alertMessage);
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



/**
 * Sends a request to the server to generate an impression based on the input text and assistant list.
 *
 * @param {string} text - The input text to be sent to the server.
 * @param {Array<string>} assistantList - A list of assistant names to be included in the request.
 * @returns {Promise<string>} - Returns a promise that resolves with the server's response message or error.
 */
function generateImpressionRequest(text, assistantList) {
    // Формируем данные для отправки
    const jsonData = {
        text: text,
        assistants: assistantList // передаем список ассистентов
    };

    // Отправляем запрос на сервер с помощью sendRequest
    return sendRequest({   
        url: "/openai_api/generate_impression",
        data: jsonData,
        csrfToken: csrfToken
    }).then(data => {
        if (data.status === "success") {
            return data.data; // Возвращаем успешный ответ от сервера
        } else {
            return data.message; // Возвращаем сообщение об ошибке, если запрос не успешен
        }
    });
}
