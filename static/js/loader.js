// loader.js


/**
 * Adds a loading indicator to the page.
 */
function showLoader() {
    if (document.getElementById("global-loader")) {
        return;
    }
    loader = document.createElement("div");
    loader.id = "global-loader";
    loader.innerHTML = `
        <div class="loader-overlay">
            <div class="loader-spinner"></div>
        </div>
    `;
    document.body.appendChild(loader);
   
    loader.style.display = "flex"; // Показываем индикатор
}


/**
 * Removes the loading indicator from the page.
 */
function hideLoader() {
    const loader = document.getElementById("global-loader");
    if (loader) {
        loader.style.display = "none"; // Скрываем индикатор
    }
}