// edit_head_sentence.js

document.addEventListener("DOMContentLoaded", function () {

    initSortableBodySentences(); // Инициализация Sortable для head предложений (изменение индекса перетаскиванием)

    initSentencePopupCloseHandlers(); // Инициализация слушателей на закрытие попапа

    document.getElementById("sentenceSearch").addEventListener("input", filterSentencesByText); // Слушатель на поиск предложений по тексту


    // Слушатель на кнопку 🔒 (запускает попап для управления связью группы предложений)
    document.querySelectorAll(".edit-sentence__title-span").forEach(item => {
        item.addEventListener("click", function (event) {
            event.stopPropagation();
            const itemWrapper = this.closest(".edit-sentence__title-wrapper");
            showLockPopup(itemWrapper, event);
        });
    });


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
        window.history.back();
    });

    // Слушатель на кнопку "Вернуться к редактированию протокола"
    document.getElementById("backToReportButton").addEventListener("click", function () {
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


// Инициализация Sortable для tail предложений
function initSortableBodySentences() {
    const bodySentencesList = document.querySelector("#editBodySentenceList");

    if (!bodySentencesList) {
        console.warn("Список дополнительных предложений не найден.");
        return;
    }

    new Sortable(bodySentencesList, {
        handle: ".drag-handle", // Захват только за "хваталку"
        animation: 150,
        onEnd: function (evt) {
            saveBodySentencesOrder(evt);
        }
    });
}



// Функция для добавления нового дополнительного предложения
async function addBodySentence(itemFromBuffer) {
    // Проверяем, заблокирована ли группа предложений
    if (isLocked()) return;

    const bodySentenceList = document.getElementById("editBodySentenceList");
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

    try {
        const response = await sendRequest({
            url: "/editing_report/add_new_sentence",
            method: "POST",
            data: data
        });

        if (response.status === "success") {
            console.log("Предложение успешно добавлено:", response.data);
        } 
            
    } catch (error) {
        console.error("Ошибка запроса:", error);
    }
}



function makeSentenceEditable(sentenceElement) {
    // Проверяем, заблокирована ли группа предложений
    if (isLocked()) return;

    const sentenceItem = sentenceElement.closest(".edit-sentence__item");

    const isLinked = sentenceItem.getAttribute("data-sentence-is-linked") === "True";
    const sentenceIsLinkedIcon = sentenceItem.querySelector(".edit-sentence__links-icon--is-linked");   

    if (isLinked && sentenceIsLinkedIcon) {
        const audioLocked = new Audio("/static/audio/dzzz.mp3");
        audioLocked.play();
        toastr.warning("Нельзя редактировать - это связанное предложение");
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
    


function isLocked() {
    const sentenceList = document.getElementById("editBodySentenceList");
    const sentenceListTitle = document.getElementById("editSentenceTitleBody");
    const isLocked = sentenceList.getAttribute("data-locked") === "True";
    
    if (isLocked) {
        const audioKnock = new Audio("/static/audio/dzzz.mp3");
        const groupIsLinkedIcon = sentenceListTitle.querySelector(".edit-sentence__title-span");
        createRippleAtElement(groupIsLinkedIcon);
        audioKnock.play();
        toastr.warning("Осторожно! Данная группа предложений связана с другими протоколами.");
        return true;
    }
    return false;
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
        hidePopup(popup);
    };

    allowBtn.onclick = function () {
        allowEditing(itemWrapper);
        hidePopup(popup);
    };

    // Вешаем временный обработчик клика вне попапа
    function onClickOutside(event) {
        if (!popup.contains(event.target)) {
            hidePopup(popup);
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
        console.error("Кнопка 'Отвязать' в попапе не найдена!");
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

        const bodyLinkedIcon = sentenceItem.querySelector("control-info-icons .edit-sentence__links-icon--linked-obj");
        if (bodyLinkedIcon) bodyLinkedIcon.remove(); // Удаляем иконку body

        // Запускаем редактирование предложения
        makeSentenceEditable(sentenceElement);

        // Закрываем попап
        hideSentencePopup();
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
        hidePopup(popup);
    });
}


// Функция показа попапа с буфером
function showBufferPopup(button) {
    // Проверяем, заблокирована ли группа предложений
    if (!isLocked()) {
        
        bufferPopupListeners(); // Инициализация слушателей для буфера
        refreshBufferPopup(); // Обновляем содержимое попапа

        const popup = document.getElementById("bufferPopup");
        popup.style.display = "block"
    }   
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


// Инициализация обработчиков закрытия попапа предложения
function initSentencePopupCloseHandlers() {
    const popup = document.getElementById("sentencePopup");
    const closeButton = popup.querySelector("#closeSentencePopupButton");

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

    // ❗ Закрытие при начале ввода текста
    document.querySelectorAll(".edit-sentence__text").forEach(sentence => {
        sentence.addEventListener("input", function () {
            if (popup.style.display === "block") {
                hideSentencePopup();
            }
        });
    });
}

// Hides the sentence popup.
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
    // Проверяем, заблокирована ли группа предложений
    if (isLocked()) return;

    const sentenceItem = button.closest(".edit-sentence__item");
    const sentenceId = sentenceItem.getAttribute("data-sentence-id");
    const headSentenceId = sentenceItem.getAttribute("data-head-sentence-id");

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
            }
        });

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
    const reportType = button.closest(".control-buttons").getAttribute("data-report-type");

    dataToBuffer = {
        object_id: objectId,
        object_type: objectType,
        related_id: relatedId,
        object_text: objectText,
        sentence_type: sentenceType,
        group_id: sentenceGroupId,
        report_type: reportType
    };

    addToBuffer(dataToBuffer);
}


// Функция для вставки предложения из буфера, буду использовать функцию создания нового предложения, но с данными из буфера
function insertFromBuffer(index) {
    const itemFromBuffer = getFromBuffer(index);
    const reportType = document.getElementById("editSentenceContainer").getAttribute("data-report-type");
    const bufferReportType = itemFromBuffer.report_type;

    if (!itemFromBuffer) {
        console.error("Элемент из буфера не найден.");
        return;
    }
    if (bufferReportType != reportType) {
        alert("Нельзя вставить предложение принадлежащее другому типу протокола (например нельзя вставить предложение из протокола с типом КТ в протокол с типом МРТ).");
        return;
    }

    if (itemFromBuffer.object_type === "paragraph") {
        alert("Нельзя вставить параграф в данной секции.");
        return;
    } else if (itemFromBuffer.sentence_type != "body") {
        alert("Нельзя вставить head или tail предложение в данной секции.");
        return
    }
    
    addBodySentence(itemFromBuffer);
    
}


// Функция поиска предложений по словам в тексте
function filterSentencesByText() {
    const searchText = document.getElementById("sentenceSearch").value.toLowerCase().trim();
    const searchWords = searchText.split(/\s+/);
    const sentences = document.querySelectorAll(".edit-sentence__item");

    sentences.forEach(item => {
        const sentenceText = item.querySelector(".edit-sentence__text").textContent.toLowerCase();
        const isMatch = searchWords.every(word => sentenceText.includes(word));
        item.style.display = isMatch ? "flex" : "none";
    });
}


// Функция для отсоединения группы предложений
function unlinkGroup(itemWrapper) {
    const groupId = itemWrapper.getAttribute("data-group-id");
    const sentenceType = itemWrapper.getAttribute("data-sentence-type");
    const relatedId = itemWrapper.getAttribute("data-head-sentence-id");
    

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
    itemWrapper.querySelector(".edit-sentence__title").textContent = "Дополнительные предложения (разблокировано)";

    // Скрываем иконку замка
    const lockIcon = itemWrapper.querySelector(".edit-sentence__title-span");
    if (lockIcon) {
        lockIcon.style.display = "none";
    }

    // Находим соответствующий список и снимаем блокировку
    const sentenceList = document.getElementById("editBodySentenceList");
    sentenceList.setAttribute("data-locked", "False");
}


// Функция для удаления связей предолжений путем создания нового предложения
function unlinkSentence(sentenceItem) {
    const sentenceId = sentenceItem.getAttribute("data-sentence-id");
    const sentenceType = sentenceItem.getAttribute("data-sentence-type");
    const related_id = sentenceItem.getAttribute("data-head-sentence-id");
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


// Функция для сохранения порядка tail предложений (меняет вес предложения на вес предыдущего + 1)
function saveBodySentencesOrder(evt) {
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
