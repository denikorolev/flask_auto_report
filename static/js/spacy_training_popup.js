// spacy_training_popup.js

// Это попап для дообучения spacy разделению предложений
// Он открывается при нажатии на кнопку "🧠 Учить" в отчете о добавленных предложениях.
function showTrainingPopup(sentenceText, onSubmit) {
    fetch("/working_with_reports/get_spacy_tokens", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken
        },
        body: JSON.stringify({ text: sentenceText })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status !== "success") {
            alert("Ошибка при получении токенов SpaCy: " + data.message);
            return;
        }

        const tokens = data.tokens;
        const popup = document.createElement("div");
        popup.className = "training-popup";

        const heading = document.createElement("h4");
        heading.textContent = "Укажите начало предложений:";

        const tokenList = document.createElement("ul");
        tokens.forEach((token, idx) => {
            const item = document.createElement("li");
            const checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            checkbox.dataset.index = idx;
            checkbox.checked = token.is_sent_start;

            item.appendChild(checkbox);
            item.append(" " + token.text);
            tokenList.appendChild(item);
        });

        const submitBtn = document.createElement("button");
        submitBtn.textContent = "Сохранить обучение";
        submitBtn.onclick = () => {
            const sent_starts = Array.from(tokenList.querySelectorAll("input")).map(cb => cb.checked);
            onSubmit({ text: sentenceText, sent_starts });
            document.body.removeChild(popup);
        };

        const cancelBtn = document.createElement("button");
        cancelBtn.textContent = "Закрыть";
        cancelBtn.style.marginLeft = "10px";
        cancelBtn.onclick = () => {
            document.body.removeChild(popup);
        };

        popup.append(heading, tokenList, submitBtn, cancelBtn);
        Object.assign(popup.style, {
            position: "fixed",
            top: "20%",
            left: "40%",
            background: "white",
            padding: "20px",
            border: "1px solid #ccc",
            zIndex: 1000,
            maxWidth: "600px",
            boxShadow: "0 2px 10px rgba(0,0,0,0.1)",
            fontFamily: "sans-serif"
        });

        document.body.appendChild(popup);
    })
    .catch(err => {
        console.error("Ошибка при запросе токенов:", err);
        alert("Ошибка при получении токенов SpaCy");
    });
}
