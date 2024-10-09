// api.js

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
                // If HTTP status is not OK, handle as an error
                return response.json().then(errorData => {
                    throw new Error(errorData.message || `HTTP error! Status: ${response.status}`);
                });
            }

            // Process response based on responseType
            return responseType === "blob" ? response.blob() : response.json();
        })
        .then(data => {
            // Check if the response contains a status field
            if (responseType === "json" && data.status) {
                if (data.status !== "success") {
                    throw new Error(data.message || "Request failed");
                }
            }

            // Return the data if status is success
            return data;
        })
        .catch(error => {
            // Centralized error handling
            console.error("Error:", error);
            throw error; // Re-throw the error for the caller to handle
        });
}
