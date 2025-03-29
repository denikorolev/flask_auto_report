// openai_api.js

document.addEventListener("DOMContentLoaded", function(){

    

    document.getElementById("startOpenAIChat").addEventListener("click", function(event){
        startOpenAIChat();
    });

});

function startOpenAIChat(){
    const AIQuestionBlock = document.getElementById("AIQuestionBlock");
    const AIAnswerText = document.getElementById("AIAnswerText");

    AIAnswerText.innerHTML = ""; // Очистка предыдущих ответов

    AIQuestionBlock.style.display = "block";

    document.getElementById("sentRequestToAI").addEventListener("click", function(event){
        sendQuestionToAI();
        });

    sendQuestionToAI(newConversation = true);

}




function sendQuestionToAI(newConversation = false) {
   
    const AIQuestionBlock = document.getElementById("AIQuestionBlock");
    const AIAnswerBlock = document.getElementById("AIAnswerBlock");
    const AIAnswerText = document.getElementById("AIAnswerText");
    const userName = document.getElementById("userNameHeader").getAttribute("data-user-name") || "Пользователь";

    let userInputAIRequest = AIQuestionBlock.querySelector("#AIQuestionInput").value;

    if (newConversation){
        userInputAIRequest = "Привет! Проверка связи.";
    }

    const jsonData = {
        text: userInputAIRequest,
        new_conversation: newConversation
    };

    if ((!jsonData.text || jsonData.text.trim() === "") && !newConversation) {
        const errorMessage = document.createElement("p");
        errorMessage.classList.add("ai-conversation__text");
        errorMessage.textContent = "Radiologary: Поле с вопросом не должно быть пустым.";
        AIAnswerText.appendChild(errorMessage);
        AIAnswerBlock.style.display = "block";
        return;
    }

    // ➕ Добавляем вопрос в интерфейс
    const questionEl = document.createElement("p");
    questionEl.classList.add("ai-conversation__text");
    questionEl.textContent = `${userName}: ${userInputAIRequest}`;
    AIAnswerText.appendChild(questionEl);

    // Очищаем поле ввода
    AIQuestionBlock.querySelector("#AIQuestionInput").value = "";

    // Показываем блок ответов
    AIAnswerBlock.style.display = "block";

    // Отправка запроса
    sendRequest({
        url: "/openai_api/generate_general",
        data: jsonData
    })
    .then((response) => {
        const replyEl = document.createElement("p");
        replyEl.classList.add("ai-conversation__text");

        if (response.status === "success") {
            replyEl.textContent = `ИИ: ${response.data}`;
        } else {
            replyEl.textContent = "Произошла ошибка при получении ответа.";
        }

        AIAnswerText.appendChild(replyEl);
    })
    .catch((error) => {
        const errorEl = document.createElement("p");
        errorEl.classList.add("ai-conversation__text");
        errorEl.textContent = "Ошибка при запросе к ИИ.";
        AIAnswerText.appendChild(errorEl);
        console.error("Ошибка при запросе к ИИ:", error);
    });
}


