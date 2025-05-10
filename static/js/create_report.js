// create_report.js

// Массив для хранения последовательности выбора отчетов
let selectedReports = [];

document.addEventListener("DOMContentLoaded", function() {
    
    // Вешаем обработчик на изменение типа отчета
    document.getElementById("reportType").addEventListener("change", handleReportTypeChange);
    // Триггерим для начальной настройки(имитируем нажатие от пользователя, чтобы запустить логику выбора)
    document.getElementById("reportType").dispatchEvent(new Event("change"));

    // Вешаем обработчик на изменение способа создания отчета
    document.querySelectorAll('input[name="action"]').forEach(radio => {
        radio.addEventListener("change", function () {
            handleActionChange(this.value);
        });
    });

    
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
    const reportTypeText = selectedType ? selectedType.type_text : "неизвестный тип";

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
        if (itemReportType === String(reportTypeText)) {
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


// Обрабатывает выбор отчетов, управляет массивом `selectedReports`.
function handleReportSelection(event) {
    const target = event.target;

    if (target.type === "checkbox") {
        const reportId = target.value;

        if (target.checked) {
            if (!selectedReports.includes(reportId)) {
                selectedReports.push(reportId);
            }
        } else {
            selectedReports = selectedReports.filter(id => id !== reportId);
        }

        updateOrderCircles();
    }
}


// Определяет выбранное действие и вызывает соответствующую функцию.
function handleCreateReportClick() {
    const selectedRadio = document.querySelector('input[name="action"]:checked');
    const selectedAction = selectedRadio ? selectedRadio.value : null;

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
        case "shared":
            createReportFromShared();
        case "public":
            createReportFromPublic();
            break;
        default:
            alert("Пожалуйста, выберите способ создания протокола.");
            console.error("Выбрано неизвестное действие:", selectedAction);
    }
}


// Определяет какое значение выбрано в radio input и настраивает вид окна в зависимости от этого.
function handleActionChange(selectedAction) {
    const fileUploadContainer = document.getElementById("reportCreationForm");
    const existingReportContainer = document.getElementById("existingReportContainer");
    const sharedReportContainer = document.getElementById("sharedReportContainer");
    const publicReportContainer = document.getElementById("publicReportContainer");

    // Скрываем все
    fileUploadContainer.style.display = "none";
    existingReportContainer.style.display = "none";
    sharedReportContainer.style.display = "none";
    publicReportContainer.style.display = "none";

    // Показываем выбранный
    if (selectedAction === "file") {
        fileUploadContainer.style.display = "flex";
    } else if (selectedAction === "existing_few") {
        existingReportContainer.style.display = "block";
    } else if (selectedAction === "shared") {
        sharedReportContainer.style.display = "block";
        loadSharedReports();  // функция уже есть
    } else if (selectedAction === "public") {
        publicReportContainer.style.display = "block";
        loadPublicReports();  // создадим её ниже
    }


    // Сброс выбранных отчетов
    selectedReports = [];
    // Сброс состояния всех чекбоксов
    document.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
        checkbox.checked = false;
    });

    updateOrderCircles();

}


// Отправляет запрос на сервер для получения данных о существующих shared отчетах
async function loadSharedReports() {
    const list = document.getElementById("sharedReportList");
    list.innerHTML = ""; // очистим

    try {
        const response = await sendRequest({
            url: "/new_report_creation/get_shared_reports",
            method: "GET"
        });

        if (response.status != "error") {
            if (response.reports.length === 0) {
                console.log("Нет доступных протоколов от других пользователей.");
                list.innerHTML = `<li>Нет доступных протоколов от других пользователей.</li>`;
                return;
            }
            response.reports.forEach(report => {
                const li = document.createElement("li");
                li.setAttribute("data-report-type", report.report_type);
                li.classList.add("existing-fewreports__item");
                li.innerHTML = `
                    <label>
                        <input type="radio" name="shared_report_radio" value="${report.id}" />
                        ${report.report_name} - ${report.report_type}  (${report.shared_by_email})
                    </label>
                `;
                list.appendChild(li);
            });
        } else {
            list.innerHTML = `<li>Ошибка: ${response.message}</li>`;
        }
    } catch (error) {
        list.innerHTML = `<li>Не удалось загрузить протоколы других пользователей.</li>`;
    }
}

// Отправляет запрос на сервер для получения данных о существующих public отчетах
async function loadPublicReports() {    
    const list = document.getElementById("publicReportList");
    list.innerHTML = ""; // очистка

    try {
        const response = await sendRequest({
            method: "GET",
            url: "/new_report_creation/get_public_reports"
        });

        if (response.status === "success" && response.reports.length > 0) {
            response.reports.forEach(report => {
                const li = document.createElement("li");
                li.setAttribute("data-report-type", report.report_type);
                li.classList.add("public-reports__item");
                li.innerHTML = `
                    <label>
                        <input type="radio" name="public_report_radio" value="${report.id}">
                        ${report.report_name} - ${report.report_type}
                    </label>
                `;
                list.appendChild(li);
            });
        } else {
            list.innerHTML = `<li>Нет общедоступных протоколов.</li>`;
        }
    } catch (error) {
        list.innerHTML = `<li>Не удалось загрузить общедоступные протоколы.</li>`;
        console.error(error);
    }
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


// Создание протокола из файла с валидацией
function createReportFromFile() {
    const reportForm = document.getElementById("reportCreationForm");
    const reportName = document.getElementById("report_name")?.value?.trim();
    const reportSubtype = document.getElementById("reportSubtype")?.value;
    const comment = document.getElementById("reportCreationComment")?.value?.trim() || "";
    const reportSide = document.querySelector("input[name='report_side']:checked")?.value === "true";
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

    // Добавляем остальные поля вручную
    formData.append("report_name", reportName);
    formData.append("report_subtype", reportSubtype);
    formData.append("comment", comment);
    formData.append("report_side", reportSide); // булево значение преобразуется автоматически
    
    sendRequest({
        url: "/new_report_creation/create_report_from_file",
        data: formData
    }).then(response => {
        if (response?.status === "success") {
            window.location.href = `/editing_report/edit_report?report_id=${response.report_id}`;
        }
    });
}



// Создание протокола на основе нескольких существующих с валидацией
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


    const jsonData = {
        report_name: reportName,
        report_subtype: reportSubtype,
        comment: comment,
        report_side: reportSide,
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

function createReportFromPublic() {
    const reportName = document.getElementById("report_name")?.value?.trim();
    const reportSubtype = document.getElementById("reportSubtype")?.value;
    const comment = document.getElementById("reportCreationComment")?.value?.trim() || "";
    const reportSide = document.querySelector("input[name='report_side']:checked")?.value === "true";
    const selectedReportId = document.querySelector("input[name='public_report_radio']:checked").value;
    

    if (!selectedReportId) {
        alert("Выберите хотя бы один существующий отчет!");
        return;
    }

    if (!reportName || !reportSubtype) {
        alert("Заполните все обязательные поля: название протокола и его подтип!");
        return;
    }
    const jsonData = {
        report_name: reportName,
        report_subtype: reportSubtype,
        comment: comment,
        report_side: reportSide,
        selected_report_id: selectedReportId
    };
    sendRequest({
        url: "/new_report_creation/create_report_from_public",
        data: jsonData
    }).then(response => {
        if (response?.status === "success") {
            window.location.href = `/editing_report/edit_report?report_id=${response.report_id}`;
        }
    });
}

// Создание протокола на протоколов, которые были поделены с пользователем
function createReportFromShared() {
    const reportName = document.getElementById("report_name")?.value?.trim();
    const reportSubtype = document.getElementById("reportSubtype")?.value;
    const comment = document.getElementById("reportCreationComment")?.value?.trim() || "";
    const reportSide = document.querySelector("input[name='report_side']:checked")?.value === "true";
    const selectedReport = document.querySelector("input[name='shared_report_radio']:checked");
    const selectedReportId = selectedReport?.value;

    if (!selectedReportId) {
        alert("Выберите хотя бы один существующий отчет!");
        return;
    }

    if (!reportName || !reportSubtype) {
        alert("Заполните все обязательные поля: название протокола и его подтип!");
        return;
    }
    const jsonData = {
        report_name: reportName,
        report_subtype: reportSubtype,
        comment: comment,
        report_side: reportSide,
        selected_report_id: selectedReportId,
        is_shared: true
    };
    sendRequest({
        url: "/new_report_creation/create_report_from_public",
        data: jsonData
    }).then(response => {
        if (response?.status === "success") {
            window.location.href = `/editing_report/edit_report?report_id=${response.report_id}`;
        }
    });
}






