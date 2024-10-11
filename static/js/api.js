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
async function sendRequest({ url, method = "POST", data = {}, responseType = "json" }) {
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

    try {
        const response = await fetch(url, fetchOptions);

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || `HTTP error! Status: ${response.status}`);
        }

        const data = responseType === "blob" ? await response.blob() : await response.json();

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
        
        console.log(data);
        return data;

    } catch (error) {
        alert(error.message);
        console.error("Error:", error);
        throw error;
    }
}
