// static/js/report_settings.js

// Функция удаления ключевых слов
function deleteKeywords({ groupIndex, reportId = null }) {
    const data = reportId ? { report_id: reportId, group_index: groupIndex } : { group_index: groupIndex };
    sendRequest({
        url: "/report_settings/delete_keywords", // URL необходимо изменить на относительный, если нужно
        method: "POST",
        data: data
    }).then(() => location.reload());
}

// Функция редактирования ключевых слов
function editKeywords({ updatedWords }) {
    sendRequest({
        url: "/report_settings/edit_keywords",
        method: "POST",
        data: { key_words: updatedWords }  // Передаем массив слов с id и новым значением
    }).then(() => location.reload());
}

// Функция добавления ключевого слова в существующую группу ключевых слов
function addKeywords({ groupIndex, reportId = null, newKeywords }) {
    const data = reportId ? { report_id: reportId, group_index: groupIndex, key_word_input: newKeywords } : { group_index: groupIndex, key_word_input: newKeywords };
    sendRequest({
        url: "/report_settings/add_word_to_exist_group",
        method: "POST",
        data: data
    }).then(() => location.reload());
}

// Универсальная функция для обработки нажатия кнопки Edit для ключевых слов
function handleEditButtonClick(button) {
    const groupElement = document.querySelector(`.key-words-group[data-group='${button.dataset.group}']`);

    if (groupElement) {
        const spans = groupElement.querySelectorAll("span");

        if (button.textContent === "Edit") {
            // Преобразуем span в input для редактирования
            spans.forEach(span => {
                const input = document.createElement("input");
                input.value = span.textContent.trim().replace(/,\s*$/, '');  // Убираем запятую
                input.setAttribute("data-id", span.getAttribute("data-id"));  // Переносим id слова в input
                input.classList.add("key-word-input");
                span.replaceWith(input);
            });
            button.textContent = "Save";
        } else {
            // Собираем измененные ключевые слова с их id
            const updatedWords = [];
            const inputs = groupElement.querySelectorAll(".key-word-input");
            inputs.forEach(input => {
                updatedWords.push({
                    id: input.getAttribute("data-id"),  // Добавляем id слова
                    word: input.value.trim()  // Добавляем измененное ключевое слово
                });
            });

            // Отправляем изменения на сервер
            editKeywords({ updatedWords });  // Передаем только обновленные ключевые слова с их id
        }
    }
}

// Универсальная функция для обработки нажатия кнопки Add для ключевых слов
function handleAddButtonClick(button) {
    const groupIndex = button.dataset.group;
    const inputContainer = document.querySelector(`.add-keyword-input[data-group='${groupIndex}']`);

    if (inputContainer) {
        if (button.textContent === "Add Word") {
            // Показать поле для ввода и изменить текст кнопки на Save
            inputContainer.style.display = "inline-block";
            button.textContent = "Save";
        } else {
            // Собрать данные и отправить на сервер, после этого скрыть поле и изменить текст кнопки обратно на Add Word
            const inputElement = inputContainer.querySelector(".new-keyword-input");
            const newKeywords = inputElement.value.trim();

            if (!newKeywords) {
                alert("Please enter at least one keyword.");
                return;
            }

            addKeywords({ groupIndex, newKeywords });  // Отправляем данные на сервер
        }
    }
}

// Логика для кнопок Edit в глобальном и report-specific блоках
document.querySelectorAll(".edit-keywords-btn, .edit-report-keywords-btn").forEach(button => {
    button.addEventListener("click", function() {
        handleEditButtonClick(this);  // Обрабатываем нажатие на кнопку Edit
    });
});





// Удаление группы слов глобально
document.querySelectorAll(".delete-keywords-btn").forEach(button => {
    button.addEventListener("click", function() {
        const groupIndex = this.dataset.group;  // Получаем group_index
        deleteKeywords({ groupIndex });  // Удаляем ключевые слова для global_key_words
    });
});




// Удаление для конкретного отчета
document.querySelectorAll(".delete-report-keywords-btn").forEach(button => {
    button.addEventListener("click", function() {
        const reportId = this.dataset.report;  // Получаем report_id
        const groupIndex = this.dataset.group;  // Получаем group_index
        deleteKeywords({ reportId, groupIndex });  // Удаляем ключевые слова для report_key_words
    });
});

// Добавление слова в группу глобально
document.querySelectorAll(".add-keywords-btn").forEach(button => {
    button.addEventListener("click", function() {
        handleAddButtonClick(this);  // Обрабатываем нажатие на кнопку Add Word
    });
});

// Добавление слова в группу для отчета
document.querySelectorAll(".add-report-keywords-btn").forEach(button => {
    button.addEventListener("click", function() {
        handleAddButtonClick(this);  // Обрабатываем нажатие на кнопку Add Word для report-specific
    });
});


// File directory logic
function updateDirectoryPath() {
    var input = document.getElementById('file-input');
    var path = input.files[0].webkitRelativePath;
    document.getElementById('directory-path').value = path.split('/')[0];
}

// Показываем или скрываем список отчетов при выборе чекбокса
document.getElementById('link_reports_checkbox').addEventListener('change', function() {
    const reportCheckboxesContainer = document.getElementById('report-checkboxes-container');
    if (this.checked) {
        reportCheckboxesContainer.style.display = 'block';
    } else {
        reportCheckboxesContainer.style.display = 'none';
    }
});

// Добавление нового ключевого слова на страницу
document.getElementById("keywords-form").addEventListener("submit", function(event) {
    event.preventDefault();

    const keyWordInput = document.getElementById("key_word_input").value;
    const linkReportsCheckbox = document.getElementById("link_reports_checkbox").checked;

    // Собираем выбранные отчеты, если чекбокс отмечен
    let reportIds = [];
    if (linkReportsCheckbox) {
        const reportCheckboxes = document.querySelectorAll('input[name="report_ids"]:checked');
        reportCheckboxes.forEach(checkbox => reportIds.push(checkbox.value));
    }

    // Отправляем данные на сервер
    sendRequest({
        url: "/report_settings/add_keywords",
        method: "POST",
        data: {
            key_word_input: keyWordInput,
            report_ids: reportIds  // Передаем выбранные отчеты
        }
    }).then(() => location.reload()).catch(error => console.error("Error:", error));
});

// Загрузка файла шаблона для word на сервер
document.getElementById("file-upload-form").addEventListener("submit", function(event) {
    event.preventDefault();
    
    const formData = new FormData();
    const fileInput = document.getElementById("file-input");
    formData.append("file", fileInput.files[0]);

    // Используем sendRequest для отправки файла
    sendRequest({
        url: "{{ url_for('report_settings.upload_template') }}",
        method: "POST",
        data: formData  // Отправляем объект FormData
    })
    .then(() => {
        alert("File uploaded successfully");
        location.reload();
    })
    .catch(error => {
        console.error("Error:", error);
        alert("File upload failed: " + error.message);
    });
});
