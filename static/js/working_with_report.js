// working_with_report.js


// Объявляем глобальные переменные и запускаем стартовые функции, постепенно нужно перенести сюда и логику связанную с ключевыми словами и развешивание части слушателей
document.addEventListener("DOMContentLoaded", function() {

    let activeSentence = null;  // Для отслеживания активного предложения
    const popupList = document.getElementById("popupList");  // Для обращения к PopUp
    const exportButton = document.getElementById("exportButton"); // Для обращения к кнопке "Экспорт в Word"
    const copyButton = document.getElementById("copyButton"); // Для обращения к кнопке "Копировать текст"
    const nextReportButton = document.getElementById("nextPatientButton"); // Для обращения к кнопке "Следующий пациент"
    const editButton = document.getElementById("editFormButton"); // Для обращения к кнопке Edit Form
    const addReportButton = document.getElementById("addReportButton"); // Для обращения к кнопке Add Report
    const generateButton = document.getElementById("generateImpression"); // Для обращения к кнопке Generate Impression
    const boxForAiResponse = document.getElementById("aiResponse");     // Для обращения к блоку с ответом от AI
    const addImpressionButton = document.getElementById("addImpressionToReportButton"); // Для обращения к кнопке "Вставить заключение"
    
    linkSentences(); // Связываем предложения с данными
    
    updateCoreParagraphText(); // Запускает выделение ключевых слов при загрузке страницы

    sentenceDoubleClickHandle () // Включаем логику двойного клика на предложение

    addSentenceButtonLogic(); // Включаем логику кнопки "+"


    // Проверяем наличие кнопки экспорт в Word и при ее наличии запускаем логику связанную с данным экспортом
    if (exportButton) {
        wordButtonLogic(exportButton);
    }

    // Проверяем наличие кнопки "Копировать текст" и при ее наличии запускаем логику связанную с копированием текста
    if (copyButton) {
        copyButtonLogic(copyButton);
    }

    // Проверяем наличие кнопки "Следующий пациент и при ее наличии запускаем логику связанную с созданием нового пациента и автоматическим увеличением номера отчета"
    if (nextReportButton) {
        nextButtonLogic(nextReportButton);
    }

    // Проверяем наличие кнопки "Edit Form" и при ее наличии запускаем логику связанную с редактированием формы
    if (editButton) {
        editButtonLogic(editButton);
    }

    // Проверяем наличие кнопки "Add Report" и при ее наличии запускаем логику связанную с добавлением нового отчета для текущего пациента
    if (addReportButton) {
        addReportButtonLogic(addReportButton);
    }

    if (generateButton) {
        generateImpressionLogic(generateButton, boxForAiResponse);
    }

    if (addImpressionButton) {
        addImpressionButtonLogic(addImpressionButton);
    }

    addFocusListeners(); // Добавляем логику для автоматической отправки на сервер новых предложений
});

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
 * Handles the focus event for a sentence element.
 * Saves the original text in a data attribute.
 */
function handleSentenceFocus() {
    if (!this.hasAttribute("data-original-text")) {
        this.setAttribute("data-original-text", this.textContent.trim());
        console.log("Focus: Original text saved:", this.textContent.trim());
    }
}

/**
 * Handles the blur event for a sentence element.
 * Checks for changes and marks the sentence as modified if needed.
 */
function handleSentenceBlur() {
    const originalText = this.getAttribute("data-original-text");
    const currentText = this.textContent.trim();
    const linkedSentences = this.linkedSentences || [];
    const paragraphId = this.dataset.paragraphId;

    // Блок условий для проверки изменений в предложении
    if (!currentText) {return;}
    if (normalizeSentence(originalText, keyWordsGroups) === normalizeSentence(currentText, keyWordsGroups)) {return;}
    const isDuplicate = linkedSentences.some(sentence =>
        normalizeSentence(sentence.sentence, keyWordsGroups) === normalizeSentence(currentText, keyWordsGroups)
    );
    if (isDuplicate) {return;}

    this.setAttribute("data-modified", "true");
    this.classList.add("was-changed-highlighted-sentence");
    console.log("Blur: Marked sentence as modified.");
}

/**
 * Creates an editable sentence element wrapped in a <span>.
 * Adds necessary attributes and attaches focus and blur event listeners.
 * 
 * @param {string} sentenceText - The text of the sentence to be added to the element.
 * @param {string} paragraphId - The ID of the paragraph to which the sentence belongs.
 * @returns {HTMLElement} - A new <span> element containing the editable sentence.
 */
function createEditableSentenceElement(sentenceText, paragraphId) {
    const newSentenceElement = document.createElement("span");
    newSentenceElement.classList.add("report__sentence");
    newSentenceElement.dataset.paragraphId = paragraphId; // Set paragraph ID
    newSentenceElement.dataset.index = "0"; // New sentences always start with index 0
    newSentenceElement.textContent = sentenceText;

    // Make the content editable
    newSentenceElement.contentEditable = "true";

    // Attach event listeners
    newSentenceElement.addEventListener("focus", handleSentenceFocus);
    newSentenceElement.addEventListener("blur", handleSentenceBlur);

    return newSentenceElement;
}



/**
 * Проверяет, виден ли элемент на экране.
 * 
 * @param {HTMLElement} element - HTML-элемент, который нужно проверить.
 * @returns {boolean} - Возвращает `true`, если элемент виден, и `false` в противном случае.
 */
function isElementVisible(element) {
    const style = window.getComputedStyle(element);
    return style.display !== "none" && style.visibility !== "hidden";
}


/**
 * Очищает текст элемента, удаляя кнопки и HTML-теги, оставляя только выбранный текст из <select>.
 * 
 * Функция предназначена для получения чистого текста из HTML-элемента. Удаляет все кнопки и HTML-теги, 
 * заменяет теги <select> выбранным текстом и убирает лишние пробелы.
 * 
 * @param {HTMLElement} element - HTML-элемент, содержащий текст для очистки.
 * @returns {string} - Очищенный текст.
 * 
 * Логика работы:
 * - Удаляет все кнопки внутри элемента.
 * - Заменяет <select> элементы их выбранным значением.
 * - Удаляет все оставшиеся HTML-теги, оставляя только текст.
 * - Преобразует HTML-сущности в обычные символы (например, &amp; → &).
 * - Убирает лишние пробелы, оставляя только один пробел между словами.
 */
function cleanSelectText(element) {
    let text = element.innerHTML;

    // Remove all buttons from the text
    element.querySelectorAll("button").forEach(button => {
        button.remove();  // Remove buttons from DOM to avoid interference with text collection
    });

    // Replace all <select> elements with their selected text
    element.querySelectorAll("select").forEach(select => {
        const selectedOption = select.options[select.selectedIndex].textContent;
        text = text.replace(select.outerHTML, selectedOption);
    });

    // Remove all HTML tags except text
    text = text.replace(/<[^>]*>/gm, '').trim();

    // Use a DOM parser to replace entities
    const tempElement = document.createElement("textarea");
    tempElement.innerHTML = text;
    text = tempElement.value;

    // Remove extra spaces (leave only one space between words)
    text = text.replace(/\s\s+/g, ' ');

    return text;
}


/**
 * Отображает обработанные абзацы и предложения, которые предлагаются для добавления в базу данных.
 * 
 * Функция очищает контейнер для отображения запросов на добавление предложений и создает элементы для 
 * каждого абзаца и его предложений. Предоставляет возможность добавления предложений по отдельности или всех сразу.
 * 
 * @param {Array} paragraphs - Массив объектов абзацев, где каждый объект содержит `paragraph_id`, `paragraph_text`, 
 *                             и массив `sentences` или строку `sentence`.
 * 
 * Логика работы:
 * - Проверяет валидность переданных данных.
 * - Очищает контейнер перед добавлением новых данных.
 * - Для каждого предложения создает элемент с текстом предложения и кнопкой "Добавить".
 * - Если общее количество предложений больше одного, добавляется кнопка "Отправить все", 
 *   которая позволяет отправить все предложения одним запросом.
 * 
 * Вспомогательные функции:
 * - `sendSentences(dataToSend)` — отправляет данные выбранных предложений на сервер.
 * - `createSentenceElement(paragraphId, sentence)` — создает элемент предложения с текстом и кнопкой "Добавить".
 * 
 */
function displayProcessedParagraphs(paragraphs) {
    const container = document.getElementById('sentenceAddingRequestContainer');
    container.innerHTML = ''; // Clear the container before adding new data

    // Проверка, есть ли данные для обработки
    if (!paragraphs || !Array.isArray(paragraphs)) {
        console.error("Invalid paragraphs data:", paragraphs);
        return;
    }

    // Внутренняя функция для отправки данных на сервер
    function sendSentences(dataToSend) {
        sendRequest({
            url: "/working_with_reports/add_sentence_to_paragraph",
            method: "POST",
            data: dataToSend,
            csrfToken: csrfToken
        })
        .then(response => {
            if (response) {
                toastr.success(response.message || 'Operation completed successfully!', 'Success');
            }
        })
        .catch(error => {
            console.error("Failed to send sentences:", error);
            alert("Failed to send sentences.");
        });
    }

    // Внутренняя функция для создания предложения и кнопки "Добавить"
    function createSentenceElement(paragraphId, sentence) {
        const sentenceDiv = document.createElement('div');
        sentenceDiv.classList.add('sentence-container');
        
        sentenceDiv.textContent = sentence;

        // Добавляем кнопку "Добавить"
        const addButton = document.createElement('button');
        addButton.textContent = 'Добавить';
        addButton.classList.add('add-sentence-btn');
        addButton.addEventListener('click', function() {
            const dataToSend = {
                sentence_for_adding: [
                    {
                        paragraph_id: paragraphId,
                        sentences: [sentence]
                    }
                ]
            };

            // Используем внутреннюю функцию для отправки данных
            sendSentences(dataToSend);
        });

        sentenceDiv.appendChild(addButton);
        return sentenceDiv;
    }

    // Collect total number of sentences to be added
    let totalSentences = 0;
    paragraphs.forEach(paragraph => {
        const sentences = Array.isArray(paragraph.sentences) ? paragraph.sentences : [paragraph.sentence];
        totalSentences += sentences.length;
    });
    
    // Создаем кнопку "Отправить все"
    if (totalSentences >= 2) {
        // Create "Send All" button
        const sendAllButton = document.createElement('button');
        sendAllButton.textContent = 'Отправить все';
        sendAllButton.classList.add('send-all-btn');
        sendAllButton.addEventListener('click', function() {
            const allSentences = [];

            // Собираем все предложения для отправки
            paragraphs.forEach(paragraph => {
                const sentences = Array.isArray(paragraph.sentences) ? paragraph.sentences : [paragraph.sentence];
                if (sentences) {
                    allSentences.push({
                        paragraph_id: paragraph.paragraph_id,
                        sentences: sentences
                    });
                }
            });

            // Формируем данные для отправки
            const dataToSend = {
                sentence_for_adding: allSentences
            };

            // Используем внутреннюю функцию для отправки данных
            sendSentences(dataToSend);
        });

        // Добавляем кнопку "Отправить все" в контейнер
        container.appendChild(sendAllButton);
    }

    // Создаем и добавляем элементы предложений в контейнер
    paragraphs.forEach(paragraph => {
        const paragraphDiv = document.createElement('div');
        paragraphDiv.classList.add('paragraph-container');

        const paragraphText = paragraph.paragraph_text || `Paragraph: ${paragraph.paragraph_id}`;
        paragraphDiv.textContent = `Paragraph: ${paragraphText}`;

        // Проверка на массив предложений
        if (Array.isArray(paragraph.sentences)) {
            paragraph.sentences.forEach(sentence => {
                const sentenceElement = createSentenceElement(paragraph.paragraph_id, sentence);
                paragraphDiv.appendChild(sentenceElement);
            });
        } else if (typeof paragraph.sentence === 'string') {
            // Если предложение передано как строка (единичное предложение)
            const sentenceElement = createSentenceElement(paragraph.paragraph_id, paragraph.sentence);
            paragraphDiv.appendChild(sentenceElement);
        } else {
            console.error('No valid sentences found for paragraph:', paragraph);
        }

        container.appendChild(paragraphDiv);
    });
}


/**
 * Выделяет ключевые слова в тексте, оборачивая их в выпадающие списки.
 * 
 * Функция обрабатывает переданный текст, заменяя ключевые слова из заданных групп ключевых слов 
 * на выпадающие списки (`<select>`), содержащие варианты из той же группы. Каждое ключевое слово 
 * обрабатывается с использованием регулярных выражений для обеспечения корректного выделения.
 * 
 * @param {string} text - Текст для обработки.
 * @param {Array} keyWordsGroups - Массив групп ключевых слов. Каждая группа представляет собой массив объектов, 
 *                                 где каждый объект содержит свойство `word` с ключевым словом.
 * @returns {string} - Обновленный текст с выделенными ключевыми словами.
 * 
 * Логика работы:
 * - Для каждой группы ключевых слов создается регулярное выражение, которое находит ключевые слова в тексте.
 * - Ключевые слова заменяются на элемент `<select>`, содержащий варианты из группы.
 * - Обработанные ключевые слова получают уникальный индекс `data-match-index` для удобства взаимодействия.
 * 
 * @requires keyWordsGroups - Глобальная переменная, содержащая группы ключевых слов для выделения.
 * 
 * Ограничения:
 * - Ключевые слова выделяются только если они находятся вне HTML-тегов.
 * - При совпадении нескольких ключевых слов в одной позиции используется первый подходящий вариант.
 */
function highlightKeyWords(text, keyWordsGroups) {
    const matchIndexes = {};

    // Проходим по каждой группе ключевых слов
    keyWordsGroups.forEach(group => {
        group.forEach(item => {
            const word = item.word; // Достаем слово из словаря
            if (!matchIndexes[word]) {
                matchIndexes[word] = 0;
            }

            // Регулярное выражение для нахождения ключевого слова вне тегов и без букв перед и после
            const regex = new RegExp(`(?<!<[^>]*>|[a-zA-Zа-яА-ЯёЁ])(${word})(?![^<]*>|[a-zA-Zа-яА-ЯёЁ])`, "gi");

            text = text.replace(regex, (matchedWord) => {
                matchIndexes[word] += 1;

                // Создаём select с опциями из той же группы слов
                const options = group
                    .map(option => {
                        const optionWord = option.word; // Получаем слово из каждого словаря
                        const isSelected = optionWord.toLowerCase() === matchedWord.toLowerCase() ? "selected" : "";
                        return `<option value="${optionWord}" ${isSelected}>${optionWord}</option>`;
                    })
                    .join("");

                return `<select class="report__select_dynamic" data-match-index="${word}-${matchIndexes[word]}">${options}</select>`;
            });
        });
    });

    return text;
}


/**
 * Обновляет текст абзацев с классом `paragraph__list--core` и выделяет ключевые слова.
 * 
 * Функция проходит по всем элементам с классом `paragraph__list--core`, извлекает текст абзацев 
 * и выделяет ключевые слова, используя функцию `highlightKeyWords`. Выделение применяется только 
 * если абзац еще не содержит выпадающих списков (`<select>`). Также сохраняется атрибут `data-index` 
 * для каждого абзаца.
 * 
 * @requires highlightKeyWords - Функция для выделения ключевых слов в тексте.
 * @requires keyWordsGroups - Глобальная переменная, содержащая группы ключевых слов для выделения.
 *
 * @global {NodeList} coreParagraphLists - Элементы с классом `paragraph__list--core`.
 * 
 * Логика работы:
 * - Для каждого элемента `paragraph__list--core` находятся вложенные элементы `p` и `span`.
 * - Из каждого элемента извлекается текст.
 * - Если текст еще не содержит `<select>`, применяется выделение ключевых слов.
 * - Восстанавливается атрибут `data-index` для каждого абзаца.
 */
function updateCoreParagraphText() {
    const coreParagraphLists = document.querySelectorAll(".paragraph__list--core");

    coreParagraphLists.forEach(paragraphList => {
        paragraphList.querySelectorAll("p, span").forEach(paragraph => {
            const currentIndex = paragraph.getAttribute("data-index");

            if (!currentIndex) {
                return;
            }

            let plainText = paragraph.innerText || paragraph.textContent;

            if (!paragraph.querySelector("select")) {
                const highlightedText = highlightKeyWords(plainText, keyWordsGroups);
                paragraph.innerHTML = highlightedText;
            }

            paragraph.setAttribute("data-index", currentIndex);
        });
    });
}


/**
 * Собирает данные абзацев и предложений для отправки на сервер.
 * 
 * Функция проходит по всем абзацам с классом `paragraph__list--core`, извлекает текст абзацев, 
 * их идентификаторы, а также вложенные предложения. Собранные данные возвращаются в формате массива объектов.
 * Каждый объект содержит:
 * - `paragraph_id` — идентификатор абзаца;
 * - `paragraph_text` — текст абзаца;
 * - `sentences` — массив текста всех предложений, принадлежащих данному абзацу.
 * 
 * @returns {Array<Object>} Массив объектов с данными абзацев и предложений.
 * Каждый объект имеет структуру:
 * {
 *   paragraph_id: {string},
 *   paragraph_text: {string},
 *   sentences: {Array<string>}
 * }
 * @requires isElementVisible - Глобальная функция, которая проверяет, видим ли элемент на странице.
 * @requires cleanSelectText - Глобальная функция, которая очищает текст предложения от HTML-тегов и других элементов.
 */
function collectParagraphsData() {
    const coreParagraphLists = document.querySelectorAll(".paragraph__list--core"); // Ищем списки с классом paragraph__list--core
    const paragraphsData = [];

    coreParagraphLists.forEach(paragraphList => {
        // Находим элемент абзаца внутри текущего списка (paragraph__list--core)
        const paragraphElement = paragraphList.querySelector(".report__paragraph > p");
        

        // Проверяем, что элемент абзаца существует
        if (!paragraphElement) {
            console.error("Paragraph element not found in paragraph__list--core.");
            return;
        }

        const paragraphId = paragraphElement.getAttribute("data-paragraph-id");
        const paragraphText = paragraphElement.innerText.trim();
        const sentences = [];

        // Находим все предложения внутри текущего абзаца
        paragraphList.querySelectorAll(".report__sentence").forEach(sentenceElement => {
            const sentenceText = cleanSelectText(sentenceElement);
            if (sentenceText) {
                sentences.push(sentenceText);
            }
        });

        if (sentences.length > 0) {
            paragraphsData.push({
                paragraph_id: paragraphId,
                paragraph_text: paragraphText,
                sentences: sentences,
            });
        }
    });
    

    return paragraphsData;
}


/**
 * Собирает текст из абзацев на основе указанного класса.
 * 
 * Функция находит все абзацы с указанным классом, извлекает их текст, а также текст вложенных предложений,
 * и возвращает полный текст в виде строки. Текст очищается от лишних пробелов и объединяется 
 * с учетом структуры абзацев и предложений.
 * 
 * @param {string} paragraphClass - Класс абзацев, текст которых необходимо собрать.
 * @returns {string} - Собранный текст абзацев и предложений.
 * 
 * @requires isElementVisible - Глобальная функция, которая проверяет, видим ли элемент на странице.
 * @requires cleanSelectText - Глобальная функция, которая очищает текст предложения от HTML-тегов и других элементов.
 */
function collectTextFromParagraphs(paragraphClass) {
    const paragraphLists = document.querySelectorAll(`.${paragraphClass}`); // Ищем списки по указанному классу
    let collectedText = "";

    paragraphLists.forEach(paragraphList => {
        // Находим элемент абзаца
        const paragraphElement = paragraphList.querySelector(".report__paragraph > p");
        
        if (!paragraphElement) {
            console.error("Paragraph element not found in", paragraphClass);
            return;
        }

        // Добавляем текст абзаца, если он виден
        if (isElementVisible(paragraphElement)) {
            const paragraphText = paragraphElement.innerText.trim();
            collectedText += paragraphText;

            // Проверяем, является ли абзац заголовком
            const isTitleParagraph = paragraphElement.getAttribute("data-title-paragraph") === "True";
            if (isTitleParagraph) {
                collectedText += "\n";  // Добавляем новую строку после заголовков
            } else {
                collectedText += " "; // Добавляем пробел после обычных абзацев
            }
        }

        let hasSentences = false;  // Флаг для проверки наличия предложений

        // Проходим по предложениям внутри абзаца
        paragraphList.querySelectorAll(".report__sentence").forEach(sentenceElement => {
            if (isElementVisible(sentenceElement)) {
                const sentenceText = cleanSelectText(sentenceElement);
                if (sentenceText) {
                    collectedText += sentenceText + " ";
                    hasSentences = true;
                }
            }
        });

        // Если предложения были найдены, добавляем новую строку
        if (hasSentences) {
            collectedText += "\n";
        }
    });

    return collectedText.trim();  // Убираем лишние пробелы и возвращаем текст
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
 * @requires hidePopup - Глобальная функция для скрытия popup.
 */
function showPopup(x, y, sentenceList, onSelect) {
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
                    hidePopup();
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
    popup.style.top = `${y + 10}px`; // Отображаем окно чуть ниже кружка
    popup.style.display = 'block';
}


/**
 * Скрывает всплывающее окно с предложениями.
 */
function hidePopup() {
    popup.style.display = 'none';
}


/**
 * Связывает предложения на странице с данными из объекта `reportData` и добавляет к ним связанные предложения.
 * 
 * Основная цель функции — обработать все предложения, отображаемые на странице (элементы с классом `report__sentence`), 
 * и связать их с соответствующими предложениями из данных `reportData`. 
 * Это позволяет обеспечить взаимодействие, например, замену или выбор альтернативных предложений.
 * 
 * Алгоритм работы:
 * 1. Находит все элементы с классом `report__sentence` на странице.
 * 2. Для каждого элемента:
 *    - Получает идентификаторы параграфа (`data-paragraph-id`), индекс предложения (`data-index`) и ID предложения (`data-id`).
 *    - Ищет соответствующий параграф в данных `reportData` по `paragraphId`.
 *    - Фильтрует список предложений в найденном параграфе, исключая текущее предложение (по его ID). 
 *    - Добавляет отфильтрованные предложения в свойство `linkedSentences` элемента предложения.
 * 
 * @global
 * @param {Object} reportData - Объект, содержащий данные параграфов и их предложений находится на странице working_with_report.html!!! 
 *                              Ожидается, что он имеет следующую структуру:
 *                              {
 *                                  paragraphs: [
 *                                      {
 *                                          id: Number,
 *                                          sentences: {
 *                                              [index]: Array<{ id: Number, sentence: String }>
 *                                          }
 *                                      }
 *                                  ]
 *                              }
 */
function linkSentences() {
    // Находим все предложения на странице
    const sentencesOnPage = document.querySelectorAll(".report__sentence");

    // Проходим по каждому предложению на странице
    sentencesOnPage.forEach(sentenceElement => {
        const paragraphId = sentenceElement.getAttribute("data-paragraph-id");
        const index = sentenceElement.getAttribute("data-index");
        const sentenceId = sentenceElement.getAttribute("data-id");

        // Ищем параграф с соответствующим ID и совпадающим index в reportData
        const paragraphData = reportData.paragraphs.find(p => p.id === parseInt(paragraphId));

        if (paragraphData && paragraphData.sentences[index]) {
            // Фильтруем предложения, исключая текущее видимое предложение по его ID
            const filteredSentences = paragraphData.sentences[index].filter(sentence => {
                return sentence.id.toString() !== sentenceId; // Сравнение по ID
            });

            // Связываем видимое предложение с отфильтрованными предложениями из reportData
            sentenceElement.linkedSentences = filteredSentences;

            // Если есть связанные предложения, выделяем цветом текущее предложение
            if (sentenceElement.linkedSentences.length > 0) {
                sentenceElement.classList.add("has-linked-sentences-highlighted-sentence");
            }
        }
    });
}


/**
 * Добавляет обработчики двойного клика и ввода для элементов предложений на странице.
 * 
 * Функциональность:
 * - При двойном клике отображает всплывающее окно с альтернативными предложениями, связанными с выбранным предложением.
 * - Позволяет заменить текст предложения выбранным вариантом из всплывающего окна.
 * - Обновляет текст абзацев после замены предложения.
 * - Скрывает всплывающее окно при начале ввода текста в предложении или при клике за пределы всплывающего окна.
 * 
 * Требования:
 * - Элементы предложений на странице должны иметь класс "report__sentence".
 * - У каждого элемента предложения должен быть массив `linkedSentences`, содержащий связанные предложения.
 * - Глобальная переменная `popup` должна быть доступна для отображения списка предложений.
 * - Должны существовать функции:
 *   - `showPopup(x, y, sentenceList, onSelect)` для отображения всплывающего окна.
 *   - `hidePopup()` для скрытия всплывающего окна.
 *   - `updateCoreParagraphText()` для обновления текста абзацев после изменений.
 * 
 * Использование:
 * - Вызвать эту функцию после полной загрузки DOM и отрисовки предложений на странице.
 */
function sentenceDoubleClickHandle (){
    const sentencesOnPage = document.querySelectorAll(".report__sentence");
    sentencesOnPage.forEach(sentenceElement => {
        // Добавляю слушатель двойного клика на предложение
        sentenceElement.addEventListener("dblclick", function(event){
            activeSentence = sentenceElement;
            if (sentenceElement.linkedSentences && sentenceElement.linkedSentences.length > 0) {
                // Передаем функцию, которая заменяет текст предложения
                showPopup(event.pageX, event.pageY, sentenceElement.linkedSentences, (selectedSentence) => {
                    activeSentence.textContent = selectedSentence.sentence; // Заменяем текст предложения
                    updateCoreParagraphText(); // Обновляем текст
                });
            } else {
                console.error("No linked sentences or linked sentences is not an array");
            }
        });
        // Добавляю слушатель начала ввода на предложение
        sentenceElement.addEventListener("input", function(event) {
            hidePopup();
        });
    });

    // Скрываем всплывающее окно при клике вне его
    document.addEventListener("click", function(event) {
        if (!popup.contains(event.target)) {
            hidePopup();
        }
    });
}

/**
 * Обрабатывает логику кнопки "Next".
 * 
 * Функциональность:
 * - При нажатии на кнопку "Next" вычисляет новый номер протокола, увеличивая текущий номер на единицу.
 * - Формирует URL для перехода на страницу выбора нового отчета с обновленным номером протокола.
 * - Выполняет переход на указанную страницу.
 * - После загрузки новой страницы автоматически ставит фокус на поле ввода фамилии пациента.
 * 
 * Требования:
 * - Элемент кнопки, переданный в параметр `nextReportButton`, должен существовать на странице.
 * - Поле с ID "report-number" должно содержать текущий номер протокола.
 * - Должна быть доступна функция `getMaxReportNumber(reportNumber)` для вычисления нового номера протокола.
 * - Поле с ID "patient-surname" должно присутствовать на целевой странице, чтобы фокус был установлен корректно.
 * 
 * Использование:
 * - Вызвать эту функцию, передав элемент кнопки "Next", после полной загрузки DOM.
 * 
 * Примечания:
 * - Если необходимые элементы не найдены, функция выведет сообщение об ошибке в консоль и прекратит выполнение.
 */
function nextButtonLogic(nextReportButton) {
    nextReportButton.addEventListener("click", function() {
        // Получаем текущий номер протокола и вычисляем новый номер
        const reportNumberField = document.getElementById("report-number");
        if (!reportNumberField) {
            console.error("Поле 'report-number' не найдено.");
            return;
        }
        const reportNumber = reportNumberField.value.trim();
        const maxReportNumber = getMaxReportNumber(reportNumber);
        const newReportNumber = maxReportNumber.toString();

        // Формируем URL для перехода на страницу choosing_report с новым номером протокола
        const url = `choosing_report?report_number=${encodeURIComponent(newReportNumber)}`;

        // Переходим на страницу choosing_report и ставим фокус на поле фамилии
        window.location.href = url;

        // Устанавливаем таймер, чтобы поставить фокус на поле после загрузки страницы
        setTimeout(() => {
            const surnameField = document.getElementById("patient-surname");
            if (surnameField) {
                surnameField.focus();
            }
        }, 600); // Настройте время таймера по необходимости
    });
}



/**
 * Логика для кнопки "Add Report".
 * 
 * Функция обрабатывает нажатие на кнопку "Add Report" для формирования нового отчета.
 * 
 * Шаги выполнения:
 * 1. Получает данные из следующих полей:
 *    - `patient-name`: Имя, фамилия и отчество пациента (строка, разбивается на части).
 *    - `patient-birthdate`: Дата рождения пациента.
 *    - `report-number`: Номер текущего отчета.
 * 2. Вычисляет новый номер отчета, увеличивая текущий на 1 с помощью функции `getMaxReportNumber`.
 * 3. Формирует URL для перехода на страницу `choosing_report`, включая следующие параметры:
 *    - Фамилия, имя, отчество пациента.
 *    - Дата рождения пациента.
 *    - Новый номер отчета.
 * 4. Переходит на страницу `choosing_report` с указанными параметрами.
 * 
 * Требования:
 * - Поля ввода с ID `patient-name`, `patient-birthdate`, `report-number`.
 * - Кнопка, которая запускает данную логику, передается как аргумент функции.
 * - Функция `getMaxReportNumber` для вычисления нового номера отчета.
 * 
 * @param {HTMLElement} addReportButton - Кнопка добавления нового отчета.
 */
function addReportButtonLogic(addReportButton) {
    addReportButton.addEventListener("click", function() {
        // Получаем значение из поля "surname" и разбиваем его на части
        const surnameInput = document.getElementById("patient-name")?.value.trim() || "";
        const [surname = "", name = "", patronymic = ""] = surnameInput.split(" ");

        const birthdate = document.getElementById("patient-birthdate")?.value || "";
        const reportNumberField = document.getElementById("report-number");

        if (!reportNumberField) {
            console.error("Поле 'report-number' не найдено.");
            return;
        }

        const reportNumber = reportNumberField.value.trim();
        const maxReportNumber = getMaxReportNumber(reportNumber);
        const newReportNumber = maxReportNumber.toString();

        // Формируем строку для передачи параметров через URL
        const url = `choosing_report?patient_surname=${encodeURIComponent(surname)}
        &patient_name=${encodeURIComponent(name)}
        &patient_patronymicname=${encodeURIComponent(patronymic)}
        &patient_birthdate=${encodeURIComponent(birthdate)}
        &report_number=${encodeURIComponent(newReportNumber)}`;

        // Переходим на страницу choosing_report
        window.location.href = url;
    });
}



/**
 * Логика для кнопки "Edit Form".
 * 
 * Функция обрабатывает нажатие на кнопку "Edit Form" для переключения режима редактирования формы.
 * 
 * Шаги выполнения:
 * 1. Проверяет, являются ли поля формы с ID `exportForm` только для чтения.
 * 2. В зависимости от текущего состояния (только для чтения или редактируемые):
 *    - Удаляет атрибут `readonly` для переключения в режим редактирования.
 *    - Добавляет атрибут `readonly` для возврата в режим только для чтения.
 * 3. Изменяет иконку кнопки и текст подсказки (`title`) в зависимости от состояния:
 *    - При включении режима редактирования устанавливается иконка сохранения и подсказка "Save Changes".
 *    - При возврате в режим только для чтения устанавливается иконка редактирования и подсказка "Edit Form".
 * 
 * Требования:
 * - Элемент с ID `exportForm`, содержащий поля ввода (input).
 * - Элемент кнопки для редактирования передается в качестве аргумента функции.
 * 
 * @param {HTMLElement} editButton - Кнопка, запускающая логику редактирования формы.
 */
function editButtonLogic(editButton) {
    const formInputs = document.querySelectorAll("#exportForm input");

    editButton.addEventListener("click", function() {
        // Проверяем, являются ли поля формы только для чтения
        const isReadOnly = formInputs[0]?.hasAttribute("readonly");

        formInputs.forEach(input => {
            if (isReadOnly) {
                input.removeAttribute("readonly"); // Делаем поля формы редактируемыми
            } else {
                input.setAttribute("readonly", true); // Делаем поля формы только для чтения
            }
        });

        // Меняем иконку кнопки и текст подсказки
        if (isReadOnly) {
            editButton.style.background = "url('/static/pic/save_button.svg') no-repeat center center";
            editButton.title = "Save Changes";
        } else {
            editButton.style.background = "url('/static/pic/edit_button.svg') no-repeat center center";
            editButton.title = "Edit Form";
        }
    });
}


/**
 * Логика для кнопки "+". Открывает popup с отфильтрованными предложениями.
 * 
 * Функциональность:
 * - Добавляет обработчики событий для всех кнопок с классом "icon-btn--add-sentence".
 * - При нажатии на кнопку создает пустое редактируемое предложение и добавляет его в DOM перед кнопкой.
 * - Отправляет запрос на сервер для получения предложений, связанных с параграфом, к которому принадлежит кнопка.
 * - Отображает popup с полученными предложениями, позволяя пользователю выбрать одно из них.
 * - Выбранное предложение добавляется как новый элемент предложения.
 * - Обновляет текст параграфа после добавления предложения.
 * - Обрабатывает ситуации, когда popup скрывается или новое предложение остается пустым.
 * 
 * Требования:
 * - Элементы кнопок с классом "icon-btn--add-sentence" должны присутствовать на странице.
 * - Серверный маршрут "/working_with_reports/get_sentences_with_index_zero" должен возвращать данные в формате JSON с массивом предложений.
 * - Должны быть доступны функции `createEditableSentenceElement`, `showPopup`, `updateCoreParagraphText`, и `hidePopup`.
 * - Должен быть определен CSRF-токен для безопасности запросов.
 * 
 * Использование:
 * - Вызвать эту функцию после полной загрузки DOM.
 * 
 * Примечания:
 * - Если предложения для параграфа отсутствуют, будет выведено сообщение об ошибке в консоль.
 * - Если текст нового предложения остается пустым после потери фокуса, оно автоматически удаляется.
 */
function addSentenceButtonLogic() {
    document.querySelectorAll(".icon-btn--add-sentence").forEach(button => {
        button.addEventListener("click", function(event) {
            const paragraphId = this.getAttribute("data-paragraph-id");
            console.log("paragraphId", paragraphId);
            // Создаем пустое предложение и добавляем перед кнопкой
            const newSentenceElement = createEditableSentenceElement("",paragraphId);
            button.parentNode.insertBefore(newSentenceElement, button);
            newSentenceElement.focus(); // Устанавливаем фокус на новый элемент

            // Получаем предложения с индексом 0 для этого параграфа
            sendRequest({
                url: "/working_with_reports/get_sentences_with_index_zero",
                method: "POST",
                data: { paragraph_id: paragraphId },
                csrfToken: csrfToken
            }).then(data => {
                if (data.sentences && data.sentences.length > 0) {
                    // Используем popup для показа предложений
                    showPopup(event.pageX, event.pageY, data.sentences, function(selectedSentence) {
                        // Логика при выборе предложения из popup
                        const newSentenceElement = createEditableSentenceElement(selectedSentence.sentence, paragraphId);
                        button.parentNode.insertBefore(newSentenceElement, button);
                        updateCoreParagraphText(); // Обновляем текст абзаца после добавления предложения
                        newSentenceElement.focus(); // Устанавливаем фокус на новый элемент
                    });
                } else {
                    console.warn("No sentences available for this paragraph.");
                }
            }).catch(error => {
                console.error("Error fetching sentences:", error);
            });

            // Логика скрытия popup или удаления предложения
            newSentenceElement.addEventListener("input", function() {
                hidePopup(); // Скрываем popup при начале ввода
            });

            newSentenceElement.addEventListener("blur", function() {
                if (newSentenceElement.textContent.trim() === "") {
                    // Удаляем пустое предложение, если потеряно фокус без ввода текста
                    newSentenceElement.remove();
                }
            });
        });
    });
}


/**
 * Обрабатывает логику кнопки "Copy to Clipboard".
 * 
 * Функциональность:
 * - При нажатии на кнопку собирает текст из параграфов с классами "paragraph__list--initial", "paragraph__list--core", и "paragraph__list--impression".
 * - Формирует общий текст, объединяя данные из указанных параграфов.
 * - Копирует сформированный текст в буфер обмена.
 * - Отправляет собранные данные абзацев на сервер для обработки.
 * - При успешной обработке отображает обновленные данные абзацев на странице.
 * 
 * Требования:
 * - Должна быть доступна функция `collectTextFromParagraphs` для извлечения текста из параграфов.
 * - Должна быть доступна функция `collectParagraphsData` для сбора данных абзацев.
 * - Должны быть доступны функции `sendRequest` для выполнения HTTP-запросов и `displayProcessedParagraphs` для отображения обновленных данных.
 * - Должен быть подключен библиотека `toastr` для отображения уведомлений.
 * - Серверный маршрут "/working_with_reports/new_sentence_adding" должен принимать данные абзацев и возвращать обработанные данные.
 * - Должен быть определен CSRF-токен для безопасности запросов.
 * 
 * Использование:
 * - Вызвать эту функцию и передать элемент кнопки "Copy to Clipboard" как аргумент.
 * - Функция автоматически добавит обработчик событий к переданной кнопке.
 * 
 * Примечания:
 * - В случае успешного копирования отображается уведомление с помощью `toastr.success`.
 * - При возникновении ошибок копирования или отправки данных выводится сообщение об ошибке.
 * 
 * Аргументы:
 * @param {HTMLElement} copyButton - Элемент кнопки "Copy to Clipboard".
 */
function copyButtonLogic(copyButton) {
    copyButton.addEventListener("click", async function () {

        // Собираем текст из параграфов
        const initialText = collectTextFromParagraphs("paragraph__list--initial");
        const coreText = collectTextFromParagraphs("paragraph__list--core");
        const impressionText = collectTextFromParagraphs("paragraph__list--impression");

        // Соединяем все части с пустой строкой между ними
        const textToCopy = `${initialText}\n\n${coreText}\n\n${impressionText}`.trim();

        try {
            // Копируем текст в буфер обмена
            await navigator.clipboard.writeText(textToCopy);
            toastr.success("Text copied to clipboard successfully", "Success");

            // После успешного копирования выполняем отправку данных
            const paragraphsData = collectParagraphsData();

            // Отправляем данные параграфов
            // await sendParagraphsData(paragraphsData);
            await sendModifiedSentencesToServer();
            
        } catch (error) {
            alert(error.message || "Failed to process paragraphs.");
        }
    });
}


/**
 * Функция для отправки данных предложений на сервер.
 * Это старая функция, я ее пока оставляю, но потом ее нужно будет переделать.
 * 
 * @param {Array} paragraphsData - The data of paragraphs to send.
 */
async function sendParagraphsData(paragraphsData) {
    try {
        const response = await sendRequest({
            url: "/working_with_reports/new_sentence_adding",
            method: "POST",
            data: { paragraphs: paragraphsData },
            csrfToken: csrfToken
        });

        // Если запрос успешен, отображаем обработанные абзацы
        displayProcessedParagraphs(response.processed_paragraphs);
        console.log("sendParagraphsData: Successfully sent paragraphs data.");
    } catch (error) {
        console.error("sendParagraphsData: Failed to send paragraphs data.", error);
        alert(error.message || "Не удалось обработать абзацы.");
    }
}


/**
 * Обрабатывает логику кнопки "Export to Word".
 * 
 * Функциональность:
 * - Собирает текст из абзацев с классами "paragraph__list--initial", "paragraph__list--core", и "paragraph__list--impression".
 * - Отправляет данные абзацев на сервер для обработки.
 * - При успешной обработке данных выполняет экспорт текста в формат Word.
 * - Формирует имя файла на основе имени пациента, типа отчета, подтипа отчета и текущей даты.
 * - Позволяет пользователю скачать сгенерированный файл Word.
 * 
 * Требования:
 * - Должна быть доступна функция `collectTextFromParagraphs` для извлечения текста из параграфов.
 * - Должна быть доступна функция `collectParagraphsData` для сбора данных абзацев.
 * - Должны быть доступны функции `sendRequest` для выполнения HTTP-запросов и `displayProcessedParagraphs` для отображения обновленных данных.
 * - Должен быть подключен CSRF-токен для безопасности запросов.
 * - Серверные маршруты:
 *   - "/working_with_reports/new_sentence_adding" для обработки данных абзацев.
 *   - "/working_with_reports/export_to_word" для создания файла Word.
 * - Поля ввода с идентификаторами "patient-name", "patient-birthdate", "report-number" должны содержать соответствующие данные пациента.
 * 
 * Использование:
 * - Вызвать эту функцию и передать элемент кнопки "Export to Word" как аргумент.
 * - Функция автоматически добавит обработчик событий к переданной кнопке.
 * 
 * Примечания:
 * - При успешном завершении операций отображается уведомление об успехе.
 * - Если обработка данных или экспорт в Word завершились ошибкой, выводится сообщение об ошибке в консоль и пользователю.
 * - Файл Word формируется и скачивается автоматически.
 * 
 * Аргументы:
 * @param {HTMLElement} exportButton - Элемент кнопки "Export to Word".
 */
function wordButtonLogic(exportButton) {
    
    exportButton.addEventListener("click", async function() {
        // Собираем текст из разных списков абзацев
        const initialText = collectTextFromParagraphs("paragraph__list--initial");
        const coreText = collectTextFromParagraphs("paragraph__list--core");
        const impressionText = collectTextFromParagraphs("paragraph__list--impression");

        const textToExport = `${coreText}\n\n${impressionText}`.trim();
        const scanParam = initialText.trim();

        // Формируем данные абзацев
        const paragraphsData = collectParagraphsData();

        try {
            // Отправляем данные абзацев на сервер
            const response = await sendRequest({
                url: "/working_with_reports/new_sentence_adding",
                method: "POST",
                data: { paragraphs: paragraphsData },
                csrfToken: csrfToken
            });

            // Отображаем обработанные абзацы, если запрос успешен
            displayProcessedParagraphs(response.processed_paragraphs);
        } catch (error) {
            console.error("Ошибка обработки абзацев:", error);
            alert(error.message || "Не удалось обработать абзацы.");
            return;
        }

        // Если обработка абзацев успешна, выполняем экспорт в Word
        try {
            const name = document.getElementById("patient-name").value;
            const birthdate = document.getElementById("patient-birthdate").value;
            const reportnumber = document.getElementById("report-number").value;

            const exportForm = document.getElementById("exportForm");
            const subtype = exportForm.getAttribute("data-subtype");
            const reportType = exportForm.getAttribute("data-report-type");

            const reportSideElement = document.getElementById("report-side");
            const reportSide = reportSideElement ? reportSideElement.value : "";

            const blob = await sendRequest({
                url: "/working_with_reports/export_to_word",
                method: "POST",
                data: {
                    text: textToExport,
                    name: name,
                    birthdate: birthdate,
                    subtype: subtype,
                    report_type: reportType,
                    reportnumber: reportnumber,
                    scanParam: scanParam,
                    side: reportSide
                },
                responseType: "blob",
                csrfToken: csrfToken
            });

            // Создаем ссылку для скачивания файла
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            const currentDate = new Date();
            const day = currentDate.getDate();
            const month = currentDate.getMonth() + 1;
            const year = currentDate.getFullYear();
            const formattedDate = `${day.toString().padStart(2, '0')}${month.toString().padStart(2, '0')}${year}`;

            let fileReportSide = "";
            if (reportSide === "right") {
                fileReportSide = " правая сторона";
            } else if (reportSide === "left") {
                fileReportSide = " левая сторона";
            }

            a.style.display = "none";
            a.href = url;
            a.download = `${name} ${reportType} ${subtype}${fileReportSide} ${formattedDate}.docx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);

        } catch (error) {
            console.error("Ошибка экспорта в Word:", error);
            alert(error.message || "Не удалось выполнить экспорт в Word.");
        }
    });
}


/**
 * Логика для кнопки "Generate Impression".
 * 
 * Функция обрабатывает нажатие на кнопку "Generate Impression". Она:
 * 1. Собирает текст из абзацев с классом "paragraph__list--core".
 * 2. Отправляет текст на сервер для генерации впечатления с помощью ассистента.
 * 3. Отображает результат в поле `aiResponse`.
 * 4. Обрабатывает ошибки, если запрос не удается.
 */
function generateImpressionLogic(generateButton, boxForAiResponse) {
    generateButton.addEventListener("click", async function () {
        const textToCopy = collectTextFromParagraphs("paragraph__list--core");
        const assistantNames = ["airadiologist"];
        boxForAiResponse.textContent = "Ожидаю ответа ИИ...";

        try {
            const aiResponse = await generateImpressionRequest(textToCopy, assistantNames);
            boxForAiResponse.textContent = aiResponse || "No response received.";
        } catch (error) {
            console.error(error);
            boxForAiResponse.textContent = "An error occurred. Please try again.";
        }
    });
}

/**
 * Логика кнопки "Add Impression to Report".
 * 
 * Функция обрабатывает нажатие на кнопку "Add Impression to Report" для добавления сгенерированного ИИ заключения в отчет.
 * 
 * Шаги выполнения:
 * 1. Извлекает текст заключения из элемента с ID `aiResponse`.
 * 2. Если текст пуст, отображает предупреждение пользователю о необходимости сгенерировать заключение.
 * 3. Ищет первый видимый элемент предложения в абзацах с классом `paragraph__list--impression`.
 * 4. Заменяет текст найденного предложения на текст из `aiResponse`.
 * 
 * В случае отсутствия видимого предложения:
 * - Отображает предупреждение о том, что не найдено видимых предложений для вставки.
 * 
 * Требования:
 * - Элемент с ID `addImpressionToReportButton` (кнопка).
 * - Элемент с ID `aiResponse` для получения текста заключения.
 * - Элементы с классом `paragraph__list--impression .report__sentence` для вставки текста.
 * - Функция `isElementVisible` для проверки видимости элементов.
 */
function addImpressionButtonLogic(addImpressionButton) {
    addImpressionButton.addEventListener("click", function() {
        // Получаем текст ответа ИИ
        const aiResponseText = document.getElementById("aiResponse")?.innerText.trim();

        if (!aiResponseText) {
            alert("Ответ ИИ пуст. Пожалуйста, сначала сгенерируйте впечатление.");
            return;
        }

        // Ищем первый видимый элемент предложения в paragraph__list--impression
        const impressionParagraphs = document.querySelectorAll(".paragraph__list--impression .report__sentence");
        let foundVisibleSentence = false;

        impressionParagraphs.forEach(sentenceElement => {
            if (isElementVisible(sentenceElement) && !foundVisibleSentence) {
                // Заменяем текст первого видимого предложения на ответ ИИ
                sentenceElement.textContent = aiResponseText;
                foundVisibleSentence = true;  // Останавливаем поиск после первого найденного
            }
        });

        if (!foundVisibleSentence) {
            alert("Не найдено видимых предложений для впечатлений.");
        }
    });
}

/** Функция для нормализации предложения.*/
function normalizeSentence(sentence, keyWordsGroups) {
    // Приводим текст к нижнему регистру
    sentence = sentence.toLowerCase();

    // Убираем лишние пробелы
    sentence = sentence.replace(/\s+/g, " ").trim();

    // Удаляем лишние символы пунктуации
    sentence = sentence.replace(/[.,!?;:()"]/g, "");

    // Проходим по группам ключевых слов
    keyWordsGroups.forEach((group, groupIndex) => {
        group.forEach(keyword => {
            const regex = new RegExp(`\\b${keyword.word}\\b`, "gi");
            sentence = sentence.replace(regex, `{${groupIndex}}`);
        });
    });

    // Заменяем числа на плейсхолдеры
    sentence = sentence.replace(/\b\d+(\.\d+)?\b/g, "{число}");

    // Убираем повторяющиеся слова
    sentence = sentence.replace(/\b(\w+)\b\s+\1\b/g, "$1");

    return sentence;
}


/**
 * Adds focus and blur listeners to sentence elements with logging.
 * 
 * - On `focus`: Saves the original text of the sentence in a `data-original-text` attribute.
 * - On `blur`: Checks if the text has been modified and logs the decision-making process.
 */
// function addFocusListeners() {
//     // Находим все предложения на странице
//     const sentenceElements = document.querySelectorAll(".report__sentence");

//     sentenceElements.forEach(sentenceElement => {
//         // Сохраняем оригинальный текст при получении фокуса
//         sentenceElement.addEventListener("focus", function () {
//             if (!this.hasAttribute("data-original-text")) {
//                 this.setAttribute("data-original-text", this.textContent.trim());
//                 console.log("Focus: Original text saved:", this.textContent.trim());
//             }
//         });

//         // Обрабатываем изменения при потере фокуса
//         sentenceElement.addEventListener("blur", function () {
//             const originalText = this.getAttribute("data-original-text");
//             const currentText = this.textContent.trim();
//             const paragraphId = this.getAttribute("data-paragraph-id");
//             const sentenceId = this.getAttribute("data-id");

            
//             console.log(`Blur: Processing text for sentence (ID: ${sentenceId}, Paragraph: ${paragraphId})`);
//             console.log("Blur: normalized current text:", normalizeSentence(currentText, keyWordsGroups));
//             // Если текст пустой, ничего не делаем
//             if (!currentText) {
//                 console.log("Blur: Text is empty. Ignoring.");
//                 return;
//             }

//             // Если текст совпадает с оригиналом, ничего не делаем
//             if (normalizeSentence(originalText, keyWordsGroups) === normalizeSentence(currentText, keyWordsGroups)) {
//                 console.log("Blur: Text matches the original. No changes detected.");
//                 return;
//             }

//             // Сравниваем с linkedSentences
//             const linkedSentences = this.linkedSentences || [];
//             const isDuplicate = linkedSentences.some(sentence =>
//                 normalizeSentence(sentence.sentence, keyWordsGroups) === normalizeSentence(currentText, keyWordsGroups)
//             );

//             if (isDuplicate) {
//                 console.log("Blur: Text matches a linked sentence. No changes detected.");
//                 return;
//             }

//             // Помечаем предложение как изменённое
//             this.setAttribute("data-modified", "true");
//             this.classList.add("was-changed-highlighted-sentence");
//             console.log("Blur: Text is unique. Marking as modified.");
//         });
//     });
// }


/**
 * Adds focus and blur listeners to all sentence elements on the page.
 * Utilizes external handlers for focus and blur events.
 */
function addFocusListeners() {
    // Находим все предложения на странице
    const sentenceElements = document.querySelectorAll(".report__sentence");

    sentenceElements.forEach(sentenceElement => {
        // Attach focus and blur event listeners
        sentenceElement.addEventListener("focus", handleSentenceFocus);
        sentenceElement.addEventListener("blur", handleSentenceBlur);
    });

    console.log("Focus and blur listeners attached to all sentence elements.");
}


/**
 * Collects data of modified sentences and sends it to the server.
 * - Gathers all sentences with `data-modified="true"`.
 * - Formats the data as a JSON object for sending to the server.
 * - Uses `sendRequest` to make the API call.
 */
async function sendModifiedSentencesToServer() {
    // Находим все предложения, помеченные как изменённые
    const modifiedSentences = document.querySelectorAll("[data-modified='true']");
    const reportId = document.getElementById("csrf_token").dataset.reportId;
    console.log("Report ID:", reportId);
    if (modifiedSentences.length === 0) {
        console.log("No modified sentences to send.");
        toastr.info("No changes detected to save.");
        return;
    }

    const dataToSend = [];

    modifiedSentences.forEach(sentenceElement => {
        const paragraphId = sentenceElement.getAttribute("data-paragraph-id");
        const sentenceIndex = sentenceElement.getAttribute("data-index") || 0;

        const currentText = cleanSelectText(sentenceElement).trim();

        if(!currentText) {
            console.log("Empty sentence. Ignoring.");
            return;
        } 
        // Собираем данные для одного предложения
        dataToSend.push({
            paragraph_id: paragraphId,
            sentence_index: sentenceIndex,
            text: currentText
        });

        console.log(`Collected modified sentence: ${currentText} (Paragraph ID: ${paragraphId}, Index: ${sentenceIndex})`);
    });

    // Если нет данных для отправки, выводим сообщение и завершаем выполнение
    if (dataToSend.length === 0) {
        toastr.info("No valid modified sentences to send.");
        return;
    }

    // Формируем данные для отправки
    const requestData = {
        sentences: dataToSend,
        report_id: reportId
    };

    try {
        // Отправляем запрос на сервер
        const response = await sendRequest({
            url: "/working_with_reports/save_modified_sentences",
            method: "POST",
            data: requestData,
            csrfToken: csrfToken // предполагаем, что CSRF-токен доступен глобально
        });
        
        if (response.status === "success") {
            const bottomContainer = document.getElementById("bottomContainer");
            const reportContainer = document.getElementById("sentenceAddingReportContainer");

            // Вставляем сгенерированный HTML в контейнер
            reportContainer.innerHTML = response.html;
            bottomContainer.style.display = "flex";
            // Убираем атрибут `data-modified` после успешного сохранения
            modifiedSentences.forEach(sentenceElement => {
                sentenceElement.removeAttribute("data-modified");
                sentenceElement.classList.remove("was-changed-highlighted-sentence");
            });
        }

        
        
    } catch (error) {
        // Обработка ошибок
        console.error("Error saving modified sentences:", error);
    }
}
