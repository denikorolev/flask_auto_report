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
    

    // Проверяем наличие списка неактивных абзацев и скрываем его, если он пуст
    const inactiveParagraphsList = document.querySelector(".report-controlpanel__inactive-paragraphs-list");
    const items = inactiveParagraphsList.querySelectorAll(".report-controlpanel__inactive-paragraphs-item");
    if (items.length === 0) {
        inactiveParagraphsList.style.display = "none"; // Скрываем ul
    }
    
    
    linkSentences(); // Связываем предложения с данными
    
    updateCoreAndImpessionParagraphText(); // Запускает выделение ключевых слов при загрузке страницы

    sentenceDoubleClickHandle () // Включаем логику двойного клика на предложение

    addSentenceButtonLogic(); // Включаем логику кнопки "+"


    

    
    // Слушатели на список неактивных абзацев
    document.getElementById("inactiveParagraphsList").querySelectorAll(".report-controlpanel__inactive-paragraphs-item").forEach(item => {
        item.addEventListener("click", function() {
            inactiveParagraphsListClickHandler(item);
        });
    });


    // Проверяем наличие кнопки экспорт в Word и при ее наличии запускаем логику связанную с данным экспортом
    if (exportButton) {
        wordButtonLogic(exportButton);
    }

    // Проверяем наличие кнопки "Копировать текст" и при ее наличии запускаем логику связанную с копированием текста
    if (copyButton) {
        copyButtonLogic(copyButton);
    }

    // Проверяем наличие кнопки "Следующий пациент и при ее наличии запускаем логику связанную 
    // с созданием нового пациента и автоматическим увеличением номера отчета" Это для работы в рамках логики Word
    if (nextReportButton) {
        nextButtonLogic(nextReportButton);
    }

    // Проверяем наличие кнопки "Edit Form" и при ее наличии запускаем логику связанную 
    // с редактированием формы. Это для формы, которая используется для работы с Word
    if (editButton) {
        editButtonLogic(editButton);
    }

    // Проверяем наличие кнопки "Add Report" и при ее наличии запускаем логику связанную 
    // с добавлением нового отчета для текущего пациента (работа в рамках логики Word)
    if (addReportButton) {
        addReportButtonLogic(addReportButton);
    }

    if (generateButton) {
        generateImpressionLogic(generateButton, boxForAiResponse);
    }

    if (addImpressionButton) {
        addImpressionButtonLogic(addImpressionButton);
    }


    // Слушатель на получение и потерю фокуса для всех предложений
    document.querySelectorAll(".report__sentence").forEach(sentenceElement => {
        // Attach focus and blur event listeners
        sentenceElement.addEventListener("focus", handleSentenceFocus);
        sentenceElement.addEventListener("blur", handleSentenceBlur);
    }); 


    // Слушатель на кнопку "Завершить"
    document.getElementById("finishWork").addEventListener("click", function() {
        finishWorkAndSaveSnapShot();
    });


    // Слушатель на кнопку "Проверить протокол ИИ"
    document.getElementById("aiReportCheck").addEventListener("click", function() {
        checkReportAI(boxForAiResponse);
    });
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
    }
}



/**
 * Handles the blur event for a sentence element.
 * Checks for changes and marks the sentence as modified if needed.
 */
function handleSentenceBlur() {
    const originalText = this.getAttribute("data-original-text");
    const currentText = this.textContent;
    const linkedSentences = this.linkedSentences || [];
    const firstGrammaCheckedText = this.getAttribute("data-first-gramma-checked-text") || "";
    
    if (!currentText) {return;}
    
    const normalizedCurrent = normalizeSentence(currentText, keyWordsGroups);
    const normalizedOriginal = normalizeSentence(originalText, keyWordsGroups);
    const normalizedFirstGrammaChecked = normalizeSentence(firstGrammaCheckedText, keyWordsGroups);

    // Проверяем, совпадает ли с оригинальным текстом
    if (normalizedFirstGrammaChecked === normalizedCurrent) {return;}
    if (normalizedCurrent === normalizedOriginal) {return;}
    
    const isDuplicate = linkedSentences.some(sentence =>
        normalizeSentence(sentence.sentence, keyWordsGroups) === normalizedCurrent
    );
    if (isDuplicate) {
        return;
    }

    const GrammaCheckedText = firstGrammaSentence(currentText);
    this.textContent = GrammaCheckedText;
    this.setAttribute("data-first-gramma-checked-text", GrammaCheckedText);
    
    highlightKeyWords(this);
    
    if (!this.hasAttribute("data-sentence-modified")) {
        this.setAttribute("data-sentence-modified", "true");
        this.classList.add("was-changed-highlighted-sentence");
    }
}

/**
 * Создает редактируемый элемент предложения, обернутый в <span>.
 * Добавляет необходимые атрибуты и привязывает обработчики событий 
 */
function createEditableSentenceElement(sentenceText, paragraphId) {
    const newSentenceElement = document.createElement("span");
    newSentenceElement.classList.add("report__sentence"); // Добавляем класс для стилизации и идентификации
    newSentenceElement.dataset.paragraphId = paragraphId; // Привязываем к конкретному абзацу
    newSentenceElement.dataset.sentenceType = "tail" // Новое предложение всегда получает тип "tail"
    newSentenceElement.textContent = sentenceText; 
    newSentenceElement.setAttribute("data-original-text", "new-sentence"); // Устанавливаем атрибут чтобы было понятно что это новое предложение
    
    // Делаем элемент редактируемым
    newSentenceElement.contentEditable = "true";
    
    // Добавляем обработчики событий для отслеживания изменений
    
    newSentenceElement.addEventListener("focus", handleSentenceFocus); // Сохраняем исходный текст при фокусе
    newSentenceElement.addEventListener("blur", handleSentenceBlur);   // Проверяем изменения при потере фокуса

    // Слушатель на энтер для потери фокуса при его нажатии
    newSentenceElement.addEventListener("keydown", function(e) {
        if (e.key === "Enter") {
            e.preventDefault();
            this.blur();
        }
    });

    return newSentenceElement;
}



/**
 * Проверяет, виден ли элемент на экране.
 */
function isElementVisible(element) {
    const style = window.getComputedStyle(element);
    return style.display !== "none" && style.visibility !== "hidden";
}


/**
 * Очищает текст элемента, удаляя кнопки и HTML-теги.
 */
function cleanSelectText(element) {
    let text = element.innerHTML;

    // Remove all buttons from the text
    element.querySelectorAll("button").forEach(button => {
        button.remove();  // Remove buttons from DOM to avoid interference with text collection
    });

    // Remove all HTML tags except text
    text = text.replace(/<[^>]*>/gm, '').trim();

    // Use a DOM parser to replace entities
    const tempElement = document.createElement("textarea");
    tempElement.innerHTML = text;
    text = tempElement.value;

    // Удаляет лишние пробелы
    text = text.replace(/\s\s+/g, ' ');

    return text;
}


/**
 * Выделяет ключевые слова в переданном элементе.
 */
function highlightKeyWords(element) {
    if (!element || !(element instanceof HTMLElement)) return;

    let originalText = element.innerHTML;

    let text = originalText; // Работаем с копией, чтобы следить за изменениями

    keyWordsGroups.forEach(group => {
        group.forEach(keyword => {
            const word = keyword.word;

            // Улучшенный regex:
            // 1. Проверяем, не находится ли слово уже внутри <span> (не трогаем уже выделенные слова).
            // 2. Ищем только целые слова (чтобы не выделять часть слова).
            const regex = new RegExp(
                `(?<!<span[^>]*>)(?<!\\p{L})${word}(?!\\p{L})(?![^<]*<\\/span>)`,
                "giu"
            );

            text = text.replace(regex, (matchedWord) => {
                // Проверяем, была ли первая буква заглавной
                const isCapitalized = matchedWord.charAt(0) === matchedWord.charAt(0).toUpperCase();
                const transformedGroup = isCapitalized
                    ? group.map(item => item.word.charAt(0).toUpperCase() + item.word.slice(1))
                    : group.map(item => item.word.toLowerCase());

                    const replacement = `<span class="keyword-highlighted" 
                    data-keywords="${transformedGroup.join(",")}" 
                    onclick="handleKeywordClick(event)">${matchedWord}</span>`;
                    return replacement;
            });
        });
    });

    if (text !== originalText) {
        element.innerHTML = text;
    } 
}


/**
 * Обрабатывает клик по ключевому слову и открывает popup с вариантами.
 */
function handleKeywordClick(event) {
    const span = event.target;
    

    if (!span.classList.contains("keyword-highlighted")) return;

    const keywordList = span.dataset.keywords.split(","); // Берем из `data-keywords`

    if (keywordList.length === 0) {
        console.warn("Нет связанных ключевых слов:", span.textContent);
        return;
    }

    showPopupSentences(event.pageX, event.pageY, keywordList.map(word => ({ sentence: word })), (selectedWord) => {
        span.textContent = selectedWord.sentence;
    });
}



/**
 * Обновляет текст абзацев с классом `paragraph__item--core` и "paragraph__item--impression" и выделяет ключевые слова.
 * 
 */
function updateCoreAndImpessionParagraphText() {
    const coreAndImpessionParagraphLists = document.querySelectorAll(".paragraph__item--core, .paragraph__item--impression");
    coreAndImpessionParagraphLists.forEach(paragraphList => {
        paragraphList.querySelectorAll("span").forEach(paragraph => {
            if (isElementVisible(paragraph)) { // Проверяем, виден ли элемент
                highlightKeyWords(paragraph);
            }
        });
    });
}




// Собирает текст из абзацев на основе указанного класса. САМОЕ ВАЖНОЕ
function collectTextFromParagraphs(paragraphClass) {
    const paragraphLists = document.querySelectorAll(`.${paragraphClass}`); // Ищем списки по указанному классу
    let collectedText = "";

    paragraphLists.forEach(paragraphList => {
        // Находим элемент абзаца
        const paragraphElement = paragraphList.querySelector(".paragraph__item > p");
        
        
        if (!paragraphElement) {
            console.error("Paragraph element not found in", paragraphClass);
            return;
        }

        const strBefore = paragraphElement.getAttribute("data-paragraph-str-before") === "True";
        const strAfter = paragraphElement.getAttribute("data-paragraph-str-after") === "True";

        // Добавляем новую строку перед абзацем, если есть соответсвующий флаг даже если текст абзаца не виден
        if (strBefore) {
            collectedText += "\n";
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

            // Добавляем новую строку после абзаца, если есть соответсвующий флаг. 
            if (strAfter) {
                collectedText += "\n";
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


// Функция для получения предложения по его ID из данных с сервера 
// при условии что я уже получил данные параграфа. Если больше нигде 
// не будет использоваться то можно просто поместить в фунцию linkSentences
function findHeadSentenceById(paragraphData, sentenceId) {
    for (const headIndex in paragraphData.head_sentences) {
        const headSentence = paragraphData.head_sentences[headIndex];
        if (headSentence.id === sentenceId) {
            return headSentence;
        }
    }
    return null; // Если не найдено
}


// Связывает head предложения с body предложениями. САМОЕ ВАЖНОЕ
function linkSentences() {
    // Находим все предложения на странице
    const sentencesOnPage = document.querySelectorAll(".report__sentence");
    // Проходим по каждому предложению на странице
    sentencesOnPage.forEach(sentenceElement => {
        const paragraphId = parseInt(sentenceElement.getAttribute("data-paragraph-id"));
        const sentenceId = parseInt(sentenceElement.getAttribute("data-id"));

        const paragraphData = currentReportParagraphsData.find(paragraph => paragraph.id === paragraphId) || null;
        const currentHeadSentence = paragraphData.head_sentences.find(sentence => sentence.id === sentenceId) || null;
        const bodySentences = currentHeadSentence.body_sentences;

            // Связываем видимое предложение с отфильтрованными предложениями из reportData
            sentenceElement.linkedSentences = bodySentences;

            // Если есть связанные предложения, выделяем цветом текущее предложение
            if (sentenceElement.linkedSentences.length > 0) {
                sentenceElement.classList.add("has-linked-sentences-highlighted-sentence");
            }
            // Слушатель на enter для потери фокуса при его нажатии
            sentenceElement.addEventListener("keydown", function(e) {
                if (e.key === "Enter") {
                    e.preventDefault();
                    this.blur();
                }
            });
    });
}


// Добавляет обработчики двойного клика и ввода для элементов предложений на странице. САМОЕ ВАЖНОЕ
function sentenceDoubleClickHandle (){
    const sentencesOnPage = document.querySelectorAll(".report__sentence");
    sentencesOnPage.forEach(sentenceElement => {
        // Добавляю слушатель двойного клика на предложение
        sentenceElement.addEventListener("dblclick", function(event){
            activeSentence = sentenceElement;
            if (sentenceElement.linkedSentences && sentenceElement.linkedSentences.length > 0) {
                // Передаем функцию, которая заменяет текст предложения
                showPopupSentences(event.pageX, event.pageY, sentenceElement.linkedSentences, (selectedSentence) => {
                    activeSentence.textContent = selectedSentence.sentence; // Заменяем текст предложения
                    activeSentence.focus(); // Устанавливаем фокус на предложение
                    activeSentence.blur(); // Убираем фокус

                    //  Увеличиваем вес предложения
                    if (selectedSentence.id && selectedSentence.group_id) {
                        increaseSentenceWeight({
                            sentence_id: selectedSentence.id,
                            group_id: selectedSentence.group_id,
                            sentence_type: "body"
                        });
                    }
                    
                });
            } else {
                console.warn("No linked sentences or linked sentences is not an array");
            }
        });
        // Добавляю слушатель начала ввода на предложение
        sentenceElement.addEventListener("input", function(event) {
            hidePopupSentences();
        });
    });
}

// Отправляет запрос на сервер для увеличения веса предложения
function increaseSentenceWeight({ sentence_id, group_id, sentence_type }) {
    fetch("/working_with_reports/increase_sentence_weight", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken
        },
        body: JSON.stringify({ sentence_id, group_id, sentence_type })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status !== "success") {
            console.warn("⚠️ Ошибка при увеличении веса:", data.message);
        } else {
            console.log("✅ Вес предложения успешно увеличен:");
        }
    })
    .catch(err => {
        console.error("❌ Не удалось увеличить вес предложения:", err);
    });
}


// Обрабатывает логику кнопки "Next". Это для работы в рамках логики Word
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



// Логика для кнопки "Add Report". Это для работы в рамках логики Word
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



// Логика для кнопки "Edit Form". Это для работы в рамках логики Word
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

// Функция для поиска по введенным в поисковое поле словам среди прикрепленных 
// предложений. Используется в showPopupSentences и addSentenceButtonLogic
function matchesAllWords(text, query) {
    const words = query.toLowerCase().trim().split(/\s+/);
    const normalized = text.toLowerCase().replace(/[.,!?;:]/g, "");
    return words.every(word => normalized.includes(word));
}


// Логика для кнопки "+". Открывает popup с отфильтрованными предложениями.
function addSentenceButtonLogic() {
    document.querySelectorAll(".icon-btn--add-sentence").forEach(button => {
        button.addEventListener("click", function(event) {
            const paragraphId = parseInt(this.closest(".paragraph__item").querySelector("p").getAttribute("data-paragraph-id"));
            // Создаем пустое предложение и добавляем перед кнопкой
            const newSentenceElement = createEditableSentenceElement("", paragraphId);
            button.parentNode.insertBefore(newSentenceElement, button);
            newSentenceElement.focus(); // Устанавливаем фокус на новый элемент
            // Получаем данные параграфа по его ID из данных с сервера
            const paragraph = currentReportParagraphsData.find(paragraph => paragraph.id === paragraphId) || null;
            const tailSentences = paragraph.tail_sentences;
           
            if (tailSentences && tailSentences.length > 0) {
                // Используем popup для показа предложений
                showPopupSentences(event.pageX, event.pageY, tailSentences, function(selectedSentence) {
                    // Логика при выборе предложения из popup
                    const newSentenceElement = createEditableSentenceElement(selectedSentence.sentence, paragraphId);
                    button.parentNode.insertBefore(newSentenceElement, button);
                    newSentenceElement.focus(); // Устанавливаем фокус на новый элемент
                    newSentenceElement.blur(); // Убираем фокус
                    highlightKeyWords(newSentenceElement); // Обновляем текст абзаца после добавления предложения

                    if (selectedSentence.id && selectedSentence.group_id) {
                        increaseSentenceWeight({
                            sentence_id: selectedSentence.id,
                            group_id: selectedSentence.group_id,
                            sentence_type: "tail"
                        });
                    }

                });
            } else {
                console.warn("No sentences available for this paragraph.");
            }
            

            // Логика скрытия popup или удаления предложения
            newSentenceElement.addEventListener("input", function() {
                const inputText = this.textContent.toLowerCase().trim();
                const filtered = tailSentences.filter(sentence =>
                    matchesAllWords(sentence.sentence, inputText)
                );

                if (filtered.length > 0) {
                    showPopupSentences(event.pageX, event.pageY, filtered, function (selectedSentence) {
                        newSentenceElement.textContent = selectedSentence.sentence;
                        highlightKeyWords(newSentenceElement);
                    });
                } else {
                    hidePopupSentences();
                }
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


// Логика для кнопки "Copy". САМАЯ ВАЖНАЯ ЧАСТЬ
function copyButtonLogic(copyButton) {
    copyButton.addEventListener("click", async function () {

        // Собираем текст из параграфов
        const coreText = collectTextFromParagraphs("paragraph__item--core");
        const impressionText = collectTextFromParagraphs("paragraph__item--impression");

        // Соединяем все части с пустой строкой между ними
        const textToCopy = `${coreText}\n\n${impressionText}`.trim();
        
        try {
            // Копируем текст в буфер обмена
            await navigator.clipboard.writeText(textToCopy);
            toastr.success("Текст успешно скопирован в буфер обмена");

            // После успешного копирования выполняем отправку данных
            // const paragraphsData = collectParagraphsData();

            // Отправляем данные параграфов
            // await sendParagraphsData(paragraphsData);
            
            if (userSettings.USE_SENTENCE_AUTOSAVE) {
                await sendModifiedSentencesToServer();
            }
            
        } catch (error) {
            alert(error.message || "Failed to process paragraphs.");
        }
    });
}



// Логика для кнопки "Export to Word". Сильно поменялось, может не работать
function wordButtonLogic(exportButton) {
    
    exportButton.addEventListener("click", async function() {
        // Собираем текст из разных списков абзацев
        const coreText = collectTextFromParagraphs("paragraph__item--core");
        const impressionText = collectTextFromParagraphs("paragraph__item--impression");

        const textToExport = `${coreText}\n\n${impressionText}`.trim();

        // Формируем данные абзацев
        // const paragraphsData = collectParagraphsData();

        try {
            await sendModifiedSentencesToServer();
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


// Логика для кнопки "Generate Impression". Возможно нужно объединить с логикой generateImpressionRequest   
function generateImpressionLogic(generateButton, boxForAiResponse) {
    generateButton.addEventListener("click", async function () {
        const textToCopy = collectTextFromParagraphs("paragraph__item--core");
        boxForAiResponse.textContent = "Ожидаю ответа ИИ...";

        try {
            const aiResponse = await generateImpressionRequest(textToCopy);
            boxForAiResponse.textContent = aiResponse || "Ответ ИИ не получен.";
        } catch (error) {
            console.error(error);
            boxForAiResponse.textContent = "Ошибка при получении ответа ИИ.";
        }
    });
}



// Логика для кнопки "Add Impression".
function addImpressionButtonLogic(addImpressionButton) {
    addImpressionButton.addEventListener("click", function() {
        // Получаем текст ответа ИИ
        const aiResponseText = document.getElementById("aiResponse")?.innerText.trim();

        if (!aiResponseText) {
            alert("Ответ ИИ пуст. Пожалуйста, сначала сгенерируйте заключение.");
            return;
        }

        // Ищем первый видимый элемент предложения в paragraph__item--impression
        const impressionParagraphs = document.querySelectorAll(".paragraph__item--impression .report__sentence");
        let foundVisibleSentence = false;

        impressionParagraphs.forEach(sentenceElement => {
            if (isElementVisible(sentenceElement) && !foundVisibleSentence) {
                // Заменяем текст первого видимого предложения на ответ ИИ
                sentenceElement.textContent = aiResponseText;
                foundVisibleSentence = true;  // Останавливаем поиск после первого найденного
            }
        });

        if (!foundVisibleSentence) {
            alert("Не найдено видимых предложений для заключения.");
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
            const regex = new RegExp(`(^|[^\\p{L}\\d])${keyword.word}([^\\p{L}\\d]|$)`, "gui");
            sentence = sentence.replace(regex, `{${groupIndex}}`);
        });
    });

    // Заменяем числа на плейсхолдеры
    sentence = sentence.replace(/\b\d+(\.\d+)?\b/g, "{число}");

    // Убираем повторяющиеся слова
    sentence = sentence.replace(/\b(\w+)\b\s+\1\b/g, "$1");

    return sentence;
}



// Отправляет на сервер новые предложения для сохранения
async function sendModifiedSentencesToServer() {
    // Находим все предложения, помеченные как изменённые
    const modifiedSentences = document.querySelectorAll("[data-sentence-modified='true']");
    const reportId = reportData.id;
    if (modifiedSentences.length === 0) {
        toastr.info("Ни одно предложение не было изменено.");
        return;
    }

    const dataToSend = [];

    modifiedSentences.forEach(sentenceElement => {
        const paragraphId = sentenceElement.getAttribute("data-paragraph-id");
        const isAdditionalParagraph = sentenceElement.getAttribute("data-paragraph-additional") === "True";
        if (isAdditionalParagraph) {
            console.log("Additional paragraph found. Skipping...");
            return;
        }
        const sentenceType = sentenceElement.getAttribute("data-sentence-type") === "head" ? "body" : "tail";
        const currentText = cleanSelectText(sentenceElement).trim();
        const headSentenceId = sentenceElement.getAttribute("data-id" || null);

        if(!currentText) {
            return;
        } 
        // Собираем данные для одного предложения
        dataToSend.push({
            paragraph_id: paragraphId,
            text: currentText,
            type: sentenceType,
            head_sentence_id: headSentenceId
        });

    });

    // Если нет данных для отправки, выводим сообщение и завершаем выполнение
    if (dataToSend.length === 0) {
        toastr.info("Нет подходящих предложений для автоматического добавления в базу данных");
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
        });
        
        if (response.status === "success") {
            const bottomContainer = document.getElementById("bottomContainer");
            const reportContainer = document.getElementById("sentenceAddingReportContainer");

            // Вставляем сгенерированный HTML в контейнер
            reportContainer.innerHTML = response.html;
            bottomContainer.style.display = "flex";
            // Убираем атрибут `data-sentence-modified` после успешного сохранения
            modifiedSentences.forEach(sentenceElement => {
                sentenceElement.removeAttribute("data-sentence-modified");
                sentenceElement.classList.remove("was-changed-highlighted-sentence");
            });

            // Назначаем обработчик на кнопку "🧠 Учить выбранные"
            const trainSelectedButton = document.getElementById("trainSelectedSentencesButton");
            if (trainSelectedButton) {
                trainSelectedButton.addEventListener("click", () => {
                    const checkboxes = document.querySelectorAll(".train-sentence__checkbox:checked");
                    if (checkboxes.length === 0) {
                        alert("Выберите хотя бы одно предложение.");
                        return;
                    }

                    const selectedTexts = Array.from(checkboxes).map(cb => cb.dataset.text);
                    const combinedText = selectedTexts.join(" ");

                    showTrainingPopup(combinedText, async ({ text, sent_starts }) => {
                        try {
                            await sendRequest({
                                url: "/working_with_reports/train_sentence_boundary",
                                data: { text, sent_starts },
                            });
                            toastr.success("Пример отправлен на дообучение");
                        } catch (e) {
                            console.error("Ошибка обучения:", e);
                            alert("Ошибка отправки обучающего примера");
                        }
                    });
                });
            }
            // Назначаем обработчик на кнопку "❌ Удалить"
            const deleteBadSentenceButton = document.querySelectorAll(".train-sentence__btn--delete");
            if (deleteBadSentenceButton) {
                deleteBadSentenceButton.forEach(button => {
                    button.addEventListener("click", async () => {
                        const sentenceId = button.getAttribute("data-id");
                        const sentenceRelatedId = button.getAttribute("data-related-id");
                        const sentenceType = button.getAttribute("data-sentence-type");
                        try {
                            const response = await sendRequest({
                                url: "/editing_report/delete_sentence",
                                method: "DELETE",
                                data: { sentence_id: sentenceId,
                                        related_id: sentenceRelatedId,
                                        sentence_type: sentenceType
                                 },
                            });
                            if (response.status === "success") {
                                console.log("Предложение удалено:", response.message);
                                button.closest(".train-sentence__item").remove();
                            } else {
                                console.error("Ошибка удаления предложения:", response.message);
                            }
                        } catch (e) {
                            console.error("Ошибка удаления предложения:", e);
                            alert("Ошибка удаления предложения");
                        }
                    });
                });
            }

        }
        
    } catch (error) {
        // Обработка ошибок
        console.error("Error saving modified sentences:", error);
    }
}





// Очищает текст по заданным правилам
function firstGrammaSentence(sentence) {
    sentence = sentence.trim();
    if (!sentence) return sentence; // Если пустая строка — ничего не делаем

    sentence = sentence.replace(/\.{2,}$/g, ".") // Убираем двойные точки в конце предложения
    
    // Ставим точку в конце предложения, если ее нет, это специально 
    if (!/[.!?]$/.test(sentence)) {
        sentence += ".";
    }

    
    sentence = sentence.charAt(0).toUpperCase() + sentence.slice(1); //  Делаем первую букву заглавной
    sentence = sentence.replace(/(\d)\s*[гГ][р](?=[^\p{L}]|$)/gu, "$1°"); // `Гр и гр` после цифры → заменяем на `°`

    sentence = sentence.replace(/(\S+)\s*[.]?\s*\)/g, "$1)"); // Убираем точку и пробел перед `)`
    sentence = sentence.replace(/\)/g, ") "); // Добавляем пробел после `)`
    sentence = sentence.replace(/\(\s+/g, "("); // Убираем пробел после `(`

    sentence = sentence.replace(/([,.!?:;])(?=\p{L})/gu, "$1 "); // Добавляем пробел после знаков, если его нет, но только перед буквой, например 1,5 останется неизменным
    sentence = sentence.replace(/\s([,.!?:;])/g, "$1"); // Убираем пробел перед знаками препинания
    sentence = sentence.replace(/\s+/g, " "); // Заменяем несколько пробелов на один

    const abbreviations = userSettings.EXCEPTIONS_AFTER_PUNCTUATION;
    // Если слово в нижнем регистре и является аббревиатурой, то делаем его заглавным
    sentence = sentence.replace(/(?<!\p{L})[а-яёa-z-]+(?!\p{L})/giu, (match) => {
        const upperMatch = match.toUpperCase();
        return abbreviations.includes(upperMatch) ? upperMatch : match;
    });
    
    // Если слова стоит после `:`, то делаем его с маленькой буквы кроме аббревиатур из списка
    sentence = sentence.replace(/:\s*([А-ЯЁA-Z][а-яёa-z]+)/g, (match, word) =>
        abbreviations.includes(word.toUpperCase()) ? match : `: ${word.toLowerCase()}`
    );

    return sentence.trim();
}


// Функция для генерации запроса на сервер для получения заключения
function generateImpressionRequest(text) {
    // Формируем данные для отправки
    const reportType = reportData.report_type;
    let modality = reportType

    if (modality === "МРТ") {
        modality = "MRI";
    } else if (modality === "КТ") {
        modality = "CT";
    } else if (modality === "Рентгенография" || modality === "Рентгеноскопия") {
        modality = "XRAY";
    } else {
        alert("Неизвестный тип исследования: " + reportType);
        return;
    }

    const jsonData = {
        text: text,
        modality: modality
       
    };

    // Отправляем запрос на сервер с помощью sendRequest
    return sendRequest({   
        url: "/openai_api/generate_impression",
        data: jsonData,
        csrfToken: csrfToken
    }).then(data => {
        if (data.status === "success") {
            return data.data; // Возвращаем успешный ответ от сервера
        } else {
            return data.message; // Возвращаем сообщение об ошибке, если запрос не успешен
        }
    });
}



// Функция для обработки клика по неактивному параграфу в списке неактивных параграфов
function inactiveParagraphsListClickHandler(element) {
    const paragraphId = element.getAttribute("data-paragraph-id");
    const inactiveParagraphElement = document.querySelector(`.paragraph__item[data-paragraph-id="${paragraphId}"]`);

    if (inactiveParagraphElement) {
        const currentDisplay = window.getComputedStyle(inactiveParagraphElement).display;
        const newDisplay = (currentDisplay === "none") ? "block" : "none";
        inactiveParagraphElement.style.display = newDisplay;

        // Показываем/скрываем все предложения (span) внутри параграфа
        const sentenceSpans = inactiveParagraphElement.querySelectorAll(".report__sentence");
        sentenceSpans.forEach(span => {
            span.style.display = (newDisplay === "none") ? "none" : "inline";
        });

        // Работаем с параграфом (p)
        const paragraphText = inactiveParagraphElement.querySelector("p");
        if (paragraphText) {
            if (newDisplay === "none") {
                // Если скрываем весь li — скрываем и p
                paragraphText.style.display = "none";
            } else {
                // Если показываем — проверяем data-visible-paragraph
                const isVisible = paragraphText.getAttribute("data-visible-paragraph")?.toLowerCase() === "true";
                paragraphText.style.display = isVisible ? "block" : "none";
            }
        }
    }
}


// Функция для обработки клика по кнопке завершить. Завершает работу, 
// отправляется текст на сервер и переходит на страницу выбора отчета
function finishWorkAndSaveSnapShot() {
    const coreText = collectTextFromParagraphs("paragraph__item--core");
    const impressionText = collectTextFromParagraphs("paragraph__item--impression");

    const textToSave = `${coreText}\n\n${impressionText}`.trim();
    
    return sendRequest({
        url: "/working_with_reports/save_report_snapshot",
        method: "POST",
        data: {
            text: textToSave,
            report_id: reportData.id
        },
    }).then(data => {
        if (data.status === "success") {
            
            window.location.href = "/working_with_reports/choosing_report";
        } 
    }).catch(error => {
        console.error("Ошибка сохранения отчета:", error);
    });
}


// Функция для отправки протокола на проверку ИИ (REDACTOR)
function checkReportAI(boxForAiResponse){
    const coreText = collectTextFromParagraphs("paragraph__item--core");
    const impressionText = collectTextFromParagraphs("paragraph__item--impression");

    const textToCheck = `${coreText}\n\n${impressionText}`.trim();
    
    return sendRequest({
        url: "/openai_api/generate_redactor",
        method: "POST",
        data: {
            text: textToCheck,
        },
    }).then(data => {
        if (data.status === "success") {
            boxForAiResponse.innerText = data.data || "Ответ ИИ не получен.";
        } 
    }).catch(error => {
        console.error("Ошибка отправки отчета на проверку:", error);
    });
}