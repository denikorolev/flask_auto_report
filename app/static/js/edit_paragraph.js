// edit_paragraph.js

document.addEventListener("DOMContentLoaded", function () {

    initSortableHeadSentences(); // Инициализация Sortable для head предложений (изменение индекса перетаскиванием)

    initSortableTailSentences(); // Инициализация Sortable для tail предложений (изменение индекса перетаскиванием)

    initSentencePopupCloseHandlers(); // Инициализация слушателей на закрытие попапа

    document.getElementById("sentenceSearch").addEventListener("input", filterSentencesByText); // Слушатель на поиск предложений по тексту


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


    // Слушатель на кнопку 🔒 (запускает попап для управления связью группы предложений)
    document.querySelectorAll(".edit-sentence__title-span").forEach(item => {
        item.addEventListener("click", function (event) {
            event.stopPropagation();
            const itemWrapper = this.closest(".edit-sentence__title-wrapper");
            showLockPopup(itemWrapper, event);
        });
    });



    // Слушатель на кнопку открыть попап буфера
    document.getElementById("openBufferPopupButton").addEventListener("click", function() {
        showBufferPopup(this);
    });


    // Слушатель на кнопку "Вернуться к редактированию протокола"
    document.getElementById("backToReportButton").addEventListener("click", function () {
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
    const headSentencesList = document.querySelector("#editHeadSentenceList");

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

// Инициализация Sortable для tail предложений
function initSortableTailSentences() {
    const tailSentencesList = document.querySelector("#editTailSentenceList");

    if (!tailSentencesList) {
        console.warn("Список дополнительных предложений не найден.");
        return;
    }

    new Sortable(tailSentencesList, {
        handle: ".drag-handle", // Захват только за "хваталку"
        animation: 150,
        onEnd: function (evt) {
            saveTailSentencesOrder(evt);
        }
    });
}


// Функция для редактирования предложений
function makeSentenceEditable(sentenceElement) {
    const sentenceItem = sentenceElement.closest(".edit-sentence__item");
    const sentenceType = sentenceItem.getAttribute("data-sentence-type");
    
    if (groupIsLocked(sentenceType)) {
        return;
    }
    
    const isLinked = sentenceItem.getAttribute("data-sentence-is-linked") === "True";
    const sentenceIsLinkedIcon = sentenceItem.querySelector(".edit-sentence__links-icon--is-linked");   
    
    // есть ли другие связи у данного предложения
    if (isLinked && sentenceIsLinkedIcon) {
        const audioKnock = new Audio("/static/audio/dzzz.mp3");
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
        // Удаляем универсальный обработчик Enter (если не одноразовый)
        if (sentenceElement._onEnterHandler) {
            sentenceElement.removeEventListener("keydown", sentenceElement._onEnterHandler);
            delete sentenceElement._onEnterHandler;
        }
        const firstGrammaSentenceCheckBox = document.getElementById("firstGrammaSentence").checked;
        const newText = firstGrammaSentenceCheckBox ? firstGrammaSentence(sentenceElement.textContent.trim()) : sentenceElement.textContent.trim();

        const validationResult = validateInputText(newText, 600, 1);
        if (!validationResult.valid) {
            alert(validationResult.message);
            sentenceElement.textContent = oldText; // Возвращаем старый текст
            return;
        }

        if (newText !== oldText) {
            sentenceElement.textContent = newText; // Обновляем текст элемента
            updateSentence(sentenceElement); // Вызов твоей функции обновления
        }
    }

    // Потеря фокуса
    sentenceElement.addEventListener("blur", finishEditing, { once: true });

    // Универсальный обработчик Enter
    const handleEnter = function(e, el) {
        e.preventDefault();
        el.blur();
    };
    sentenceElement._onEnterHandler = handleEnter;
    onEnter(sentenceElement, handleEnter, true);
}


// Функция показа попапа с буфером
function showBufferPopup(button) {
    if (groupIsLocked("head")) {
        return;
    }
    if (groupIsLocked("tail")) {
        return;
    }
    bufferPopupListeners(); // Инициализируем слушатели на кнопки попапа
    refreshBufferPopup(); // Перед открытием — обновить содержимое
    
    const popup = document.getElementById("bufferPopup");
    popup.style.display = "block"
}



function showLockPopup(itemWrapper, event) {
    const popup = document.getElementById("lockPopup");

    // Сохраняем ссылку на текущий wrapper
    popup.dataset.targetWrapperId = itemWrapper.getAttribute("data-wrapper-id") || "";

    // Позиционируем попап
    popup.style.display = "block";
    popup.style.left = `${event.pageX + 10}px`;
    popup.style.top = `${event.pageY + 10}px`;

    // Навешиваем слушатели на кнопки внутри попапа
    const unlinkBtn = document.getElementById("unlinkGroupButton");
    const allowBtn = document.getElementById("allowEditButton");

    unlinkBtn.onclick = function () {
        unlinkGroup(itemWrapper);
        hideElement(popup);
    };

    allowBtn.onclick = function () {
        allowEditing(itemWrapper);
        hideElement(popup);
    };

    // Вешаем временный обработчик клика вне попапа
    function onClickOutside(event) {
        if (!popup.contains(event.target)) {
            hideElement(popup);
            document.removeEventListener("click", onClickOutside);
        }
    }

    // Чуть отложим, чтобы клик по самой иконке не сразу закрыл
    setTimeout(() => {
        document.addEventListener("click", onClickOutside);
    }, 0);

}



/**
 * Инициализация обработчика кнопки "Редактировать" в попапе
 */
function initPopupButtons(sentenceElement, sentenceId) {
    const editButton = document.getElementById("sentencePopupEditButton");
    const unlinkButton = document.getElementById("sentencePopupUnlinkButton");
    if (!editButton) {
        console.error("Кнопка 'Редактировать' в попапе не найдена!");
        return;
    }

    if (!unlinkButton) {
        console.error("Кнопка 'Разорвать связь' в попапе не найдена!");
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


        // Меняем иконки замков и линков
        const linkedIcon = sentenceItem.querySelector(".edit-sentence__links-icon--is-linked");
        if (linkedIcon) linkedIcon.remove(); // Удаляем иконку связи

        const bodyLinkedIcon = sentenceItem.querySelector(".edit-sentence__links-icon--linked-obj");
        if (bodyLinkedIcon) bodyLinkedIcon.remove(); // Удаляем иконку body

        // Запускаем редактирование предложения
        makeSentenceEditable(sentenceElement);

        // Закрываем попап
        const popup = document.getElementById("sentencePopup");
        hideElement(popup);
    });

    unlinkButton.addEventListener("click", function () {
        // Находим элемент предложения
        const sentenceItem = document.querySelector(`.edit-sentence__item[data-sentence-id="${sentenceId}"]`);

        if (!sentenceItem || !sentenceElement) {
            console.error(`Предложение с ID=${sentenceId} не найдено!`);
            return;
        }

        // Разблокируем редактирование: убираем атрибуты связанности
        sentenceItem.setAttribute("data-sentence-is-linked", "False");
        

        // Меняем иконки замков и линков
        const linkedIcon = sentenceItem.querySelector(".edit-sentence__links-icon--is-linked");
        if (linkedIcon) linkedIcon.remove(); // Удаляем иконку связи

        // Отвязываем предложение путем создания нового предложения
        unlinkSentence(sentenceItem);

        // Закрываем попап
        const popup = document.getElementById("sentencePopup");
        hideElement(popup);
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
    const closeButton = popup.querySelector("#closeSentencePopupButton");

    if (!popup) {
        console.error("Попап или кнопка закрытия не найдены!");
        return;
    }

    // Закрытие по кнопке
    closeButton.addEventListener("click", () => hideElement(popup));

    // Закрытие при клике вне попапа
    document.addEventListener("click", function (event) {
        if (popup.style.display === "block" && !popup.contains(event.target)) {
            hideElement(popup);
        }
    });

    // ❗ Закрытие при начале ввода текста
    document.querySelectorAll(".edit-sentence__text").forEach(sentence => {
        sentence.addEventListener("input", function () {
            if (popup.style.display === "block") {
                hideElement(popup);
            }
        });
    });
}



// Функция редактирования предложения (переход на страницу редактирования)
function editSentence(button) {
    const sentenceType = button.closest(".edit-sentence__item").getAttribute("data-sentence-type");
    
    if (groupIsLocked(sentenceType)) {
        return;
    }
    
    const sentenceId = button.closest(".control-buttons").getAttribute("data-object-id");
    const paragraphId = button.closest(".control-buttons").getAttribute("data-related-id");
    const reportId = reportInfo.id;

    window.location.href = `/editing_report/edit_head_sentence?sentence_id=${sentenceId}&paragraph_id=${paragraphId}&report_id=${reportId}`;
    
}


// Функция для добавления нового дополнительного предложения
async function addHeadSentence(itemFromBuffer) {
    // Проверяю не заблокирована ли данная группа предложений
    const sentenceType = "head";
    if (groupIsLocked(sentenceType)) {
        return;
    }
    
    const headSentenceList = document.getElementById("editHeadSentenceList");
    const paragraphId = parseInt(headSentenceList.getAttribute("data-paragraph-id"));
    const reportId = reportInfo.id;
    const sentences = paragraphData.head_sentences;
    const sentenceIndexes = sentences.map(sentence => sentence.sentence_index);
    const maxIndex = findMaxIndex(sentenceIndexes);
    const uniqueSentence = !document.getElementById("useDuplicate").checked;
    
    if (itemFromBuffer) {
        data = {
            sentence_id: itemFromBuffer.object_id,
            sentence_text: itemFromBuffer.object_text,
            sentence_type: "head",
            related_id: paragraphId,
            report_id: reportId,
            sentence_index: maxIndex + 1,
            unique: false,
            
        }; 
    } else {
            data = {
                related_id: paragraphId,
                report_id: reportId,
                sentence_index: maxIndex + 1,
                sentence_type: "head",
                unique: uniqueSentence
            }
    };

    try {
        const response = await sendRequest({
            url: "/editing_report/add_new_sentence",
            method: "POST",
            data: data
        });

        if (response.status === "success") {
            console.log("Успешно добавлено новое предложение:", response);
            window.location.reload();
        } 
    } catch (error) {
        console.error("Ошибка запроса:", error);
    }
}


// Функция для добавления нового дополнительного предложения
async function addTailSentence(itemFromBuffer) {
    // Проверяю не заблокирована ли данная группа предложений
    const sentenceType = "tail";
    if (groupIsLocked(sentenceType)) {
        return;
    }


    const tailSentenceList = document.getElementById("editTailSentenceList");
    const paragraphId = tailSentenceList.getAttribute("data-paragraph-id");
    const reportId = reportInfo.id;
    const uniqueSentence = !document.getElementById("useDuplicate").checked;

    if (itemFromBuffer) {
        data = {
            sentence_id: itemFromBuffer.object_id,
            sentence_text: itemFromBuffer.object_text,
            sentence_type: "tail",
            related_id: paragraphId,
            report_id: reportId,
            unique: false,
        }; 
    }
    else {
        data = {
            related_id: paragraphId,
            report_id: reportId,
            sentence_type: "tail",
            unique: uniqueSentence
        };
    }


    try {
        const response = await sendRequest({
            url: "/editing_report/add_new_sentence",
            method: "POST",
            data: data
        });

        
        if (response.status === "success") {
            console.log("Успешно добавлено новое предложение:", response);
            window.location.reload();
        } 
    } catch (error) {
        console.error("Ошибка запроса:", error);
    }
}

function groupIsLocked(sentenceType) {
    const listId = sentenceType === "head" ? "editHeadSentenceList" : "editTailSentenceList";
    const titleListId = sentenceType === "head" ? "editSentenceTitleHead" : "editSentenceTitleTail";
    const sentenceList = document.getElementById(listId);
    const sentenceListTitle = document.getElementById(titleListId);
    const groupIsLocked = sentenceList.getAttribute("data-locked") === "True";
    
    if (groupIsLocked) {
        const audioKnock = new Audio("/static/audio/dzzz.mp3");
        const groupIsLinkedIcon = sentenceListTitle.querySelector(".edit-sentence__title-span");
        createRippleAtElement(groupIsLinkedIcon);
        audioKnock.play();
        toastr.warning("Осторожно! Данная группа предложений связана с другими протоколами.");
        return true;
    }
    return false;
}

function sentenceIsLocked(sentenceType) {

}


// Функция удаления дополнительного предложения
async function deleteTailSentence(button) {
    const sentenceType = button.closest(".edit-sentence__item").getAttribute("data-sentence-type");
    const sentenceItem = button.closest(".edit-sentence__item");
    
    if (groupIsLocked(sentenceType)) {
        return;
    }
    
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
            sentenceItem.closest(".edit-sentence__item").remove();
        } 
    } catch (error) {
        console.error("Ошибка запроса:", error);
    }
}

// Функция удаления главного предложения
async function deleteHeadSentence(button) {
    const sentenceType = button.closest(".edit-sentence__item").getAttribute("data-sentence-type");
    const sentenceItem = button.closest(".edit-sentence__item");
    
    if (groupIsLocked(sentenceType)) {
        return;
    }
    
    const confirmation = confirm("Вы уверены, что хотите удалить это предложение?");
    if (!confirmation) {
        return; 
    }


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
        } else {
            console.error("Ошибка при сохранении порядка:", response.message);
        }
    });
}

// Функция для сохранения порядка tail предложений (меняет вес предложения на вес предыдущего + 1)
function saveTailSentencesOrder(evt) {
    const movedItem = evt.item;
    const sentenceId = movedItem.getAttribute("data-sentence-id");
    const groupId = movedItem.getAttribute("data-sentence-group-id");
    const sentenceType = movedItem.getAttribute("data-sentence-type");

    let newWeight = 1; // значение по умолчанию

    // Ищем предыдущий элемент в списке
    const prevItem = movedItem.nextElementSibling;


    if (prevItem && prevItem.hasAttribute("data-sentence-weight")) {
        const prevWeight = parseInt(prevItem.getAttribute("data-sentence-weight")) || 0;
        newWeight = prevWeight + 1;
    }

    sendRequest({
        url: "/editing_report/update_sentence_weight",
        method: "PATCH",
        data: {
            sentence_id: sentenceId,
            group_id: groupId,
            sentence_weight: newWeight,
            sentence_type: sentenceType
        }
    }).then(response => {
        if (response.status === "success") {
            window.location.reload();
        } else {
            console.error("Ошибка при обновлении веса:", response.message);
        }
    }).catch(error => {
        console.error("Ошибка запроса:", error);
    });
}



// Функция отправки обновленного текста предложения на сервер
async function updateSentence(sentenceElement) {
    const sentenceId = sentenceElement.closest("li").getAttribute("data-sentence-id");
    const sentenceType = sentenceElement.closest("li").getAttribute("data-sentence-type");
    const groupId = sentenceElement.closest("li").getAttribute("data-sentence-group-id"); // id группы через параграф
    const sentenceText = sentenceElement.textContent.trim();
    const related_id = sentenceElement.closest("li").getAttribute("data-paragraph-id");
    const aiGrammaCheck = document.getElementById("grammaAiChecker").checked;
    const useDublicate = document.getElementById("useDuplicate").checked;
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
                ai_gramma_check: aiGrammaCheck,
                use_dublicate: useDublicate
            }
        });

        if (response.status === "success" && aiGrammaCheck) {
            window.location.reload();
        }

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
        group_id: sentenceGroupId,
        report_modality: reportInfo.global_category_id, 
        report_modality_name: reportInfo.category_1_name


    };

    addToBuffer(dataToBuffer);
    toastr.success("Предложение добавлено в буфер", "Успех")

}



function deleteSubsidiaries (button) {
    const sentenceType = button.closest(".edit-sentence__item").getAttribute("data-sentence-type");
    
    if (groupIsLocked(sentenceType)) {
        return;
    }

    const confirmation = confirm("Вы уверены, что хотите удалить дочерние элементы?");
    if (!confirmation) {
        return;
    }


    const objectId = button.closest(".control-buttons").getAttribute("data-object-id");
    const objectType = button.closest(".control-buttons").getAttribute("data-object-type");
    const relatedId = button.closest(".control-buttons").getAttribute("data-related-id");
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
    const bufferReportModality = parseInt(itemFromBuffer.report_modality);
    const globalReportModality = parseInt(reportInfo.global_category_id);

    if (!itemFromBuffer) {
        console.error("Элемент из буфера не найден.");
        return;
    }

    if (bufferReportModality !== globalReportModality) {
        alert("Нельзя вставить предложение принадлежащее другому типу протокола (например нельзя вставить предложение из протокола с типом КТ в протокол с типом МРТ).");
        return;
    }

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
    // Меняем статус группы на разблокированную
    itemWrapper.setAttribute("data-group-is-linked", "False");
    itemWrapper.querySelector(".edit-sentence__title").textContent = "Главные предложения (разблокировано)";

    // Скрываем иконку замка
    const lockIcon = itemWrapper.querySelector(".edit-sentence__title-span");
    if (lockIcon) {
        lockIcon.style.display = "none";
    }

    // Находим соответствующий список и снимаем блокировку
    const groupType = itemWrapper.getAttribute("data-sentence-type");
    const listId = groupType === "head" ? "editHeadSentenceList" : "editTailSentenceList";
    const sentenceList = document.getElementById(listId);
    sentenceList.setAttribute("data-locked", "False");
}



// Функция поиска предложений по словам в тексте
function filterSentencesByText() {
    const searchText = document.getElementById("sentenceSearch").value.toLowerCase().trim();
    const searchWords = searchText.split(/\s+/);  // Разбиваем слова в поле поиска по пробелам
    const sentences = document.querySelectorAll(".edit-sentence__item");

    sentences.forEach(item => {
        const sentenceText = item.querySelector(".edit-sentence__text").textContent.toLowerCase();
        const isMatch = searchWords.every(word => sentenceText.includes(word));
        item.style.display = isMatch ? "flex" : "none";
    });
}


// Функция для удаления связей предолжений путем создания нового предложения
function unlinkSentence(sentenceItem) {
    const sentenceId = sentenceItem.getAttribute("data-sentence-id");
    const sentenceType = sentenceItem.getAttribute("data-sentence-type");
    const related_id = sentenceItem.getAttribute("data-paragraph-id");
    const sentenceIndex = sentenceType === "head" ? sentenceItem.getAttribute("data-sentence-index") : sentenceItem.getAttribute("data-sentence-weight");
    const groupId = sentenceItem.getAttribute("data-sentence-group-id");

    sendRequest({
        url: "/editing_report/unlink_sentence",
        method: "POST",
        data: {
            sentence_id: sentenceId,
            sentence_type: sentenceType,
            related_id: related_id,
            sentence_index: sentenceIndex,
            group_id: groupId
        }
    }).then(response => {
        if (response.status === "success") {
            window.location.reload();
        } else {
            console.error("Ошибка при удалении связи предложения:", response.message);
        }
    }).catch(error => {
        console.error("Ошибка удаления связи предложения:", error);
    });
}