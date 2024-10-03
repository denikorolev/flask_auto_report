// create_report.js

document.addEventListener("DOMContentLoaded", function() {
    // Инициализируем логику типа и подтипа через utils.js
    initializeSubtypeLogic("report_type", "report_subtype", "report-types-data");


    // Логика показа полей загрузки файлов в зависимости от выбора типа создания протокола
    const actionSelect = document.getElementById("action");
    const fileUploadContainer = document.getElementById("file-upload-container");

    // Show or hide file upload field based on action selection
    actionSelect.addEventListener("change", function() {
        if (this.value === "file") {
            fileUploadContainer.style.display = "flex";
        } else {
            fileUploadContainer.style.display = "none";
        }
    });

        actionSelect.dispatchEvent(new Event("change"));
});
