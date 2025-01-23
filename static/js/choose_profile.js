// choose_profile.js

document.addEventListener("DOMContentLoaded", function(){
    
    document.getElementById("profileCreationButton").addEventListener("click", profileCreationButtonHandler);

    document.getElementById("saveProfileButton").addEventListener("click", saveProfileButtonHandler);
});

function profileCreationButtonHandler() {
    const profileCreationBlock = document.getElementById("profileCreationForm");
    const profileCreationButton = document.getElementById("profileCreationButton");

    if (profileCreationBlock.style.display === "none") {
        profileCreationBlock.style.display = "block";
        profileCreationButton.textContent = "Отмена";
    } else {
        profileCreationBlock.style.display = "none";
        profileCreationButton.textContent = "Создать профиль";
    }
}

function saveProfileButtonHandler() {
    const profileCreationBlock = document.getElementById("profileCreationForm");
    
    const profileData = {
        profile_name: profileCreationBlock.querySelector("#profileName").value,
        description: profileCreationBlock.querySelector("#profileDescription").value,
        is_default: profileCreationBlock.querySelector("#isDefault").checked
    };

    sendRequest({
        url: "/profile_settings/create_profile",
        method: "POST",
        csrfToken: csrfToken,
        data: profileData
    }).then(response => {
        console.log(response.message || "Profile created successfully.");
        window.location.reload();
    }).catch(error => {
        console.error("Failed to create profile:", error);
    });
}