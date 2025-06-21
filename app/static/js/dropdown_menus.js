// dropdown_menus.js
// Логика для выпадающих меню header в base.html

document.addEventListener("DOMContentLoaded", function(){
    
    const changeProfileBlock = document.getElementById("changeProfileBlock");
    const chooseProfilePopup = document.getElementById("chooseProfilePopup");

    // Слушатель для клика по блоку смены профиля
    if (changeProfileBlock) {
        changeProfileBlock.addEventListener("click", function(event) {
            event.stopPropagation(); // Останавливаем всплытие события
            showElement(chooseProfilePopup);
        });
    }

    // Слушатель для крестика закрытия попапа смены профиля
    const closeChooseProfilePopup = document.getElementById("closeChooseProfilePopup");
    if (closeChooseProfilePopup) {
        closeChooseProfilePopup.addEventListener("click", function(event) {
            event.stopPropagation(); // Останавливаем всплытие события
            hideElement(chooseProfilePopup);
        });
    }

});









