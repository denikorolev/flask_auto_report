// edit_paragraph.js

document.addEventListener("DOMContentLoaded", function () {

    initSortableHeadSentences(); // Инициализация Sortable для главных предложений (изменение индекса перетаскиванием)

    initSentencePopupCloseHandlers(); // Инициализация слушателей на закрытие попапа


    // Инициализация слушателей двойного клика на предложения для показа попапа
    document.querySelectorAll(".edit-sentence__text").forEach(sentence => {
        sentence.addEventListener("dblclick", function (event) {
            event.stopPropagation();
            showSentencePopup(this, event);
        });
    });





    // Слушатель на кнопку "Вернуться к редактированию протокола"
    document.getElementById("backToReportButton").addEventListener("click", function () {
        console.log("Back to report button clicked");
        window.history.back();
    });
    


    // Инициализация слушателей на предложения для редактирования текста при клике
    document.querySelectorAll(".edit-sentence__text").forEach(sentence => {
        sentence.addEventListener("click", function (event) {
            event.stopPropagation(); // Остановим всплытие
            makeSentenceEditable(this, event); // Запускаем редактирование
        });
    });
    

    // Слушатель на кнопку "Редактировать предложение" (переход на страницу редактирования)
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



// Функция для редактирования предложений с разблокировкой на тройной клик
function makeSentenceEditable(sentenceElement) {
    const sentenceItem = sentenceElement.closest(".edit-sentence__item");
    const isLinked = sentenceItem.getAttribute("data-sentence-is-linked") === "True";
    const hasLinkedBody = sentenceItem.getAttribute("data-sentence-has-linked-body") === "True";
    const linkedBodyIcon = sentenceItem.querySelector(".edit-sentence__links-icon--linked-body");
    const linkedIcon = sentenceItem.querySelector(".edit-sentence__links-icon--is-linked");
    const audioKnock = new Audio("/static/audio/dzzz.mp3");

    // Если есть связи с body 
    if (hasLinkedBody && linkedBodyIcon) {
        createRippleAtElement(linkedBodyIcon);
        toastr.warning("Нельзя редактировать: связано с дополнительными предложениями");
        audioKnock.play();
        return;
    }

    // Если связано с другими протоколами
    if (isLinked) {
        createRippleAtElement(linkedIcon);
        toastr.warning("Нельзя редактировать: связано с другими протоколами. ");
        audioKnock.play();
        return;
    }

    // Если уже редактируется — выходим
    if (sentenceElement.getAttribute("contenteditable") === "true") return;

    // Иначе — разрешаем редактирование
    sentenceElement.setAttribute("contenteditable", "true");
    sentenceElement.focus();
    makeSentenceEditableActions(sentenceElement);
}


// Вспомогательная функция завершения редактирования вызывается из makeSentenceEditable
function makeSentenceEditableActions(sentenceElement) {
    const oldText = sentenceElement.textContent.trim();

    function finishEditing() {
        sentenceElement.setAttribute("contenteditable", "false");
        sentenceElement.removeEventListener("keydown", onEnterPress);

        const newText = sentenceElement.textContent.trim();
        if (newText !== oldText) {
            updateSentence(sentenceElement); // Вызов твоей функции обновления
        }
    }

    // Потеря фокуса
    sentenceElement.addEventListener("blur", finishEditing, { once: true });

    // Enter для сохранения
    function onEnterPress(event) {
        if (event.key === "Enter") {
            event.preventDefault();
            sentenceElement.blur();
        }
    }

    sentenceElement.addEventListener("keydown", onEnterPress);
}



/**
 * Инициализация обработчика кнопки "Редактировать" в попапе
 */
function initPopupButtons(sentenceElement, sentenceId) {
    const editButton = document.getElementById("sentencePopupEditButton");
    const hardEditCheckbox = document.getElementById("hardEditCheckbox");
    if (!editButton) {
        console.error("Кнопка 'Редактировать' в попапе не найдена!");
        return;
    }

    editButton.addEventListener("click", function () {
        // Находим элемент предложения
        const sentenceItem = document.querySelector(`.edit-sentence__item[data-sentence-id="${sentenceId}"]`);

        if (!sentenceItem || !sentenceElement) {
            console.error(`Предложение с ID=${sentenceId} не найдено!`);
            return;
        }

        // Разблокируем редактирование: убираем атрибуты связанности
        sentenceItem.setAttribute("data-sentence-is-linked", "False");
        sentenceItem.setAttribute("data-sentence-has-linked-body", "False");

        // Если чекбокс "жесткое редактирование" отмечен — устанавливаем флаг
        if (hardEditCheckbox.checked) {
            sentenceItem.setAttribute("data-sentence-hard-edit", "True");
        }

        // Меняем иконки замков и линков
        const linkedIcon = sentenceItem.querySelector(".edit-sentence__links-icon--is-linked");
        if (linkedIcon) linkedIcon.remove(); // Удаляем иконку связи

        const bodyLinkedIcon = sentenceItem.querySelector(".edit-sentence__links-icon--linked-body");
        if (bodyLinkedIcon) bodyLinkedIcon.remove(); // Удаляем иконку body

        // Запускаем редактирование предложения
        makeSentenceEditable(sentenceElement);

        // Закрываем попап
        hideSentencePopup();
    });
}



// Функция показа попапа с информацией о предложении
function showSentencePopup(sentenceElement, event) {
    const popup = document.getElementById("sentencePopup");

    // Получаем данные из атрибутов
    const sentenceId = sentenceElement.closest("li").getAttribute("data-sentence-id");
    const sentenceIndex = sentenceElement.closest("li").getAttribute("data-sentence-index");
    const sentenceComment = sentenceElement.closest("li").getAttribute("data-sentence-comment") || "None";
    const sentenceTags = sentenceElement.closest("li").getAttribute("data-sentence-tags") || "None";

    // Заполняем попап
    document.getElementById("popupSentenceId").textContent = sentenceId;
    document.getElementById("popupSentenceIndex").textContent = sentenceIndex;
    document.getElementById("popupSentenceComment").textContent = sentenceComment;
    document.getElementById("popupSentenceTags").textContent = sentenceTags;

    // Проверяем и скрываем, если значение None, пустое или null
    document.querySelectorAll(".sentence-popup__info-item").forEach(item => {
        const value = item.querySelector("span").textContent.trim();
        if (!value || value === "None") {
            item.style.display = "none";
        } else {
            item.style.display = "block"; // Показываем обратно, если были скрыты до этого
        }
    });

    // Инициализация обработчика кнопки "Редактировать"
    initPopupButtons(sentenceElement, sentenceId);

    // Показываем попап
    popup.style.display = "block";

    // Позиция попапа
    const popupWidth = popup.offsetWidth;
    const popupHeight = popup.offsetHeight;
    let posX = event.pageX + 15;
    let posY = event.pageY + 15;

    if (posX + popupWidth > window.innerWidth) {
        posX -= popupWidth + 30;
    }
    if (posY + popupHeight > window.innerHeight) {
        posY -= popupHeight + 30;
    }

    popup.style.left = `${posX}px`;
    popup.style.top = `${posY}px`;
}


/** 
 * Инициализация обработчиков закрытия попапа предложения
 */
function initSentencePopupCloseHandlers() {
    const popup = document.getElementById("sentencePopup");
    const closeButton = document.getElementById("closeSentencePopup");

    if (!popup || !closeButton) {
        console.error("Попап или кнопка закрытия не найдены!");
        return;
    }

    // Закрытие по кнопке
    closeButton.addEventListener("click", hideSentencePopup);

    // Закрытие при клике вне попапа
    document.addEventListener("click", function (event) {
        if (popup.style.display === "block" && !popup.contains(event.target)) {
            hideSentencePopup();
        }
    });
}


/**
 * Hides the sentence popup.
 */
function hideSentencePopup() {
    const popup = document.getElementById("sentencePopup");
    if (popup) {
        popup.style.display = "none";
    } else {
        console.warn("Попап для предложения не найден.");
    }
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
    console.log("Данные с сервера:", paragraphData);
    console.log("Предложения:", sentences);
    const sentenceIndexes = sentences.map(sentence => sentence.sentence_index);
    console.log("Индексы предложений:", sentenceIndexes);
    console.log("Индексы предложений:", sentenceIndexes);
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
    const paragraphId = document.getElementById("editParagraphContainer").getAttribute("data-paragraph-id");

    console.log("Параграф ID:", paragraphId);
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
        data: { updated_order: updatedOrder,
                paragraph_id: paragraphId 
            }
    }).then(response => {
        if (response.status === "success") {
            window.location.reload();
            console.log("Порядок главных предложений успешно сохранен");
        } else {
            console.error("Ошибка при сохранении порядка:", response.message);
        }
    });
}




// Функция отправки обновленного текста предложения на сервер
async function updateSentence(sentenceElement) {
    const sentenceId = sentenceElement.closest("li").getAttribute("data-sentence-id");
    const sentenceType = sentenceElement.closest("li").getAttribute("data-sentence-type");
    const groupId = sentenceElement.closest("li").getAttribute("data-sentence-group-id"); // id группы через параграф
    const sentenceText = sentenceElement.textContent.trim();
    const related_id = sentenceElement.closest("li").getAttribute("data-paragraph-id");
    const hardEdit = sentenceElement.closest("li").getAttribute("data-sentence-hard-edit");

    console.log("Отправка обновленного предложения:", sentenceText);

    try {
        const response = await sendRequest({
            url: "/editing_report/update_sentence_text",
            method: "PATCH",
            data: {
                sentence_id: sentenceId,
                sentence_type: sentenceType,
                group_id: groupId,
                sentence_text: sentenceText,
                related_id: related_id,
                hard_edit: hardEdit
            }
        });

        console.log("Предложение обновлено:", response);
    } catch (error) {
        console.error("Ошибка обновления предложения:", error);
    }
}



