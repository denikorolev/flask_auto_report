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
 * Отображает всплывающее окно с предложениями для замены.
 * 
 * Функция создает и отображает всплывающее окно (popup) с предложениями для выбора. 
 * Пользователь может отфильтровать список предложений и выбрать нужное, после чего вызывается 
 * переданная callback-функция с выбранным элементом.
 * 
 * @param {number} x - Координата X для отображения окна (в пикселях).
 * @param {number} y - Координата Y для отображения окна (в пикселях).
 * @param {Array} sentenceList - Список предложений для выбора, где каждый элемент 
 * является объектом с текстом предложения (например, { sentence: "Текст предложения" }).
 * @param {Function} onSelect - Callback-функция, которая вызывается при выборе предложения. 
 * В функцию передается объект выбранного предложения.
 * 
 * @requires popup - Глобальный элемент, отвечающий за отображение всплывающего окна.
 * @requires popupList - Глобальный элемент списка внутри popup.
 * @requires hidePopupSentences - Глобальная функция для скрытия popup.
 */
function showPopupSentences(x, y, sentenceList, onSelect) {
    popupList.innerHTML = ''; // Очищаем старые предложения

    // Создаем поле ввода для фильтрации
    const filterInput = document.createElement("input");
    filterInput.type = "text";
    filterInput.placeholder = "Введите текст для фильтрации...";
    filterInput.classList.add("input", "popup-filter-input");

    // Добавляем поле ввода в начало popupList
    popupList.appendChild(filterInput);

    // Функция для отображения отфильтрованного списка
    function renderFilteredList() {
        const filterText = filterInput.value.toLowerCase(); // Текст фильтра, приведенный к нижнему регистру

        // Очищаем список перед обновлением
        popupList.querySelectorAll("li").forEach(li => li.remove());

        // Отображаем только те предложения, которые соответствуют фильтру
        sentenceList.forEach(sentence => {
            if (sentence.sentence.toLowerCase().includes(filterText)) {
                const li = document.createElement("li");
                li.textContent = sentence.sentence; // Используем текст предложения
               

                // Устанавливаем обработчик клика на элемент списка
                li.addEventListener("click", () => {
                    onSelect(sentence); // Вызываем переданную функцию при выборе предложения
                    hidePopupSentences();
                });

                popupList.appendChild(li);
            }
        });
    }

    // Запускаем рендеринг отфильтрованного списка при вводе текста
    filterInput.addEventListener("input", renderFilteredList);

    // Изначально отображаем полный список
    renderFilteredList();

    // Устанавливаем позицию и отображаем popup
    popup.style.left = `${x}px`;
    popup.style.top = `${y + 10}px`; // Отображаем окно чуть ниже предложения
    popup.style.display = 'block';

    // **Добавляем обработчик клика для скрытия popup**
    document.addEventListener("click", function handleOutsideClick(event) {
        if (!popup.contains(event.target) && 
            !event.target.classList.contains("keyword-highlighted") && 
            !event.target.classList.contains("report__sentence")) {
            hidePopupSentences();
            document.removeEventListener("click", handleOutsideClick);
        }
    });
}


/**
 * Скрывает всплывающее окно с предложениями.
 */
function hidePopupSentences() {
    popup.style.display = 'none';
}


