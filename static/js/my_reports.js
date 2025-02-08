// my_reports.js

let paragraphLinks = null; // Глобальная переменная


document.addEventListener('DOMContentLoaded', function() {
    const filterTypeSelect = document.getElementById('filter_type');
    const reportList = document.getElementById('reports_list');
    const linkReportsButton = document.getElementById("linkReports");

    // Инициализируем фильтрацию отчетов по типу при изменении фильтра. 
    // Функция filterReportsByType находится в utils.js
    filterTypeSelect.addEventListener('change', function() {
        filterReportsByType(filterTypeSelect, reportList);
    });

    // Инициализирую слушатель кнопки удалить отчет
    document.querySelectorAll('.my-report-list__button--delete').forEach(button => {
        button.addEventListener('click', deleteReport);
    });

    // Инициализирую слушатель кнопки "Связать отчеты"
    if (linkReportsButton) {
        linkReportsButton.addEventListener("click", linkSelectedReports);
    };

    // Инициализирую слушатель кнопки "Отправить связанные параграфы" эта кнопка в popup и по умолчанию не видна.
    document.getElementById("sendLinkedPairs").addEventListener("click", sendLinkedParagraphs);

});



//Функции

// Функция удаления отчета
function deleteReport(event){
    button = event.currentTarget;
    const reportId = button.dataset.reportId;
    if (!reportId) {
        console.error('report ID is missing.');
        return;
    }
    
    const confirmation = confirm('Вы действительно хотите удалить протокол? Это действие нельзя отменить.');
    if (!confirmation) return;

        sendRequest({
            url: `/my_reports/delete_report/${reportId}`,
            method: "DELETE",
            csrfToken: csrfToken
        }).then(response => {
            window.location.reload();
        }).catch(error => {
            console.log("Ошибка удаления удаления отчета.");
        });
};


// Функция для создания связи выбранных протоколов
function linkSelectedReports() {
    const checkboxes = document.querySelectorAll(".report_form_checkbox--linker:checked");
    const selectedReportIds = Array.from(checkboxes).map(checkbox => checkbox.value);

    if (selectedReportIds.length < 2) {
        alert("Выберите минимум два отчета для связывания.");
        return;
    }

    // Проверяем, совпадают ли типы отчетов
    const reportTypes = new Set();
    checkboxes.forEach(checkbox => {
        const reportItem = checkbox.closest(".report_form_item"); // Получаем родительский <li>
        if (reportItem) {
            reportTypes.add(reportItem.dataset.reportType); // Добавляем тип отчета в Set
        }
    });

    if (reportTypes.size > 1) {
        alert("Ошибка: Вы выбрали отчеты с разными типами. Можно связывать только отчеты одного типа.");
        return;
    }
    sendRequest({
        url: "/my_reports/auto_link_reports",  
        data: { reports: selectedReportIds },
    }).then(response => {
        
        if (!response) return;

        // Если нет связанных параграфов, изменяем статус и сообщение
        if (response.linked_paragraphs.length === 0) {
            response.status = "warning";
            response.message = "Автоматическое связывание не найдено, попробуйте вручную.";
            document.getElementById("linkedParagraphsTitle").style.display = "none";
        }

        // Вызываем функцию отображения popup
        showLinkingPopup(response);

    }).catch(error => {
        console.error("Ошибка при связывании отчетов:", error);
    });
}


// Связанные функции (не требуют инициализации)


// Открывает popup с отчетом
function showLinkingPopup(response) {
    const popup = document.getElementById("linkReportsPopup");
    const linkedList = document.getElementById("linkedParagraphsList");
    const unlinkedTable = document.getElementById("unlinkedParagraphsTable");
    const unlinkedBody = unlinkedTable.querySelector("tbody");
    const messageBlock = document.getElementById("linkingMessage");

    linkedList.innerHTML = "";
    unlinkedBody.innerHTML = "";
    messageBlock.textContent = response.message;

    if (response.status === "success") {
        response.linked_paragraphs.forEach(item => {
            const li = document.createElement("li");
            li.textContent = `Связан параграф ${item.index}: ${item.paragraph} (${item.reports.join(", ")})`;
            linkedList.appendChild(li);
        });
    }

    if (response.unlinked_paragraphs.length > 0) {
        const reports = {};

        // Группируем параграфы по отчетам
        response.unlinked_paragraphs.forEach(item => {
            if (!reports[item.report]) {
                reports[item.report] = [];
            }
            reports[item.report].push(item);
        });

        // Сортируем параграфы по индексу внутри каждого отчета
        Object.keys(reports).forEach(reportName => {
            reports[reportName].sort((a, b) => a.index - b.index);
        });

        // Создаем заголовки колонок
        const headerRow = unlinkedTable.createTHead().insertRow();
        Object.keys(reports).forEach(reportName => {
            const th = document.createElement("th");
            th.textContent = reportName;
            headerRow.appendChild(th);
        });

        // Определяем максимальное количество строк
        const maxRows = Math.max(...Object.values(reports).map(arr => arr.length));

        for (let i = 0; i < maxRows; i++) {
            const row = unlinkedBody.insertRow();
            Object.values(reports).forEach(paragraphs => {
                const cell = row.insertCell();
                if (paragraphs[i]) {
                    // Создаем блок для параграфа
                    const index = paragraphs[i].index;
                    const paragraphBlock = document.createElement("div");
                    paragraphBlock.classList.add("paragraph-block");
                    paragraphBlock.setAttribute("draggable", "true"); // Теперь можно перетаскивать
                    paragraphBlock.setAttribute("data-paragraph-id", paragraphs[i].report_id + "-" + paragraphs[i].paragraph_id); // Уникальный ID

                    const paragraphText = document.createElement("p");
                    paragraphText.textContent = `${paragraphs[i].paragraph} (индекс ${index})`;

                    paragraphBlock.appendChild(paragraphText);
                    cell.appendChild(paragraphBlock);
                }
            });
        }
    }

    popup.style.display = "block";

    // Вызываем функцию перетаскивания параграфов
    paragraphLinks = enableParagraphDragAndDrop(); // Инициализируем перетаскивание параграфов
    console.log("Связанные параграфы:", paragraphLinks.getLinkedPairs());
}


// Функция для включения перетаскивания параграфов
function enableParagraphDragAndDrop() {
    const paragraphs = document.querySelectorAll(".paragraph-block");

    let draggedParagraphData = null;
    let linkedPairs = []; // Теперь хранится глобально

    paragraphs.forEach(paragraph => {
        paragraph.setAttribute("draggable", true);

        paragraph.addEventListener("dragstart", function(event) {
            draggedParagraphData = this.dataset.paragraphId;
            this.classList.add("dragging");
        });

        paragraph.addEventListener("dragend", function() {
            this.classList.remove("dragging");
        });

        paragraph.addEventListener("dragover", function(event) {
            event.preventDefault();
        });

        paragraph.addEventListener("drop", function(event) {
            event.preventDefault();
            let targetParagraphData = this.dataset.paragraphId;

            if (!draggedParagraphData || draggedParagraphData === targetParagraphData) return;

            // **Получаем `report_id` обоих параграфов**
            let [draggedReportId, draggedParagraphId] = draggedParagraphData.split("-");
            let [targetReportId, targetParagraphId] = targetParagraphData.split("-");

            if (draggedReportId === targetReportId) {
                alert("Нельзя связывать параграфы из одного отчета!");
                return; // **Отмена связывания**
            }

            // Проверяем, есть ли уже такая связь
            let alreadyLinked = linkedPairs.some(pair =>
                (pair[0] === draggedParagraphId && pair[1] === targetParagraphId) ||
                (pair[0] === targetParagraphId && pair[1] === draggedParagraphId)
            );

            if (!alreadyLinked) {
                linkedPairs.push([draggedParagraphId, targetParagraphId]);

                let draggedElement = document.querySelector(`[data-paragraph-id='${draggedParagraphData}']`);
                let targetElement = this;

                draggedElement.classList.add("linked");
                targetElement.classList.add("linked");

                addLinkedIndicator(draggedElement, targetElement);
                addLinkedIndicator(targetElement, draggedElement);

                console.log("Связанные параграфы:", linkedPairs);
            }
        });
    });

    return {
        getLinkedPairs: () => [...linkedPairs]
    };
}

// Добавляем индикатор связи
function addLinkedIndicator(element, linkedElement) {
    let indicator = element.querySelector(".link-indicator");
    if (!indicator) {
        indicator = document.createElement("div");
        indicator.classList.add("link-indicator");
        element.appendChild(indicator);
    }
    indicator.innerText = `Параграф ${element.dataset.paragraphId} cвязан с: ${linkedElement.dataset.paragraphId}`;
}

// Отправка связанных пар на сервер
function sendLinkedParagraphs() {
    let linkedParagraphs = paragraphLinks.getLinkedPairs();
    console.log("Отправляем связанные параграфы:", linkedParagraphs);

    if (linkedParagraphs.length === 0) {
        alert("Нет выбранных пар для связывания.");
        return;
    }

    sendRequest({
        url: "/my_reports/manual_link_paragraphs",
        method: "POST",
        data: linkedParagraphs
    }).then(response => {
        if (response.status === "success") {
            alert("Параграфы успешно связаны!");
            window.location.reload();
        }
    }).catch(error => {
        console.error("Ошибка при связывании параграфов:", error);
    });
}


// Закрытие popup
document.getElementById("closePopup").addEventListener("click", function() {
    document.getElementById("linkReportsPopup").style.display = "none";
});