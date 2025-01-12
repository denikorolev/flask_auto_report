// create_report.js

document.addEventListener("DOMContentLoaded", function() {
    // Инициализируем логику типа и подтипа через utils.js
    initializeSubtypeLogic("report_type", "report_subtype", "report-types-data");
    
    let selectedReports = []; // тут мы сохраним последовательность выбора для кружков и отправки на сервер

    const reportForm = document.getElementById("report-creation-form");
    const actionSelect = document.getElementById("action");
    const fileUploadContainer = document.getElementById("file-upload-container");
    const existingReportContainer = document.getElementById("existing-report-container");
    const reportTypeSelect = document.getElementById("report_type");
    const existingReportList = document.getElementById("existing-report-list");
    const inputReportListElements = existingReportList.querySelectorAll("input");
    const additionalParagraphContainer = document.getElementById("additional_paragraphs_container");
    const additionalParagraphCount = document.getElementById("additional_paragraphs");
    // Фильтруем список отчетов при выборе типа исследования
    reportTypeSelect.addEventListener("change", function() {
        filterReportsByType(reportTypeSelect, existingReportList);
    });

    // Программно вызываем событие для первоначального отображения правильных полей
    actionSelect.dispatchEvent(new Event("change"));

    // Показываем или скрываем поля в зависимости от выбора действия
    actionSelect.addEventListener("change", function() {
        // вначале обновляем кружки, снимаем выбор и очищаем массив
        inputReportListElements.forEach(input => {
            input.checked = false; // Снимаем выбор со всех чекбоксов/радиокнопок
        });
        selectedReports = []; // Очищаем массив выбранных отчетов

        if (typeof updateOrderCircles === "function") {
            updateOrderCircles();
        } // Обновляем кружки

        if (this.value === "file") {
            fileUploadContainer.style.display = "flex";  // Показываем поле загрузки файла
            existingReportContainer.style.display = "none";  // Скрываем список существующих отчетов
        } else if (this.value === "existing") {
            fileUploadContainer.style.display = "none";  // Скрываем поле загрузки файла
            filterReportsByType(reportTypeSelect, existingReportList);  // Фильтруем список отчетов
            existingReportContainer.style.display = "block";  // Показываем список существующих отчетов
            additionalParagraphContainer.style.display = "none"; // Скрываем добавление дополнительных параграфов
            inputReportListElements.forEach(input => {
                input.type = "radio"; // Меняем тип на radiobox
            });
        } else if (this.value === "existing_few") {
            fileUploadContainer.style.display = "none";
            filterReportsByType(reportTypeSelect, existingReportList);
            existingReportContainer.style.display = "block";
            additionalParagraphContainer.style.display = "block" // Показываем добавление дополнительных параграфов
            inputReportListElements.forEach(input => {
                input.type = "checkbox"; // Меняем тип на checkbox
            });
            // Логика для выбора нескольких отчетов при помощи checkbox
            
            console.log("i'm in existing_few logic");

            // Функция для обновления кружков
            function updateOrderCircles() {
                const listItems = document.querySelectorAll("#existing-report-list li");

                listItems.forEach((item) => {
                    const input = item.querySelector("input[type='checkbox']");
                    const circle = item.querySelector(".existing-fewreports__order-circle");

                    if (input && circle) {
                        const indexInArray = selectedReports.indexOf(input.value);

                        if (indexInArray !== -1) {
                            // Обновляем текст кружка с позицией
                            circle.textContent = indexInArray + 1; // Позиция в массиве, начиная с 1
                            circle.style.display = "inline-block"; // Показываем кружок
                        } else {
                            // Скрываем кружок, если элемент не выбран
                            circle.textContent = "";
                            circle.style.display = "none";
                        }
                    }
                });
            }

            // Функция для обновления отображения
            existingReportList.addEventListener("change", function(event) {
                const target = event.target;
            
                if (target.type === "checkbox") {
                    const reportId = target.value;
            
                    if (target.checked) {
                        // Добавляем ID выбранного отчета в массив
                        selectedReports.push(reportId);
                    } else {
                        // Удаляем ID отчета из массива, если выбор снят
                        selectedReports = selectedReports.filter(id => id !== reportId);
                    }
                    // Лог массива для проверки
                    console.log("Selected reports:", selectedReports);
                    // Обновляем кружки
                    updateOrderCircles();
                    
                };
                
            });
            
        } else {
            fileUploadContainer.style.display = "none";  // Скрываем поле загрузки файла
            existingReportContainer.style.display = "none";  // Скрываем список существующих отчетов
        }
    });

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
            const selectedReportId = Array.from(existingReportList.querySelectorAll("input[type='radio']:checked"))
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
        } else if (action === "existing_few") {
            // Логика для создания отчета на основе нескольких существующих
            if (selectedReports.length === 0) {
                alert("Please select at least one report.");
                return;
            }
        
            // Формируем данные для отправки
            const jsonData = {
                report_name: formData.get("report_name"),
                report_subtype: formData.get("report_subtype"),
                comment: formData.get("comment"),
                report_side: formData.get("report_side") === "false",
                additional_paragraphs: additionalParagraphCount.value,
                selected_reports: selectedReports // Передаем массив с ID выбранных отчетов
            };
        
            // Отправляем запрос на сервер
            sendRequest({
                url: "/new_report_creation/create_report_from_existing_few",
                method: "POST",
                data: jsonData,
                responseType: "json",
                csrfToken: csrfToken
            })
                .then(response => {
                    if (response.status === "success") {
                        toastr.success(response.message);
                        window.location.href = `/editing_report/edit_report?report_id=${response.report_id}`; // Переход на страницу редактирования
                    } else {
                        alert(response.message || "Failed to create report from multiple existing reports.");
                    }
                })
                .catch(error => {
                    console.error("Error creating report from multiple existing reports:", error);
                });
        }
        
    });
});
