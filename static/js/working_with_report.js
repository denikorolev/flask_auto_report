// working_with_report.js
// v0.1.0

// Функция для создания редактируемого предложения в span
function createEditableSentenceElement(sentenceText) {
    const newSentenceElement = document.createElement("span");
    newSentenceElement.classList.add("report__sentence");
    newSentenceElement.textContent = sentenceText;

    // Делаем содержимое редактируемым
    newSentenceElement.contentEditable = "true";

    return newSentenceElement;
}


// Функция для переключения видимости списка предложений
function toggleSentenceList(button) {
    const sentenceList = button.closest(".report__paragraph").querySelector(".sentence-list");
    if (sentenceList.style.display === "none" || sentenceList.style.display === "") {
        sentenceList.style.display = "block";
        button.classList.add("expanded");
        button.classList.remove("collapsed");
        button.title = "Collapse";
    } else {
        sentenceList.style.display = "none";
        button.classList.remove("expanded");
        button.classList.add("collapsed");
        button.title = "Expand";
    }
}


// Функция для проверки, виден ли элемент на экране
function isElementVisible(element) {
    const style = window.getComputedStyle(element);
    return style.display !== "none" && style.visibility !== "hidden";
}


// Функция для очистки текста от <select> элементов и кнопок, оставляя только выбранный текст
function cleanSelectText(element) {
    let text = element.innerHTML;

    // Удаляем все кнопки из текста
    element.querySelectorAll("button").forEach(button => {
        button.remove();  // Удаляем кнопки из DOM, чтобы они не мешали сбору текста
    });

    // Заменяем все <select> на выбранный текст
    element.querySelectorAll("select").forEach(select => {
        const selectedOption = select.options[select.selectedIndex].textContent;
        text = text.replace(select.outerHTML, selectedOption);
    });

    // Убираем все HTML теги, кроме текста
    text = text.replace(/<[^>]*>?/gm, '').trim();

    // Используем встроенный DOM-парсер для замены мнемоник
    const tempElement = document.createElement("textarea");
    tempElement.innerHTML = text;
    text = tempElement.value;


    // Удаляем лишние пробелы (оставляем только один пробел между словами)
    text = text.replace(/\s\s+/g, ' ');

    return text;
}


// Собираем текст из правой части экрана для дальнейшей его обработки
function collectTextFromRightSide() {
    const rightParagraphList = document.getElementById("right-paragraph-list");
    let collectedText = "";

    // Проходим по каждому параграфу
    rightParagraphList.querySelectorAll(".report__paragraph").forEach(paragraphElement => {
        const paragraph = paragraphElement.querySelector("p");

        // Добавляем текст параграфа, если он виден
        if (isElementVisible(paragraph)) {
            const paragraphText = paragraph.innerText.trim();
            collectedText += paragraphText + " ";  // Добавляем текст параграфа, если он виден
        }

        let hasSentences = false;  // Флаг для проверки наличия предложений

        // Проходим по каждому предложению внутри параграфа
        paragraphElement.querySelectorAll(".report__sentence").forEach(sentenceElement => {
            // Проверяем, видимо ли предложение
            if (isElementVisible(sentenceElement)) {
                const sentenceText = cleanSelectText(sentenceElement);  // Используем функцию для очистки текста
                if (sentenceText) {
                    collectedText += sentenceText + " ";  // Добавляем текст предложения
                    hasSentences = true;  // Устанавливаем флаг, что есть предложения
                }
            }
        });

        // Если есть предложения, добавляем перевод строки
        if (hasSentences) {
            collectedText += "\n";  // Разделяем параграфы, если были предложения
        }
    });

return collectedText.trim();  // Убираем лишние пробелы и возвращаем текст
}


// функция для отображения предложений, которые мы предлагаем пользователю добавить в базу данных
function displayProcessedParagraphs(paragraphs) {
    const container = document.getElementById('sentenceAddingRequestContainer');
    container.innerHTML = ''; // Очищаем контейнер перед добавлением новых данных

    // Проверка, есть ли данные для обработки
    if (!paragraphs || !Array.isArray(paragraphs)) {
        console.error("Invalid paragraphs data:", paragraphs);
        return;
    }

    paragraphs.forEach(paragraph => {
        const paragraphDiv = document.createElement('div');
        paragraphDiv.classList.add('paragraph-container');

        const paragraphText = paragraph.paragraph_text || `Paragraph: ${paragraph.paragraph_id}`;
        paragraphDiv.textContent = `Paragraph: ${paragraphText}`;

        // Проверка на массив предложений
        if (Array.isArray(paragraph.sentences)) {
            paragraph.sentences.forEach(sentence => {
                const sentenceDiv = document.createElement('div');
                sentenceDiv.classList.add('sentence-container');
                sentenceDiv.textContent = sentence;

                // Добавляем кнопку "Добавить" для каждого предложения
                const addButton = document.createElement('button');
                addButton.textContent = 'Добавить';
                addButton.classList.add('add-sentence-btn');
                addButton.addEventListener('click', function() {
                    // Отправляем предложение на сервер
                    addSentenceToDatabase(paragraph.paragraph_id, sentence);
                });

                sentenceDiv.appendChild(addButton); // Добавляем кнопку к предложению
                paragraphDiv.appendChild(sentenceDiv);
            });
        } else if (typeof paragraph.sentence === 'string') {
            // Если предложение передано как строка (единичное предложение)
            const sentenceDiv = document.createElement('div');
            sentenceDiv.classList.add('sentence-container');
            sentenceDiv.textContent = paragraph.sentence;

            // Добавляем кнопку "Добавить" для предложения
            const addButton = document.createElement('button');
            addButton.textContent = 'Добавить';
            addButton.classList.add('add-sentence-btn');
            addButton.addEventListener('click', function() {
                // Отправляем предложение на сервер
                addSentenceToDatabase(paragraph.paragraph_id, paragraph.sentence);
            });

            sentenceDiv.appendChild(addButton);
            paragraphDiv.appendChild(sentenceDiv);
        } else {
            console.error('No valid sentences found for paragraph:', paragraph);
        }

        container.appendChild(paragraphDiv);
    });
}


// Функция для отправки предложения на сервер
function addSentenceToDatabase(paragraphId, sentenceText) {
    fetch("{{ url_for('working_with_reports.add_sentence_to_paragraph') }}", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            paragraph_id: paragraphId,
            sentence_text: sentenceText
        })
    }).then(response => {
        if (response.ok) {
            response.json().then(data => {
                alert("Sentence added successfully!");
            });
        } else {
            alert("Failed to add sentence.");
        }
    });
}

// Функция для отправки данных на сервер в маршрут new_sentence_adding где будет произведен поиск новых предложений в тексте справа
function sendParagraphsToServer(paragraphsData) {
    fetch("{{ url_for('working_with_reports.new_sentence_adding') }}", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            paragraphs: paragraphsData
        })
    }).then(response => {
        if (response.ok) {
            response.json().then(data => {
                displayProcessedParagraphs(data.processed_paragraphs);
            });
        } else {
            alert("Failed to process paragraphs.");
        }
    });
}

// Функция для формирования данных параграфов и предложений для формирования предложений для добавления в базу данных
function collectParagraphsData() {
    const rightParagraphList = document.getElementById("right-paragraph-list");
    const paragraphsData = [];

    rightParagraphList.querySelectorAll(".report__paragraph").forEach(paragraphElement => {
        const paragraph = paragraphElement.querySelector("p");

        // Проверяем, виден ли параграф на экране
            const paragraphId = paragraph.getAttribute("data-paragraph-id");
            const paragraphText = paragraph.innerText.trim();
            const sentences = [];

            paragraphElement.querySelectorAll(".report__sentence").forEach(sentenceElement => {
                const sentenceText = cleanSelectText(sentenceElement);
                if (sentenceText) {
                    sentences.push(sentenceText);
                }
            });

            if (sentences.length > 0) {
                paragraphsData.push({
                    paragraph_id: paragraphId,
                    paragraph_text: paragraphText,
                    sentences: sentences
                });
            }
    });

    return paragraphsData;
}

// Функция очистки и форматирования текста перед использованием его в функциях copy-to-clipboard и export-to-word
function cleanAndFormatText(element) {
    let formattedText = element.innerHTML;

    // Проходим по каждому select и заменяем его на выбранный текст
    element.querySelectorAll("select").forEach(function(select) {
        const selectedOption = select.options[select.selectedIndex].textContent;
        formattedText = formattedText.replace(select.outerHTML, selectedOption);
    });

    // Убираем все теги <span> и оставляем только текст внутри них
    formattedText = formattedText.replace(/<span[^>]*>(.*?)<\/span>/gi, function(match, p1) {
        return p1.trim(); // Возвращаем текст внутри span, удаляя лишние пробелы
    });

    // Удаляем лишние пробелы, табуляции и новые строки
    formattedText = formattedText.replace(/\s+/g, " ").trim();

    // Убираем лишние пробелы и пустые строки между абзацами
    formattedText = formattedText.replace(/\s*\n\s*/g, "\n").trim();

    return formattedText;
}


// Функция для выделения ключевых слов и работы с ними
function highlightKeyWords(text, keyWordsGroups) {
    const matchIndexes = {};

    // Функция для проверки, является ли символ буквой (учитывает кириллицу и латиницу)
    function isLetter(char) {
        return /[a-zA-Zа-яА-ЯёЁ]/.test(char);
    }

    // Проходим по каждой группе ключевых слов
    keyWordsGroups.forEach(group => {
        group.forEach(item => {
            const word = item.word;  // Достаем слово из словаря
            if (!matchIndexes[word]) {
                matchIndexes[word] = 0;
            }

            // Регулярное выражение для нахождения ключевого слова вне тегов и без букв перед и после
            const regex = new RegExp(`(?<!<[^>]*>|[a-zA-Zа-яА-ЯёЁ])(${word})(?![^<]*>|[a-zA-Zа-яА-ЯёЁ])`, 'gi');

            text = text.replace(regex, (matchedWord, offset, fullText) => {
                matchIndexes[word] += 1;

                // Создаём select с опциями из той же группы слов
                const options = group.map(option => {
                    const optionWord = option.word;  // Получаем слово из каждого словаря
                    const isSelected = optionWord.toLowerCase() === matchedWord.toLowerCase() ? "selected" : "";
                    return `<option value="${optionWord}" ${isSelected}>${optionWord}</option>`;
                }).join('');

                return `<select class="report__select_dynamic" data-match-index="${word}-${matchIndexes[word]}">${options}</select>`;
            });
        });
    });

    return text;
}


// Функция для поиска key_words
function updateRightSideText() {
const keyWordsGroups = {{ key_words|tojson }};
const rightParagraphList = document.getElementById("right-paragraph-list");

rightParagraphList.querySelectorAll("p, span").forEach(paragraph => {
    const currentIndex = paragraph.getAttribute("data-index");

    if (!currentIndex) {
        return;
    }

    let plainText = paragraph.innerText || paragraph.textContent;

    if (!paragraph.querySelector('select')) {
        const highlightedText = highlightKeyWords(plainText, keyWordsGroups);
        paragraph.innerHTML = highlightedText;
    }

    paragraph.setAttribute("data-index", currentIndex);
});
}


// Обновление текста справа. Нужно для работы логики key_words. По сути здесь запускается вся эта логика.
document.addEventListener("DOMContentLoaded", function() {
    updateRightSideText(); 
});

// Кнопка переключатель видимости кнопок редактирования
document.querySelector(".icon-btn--show-edit-groups").addEventListener("click", function() {
    const editGroups = document.querySelectorAll(".edit-group");

    // Переключение между видимостью "none" и "inline-block" у элементов с классом .edit-group
    editGroups.forEach(group => {
        if (group.style.display === "none" || group.style.display === "") {
            group.style.display = "inline-block";
        } else {
            group.style.display = "none";
        }
    });
    
    // Изменение текста кнопки в зависимости от состояния
    const button = document.querySelector(".icon-btn--show-edit-groups");
    if (button.textContent === "Show Edit Options") {
        button.textContent = "Hide Edit Options";
    } else {
        button.textContent = "Show Edit Options";
    }
});


// Логика для кнопки "expand"
document.querySelectorAll(".icon-btn--expand").forEach(button => {
    button.addEventListener("click", function() {
        toggleSentenceList(this);
    });
});

// Логика для разворачивания по клику на текст параграфа
document.querySelectorAll(".paragraph_title").forEach(paragraph => {
    paragraph.addEventListener("click", function() {
        const expandButton = this.closest(".report__paragraph").querySelector(".icon-btn--expand");
        toggleSentenceList(expandButton);  // Используем ту же логику, что и для кнопки
    });
});

// Button edit logic for editing name, date of birth etc
document.addEventListener("DOMContentLoaded", function() {
    const editButton = document.querySelector(".icon-btn--edit-form");
    const formInputs = document.querySelectorAll("#exportForm input");

    editButton.addEventListener("click", function() {
        // Check if the inputs are currently read-only
        const isReadOnly = formInputs[0].hasAttribute("readonly");

        formInputs.forEach(input => {
            if (isReadOnly) {
                input.removeAttribute("readonly"); // Make inputs editable
            } else {
                input.setAttribute("readonly", true); // Make inputs read-only
            }
        });

        // Change the button icon accordingly
        if (isReadOnly) {
            editButton.style.background = "url('{{ url_for('static', filename='pic/save_button.svg') }}') no-repeat center center";
            editButton.title = "Save Changes";
        } else {
            editButton.style.background = "url('{{ url_for('static', filename='pic/edit_button.svg') }}') no-repeat center center";
            editButton.title = "Edit Form";
        }
    });
});


// Кнопка "Edit" для предложений
document.querySelectorAll(".icon-btn--edit").forEach(button => {
    button.addEventListener("click", function() {
        const container = this.closest(".edit-container");
        const sentenceElement = container.querySelector(".report__sentence");
        const selectElement = container.querySelector(".report__select");

        if (this.classList.contains("editing")) {
            // Save logic
            const sentenceId = sentenceElement ? sentenceElement.getAttribute("data-sentence-id") : selectElement.value;
            const newValue = sentenceElement ? sentenceElement.innerText : container.querySelector(".report__input").value;

            fetch("{{ url_for('working_with_reports.update_sentence') }}", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    sentence_id: sentenceId,
                    new_value: newValue
                })
            }).then(response => {
                if (response.ok) {
                    this.classList.remove("editing");
                    this.style.background = "url('{{ url_for('static', filename='pic/edit_button.svg') }}') no-repeat center center";
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
                } else {
                    alert("Failed to update sentence.");
                }
            });
        } else {
            // Edit logic
            this.classList.add("editing");
            this.style.background = "url('{{ url_for('static', filename='pic/save_button.svg') }}') no-repeat center center";

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

// Кнопка "Edit" для параграфов
document.querySelectorAll(".icon-btn--edit-paragraph").forEach(button => {
    button.addEventListener("click", function() {
        const paragraphElement = this.closest("li").querySelector(".paragraph_title");
        
        // Проверка на null
    if (!paragraphElement) {
        console.error("Paragraph element not found.");
        return;
    }

        const paragraphId = paragraphElement.getAttribute("data-paragraph-id");

        if (this.classList.contains("editing")) {
            // Save logic for paragraph
            const newParagraphValue = paragraphElement.innerText;

            fetch("{{ url_for('working_with_reports.update_paragraph') }}", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    paragraph_id: paragraphId,
                    new_value: newParagraphValue
                })
            }).then(response => {
                if (response.ok) {
                    this.classList.remove("editing");
                    paragraphElement.contentEditable = false;
                    paragraphElement.classList.remove("editing");
                    this.style.background = "url('{{ url_for('static', filename='pic/edit_button.svg') }}') no-repeat center center";
                } else {
                    alert("Failed to update paragraph.");
                }
            });
        } else {
            // Edit logic for paragraph
            this.classList.add("editing");
            paragraphElement.contentEditable = true;
            paragraphElement.classList.add("editing");
            this.style.background = "url('{{ url_for('static', filename='pic/save_button.svg') }}') no-repeat center center";
        }
    });
});


// Logic for renewing data on the right container then data on the left one was changed
document.getElementById("left-paragraph-list").addEventListener("change", function(event) {
    if (event.target.tagName === "SELECT") {
        const index = event.target.getAttribute("data-index");
        const selectedOption = event.target.selectedOptions[0];
        const selectedSentence = selectedOption.getAttribute("data-sentence");
        const correspondingIndex = index.replace("left-side", "right-side");
        const correspondingParagraph = document.querySelector('[data-index="' + correspondingIndex + '"]');

        // Проверяем, найден ли соответствующий параграф на правой стороне
        if (correspondingParagraph) {
            correspondingParagraph.innerText = selectedSentence;
            // После обновления текста выделяем ключевые слова
            updateRightSideText();
        } else {
            console.error("Corresponding paragraph not found for index: " + correspondingIndex);
        }
    }
});


// Button "Copy to clipboard" logic
document.getElementById("copyButton").addEventListener("click", function() {
    // Собираем текст из правой части экрана
    const textToCopy = collectTextFromRightSide();

    navigator.clipboard.writeText(textToCopy.trim()).then(function() {
        alert("Text copied to clipboard");

        // После успешного копирования выполняем отправку данных
        const paragraphsData = collectParagraphsData();
        sendParagraphsToServer(paragraphsData);

    }).catch(function(err) {
        console.error("Failed to copy text: ", err);
    });
});

// "Export to word" button logic
document.getElementById("exportButton").addEventListener("click", function() {
    // Собираем текст из правой части экрана для экспорта в Word
    const textToExport = collectTextFromRightSide();
    // Формируем данные параграфов и предложений
    const paragraphsData = collectParagraphsData();

    // Отправляем данные параграфов на сервер
    sendParagraphsToServer(paragraphsData);

    const name = document.getElementById("patient-name").value;
    const birthdate = document.getElementById("patient-birthdate").value;
    const reportnumber = document.getElementById("report-number").value;
    const subtype = "{{ subtype }}";
    const reportType = "{{ report_type }}";
    const scanParam = "{{ report.comment }}";
    const reportSideElement = document.getElementById("report-side");
    const reportSide = reportSideElement ? reportSideElement.value : "";

    fetch("{{ url_for('working_with_reports.export_to_word') }}", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            text: textToExport,
            name: name,
            birthdate: birthdate,
            subtype: subtype,
            report_type: reportType,
            reportnumber: reportnumber,
            scanParam: scanParam,
            side: reportSide
        })
    }).then(response => {
        if (response.ok) {
            response.blob().then(blob => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.style.display = "none";
                a.href = url;
                a.download = `${name}_${subtype}.docx`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
            });
        } else {
            alert("Failed to export to Word.");
        }
    });
});

// Логика добавления предложения после нажания на кнопку +
document.addEventListener("DOMContentLoaded", function() {
    // Функция для создания инпута для добавления нового предложения
    function createInputForNewSentence(buttonElement) {
        // Удаляем все активные элементы (селекты или инпуты)
        document.querySelectorAll(".dynamic-select, .dynamic-input").forEach(el => el.remove());

        // Создаем инпут для нового предложения
        const inputElement = document.createElement("input");
        inputElement.type = "text";
        inputElement.classList.add("dynamic-input");
        inputElement.placeholder = "Введите предложение";

        // Добавляем поле ввода перед кнопкой
        buttonElement.parentNode.insertBefore(inputElement, buttonElement);

        // Устанавливаем фокус на поле ввода
        inputElement.focus();

        // Обработка нажатия Enter для добавления предложения
        inputElement.addEventListener("keydown", function(event) {
            if (event.key === "Enter") {
                const customSentence = inputElement.value.trim();
                if (customSentence) {
                    const newSentenceElement = createEditableSentenceElement(customSentence);

                    buttonElement.parentNode.insertBefore(newSentenceElement, buttonElement);
                    inputElement.remove();  
                }
            }
        });
    }

    // Основная логика при нажатии на кнопку "+"
    document.querySelectorAll(".icon-btn--add-sentence").forEach(button => {
        button.addEventListener("click", function() {
            const paragraphId = this.getAttribute("data-paragraph-id");
            const buttonElement = this;

            // Удаляем предыдущие выпадающие списки или поля ввода, если они уже существуют
            document.querySelectorAll(".dynamic-select, .dynamic-input").forEach(el => el.remove());
            
            // Получаем предложения с индексом 0 для этого параграфа
            fetch("{{ url_for('working_with_reports.get_sentences_with_index_zero') }}", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    paragraph_id: paragraphId  // Передаем ID параграфа
                })
            }).then(response => response.json())
            .then(data => {
                if (data.sentences && data.sentences.length > 0) {
                    // Создаем выпадающий список (select) с предложениями
                    const selectElement = document.createElement("select");
                    selectElement.classList.add("dynamic-select");

                    // Добавляем первое пустое поле, значение пустое, а текст — "Введите предложение"
                    const startOption = document.createElement("option");
                    startOption.value = "";  // Пустое значение для выбора
                    startOption.textContent = "Выберете предложение для добавления";  // Текст, который видит пользователь
                    selectElement.appendChild(startOption);

                    // Добавляем первое пустое поле, значение пустое, а текст — "Введите предложение"
                    const emptyOption = document.createElement("option");
                    emptyOption.value = "";  // Пустое значение для выбора
                    emptyOption.textContent = "Введите свое предложение";  // Текст, который видит пользователь
                    selectElement.appendChild(emptyOption);

                    // Добавляем остальные предложения с индексом 0
                    data.sentences.forEach(sentence => {
                        const option = document.createElement("option");
                        option.value = sentence.id;
                        option.textContent = sentence.sentence;
                        selectElement.appendChild(option);
                    });
                    selectElement.value = "";

                    

                    // Добавляем выпадающий список перед кнопкой
                    buttonElement.parentNode.insertBefore(selectElement, buttonElement);

                    // Обработка выбора предложения
                    selectElement.addEventListener("change", function() {
                        if (selectElement.value === "") {
                            // Если выбрано пустое поле, вызываем функцию для инпута
                            
                            createInputForNewSentence(buttonElement);
                            selectElement.remove();  // Удаляем выпадающий список
                        } else {
                            // Если выбрано предложение из списка, добавляем его в текст
                            const selectedSentence = selectElement.options[selectElement.selectedIndex].textContent;
                            const newSentenceElement = createEditableSentenceElement(selectedSentence);
                            buttonElement.parentNode.insertBefore(newSentenceElement, buttonElement);
                            selectElement.remove();  
                        }
                    });

                } else {
                    // Если предложений нет, вызываем функцию для инпута
                    createInputForNewSentence(buttonElement);
                }
            }).catch(error => {
                console.error("Error:", error);
            });
        });
    });
});