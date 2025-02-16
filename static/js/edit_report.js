// edit_report.js

document.addEventListener("DOMContentLoaded", function () {

    // Добавляю слушатели на все select для изменения типа предложения
    document.querySelectorAll("select[name='sentence_type']").forEach(select => {
        select.addEventListener("change", function(event) {
            sentenceTypeChanger(event.target);
        });
    });

    // Слушатель на кнопку "удалить предложение"
    document.querySelectorAll(".edit-sentence__btn--delete-sentence").forEach(button => {
        button.addEventListener("click", function() {
            deleteSentenceButton(this);
        });
    });

    // слушатель на кнопку изменения протокола
    document.getElementById("updateReportButton").addEventListener("click", function() {
        handleUpdateReportButtonClick();
    });

});


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
        button.textContent = `Развернуть (${button.dataset.sentencesCount})`;


        // Сбор данных для всех предложений в списке
        const changedForms = sentencesList.querySelectorAll(".edit-paragraph__form--sentence[data-changed='true']");
        const sentenceData = [];

        changedForms.forEach(form => {
            const formData = new FormData(form);
            const jsonData = Object.fromEntries(formData.entries());
            jsonData["sentence_id"] = form.dataset.sentenceId;
            jsonData["sentence_type"] = form.querySelector("select[name='sentence_type']").value;
            jsonData["paragraph_id"] = form.dataset.sentenceParagraphId;
            

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
    newSentenceForm.setAttribute("data-changed", "true")
    newSentenceForm.setAttribute("data-sentence-paragraph-id", paragraphId)

    newSentenceForm.innerHTML = `
        <div class="wrapper__card">
            <div class="flex edit-sentence__info-box">
                <div class="edit-sentence__wrapper edit-sentence__wrapper--short">
                        <label class="label edit-sentence__label" for="sentence_index">Индекс:</label>
                    <input class="input edit-sentence__input" type="text" name="sentence_index" value="${newSentenceIndex}">
                </div>
                <div class="edit-sentence__wrapper edit-sentence__wrapper--short">
                        <label class="label edit-sentence__label" for="sentence_weight">Вес:</label>
                    <input class="input edit-sentence__input" type="text" name="sentence_weight" value="1">
                </div>
                <div class="edit-sentence__wrapper edit-sentence__wrapper--short">
                    <label class="label edit-sentence__label" for="sentence_type">Тип:</label>
                    <div class="select-wrapper">
                        <select class="select" name="sentence_type">
                            <option value="head">head</option>
                            <option value="body" selected>body</option>
                            <option value="tail">tail</option>
                        </select>
                    </div>
                </div>
                <div class="edit-sentence__wrapper">
                        <label class="label edit-sentence__label" for="sentence_comment">Комментарий:</label>
                    <input class="input edit-sentence__input" type="text" name="sentence_comment" value="">
                </div>
                <button class="btn report__btn edit-sentence__btn edit-sentence__btn--delete-sentence" type="button">Удалить</button>
            </div>
            <div class="edit-sentence__wrapper">
                <label class="label edit-sentence__label edit-sentence__label--text" for="sentence_sentence">Текст предложения:</label>
                <input class="input edit-sentence__input edit-sentence__input-text" type="text" name="sentence_sentence" value="New sentence">
            </div>
        </div>
    `;

    newSentenceLi.appendChild(newSentenceForm);
    sentencesList.appendChild(newSentenceLi);

    newSentenceForm.querySelector("select[name='sentence_type']").addEventListener("change", function(event) {
        sentenceTypeChanger(event.target);
    });

};
    


// Delete sentence deleteSentenceButton()
function deleteSentenceButton(button) {
    const sentenceId = button.closest("form").dataset.sentenceId;

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


function sentenceTypeChanger(sentenceTypeSelect) {
    console.log("sentenceTypeChanger", sentenceTypeSelect.value);
    const sentenceForm = sentenceTypeSelect.closest("form");
    const sentenceId = sentenceForm.dataset.sentenceId;
    const sentenceType = sentenceTypeSelect.value;
    const sentenceParagraphId = sentenceForm.dataset.sentenceParagraphId;
    const sentenceIndex = sentenceForm.dataset.sentenceIndex;

    if (sentenceId === "new") {
        console.log("this is new sentence and you try to change it's type");
        return; // Выход, если попытка установить тип главного 
        // предложения у нового предложения так как оно еще не сохранено
    } 

    sendRequest({
        url: `/editing_report/change_sentence_type`,
        method: "POST",
        data: {sentence_id: sentenceId,
                paragraph_id: sentenceParagraphId,
                sentence_index: sentenceIndex,
                sentence_type: sentenceType}
    }).then(response => {
        if (response.status === "success") {
            window.location.reload();
        } 
    });

}



