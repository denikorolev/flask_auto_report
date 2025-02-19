// create_report.js

// Массив для хранения последовательности выбора отчетов
let selectedReports = [];

document.addEventListener("DOMContentLoaded", function() {
    
    // Вешаем обработчик на изменение подтипа отчета
    document.getElementById("reportType").addEventListener("change", handleReportTypeChange);
    // Триггерим для начальной настройки(имитируем нажатие от пользователя, чтобы запустить логику выбора)
    document.getElementById("reportType").dispatchEvent(new Event("change"));

    // Вешаем обработчик на изменение способа создания отчета
    document.getElementById("action").addEventListener("change", handleActionChange); 
    // Триггерим для начальной настройки(имитируем нажатие от пользователя, чтобы запустить логику выбора)
    document.getElementById("action").dispatchEvent(new Event("change")); 
    // Вешаем функцию обработчик на кнопку "Создать протокол"
    document.getElementById("createReportButton")?.addEventListener("click", handleCreateReportClick);
    // Вешаем обработчик на чекбоксы существующих отчетов
    document.getElementById("existingReportList").addEventListener("change", handleReportSelection);

});


//Фильтрует подтипы в зависимости от выбранного типа.
function handleReportTypeChange() {
    const reportType = parseInt(document.getElementById("reportType").value, 10); // приводим к числу   
    const reportSubtypeSelect = document.getElementById("reportSubtype");

    reportSubtypeSelect.innerHTML = ''; // Очищаем select

    // Получаем подтипы для выбранного типа
    const selectedType = reportTypesAndSubtypes.find(type => type.type_id === reportType);
    const currentSubtypes = selectedType ? selectedType.subtypes : [];

    // Если нет подтипов, добавлям заглушку
    if (currentSubtypes.length === 0) {
        const emptyOption = document.createElement("option");
        emptyOption.value = "";
        emptyOption.textContent = "Нет доступных подтипов";
        emptyOption.disabled = true;
        emptyOption.selected = true;
        reportSubtypeSelect.appendChild(emptyOption);
        return;
    }

    // Добавляем новые options
    currentSubtypes.forEach(subtype => {
        const option = document.createElement("option");
        option.value = subtype.subtype_id;
        option.textContent = subtype.subtype_text;
        reportSubtypeSelect.appendChild(option);
    });
    
    // фильтруем список существующих протоколов в зависимости от выбранного типа
    const existingReportsList = document.querySelectorAll("#existingReportList li");

    existingReportsList.forEach(item => {
        const itemReportType = item.dataset.reportType;
        if (itemReportType === String(reportType)) {
            item.style.display = "block";
        } else {
            item.style.display = "none";
        }
    });

    // Сбрасываем выбор отчетов
    selectedReports = [];

}

// Функции обработчики

/**
 * Обновляет номера в кружках порядка выбора отчетов.
 */
function updateOrderCircles() {
    document.querySelectorAll("#existingReportList li").forEach((item) => {
        const input = item.querySelector("input[type='checkbox']");
        const circle = item.querySelector(".existing-fewreports__order-circle");

        if (input && circle) {
            const indexInArray = selectedReports.indexOf(input.value);

            if (indexInArray !== -1) {
                circle.textContent = indexInArray + 1; // Устанавливаем номер
                circle.style.display = "inline-block"; // Показываем кружок
            } else {
                circle.textContent = "";
                circle.style.display = "none"; // Скрываем кружок
            }
        }
    });
}


/**
 * Обрабатывает выбор отчетов, управляет массивом `selectedReports`.
 */
function handleReportSelection(event) {
    const target = event.target;

    // Проверяем, что кликнули по чекбоксу и что он находится внутри списка отчетов
    if (target.type === "checkbox" && target.closest("#existingReportList")) {
        const reportId = target.value;

        if (target.checked) {
            selectedReports.push(reportId);
        } else {
            selectedReports = selectedReports.filter(id => id !== reportId);
        }

        updateOrderCircles();
        console.log("Выбранные отчеты:", selectedReports);
    }
}


/**
 * Определяет выбранное действие и вызывает соответствующую функцию.
 */
function handleCreateReportClick() {
    const selectedAction = document.getElementById("action")?.value;

    switch (selectedAction) {
        case "manual":
            createManualReport();
            break;
        case "file":
            createReportFromFile();
            break;
        case "existing_few":
            createReportFromExistingFew();
            break;
        default:
            alert("Пожалуйста, выберите способ создания протокола.");
            console.error("Выбрано неизвестное действие:", selectedAction);
    }
}


/**
 * Определяет какое значение выбрано в action и настраивает вид окна в зависимости от этого.
 */
function handleActionChange() {
    const actionSelect = document.getElementById("action");
    const fileUploadContainer = document.getElementById("file-upload-container");
    const existingReportContainer = document.getElementById("existing-report-container");
    const additionalParagraphContainer = document.getElementById("additional_paragraphs_container");

    if (!actionSelect) return;
    
    const selectedAction = actionSelect.value;

    // Показываем или скрываем контейнеры в зависимости от выбора
    fileUploadContainer.style.display = selectedAction === "file" ? "flex" : "none";
    existingReportContainer.style.display = selectedAction === "existing_few" ? "block" : "none";
    additionalParagraphContainer.style.display = selectedAction === "existing_few" ? "block" : "none";

    // Если изменили действие, сбрасываем выбор отчетов
    selectedReports = [];
    updateOrderCircles();
}



// Функции для создания отчета после нажатия на кнопку "Создать протокол"

/**
 * Создание протокола вручную с валидацией
 */
function createManualReport() {
    const reportName = document.getElementById("report_name")?.value?.trim();
    const reportSubtype = document.getElementById("reportSubtype")?.value;
    const comment = document.getElementById("reportCreationComment")?.value?.trim() || "";
    const reportSide = document.querySelector("input[name='report_side']:checked")?.value === "true";

    if (!reportName || !reportSubtype) {
        alert("Заполните все обязательные поля: название протокола и его подтип!");
        return;
    }

    const jsonData = {
        report_name: reportName,
        report_subtype: reportSubtype,
        comment: comment,
        report_side: reportSide
    };

    sendRequest({
        url: "/new_report_creation/create_manual_report",
        data: jsonData
    }).then(response => {
        if (response?.status === "success") {
            window.location.href = `/editing_report/edit_report?report_id=${response.report_id}`;
        }
    });
}


/**
 * Создание протокола из файла с валидацией
 */
function createReportFromFile() {
    const reportForm = document.getElementById("report-creation__form");
    const reportName = document.getElementById("report_name")?.value?.trim();
    const reportSubtype = document.getElementById("reportSubtype")?.value;
    const reportFile = document.getElementById("report_file")?.files[0];

    // Валидация обязательных полей
    if (!reportName || !reportSubtype) {
        alert("Заполните все обязательные поля: название протокола и его подтип!");
        return;
    }

    // Проверка на загруженный файл
    if (!reportFile) {
        alert("Загрузите файл с протоколом!");
        return;
    }

    // Создаем объект FormData для отправки файла
    const formData = new FormData(reportForm);
    
    sendRequest({
        url: "/new_report_creation/create_report_from_file",
        data: formData
    }).then(response => {
        if (response?.status === "success") {
            window.location.href = `/editing_report/edit_report?report_id=${response.report_id}`;
        }
    });
}



/**
 * Создание протокола на основе нескольких существующих с валидацией
 */
function createReportFromExistingFew() {
    const reportName = document.getElementById("report_name")?.value?.trim();
    const reportSubtype = document.getElementById("reportSubtype")?.value;
    const comment = document.getElementById("reportCreationComment")?.value?.trim() || "";
    const reportSide = document.querySelector("input[name='report_side']:checked")?.value === "true";


    if (selectedReports.length === 0) {
        alert("Выберите хотя бы один существующий отчет!");
        return;
    }

    if (!reportName || !reportSubtype) {
        alert("Заполните все обязательные поля: название протокола и его подтип!");
        return;
    }

    const additionalParagraphs = document.getElementById("additional_paragraphs")?.value || 0;

    const jsonData = {
        report_name: reportName,
        report_subtype: reportSubtype,
        comment: comment,
        report_side: reportSide,
        additional_paragraphs: additionalParagraphs,
        selected_reports: selectedReports
    };

    sendRequest({
        url: "/new_report_creation/create_report_from_existing_few",
        data: jsonData
    }).then(response => {
        if (response?.status === "success") {
            window.location.href = `/editing_report/edit_report?report_id=${response.report_id}`;
        }
    });
}


