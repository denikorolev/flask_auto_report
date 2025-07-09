// admin.js

document.addEventListener("DOMContentLoaded", function() {

    const tableCheckboxes = document.querySelectorAll(".admin-filter__checkbox--table");

    initCategoriesHandlers();

    
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


function initCategoriesHandlers() {
    // Загрузка категорий
    let categoriesCache = [];

    const levelInput = document.getElementById("category-level");
    const parentSelect = document.getElementById("parent-id");

    // Загрузка категорий с сервера
    const loadCategories = () => {
        sendRequest({
            url: "/admin/categories",
            method: "GET"
        }).then(response => {
            if (response.status === "success") {
                categoriesCache = response.data;
                renderCategories(categoriesCache);
            }
        });
    };

    // Рендерит варианты родителей только с нужным level
    const renderParentCategoryOptions = (categories, level) => {
        parentSelect.innerHTML = `<option value="">Нет родителя</option>`;
        if (!level || isNaN(level) || level <= 1) {
            parentSelect.disabled = true;
            parentSelect.value = "";
            return;
        }
        categories.forEach(cat => {
            if (cat.level === (level - 1)) {
                parentSelect.innerHTML += `<option value="${cat.id}">${cat.name} (id: ${cat.id}, уровень: ${cat.level})</option>`;
            }
        });
        parentSelect.disabled = false;
    };

    // Отрисовка таблицы категорий
    const renderCategories = (categories) => {
        const tbody = document.querySelector("#category-table tbody");
        tbody.innerHTML = "";
        categories.forEach(cat => {
            const tr = document.createElement("tr");
            const idToName = {};
                categories.forEach(cat => {
                    idToName[cat.id] = cat.name;
                });
            tr.innerHTML = `
                <td>${cat.id}</td>
                <td>${cat.name}</td>
                <td>${cat.level}</td>
                <td>${cat.parent_id ? (idToName[cat.parent_id] || cat.parent_id) : "<-->"}</td>
                <td>
                    <button class="btn btn-delete-category" data-id="${cat.id}">Удалить</button>
                </td>
            `;
            tbody.appendChild(tr);
        });

        // Навешиваем обработчики на кнопки удаления
        tbody.querySelectorAll(".btn-delete-category").forEach(btn => {
            btn.addEventListener("click", function() {
                if (confirm("Удалить категорию?")) {
                    deleteCategory(this.dataset.id);
                }
            });
        });
    };

    // Добавление новой категории
    const addCategory = () => {
        const name = document.getElementById("category-name").value.trim();
        const level = parseInt(document.getElementById("category-level").value, 10);
        const parent_id_val = document.getElementById("parent-id").value;
        const parent_id = parent_id_val ? parseInt(parent_id_val, 10) : null;

        if (!name) {
            alert("Введите название категории");
            return;
        }

        if (isNaN(level) || level < 0) {
            alert("Введите корректный уровень категории");
            return;
        }

        // === Новая валидация: если уровень > 1 и не выбран родитель ===
        if (level > 1 && !parent_id) {
            alert("Для категории с уровнем больше 1 необходимо выбрать родительскую категорию.");
            return;
        }


        // === ПРОВЕРКА НА УНИКАЛЬНОСТЬ  ===
        
        const nameLower = name.toLowerCase();
        const exists = categoriesCache.some(cat =>
            cat.level === level &&
            cat.name.toLowerCase() === nameLower
        );
        if (exists) {
            alert("Глобальная категория с таким именем уже существует на этом уровне.");
            return;
        }
        

        sendRequest({
            url: "/admin/categories",
            method: "POST",
            data: { name, level, parent_id }
        })
        .then(response => {
            if (response.status === "success") {
                loadCategories();
                document.getElementById("add-category-form").reset();
            } else {
                alert(response.message || "Ошибка при добавлении");
            }
        })
        .catch(error => alert("Ошибка: " + error));
    };

    // Удаление категории
    const deleteCategory = (id) => {
        sendRequest({
            url: `/admin/categories/${id}`,
            method: "DELETE"
        })
        .then(response => {
            if (response.status === "success") {
                loadCategories();
            } else {
                alert(response.message || "Ошибка при удалении");
            }
        })
        .catch(error => alert("Ошибка: " + error));
    };

    // Следим за изменением поля уровня
    levelInput.addEventListener("input", function() {
        const newLevel = parseInt(levelInput.value, 10);
        renderParentCategoryOptions(categoriesCache, newLevel);
    });

    // Слушатель для формы добавления
    document.getElementById("add-category-form").addEventListener("submit", function(e) {
        e.preventDefault();
        addCategory();
    });

    // Первичная загрузка категорий при инициализации
    loadCategories();

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


// Логика для кнопки "Сделать все протоколы публичными"
document.getElementById("make-all-public").addEventListener("click", function () {
    if (!confirm("Сделать все протоколы публичными?")) return;
    sendRequest({
        url: "/admin/make_all_public",
    }).then(result => {
        const statusBox = document.getElementById("make-public-status");
        if (statusBox) {
            statusBox.innerHTML = ""; // очищаем старые сообщения
            if (result && result.status === "success") {
                const li = document.createElement("li");
                li.textContent = result.message || "Операция выполнена успешно";
                li.style.color = "green";
                statusBox.appendChild(li);
            } else {
                const li = document.createElement("li");
                li.textContent = result && result.message ? result.message : "Произошла ошибка";
                li.style.color = "red";
                statusBox.appendChild(li);
            }
        }
    });
});



// Логика для кнопки "Поделиться ключевыми словами"
document.getElementById("share-keywords").addEventListener("click", function () {
    const emailInput = document.getElementById("share-keywords-input");
    const email = emailInput.value.trim();
    if (!email) {
        alert("Введите email получателя.");
        return;
    }
    sendRequest({
        url: "/admin/share_global_keywords",
        data: { email }
    }).then(result => {
        if (statusBox) {
            statusBox.innerHTML = ""; // очищаем старые сообщения
            const li = document.createElement("li");
            if (result && result.status === "success") {
                li.textContent = result.message || "Операция выполнена успешно";
                li.style.color = "green";
                emailInput.value = "";
            } else {
                li.textContent = (result && result.message) ? result.message : "Произошла ошибка";
                li.style.color = "red";
            }
            statusBox.appendChild(li);
        }
    });
});


