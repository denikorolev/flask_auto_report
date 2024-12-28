// create_report.js

document.addEventListener("DOMContentLoaded", function() {
    // Инициализируем логику типа и подтипа через utils.js
    initializeSubtypeLogic("report_type", "report_subtype", "report-types-data");

    const reportForm = document.getElementById("report-creation-form");
    const actionSelect = document.getElementById("action");
    const fileUploadContainer = document.getElementById("file-upload-container");
    const existingReportContainer = document.getElementById("existing-report-container");
    const reportTypeSelect = document.getElementById("report_type");
    const existingReportList = document.getElementById("existing-report-list");

    // Фильтруем список отчетов при выборе типа исследования
    reportTypeSelect.addEventListener("change", function() {
        filterReportsByType(reportTypeSelect, existingReportList);
    });

    // Программно вызываем событие для первоначального отображения правильных полей
    actionSelect.dispatchEvent(new Event("change"));

    // Показываем или скрываем поля в зависимости от выбора действия
    actionSelect.addEventListener("change", function() {
        if (this.value === "file") {
            fileUploadContainer.style.display = "flex";  // Показываем поле загрузки файла
            existingReportContainer.style.display = "none";  // Скрываем список существующих отчетов
        } else if (this.value === "existing") {
            fileUploadContainer.style.display = "none";  // Скрываем поле загрузки файла
            existingReportContainer.style.display = "block";  // Показываем список существующих отчетов
        } else {
            fileUploadContainer.style.display = "none";  // Скрываем поле загрузки файла
            existingReportContainer.style.display = "none";  // Скрываем список существующих отчетов
        }
    });

    

    // Показываем или скрываем список существующих отчетов при выборе действия "existing"
    // actionSelect.addEventListener("change", function() {
    //     if (this.value === "existing") {
    //         existingReportContainer.style.display = "block";  // Показываем список
    //     } else {
    //         existingReportContainer.style.display = "none";  // Скрываем список
    //     }
    // });

    // Логика для создания отчета вручную или на основе файла
    document.querySelector(".btn.report__btn").addEventListener("click", function() {
        const formData = new FormData(reportForm);
        const action = actionSelect.value;

        if (action === "manual") {
            sendRequest({
                url: "/new_report_creation/create_manual_report",
                method: "POST",
                data: formData,
                responseType: "json",
                csrfToken: csrfToken
            }).then(response => {
                if (response.status === "success") {
                    toastr.success(response.message);
                    window.location.href = `/editing_report/edit_report?report_id=${response.report_id}`;
                } else {
                    alert(response.message || "Failed to create report");
                }
            }).catch(error => {
                console.error("Error creating report:", error);
            });
        } else if (action === "file") {
            sendRequest({
                url: "/new_report_creation/create_report_from_file",
                method: "POST",
                data: formData,
                responseType: "json",
                csrfToken: csrfToken
            }).then(response => {
                if (response.status === "success") {
                    toastr.success(response.message);
                    window.location.href = `/editing_report/edit_report?report_id=${response.report_id}`;
                } else {
                    alert(response.message || "Failed to create report");
                }
            }).catch(error => {
                console.error("Error creating report from file:", error);
            });
        } else if (action === "existing") {
            // Логика для создания отчета на основе существующего
            const selectedReportId = Array.from(existingReportList.querySelectorAll("input[type='checkbox']:checked"))
                .map(checkbox => checkbox.value)[0];  // Получаем выбранный отчет

            if (!selectedReportId) {
                alert("Please select an existing report");
                return;
            }

            formData.append("existing_report_id", selectedReportId);  // Добавляем ID выбранного отчета

            sendRequest({
                url: "/new_report_creation/create_report_from_existing_report",  // Правильный маршрут
                method: "POST",
                data: formData,
                responseType: "json",
                csrfToken: csrfToken
            }).then(response => {
                if (response.status === "success") {
                    toastr.success(response.message);
                    window.location.href = `/editing_report/edit_report?report_id=${response.report_id}`;  // Переход на правильный URL
                } else {
                    alert(response.message || "Failed to create report from existing report");
                }
            }).catch(error => {
                console.error("Error creating report from existing report:", error);
            });
        }
    });
});
