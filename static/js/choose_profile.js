// choose_profile.js

document.addEventListener("DOMContentLoaded", function(){
    
    document.getElementById("profileCreationButton").addEventListener("click", profileCreationButtonHandler);

    document.getElementById("saveProfileButton").addEventListener("click", saveProfileButtonHandler);

    document.getElementById("changeDefaultProfileButton").addEventListener("click", changeDefaultProfileButtonHandler);

    document.getElementById("saveDefaultProfileButton").addEventListener("click", saveDefaultProfileButtonHandler);

});


function profileCreationButtonHandler() {
    const profileCreationBlock = document.getElementById("profileCreationForm");
    const profileCreationButton = document.getElementById("profileCreationButton");
    const changeDefaultProfileButton = document.getElementById("changeDefaultProfileButton");

    if (profileCreationBlock.style.display === "none") {
        profileCreationBlock.style.display = "block";
        profileCreationButton.textContent = "Отмена";
        changeDefaultProfileButton.style.display = "none";

    } else {
        profileCreationBlock.style.display = "none";
        profileCreationButton.textContent = "Создать профиль";
        changeDefaultProfileButton.style.display = "block";
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

function changeDefaultProfileButtonHandler() {
    const makeProfileDefaultBlock = document.getElementById("makeProfileDefaultBlock");
    const changeDefaultProfileButton = document.getElementById("changeDefaultProfileButton");
    const profileCreationButton = document.getElementById("profileCreationButton");

    if (makeProfileDefaultBlock.style.display === "none") {
        makeProfileDefaultBlock.style.display = "block";
        changeDefaultProfileButton.textContent = "Отмена";
        profileCreationButton.style.display = "none";
        
    } else {
        makeProfileDefaultBlock.style.display = "none";
        changeDefaultProfileButton.textContent = "Изменить профиль по умолчанию";
        profileCreationButton.style.display = "block";
        
    }
}


function saveDefaultProfileButtonHandler() {
    const makeProfileDefaultBlock = document.getElementById("makeProfileDefaultBlock");
    const selectedRadio = makeProfileDefaultBlock.querySelector("input.make-profile-default__radio:checked");

    if (!selectedRadio) {
        alert("Выберите профиль по умолчанию перед сохранением.");
        return;
    }

    const profileID = selectedRadio.dataset.profileId;
    console.log("Selected profile ID:", profileID);

    sendRequest({
        url: `/profile_settings/set_default_profile/${profileID}`,
        method: "POST",
        csrfToken: csrfToken
    }).then(response => {
        window.location.reload();
    }).catch(error => {
        console.error("Failed to change default profile:", error);
    });
}