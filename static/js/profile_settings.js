// profile_settings.js

document.addEventListener("DOMContentLoaded", function(){
    
    profileSettingsSave();

    profileGlobalSettingsSave();

    deleteProfile();

    initializeChangeListeners(); // Слушатели изменения для элементов чтобы отправлять только измененные данные

});


/**
 * Добавляет обработчик клика на кнопку "Сохранить настройки профиля",
 * собирает данные профиля и отправляет их на сервер.Сохраняет глобальные настройки - имя профиля и описание.
 * Потом уберу его отсюда в настройки юзера
 */
function profileGlobalSettingsSave() {
   
    document.getElementById("saveSettingProfile").addEventListener("click", function() {
        const profileSettingBlock = document.getElementById("profileSettingBlock");
        
        const settingsData = {
            profile_id: profileSettingBlock.dataset.profileId,
            profile_name: profileSettingBlock.querySelector("#profileName").value,
            description: profileSettingBlock.querySelector("#profileDescription").value,
        };

        // Отправляем данные на сервер
        sendRequest({
            url: "/profile_settings/update_profile_settings",
            method: "POST",
            csrfToken: csrfToken,
            data: settingsData
        }).then(response => {
            console.log(response.message || "Settings updated successfully.");
        }).catch(error => {
            console.error("Failed to update settings:", error);
        });
    });
}


/**
 * Добавляет обработчик клика на кнопку "Сохранить настройки", 
 * проверяет наличие флага изменения для каждого элемента формы,
 * собирает данные настроек и отправляет их на сервер.
 * После успешного сохранения удаляет флаг изменения и убирает класс изменения.
 */
function profileSettingsSave() {
    
    document.getElementById("saveSettings").addEventListener("click", () => {
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
            inputs.forEach(input => delete input.dataset.changed);
            inputs.forEach(input => {
                const parentLi = input.closest(".settings-block__item");
                if (parentLi) {
                        parentLi.classList.remove("settings-block__item--changed");
                }
            });
        }).catch(error => {
            console.error("Failed to update settings:", error);
        });
    });
}

/** Инициализирует слушателей событий изменения для элементов формы настроек 
 * и устанавливает флаг для измененных элементов.
 * При изменении элемента добавляет класс изменения для родительского элемента <li>.
*/
function initializeChangeListeners() {
    const settingsBlock = document.getElementById("settings-block");
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


/**
 * Добавляет обработчик клика на кнопку "Удалить профиль".
 * Отправляет запрос на сервер для удаления профиля.
 */
function deleteProfile() {
    
    document.getElementById("deleteProfile").addEventListener("click", () => {
        const profileID = document.getElementById("profileSettingBlock").dataset.profileId;

        // Отправляем данные на сервер
        sendRequest({
            url: `/profile_settings/delete_profile/${profileID}`,
            method: "DELETE",
            csrfToken: csrfToken,
        }).then(response => {
            location.reload();
        }).catch(error => {
            console.error("Failed to delete profile:", error);
        });
    });
}   