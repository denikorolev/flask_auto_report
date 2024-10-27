/**
 * Sends a JSON or FormData request to the server.
 * 
 * @param {Object} options - Options for the request.
 * @param {string} options.url - The URL for the request.
 * @param {string} [options.method="POST"] - The HTTP method (default is POST).
 * @param {Object|FormData} options.data - The data to be sent in the request body.
 * @param {string} [options.responseType="json"] - The type of response expected ("json" or "blob").
 * @returns {Promise<Object|Blob>} - The response data as a JSON object or Blob.
 */
function sendRequest({ url, method = "POST", data = {}, responseType = "json" }) {
    const fetchOptions = {
        method: method,
        headers: {}
    };

    // Check if data is FormData
    if (data instanceof FormData) {
        fetchOptions.body = data;  // FormData automatically sets the headers
    } else {
        fetchOptions.headers["Content-Type"] = "application/json";
        fetchOptions.body = JSON.stringify(data);  // Convert data to JSON for normal requests
    }

    return fetch(url, fetchOptions)
        .then(response => {
            if (!response.ok) {
                // Parse error message from the response
                return response.json().then(errorData => {
                    throw new Error(errorData.message || `HTTP error! Status: ${response.status}`);
                });
            }
            // Handle different response types
            return responseType === "blob" ? response.blob() : response.json();
        })
        .then(data => {
            // If it's JSON and has a status field, handle it
            if (responseType === "json" && data.status) {
                if (data.status !== "success") {
                    throw new Error(data.message || "Request failed");
                }

                // Combine the main message and notifications
                let alertMessage = data.message || "Request completed successfully.";

                // Check for notifications and append them to the message
                if (data.notifications && Array.isArray(data.notifications)) {
                    const notificationMessage = data.notifications.join('\n');
                    alertMessage += `\n\nNotifications:\n${notificationMessage}`;
                }
                toastr.success(alertMessage);
            }
            return data;
        })
        .catch(error => {
            alert(error.message);
            console.error("Error:", error);
            throw error;
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
        data: jsonData
    }).then(data => {
        if (data.status === "success") {
            return data.data; // Возвращаем успешный ответ от сервера
        } else {
            return data.message; // Возвращаем сообщение об ошибке, если запрос не успешен
        }
    });
}
