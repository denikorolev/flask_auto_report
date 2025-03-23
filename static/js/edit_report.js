// edit_report.js

document.addEventListener("DOMContentLoaded", function () {

    initSortable(); // Вызываем функцию для включения перетаскивания параграфов

    initParagraphPopupCloseHandlers(); // Инициализация слушателей на закрытие попапа

    // Слушатель на кнопку "сохранить" в попапе текста параграфа
    document.getElementById("elementPopupSaveChangesButton").addEventListener("click", function() {
        handleSaveChangesButtonClick();
    });

    // Слушатель на кнопку открыть попап буфера
    document.getElementById("openBufferPopupButton").addEventListener("click", function() {
        showBufferPopup(this);
    });

    // Слушатель на кнопки 🗒️
    document.querySelectorAll(".control-btn--copy-to-buffer").forEach(btn => {btn.addEventListener("click", function() {
        addGroupDataToBuffer(this);
        });
    });

    // Слушатель на кнопку "✂️"
    document.querySelectorAll(".control-btn--unlink").forEach(btn => {
        btn.addEventListener("click", function() {
            deleteSubsidiaries(this);
        });
    });



    // Инициализация слушателей двойного клика на предложения для показа попапа
    document.querySelectorAll(".edit-paragraph__title").forEach(sentence => {
        sentence.addEventListener("dblclick", function (event) {
            event.stopPropagation();
            showParagraphPopup(this, event);
        });
    });

    // Слушатель для вызова обновления текста параграфа при клике на него
    document.querySelectorAll(".edit-paragraph__title").forEach(paragraph => {
        paragraph.addEventListener("click", function (event) {
            event.stopPropagation(); // Останавливаем всплытие события
            makeEditable(this);
        });
    });

    // слушатель на кнопку изменения протокола
    document.getElementById("updateReportButton").addEventListener("click", function() {
        handleUpdateReportButtonClick();
    });

    

    // Слушатель на кнопку "Добавить параграф"
    document.getElementById("addParagraphButton").addEventListener("click", function() {
        const itemFromBuffer = null
        addParagraph(itemFromBuffer);
        }
    );


    // Слушатель на кнопку "Редактировать параграф" перенаправляет на страницу редактирования параграфа
    document.querySelectorAll(".control-btn--edit").forEach(button => {
        button.addEventListener("click", function() {
            editParagraph(this);
        });
    });

    // Слушатель на кнопку "Удалить параграф"
    document.querySelectorAll(".control-btn--delete").forEach(button => {
        button.addEventListener("click", function() {
            deleteParagraph(this);
        });
    });
    
    // Слушатель на кнопку "Запуск проверки"
    document.getElementById("startCheckersButton").addEventListener("click", function() {
        startReportCheckers(this);
    });

});


// Функция инициализации SortableJS
function initSortable() {
    const paragraphContainer = document.querySelector(".edit-paragraph__list");

    if (paragraphContainer) {
        new Sortable(paragraphContainer, {
            handle: ".drag-handle", // Тянем за этот элемент
            animation: 150, // Гладкая анимация
            ghostClass: "sortable-ghost", // Прозрачный стиль перетаскиваемого элемента
            onEnd: function () {
                updateParagraphOrder();
            }
        });
    }
}


// Функция обновления порядка параграфов
function updateParagraphOrder() {
    const paragraphs = document.querySelectorAll(".edit-paragraph__item");
    const newOrder = [];

    paragraphs.forEach((paragraph, index) => {
        const paragraphId = paragraph.getAttribute("data-paragraph-id");
        newOrder.push({ id: paragraphId, index: index});
    });

    // Отправляем новый порядок на сервер
    console.log("Отправляем новый порядок на сервер:", newOrder);
    sendRequest({
        url: `/editing_report/update_paragraph_order`,
        method: "POST",
        data: { paragraphs: newOrder }
    }).then(response => {
        window.location.reload();
        console.log("Порядок параграфов обновлен", response);
    }).catch(error => {
        console.error("Ошибка обновления порядка:", error);
    });
}



// Функция для обновления флагов параграфа
async function handleSaveChangesButtonClick() {
    const popup = document.getElementById("elementPopup");
    const paragraphId = popup.getAttribute("data-element-id");

    const changedData = { paragraph_id: paragraphId };

    // Сбор значений чекбоксов и сравнение с текущими атрибутами
    const checkboxMapping = [
        { id: "elementVisibleCheckbox", key: "paragraph_visible", attr: "data-paragraph-visible" },
        { id: "elementBoldCheckbox", key: "bold_paragraph", attr: "data-bold-paragraph" },
        { id: "elementTitleCheckbox", key: "title_paragraph", attr: "data-title-paragraph" },
        { id: "elementImpressionCheckbox", key: "is_impression", attr: "data-paragraph-impression" },
        { id: "elementIsActiveCheckbox", key: "is_active", attr: "data-paragraph-active" },
        { id: "elementStrBefore", key: "str_before", attr: "data-paragraph-str-before" },
        { id: "elementStrAfter", key: "str_after", attr: "data-paragraph-str-after" },
        { id: "elementIsAdditional", key: "is_additional", attr: "data-paragraph-additional" },
    ];

    const paragraphElement = document.querySelector(`.edit-paragraph__title[data-paragraph-id="${paragraphId}"]`);


    checkboxMapping.forEach(({ id, key, attr }) => {
        const checkbox = document.getElementById(id);
        const currentValue = paragraphElement.getAttribute(attr)?.toLowerCase() === "true";
        const checkboxValue = checkbox.checked === true;
        if (checkboxValue !== currentValue) {
            changedData[key] = checkboxValue;
        }
    });

    console.log("Измененные данные параграфа:", changedData);

    // Если нет изменений, не отправляем запрос
    if (Object.keys(changedData).length === 1) {
        console.log("Нет изменений для отправки.");
        hidePopup();
        return;
    }
    // Отправляем запрос на сервер
    try {
        const response = await sendRequest({
            url: "/editing_report/update_paragraph_flags",
            method: "PATCH",
            data: changedData
            
        });

        console.log("Ответ от сервера после обновления флагов параграфа:", response);

        if (response?.status === "success") {
            // пока просто перезагрузить страницу потом добавить динамическое обновление данных на странице
            window.location.reload();
        }
    } catch (error) {
        console.error("Ошибка при отправке данных обновления параграфа:", error);
    }
}




// Функция показа попапа с буфером
function showBufferPopup(button) {
    const popup = document.getElementById("bufferPopup");

    popup.style.display === "block"
}





// Функция показа попапа с информацией о параграфе
function showParagraphPopup(sentenceElement, event) {
    const popup = document.getElementById("elementPopup");

    // Получаем данные из атрибутов
    const elementId = sentenceElement.getAttribute("data-paragraph-id");
    const elementIndex = sentenceElement.getAttribute("data-paragraph-index");
    const elementComment = sentenceElement.getAttribute("data-paragraph-comment") || "None";
    const elementTags = sentenceElement.getAttribute("data-paragraph-tags") || "None";

    // Устанавливаем elementId в аттрибуты попапа
    popup.setAttribute("data-element-id", elementId);

    // Заполняем попап
    document.getElementById("popupElementId").textContent = elementId;
    document.getElementById("popupElementIndex").textContent = elementIndex;
    document.getElementById("popupElementComment").textContent = elementComment;
    document.getElementById("popupElementTags").textContent = elementTags;

    // Проверяем и скрываем, если значение None, пустое или null
    document.querySelectorAll(".sentence-popup__info-item").forEach(item => {
        const value = item.querySelector("span").textContent.trim();
        if (!value || value === "None") {
            item.style.display = "none";
        } else {
            item.style.display = "block"; // Показываем обратно, если были скрыты до этого
        }
    });

    // Устанавливаем правильное состояние чекбоксов в попапе
    const checkboxMapping = [
        { id: "elementVisibleCheckbox", attr: "data-paragraph-visible" },
        { id: "elementBoldCheckbox", attr: "data-bold-paragraph" },
        { id: "elementTitleCheckbox", attr: "data-title-paragraph" },
        { id: "elementImpressionCheckbox", attr: "data-paragraph-impression" },
        { id: "elementIsActiveCheckbox", attr: "data-paragraph-active" },
        { id: "elementStrBefore", attr: "data-paragraph-str-before" },
        { id: "elementStrAfter", attr: "data-paragraph-str-after" },
        { id: "elementIsAdditional", attr: "data-paragraph-additional" },
    ];

    checkboxMapping.forEach(({ id, attr }) => {
        const checkbox = document.getElementById(id);
        const value = sentenceElement.getAttribute(attr)?.toLowerCase() === "true"; // Приводим к boolean
        checkbox.checked = value; // Устанавливаем состояние чекбокса
    });

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


// Инициализация слушателей попапа параграфа
function initParagraphPopupCloseHandlers() {
    const popup = document.getElementById("elementPopup");
    const closeButton = document.getElementById("closeElementPopup");

    if (!popup || !closeButton) {
        console.error("Попап или кнопка закрытия не найдены!");
        return;
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



// Функция закрытия попапа параграфа
function hidePopup() {
    const popup = document.getElementById("elementPopup");
    if (popup) {
        popup.style.display = "none";
        // Очищаем атрибуты попапа
        popup.removeAttribute("data-element-id");
    } else {
        console.warn("Попап для предложения не найден.");
    }
}



// Функция для добавления параграфа
async function addParagraph(itemFromBuffer) {
    const reportId = document.getElementById("editReportContainer").getAttribute("data-report-id");
    console.log("Добавление нового параграфа в протокол:", reportId);
    const paragraphsList = document.getElementById("editParagraphsList");

    if (itemFromBuffer) {
        console.log("Добавление нового параграфа с данными:", itemFromBuffer);
        data = { paragraph_text: itemFromBuffer.object_text,
                 object_id: itemFromBuffer.object_id,
                 object_type: itemFromBuffer.object_type,
                 report_id: reportId
                };
    } else {
        data = { report_id: reportId };
    }

    try {
        const response = await sendRequest({
            url: "/editing_report/add_new_paragraph",
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


// Функция для редактирования параграфа (переход на страницу редактирования параграфа) 
function editParagraph(button) {
    const paragraphId = button.closest(".control-buttons").getAttribute("data-object-id");
    const reportId = button.closest(".control-buttons").getAttribute("data-related-id");

    if (!paragraphId) {
        console.error("Не найден атрибут data-paragraph-id");
        return;
    }

    window.location.href = `/editing_report/edit_paragraph?paragraph_id=${paragraphId}&report_id=${reportId}`;
}


// Функция для обновления протокола
async function handleUpdateReportButtonClick() {

    data = { report_name: document.getElementById("reportName").value,
             report_id: document.getElementById("editReportContainer").getAttribute("data-report-id"),
             report_comment: document.getElementById("reportComment").value,
             report_side: document.querySelector('input[name="report_side"]:checked').value
            };

    console.log("Обновление протокола:", data);

    try {
        const response = await sendRequest({
            url: `/editing_report/update_report`,
            method: "PATCH",
            data: data
        });
        if (response.status === "success") {
            console.log("Протокол обновлен:", response.message);
        }
        
    } catch (error) {
        console.error("Ошибка обновления протокола:", response.message);
    }
}



// Обработчик для кнопки "Удалить параграф" 
function deleteParagraph(button){
    console.log("Удаление параграфа");
    const paragraphId = button.closest(".control-buttons").getAttribute("data-object-id");
        sendRequest({
            url: `/editing_report/delete_paragraph`,
            method: "DELETE",
            data: { paragraph_id: paragraphId },
        }).then(response => {
            window.location.reload();
        }).catch(error => {
            console.log("Ошибка удаления параграфа.");
        });
};
       
   
// запуск чекеров. 
// Обновил но костылями !!!!!!!!!!!!!!!!!!!!!!!
function startReportCheckers(button) {
    const reportId = button.getAttribute("data-report-id");
    const checksReportUl = document.getElementById("reportCheckList");

    if (!checksReportUl) {
        console.error("Элемент reportCheckList не найден!");
        return;
    }

    const checkReportLi = document.createElement("li");

    console.log(reportId);
    sendRequest({
        url: `/editing_report/report_checkers`,
        data: {report_id: reportId},
    }).then(response => {
        
        checkReportLi.innerHTML = response.message;
        checksReportUl.appendChild(checkReportLi);
        checksReportUl.style.display = "block";
    });
}




// Вызываемые функции (не нужно инициировать при загрузке страницы)

// Функция делает заголовок параграфа редактируемым и собирает изменения
function makeEditable(paragraphElement) {
    if (paragraphElement.getAttribute("contenteditable") === "true") return; // Уже редактируется

    const oldText = paragraphElement.textContent.trim(); // Запоминаем старый текст
    paragraphElement.setAttribute("contenteditable", "true");
    paragraphElement.focus(); // Даём фокус

    // Функция для завершения редактирования
    function finishEditing() {
        paragraphElement.setAttribute("contenteditable", "false"); // Заканчиваем редактирование
        paragraphElement.removeEventListener("keydown", onEnterPress); // Удаляем обработчик Enter

        const newText = paragraphElement.textContent.trim();
        if (newText !== oldText) {
            updateParagraph(paragraphElement); // Отправляем на сервер только если текст изменился
        }
    }

    // Обработчик потери фокуса (сохранение изменений)
    paragraphElement.addEventListener("blur", finishEditing, { once: true });

    // Обработчик нажатия Enter
    function onEnterPress(event) {
        if (event.key === "Enter") {
            console.log("Нажат Enter (Return на Mac)");
            event.preventDefault(); // Отменяем перенос строки
            paragraphElement.blur(); // Симулируем потерю фокуса
        }
    }

    paragraphElement.addEventListener("keydown", onEnterPress);
}


// Функция для обновления текста параграфа отправляет запрос на сервер
async function updateParagraph(paragraphElement) {
    const paragraphId = paragraphElement.getAttribute("data-paragraph-id");
    const paragraphText = paragraphElement.textContent.trim();
    console.log("Отправка обновленного текста:", paragraphText);

    try {
        const response = await sendRequest({
            url: "/editing_report/update_paragraph_text",
            method: "PATCH",
            data: {
                paragraph_id: paragraphId,
                paragraph_text: paragraphText
            }
        });

        console.log("Параграф обновлен:", response);
    } catch (error) {
        console.error("Ошибка обновления параграфа:", error);
    }
}



// Функция для добавления параграфа в буфер
function addGroupDataToBuffer(button, sentenceType) {
    const objectId = button.closest(".control-buttons").getAttribute("data-object-id");
    const objectType = button.closest(".control-buttons").getAttribute("data-object-type");
    const relatedId = button.closest(".control-buttons").getAttribute("data-related-id");
    const objectText = button.closest(".control-buttons").getAttribute("data-text");

    dataToBuffer = {
        object_id: objectId,
        object_type: objectType,
        related_id: relatedId,
        object_text: objectText
    };

    addToBuffer(dataToBuffer);
    console.log("Добавление в буфер:", dataToBuffer);

}


function deleteSubsidiaries (button) {
    const objectId = button.closest(".control-buttons").getAttribute("data-object-id");
    const objectType = button.closest(".control-buttons").getAttribute("data-object-type");

    sendRequest({
        url: `/editing_report/delete_subsidiaries`,
        method: "DELETE",
        data: { object_id: objectId, object_type: objectType}
    }).then(response => {
        window.location.reload();
    }).catch(error => {
        console.error(response.message || "Ошибка удаления дочерних элементов:", error);
    });
}


// Функция для вставки параграфа из буфера, буду использовать функцию создания нового параграфа, но с данными из буфера
function insertFromBuffer(index) {
    const itemFromBuffer = getFromBuffer(index);

    if (!itemFromBuffer) {
        alert("Элемент не найден в буфере");
        return;
    }

    console.log("Вставка из буфера:", itemFromBuffer);
    // Создаем новый параграф
    addParagraph(itemFromBuffer);
}