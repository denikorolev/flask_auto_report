
// landing.js

document.addEventListener("DOMContentLoaded", function() {
    const images = document.querySelectorAll(".carousel-image");
    let currentImage = 0;

    // Показать первый слайд
    function showSlide(idx) {
        images.forEach((img, i) => img.classList.toggle("active", i === idx));
    }
    showSlide(currentImage);

    // Кнопки навигации слайдов
    document.getElementById("prev-slide").onclick = function() {
        currentImage = (currentImage - 1 + images.length) % images.length;
        showSlide(currentImage);
    };
    document.getElementById("next-slide").onclick = function() {
        currentImage = (currentImage + 1) % images.length;
        showSlide(currentImage);
    };

    // Автоматическая смена слайдов
    setInterval(() => {
        currentImage = (currentImage + 1) % images.length;
        showSlide(currentImage);
    }, 7000);
});
 