// edit_report.js




// Обработчик для кнопки update report работает через onclick
function handleUpdateReportButtonClick() {
    const reportId = document.querySelector(".edit-report").getAttribute("data-report-id");
    const form = document.getElementById("edit-report-form");
    const formData = new FormData(form);
    formData.append("report_id", reportId);
        sendRequest({
            url: `/editing_report/update_report`,
            method: "PUT",
            data: formData
        }).then (response => {
            console.log("all right", response.message)
        });
};


// Обработчик для кнопки new_paragraph работает через onclick
function newParagraphCreate(){
    const reportId = document.querySelector(".edit-report").getAttribute("data-report-id");
    sendRequest({
        url: `/editing_report/new_paragraph`,
        data: {"report_id": reportId},
        // csrfToken: csrfToken
    }).then(response => {
        if (response.status === "success") {
            window.location.reload();
        } else {
            alert(response.message);
        }
    });
};


// Обработчик для кнопки edit-paragraph__button--edit работает через onclick
function handleEditParagraphButtonClick(button){
    const paragraphId = button.getAttribute("data-paragraph-id");
    const form = button.closest("form");
    const formData = new FormData(form);
    formData.append("paragraph_id", paragraphId);
    
    sendRequest({
        url: `/editing_report/edit_paragraph`,
        data: formData
    });
};


// Обработчик для кнопки edit-paragraph__button--delete работает через onclick
function deleteParagraph(button){
    const paragraphId = button.getAttribute("data-paragraph-id") 
        sendRequest({
            url: `/editing_report/delete_paragraph`,
            method: "DELETE",
            data: { paragraph_id: paragraphId },
            // csrfToken: csrfToken
        }).then(response => {
            window.location.reload();
        }).catch(error => {
            console.log("Ошибка удаления параграфа.");
        });
};
       

// Обработчик для кнопки edit-paragraph__button--expand работает через onclick
function expandSentencesOfParagraph(button){

    const paragraphId = button.getAttribute("data-paragraph-id");
    const sentencesList = document.getElementById(`sentences-${paragraphId}`);

    if (button.getAttribute("data-state") === "collapsed") {
        sentencesList.style.display = "block";
        button.setAttribute("data-state", "save");
        button.textContent = "Сохранить и свернуть";

        // Вешаем обработчики на все input внутри предложений
        sentencesList.querySelectorAll(".edit-paragraph__form--sentence input").forEach(input => {
            input.addEventListener("change", function () {
                this.closest("form").setAttribute("data-changed", "true"); // Помечаем форму как изменённую
            });
        });

    } else if (button.getAttribute("data-state") === "save") {
        button.setAttribute("data-state", "collapsed"); 
        sentencesList.style.display = "none";
        button.textContent = "Развернуть"


        // Сбор данных для всех предложений в списке
        const changedForms = sentencesList.querySelectorAll(".edit-paragraph__form--sentence[data-changed='true']");
        const sentenceData = [];

        changedForms.forEach(form => {
            const formData = new FormData(form);
            const jsonData = Object.fromEntries(formData.entries());
            jsonData["sentence_id"] = form.getAttribute("data-sentence-id");
            jsonData["is_head"] = form.querySelector("input[name='is_head']").checked;
            

            sentenceData.push(jsonData);
        });

        if (sentenceData.length === 0) {
            console.log("Нет изменений, запрос не отправляем.");
            return; // Выход, если изменений нет
        }

        // Отправляем данные предложений на сервер
        sendRequest({
            url: "/editing_report/edit_sentences_bulk",
            data: sentenceData,
        }).then(response => {
            if (response.success) {
                window.location.reload();
            };
        });
    };
};


// Добавление нового предложения в параграф
function newSentenceCreate(button){

    const paragraphId = button.getAttribute("data-paragraph-id");
    const sentencesList = document.getElementById(`sentences-${paragraphId}`);
        
    const indexInputs = sentencesList.querySelectorAll("input[name='sentence_index']");
    maxIndex = findMaxIndex(indexInputs)
    

    // Назначаем новый индекс
    const newSentenceIndex = maxIndex + 1;

    // Создаем новый элемент предложения
    const newSentenceLi = document.createElement("li");
    const newSentenceForm = document.createElement("form");
    newSentenceForm.classList.add("flex","edit-paragraph__form--sentence");
    newSentenceForm.setAttribute("data-sentence-id", "new")

    newSentenceForm.innerHTML = `
        <input type="hidden" name="sentence_id" value="new">
        <input type="hidden" name="add_sentence_paragraph" value="${paragraphId}">
        <input class="input input--short edit-paragraph__input" type="text" name="sentence_index" value="${newSentenceIndex}">
        <input class="input input--short edit-paragraph__input" type="text" name="sentence_weight" value="1">
        <input class="input--checkbox" type="checkbox" name="is_head">
        <input class="input input--short edit-paragraph__input" type="text" name="sentence_comment" value="">
        <input class="input input--wide edit-paragraph__input" type="text" name="sentence_sentence" value="New sentence">
        <button class="btn report__btn edit-paragraph__btn--delete-sentence" type="button" data-sentence-id="new" onclick="deleteSentenceButton(this)">Delete Sentence</button>
    `;

    newSentenceLi.appendChild(newSentenceForm);
    sentencesList.appendChild(newSentenceLi);
};
    


// Delete sentence deleteSentenceButton()
function deleteSentenceButton(button) {
    const sentenceId = button.getAttribute("data-sentence-id");

    if(sentenceId === "new") {
        button.closest("li").remove();
    } else {
        sendRequest({
            url: `/editing_report/delete_sentence`,
            method: "DELETE",
            data: {sentence_id: sentenceId},
        }).then(response => {
            if (response.status === "success") {
                button.closest("li").remove();
            } 
        });
    };
};
   

// Обработчик для кнопки edit-paragraph__btn--main-sentence работает через onclick
function makeSentenceMainButton(button) {
    const sentenceId = button.dataset.sentenceId;
    const sentenceParagraphId = button.dataset.sentenceParagraphId;
    const sentenceIndex = button.dataset.sentenceIndex;

    console.log("sentenceId", sentenceId);
    console.log("sentenceParagraphId", sentenceParagraphId);
    console.log("sentenceIndex", sentenceIndex);

    sendRequest({
        url: `/editing_report/make_sentence_main`,
        method: "POST",
        data: {sentence_id: sentenceId,
                paragraph_id: sentenceParagraphId,
                sentence_index: sentenceIndex
        },
    }).then(response => {
        if (response.status === "success") {
            window.location.reload();
        } 
    });
};

// Обработчик для кнопки btnCheckIsHead работает через onclick 
// отправляет запрос на сервер для проверки на наличие лишних главных предложений
function reportCheckIsHeadSentensesUnic(button) {
    const reportId = button.dataset.reportId;
    const blockForMessage = document.getElementById("reportCheckIsHead");
    const messageList = document.getElementById("reportCheckIsHeadList");

    sendRequest({
        url: "/editing_report/check_report_for_excess_ishead",
        data: { report_id: reportId },
    }).then(response => {
        if (response.status === "success") {
            messageList.innerHTML = ""; // Очищаем старые ошибки перед обновлением

            if (response.errors.length === 0) {
                // Если ошибок нет — показываем сообщение об успехе
                messageList.innerHTML = `<li class="report-check__item-success">✅ Все предложения корректны!</li>`;
            } else {
                // Если есть ошибки — добавляем их в список
                response.errors.forEach(error => {
                    const errorItem = document.createElement("li");
                    errorItem.classList.add("report-check__item-error");
                    errorItem.textContent = `🔴 Параграф ${error.paragraph_index}  ${error.paragraph}, содержит группу предложений с индексом=${error.index} со следующими ошибками:  ${error.issue} (Лишних главных предложений: ${error.extra_main_count})`;
                    messageList.appendChild(errorItem);
                });
            }

            // Показываем блок с сообщением
            blockForMessage.style.display = "block";
        }
    });
}
