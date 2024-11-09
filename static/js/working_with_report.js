// working_with_report.js



/**
 * Extracts the maximum number from the protocol number and increments it by 1.
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
 * Creates an editable sentence element wrapped in a span.
 * 
 * @param {string} sentenceText - The text of the sentence.
 * @returns {HTMLElement} - A new span element containing the editable sentence.
 */
function createEditableSentenceElement(sentenceText) {
    const newSentenceElement = document.createElement("span");
    newSentenceElement.classList.add("report__sentence");
    newSentenceElement.dataset.index = "right-side-{{ paragraphId }}-{{ index }}"
    newSentenceElement.textContent = sentenceText;

    // Make the content editable
    newSentenceElement.contentEditable = "true";

    return newSentenceElement;
}


/**
 * Toggles the visibility of the sentence list associated with a button.
 * 
 * @param {HTMLElement} button - The button that toggles the sentence list.
 */
// function toggleSentenceList(button) {
//     const sentenceList = button.closest(".report__paragraph").querySelector(".sentence-list");
//     if (sentenceList.style.display === "none" || sentenceList.style.display === "") {
//         sentenceList.style.display = "block";
//         button.classList.add("expanded");
//         button.classList.remove("collapsed");
//         button.title = "Collapse";
//     } else {
//         sentenceList.style.display = "none";
//         button.classList.remove("expanded");
//         button.classList.add("collapsed");
//         button.title = "Expand";
//     }
// }


/**
 * Checks if an element is visible on the screen.
 * 
 * @param {HTMLElement} element - The element to check.
 * @returns {boolean} - True if the element is visible, false otherwise.
 */
function isElementVisible(element) {
    const style = window.getComputedStyle(element);
    return style.display !== "none" && style.visibility !== "hidden";
}


/**
 * Cleans text from <select> elements and buttons, leaving only the selected text.
 * 
 * @param {HTMLElement} element - The element containing the text to clean.
 * @returns {string} - The cleaned text.
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
 * Displays processed paragraphs and sentences that are suggested for the user to add to the database.
 * 
 * @param {Array} paragraphs - Array of paragraph objects to display.
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
            data: dataToSend
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


// /**
//  * Функция для переключения видимости списка предложений
//  * @param {HTMLElement} button - Кнопка, которая была нажата
//  */
// function toggleSentenceList(button) {
//     const sentenceList = button.closest(".report__paragraph").querySelector(".sentence-list");
//     if (sentenceList.style.display === "none" || sentenceList.style.display === "") {
//         sentenceList.style.display = "block";
//         button.classList.add("expanded");
//         button.classList.remove("collapsed");
//         button.title = "Collapse";
//     } else {
//         sentenceList.style.display = "none";
//         button.classList.remove("expanded");
//         button.classList.add("collapsed");
//         button.title = "Expand";
//     }
// }


/**
 * Функция для выделения ключевых слов в тексте
 * @param {string} text - Текст для обработки
 * @param {Array} keyWordsGroups - Массив групп ключевых слов
 * @returns {string} - Обновленный текст с выделенными ключевыми словами
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
 * Функция для обновления текста абзацев с классом core-paragraph-list и выделения ключевых слов.
 */
function updateCoreParagraphText() {
    const coreParagraphLists = document.querySelectorAll(".core-paragraph-list");

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
 * @returns {Array} Массив с данными абзацев и предложений.
 */
function collectParagraphsData() {
    const coreParagraphLists = document.querySelectorAll(".core-paragraph-list"); // Ищем списки с классом core-paragraph-list
    const paragraphsData = [];

    coreParagraphLists.forEach(paragraphList => {
        // Находим элемент абзаца внутри текущего списка (core-paragraph-list)
        const paragraphElement = paragraphList.querySelector(".report__paragraph > p");
        

        // Проверяем, что элемент абзаца существует
        if (!paragraphElement) {
            console.error("Paragraph element not found in core-paragraph-list.");
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
 * @param {string} paragraphClass - Класс, по которому будут собираться данные.
 * @returns {string} - Собранный и очищенный текст.
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




// /**
//  * Отображает кружок "+" рядом с предложением.
//  * 
//  * @param {number} x - Координата X курсора.
//  * @param {number} y - Координата Y курсора.
//  * @param {HTMLElement} target - Элемент, для которого отображаем кружок.
//  */
// function showPlusCircle(x, y, target) {
//     activeSentence = target;
//     plusCircle.style.left = `${x + 7}px`; // Чуть правее курсора
//     plusCircle.style.top = `${y + 7}px`; // Чуть ниже курсора
//     plusCircle.style.display = 'flex';
// }

/**
 * Скрывает кружок "+" с небольшой задержкой.
 */
// function hidePlusCircle() {
//     hideTimeout = setTimeout(() => {
//         plusCircle.style.display = 'none';
//     }, 800); 
// }





/**
 * Отображает всплывающее окно с предложениями для замены.
 * 
 * @param {number} x - Координата X для отображения окна.
 * @param {number} y - Координата Y для отображения окна.
 * @param {Array} sentenceList - Список предложений для выбора.
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
 * Связывает предложения на странице с данными из reportData и связывает их с подходящими предложениями.
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

            // Если есть связанные предложения, озеленяем текущее предложение
            if (sentenceElement.linkedSentences.length > 0) {
                highlightSentence(sentenceElement);
            }
        }
    });
}

/**
 * Изменяет стиль предложения. Нужно для выделения предложений у которых есть альтернатива.
 * 
 * @param {HTMLElement} sentenceElement - Элемент предложения для изменения цвета.
 */
function highlightSentence(sentenceElement) {
    sentenceElement.classList.add("highlighted-sentence");
}






// Объявляем глобальные переменные и запускаем стартовые функции, постепенно нужно перенести сюда и логику связанную с ключевыми словами и развешивание части слушателей
document.addEventListener("DOMContentLoaded", function() {
    // let hoverTimeout; // Объявляем переменную для хранения таймера
    // let hideTimeout;  // Объявляем переменную для хранения таймера скрытия кружка
    let activeSentence = null;  // Для отслеживания активного предложения
    const popupList = document.getElementById("popupList"); // // Для обращения к PopUp

    linkSentences(); // Связываем предложения с данными
    // setupHoverAndClickLogic(); // Настраиваем логику отображения кружка и всплывающего окна
    sentenceDoubleClickHandle () // Включаем логику двойного клика на предложение
});







// Обработчик двойного клика на предложение
function sentenceDoubleClickHandle (){
    const sentencesOnPage = document.querySelectorAll(".report__sentence");
    console.log("logic started")
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
 * Настраивает логику наведения мыши и клика по предложениям для отображения кружка и списка предложений.
 */
// function setupHoverAndClickLogic() {
//     const sentencesOnPage = document.querySelectorAll(".report__sentence");
    
//     sentencesOnPage.forEach(sentenceElement => {
//         // Наведение на предложение
//         sentenceElement.addEventListener("mouseenter", function(event) {
//             if (!sentenceElement.classList.contains("editing") && sentenceElement.linkedSentences.length > 0) { // Проверяем, что предложение не в режиме редактирования
//                 hoverTimeout = setTimeout(() => {
//                     showPlusCircle(event.pageX, event.pageY, sentenceElement);
//                 }, 700);
//             }
//         });

//         sentenceElement.addEventListener("mouseleave", function() {
//             clearTimeout(hoverTimeout); // Отменяем показ кружка, если мышь ушла
//             hidePlusCircle(); // Скроем кружок с небольшой задержкой
//         });

//         // Добавляем обработку фокуса (когда предложение редактируется)
//         sentenceElement.addEventListener("focus", function() {
//             sentenceElement.classList.add("editing"); // Добавляем класс для режима редактирования
//             hidePlusCircle(); // Скрываем кружок, если предложение редактируется
//         });

//         // Добавляем обработку потери фокуса (когда предложение больше не редактируется)
//         sentenceElement.addEventListener("blur", function() {
//             sentenceElement.classList.remove("editing"); // Убираем класс режима редактирования
//         });

//     });

//     // Клик по кружку "+"
//     plusCircle.addEventListener("click", function(event) {
//         if (activeSentence && activeSentence.linkedSentences) {
//             showPopup(event.pageX, event.pageY, activeSentence.linkedSentences);
//         } else {
//             console.error('No linked sentences or linked sentences is not an array');
//         }
//     });

//     // Добавляем обработку событий для наведения на кружок
//     plusCircle.addEventListener("mouseenter", function() {
//         clearTimeout(hideTimeout); // Останавливаем таймер скрытия, если мышь над кружком
//     });

//     plusCircle.addEventListener("mouseleave", function() {
//         hidePlusCircle(); // Скрываем кружок, если мышь ушла
//     });

//     // Скрываем всплывающее окно при клике вне его
//     document.addEventListener("click", function(event) {
//         if (!popup.contains(event.target) && !plusCircle.contains(event.target)) {
//             hidePopup();
//         }
//     });
// }




// Логика для кнопки "Next"
document.addEventListener("DOMContentLoaded", function() {
    const nextReportButton = document.querySelector(".icon-btn--next-report");

    nextReportButton.addEventListener("click", function() {
        // Получаем текущий номер протокола и вычисляем новый номер
        let reportNumber = document.getElementById("report-number").value.trim();
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
});


// Логика для кнопки "Add Report"
document.addEventListener("DOMContentLoaded", function() {
    const addReportButton = document.querySelector(".icon-btn--add-report");

    addReportButton.addEventListener("click", function() {
        // Получаем значение из поля "surname" и разбиваем его на части
        let surnameInput = document.getElementById("patient-name").value.trim();
        let [surname = "", name = "", patronymic = ""] = surnameInput.split(" ");

        const birthdate = document.getElementById("patient-birthdate").value;
        let reportNumber = document.getElementById("report-number").value.trim();

        // Преобразуем номер протокола к максимальному числу и прибавляем 1
        const maxReportNumber = getMaxReportNumber(reportNumber);
        const newReportNumber = (maxReportNumber).toString();

        // Формируем строку для передачи параметров через URL
        const url = `choosing_report?patient_surname=${encodeURIComponent(surname)}&patient_name=${encodeURIComponent(name)}&patient_patronymicname=${encodeURIComponent(patronymic)}&patient_birthdate=${encodeURIComponent(birthdate)}&report_number=${encodeURIComponent(newReportNumber)}`;

        // Переходим на страницу choose_report
        window.location.href = url;
    });
});


// Логика для обновления текста и выделения ключевых слов. С нее начинается вся 
// логика ключевых слов, по сути здесь просто запускается эта логика 
// при старте страницы
document.addEventListener("DOMContentLoaded", function() {
    updateCoreParagraphText(); // Запускает выделение ключевых слов при загрузке страницы
});



// Логика для кнопки "Edit Form" (редактирование имени, даты рождения и номера отчета)
document.addEventListener("DOMContentLoaded", function() {
    const editButton = document.querySelector(".icon-btn--edit-form");
    const formInputs = document.querySelectorAll("#exportForm input");

    editButton.addEventListener("click", function() {
        // Проверяем, являются ли поля формы только для чтения
        const isReadOnly = formInputs[0].hasAttribute("readonly");

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
});



// Логика редактирования предложений и параграфов
document.addEventListener("DOMContentLoaded", function() {
    /**
     * Логика для кнопки "Edit" в предложениях.
     */
    document.querySelectorAll(".icon-btn--edit").forEach(button => {
        button.addEventListener("click", function() {
            const container = this.closest(".edit-container");
            const sentenceElement = container.querySelector(".report__sentence");
            const selectElement = container.querySelector(".report__select");

            if (this.classList.contains("editing")) {
                // Save logic
                const sentenceId = sentenceElement ? sentenceElement.getAttribute("data-sentence-id") : selectElement.value;
                const newValue = sentenceElement ? sentenceElement.innerText : container.querySelector(".report__input").value;

                // Отправляем запрос на сервер с использованием sendRequest
                sendRequest({
                    url: "/working_with_reports/update_sentence",
                    method: "POST",
                    data: {
                        sentence_id: sentenceId,
                        new_value: newValue
                    }
                }).then(() => {
                    this.classList.remove("editing");
                    this.style.background = "url('/static/pic/edit_button.svg') no-repeat center center";
                    if (selectElement) {
                        const input = container.querySelector(".report__input");
                        const selectedOption = selectElement.selectedOptions[0];
                        selectedOption.setAttribute("data-sentence", input.value);
                        selectedOption.textContent = input.value;
                        input.remove();
                        selectElement.style.display = "inline-block";
                    } else {
                        sentenceElement.contentEditable = false;
                        sentenceElement.classList.remove("editing");
                    }
                }).catch(error => {
                    alert("Failed to update sentence.");
                    console.error("Error updating sentence:", error);
                });
            } else {
                // Edit logic
                this.classList.add("editing");
                this.style.background = "url('/static/pic/save_button.svg') no-repeat center center";

                if (selectElement) {
                    const selectedOption = selectElement.selectedOptions[0];
                    const sentenceText = selectedOption.getAttribute("data-sentence");
                    const input = document.createElement("input");
                    input.type = "text";
                    input.value = sentenceText;
                    input.className = "report__input";
                    container.insertBefore(input, selectElement);
                    selectElement.style.display = "none";
                } else {
                    sentenceElement.contentEditable = true;
                    sentenceElement.classList.add("editing");
                }
            }
        });
    });

    /**
     * Логика для кнопки "Edit" в параграфах.
     */
    document.querySelectorAll(".icon-btn--edit-paragraph").forEach(button => {
        button.addEventListener("click", function() {
            const paragraphElement = this.closest("li").querySelector(".paragraphTitle");

            // Проверка на null
            if (!paragraphElement) {
                console.error("Paragraph element not found.");
                return;
            }

            const paragraphId = paragraphElement.getAttribute("data-paragraph-id");

            if (this.classList.contains("editing")) {
                // Save logic for paragraph
                const newParagraphValue = paragraphElement.innerText;

                // Отправляем запрос на сервер с использованием sendRequest
                sendRequest({
                    url: "/working_with_reports/update_paragraph",
                    method: "POST",
                    data: {
                        paragraph_id: paragraphId,
                        new_value: newParagraphValue
                    }
                }).then(() => {
                    this.classList.remove("editing");
                    paragraphElement.contentEditable = false;
                    paragraphElement.classList.remove("editing");
                    this.style.background = "url('/static/pic/edit_button.svg') no-repeat center center";
                }).catch(error => {
                    alert("Failed to update paragraph.");
                    console.error("Error updating paragraph:", error);
                });
            } else {
                // Edit logic for paragraph
                this.classList.add("editing");
                paragraphElement.contentEditable = true;
                paragraphElement.classList.add("editing");
                this.style.background = "url('/static/pic/save_button.svg') no-repeat center center";
            }
        });
    });
});


// // Логика добавления предложения при нажатии на кнопку "+"
// document.addEventListener("DOMContentLoaded", function() {
//     /**
//      * Создает поле ввода для нового предложения.
//      * @param {HTMLElement} buttonElement - Кнопка, перед которой будет вставлено поле ввода.
//      */
//     function createInputForNewSentence(buttonElement) {
//         // Удаляем все активные элементы (селекты или инпуты)
//         document.querySelectorAll(".dynamic-select, .dynamic-input").forEach(el => el.remove());

//         // Создаем инпут для нового предложения и добавляем его перед кнопкой +
//         const inputElement = document.createElement("input");
//         inputElement.type = "text";
//         inputElement.classList.add("dynamic-input");
//         inputElement.placeholder = "Введите предложение";
//         buttonElement.parentNode.insertBefore(inputElement, buttonElement);

//         inputElement.focus();

//         // Обработка нажатия Enter для добавления предложения
//         inputElement.addEventListener("keydown", function(event) {
//             if (event.key === "Enter") {
//                 const customSentence = inputElement.value.trim();
//                 if (customSentence) {
//                     const newSentenceElement = createEditableSentenceElement(customSentence);
//                     buttonElement.parentNode.insertBefore(newSentenceElement, buttonElement);
//                     inputElement.remove();
                    
//                     updateCoreParagraphText();
//                 }else {
//                     inputElement.remove(); 
//                 }
//             }
            
//         });
        
//     }

//     /**
//      * Логика при нажатии на кнопку "+". Создает выпадающий список или поле ввода для добавления предложения.
//      */
//     document.querySelectorAll(".icon-btn--add-sentence").forEach(button => {
//         button.addEventListener("click", function() {
//             const paragraphId = this.getAttribute("data-paragraph-id");
//             const buttonElement = this;

//             // Удаляем предыдущие выпадающие списки или поля ввода, если они уже существуют
//             document.querySelectorAll(".dynamic-select, .dynamic-input").forEach(el => el.remove());

//             // Получаем предложения с индексом 0 для этого параграфа
//             sendRequest({
//                 url: "/working_with_reports/get_sentences_with_index_zero",
//                 method: "POST",
//                 data: {
//                     paragraph_id: paragraphId
//                 }
//             }).then(data => {
//                 if (data.sentences && data.sentences.length > 0) {
//                     // Создаем выпадающий список (select) с предложениями
//                     const selectElement = document.createElement("select");
//                     selectElement.classList.add("dynamic-select");

//                     // Добавляем первое пустое поле, значение пустое, а текст — "Введите предложение"
//                     const startOption = document.createElement("option");
//                     startOption.value = "";
//                     startOption.textContent = "Выберите предложение для добавления";
//                     selectElement.appendChild(startOption);

//                     // Добавляем поле для ввода своего предложения
//                     const emptyOption = document.createElement("option");
//                     emptyOption.value = "";
//                     emptyOption.textContent = "Введите свое предложение";
//                     selectElement.appendChild(emptyOption);

//                     // Добавляем остальные предложения с индексом 0
//                     data.sentences.forEach(sentence => {
//                         const option = document.createElement("option");
//                         option.value = sentence.id;
//                         option.textContent = sentence.sentence;
//                         selectElement.appendChild(option);
//                     });
//                     selectElement.value = "";

//                     // Добавляем выпадающий список перед кнопкой
//                     buttonElement.parentNode.insertBefore(selectElement, buttonElement);

//                     // Обработка выбора предложения
//                     selectElement.addEventListener("change", function() {
//                         if (selectElement.value === "") {
//                             // Если выбрано пустое поле, вызываем функцию для инпута
//                             createInputForNewSentence(buttonElement);
//                             selectElement.remove();  // Удаляем выпадающий список
//                         } else {
//                             // Если выбрано предложение из списка, добавляем его в текст
//                             const selectedSentence = selectElement.options[selectElement.selectedIndex].textContent;
//                             const newSentenceElement = createEditableSentenceElement(selectedSentence);
//                             buttonElement.parentNode.insertBefore(newSentenceElement, buttonElement);
//                             selectElement.remove();
//                             updateCoreParagraphText();
//                         }
//                     });

//                 } else {
//                     // Если предложений нет, вызываем функцию для инпута
//                     createInputForNewSentence(buttonElement);
//                 }
//             }).catch(error => {
//                 console.error("Error:", error);
//             });
//         });
//     });
// });



/**
 * Логика для кнопки "+". Открывает popup с отфильтрованными предложениями.
 */
document.querySelectorAll(".icon-btn--add-sentence").forEach(button => {
    button.addEventListener("click", function(event) {
        const paragraphId = this.getAttribute("data-paragraph-id");

        // Создаем пустое предложение и добавляем перед кнопкой
        const newSentenceElement = createEditableSentenceElement("");
        button.parentNode.insertBefore(newSentenceElement, button);
        newSentenceElement.focus(); // Устанавливаем фокус на новый элемент

        // Получаем предложения с индексом 0 для этого параграфа
        sendRequest({
            url: "/working_with_reports/get_sentences_with_index_zero",
            method: "POST",
            data: { paragraph_id: paragraphId }
        }).then(data => {
            if (data.sentences && data.sentences.length > 0) {
                // Используем общий popup для показа предложений
                showPopup(event.pageX, event.pageY, data.sentences, function(selectedSentence) {
                    // Логика при выборе предложения из popup
                    const newSentenceElement = createEditableSentenceElement(selectedSentence.sentence);
                    button.parentNode.insertBefore(newSentenceElement, button);
                    updateCoreParagraphText(); // Обновляем текст абзаца после добавления предложения
                });
            } else {
                console.error("No sentences available for this paragraph.");
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




// "Copy to clipboard" button logic
document.getElementById("copyButton").addEventListener("click", async function() {

    // Собираем текст из параграфов: initial, core, impression
    const initialText = collectTextFromParagraphs("initial-paragraph-list");
    const coreText = collectTextFromParagraphs("core-paragraph-list");
    const impressionText = collectTextFromParagraphs("impression-paragraph-list");

    // Соединяем все части с пустой строкой между ними
    const textToCopy = `${initialText}\n\n${coreText}\n\n${impressionText}`.trim();

    try {
        await navigator.clipboard.writeText(textToCopy.trim());
        toastr.success("Text copied to clipboard successfully", "Success");

        // После успешного копирования выполняем отправку данных
        const paragraphsData = collectParagraphsData();
        console.log("This is paragraphsData from clipboard logic:    " + paragraphsData)
       
        console.log("This is paragraphsData from server in clipboard logic:    " + paragraphsData)

        const response = await sendRequest({
            url: "/working_with_reports/new_sentence_adding",
            method: "POST",
            data: {
                paragraphs: paragraphsData
            }
        });
        console.log("This is response from server in clipboard logic:    " + response.processed_paragraphs)
        // Если запрос успешен, отображаем обработанные абзацы
        displayProcessedParagraphs(response.processed_paragraphs);

        
    } catch (error) {
        console.error("Error processing paragraphs:", error);
        alert(error.message || "Failed to process paragraphs.");
    }
});

// "Export to Word" button logic
document.getElementById("exportButton").addEventListener("click", async function() {

    // Собираем текст из initial, core и impression
    const initialText = collectTextFromParagraphs("initial-paragraph-list");
    const coreText = collectTextFromParagraphs("core-paragraph-list");
    const impressionText = collectTextFromParagraphs("impression-paragraph-list");
    
    // Текст для экспорта в Word: initial идет в scanParam, core + impression идут в text
    const textToExport = `${coreText}\n\n${impressionText}`.trim();
    const scanParam = initialText.trim();  // Вставляем initial в scanParam
    
    
    // Формируем данные параграфов и предложений
    const paragraphsData = collectParagraphsData();

    try {
        // Отправляем данные абзацев на сервер, используя sendRequest
        const response = await sendRequest({
            url: "/working_with_reports/new_sentence_adding",
            method: "POST",
            data: {
                paragraphs: paragraphsData
            }
        });

        // Отображаем обработанные параграфы, если запрос успешен
        displayProcessedParagraphs(response.processed_paragraphs);

    } catch (error) {
        console.error("Error processing paragraphs:", error);
        alert(error.message || "Failed to process paragraphs.");
        return; // Прекращаем выполнение, если отправка абзацев не удалась
    }

    // Если отправка абзацев успешна, выполняем экспорт в Word
    try {
        const name = document.getElementById("patient-name").value;
        const birthdate = document.getElementById("patient-birthdate").value;
        const reportnumber = document.getElementById("report-number").value;
        // Извлекаем значения из data-атрибутов
        const exportForm = document.getElementById("exportForm");
        const subtype = exportForm.getAttribute("data-subtype");
        const reportType = exportForm.getAttribute("data-report-type");

        const reportSideElement = document.getElementById("report-side");
        const reportSide = reportSideElement ? reportSideElement.value : "";

        // Отправляем запрос на экспорт в Word, используя sendRequest и получаем Blob
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
            responseType: "blob"
        });

        // Обрабатываем Blob для загрузки файла
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        const currentDate = new Date();
        const day = currentDate.getDate();
        const month = currentDate.getMonth() + 1;
        const year = currentDate.getFullYear();
        const formattedDate = `${day.toString().padStart(2, '0')}${month.toString().padStart(2, '0')}${year}`;

        let fileReportSide;
        if (reportSide === "right") {
            fileReportSide = " правая сторона";
        } else if (reportSide === "left") {
            fileReportSide = " левая сторона";
        } else {
            fileReportSide = "";
        }

        a.style.display = "none";
        a.href = url;
        a.download = `${name} ${reportType} ${subtype}${fileReportSide} ${formattedDate}.docx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);

    } catch (error) {
        console.error("Error exporting to Word:", error);
        alert(error.message || "Failed to export to Word.");
    }
});


// "Generate expression" button logic
document.getElementById("generateImpression").addEventListener("click", async function(){
    const textToCopy = collectTextFromParagraphs("core-paragraph-list");
    const assistantNames = [
        "airadiologist"
    ];
    const boxForAiResponse = document.getElementById("aiResponse");
    boxForAiResponse.textContent = "waiting for ai response...";

    try {
        const aiResponse = await generateImpressionRequest(textToCopy, assistantNames);
        boxForAiResponse.textContent = aiResponse || "No response received.";
    } catch(error) {
        console.log(error);
        boxForAiResponse.textContent = "An error occurred. Please try again.";
    }

});


// "Add Impression to Report" button logic
document.getElementById("addImpressionToReportButton").addEventListener("click", function() {
    // Получаем текст ответа ИИ
    const aiResponseText = document.getElementById("aiResponse").innerText.trim();

    if (!aiResponseText) {
        alert("AI response is empty. Please generate an impression first.");
        return;
    }

    // Ищем первый видимый элемент предложения в impression-paragraph-list
    const impressionParagraphs = document.querySelectorAll(".impression-paragraph-list .report__sentence");
    let foundVisibleSentence = false;

    impressionParagraphs.forEach(sentenceElement => {
        if (isElementVisible(sentenceElement) && !foundVisibleSentence) {
            // Заменяем текст первого видимого предложения на ответ ИИ
            sentenceElement.textContent = aiResponseText;
            foundVisibleSentence = true;  // Останавливаем поиск после первого найденного
        }
    });

    if (!foundVisibleSentence) {
        alert("No visible impression sentence found.");
    }
});