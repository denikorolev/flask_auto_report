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


    // Слушатель на кнопку 🗒️
    document.querySelectorAll(".control-btn--copy-to-buffer").forEach(btn => {btn.addEventListener("click", function() {
            addSentenceToBuffer(this);
        });
    });


    // Слушатель на кнопку "✂️"
    document.querySelectorAll(".control-btn--unlink").forEach(btn => {
        btn.addEventListener("click", function() {
            deleteSubsidiaries(this);
        });
    });


    // Слушатель на кнопку 🔗 двойной клик
    document.querySelectorAll(".edit-sentence__title-span").forEach(item => {item.addEventListener("dblclick", function() {
        const itemWrapper = this.closest(".edit-sentence__title-wrapper");
        unlinkGroup(itemWrapper);
        });
    });

    
    // Слушатель на кнопку 🔗 одинарный клик
    document.querySelectorAll(".edit-sentence__title-span").forEach(item => {item.addEventListener("click", function() {
        const itemWrapper = this.closest(".edit-sentence__title-wrapper");
        allowEditing(itemWrapper);
        });
    });



    // Слушатель на кнопку открыть попап буфера
    document.getElementById("openBufferPopupButton").addEventListener("click", function() {
        showBufferPopup(this);
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
    document.querySelectorAll(".control-btn--edit").forEach(button => {
        button.addEventListener("click", function () {
            editSentence(this);
        });
    });


    // Слушатель на кнопку "Добавить дополнительное предложение"
    document.getElementById("addTailSentenceButton").addEventListener("click", function () {
        const itemFromBuffer = null;
        addTailSentence(itemFromBuffer);
    });


    // Слушатель на кнопку "Добавить главное предложение"
    document.getElementById("addHeadSentenceButton").addEventListener("click", function () {
        const itemFromBuffer = null;
        addHeadSentence(itemFromBuffer);
    });


    // Слушатель на кнопку "Удалить предложение"
    document.querySelectorAll(".control-btn--delete").forEach(button => {
        button.addEventListener("click", function () {
            const sentenceType = this.closest(".control-buttons").getAttribute("data-sentence-type");
            if (sentenceType === "tail") {
                deleteTailSentence(this);
            }
            else if (sentenceType === "head") {
                deleteHeadSentence(this);
            }
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



// Функция для редактирования предложений
function makeSentenceEditable(sentenceElement) {
    console.log("Редактирование предложения:", sentenceElement);
    const sentenceItem = sentenceElement.closest(".edit-sentence__item");
    const sentenceType = sentenceItem.getAttribute("data-sentence-type");
    let sentenceGroupTitle = null;
    console.log("Тип предложения:", sentenceType);
    if (sentenceType === "tail") {
        sentenceGroupTitle = document.getElementById("editSentenceTitleTail");
    } else {
        sentenceGroupTitle = document.getElementById("editSentenceTitleHead");
    }
    const sentenceGroupIsLinked = sentenceGroupTitle.getAttribute("data-group-is-linked") === "True";

    const isLinked = sentenceItem.getAttribute("data-sentence-is-linked") === "True";
    const groupIsLinkedIcon = sentenceGroupTitle.querySelector(".edit-sentence__title-span");
    const sentenceIsLinkedIcon = sentenceItem.querySelector(".edit-sentence__links-icon--is-linked");    
    const audioKnock = new Audio("/static/audio/dzzz.mp3");

    // Если есть связи с body 
    if (sentenceGroupIsLinked && groupIsLinkedIcon) {
        createRippleAtElement(groupIsLinkedIcon);
        toastr.warning("Нельзя редактировать: связано с дополнительными предложениями");
        audioKnock.play();
        return;
    }

    // Если связано с другими протоколами
    if (isLinked) {
        createRippleAtElement(sentenceIsLinkedIcon);
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


// Функция показа попапа с буфером
function showBufferPopup(button) {
    const popup = document.getElementById("bufferPopup");

    popup.style.display === "block"
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

        const bodyLinkedIcon = sentenceItem.querySelector(".edit-sentence__links-icon--linked-obj");
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
    const sentenceId = button.closest(".control-buttons").getAttribute("data-object-id");
    const paragraphId = button.closest(".control-buttons").getAttribute("data-related-id");
    const reportId = document.getElementById("editParagraphContainer").getAttribute("data-report-id");

    window.location.href = `/editing_report/edit_head_sentence?sentence_id=${sentenceId}&paragraph_id=${paragraphId}&report_id=${reportId}`;
    
}



// Функция для добавления нового дополнительного предложения
async function addHeadSentence(itemFromBuffer) {
    const headSentenceList = document.getElementById("editHeadSentenceList");
    const paragraphId = parseInt(headSentenceList.getAttribute("data-paragraph-id"));
    const reportId = document.getElementById("editParagraphContainer").getAttribute("data-report-id");
    const sentences = paragraphData.head_sentences;
    const sentenceIndexes = sentences.map(sentence => sentence.sentence_index);
    const maxIndex = findMaxIndex(sentenceIndexes);
    
    if (itemFromBuffer) {
        data = {
            sentence_id: itemFromBuffer.object_id,
            sentence_text: itemFromBuffer.object_text,
            sentence_type: "head",
            related_id: paragraphId,
            report_id: reportId,
            sentence_index: maxIndex + 1
        }; 
    } else {
            data = {
                related_id: paragraphId,
                report_id: reportId,
                sentence_index: maxIndex + 1,
                sentence_type: "head"
            }
    };

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


// Функция для добавления нового дополнительного предложения
async function addTailSentence(itemFromBuffer) {
    const tailSentenceList = document.getElementById("editTailSentenceList");
    const paragraphId = tailSentenceList.getAttribute("data-paragraph-id");
    const reportId = document.getElementById("editParagraphContainer").getAttribute("data-report-id");

    if (itemFromBuffer) {
        data = {
            sentence_id: itemFromBuffer.object_id,
            sentence_text: itemFromBuffer.object_text,
            sentence_type: "tail",
            related_id: paragraphId,
            report_id: reportId
        }; 
    }
    else {
        data = {
            related_id: paragraphId,
            report_id: reportId,
            sentence_type: "tail"
        };
    }


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


// Функция удаления дополнительного предложения
async function deleteTailSentence(button) {
    const sentenceItem = button.closest(".control-buttons");
    const sentenceId = sentenceItem.getAttribute("data-object-id");
    const paragraphId = sentenceItem.getAttribute("data-related-id");
    

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
            sentenceItem.closest(".edit-sentence__item").remove();
        } 
    } catch (error) {
        console.error("Ошибка запроса:", error);
    }
}

// Функция удаления главного предложения
async function deleteHeadSentence(button) {
    const sentenceItem = button.closest(".control-buttons");
    const sentenceId = sentenceItem.getAttribute("data-object-id");
    const paragraphId = sentenceItem.getAttribute("data-related-id");

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
            sentenceItem.closest(".edit-sentence__item").remove();
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



// Функция для добавления группы head предложений в буфер
function addSentenceToBuffer(button) {
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



function deleteSubsidiaries (button) {
    const objectId = button.closest(".control-buttons").getAttribute("data-object-id");
    const objectType = button.closest(".control-buttons").getAttribute("data-object-type");
    const relatedId = button.closest(".control-buttons").getAttribute("data-related-id");
    const sentenceType = button.closest(".control-buttons").getAttribute("data-sentence-type");
    const sentenceGroupId = button.closest(".control-buttons").getAttribute("data-group-id");

    sendRequest({
        url: `/editing_report/delete_subsidiaries`,
        method: "DELETE",
        data: { object_id: objectId, 
            object_type: objectType, 
         }
    }).then(response => {
        window.location.reload();
    }).catch(error => {
        console.error(response.message || "Ошибка удаления дочерних элементов:", error);
    });
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
    }

    if (itemFromBuffer.sentence_type === "head") {
        addHeadSentence(itemFromBuffer);
    }
    else if (itemFromBuffer.sentence_type === "tail") {
        addTailSentence(itemFromBuffer);
    } else {
        alert("Некорректный тип предложения для вставки в данной секции.");
    }

    
}


// Функция для отсоединения группы предложений
function unlinkGroup(itemWrapper) {
    const groupId = itemWrapper.getAttribute("data-group-id");
    const sentenceType = itemWrapper.getAttribute("data-sentence-type");
    const relatedId = itemWrapper.getAttribute("data-related-id");
    

    sendRequest({
        url: "/editing_report/unlink_group",
        method: "PATCH",
        data: { group_id: groupId,
                sentence_type: sentenceType,
                related_id: relatedId
            }
    }).then(response => {
        if (response.status === "success") {
            window.location.reload();
        } else {
            console.error("Ошибка при отсоединении группы:", response.message);
        }
    }
    ).catch(error => {
        console.error("Ошибка при отсоединении группы:", error);
    });
}


// Функция для разрешения редактирования предложения (снимает блок вызванный наличием связей у группы предложений)
function allowEditing(itemWrapper) {
    const groupIsLinked = itemWrapper.getAttribute("data-group-is-linked").toLowerCase();
    const sentenceTitleElement = itemWrapper.querySelector(".edit-sentence__title");

    if (groupIsLinked === "true") {
        itemWrapper.setAttribute("data-group-is-linked", "False");
        sentenceTitleElement.textContent += "(временно разброкировано) 🔓";
        return;
       
    } else if (groupIsLinked === "false") {
        itemWrapper.setAttribute("data-group-is-linked", "True");
        sentenceTitleElement.textContent.replace("(временно разброкировано) 🔓", "");
        sentenceTitleElement.textContent += "(заблокировано) 🔒";
        return;
    }

}
