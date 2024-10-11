// static/js/report_settings.js
// v0.3.0

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

// Функция для удаления связи ключевого слова с отчетом
function unlinkKeywordFromReport({ groupIndex, reportId }) {
    sendRequest({
        url: "/report_settings/unlink_keyword_from_report",
        method: "POST",
        data: {
            group_index: groupIndex,
            report_id: reportId
        }
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
    const reportId = button.dataset.report || null;  // Если есть reportId, используем его
    let inputContainer;

    if (reportId) {
        // Если это ключевые слова, привязанные к отчету
        inputContainer = document.querySelector(`.add-keyword-input[data-group='${groupIndex}'][data-report='${reportId}']`);
    } else {
        // Если это глобальные ключевые слова
        inputContainer = document.querySelector(`.add-keyword-input[data-group='${groupIndex}']`);
    }

    if (inputContainer) {
        if (button.textContent === "Add Word") {
            // Показать поле для ввода и изменить текст кнопки на Save
            inputContainer.style.display = "inline-block";
            button.textContent = "Save";
        } else {
            // Собрать данные и отправить на сервер, после этого скрыть поле и изменить текст кнопки обратно на Add Word
            const inputElement = inputContainer.querySelector(".new-keyword-input");
            console.log(inputElement);
            const newKeywords = inputElement.value.trim();
            
            console.log(newKeywords);
            if (!newKeywords) {
                alert("Please enter at least one keyword.");
                return;
            }

            addKeywords({ groupIndex, reportId, newKeywords });  // Отправляем данные на сервер
        }
    } else {
        console.error("Input container not found for groupIndex:", groupIndex, "reportId:", reportId);
    }
}

// Логика для кнопок Edit в глобальном и report-specific блоках
document.querySelectorAll(".edit-keywords-btn, .edit-report-keywords-btn").forEach(button => {
    button.addEventListener("click", function() {
        handleEditButtonClick(this);  // Обрабатываем нажатие на кнопку Edit
    });
});

// Логика для кнопок Unlink в блоке ключевых слов, привязанных к отчетам
document.querySelectorAll(".unlink-report-keywords-btn").forEach(button => {
    button.addEventListener("click", function() {
        const reportId = this.dataset.report;
        const groupIndex = this.dataset.group;
        unlinkKeywordFromReport({ groupIndex, reportId });
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
        handleAddButtonClick(this); 
    });
});


// File directory logic
function updateDirectoryPath() {
    var input = document.getElementById('file-input');
    var path = input.files[0].webkitRelativePath;
    document.getElementById('directory-path').value = path.split('/')[0];
}

// Логика получения новых ключевых слов при нажатии на кнопку upload в секции upload word file with key words
document.getElementById('upload-word-btn').addEventListener('click', function(event) {
    event.preventDefault(); // Останавливаем стандартное поведение формы

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

    // Отправляем запрос на сервер
    sendRequest({
        url: "/report_settings/upload_keywords_from_word",  // Маршрут загрузки
        data: formData,
        // processData: false,  // Отключаем обработку данных
        // contentType: false,  // Отключаем установку заголовка Content-Type, т.к. FormData сам его установит
    })
    .then(response => {
        location.reload();  // Обновляем страницу после успешной загрузки
    })
    .catch(error => {
        alert(error.message);
    });
});


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

// Логика для добавления нового типа параграфа
document.getElementById('paragraph-type-form').addEventListener('submit', async function(event) {
    event.preventDefault(); // Prevent form submission and page reload

    const input = document.getElementById('new_paragraph_type');
    const newTypeName = input.value.trim();

    if (!newTypeName) {
        alert('Paragraph type name cannot be empty.');
        return;
    }

    try {
        const response = await sendRequest({
            url: '/report_settings/add_paragraph_type',  // Directly use the URL string
            method: 'POST',
            data: { new_paragraph_type: newTypeName },
        });

        // If the request is successful, update the list on the page
        if (response.status === 'success') {
            const paragraphTypesList = document.getElementById('paragraph-types-list');
            const newListItem = document.createElement('li');
            newListItem.textContent = newTypeName;
            paragraphTypesList.appendChild(newListItem);

            input.value = ''; // Clear the input field
            toastr.success(response.message);
        } else {
            alert(response.message);
        }
    } catch (error) {
        // Handle the error returned by sendRequest
        alert(error.message || 'An error occurred while adding the paragraph type.');
    }
});
