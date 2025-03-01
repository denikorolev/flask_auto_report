// edit_head_sentence.js

document.addEventListener("DOMContentLoaded", function () {

    initSentencePopup(); // Вызываем функцию для включения и выключения попапа предложения

    // Слушатель на заголовок "Дополнительные предложения для главного предложения"
    document.getElementById("editSentenceTitle").addEventListener("click", function () {
        expandBodySentencesHandler();
    }); 

    // Слушатель на кнопку "Вернуться к редактированию параграфа"
    document.getElementById("backToParagraphButton").addEventListener("click", function () {
        console.log("Back to paragraph button clicked");
        window.history.back();
    });

    // Слушатель на кнопку "Вернуться к редактированию протокола"
    document.getElementById("backToReportButton").addEventListener("click", function () {
        console.log("Back to report button clicked");
        window.history.go(-2);
    });



});


// Функция инициализации попапа предложений
// Функция инициализации попапа предложений
function initSentencePopup() {
    document.querySelectorAll(".edit-sentence__text").forEach(sentence => {
        sentence.addEventListener("click", function (event) {
            event.stopPropagation();
                showBodySentencePopup(this, event);
        });
    });

    // Закрытие попапа при клике вне его
    document.addEventListener("click", function () {
        const popup = document.getElementById("bodySentencePopup");
        
        if (popup) {
            popup.remove();
        }
        
    });
}


// Функция обработки клика на заголовок "Дополнительные предложения для главного предложения"
function expandBodySentencesHandler() {
    const bodySentencesList = document.getElementById("bodySentenceList");

    if (!bodySentencesList) {
        console.warn("Список дополнительных предложений не найден.");
        return;
    }

    bodySentencesList.style.display = bodySentencesList.style.display === "none" ? "block" : "none";
}


// Вызываемые функции (не требуют инициализации при загрузке страницы)

// Функция отображения попапа для дополнительного предложения
function showBodySentencePopup(sentenceElement, event) {
    // Удаляем старый попап, если он есть
    document.getElementById("bodySentencePopup")?.remove();

    // Данные предложения
    const parentElement = sentenceElement.closest(".edit-sentence__item");

    const sentenceId = parentElement.getAttribute("data-sentence-id");
    const sentenceComment = parentElement.getAttribute("data-sentence-comment") || "Нет комментария";
    const sentenceTags = parentElement.getAttribute("data-sentence-tags") || "Нет тегов";

    // Создаем элемент попапа
    const popup = document.createElement("div");
    popup.id = "bodySentencePopup";
    popup.classList.add("paragraph-popup");
    popup.innerHTML = `
            <span>ID:</span> <span>${sentenceId}</span><br>
            <label>Комментарий:</label> <input type="text" value="${sentenceComment}" class="paragraph-popup-input"><br>
            <label>Теги:</label> <input type="text" value="${sentenceTags}" class="paragraph-popup-input"><br>
            <button class="btn report__btn paragraph-popup-btn--save">Сохранить</button>
            `;

    // Позиционируем попап рядом с курсором
    popup.style.position = "absolute";
    popup.style.left = `${event.pageX + 15}px`;
    popup.style.top = `${event.pageY + 15}px`;

    document.body.appendChild(popup);

    // Останавливаем всплытие клика, чтобы не закрыть попап сразу
    popup.addEventListener("click", event => event.stopPropagation());
}