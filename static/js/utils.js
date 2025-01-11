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




/**
 * Finds the maximum numeric value among a collection of input elements, used in edit_report.
 * 
 * @param {NodeList|Array} indexInputs - A collection of input elements whose values are to be evaluated as integers.
 * @returns {number} - The highest integer value found among the input elements, or 0 if the collection is empty or contains no valid numbers.
 */
function findMaxIndex(indexInputs) {
    let maxIndex = 0;

    if (indexInputs.length === 0) {
        return maxIndex;  // Return 0 if there are no elements
    }

    indexInputs.forEach(input => {
        const index = parseInt(input.value, 10);
        if (!isNaN(index) && index > maxIndex) {
            maxIndex = index;
        }
    });

    return maxIndex;
}


/**
 * Extracts the maximum number from the protocol number and increments it by 1 used in working with report.
 * 
 * @param {string} reportNumber - The report number in format "XXXX-XXXX".
 * @returns {number} - The incremented report number.
 */
function getMaxReportNumber(reportNumber) {
    // Split the string by the "-" character
    const parts = reportNumber.split('-');

    if (parts.length < 2) {
        // If there's no "-", simply convert the string to a number and return
        return parseInt(reportNumber, 10) + 1;
    }

    // Get the right part (the last number)
    const rightPart = parts[parts.length - 1];

    // Get the left part (everything except the last part)
    let leftPart = parts.slice(0, parts.length - 1).join('-');

    // Determine the number of digits in the right part
    const numDigitsInRightPart = rightPart.length;

    // Replace the last characters of the left part with the right part
    const newLeftPart = leftPart.slice(0, -numDigitsInRightPart) + rightPart;

    // Convert the result to a number and add 1
    return parseInt(newLeftPart, 10) + 1;
}




