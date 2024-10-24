// admin.js

document.addEventListener("DOMContentLoaded", function(){
    userDeleteButtonClick();
    userEditButtonClick();

    paragraphDeleteButtonClick();
    paragraphEditButtonClick();

    profileDeleteButtonClick();
    profileEditButtonClick();
});


function userDeleteButtonClick() {
    document.querySelectorAll(".setup-users__btn--delete").forEach(button => {
        button.addEventListener("click", function() {
            let userId = this.dataset.userId;
            userId = parseInt(userId, 10);
            sendRequest({
                url: `/admin/delete_user/${userId}`,
                method: "DELETE"
            }).then(response => {
                if (response.status === "success") {
                    console.log(response.message);
                    location.reload(); 
                } 
            }).catch(error => {
                console.error("Error deleting user:");
            });
        });
    });
}

function userEditButtonClick() {
    document.querySelectorAll(".setup-users__btn--edit").forEach(button => {
        button.addEventListener("click", function() {
            const userId = this.previousElementSibling.dataset.userId; // Предполагаем, что предыдущий элемент — это кнопка "delete"
            const userName = this.closest(".setup-users__list").querySelector(".setup-users__item--name").innerText;
            const userRole = this.closest(".setup-users__list").querySelector(".setup-users__item--role").innerText;

            sendRequest({
                url: `/admin/edit_user/${userId}`,
                method: "PUT",
                data: { user_name: userName, user_role: userRole }
            }).then(response => {
                if (response.status === "success") {
                    location.reload(); 
                }
            }).catch(error => {
                console.error("Error editing user:");
            });
        });
    });
}


function paragraphDeleteButtonClick() {
    document.querySelectorAll(".setup-paragraphs__btn--delete").forEach(button => {
        button.addEventListener("click", function() {
            const paragraphId = this.dataset.paragraphId;
            sendRequest({
                url: `/admin/delete_paragraph/${paragraphId}`,
                method: "DELETE"
            }).then(response => {
                if (response.status === "success") {
                    console.log(response.message);
                    location.reload();  
                } 
            }).catch(error => {
                console.error("Error deleting paragraph:");
            });
        });
    });
}

function paragraphEditButtonClick() {
    document.querySelectorAll(".setup-paragraphs__btn--edit").forEach(button => {
        button.addEventListener("click", function() {
            const paragraphId = this.previousElementSibling.dataset.paragraphId;
            const paragraphText = this.closest(".setup-paragraphs__list").querySelector(".setup-paragraphs__item--text").innerText;
            const paragraphWeight = this.closest(".setup-paragraphs__list").querySelector(".setup-paragraphs__item--weight").innerText;

            sendRequest({
                url: `/admin/edit_paragraph/${paragraphId}`,
                method: "PUT",
                data: { paragraph: paragraphText, weight: paragraphWeight }
            }).then(response => {
                if (response.status === "success") {
                    location.reload();  // Перезагружаем страницу после редактирования
                }
            }).catch(error => {
                console.error("Error editing paragraph:", error);
            });
        });
    });
}


function profileDeleteButtonClick() {
    document.querySelectorAll(".setup-profiles__btn--delete").forEach(button => {
        button.addEventListener("click", function() {
            const profileId = this.dataset.profileId;
            sendRequest({
                url: `/admin/delete_profile/${profileId}`,
                method: "DELETE"
            }).then(response => {
                if (response.status === "success") {
                    console.log(response.message);
                    location.reload();  // Перезагружаем страницу для обновления списка профилей
                } 
            }).catch(error => {
                console.error("Error deleting profile:");
            });
        });
    });
}

function profileEditButtonClick() {
    document.querySelectorAll(".setup-profiles__btn--edit").forEach(button => {
        button.addEventListener("click", function() {
            const profileId = this.dataset.profileId;
            const profileName = this.closest(".setup-profiles__list").querySelector(".setup-profiles__item--name").innerText;

            sendRequest({
                url: `/admin/edit_profile/${profileId}`,
                method: "PUT",
                data: { profile_name: profileName }
            }).then(response => {
                if (response.status === "success") {
                    location.reload();  
                }
            }).catch(error => {
                console.error("Error editing profile:", error);
            });
        });
    });
}
