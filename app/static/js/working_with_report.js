// working_with_report.js
// у меня есть глобальные переменные const keyWordsGroups = {{ key_words_groups | tojson | safe }};
    // const reportData = {{ report_data | tojson | safe }};
    // const currentReportParagraphsData = {{ paragraphs_data | tojson | safe }};
    // MAX_ATTEMPTS_FOR_DYNAMICS

import { setupDynamicsDropZone, handleFileUpload, handlePasteFromClipboard } from "/static/js/utils/dynamicsDropZone.js";
import { prepareTextWithAI } from "/static/js/utils/ai_handlers.js";
import { pollTaskStatus, updateProgressBar } from "/static/js/utils/utils_module.js";      

let activeSentence = null;  // Для отслеживания активного предложения
document.addEventListener("DOMContentLoaded", initWorkingWithReport);



// Объявляем глобальные переменные и запускаем стартовые функции, постепенно нужно перенести сюда и логику связанную с ключевыми словами и развешивание части слушателей
function initWorkingWithReport() {

    console.log(userSettings);

    const popupList = document.getElementById("popupList");  // Для обращения к PopUp
    const copyButton = document.getElementById("copyButton"); // Для обращения к кнопке "Копировать текст"
    const generateButton = document.getElementById("generateImpression"); // Для обращения к кнопке Generate Impression
    const boxForAiImpressionResponse = document.getElementById("aiImpressionResponseBlock"); // Для обращения к блоку с ответом ИИ по заключению
    const boxForAiRedactorResponse = document.getElementById("aiRedactorResponseBlock"); // Для обращения к блоку с ответом ИИ по редактированию
    const boxForAiDynamicResponse = document.getElementById("aiDynamicBlock"); // Для обращения к блоку с ответом ИИ по динамическому отчету
    const addImpressionButton = document.getElementById("addImpressionToReportButton"); // Для обращения к кнопке "Вставить заключение"
    const dynamicReportButton = document.getElementById("dynamicReportButton"); // Для обращения к кнопке "Динамический отчет"
    

    // Проверяем наличие списка неактивных абзацев и скрываем его, если он пуст
    const inactiveParagraphsList = document.querySelector(".report-controlpanel__inactive-paragraphs-list");
    const items = inactiveParagraphsList.querySelectorAll(".report-controlpanel__inactive-paragraphs-item");
    if (items.length === 0) {
        inactiveParagraphsList.style.display = "none"; // Скрываем ul
    }
    
    
    linkSentences(); // Связываем предложения с данными
    
    updateCoreAndImpessionParagraphText(); // Запускает выделение ключевых слов при загрузке страницы

    sentenceDoubleClickHandle(); // Включаем логику двойного клика на предложение

    addSentenceButtonLogic(); // Включаем логику кнопки "+"

    

    
    // Слушатели на список неактивных абзацев
    document.getElementById("inactiveParagraphsList").querySelectorAll(".report-controlpanel__inactive-paragraphs-item").forEach(item => {
        item.addEventListener("click", function() {
            inactiveParagraphsListClickHandler(item);
        });
    });


    // Проверяем наличие кнопки экспорт в Word и при ее наличии запускаем логику связанную с данным экспортом


    // Проверяем наличие кнопки "Копировать текст" и при ее наличии запускаем логику связанную с копированием текста
    if (copyButton) {
        copyButtonLogic(copyButton);
    }

    if (generateButton) {
        generateButton.addEventListener("click", async function() {
            await generateImpressionLogic(boxForAiImpressionResponse, boxForAiRedactorResponse, boxForAiDynamicResponse);
        });
    }

    if (addImpressionButton) {
        addImpressionButton.addEventListener("click", function() {
            addImpressionButtonLogic(boxForAiImpressionResponse);
        });
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
        checkReportAI(boxForAiRedactorResponse, boxForAiImpressionResponse, boxForAiDynamicResponse);
    });

    // Слушатель на кнопку "Динамический отчет"
    if (dynamicReportButton) {
        dynamicReportButton.addEventListener("click", function() {
          // Показываем popup с динамическим отчетом
          showDynamicReportPopup(boxForAiImpressionResponse, boxForAiRedactorResponse);
        });
    }



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
 * Handles the focus event for a sentence element.
 * Saves the original text in a data attribute.
 */
function handleSentenceFocus() {
    if (!this.hasAttribute("data-original-text")) {
        this.setAttribute("data-original-text", this.textContent.trim());
    }
    console.log(this)
    // --- Вот тут надёжная проверка ---
    if (!this._onEnterHandler) {
        this._onEnterHandler = function(e, el) {
        el.blur()
        };
        onEnter(this, this._onEnterHandler, true);
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

    // Находим все ключевые слова в данном предложении и меняем их цвет на более светлый
    const keywords = this.querySelectorAll(".keyword-highlighted");
    keywords.forEach(keyword => {
        keyword.classList.add("keyword-highlighted--light");
    });

    // Снимаем слушатель нажатия Enter если он навешен на элемент
    if(this._onEnterHandler) {
        this.removeEventListener("keydown", this._onEnterHandler);
        delete this._onEnterHandler;
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
                    data-keywords="${transformedGroup.join(",")}">${matchedWord}</span>`;
                    return replacement;
            });
        });
    });

    if (text !== originalText) {
        element.innerHTML = text;
        // Навешиваем обработчик на все .keyword-highlighted
        element.querySelectorAll('.keyword-highlighted').forEach(span => {
            span.addEventListener('click', handleKeywordClick);
        });
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
    });
}


// Добавляет обработчики двойного клика и ввода для элементов предложений на странице. САМОЕ ВАЖНОЕ
function sentenceDoubleClickHandle (){
    const sentencesOnPage = document.querySelectorAll(".report__sentence");
    sentencesOnPage.forEach(sentenceElement => {
        // Добавляю слушатель двойного клика на предложение
        sentenceElement.addEventListener("dblclick", function(event){
            activeSentence = sentenceElement;
            console.log("activeSentence", activeSentence);
            if (sentenceElement.linkedSentences && sentenceElement.linkedSentences.length > 0) {
                // Передаем функцию, которая заменяет текст предложения
                showPopupSentences(event.pageX, event.pageY, sentenceElement.linkedSentences, (selectedSentence) => {
                    activeSentence.textContent = selectedSentence.sentence; // Заменяем текст предложения
                    activeSentence.focus(); // Устанавливаем фокус на предложение
                    activeSentence.blur(); // Убираем фокус
                    highlightKeyWords(activeSentence); // Обновляем текст абзаца после добавления предложения

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







// Функция для поиска по введенным в поисковое поле словам среди прикрепленных 
// предложений. Используется в showPopupSentences и addSentenceButtonLogic
window.matchesAllWords = function (text, query) {
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
                    window.matchesAllWords(sentence.sentence, inputText)
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

            
            if (userSettings.USE_SENTENCE_AUTOSAVE) {
                await sendModifiedSentencesToServer();
            }
            
        } catch (error) {
            alert(error.message || "Failed to process paragraphs.");
        }
    });
}



// Логика для кнопки "Generate Impression". Возможно нужно объединить с логикой generateImpressionRequest
async function generateImpressionLogic(boxForAiResponse, responseForDelete, boxForAiDynamicResponse) {
    const textToCopy = collectTextFromParagraphs("paragraph__item--core");
    if (!textToCopy || !textToCopy.trim()) {
        alert("Нет текста для генерации заключения.");
        return;
    }

    if (boxForAiResponse) {
        boxForAiResponse.innerText = "";
        boxForAiResponse.style.display = "block";
    }

    if (responseForDelete) {
        console.log("я стер блок", responseForDelete);
        responseForDelete.innerText = "";
        responseForDelete.style.display = "none";
    }
    if (boxForAiDynamicResponse) {
        boxForAiDynamicResponse.innerText = "";
        boxForAiDynamicResponse.style.display = "none";
    }

    // Прогресс-бар справа (scope по .report-controlpanel, чтобы не конфликтовать с попапом динамики)
    const panel = document.querySelector(".report-controlpanel");
    const barContainer = panel ? panel.querySelector("#dynamicsProgressBarContainer") : null;
    const barElem = panel ? panel.querySelector("#dynamicsProgressBar") : null;
    const labelElem = panel ? panel.querySelector("#dynamicsProgressBarLabel") : null;
    const textElem = panel ? panel.querySelector("#dynamicsProgressBarText") : null;

    const showBar = () => { if (barContainer) barContainer.style.display = "block"; };
    const hideBar = () => { if (barContainer) barContainer.style.display = "none"; };
    const setBar = (pct, msg = null) => updateProgressBar({ bar: barElem, label: labelElem, text: textElem }, pct, msg);
    showBar();
    setBar(0, "Генерация заключения...");

    try {
        // backend возвращает task.id в поле data
        const taskId = await generateImpressionRequest(textToCopy);
        if (!taskId || typeof taskId !== "string") {
            setBar(100, "Не удалось запустить задачу генерации заключения.");
            setTimeout(hideBar, 1500);
            return;
        }

        setBar(10, "Задача поставлена. Жду результат...");

        // Поллим статус (фоллбек-прогресс)
        pollTaskStatus(taskId, {
            maxAttempts: 10,
            interval: 4000,
            onProgress: (progress) => setBar(progress, "Ожидание результата..."),
            onSuccess: (result) => {
                setBar(100, "Готово!");
                const text = (typeof result === "string") ? result : (result && result.result) || "";
                boxForAiResponse.textContent = text || "Ответ ИИ не получен.";

                // Показываем кнопку Add Impression
                const addImpressionButton = document.getElementById("addImpressionToReportButton");
                if (text && addImpressionButton) {
                    addImpressionButton.style.display = "block";
                }

                // Enter в блоке ответа — вставка заключения
                if (!boxForAiResponse._onEnterHandler) {
                    boxForAiResponse._onEnterHandler = function(e, el) {
                        addImpressionButtonLogic(boxForAiResponse);
                    };
                    onEnter(boxForAiResponse, boxForAiResponse._onEnterHandler, true);
                }

                setTimeout(hideBar, 1000);
            },
            onError: (errMsg) => {
                setBar(100, errMsg || "Ошибка при выполнении задачи генерации заключения.");
                setTimeout(hideBar, 2000);
            },
            onTimeout: () => {
                setBar(100, "Превышено время ожидания. Попробуйте ещё раз позже.");
                setTimeout(hideBar, 2000);
            }
        });
    } catch (error) {
        console.error("Ошибка запуска генерации заключения:", error);
        setBar(100, error?.message || "Ошибка при запуске задачи.");
        setTimeout(hideBar, 2000);
    }
}



// Логика для кнопки "Add Impression".
function addImpressionButtonLogic(aiImpressionBox) {
        // Получаем текст ответа ИИ
        const aiResponseText = aiImpressionBox?.innerText.trim();
        console.log("aiResponseText", aiResponseText);

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

        // После вставки заключения — снимаем обработчик onEnter с aiImpressionBox
        if (aiImpressionBox && aiImpressionBox._onEnterHandler) {
            aiImpressionBox.removeEventListener("keydown", aiImpressionBox._onEnterHandler);
            delete aiImpressionBox._onEnterHandler;
        }
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
            console.log("Дополнительный параграф найден, пропускаем");
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






// Функция для генерации запроса на сервер для получения заключения
function generateImpressionRequest(text) {
    // Формируем данные для отправки
    const reportModality = parseInt(reportData.global_category_id);
    let modality = reportModality;

    if (modality === 2) {
        modality = "MRI";
    } else if (modality === 1) {
        modality = "CT";
    } else if (modality === 7) {
        modality = "XRAY";
    } else {
        alert("Неизвестный тип исследования: " + reportModality);
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
function checkReportAI(boxForAiResponse, responseForDelete, boxForAiDynamicResponse){
    const coreText = collectTextFromParagraphs("paragraph__item--core");
    const impressionText = collectTextFromParagraphs("paragraph__item--impression");

    if (boxForAiResponse) {
        boxForAiResponse.innerText = "";
        boxForAiResponse.style.display = "block";
    }

    if (responseForDelete) {
        responseForDelete.innerText = "";
        responseForDelete.style.display = "none";
    }
    if (boxForAiDynamicResponse) {
        boxForAiDynamicResponse.innerText = "";
        boxForAiDynamicResponse.style.display = "none";
    }

    const textToCheck = `${coreText}\n\n${impressionText}`.trim();
    if (!textToCheck) {
        alert("Нет текста для проверки. Пожалуйста, заполните протокол.");
        return;
    }
    // Прогресс-бар справа (строго в .report-controlpanel, чтобы не конфликтовать с попапом динамики)
    const panel = document.querySelector(".report-controlpanel");
    const barContainer = panel ? panel.querySelector("#dynamicsProgressBarContainer") : null;
    const barElem = panel ? panel.querySelector("#dynamicsProgressBar") : null;
    const labelElem = panel ? panel.querySelector("#dynamicsProgressBarLabel") : null;
    const textElem = panel ? panel.querySelector("#dynamicsProgressBarText") : null;

    const showBar = () => { if (barContainer) barContainer.style.display = "block"; };
    const hideBar = () => { if (barContainer) barContainer.style.display = "none"; };
    const setBar = (pct, msg = null) => updateProgressBar({ bar: barElem, label: labelElem, text: textElem }, pct, msg);

    showBar();
    setBar(0, "Идет проверка отчета...");

    sendRequest({
        url: "/openai_api/generate_redactor",
        data: {
            text: textToCheck,
        },
    })
    .then(startResp => {
        const { status, data, message } = startResp || {};
        if (status !== "success" || !data) {
            setBar(100, message || "Не удалось запустить задачу редактирования.");
            setTimeout(hideBar, 1500);
            return;
        }

        const taskId = data; // backend возвращает task.id
        setBar(10, "Задача поставлена. Жду результат...");

        // Поллим статус (только фоллбек-прогресс)
        pollTaskStatus(taskId, {
            maxAttempts: 10,
            interval: 4000,
            onProgress: (progress) => setBar(progress, "Ожидание результата..."),
            onSuccess: (result) => {
                setBar(100, "Готово!");
                const text = (typeof result === "string") ? result : (result && result.result) || "";
                boxForAiResponse.innerText = text || "Ответ ИИ не получен.";
                setTimeout(hideBar, 1000);
            },
            onError: (errMsg) => {
                setBar(100, errMsg || "Ошибка при выполнении задачи редактирования.");
                setTimeout(hideBar, 2000);
            },
            onTimeout: () => {
                setBar(100, "Превышено время ожидания. Попробуйте ещё раз позже.");
                setTimeout(hideBar, 2000);
            }
        });
    })
    .catch(error => {
        console.error("Ошибка отправки отчета на проверку:", error);
        setBar(100, error?.message || "Ошибка при запуске задачи.");
        setTimeout(hideBar, 2000);
    });
    
}


// Вся логика для показа динамического отчета (отчет в динамике)
async function showDynamicReportPopup(boxForAiImpressionResponse, boxForAiRedactorResponse) {
    const popup = document.getElementById("dynamicsPopup");
    window.previousDynamicsText = null; // Сброс предыдущего текста динамики
    if (!popup) {
        console.error("Popup element not found");
        return;
    }

    if (boxForAiImpressionResponse) {
        boxForAiImpressionResponse.innerText = "";
        boxForAiImpressionResponse.style.display = "none";
    }
    if (boxForAiRedactorResponse) {
        boxForAiRedactorResponse.innerText = "";
        boxForAiRedactorResponse.style.display = "none";
    }

    const closeDynamicsPopup = document.getElementById("closeDynamicsPopup");
    const analyzeDynamicsButton = document.getElementById("analyzeDynamicsButton");
    const dynamicsTextarea = document.getElementById("Textarea");
    const dynamicsPreview = document.getElementById("DropZonePreview");
    const pasteDynamicsButton = document.getElementById("pasteDynamicsButton");
    const prepareTextDynamicsButton = document.getElementById("prepareTextDynamicsButton");
    const dynamicFileUploadButton = document.getElementById("uploadFileDynamicsButton");
    const dynamicFileUploadInput = document.getElementById("dynamicFileUploadInput");

    // Очистка перед показом
    dynamicsTextarea.value = "";

    showElement(popup, false); // второй параметр это bool для useHideOnClickOutside

    let detachDropZone = setupDynamicsDropZone(
        {
            dropZoneId: "DropZone",
            previewId: "DropZonePreview",
            textareaId: "Textarea"
        }
    );

    // Внутренняя функция, нужна чтобы не вводить каждый раз параметры 
    // bar, label, text для универсальной функции updateProgressBar
    function updateDynamicsProgressBar(percent, statusText = null) {
        const progressBarContainer = document.getElementById("dynamicsProgressBarContainer");
        if (progressBarContainer && progressBarContainer.style.display === "none") {
            progressBarContainer.style.display = "block";
        }
        updateProgressBar(
            {
                bar: "dynamicsProgressBar",
                label: "dynamicsProgressBarLabel",
                text: "dynamicsProgressBarText"
            },
            percent,
            statusText
        );
    }

    // Обработчики (нужно сохранять ссылки, чтобы можно было удалить потом)
    const closeHandler = () => {
        hideElement(popup);
        dynamicsTextarea.value = "";
        dynamicsPreview.innerHTML = "";
        // Снятие обработчиков
        closeDynamicsPopup.removeEventListener("click", closeHandler);
        analyzeDynamicsButton.removeEventListener("click", analyzeHandler);
        pasteDynamicsButton.removeEventListener("click", pasteHandler);
        dynamicFileUploadButton.removeEventListener("click", uploadBtnHandler);
        dynamicFileUploadInput.removeEventListener("change", fileSelectHandler);
        prepareTextDynamicsButton.removeEventListener("click", prepareTextHandler);
        if (detachDropZone) detachDropZone();
    };

    // Обработчик для кнопки анализа динамики
    const analyzeHandler = async () => {
        const rawText = dynamicsTextarea.value.trim();
        if (!window.previousDynamicsText) {
            window.previousDynamicsText = rawText
        } // Сохраняем текст для последующего использования в overlay

        if (!rawText) {
            alert("Пожалуйста, введите текст для анализа.");
            return;
        }
        // Блокируем кнопку анализа
        analyzeDynamicsButton.disabled = true;
        closeDynamicsPopup.innerText = "Отмена";

        const startResponse = await sendRequest({
            url: "/working_with_reports/analyze_dynamics",
            data: {
                origin_text: rawText,
                report_id: reportData.id
            }
        });
        const {status, message, task_id} = startResponse || {};
        if (status !== "success" || !task_id) {
            console.error("Ошибка при отправке текста на анализ динамики:", message);
            analyzeDynamicsButton.disabled = false;
            closeDynamicsPopup.innerText = "Закрыть";
            return;
        }
        
        pollTaskStatus(task_id, {
            maxAttempts: 20,
            interval: 7000,
            onProgress: (progress) => updateDynamicsProgressBar(progress, "Ожидание результата..."),
            onSuccess: (result) => {
                updateDynamicsProgressBar(100, "Готово!");
                finalizeAnalyzeDynamics(result);
            },
            onError: (errMsg) => updateDynamicsProgressBar(100, errMsg),
            onTimeout: () => updateDynamicsProgressBar(100, "Превышено время ожидания ответа. Попробуйте ещё раз позже.")
        });

    };

    const prepareTextHandler = async () => {
        const rawText = dynamicsTextarea.value.trim();
        if (!rawText) {
            alert("Пожалуйста, введите текст для подготовки.");
            return;
        }
        window.previousDynamicsText = rawText; // Сохраняем текст для последующего использования в overlay
        const taskID = await prepareTextWithAI(dynamicsTextarea, prepareTextDynamicsButton);

        pollTaskStatus(taskID, {
            maxAttempts: 12,
            interval: 4000,
            onProgress: (progress) => updateDynamicsProgressBar(progress, "Ожидание результата..."),
            onSuccess: (result) => {
                updateDynamicsProgressBar(100, "Готово!");
                dynamicsTextarea.value = result || "";
            },
            onError: (errMsg) => updateDynamicsProgressBar(100, errMsg),
            onTimeout: () => updateDynamicsProgressBar(100, "Превышено время ожидания ответа. Попробуйте ещё раз позже.")
        });
    };

    // Обработчик для вставки из буфера обмена
    const pasteHandler = async () => {
        await handlePasteFromClipboard(dynamicsTextarea, dynamicsPreview);
    };

    // Обработчик выбора файла
    const fileSelectHandler = (e) => {
        const file = e.target.files && e.target.files[0];
        if (file) {
            handleFileUpload(file, dynamicsPreview, dynamicsTextarea);
        }
        // Сброс значения чтобы можно было выбрать тот же файл снова при необходимости
        dynamicFileUploadInput.value = "";
    };

    // Промежуточный обработчик симулирующий клик на input для 
    // загрузки файла при клике на кнопку загрузить файл
    const uploadBtnHandler = () => {
        dynamicFileUploadInput.click();
    };


    // Назначаем обработчики
    closeDynamicsPopup.addEventListener("click", closeHandler);
    analyzeDynamicsButton.addEventListener("click", analyzeHandler);
    pasteDynamicsButton.addEventListener("click", pasteHandler);
    dynamicFileUploadButton.addEventListener("click", uploadBtnHandler);
    dynamicFileUploadInput.addEventListener("change", fileSelectHandler);
    prepareTextDynamicsButton.addEventListener("click", prepareTextHandler);

}

    
// Функция для финального этапа анализа динамики
async function finalizeAnalyzeDynamics(resultObj) {
    // resultObj должен содержать: result, report_id, skeleton
    if (!resultObj || !resultObj.result || !resultObj.report_id || !resultObj.skeleton) {
        alert("Ошибка: не хватает данных для финального этапа анализа динамики.");
        return;
    }

    try {
        const response = await sendRequest({
            url: "/working_with_reports/analyze_dynamics_finalize",
            data: {
                result: resultObj.result,
                report_id: resultObj.report_id,
                skeleton: resultObj.skeleton,
            }
        });

        if (response && response.status === "success") {
            handleAnalyzeDynamicsResponse(response);
        } else {
            console.error("Ошибка при финальном этапе анализа динамики:", response.message || "Неизвестная ошибка");
        }
    } catch (e) {
        console.error(e);
    }
}


// Функция для повторного выполнения встроенных скриптов в контейнере
// использую после ререндеринга body без перезагрузки страницы
function reexecuteInlineScripts(container = document.body) {
    const scripts = container.querySelectorAll("script:not(.no-reexec)");

    scripts.forEach(oldScript => {
        const newScript = document.createElement("script");
        [...oldScript.attributes].forEach(attr => newScript.setAttribute(attr.name, attr.value));
        if (oldScript.src) {
            newScript.src = oldScript.src;
        } else {
            newScript.textContent = oldScript.textContent;
        }
        oldScript.replaceWith(newScript);
    });
}


// Функция для обработки ответа после трансформации предыдущего протокола. 
// Перерисовывает body
function handleAnalyzeDynamicsResponse(response) {
    document.body.innerHTML = response.html;
    window.keyWordsGroups = response.key_words_groups;
    window.reportData = response.report_data;
    window.currentReportParagraphsData = response.paragraphs_data;
    refreshCsrfToken();
    initWorkingWithReport();
    reexecuteInlineScripts(); // Перезапускаем скрипты в новом body
    additionalFindings(response); // Отображаем нераспознанные предложения
    attachPrevReportOverlayLogic(); // навешиваем поведение Overlay
    // показываем кнопку showPrevReportButton
    const showPrevReportButton = document.getElementById("showPrevReportButton");
    if (showPrevReportButton) {
        showPrevReportButton.style.display = "block";
    }
    // Скрываем кнопки dynamicReportButton и editReportButton
    const dynamicReportButton = document.getElementById("dynamicReportButton");
    const editReportButton = document.getElementById("editReportButton");
    if (dynamicReportButton) {
        dynamicReportButton.style.display = "none";
    }
    if (editReportButton) {
        editReportButton.style.display = "none";
    }

    if(!userSettings.USE_SENTENCE_AUTOSAVE_FOR_DYNAMIC_REPORT) {
        // Меняем значение USE_SENTENCE_AUTOSAVE на false
        userSettings.USE_SENTENCE_AUTOSAVE = false;
    }
}


// Функция для обработки дополнительных находок после анализа динамики
// Отображает нераспознанные предложения в блоке aiDynamicBlock
function additionalFindings(response) {
    const aiBlock = document.getElementById("aiDynamicBlock");
    const aiRedactorResponseBlock = document.getElementById("aiRedactorResponseBlock");
    const aiImpressionResponseBlock = document.getElementById("aiImpressionResponseBlock"); 

    if (aiRedactorResponseBlock) {
        aiRedactorResponseBlock.innerHTML = ""; 
        aiRedactorResponseBlock.style.display = "none"; // Скрываем блок
    }
    if (aiImpressionResponseBlock) {
        aiImpressionResponseBlock.innerHTML = "";
        aiImpressionResponseBlock.style.display = "none"; // Скрываем блок
    }

    if (aiBlock) {
        aiBlock.style.display = "block"; // Показываем блок, если он существует
        aiBlock.innerHTML = ""; // Очистка перед новым рендером
    }

    const miscSentences = response.misc_sentences;

    if (Array.isArray(miscSentences) && miscSentences.length > 0) {

        const header = document.createElement("h5");
        header.className = "ai-response-header";
        header.textContent = "📌 Не классифицированные предложения (оригинальный протокол можно посмотреть удерживая клавиши shift+пробел):";

        const ul = document.createElement("ul");
        ul.className = "ai-response-list";
        miscSentences.forEach(item => {
            const li = document.createElement("li");
            li.textContent = item.sentence || String(item);
            li.addEventListener("click", handleListMiscellaneousItemClick);
            ul.appendChild(li);
        });

        aiBlock.appendChild(header);
        aiBlock.appendChild(ul);
    } else {
        const empty = document.createElement("div");
        empty.textContent = "✅ Все фрагменты классифицированы. Нераспознанных предложений нет.";
        aiBlock.appendChild(empty);
    }
}


// Функция для навешивания логики на Shift+Пробел (Space) 
// название оставил старое для ctrl так как не меняе сути
function attachPrevReportOverlayLogic() {
    const overlay = document.getElementById("prevReportOverlay");
    const textBlock = overlay.querySelector("#prevReportText");

    // Вешаем обработчик на кнопку "Показать предыдущий отчет"
    const showPrevReportButton = document.getElementById("showPrevReportButton");
    if (showPrevReportButton) {
        showPrevReportButton.addEventListener("click", () => {
            overlay.classList.toggle("show");
        });
    }

    if (!overlay) return;
    textBlock.textContent = window.previousDynamicsText || "(нет сохранённого текста)";

    // close button logic
    const closeButton = overlay.querySelector("#closePrevReportButton");
    if (closeButton) {
        closeButton.addEventListener("click", () => {
            overlay.classList.remove("show");
        });
    }
    document.addEventListener("keydown", function (e) {
        if (e.shiftKey && e.code === "Space") {
            e.preventDefault(); // Предотвращаем скроллинг
            overlay.classList.toggle("show");
        }

        if (e.code === "Escape" && overlay.classList.contains("show")) {
            overlay.classList.remove("show");
        }
    });
}


// Функция для копирования текста в буфер обмена использую для 
// неклассфицированных предложений в логике трансформации протоколов в динамике
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        console.log("Текст скопирован в буфер обмена:", text);
    }).catch((err) => {
        console.error("Ошибка при копировании текста:", err);
    });
}


// Функция для обработки клика по элементу списка использую для 
// неклассфицированных предложений в логике трансформации протоколов в динамике
function handleListMiscellaneousItemClick(event) {
    const listItem = event.target;
    const sentenceText = listItem.textContent.trim();
    
    if (!sentenceText) return;

    // Копируем текст в буфер
    copyToClipboard(sentenceText);

    // Убираем элемент из списка
    listItem.remove();
}


