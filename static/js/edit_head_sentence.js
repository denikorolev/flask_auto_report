// edit_head_sentence.js

document.addEventListener("DOMContentLoaded", function () {

    initSentencePopupCloseHandlers(); // Инициализация слушателей на закрытие попапа


    // Инициализация слушателей двойного клика на предложения для показа попапа
    document.querySelectorAll(".edit-sentence__text").forEach(sentence => {
        sentence.addEventListener("dblclick", function (event) {
            event.stopPropagation();
            showSentencePopup(this, event);
        });
    });


    // Слушатель на клик по тексту предложения чтобы сделать его редактируемым
    document.querySelectorAll(".edit-sentence__text").forEach(sentenceText => {
        sentenceText.addEventListener("click", function (event) {
            event.stopPropagation();
            makeSentenceEditable(this);
        });
    });


    // Слушатель на кнопку 🗒️
    document.querySelectorAll(".control-btn--copy-to-buffer").forEach(btn => {btn.addEventListener("click", function() {
            addSentenceDataToBuffer(this);
        });
    });


    // Слушатель на кнопку открыть попап буфера
    document.getElementById("openBufferPopupButton").addEventListener("click", function() {
        showBufferPopup(this);
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


    // Cлушатель для кнопки "Добавить дополнительное предложение"
    document.getElementById("addBodySentenceButton").addEventListener("click", function () {
        const itemFromBuffer = null;
        addBodySentence(itemFromBuffer);
    });


    // Слушатель на кнопку "Удалить предложение"
    document.querySelectorAll(".control-btn--delete").forEach(button => {
        button.addEventListener("click", function () {
            deleteBodySentence(this);
        });
    });

});


// Функция для добавления нового дополнительного предложения
async function addBodySentence(itemFromBuffer) {
    const bodySentenceList = document.getElementById("bodySentenceList");
    const headSentenceId = bodySentenceList.getAttribute("data-head-sentence-id");
    const reportId = document.getElementById("editSentenceContainer").getAttribute("data-report-id");

    data = {
        related_id: headSentenceId,
        report_id: reportId,
        sentence_type: "body"
    }

    if (itemFromBuffer) {
        // Если есть данные из буфера, используем их
        data.sentence_id = itemFromBuffer.object_id;
    }

    console.log("Отправка запроса на добавление нового предложения:", data);

    try {
        const response = await sendRequest({
            url: "/editing_report/add_new_sentence",
            method: "POST",
            data: data
        });

        if (response.status === "success") {
            window.location.reload();
        } 
            
    } catch (error) {
        console.error("Ошибка запроса:", error);
    }
}



function makeSentenceEditable(sentenceElement) {
    const sentenceItem = sentenceElement.closest(".edit-sentence__item");
    const sentenceType = sentenceItem.getAttribute("data-sentence-type");

    const sentenceGroupTitle = document.getElementById("editSentenceTitleBody");

    const sentenceGroupIsLinked = sentenceGroupTitle.getAttribute("data-group-is-linked") === "True";
    const groupIsLinkedIcon = sentenceGroupTitle.querySelector(".edit-sentence__title-span");

    const isLinked = sentenceItem.getAttribute("data-sentence-is-linked") === "True";
    const sentenceIsLinkedIcon = sentenceItem.querySelector(".edit-sentence__links-icon--is-linked");   

    const audioLocked = new Audio("/static/audio/dzzz.mp3");

    if(sentenceGroupIsLinked && groupIsLinkedIcon) {
        audioLocked.play();
        toastr.warning("Нельзя редактировать - это связанная группа предложений");
        // Запускаем анимацию вокруг значка 🔗
        createRippleAtElement(groupIsLinkedIcon);
        return;
    }


    if (isLinked && sentenceIsLinkedIcon) {
        audioLocked.play();
        toastr.warning("Нельзя редактировать - это связанное предложение");
        // Запускаем анимацию вокруг значка 🔗
        createRippleAtElement(sentenceIsLinkedIcon);
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

        const bodyLinkedIcon = sentenceItem.querySelector("control-info-icons .edit-sentence__links-icon--linked-obj");
        if (bodyLinkedIcon) bodyLinkedIcon.remove(); // Удаляем иконку body

        // Запускаем редактирование предложения
        makeSentenceEditable(sentenceElement);

        // Закрываем попап
        hideSentencePopup();
    });
}


// Функция показа попапа с буфером
function showBufferPopup(button) {
    const popup = document.getElementById("bufferPopup");

    popup.style.display === "block"
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

    // Функция скрытия попапа
    function hidePopup() {
        popup.style.display = "none";
    }

    // Закрытие по кнопке
    closeButton.addEventListener("click", hidePopup);

    // Закрытие при клике вне попапа
    document.addEventListener("click", function (event) {
        if (popup.style.display === "block" && !popup.contains(event.target)) {
            hidePopup();
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


// Вызываемые функции (не требуют инициализации при загрузке страницы)


// Функция удаления дополнительного предложения
async function deleteBodySentence(button) {
    const sentenceItem = button.closest(".control-buttons");
    const sentenceId = sentenceItem.getAttribute("data-object-id");
    const headSentenceId = sentenceItem.getAttribute("data-related-id");

    try {
        const response = await sendRequest({
            url: "/editing_report/delete_sentence",
            method: "DELETE",
            data: { sentence_id: sentenceId,
                    related_id: headSentenceId,
                    sentence_type: "body"
                }
        });

        if (response.status === "success") {
            sentenceItem.closest(".edit-sentence__item").remove();
        } 
    } catch (error) {
        console.error("Ошибка запроса:", error);
    }
}


// Функция отправки обновленного текста предложения на сервер
async function updateSentence(sentenceElement) {
    const sentenceId = sentenceElement.closest("li").getAttribute("data-sentence-id");
    const sentenceType = sentenceElement.closest("li").getAttribute("data-sentence-type");
    const groupId = sentenceElement.closest("li").getAttribute("data-sentence-group-id"); // id группы через параграф
    const sentenceText = sentenceElement.textContent.trim();
    const related_id = sentenceElement.closest("li").getAttribute("data-head-sentence-id");
    const hardEdit = sentenceElement.closest("li").getAttribute("data-sentence-hard-edit");


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


// Функция для добавления предложения в буфер
function addSentenceDataToBuffer(button) {
    const objectId = button.closest(".control-buttons").getAttribute("data-object-id");
    const objectType = button.closest(".control-buttons").getAttribute("data-object-type");
    const relatedId = button.closest(".control-buttons").getAttribute("data-related-id");
    const objectText = button.closest(".control-buttons").getAttribute("data-text");
    const sentenceType = button.closest(".control-buttons").getAttribute("data-sentence-type");
    const sentenceGroupId = button.closest(".control-buttons").getAttribute("data-group-id");

    dataToBuffer = {
        object_id: objectId,
        object_type: objectType,
        related_id: relatedId,
        object_text: objectText,
        sentence_type: sentenceType,
        group_id: sentenceGroupId
    };

    addToBuffer(dataToBuffer);
    console.log("Добавление в буфер:", dataToBuffer);
}


// Функция для вставки предложения из буфера, буду использовать функцию создания нового предложения, но с данными из буфера
function insertFromBuffer(index) {
    const itemFromBuffer = getFromBuffer(index);
    if (!itemFromBuffer) {
        console.error("Элемент из буфера не найден.");
        return;
    }
    console.log("Вставка из буфера:", itemFromBuffer);

    if (itemFromBuffer.object_type === "paragraph") {
        alert("Нельзя вставить параграф в данной секции.");
        return;
    } else if (itemFromBuffer.sentence_type != "body") {
        alert("Нельзя вставить head или tail предложение в данной секции.");
        return
    }
    
    addBodySentence(itemFromBuffer);
    
}