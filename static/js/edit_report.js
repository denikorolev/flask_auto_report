// edit_report.js

document.addEventListener("DOMContentLoaded", function () {

    initSortable(); // Вызываем функцию для включения перетаскивания параграфов

    initParagraphPopup(); // Вызываем функцию для включения и выключения попапа параграфа при нажатии на его текст

    initParagraphUpdate(); // Вызываем функцию для обновления текста параграфа при клике на него

    // слушатель на кнопку изменения протокола
    document.getElementById("updateReportButton").addEventListener("click", function() {
        handleUpdateReportButtonClick();
    });

    

    // Слушатель на кнопку "Добавить параграф"
    document.getElementById("addParagraphButton").addEventListener("click", addParagraph);


    // Слушатель на кнопку "Редактировать параграф" перенаправляет на страницу редактирования параграфа
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


function initParagraphUpdate() {
    document.querySelectorAll(".edit-paragraph__title").forEach(paragraph => {
        paragraph.addEventListener("click", function (event) {
            event.stopPropagation(); // Останавливаем всплытие события
            makeEditable(this);
        });
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


// Функция для добавления параграфа
async function addParagraph() {
    const reportId = document.getElementById("editReportContainer").getAttribute("data-report-id");
    const paragraphsList = document.getElementById("editParagraphsList");

    try {
        const response = await sendRequest({
            url: "/editing_report/add_new_paragraph",
            method: "POST",
            data: { report_id: reportId }
        });

        // Создаем новый элемент списка
        const newParagraphHTML = `
            <li class="wrapper__card edit-sentence__item" 
                data-paragraph-id="${response.id}" 

                <div class="drag-handle">☰</div>
                <div>
                <p class="edit-paragraph__title"><b>${response.paragraph}</b></p>
                <p class="edit-sentences__list">Это новый параграф и у него еще нет предложений.</p>
                </div>
                <div>
                    <button class="btn report__btn edit-sentence__btn--edit-head" data-sentence-id="${response.id}">Редактировать </button>
                    <button class="btn report__btn edit-sentence__btn--delete-head" data-sentence-id="${response.id}">Удалить </button>
                </div>
            </li>
        `;

        // Находим все <li> кроме кнопки "Добавить предложение"
        const paragraphs = paragraphsList.querySelectorAll(".edit-paragraph__item");
        if (paragraphs.length > 0) {
            // Вставляем новый <li> после последнего предложения
            paragraphs[paragraphs.length - 1].insertAdjacentHTML("afterend", newParagraphHTML);
        } else {
            // Если список пуст, просто добавляем первым элементом
            paragraphsList.insertAdjacentHTML("afterbegin", newParagraphHTML);
        }

        console.log("Новое предложение добавлено:", response);
    } catch (error) {
        console.error("Ошибка запроса:", error);
    }
}   

// Функция для редактирования параграфа (переход на страницу редактирования параграфа) 
// Не обновлял!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
function editParagraph(button) {
    const paragraphId = button.getAttribute("data-paragraph-id");
    const reportId = document.getElementById("editReportContainer").getAttribute("data-report-id");

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







