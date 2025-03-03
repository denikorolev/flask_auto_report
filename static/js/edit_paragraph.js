// edit_paragraph.js

document.addEventListener("DOMContentLoaded", function () {

    // Слушатель на кнопку "Вернуться к редактированию протокола"
    document.getElementById("backToReportButton").addEventListener("click", function () {
        console.log("Back to report button clicked");
        window.history.back();
    });

    // Инициализация Sortable для главных предложений (изменение индекса перетаскиванием)
    initSortableHeadSentences();

    initSentencePopup(); // Вызываем функцию для включения и выключения попапа предложения

    // Слушатель на кнопку "Редактировать предложение"
    document.querySelectorAll(".edit-sentence__btn-head--edit").forEach(button => {
        button.addEventListener("click", function () {
            editSentence(this);
        });
    });

    // Слушатель на заголовок "Дополнительные предложения"
    document.getElementById("editSentenceTitle").addEventListener("click", function () {
        expandTailSentencesHandler();
    }); 


});


// Инициализация Sortable для главных предложений
function initSortableHeadSentences() {
    const headSentencesList = document.querySelector(".edit-sentence__list");

    if (!headSentencesList) {
        console.warn("Список главных предложений не найден.");
        return;
    }

    new Sortable(headSentencesList, {
        handle: ".drag-handle", // Захват только за "хваталку"
        animation: 150,
        onEnd: function () {
            saveHeadSentencesOrder();
        }
    });
}


// Функция инициализации попапа предложений
function initSentencePopup() {
    document.querySelectorAll(".edit-sentence__text").forEach(sentence => {
        sentence.addEventListener("dblclick", function (event) {
            event.stopPropagation();
            parentElement = sentence.closest(".edit-sentence__item");
            if (parentElement.getAttribute("data-sentence-type") === "head") {
                showHeadSentencePopup(this, event);
            } else {
                showTailSentencePopup(this, event);
            };
        });
    });

    // Закрытие попапа при клике вне его
    document.addEventListener("click", function () {
        const popup = document.getElementById("headSentencePopup");
        const popup2 = document.getElementById("tailSentencePopup");
        if (popup) {
            popup.remove();
        }
        if (popup2) {
            popup2.remove();
        }
    });
}


// Функция редактирования предложения
function editSentence(button) {
    const sentenceId = button.getAttribute("data-sentence-id");
    const paragraphId = document.getElementById("editParagraphContainer").getAttribute("data-paragraph-id");
    const reportId = document.getElementById("editParagraphContainer").getAttribute("data-report-id");

    window.location.href = `/editing_report/edit_head_sentence?sentence_id=${sentenceId}&paragraph_id=${paragraphId}&report_id=${reportId}`;
    
}



// Обработчик клика на заголовок "Дополнительные предложения"- разворачивает/сворачивает список
function expandTailSentencesHandler() {
    const tailSentencesList = document.getElementById("editTailSentenceList");
    if (!tailSentencesList) {
        console.warn("Список дополнительных предложений не найден.");
        return;
    }

    tailSentencesList.style.display = tailSentencesList.style.display === "none" ? "block" : "none";
}


// Вызываемые функции (не требуют инициализации при загрузке страницы)

// Функция сохранения нового порядка главных предложений
function saveHeadSentencesOrder() {
    const allSentences = document.querySelectorAll(".edit-sentence__item");
    const sentences = Array.from(allSentences).filter(sentence => sentence.getAttribute("data-sentence-type") === "head");
    const updatedOrder = [];

    sentences.forEach((sentence, newIndex) => {
        const sentenceId = sentence.getAttribute("data-sentence-id");
        updatedOrder.push({
            sentence_id: sentenceId,
            new_index: newIndex
        });
    });
    
    sendRequest({
        url: "/editing_report/update_head_sentence_order",
        method: "POST",
        data: { updated_order: updatedOrder }
    }).then(response => {
        if (response.status === "success") {
            debugger;
            window.location.reload();
            console.log("Порядок главных предложений успешно сохранен");
        } else {
            console.error("Ошибка при сохранении порядка:", response.message);
        }
    });
}


// Функция отображения попапа для главного предложения
function showHeadSentencePopup(sentenceElement, event) {
    // Удаляем старый попап, если он есть
    document.getElementById("headSentencePopup")?.remove();

    // Данные предложения
    const parentElement = sentenceElement.closest(".edit-sentence__item");

    const sentenceId = parentElement.getAttribute("data-sentence-id");
    const sentenceIndex = parentElement.getAttribute("data-sentence-index");
    const sentenceComment = parentElement.getAttribute("data-sentence-comment") || "Нет комментария";
    const sentenceTags = parentElement.getAttribute("data-sentence-tags") || "Нет тегов";

    // Создаем элемент попапа
    const popup = document.createElement("div");
    popup.id = "headSentencePopup";
    popup.classList.add("paragraph-popup");
    popup.innerHTML = `
            <span>ID:</span> <span>${sentenceId}</span><br>
            <span>Индекс:</span> <span>${sentenceIndex} </span><br>
            <span>Комментарий:</span> <span>${sentenceComment}</span><br>
            <span>Теги:</span> <span>${sentenceTags}</span><br>
            `;

    // Позиционируем попап рядом с курсором
    popup.style.position = "absolute";
    popup.style.left = `${event.pageX + 15}px`;
    popup.style.top = `${event.pageY +15}px`;

    document.body.appendChild(popup);

    // Останавливаем всплытие клика, чтобы не закрыть попап сразу
    popup.addEventListener("click", event => event.stopPropagation());
}


// Функция отображения попапа для дополнительного предложения
function showTailSentencePopup(sentenceElement, event) {
    // Удаляем старый попап, если он есть
    document.getElementById("tailSentencePopup")?.remove();

    // Данные предложения
    const parentElement = sentenceElement.closest(".edit-sentence__item");

    const sentenceId = parentElement.getAttribute("data-sentence-id");
    const sentenceComment = parentElement.getAttribute("data-sentence-comment") || "Нет комментария";
    const sentenceTags = parentElement.getAttribute("data-sentence-tags") || "Нет тегов";

    // Создаем элемент попапа
    const popup = document.createElement("div");
    popup.id = "tailSentencePopup";
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
