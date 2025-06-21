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
   
    // Если страница грузится быстрее 300 мс, лоадер не появится
    window.loaderTimeout = setTimeout(() => {
        loader.classList.remove("hidden-loader"); // Плавное появление через ccs-класс
    }, 300); // 300 мс —  задержка
}


/**
 * Removes the loading indicator from the page.
 */
function hideLoader() {
    clearTimeout(loaderTimeout); // Очищаем таймаут, чтобы лоадер не появился

    const loader = document.getElementById("global-loader");

    if (loader) {
        loader.classList.add("hidden-loader"); // Плавное исчезновение через ccs-класс
        setTimeout(() => {
            loader.remove(); // Удаляем через 300 мс после исчезновения
        }, 300);
    }
}