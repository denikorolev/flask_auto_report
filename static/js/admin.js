// admin.js


function toggleFields(tableName) {
    // Получаем контейнер для полей таблицы
    const fieldsContainer = document.getElementById(`fields-${tableName}`);
    const tableCheckbox = document.getElementById(`table-${tableName}`);

    // Проверяем состояние чекбокса таблицы
    if (tableCheckbox.checked) {
        // Показываем список полей и отмечаем их
        fieldsContainer.style.display = "block";
        const columnCheckboxes = fieldsContainer.querySelectorAll(`.admin-filter__checkbox--column`);
        columnCheckboxes.forEach(checkbox => {
            checkbox.checked = true;
        });
    } else {
        // Скрываем список полей и снимаем отметки
        fieldsContainer.style.display = "none";
        const columnCheckboxes = fieldsContainer.querySelectorAll(`.admin-filter__checkbox--column`);
        columnCheckboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
    }
}

// Функция для отправки на сервер данных из чекбоксов, для фильтрации
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
        csrfToken: csrfToken
    }).then(response => {
        displayData(response);
    }).catch(error => {
        console.error("Ошибка при отправке данных:", error);
    });
}



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


// Функция внесения изменений в данные
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




// Функция для обновления интерфейса после удаления
function displayDataAfterDeletion(id, tableName) {
    const rowToDelete = document.querySelector(`[data-id="${id}"][data-table="${tableName}"]`);
    console.log(rowToDelete)
    if (rowToDelete) {
        rowToDelete.remove();
    }
}





// Проверка, является ли значение полем пароля
function isPasswordField(columnName) {
    return typeof columnName === "string" && (columnName.toLowerCase().includes("user_pass") || columnName.toLowerCase().includes("hash"));
}







