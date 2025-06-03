// utils.js


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


/**
 * Универсальная функция для закрытия попапа.
 */
function hideElement(element) {
    if (element && element.style.display === "block") {
        element.style.display = "none";
    }
}
/**
 * Универсальная функция для показа попапа.
 */
function showElement(element) {
    if (element && element.style.display === "none") {
        element.style.display = "block";
        hideOnClickOutside(element);
    }
}

/**
 * Вешает обработчик, который скрывает элемент при клике вне его. Используется для закрытия попапов.
 * @param {HTMLElement} targetElement - Элемент, который нужно скрыть.
 * @param {Function} [onHide] - (Необязательно) callback, вызывается при скрытии.
 */
function hideOnClickOutside(targetElement, onHide) {
    if (!targetElement) return;

    // Хендлер клика
    function handleClick(event) {
        if (!targetElement.contains(event.target)) {
            hideElement(targetElement);
            if (typeof onHide === "function") onHide();
            document.removeEventListener("mousedown", handleClick);
        }
    }

    // Навешиваем слушатель
    setTimeout(() => { // setTimeout, чтобы не ловить клик, который открыл popup
        document.addEventListener("mousedown", handleClick);
    }, 0);
}


/**
 * Навешивает обработчик нажатия Enter на указанный элемент.
 * @param {Element|string} element - DOM-элемент или его id.
 * @param {Function} callback - Функция, которая будет вызвана при нажатии Enter.
 * @param {boolean} [preventDefault=true] - Нужно ли отменять стандартное действие.
 */
function onEnter(element, callback, preventDefault = true) {
    if (typeof element === "string") {
        element = document.getElementById(element);
    }
    if (!element) return;
    element.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
            if (preventDefault) e.preventDefault();
            callback(e, element);
        }
    });
}

function validateInputText(text, maxLength = 600, minLength = 1) {
    // Удаляем лишние пробелы в начале и конце строки
    const trimmedText = text.trim();

    if (typeof text !== "string") {
        return { valid: false, message: "Введённый текст должен быть строкой." };
    }
    if (trimmedText.length < minLength) {
        return { valid: false, message: `Текст слишком короткий. Пожалуйста, введите не менее ${minLength} символов.` };
    }
    if (trimmedText.length > maxLength) {
        return { valid: false, message: `Текст слишком длинный. Пожалуйста, сократите его до ${maxLength} символов.` };
    }

    return { valid: true };
}