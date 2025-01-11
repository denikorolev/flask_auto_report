// profile_settings.js

document.getElementById("save-settings").addEventListener("click", () => {
    
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