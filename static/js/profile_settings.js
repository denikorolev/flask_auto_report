// profile_settings.js

document.addEventListener("DOMContentLoaded", function(){
    
    profileSettingsSave();

    profileGlobalSettingsSave();

    deleteProfile();

});


/**
 * Добавляет обработчик клика на кнопку "Сохранить настройки профиля",
 * собирает данные профиля и отправляет их на сервер.
 *
 * Шаги:
 * 1. Слушает клик по кнопке с ID "saveSettingProfile".
 * 2. Собирает данные профиля из блока с ID "profileSettingBlock":
 *    - ID профиля (из атрибута data-profile-id),
 *    - Имя профиля (значение поля #profileName),
 *    - Описание профиля (значение поля #profileDescription).
 * 3. Отправляет данные на сервер через `sendRequest`:
 *    - URL: "/profile_settings/update_profile_settings".
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
 * собирает данные профиля и отправляет их на сервер.
 *
 * Шаги:
 * 1. Слушает клик по кнопке с ID "saveSettings".
 * 2. Собирает данные настроек (включение Word Reports и выбранная тема).
 * 3. Отправляет данные на сервер с помощью `sendRequest`.
 * 4. Обрабатывает ответ: выводит сообщение об успехе или ошибке.
 */
function profileSettingsSave() {
    
    document.getElementById("saveSettings").addEventListener("click", () => {
       
        const settingsBlock = document.getElementById("settings-block");
        // Собираем данные
        const settingsData = {
            USE_WORD_REPORTS: settingsBlock.querySelector("#use_word_reports").checked,
            THEME: settingsBlock.querySelector("#theme").value,
        };

        // Отправляем данные на сервер
        sendRequest({
            url: "/profile_settings/update_settings",
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