// playground.js

document.addEventListener("DOMContentLoaded", function () {

    // Слушатель на кнопку "Перенести"
    document.getElementById("sentenceMigration").addEventListener("click", function() {
        handleMoveButtonClick();
    });
    // Слушатель на кнопку "Обработать предложения"
    document.getElementById("sentenceProcessing").addEventListener("click", function() {
        handleProcessButtonClick();
    });


});



function handleMoveButtonClick() {
    console.log("Button migrate clicked");
    sendRequest({
        url: "/playground_button_click", 
        data: {flag: "migrate"}
    }).then(response => {
        if (response.status === "success") {
            window.location.reload();
        }
    });
}

function handleProcessButtonClick() {
    console.log("Button process clicked");
    sendRequest({
        url: "/playground_button_click", 
        data: {flag: "sentence_structure"}
    }).then(response => {
        if (response.status === "success") {
            window.location.reload();
        }
    });
}