// profile_settings.js

document.addEventListener("DOMContentLoaded", function(){

    // Инициализация слушателей изменения для элементов настроек, 
    // чтобы отправлять только измененные данные
    initializeChangeListeners(); 
    // Инициализация логики для модальностей
    initModalitySettings();

    // Слушатель на кнопку Сохранить (сохранить настройки профиля) с учетом того, что она может быть скрыта
    saveSettingsButton = document.getElementById("saveSettings");
    if (saveSettingsButton) {
        
        saveSettingsButton.addEventListener("click", () => {
            profileSettingsSave();
        });
    }   
    
    // Слушатель на кнопку Сохранить изменения (сохранить глобальные настройки профиля)
    document.getElementById("saveSettingProfile").addEventListener("click", () => {
        profileGlobalSettingsSave();
    });

    // Слушатель на кнопку "удалить профиль"
    document.getElementById("deleteProfile").addEventListener("click", () => {
        deleteProfile();
    });


    // Слушатель на кнопку "Поделиться профилем"
    document.getElementById("shareProfileButton").addEventListener("click", () => {
        shareProfileButtonHandler();
    });

    // Слушатель на кнопку "Пересобрать модальности из БД"
    document.getElementById("rebuildModalitiesFromDB").addEventListener("click", () => {
        rebuildModalitiesFromDB();
    });

});


/**
 * Добавляет обработчик клика на кнопку "Сохранить настройки профиля",
 * собирает данные профиля и отправляет их на сервер.Сохраняет глобальные настройки - имя профиля и описание.
 * Потом уберу его отсюда в настройки юзера
 */
function profileGlobalSettingsSave() {
    const profileSettingBlock = document.getElementById("profileSettingBlock");
    
    const settingsData = {
        profile_id: profileSettingBlock.dataset.profileId,
        profile_name: profileSettingBlock.querySelector("#profileName").value,
        description: profileSettingBlock.querySelector("#profileDescription").value,
        is_default: profileSettingBlock.querySelector("#isDefauleProfile").checked,
        username: profileSettingBlock.querySelector("#userName").value,
    };

    // Отправляем данные на сервер
    sendRequest({
        url: "/profile_settings/update_profile_settings",
        method: "POST",
        csrfToken: csrfToken,
        data: settingsData
    }).then(response => {
        if (response.status === "success") {
            window.location.reload(); // Перезагружаем страницу для обновления данных
        }
        console.log(response.message || "Settings updated successfully.");
    }).catch(error => {
        console.error("Failed to update settings:", error);
    });
}


/**
 * Добавляет обработчик клика на кнопку "Сохранить настройки", 
 * проверяет наличие флага изменения для каждого элемента формы,
 * собирает данные настроек и отправляет их на сервер.
 * После успешного сохранения удаляет флаг изменения и убирает класс изменения.
 */
function profileSettingsSave() {
    const inputs = document.getElementById("settings-block").querySelectorAll("input, select");
    const changedSettings = {};

    inputs.forEach(input => {
        if (input.dataset.changed === "true") { // Проверяем наличие флага
            // Собираем значение если чекбокс то берем checked если нет то value
            const value = input.type === "checkbox" ? input.checked : input.value;
            changedSettings[input.name] = value;
            }
        });

    console.log(changedSettings);
    // Отправляем данные на сервер
    sendRequest({
        url: "/profile_settings/update_settings",
        method: "POST",
        csrfToken: csrfToken,
        data: changedSettings
    }).then(response => {
        if (response.status === "success") {   
            window.location.reload();
            }
    }).catch(error => {
        console.error("Failed to update settings:", error);
    });
    
}

/** Инициализирует слушателей событий изменения для элементов формы настроек 
 * и устанавливает флаг для измененных элементов.
 * При изменении элемента добавляет класс изменения для родительского элемента <li>.
*/
function initializeChangeListeners() {
    const settingsBlock = document.getElementById("settings-block");
    if (settingsBlock) {
        const inputs = settingsBlock.querySelectorAll("input, select");
        inputs.forEach(input => {
            // Добавляем слушатель события изменения
            input.addEventListener("change", () => {
                input.dataset.changed = "true"; // Устанавливаем флаг для измененного элемента

            // Находим родительский <li> элемент
            const parentLi = input.closest(".settings-block__item");
            if (parentLi) {
                parentLi.classList.add("settings-block__item--changed"); // Добавляем класс
            }
            
            });
        });
    }
}


// Функция для обработки изменения модальности (при выборе radio кнопки)
function initModalitySettings() {
    // 1. Навешиваем слушатели на radio кнопки (модальности)
    const radios = document.querySelectorAll('input.modality-radio');
    radios.forEach(radio => {
        radio.addEventListener('change', function() {
            handleModalityChange(radio.value);
        });
    });

    // 2. Навешиваем слушатели на кнопки "✏️" )
    document.querySelectorAll('.edit-modality-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            openCategoryEditPopup(btn.getAttribute('data-id'), false);
        });
    });

    // 3. Выбираем первую модальность (если есть) и отображаем её области
    if (radios.length) {
        radios[0].checked = true;
        handleModalityChange(radios[0].value);
    }

    // Вешаю слушатели на кнопку Добавить модальность
    document.getElementById('addModalityButton').onclick = function() {
        openCategoryCreatePopup(false);
    };


    // Вешаю слушатель на кнопку Добавить область исследования
    document.getElementById('addAreaButton').onclick = function() {
        const selectedModalityId = document.querySelector('input.modality-radio:checked')?.value;
        if (!selectedModalityId) {
            alert("Сначала выберите модальность");
            return;
        }
        openCategoryCreatePopup(true, selectedModalityId);
    };

    // Фильтр областей исследования по имени
    document.getElementById('filterAreaInput').addEventListener('input', function() {
        filterAreasByName(this.value.trim());
    });
}


// Обработка выбора модальности — отрисовка областей
function handleModalityChange(modalityId) {
    const tree = window.categoriesTree || [];
    const modality = tree.find(m => String(m.id) === String(modalityId));
    const container = document.getElementById('areasList');
    container.innerHTML = '';

    if (modality && modality.children && modality.children.length) {
        modality.children.forEach(child => {
            const li = document.createElement('li');
            li.className = 'area-item';
            li.innerHTML = `
                <span>${child.name}</span>
                <span>(${child.global_name})</span>
                <button class="edit-area-btn" data-id="${child.id}" title="Редактировать область исследования">✏️</button>
            `;
            container.appendChild(li);
        });
        // Добавляем слушатель на кнопки редактирования областей
        container.querySelectorAll('.edit-area-btn').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                openCategoryEditPopup(btn.getAttribute('data-id'), true);
            });
        });
    } else {
        const li = document.createElement('li');
        li.textContent = 'Нет областей для выбранной модальности';
        li.style.color = '#888';
        container.appendChild(li);
    }
}



// Функция для открытия попапа редактирования категории
function openCategoryEditPopup(categoryId, isArea = false) {
    // 1. Найти категорию в дереве
    const popup = document.getElementById('categoryEditPopup');
    if (!popup) return;

    const tree = window.categoriesTree || [];
    const globalTree = window.globalCategoriesTree || [];
    let category;
    let globalCategories = [];
    let parentModality = null;

    if (isArea) {
        // 1. Находим область у пользователя и её родителя-модальность
        for (const mod of tree) {
            const found = (mod.children || []).find(child => String(child.id) === String(categoryId));
            if (found) {
                category = found;
                parentModality = mod;
                console.log("parentModality", parentModality);
                break;
            }
        }
        // 2. Ищем global_id модальности у пользователя
        let globalModality = null;
        if (parentModality && parentModality.global_id) {
            globalModality = (globalTree || []).find(gm => String(gm.id) === String(parentModality.global_id));
        }
        // 3. Если нашли — берём её children как глобальные области, иначе []
        globalCategories = globalModality ? (globalModality.children || []) : [];
    } else {
        // Находим модальность у пользователя
        category = tree.find(m => String(m.id) === String(categoryId));
        // Все глобальные модальности (level 1)
        globalCategories = globalTree;
    }
    if (!category) return;

    // Заполнить инпут
    document.getElementById('editCategoryName').value = category.name || "";

    // Заполнить селект
    const select = document.getElementById('editCategoryGlobal');
    select.innerHTML = `<option value="">— &lt;пусто&gt; —</option>`;
    globalCategories.forEach(gc => {
        select.innerHTML += `<option value="${gc.id}">${gc.name}</option>`;
    });
    // Выбрать нужную глобалку
    if (category.global_id && globalCategories.find(gc => gc.id == category.global_id)) {
        select.value = category.global_id;
    } else {
        select.value = "";
    }

    // Кнопки
    // Сохранение изменений
    document.getElementById('saveCategoryEditBtn').onclick = () => {
        const name = document.getElementById('editCategoryName').value.trim();
        console.log("global_id", select.value);
        return sendRequest({
            url: "/profile_settings/category_update",
            method: "POST",
            data: { "id": category.id, 
                    "name": name,
                    "global_id": select.value,
            }
        }).then(response => {
            if (response.status === "success") {
                // Обновляем категорию в дереве
                if (isArea) {
                    const area = (parentModality.children || []).find(child => String(child.id) === String(category.id));
                    console.log("area", area);
                    if (area) {
                        Object.assign(area, { name, global_id: select.value });
                    }
                    // --- Обновить DOM ---
                    const li = document.querySelector(
                        `#areasList li.area-item button.edit-area-btn[data-id="${category.id}"]`
                    )?.closest('li');
                    if (li) {
                        // Можно просто пересобрать innerHTML, но лучше только поменять что нужно:
                        const spans = li.querySelectorAll('span');
                        if (spans.length > 0) spans[0].textContent = name;
                        if (spans.length > 1) {
                            // Найди глобальное имя по глобальному id:
                            const globalName = (globalCategories.find(gc => String(gc.id) === String(select.value)) || {}).name || '-пусто-';
                            spans[1].textContent = `(${globalName})`;
                        }
                    }
                } else {
                    Object.assign(category, { name, global_id: select.value });
                    // Найти <li> по радиобатону
                    const li = document.querySelector(
                        `ul.categories-tree li input.modality-radio[value="${category.id}"]`
                    )?.closest('li');
                    if (li) {
                        // label > span.category-name
                        const spanName = li.querySelector('span.category-name');
                        if (spanName) spanName.textContent = name;
                        // label > span.category-id 
                        const spanGlobal = li.querySelector('span.category-id');
                        if (spanGlobal) {
                            const globalName = (globalCategories.find(gc => String(gc.id) === String(select.value)) || {}).name || '-пусто-';
                            spanGlobal.textContent = `(${globalName})`;
                        }
                    }
                }
                // Закрываем попап
                hideElement(popup);
            } else {
                alert("Ошибка при сохранении категории!");
                console.error("Failed to update category:", response.message);
            }
        });
    };
    // Удаление категории
    document.getElementById('deleteCategoryBtn').onclick = () => {
        return sendRequest({
            url: "/profile_settings/category_delete",
            method: "POST",
            data: { "id": category.id }
        }).then(response => {
            if (response.status === "success") {
                // Удаляем категорию из дерева
                if (isArea) {
                    const parentModality = tree.find(mod => mod.children && mod.children.some(child => String(child.id) === String(category.id)));
                    if (parentModality) {
                        parentModality.children = parentModality.children.filter(child => String(child.id) !== String(category.id));
                    }
                    // 2. Удаляем <li> из DOM
                    const li = document.querySelector(
                        `#areasList li.area-item button.edit-area-btn[data-id="${category.id}"]`
                    )?.closest('li');
                    if (li) li.remove();

                    // 3. Если областей не осталось — показать заглушку
                    const areasLeft = parentModality ? parentModality.children.length : 0;
                    if (areasLeft === 0) {
                        const container = document.getElementById('areasList');
                        const emptyLi = document.createElement('li');
                        emptyLi.textContent = 'Нет областей для выбранной модальности';
                        emptyLi.style.color = '#888';
                        container.appendChild(emptyLi);
                    }
                } else {
                    const index = tree.findIndex(m => String(m.id) === String(category.id));
                    if (index !== -1) {
                        tree.splice(index, 1);
                    }
                    const li = document.querySelector(
                        `ul.categories-tree li input.modality-radio[value="${category.id}"]`
                    )?.closest('li');
                    if (li) li.remove();
                    const firstRadio = document.querySelector('input.modality-radio');
                    if (firstRadio) {
                        firstRadio.checked = true;
                        handleModalityChange(firstRadio.value);
                    } else {
                        // Нет модальностей — очищаем области
                        document.getElementById('areasList').innerHTML = '';
                    }
                } 
                // Закрываем попап
                hideElement(popup);
            } else {
                alert("Ошибка при удалении категории!");
                console.error("Failed to delete category:", response.message);
            }
        });
    };

    const closeCategoryPopupButton = document.getElementById('closeCategoryEditPopup');
    closeCategoryPopupButton.onclick = () => {
        hideElement(popup);
    };

    // Показать попап
    showElement(popup);
}

// Функция для добавления новой категории (модальности или области в зависимости от нажатой кнопки)
function openCategoryCreatePopup(isArea = false, parentModalityId = null) {
    const popup = document.getElementById('categoryEditPopup');
    if (!popup) return;

    // Очищаем поля
    document.getElementById('editCategoryName').value = "";

    // Глобальный селект
    const select = document.getElementById('editCategoryGlobal');
    select.innerHTML = `<option value="">— &lt;пусто&gt; —</option>`;

    const globalTree = window.globalCategoriesTree || [];
    let globalCategories = [];

    if (isArea) {
        // Для области — находим нужную глобальную модальность
        let parentModality = (window.categoriesTree || []).find(m => String(m.id) === String(parentModalityId));
        let globalModality = null;
        if (parentModality && parentModality.global_id) {
            globalModality = globalTree.find(gm => String(gm.id) === String(parentModality.global_id));
        }
        globalCategories = globalModality ? (globalModality.children || []) : [];
    } else {
        // Для модальности — все глобальные модальности (level 1)
        globalCategories = globalTree;
    }

    globalCategories.forEach(gc => {
        select.innerHTML += `<option value="${gc.id}">${gc.name}</option>`;
    });
    select.value = "";

    // Меняем текст кнопки
    document.getElementById('saveCategoryEditBtn').textContent = "Добавить";

    // Скрыть кнопку удалить
    document.getElementById('deleteCategoryBtn').classList.add("hide");

    // Сохранение новой категории
    document.getElementById('saveCategoryEditBtn').onclick = () => {
        const name = document.getElementById('editCategoryName').value.trim();
        const global_id = select.value || null;
        if (!name) {
            alert("Введите имя категории");
            return;
        }
        if(!global_id) {
            alert("Выберите глобальную категорию. Глобальная категория это то, как программа видит вашу категорию в системе и, в зависимости от выбранного вами значения, будет обрабатывать протоколы, принадлежащие данной категории.");
            return;
        }
        // Собираем данные для запроса
        const data = {
            name,
            global_id,
            level: isArea ? 2 : 1
        };
        if (isArea) data.parent_id = parentModalityId;

        sendRequest({
            url: "/profile_settings/category_create",
            method: "POST",
            data: data
        }).then(response => {
            if (response.status === "success" && response.category) {
                // Добавить в дерево (и в DOM)
                if (isArea) {
                    // Найти модальность и добавить
                    let modality = (window.categoriesTree || []).find(m => String(m.id) === String(parentModalityId));
                    if (modality) {
                        modality.children = modality.children || [];
                        modality.children.push(response.category);
                        handleModalityChange(modality.id); // перерисовать области
                    }
                } else {
                    (window.categoriesTree || []).push(response.category);
                    
                    // Формируем новый li
                    const ul = document.querySelector('#modalitiesContainer ul.categories-tree');
                    if (ul) {
                        const li = document.createElement('li');
                        li.innerHTML = `
                            <label>
                                <input type="radio"
                                    name="modality_radio"
                                    class="modality-radio"
                                    value="${response.category.id}">
                                <span class="category-name">${response.category.name}</span>
                                <span class="category-id">(${response.category.global_name || ''})</span>
                            </label>
                            <span class="category-actions">
                                <button class="edit-modality-btn" data-id="${response.category.id}" title="Редактировать категорию">✏️</button>
                            </span>
                        `;
                        ul.appendChild(li);

                        // 3. Навешиваем слушатели
                        li.querySelector('input.modality-radio').addEventListener('change', function() {
                            handleModalityChange(response.category.id);
                        });
                        li.querySelector('.edit-modality-btn').addEventListener('click', function(e) {
                            e.preventDefault();
                            openCategoryEditPopup(response.category.id, false);
                        });

                        // 4. Сразу выбираем новую модальность
                        li.querySelector('input.modality-radio').checked = true;
                        handleModalityChange(response.category.id);
                    }
                }
                hideElement(popup);
            } else {
                alert("Ошибка при добавлении категории");
            }
        });
    };

    // Крестик — просто закрыть
    document.getElementById('closeCategoryEditPopup').onclick = () => {
        hideElement(popup);
    };

    // Показываем попап
    showElement(popup);

    // Вернуть стандартные кнопки после закрытия
    popup.onhide = () => {
        console.log("Popup closed, resetting buttons");
        document.getElementById('saveCategoryEditBtn').textContent = "Сохранить";
        document.getElementById('deleteCategoryBtn').classList.remove("hide");
        document.getElementById('saveCategoryEditBtn').onclick = null;
        document.getElementById('deleteCategoryBtn').onclick = null;
    };
}

// Фильтр областей исследования по имени
function filterAreasByName(query) {
    const minLength = 2; // Минимальная длина запроса для фильтрации
    const areasList = document.getElementById('areasList');
    if (!areasList) return;
    const items = areasList.querySelectorAll('li.area-item');

    if (query.length <= minLength) {
        // Показываем всё, если символов мало
        items.forEach(li => li.style.display = '');
        // Если была заглушка "нет областей", не трогаем
        return;
    }

    const lowered = query.toLowerCase();
    items.forEach(li => {
        // Имя области — это первый <span>
        const areaNameSpan = li.querySelector('span');
        const areaName = areaNameSpan ? areaNameSpan.textContent.toLowerCase() : '';
        li.style.display = areaName.includes(lowered) ? '' : 'none';
    });
}


/**
 * Добавляет обработчик клика на кнопку "Удалить профиль".
 * Отправляет запрос на сервер для удаления профиля.
 */
function deleteProfile() {
    const profileID = document.getElementById("profileSettingBlock").dataset.profileId;
    
    // Запрашиваем подтверждение перед удалением
    const confirmation = confirm("Вы уверены, что хотите удалить этот профиль? Это действие нельзя отменить.");
    if (!confirmation) return;

    // Запрашиваем подтверждение перед удалением
    const secondConfirmation = confirm("Удаление профиля приведет к удалению всех связанных с ним протоколов, включая историю уже написанных в профиле протоколов. Удалятся также все связанные с профилем ключевые слова и созданные в этом профиле типы и подтипы протоколов. Вы уверены, что хотите удалить профиль?");
    if (!secondConfirmation) return;

    // Отправляем данные на сервер
    sendRequest({
        url: `/profile_settings/delete_profile/${profileID}`,
        method: "DELETE",
    }).then(response => {
        if (response.status === "success") {
            window.location.reload(); // Перезагружаем страницу для обновления данных
        }
            console.log(response.message || "Profile deleted successfully.");
    }).catch(error => {
        console.error("Failed to delete profile:", error);
    });
}   


// Функция включающая видимость поля для ввода email пользователя с которым хотим поделиться профилем
function shareProfileButtonHandler() {
    const shareProfileBlock = document.getElementById("shareProfileEmailBlock");
    shareProfileBlock.style.display = "block";
    const shareProfileButton = shareProfileBlock.querySelector("#submitShareProfileButton");
    
    // Слушатель на кнопку "Поделиться"
    shareProfileButton.addEventListener("click", () => {
        const email = shareProfileBlock.querySelector("#shareEmailInput").value.trim();
        console.log(email);
        shareAllProfileProtocols(email);
    }, { once: true });
}


// Функция для того чтобы поделиться всеми протоколами профиля.
async function shareAllProfileProtocols(email) {
    const response = await sendRequest({
        url: `/profile_settings/share_profile`,
        method: "POST",
        data: { "email": email },
    });

    if (response.status === "success") {
        console.log(response.message || "Profile shared successfully.");
    }
}



// Функция для пересборки модальностей из базы данных
async function rebuildModalitiesFromDB() {
    const response = await sendRequest({
        url: `/profile_settings/rebuild_modalities_from_db`,
        method: "POST",
    });

    if (response.status === "success") {
        console.log(response.message || "Modalities rebuilt successfully.");
        window.location.reload(); // Перезагружаем страницу для обновления данных
    } else {
        console.error("Failed to rebuild modalities:", response.message);
    }
}