// key_words.js

document.addEventListener("DOMContentLoaded", function(){
    // Добавляем слушатель события для кнопки удаления ключевых слов
    setupDeleteKeywordsListener();
    // Добавляем слушатель события для кнопок редактирования ключевых слов
    setupEditKeywordsListener();
    // Добавляем слушатель события для кнопок добавления ключевых слов
    setupAddKeywordsListener();
    // Добавляем слушатель события для кнопок удаления связи ключевых слов с отчетами
    setupUnlinkKeywordsListener();
    // Добавляем слушатель для чекбокса "Link to Reports"
    setupLinkReportsCheckboxListener();
    // Добавляем слушатель для формы добавления новой группы ключевых слов
    setupKeywordsFormListener();
    // Добавляем слушатель для кнопки загрузки файла с ключевыми словами
    setupUploadWordButtonListener();
});


/**
 * Устанавливает слушатель для формы добавления новой группы ключевых слов и обрабатывает отправку данных на сервер.
 */
function setupKeywordsFormListener() {
    const keywordsForm = document.getElementById("keywords-form");

    keywordsForm.addEventListener("submit", function(event) {
        event.preventDefault();

        const keyWordInput = document.getElementById("key_word_input").value;
        const linkReportsCheckbox = document.getElementById("link_reports_checkbox").checked;
        const ignoreUniqueCheck = document.getElementById("ignore_unique_check").checked;

        // Собираем выбранные отчеты, если чекбокс отмечен
        let reportIds = [];
        if (linkReportsCheckbox) {
            const reportCheckboxes = document.querySelectorAll('input[name="report_ids"]:checked');
            reportCheckboxes.forEach(checkbox => reportIds.push(checkbox.value));
        }

        // Отправляем данные на сервер
        sendRequest({
            url: "/key_words/add_keywords",
            method: "POST",
            data: {
                key_word_input: keyWordInput,
                ignore_unique_check: ignoreUniqueCheck,
                report_ids: reportIds  // Передаем выбранные отчеты
            },
            csrfToken: csrfToken
        }).then(() => location.reload()).catch(error => console.error("Error:", error));
    });
}

/**
 * Устанавливает слушатель для чекбокса "Link to Reports" для key words и обрабатывает отображение/скрытие списка отчетов.
 */
function setupLinkReportsCheckboxListener() {
    const linkReportsCheckbox = document.getElementById('link_reports_checkbox');
    const reportCheckboxesContainer = document.getElementById('report-checkboxes-container');

    linkReportsCheckbox.addEventListener('change', function () {
        if (this.checked) {
            reportCheckboxesContainer.style.display = 'block';
        } else {
            reportCheckboxesContainer.style.display = 'none';
        }
    });
}

/**
 * Устанавливает слушатели для кнопок удаления связи ключевых слов с отчетами и обрабатывает логику.
 */
function setupUnlinkKeywordsListener() {
    document.querySelectorAll(".key-word__btn--unlink").forEach(button => {
        button.addEventListener("click", function () {
            const reportId = this.dataset.report;
            const groupIndex = this.dataset.group;

            // Отправляем запрос для удаления связи ключевого слова с отчетом
            sendRequest({
                url: "/key_words/unlink_keyword_from_report",
                method: "POST",
                data: {
                    group_index: groupIndex,
                    report_id: reportId
                },
                csrfToken: csrfToken
            }).then(() => location.reload());
        });
    });
}


/**
 * Устанавливает слушатели для кнопок добавления ключевых слов и обрабатывает логику добавления (кнопка Add Word).
 */
function setupAddKeywordsListener() {
    document.querySelectorAll(".key-word__btn--add").forEach(button => {
        button.addEventListener("click", function () {
            const groupIndex = this.dataset.group;
            const reportId = this.dataset.report || null;
            let inputContainer;

            // Если контейнер не существует, создаем его динамически
            if (reportId) {
                inputContainer = document.querySelector(`.key-word__input-container[data-group='${groupIndex}'][data-report='${reportId}']`);
            } else {
                inputContainer = document.querySelector(`.key-word__input-container[data-group='${groupIndex}']`);
            }

            if (!inputContainer) {
                inputContainer = createInputContainer(groupIndex, reportId);  // Создаем контейнер динамически
                this.parentNode.insertBefore(inputContainer, this.nextSibling);  // Вставляем контейнер после кнопки
            }

            if (this.textContent === "Add Word") {
                inputContainer.style.display = "inline-block";
                this.textContent = "Save";
            } else {
                const inputElement = inputContainer.querySelector(".key-word__input--add");
                const newKeywords = inputElement.value.trim();

                if (!newKeywords) {
                    alert("Please enter at least one keyword.");
                    return;
                }

                sendRequest({
                    url: "/key_words/add_word_to_exist_group",
                    method: "POST",
                    csrfToken: csrfToken,
                    data: reportId ? { report_id: reportId, group_index: groupIndex, key_word_input: newKeywords }
                                   : { group_index: groupIndex, key_word_input: newKeywords }
                    
                }).then(() => location.reload());
            }
        });
    });

    /**
     * Создает и возвращает динамический контейнер для ввода новых ключевых слов.
     * @param {string} groupIndex - Индекс группы ключевых слов.
     * @param {string|null} reportId - ID отчета, если применимо.
     * @returns {HTMLElement} - Элемент контейнера с полем ввода.
     */
    function createInputContainer(groupIndex, reportId = null) {
        const container = document.createElement("div");
        container.classList.add("key-word__input-container");
        container.setAttribute("data-group", groupIndex);
        if (reportId) {
            container.setAttribute("data-report", reportId);
        }
        container.style.display = "none";

        const input = document.createElement("input");
        input.classList.add("key-word__input--add");
        input.type = "text";
        input.placeholder = "Enter new keyword(s)";

        container.appendChild(input);
        return container;
    }
}


/**
 * Устанавливает слушатели для кнопок редактирования ключевых слов и обрабатывает логику редактирования.
 */
function setupEditKeywordsListener() {
    document.querySelectorAll(".key-word__btn--edit, .key-word__btn--edit-plus-report").forEach(button => {
        button.addEventListener("click", function () {
            const groupElement = document.querySelector(`.key-word__list[data-group='${this.dataset.group}']`);

            if (groupElement) {
                const spans = groupElement.querySelectorAll("span");

                if (this.textContent === "Edit") {
                    // Преобразуем span в input для редактирования
                    spans.forEach(span => {
                        const input = document.createElement("input");
                        input.value = span.textContent.trim().replace(/,\s*$/, '');  // Убираем запятую
                        input.setAttribute("data-id", span.getAttribute("data-id"));  // Переносим id слова в input
                        input.classList.add("key-word__input--edit");
                        span.replaceWith(input);
                    });
                    this.textContent = "Save";
                } else {
                    // Собираем измененные ключевые слова с их id
                    const updatedWords = [];
                    const inputs = groupElement.querySelectorAll(".key-word__input--edit");
                    inputs.forEach(input => {
                        updatedWords.push({
                            id: input.getAttribute("data-id"),  // Добавляем id слова
                            word: input.value.trim()  // Добавляем измененное ключевое слово
                        });
                    });

                    // Отправляем изменения на сервер
                    sendRequest({
                        url: "/key_words/edit_keywords",
                        method: "POST",
                        data: { key_words: updatedWords },  // Передаем массив слов с id и новым значением
                        csrfToken: csrfToken
                    }).then(() => location.reload());
                }
            }
        });
    });
}


/**
 * Устанавливает слушатели для кнопок удаления ключевых слов и обрабатывает логику удаления.
 */
function setupDeleteKeywordsListener() {
    document.querySelectorAll(".key-word__btn--delete").forEach(button => {
        button.addEventListener("click", function() {
            const groupIndex = this.dataset.group;  // Получаем group_index

            sendRequest({
                url: "/key_words/delete_keywords", 
                data: { group_index: groupIndex },
                csrfToken: csrfToken
            })
            .then(() => location.reload());
        });
    });
}


/**
 * Устанавливает слушатель для кнопки загрузки файла с ключевыми словами и обрабатывает отправку файла на сервер.
 */
function setupUploadWordButtonListener() {
    const uploadWordButton = document.getElementById('upload-word-btn');

    uploadWordButton.addEventListener('click', function(event) {
        event.preventDefault(); 
        const ignoreUniqueCheck = document.getElementById("ignore_unique_check").checked ? "true" : "false";

        // Получаем файл из input
        const fileInput = document.getElementById('word-file-input');
        const file = fileInput.files[0];

        if (!file) {
            alert('Please select a file.');
            return;
        }

        // Создаем объект FormData для отправки файла
        const formData = new FormData();
        formData.append('file', file);
        formData.append('ignore_unique_check', ignoreUniqueCheck);
        formData.append("csrf_token", csrfToken)

        // Отправляем данные на сервер
        sendRequest({
            url: "/key_words/upload_keywords_from_word",  
            data: formData
        })
        .then(() => {
            location.reload(); 
        })
        .catch(error => {
            console.error("Error:", error);
        });
    });
}




