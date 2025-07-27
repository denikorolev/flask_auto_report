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

    // 2. Навешиваем слушатели на кнопки "✏️" и "🗑️" (пока просто console.log)
    document.querySelectorAll('.edit-category-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const id = btn.getAttribute('data-id');
            // TODO: открыть модалку/попап для редактирования
            console.log('Редактировать модальность', id);
        });
    });

    document.querySelectorAll('.delete-category-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const id = btn.getAttribute('data-id');
            // TODO: подтвердить удаление
            console.log('Удалить модальность', id);
        });
    });

    // 3. Выбираем первую модальность (если есть) и отображаем её области
    if (radios.length) {
        radios[0].checked = true;
        handleModalityChange(radios[0].value);
    }
}


// Обработка выбора модальности — отрисовка областей
function handleModalityChange(modalityId) {
    const tree = window.globalCategoriesTree || [];
    const modality = tree.find(m => String(m.id) === String(modalityId));
    const container = document.getElementById('areasList');
    container.innerHTML = '';

    if (modality && modality.children && modality.children.length) {
        modality.children.forEach(child => {
            const li = document.createElement('li');
            li.className = 'area-item';
            li.innerHTML = `
                <span>${child.name}</span>
                <button class="edit-area-btn" data-id="${child.id}" title="Редактировать область исследования">✏️</button>
                <button class="delete-area-btn" data-id="${child.id}" title="Удалить область исследования">🗑️</button>
                <button class="change-global-category-btn" data-id="${child.id}" title="Поменять глобальную категорию области исследования">💻</button>
            `;
            container.appendChild(li);
        });
    } else {
        const li = document.createElement('li');
        li.textContent = 'Нет областей для выбранной модальности';
        li.style.color = '#888';
        container.appendChild(li);
    }
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