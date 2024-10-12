// utils.js

/**
 * Updates the subtypes in the dropdown based on the selected report type.
 * 
 * @param {string} reportTypeSelectId - The ID of the report type select element.
 * @param {string} reportSubtypeSelectId - The ID of the report subtype select element.
 * @param {Object} allSubtypes - An object containing the subtypes grouped by type IDs.
 */
function updateSubtypes(reportTypeSelectId, reportSubtypeSelectId, allSubtypes) {
    const reportTypeSelect = document.getElementById(reportTypeSelectId);
    const reportSubtypeSelect = document.getElementById(reportSubtypeSelectId);

    // Debugging logs
    console.log("updateSubtypes called");
    console.log("reportTypeSelect:", reportTypeSelect);
    console.log("reportSubtypeSelect:", reportSubtypeSelect);
    console.log("allSubtypes:", allSubtypes);

    if (!reportTypeSelect || !reportSubtypeSelect) {
        console.error("Report type or subtype select element not found");
        return;
    }

    const selectedTypeId = reportTypeSelect.value.trim();
    reportSubtypeSelect.innerHTML = '';

    const subtypes = allSubtypes[selectedTypeId] || [];

    subtypes.forEach(subtype => {
        const option = document.createElement("option");
        option.value = subtype.subtype_id || subtype.id;
        option.textContent = subtype.subtype_text || subtype.subtype;
        reportSubtypeSelect.appendChild(option);
    });

    if (subtypes.length > 0) {
        reportSubtypeSelect.selectedIndex = 0;
    }
}

/**
 * Initializes the subtype updating logic for a page.
 * 
 * @param {string} reportTypeSelectId - The ID of the report type select element.
 * @param {string} reportSubtypeSelectId - The ID of the report subtype select element.
 * @param {string} subtypesDataScriptId - The ID of the <script> element containing the subtype data in JSON format.
 */
function initializeSubtypeLogic(reportTypeSelectId, reportSubtypeSelectId, subtypesDataScriptId) {
    const subtypesDataScript = document.getElementById(subtypesDataScriptId);

    // Debugging logs
    console.log("initializeSubtypeLogic called");
    console.log("subtypesDataScript:", subtypesDataScript);

    if (!subtypesDataScript) {
        console.error(`Element with ID '${subtypesDataScriptId}' not found.`);
        return;
    }

    const reportTypesAndSubtypes = JSON.parse(subtypesDataScript.textContent);
    const allSubtypes = {};

    // Store subtypes grouped by their type_id
    reportTypesAndSubtypes.forEach(type => {
        allSubtypes[type.type_id] = type.subtypes;
    });

    // Debugging log for allSubtypes
    console.log("Parsed allSubtypes:", allSubtypes);

    const reportTypeSelect = document.getElementById(reportTypeSelectId);

    if (!reportTypeSelect) {
        console.error(`Element with ID '${reportTypeSelectId}' not found.`);
        return;
    }

    reportTypeSelect.addEventListener("change", function() {
        updateSubtypes(reportTypeSelectId, reportSubtypeSelectId, allSubtypes);
    });

    // Initial update of subtypes
    updateSubtypes(reportTypeSelectId, reportSubtypeSelectId, allSubtypes);
}



/**
 * Filters the list of reports based on the selected report type.
 * 
 * @param {HTMLElement} reportTypeSelect - The select element containing report types.
 * @param {HTMLElement} existingReportList - The list element containing the reports to be filtered.
 */
function filterReportsByType(reportTypeSelect, existingReportList) {
    const selectedType = reportTypeSelect.value;  // Получаем выбранный тип
    const reports = existingReportList.querySelectorAll("li, .report_form__item");  // Получаем все отчеты

    reports.forEach(report => {
        const reportType = report.getAttribute("data-report-type");  // Получаем тип отчета
        
        // Определяем стиль отображения родительского элемента
        const parentDisplayStyle = getComputedStyle(existingReportList).display;

        // Если выбран тип "" (All) или тип совпадает с атрибутом отчета, показываем его
        if (selectedType === "" || reportType === selectedType) {
            if (parentDisplayStyle === "grid") {
                report.style.display = "grid";  // Используем grid, если у родителя grid
            } else {
                report.style.display = "flex";  // Используем flex в остальных случаях
            }
        } else {
            report.style.display = "none";  // Скрываем отчет, если тип не совпадает
        }
    });
}