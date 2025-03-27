// profile_settings.js

document.addEventListener("DOMContentLoaded", function(){
    
    profileSettingsSave();

    profileGlobalSettingsSave();

    deleteProfile();

    initializeChangeListeners(); // Слушатели изменения для элементов чтобы отправлять только измененные данные

    isMainChecker(); // Проверка на наличие ошибок, связанных с главными предложениями в протоколах этого профиля

    // Слушатель на кнопку "Поделиться профилем"
    document.getElementById("shareProfileButton").addEventListener("click", () => {
        shareProfileButtonHandler();
        }
    );
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
            is_default: profileSettingBlock.querySelector("#isDefauleProfile").checked,
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
            if (response.status === "success") {   
                window.location.reload();
                }
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
            csrfToken: csrfToken,
        }).then(response => {
            if (response.status === "success"){
                window.location.href = "/profile_settings/choosing_profile";
                console.log(response.message || "Profile deleted successfully.");
            }
        }).catch(error => {
            console.error("Failed to delete profile:", error);
        });
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




// Проверка на наличие ошибок, связанных с главными предложениями в протоколах этого профиля
function isMainChecker(){
    document.getElementById("startCheckersButton").addEventListener("click", () => {
        
        const blockForMessage = document.getElementById("reportCheckMessageBlock");
        const title = document.getElementById("reportCheckMessageTitle");
        const messageList = document.getElementById("reportCheckMessageList");
        
        title.textContent = "Проверка на уникальность индексов параграфов и главных предложений";
        sendRequest({
            url: "/profile_settings/run_checker",
            data: { checker: "main_sentences" },
        }).then(response => {
            if (response.status === "success") {
                messageList.innerHTML = ""; // Очищаем старые ошибки перед обновлением

                if (response.errors.length === 0) {
                    // Если ошибок нет — показываем сообщение об успехе
                    messageList.innerHTML = `<li class="report-check__item-success">✅ Не выявлено ни одной ошибки связанной с неуникальными индексами параграфов и главных предложений</li>`;
                } else {
                    // Если есть ошибки — добавляем их в список
                    response.errors.forEach(error => {
                        const errorItem = document.createElement("li");
                        errorItem.classList.add("report-check__item-error");
                        errorItem.textContent = `🔴 В протоколе ${error.report} - ошибка =${error.error}`;
                        messageList.appendChild(errorItem);
                    });
                }

                // Показываем блок с сообщением
                blockForMessage.style.display = "block";
            }
        });
    });
}


function fixIndices () {
    document.getElementById("fixIndices").addEventListener("click", () => {
        sendRequest({
            url: "/profile_settings/fix_indices",
        }).then(response => {
            if (response.status === "success") {
                console.log(response.message || "Indices fixed successfully.");
            }
        }).catch(error => {
            console.error("Failed to fix indices:", error);
        });
    });
}