// admin.js

document.addEventListener("DOMContentLoaded", function() {

    // При загрузке страницы сразу загружаем версии моделей spacy, и обновляем логику отката на предыдущие модели spacy
    fetch("/admin/get_available_models")
        .then(res => res.json())
        .then(data => renderModelVersions(data.models))
        .catch(err => console.error("Ошибка при загрузке версий модели:", err));

    const tableCheckboxes = document.querySelectorAll(".admin-filter__checkbox--table");


    updateRetrainButton(); // Функция запрашивает с сервера данные о том, 
    // сколько собрано записей для обучения spacy обновляет текст кнопки 
    // "Обучить модель" в зависимости от этого и делает кнопку активной 
    // или неактивной

    
    // Функция добавляет слушатель на кнопку "Обучить модель"
    document.getElementById("retrainМodelButton").addEventListener("click", function() {
        setupRetrainButtonListener(this);
    });

    // Слушатель для кнопки "Показать данные для обучения"
    document.getElementById("show-training-data-btn").addEventListener("click", () => {
        fetch("/admin/get_training_data")
            .then(res => res.json())
            .then(data => displayTrainingData(data))
            .catch(err => console.error("Ошибка загрузки данных:", err));
    });


    
    // Добавляем слушатели для чекбоксов таблиц
    tableCheckboxes.forEach(checkbox => {
        checkbox.addEventListener("change", handleTableToggle);
    });

    // Слушатель для кнопки "Получить данные"
    document.getElementById("sendSelectedData").addEventListener("click", sendSelectedData);

    // Слушатель для кнопки "Найти пользователя"
    document.getElementById("search-user-button").addEventListener("click", searchUser);

    // Слушатель для кнопки "Сохранить изменения" не видна, пока не найден пользователь
    document.getElementById("save-user-button").addEventListener("click", saveUserChanges);

});




// Функции, которые загружаются при загрузке страницы


// Функция для поиска пользователя
function searchUser() {
    const searchValue = document.getElementById("search-user").value.trim();

    // Отправляем запрос на сервер для поиска пользователя
    sendRequest({
        url: "/admin/search_user",
        method: "POST",
        csrfToken: csrfToken,
        data: { search: searchValue }
    })
        .then(response => {
            if (response.status === "success") {
                const users = response.data;

                if (users.length === 1) {
                    // Если только один пользователь найден, сразу отображаем его детали
                    populateUserDetails(users[0]);
                } else if (users.length > 1) {
                    // Если найдено несколько пользователей, отображаем таблицу
                    displayUserResults(users);
                } else {
                    console.warn("Пользователи не найдены.");
                    hideUserResults();
                }
            }
        })
        .catch(error => {
            console.error("Ошибка при поиске пользователя:", error);
        });
}


// Функция для сохранения изменений данных пользователя
function saveUserChanges() {
    const userId = document.getElementById("user-id").value.trim();
    const updatedData = {
        username: document.getElementById("user-name").value.trim(),
        email: document.getElementById("user-email").value.trim(),
        role: document.getElementById("user-role").value
    };

    if (!userId) {
        console.warn("ID пользователя отсутствует. Попробуйте повторить поиск.");
        return;
    }

    // Отправляем данные на сервер для обновления
    sendRequest({
        url: `/admin/update_user/${userId}`,
        method: "PUT",
        csrfToken: csrfToken,
        data: updatedData
    })
        .then(response => {
            if (response.status === "success") {
                console.info("Данные пользователя успешно обновлены.");
            }
        })
        .catch(error => {
            console.error("Ошибка при сохранении изменений:", error);
        });
}



// Функция отвечающая за появление полей таблицы при выборе таблицы
function handleTableToggle(event) {
    const tableCheckbox = event.target; // Текущий чекбокс
    const tableName = tableCheckbox.value; // Имя таблицы
    const fieldsContainer = document.getElementById(`fields-${tableName}`); // Контейнер полей

    if (tableCheckbox.checked) {
        // Показываем список полей и отмечаем их
        fieldsContainer.style.display = "block";
        const columnCheckboxes = fieldsContainer.querySelectorAll(".admin-filter__checkbox--column");
        columnCheckboxes.forEach(checkbox => {
            checkbox.checked = true;
        });
    } else {
        // Скрываем список полей и снимаем отметки
        fieldsContainer.style.display = "none";
        const columnCheckboxes = fieldsContainer.querySelectorAll(".admin-filter__checkbox--column");
        columnCheckboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
    }
}


// Функция для отправки на сервер данных из чекбоксов, 
// для фильтрации обеспечивает работу кнопки "получить данные"
function sendSelectedData() {
    // Сбор выбранных таблиц
    const selectedTables = Array.from(document.querySelectorAll(".admin-filter__checkbox--table:checked")).map(checkbox => checkbox.value);

    // Сбор выбранных полей по каждой таблице
    const selectedColumns = {};
    selectedTables.forEach(table => {
        const columns = Array.from(document.querySelectorAll(`.admin-filter__checkbox--column[data-table="${table}"]:checked`)).map(checkbox => checkbox.value);
        if (columns.length > 0) {
            selectedColumns[table] = columns;
        }
    });

    // Формируем данные для отправки
    const data = {
        tables: selectedTables,
        columns: selectedColumns
    };

    // Отправка данных на сервер с использованием sendRequest из api.js
    sendRequest({
        url: "/admin/fetch_data",
        data: data,
    }).then(response => {
        displayData(response.data);
    }).catch(error => {
        console.error("Ошибка при отправке данных:", error);
    });
}

// Функция для управления кнопкой "Обучить модель"
function updateRetrainButton() {
    const button = document.getElementById("retrainМodelButton");
    if (!button) return;

    fetch("/admin/get_training_count")  // Создадим этот маршрут
        .then(response => response.json())
        .then(data => {
            const count = data.count || 0;
            button.textContent = `Переобучить модель (${count} / 50)`;
            button.disabled = count < 3;
        })
        .catch(err => {
            console.error("Ошибка при получении количества примеров для обучения:", err);
        });
}


// Функция обработки нажатия кнопки "Обучить модель"
function setupRetrainButtonListener(button) {

    console.log("Запуск переобучения модели...");
    button.disabled = true;
    button.textContent = "Обучение...";

    sendRequest({
        url: "/admin/train_spacy_model",
    })
    .then(response => {
        if (response.status === "success") {
            toastr.success("✅ Модель успешно переобучена!");
        } else {
            toastr.error("❌ Ошибка: " + response.message);
        }
        updateRetrainButton();
    })
    .catch(error => {
        console.error("Ошибка при запуске обучения:", error);
        toastr.error("❌ Ошибка при обучении модели");
        updateRetrainButton();
    });
}


function renderModelVersions(models) {
    const container = document.getElementById("model-versions-list");
    if (!container) return;

    console.log("Полученные версии моделей:", models);

    container.innerHTML = ""; // очистим

    models.forEach((model, index) => {
        const block = document.createElement("div");
        block.classList.add("model-version");

        const title = document.createElement("p");
        title.textContent = `Версия ${index === 0 ? "активная" : index} — ${model.name} (${model.modified})`;

        const revertButton = document.createElement("button");
        revertButton.textContent = `Откатить на версию ${index}`;
        revertButton.disabled = index === 0;  // активную откатывать нельзя

        revertButton.addEventListener("click", () => {
            if (confirm("Вы точно хотите откатить модель на предыдущую версию?")) {
                sendRequest({
                    url: `/admin/revert_model/${index}`,
                    method: "POST",
                    csrfToken: csrfToken
                }).then(res => {
                    if (res.status === "success") {
                        toastr.success("✅ Модель откатана!");
                        updateRetrainButton();
                        fetchModelVersions();
                    } else {
                        toastr.error("❌ Ошибка при откате: " + res.message);
                    }
                }).catch(err => {
                    toastr.error("❌ Ошибка при откате модели");
                    console.error(err);
                });
            }
        });

        block.appendChild(title);
        block.appendChild(revertButton);
        container.appendChild(block);
    });
}


// Функция для отображения данных для обучения spacy


function displayTrainingData(data) {
    const container = document.getElementById("training-data-view");
    container.innerHTML = "";  // очищаем

    data.forEach(example => {
        const { id, text, sent_starts } = example;

        const tokens = text.split(" ");
        const tokenSpans = tokens.map((token, i) => {
            const span = document.createElement("span");
            span.textContent = token + " ";
            if (sent_starts[i]) {
                span.classList.add("highlight-token");
            }
            return span;
        });

        const wrapper = document.createElement("div");
        wrapper.className = "training-item";
        tokenSpans.forEach(span => wrapper.appendChild(span));

        // Кнопки
        const deleteBtn = document.createElement("button");
        deleteBtn.textContent = "🗑";
        deleteBtn.onclick = () => deleteTrainingExample(id);

        const editBtn = document.createElement("button");
        editBtn.textContent = "✏️";
        editBtn.onclick = () => showTrainingPopup(text, updated => {
            updated.id = id;
            updateTrainingExample(updated);
        });

        wrapper.appendChild(editBtn);
        wrapper.appendChild(deleteBtn);
        container.appendChild(wrapper);
    });
}


// Вызываемые функции


/**
 * Отображение результатов поиска пользователей.
 * @param {Array} users - Список найденных пользователей.
 */
function displayUserResults(users) {
    const resultsSection = document.getElementById("user-results");
    const resultsBody = document.getElementById("user-results-body");

    // Очищаем предыдущие результаты
    resultsBody.innerHTML = "";

    // Заполняем таблицу результатами
    users.forEach(user => {
        const row = document.createElement("tr");
        row.setAttribute("data-user-id", user.id);

        row.innerHTML = `
            <td>${user.id}</td>
            <td>${user.username}</td>
            <td>${user.email}</td>
            <td>${user.current_role || "Не указана"}</td>
            <td><button class="btn btn-select-user" data-user-id="${user.id}">Выбрать</button></td>
        `;

        resultsBody.appendChild(row);
    });

    // Вешаем обработчики на кнопки "Выбрать"
    const selectButtons = document.querySelectorAll(".btn-select-user");
    selectButtons.forEach(button => {
        button.addEventListener("click", handleUserSelection);
    });

    // Показываем секцию результатов
    resultsSection.style.display = "block";
}


/**
 * Обработка выбора пользователя из списка.
 * @param {Event} event - Событие клика.
 */
function handleUserSelection(event) {
    const userId = event.target.getAttribute("data-user-id");

    // Отправляем запрос для получения полной информации о выбранном пользователе
    sendRequest({
        url: `/admin/search_user`,
        method: "POST",
        csrfToken: csrfToken,
        data: { search: userId }
    })
        .then(response => {
            if (response.status === "success" && response.data.length === 1) {
                populateUserDetails(response.data[0]);
            } else {
                console.warn("Не удалось загрузить данные пользователя.");
            }
        })
        .catch(error => {
            console.error("Ошибка при загрузке данных пользователя:", error);
        });
}


// Функция для заполнения данных пользователя
function populateUserDetails(userData) {
    const userDetailsSection = document.getElementById("user-details");

    document.getElementById("user-id").value = userData.id;
    document.getElementById("user-name").value = userData.username;
    document.getElementById("user-email").value = userData.email;

    // Заполняем выпадающий список ролей
    const userRoleSelect = document.getElementById("user-role");
    userRoleSelect.innerHTML = "";
    userData.all_roles.forEach(role => {
        const option = document.createElement("option");
        option.value = role;
        option.textContent = role;
        if (role === userData.current_role) {
            option.selected = true;
        }
        userRoleSelect.appendChild(option);
    });

    // Показываем секцию с деталями пользователя
    userDetailsSection.style.display = "block";
}


// Функция для отображения данных на странице в блоке "Данные таблиц"
function displayData(data) {
    const dataContainer = document.querySelector(".admin-data");
    dataContainer.innerHTML = ""; // Очистка контейнера перед добавлением новых данных

    for (const [tableName, rows] of Object.entries(data)) {
        const tableBlock = document.createElement("div");
        tableBlock.classList.add("admin-data__table");

        const tableTitle = document.createElement("h3");
        tableTitle.textContent = `Название таблицы: ${tableName}`;
        tableBlock.appendChild(tableTitle);

        const table = document.createElement("table");
        table.classList.add("admin-data__table-element");

        if (rows.length > 0) {
            const headerRow = document.createElement("tr");
            const columnHeaders = Object.keys(rows[0]);

            if (columnHeaders.includes("id")) {
                columnHeaders.splice(columnHeaders.indexOf("id"), 1);
                columnHeaders.unshift("id");
            }

            columnHeaders.forEach(column => {
                const headerCell = document.createElement("th");
                headerCell.textContent = column;
                if (column === "id") {
                    headerCell.style.color = "red";
                }
                headerRow.appendChild(headerCell);
            });

            const actionHeaderCell = document.createElement("th");
            actionHeaderCell.textContent = "Action";
            headerRow.appendChild(actionHeaderCell);
            table.appendChild(headerRow);

            rows.forEach(row => {
                const rowElement = document.createElement("tr");
                rowElement.setAttribute("data-id", row["id"]);
                rowElement.setAttribute("data-table", tableName);

                columnHeaders.forEach(column => {
                    const cell = document.createElement("td");
                    const cellData = row[column];

                    // Добавляем data-атрибут для хранения имени колонки
                    cell.setAttribute("data-column", column);

                    if (column === "id") {
                        cell.style.color = "red";
                    }

                    // Логика проверки данных
                    if (typeof column === "string" && (column.toLowerCase().includes("user_pass") || column.toLowerCase().includes("hash"))) {
                        cell.textContent = "скрытый пароль";
                    } else {
                        cell.textContent = cellData !== undefined ? cellData : "";
                    }

                    if (column !== "id") {
                        cell.setAttribute("data-editable", "true");
                        cell.setAttribute("contenteditable", "false");
                    }

                    rowElement.appendChild(cell);
                });

                const actionCell = document.createElement("td");
                actionCell.classList.add("admin-data__action-cell");

                const editButton = document.createElement("button");
                editButton.textContent = "Edit";
                editButton.classList.add("btn", "btn-edit");
                editButton.onclick = () => handleEdit(row.id, tableName, rowElement, editButton);

                const deleteButton = document.createElement("button");
                deleteButton.textContent = "Delete";
                deleteButton.classList.add("btn", "btn-delete");
                deleteButton.onclick = () => handleDelete(row.id, tableName);

                actionCell.appendChild(editButton);
                actionCell.appendChild(deleteButton);
                rowElement.appendChild(actionCell);

                table.appendChild(rowElement);
            });
        } else {
            const noDataMessage = document.createElement("p");
            noDataMessage.textContent = "Нет данных для отображения";
            tableBlock.appendChild(noDataMessage);
        }

        tableBlock.appendChild(table);
        dataContainer.appendChild(tableBlock);
    }
}


// Функция внесения изменений в данные, привязана к кнопке "Edit", 
// которая создается в функции displayData
function handleEdit(id, tableName, rowElement, editButton) {
    const isEditing = editButton.textContent === "Save";

    if (isEditing) {
        const updatedData = {};

        // Собираем значения всех редактируемых ячеек с учетом data-column
        rowElement.querySelectorAll("td[data-editable='true']").forEach(cell => {
            const columnName = cell.getAttribute("data-column");
            updatedData[columnName] = cell.textContent.trim();
            cell.setAttribute("contenteditable", "false");
        });

        sendRequest({
            url: `/admin/update/${tableName}/${id}`,
            csrfToken: csrfToken,
            method: "PUT",
            data: updatedData
        })
        .then(response => {
            if (response.success) {
                console.log(`Запись с id ${id} успешно обновлена.`);
            } else {
                console.error("Ошибка при обновлении записи:", response.error);
            }
        })
        .catch(error => {
            console.error("Произошла ошибка:", error);
        });

        editButton.textContent = "Edit";
    } else {
        // Переключаем ячейки в режим редактирования
        rowElement.querySelectorAll("td[data-editable='true']").forEach(cell => {
            cell.setAttribute("contenteditable", "true");
        });

        editButton.textContent = "Save";
    }
}


// Функция удаления записи из таблицы, привязана к кнопке "Delete", 
// которая создается в функции displayData
function handleDelete(id, tableName) {
    if (confirm(`Вы уверены, что хотите удалить запись с id ${id} из таблицы ${tableName}?`)) {
        sendRequest({
            url: `/admin/delete/${tableName}/${id}`,
            method: "DELETE",
            csrfToken: csrfToken
        })
        .then(response => {
            if (response.success) {
                console.log(`Запись с id ${id} успешно удалена.`);
                // Обновляем данные на экране после удаления
                displayDataAfterDeletion(id, tableName);
            } else {
                console.error("Ошибка при удалении записи:", response.error);
            }
        })
        .catch(error => {
            console.error("Произошла ошибка:", error);
        });
    }
}


// Функция удаляет данные из датасета для обучения spacy
function deleteTrainingExample(id) {
    sendRequest({
        url: `/admin/delete_training_example/${id}`,
        method: "DELETE",
    })
    .then(res => {
        if (res.status === "success") {
            toastr.success("Пример удалён");
            document.getElementById("show-training-data-btn").click(); // перезагрузим список
        } else {
            toastr.error("Ошибка при удалении: " + res.message);
        }
    })
    .catch(err => {
        console.error("Ошибка удаления:", err);
    });
}


// Функция для отображения попапа редактирования датасета для обучения spacy
function updateTrainingExample({ id, text, sent_starts }) {
    sendRequest({
        url: "/admin/update_training_example",
        method: "POST",
        data: { id, text, sent_starts }
    })
    .then(res => {
        if (res.status === "success") {
            toastr.success("Пример обновлён");
            document.getElementById("show-training-data-btn").click();
        } else {
            toastr.error("Ошибка при обновлении: " + res.message);
        }
    })
    .catch(err => {
        console.error("Ошибка обновления:", err);
    });
}



// Вспомогательные функции



// Скрытие секции с результатами поиска пользователя используется в searchUser
function hideUserResults() {
    document.getElementById("user-results").style.display = "none";
}


// Функция для обновления интерфейса после удаления используется в handleDelete
function displayDataAfterDeletion(id, tableName) {
    const rowToDelete = document.querySelector(`[data-id="${id}"][data-table="${tableName}"]`);
    console.log(rowToDelete)
    if (rowToDelete) {
        rowToDelete.remove();
    }
}


// Проверка, является ли значение полем пароля используется в displayData
function isPasswordField(columnName) {
    return typeof columnName === "string" && (columnName.toLowerCase().includes("user_pass") || columnName.toLowerCase().includes("hash"));
}











