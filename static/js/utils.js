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
        return;
    }

    reportTypeSelect.addEventListener("change", function() {
        updateSubtypes(reportTypeSelectId, reportSubtypeSelectId, allSubtypes);
    });

    // Initial update of subtypes
    updateSubtypes(reportTypeSelectId, reportSubtypeSelectId, allSubtypes);
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




/**
 * Creates ripple effect centered on the given element.
 * @param {HTMLElement} targetElement - The element from which the ripple should appear.
 */
function createRippleAtElement(targetElement) {
    const circle = document.createElement("span");
    circle.classList.add("ripple");

    const diameter = Math.max(targetElement.clientWidth, targetElement.clientHeight);
    circle.style.width = circle.style.height = `${diameter}px`;

    // Позиционируем ripple по центру элемента
    circle.style.left = `${(targetElement.clientWidth / 2) - (diameter / 2)}px`;
    circle.style.top = `${(targetElement.clientHeight / 2) - (diameter / 2)}px`;

    // Удаляем старый ripple, если есть
    const existingRipple = targetElement.querySelector(".ripple");
    if (existingRipple) existingRipple.remove();

    targetElement.style.position = "relative"; // Обязательно для корректного позиционирования
    targetElement.appendChild(circle);

    // Удаляем ripple после завершения анимации
    setTimeout(() => circle.remove(), 600);
}


/**
 * Универсальная функция для обработки тройного клика на элементе.
 * 
 * @param {HTMLElement} element - Элемент, на котором нужно отслеживать тройной клик.
 * @param {Function} callback - Функция, которая будет вызвана при тройном клике.
 */
function onTripleClick(element, callback) {
    let clickCount = 0;
    let clickTimer;

    element.addEventListener("click", () => {
        clickCount++;
        if (clickCount === 3) {
            callback();
            clearTimeout(clickTimer);
            clickCount = 0;
        } else {
            clearTimeout(clickTimer);
            clickTimer = setTimeout(() => {
                clickCount = 0;
            }, 400); // 400 мс — таймаут между кликами
        }
    });
}