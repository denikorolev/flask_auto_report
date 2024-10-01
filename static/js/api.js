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
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            // Process response based on responseType
            return responseType === "blob" ? response.blob() : response.json();
        })
        .then(data => {
            // If responseType is "json", check the status
            if (responseType === "json" && data.hasOwnProperty('status')) {
                if (data.status !== "success") {
                    throw new Error(data.message || "Request failed");
                }
            }

            // Return the data
            return data;
        })
        .catch(error => {
            console.error("Error:", error);
            throw error;
        });
}
