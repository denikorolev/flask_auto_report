// edit_report.js

document.addEventListener("DOMContentLoaded", function() {
    const reportId = document.querySelector(".container").getAttribute("data-report-id");

    // Обработка кнопки Expand/Save
    const toggleButtons = document.querySelectorAll(".toggle-sentences");
    toggleButtons.forEach(button => {
        button.addEventListener("click", function() {
            const paragraphId = this.getAttribute("data-paragraph-id");
            const sentenceList = document.getElementById(`sentences-${paragraphId}`);

            // Логика кнопки Expand/Save
            if (this.textContent.includes("Expand")) {
                sentenceList.style.display = "block";
                this.textContent = "Save";
            } else if (this.textContent.includes("Save")) {
                this.textContent = `Expand (${sentenceList.children.length - 1})`; // Обновляем текст обратно на Expand
                sentenceList.style.display = "none";

                // Сбор данных для всех предложений в списке
                const sentenceForms = sentenceList.querySelectorAll(".edit-sentence-form");
                const sentenceData = [];

                sentenceForms.forEach(form => {
                    const formData = new FormData(form);
                    const jsonData = Object.fromEntries(formData.entries());
                    sentenceData.push(jsonData);
                });

                // Отправляем данные предложений на сервер
                sendRequest({
                    url: "/editing_report/edit_sentences_bulk",
                    data: { sentences: sentenceData }
                }).then(response => {
                    if (response.success) {
                        window.location.reload();
                    } else {
                        alert(response.message);
                    }
                }).catch(() => {
                    alert("Failed to save sentences.");
                });
            }
        });
    });

    // Добавление нового предложения без отправки на сервер
    document.querySelectorAll(".add-sentence-form").forEach(form => {
        form.addEventListener("submit", function(event) {
            event.preventDefault();

            const paragraphId = form.querySelector('input[name="add_sentence_paragraph"]').value;
            const sentenceList = document.getElementById(`sentences-${paragraphId}`);

            // Находим максимальный индекс среди предложений
            let maxIndex = 0;
            sentenceList.querySelectorAll("input[name='sentence_index']").forEach(input => {
                const index = parseInt(input.value, 10);
                if (index > maxIndex) {
                    maxIndex = index;
                }
            });

            // Назначаем новый индекс
            const newSentenceIndex = maxIndex + 1;

            // Создаем новый элемент предложения
            const newSentenceLi = document.createElement("li");
            const newSentenceForm = document.createElement("form");
            newSentenceForm.classList.add("edit-sentence-form");

            newSentenceForm.innerHTML = `
                <input type="hidden" name="sentence_id" value="new">
                <input type="hidden" name="add_sentence_paragraph" value="${paragraphId}">
                <input class="report_input__item" type="text" name="sentence_sentence" value="New sentence">
                <input class="report_input__item" type="text" name="sentence_index" value="${newSentenceIndex}">
                <input class="report_input__item" type="text" name="sentence_weight" value="1">
                <input class="report_input__item" type="text" name="sentence_comment" value="">
                <button class="btn report__btn delete-sentence-btn" type="button" data-sentence-id="new">Delete Sentence</button>
            `;

            newSentenceLi.appendChild(newSentenceForm);
            sentenceList.appendChild(newSentenceLi);
            sentenceList.style.display = "block"; // Открываем список предложений, если он был скрыт

            // Добавляем обработчик для удаления нового предложения
            newSentenceForm.querySelector(".delete-sentence-btn").addEventListener("click", function() {
            newSentenceLi.remove();  // Удаляем элемент из DOM
        });
        });
    });

    // Update report
    document.getElementById("update-report-btn").addEventListener("click", function(event) {
        event.preventDefault();
        const form = document.getElementById("edit-report-form");
        const formData = new FormData(form);
        const jsonData = Object.fromEntries(formData.entries());
        jsonData.report_id = reportId;

        sendRequest({
            url: `/editing_report/update_report`,
            data:jsonData
        }).then(response => {
            if (response.status === "success") {
                toastr.success(response.message);
            } else {
                alert(response.message);
            }
        });
    });

    // Edit paragraph
    document.querySelectorAll(".edit-paragraph-form").forEach(form => {
        form.addEventListener("submit", function(event) {
            event.preventDefault();
            const formData = new FormData(this);
            const jsonData = Object.fromEntries(formData.entries());
            jsonData.paragraph_visible = form.querySelector('input[name="paragraph_visible"]').checked;
            jsonData.title_paragraph = form.querySelector('input[name="title_paragraph"]').checked;
            jsonData.bold_paragraph = form.querySelector('input[name="bold_paragraph"]').checked;
            // jsonData.paragraph_type_id = form.querySelector('select[name="paragraph_type"]').value;
            
            sendRequest({
                url: `/editing_report/edit_paragraph`,
                data: jsonData
            });
        });
    });

    // New paragraph
    document.querySelectorAll(".new-paragraph-form").forEach(form => {
        form.addEventListener("submit", function(event) {
            event.preventDefault();
            const formData = new FormData(this);
            const jsonData = Object.fromEntries(formData.entries());
            jsonData.report_id = reportId;

            sendRequest({
                url: `/editing_report/new_paragraph`,
                data: jsonData
            }).then(response => {
                if (response.status === "success") {
                    window.location.reload();
                } else {
                    alert(response.message);
                }
            });
        });
    });

    // Delete sentence
    document.querySelectorAll(".delete-sentence-btn").forEach(button => {
        button.addEventListener("click", function() {
            const sentenceId = this.getAttribute("data-sentence-id");
    
            sendRequest({
                url: `/editing_report/delete_sentence`,
                data: {
                    sentence_id: sentenceId
                }
            }).then(response => {
                if (response.status === "success") {
                    toastr.success(response.message);
                    this.closest("li").remove();
                } else {
                    alert(response.message);
                }
        });
    });

    // Delete paragraph
    document.querySelectorAll(".delete-paragraph-btn").forEach(button => {
        button.addEventListener("click", function() {
            const paragraphId = this.getAttribute("data-paragraph-id");
            sendRequest({
                url: `/editing_report/delete_paragraph`,
                data: {
                    paragraph_id: paragraphId
                }
            }).then(response => {
                if (response.status === "success") {
                    window.location.reload();
                } else {
                    alert(response.message);
                }
            });
        });
    });
    });
    
});

