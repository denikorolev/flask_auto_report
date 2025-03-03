// edit_report.js

document.addEventListener("DOMContentLoaded", function () {

    initSortable(); // Вызываем функцию для включения перетаскивания параграфов

    initParagraphPopup(); // Вызываем функцию для включения и выключения попапа параграфа при нажатии на его текст

    // слушатель на кнопку изменения протокола
    document.getElementById("updateReportButton").addEventListener("click", function() {
        handleUpdateReportButtonClick();
    });



    // Слушатель на кнопку "Редактировать параграф"
    document.querySelectorAll(".edit-paragraph__btn--edit").forEach(button => {
        button.addEventListener("click", function() {
            editParagraph(this);
        });
    });

    // Слушатель на кнопку "Удалить параграф"
    document.querySelectorAll(".edit-paragraph__btn--delete").forEach(button => {
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
    const paragraphContainer = document.querySelector(".edit-paragraph");

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
        newOrder.push({ id: paragraphId, index: index });
    });

    // Отправляем новый порядок на сервер
    console.log("Отправляем новый порядок на сервер:", newOrder);
    sendRequest({
        url: `/editing_report/update_paragraph_order`,
        method: "POST",
        data: { paragraphs: newOrder }
    }).then(response => {
        console.log("Порядок параграфов обновлен", response);
    }).catch(error => {
        console.error("Ошибка обновления порядка:", error);
    });
}


// Функция инициализации попапа
function initParagraphPopup() {
    document.querySelectorAll(".edit-paragraph__title").forEach(paragraph => {
        paragraph.addEventListener("dblclick", function (event) {
            event.stopPropagation();  // Останавливаем всплытие события. Чтобы не сработало событие на родителе
            showParagraphPopup(event, this);
        });
    });

    // Закрытие попапа при клике вне его
    document.addEventListener("click", function (event) {
        const popup = document.getElementById("paragraph-popup");
        if (popup && !popup.contains(event.target) && !event.target.classList.contains("edit-paragraph__title")) {
            popup.remove();
        }
    });
}


// Функция показа попапа
function showParagraphPopup(event, paragraphElement) {
    const paragraphId = parseInt(paragraphElement.getAttribute("data-paragraph-id"));
    const paragraphComment = paragraphElement.getAttribute("data-paragraph-comment") || "Нет комментария";
    const paragraphType = paragraphElement.getAttribute("data-paragraph-type");
    const paragraphIndex = parseInt(paragraphElement.getAttribute("data-paragraph-index"));
    const paragraphWeight = parseInt(paragraphElement.getAttribute("data-paragraph-weight")) || 0;
    const paragraphTags = paragraphElement.getAttribute("data-paragraph-tags");
    

    // Удаляем старый попап, если он есть
    let existingPopup = document.getElementById("paragraph-popup");
    if (existingPopup) {
        console.log("remove existing popup");
        existingPopup.remove();
    }

    // Создаем новый попап
    const popup = document.createElement("div");
    popup.id = "paragraph-popup";
    popup.classList.add("paragraph-popup");
    popup.innerHTML = `
        <p><strong>ID:</strong> ${paragraphId}</p>
        <p><strong>Тип:</strong> ${paragraphType}</p>
        <p><strong>Индекс:</strong> ${paragraphIndex}</p>
        <p><strong>Вес:</strong> ${paragraphWeight}</p>
        <p><strong>Теги:</strong> ${paragraphTags}</p>
        <p><strong>Комментарий:</strong> ${paragraphComment}</p>
    `;

    document.body.appendChild(popup);
    console.log("show popup");

    // Размещаем попап рядом с курсором
    const popupWidth = popup.offsetWidth;
    const popupHeight = popup.offsetHeight;
    let posX = event.clientX + 15;
    let posY = event.clientY + 15;

    // Предотвращаем выход за границы экрана
    if (posX + popupWidth > window.innerWidth) {
        posX -= popupWidth + 30;
    }
    if (posY + popupHeight > window.innerHeight) {
        posY -= popupHeight + 30;
    }

    popup.style.left = `${posX}px`;
    popup.style.top = `${posY}px`;
}



// Функция для редактирования параграфа (переход на страницу редактирования параграфа)
function editParagraph(button) {
    const paragraphId = button.getAttribute("data-paragraph-id");
    const reportId = document.getElementById("editReportContainer").getAttribute("data-report-id");

    if (!paragraphId) {
        console.error("Не найден атрибут data-paragraph-id");
        return;
    }

    window.location.href = `/editing_report/edit_paragraph?paragraph_id=${paragraphId}&report_id=${reportId}`;
}


// Обработчик для кнопки edit-paragraph__button--edit работает через onclick
function handleEditParagraphButtonClick(button){
    const paragraphId = button.getAttribute("data-paragraph-id");
    const form = button.closest("form");
    const formData = new FormData(form);
    formData.append("paragraph_id", paragraphId);
    
    sendRequest({
        url: `/editing_report/edit_paragraph`,
        data: formData
    });
};


// Обработчик для кнопки edit-paragraph__button--delete работает через onclick
function deleteParagraph(button){
    console.log("Удаление параграфа");
    const paragraphId = button.getAttribute("data-paragraph-id") 
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
       
   
// запуск чекеров
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








