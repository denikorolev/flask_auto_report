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
    document.querySelectorAll(".edit-sentence__btn--edit-head").forEach(button => {
        button.addEventListener("click", function () {
            editSentence(this);
        });
    });

    // Слушатель на заголовок "Дополнительные предложения"
    document.getElementById("editSentenceTitle").addEventListener("click", function () {
        expandTailSentencesHandler();
    }); 

    // Слушатель на кнопку "Добавить дополнительное предложение"
    document.getElementById("addTailSentenceButton").addEventListener("click", addTailSentence);

    // Слушатель на кнопку "Добавить главное предложение"
    document.getElementById("addHeadSentenceButton").addEventListener("click", addHeadSentence);

    // Слушатель на кнопку "Удалить дополнительное предложение"
    document.querySelectorAll(".edit-sentence__btn--delete-tail").forEach(button => {
        button.addEventListener("click", function () {
            deleteTailSentence(this);
        });
    });

    // Слушатель на кнопку "Удалить главное предложение"
    document.querySelectorAll(".edit-sentence__btn--delete-head").forEach(button => {
        button.addEventListener("click", function () {
            deleteHeadSentence(this);
        });
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


// Функция редактирования предложения (переход на страницу редактирования)
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


// Функция для добавления нового дополнительного предложения
async function addHeadSentence() {
    const headSentenceList = document.getElementById("editHeadSentenceList");
    const paragraphId = parseInt(headSentenceList.getAttribute("data-paragraph-id"));
    const reportId = document.getElementById("editParagraphContainer").getAttribute("data-report-id");
    const sentences = paragraphData.head_sentences;
    const sentenceIndexes = sentences.map(sentence => sentence.index);
    const maxIndex = findMaxIndex(sentenceIndexes);
    console.log("Максимальный индекс:", maxIndex);
    
    try {
        const response = await sendRequest({
            url: "/editing_report/add_new_sentence",
            method: "POST",
            data: { related_id: paragraphId,
                    report_id: reportId,
                    sentence_index: maxIndex + 1,
                    sentence_type: "head"
             }
        });

        // Создаем новый элемент списка
        const newSentenceHTML = `
            <li class="wrapper__card edit-sentence__item edit-sentence__item--head" 
                data-sentence-id="${response.id}" 
                data-paragraph-id="${paragraphId}"
                data-sentence-type="head" 
                data-sentence-index="${response.index}"
                data-sentence-tags="${response.tags || ""}" 
                data-sentence-comment="${response.comment || ""}">

                <div class="drag-handle">☰</div>
                <div>
                <p class="edit-sentence__text">${response.sentence}</p>
                <p class="edit-paragraph__title--invisible">У данного главного предложения нет дополнительных предложений</p>
                </div>
                <div>
                    <button class="btn report__btn edit-sentence__btn--edit-head" data-sentence-id="${response.id}">Редактировать </button>
                    <button class="btn report__btn edit-sentence__btn--delete-head" data-sentence-id="${response.id}">Удалить </button>
                </div>
            </li>
        `;

        // Находим все <li> кроме кнопки "Добавить предложение"
        const headSentences = headSentenceList.querySelectorAll(".edit-sentence__item--head");
        if (headSentences.length > 0) {
            // Вставляем новый <li> после последнего предложения
            headSentences[headSentences.length - 1].insertAdjacentHTML("afterend", newSentenceHTML);
        } else {
            // Если список пуст, просто добавляем первым элементом
            headSentenceList.insertAdjacentHTML("afterbegin", newSentenceHTML);
        }

        console.log("Новое предложение добавлено:", response);
    } catch (error) {
        console.error("Ошибка запроса:", error);
    }
}


// Функция для добавления нового дополнительного предложения
async function addTailSentence() {
    const tailSentenceList = document.getElementById("editTailSentenceList");
    const paragraphId = tailSentenceList.getAttribute("data-paragraph-id");
    const reportId = document.getElementById("editParagraphContainer").getAttribute("data-report-id");

    try {
        const response = await sendRequest({
            url: "/editing_report/add_new_sentence",
            method: "POST",
            data: { related_id: paragraphId,
                    report_id: reportId,
                    sentence_type: "tail"
             }
        });

        // Создаем новый элемент списка
        const newSentenceHTML = `
            <li class="wrapper__card wrapper__card--tail edit-sentence__item edit-sentence__item--tail" 
                data-sentence-id="${response.id}" 
                data-paragraph-id="${paragraphId}"
                data-sentence-type="tail" 
                data-sentence-weight="${response.weight}"
                data-sentence-tags="${response.tags || ""}" 
                data-sentence-comment="${response.comment || ""}">

                <div>${response.weight}</div>
                <p class="edit-sentence__text">${response.sentence}</p>
                <button class="btn report__btn edit-sentence__btn--delete-tail" type="button">Удалить</button>
            </li>
        `;

        // Находим все <li> кроме кнопки "Добавить предложение"
        const tailSentences = tailSentenceList.querySelectorAll(".edit-sentence__item--tail");
        if (tailSentences.length > 0) {
            // Вставляем новый <li> после последнего предложения
            tailSentences[tailSentences.length - 1].insertAdjacentHTML("afterend", newSentenceHTML);
        } else {
            // Если список пуст, просто добавляем первым элементом
            tailSentenceList.insertAdjacentHTML("afterbegin", newSentenceHTML);
        }

        console.log("Новое предложение добавлено:", response);
    } catch (error) {
        console.error("Ошибка запроса:", error);
    }
}


// Функция удаления дополнительного предложения
async function deleteTailSentence(button) {
    const sentenceItem = button.closest(".edit-sentence__item");
    const sentenceId = sentenceItem.getAttribute("data-sentence-id");
    const paragraphId = sentenceItem.getAttribute("data-paragraph-id");
    

    try {
        const response = await sendRequest({
            url: "/editing_report/delete_sentence",
            method: "DELETE",
            data: { sentence_id: sentenceId,
                    related_id: paragraphId,
                    sentence_type: "tail"
                }
        });

        if (response.status === "success") {
            sentenceItem.remove();
        } 
    } catch (error) {
        console.error("Ошибка запроса:", error);
    }
}

// Функция удаления главного предложения
async function deleteHeadSentence(button) {
    const sentenceItem = button.closest(".edit-sentence__item");
    const sentenceId = sentenceItem.getAttribute("data-sentence-id");
    const paragraphId = sentenceItem.getAttribute("data-paragraph-id");

    try {
        const response = await sendRequest({
            url: "/editing_report/delete_sentence",
            method: "DELETE",
            data: { sentence_id: sentenceId,
                    related_id: paragraphId,
                    sentence_type: "head"
                }
        });

        if (response.status === "success") {
            sentenceItem.remove();
        } 
    } catch (error) {
        console.error("Ошибка запроса:", error);
    }
}


// Вызываемые функции (не требуют инициализации при загрузке страницы)

// Функция сохранения нового порядка главных предложений
function saveHeadSentencesOrder() {
    const allSentences = document.querySelectorAll(".edit-sentence__item--head");
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
    const parentElement = sentenceElement.closest(".edit-sentence__item--head");

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
    const parentElement = sentenceElement.closest(".edit-sentence__item--tail");

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
