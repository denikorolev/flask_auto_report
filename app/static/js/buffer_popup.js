/**
 * buffer_popup.js
 * 
 * Слушатели для управления попапом буфера обмена.
 * Предполагается, что логика работы с буфером находится в sentence_buffer.js
 */

const bufferPopup = document.getElementById("bufferPopup");
const bufferList = bufferPopup.querySelector(".buffer-popup__list");

function bufferPopupListeners() {
    const closeBufferBtn = document.getElementById("closeBufferPopup");
    const clearBufferBtn = document.getElementById("clearBufferButton");
    

    // Закрыть попап
    closeBufferBtn?.addEventListener("click", function () {
        bufferPopup.style.display = "none";
        window.location.reload(); // Перезагрузить страницу при закрытии
    });

    // Очистить буфер
    clearBufferBtn?.addEventListener("click", function () {
        if (confirm("Вы уверены, что хотите очистить буфер?")) {
            clearBuffer();
            refreshBufferPopup(); // Обновить содержимое после очистки
        }
    });
}
    

    
/**
 * Функция для обновления содержимого попапа из буфера
 */
function refreshBufferPopup() {
    const buffer = getBuffer(); // Получаем буфер из sentence_buffer.js
    bufferList.innerHTML = ""; // Очищаем старый список

    if (buffer.length === 0) {
        bufferList.innerHTML = "<li>Буфер пуст</li>";
        return;
    }

    buffer.forEach((item, index) => {
        const li = document.createElement("li");
        li.classList.add("buffer-popup__item");
        li.setAttribute("data-buffer-index", index);
        li.innerHTML = `
            <div class="buffer-popup__content">
                <span class="buffer-popup__text buffer-popup__text--report-type">${item.report_type}</span>
                <span class="buffer-popup__text"><strong>${item.object_type === 'paragraph' ? 'Параграф' : 'Предложение'} (${item.object_type === 'sentence' ? item.sentence_type : item.object_id})</strong></span>
                <span class="buffer-popup__text">${item.object_text || 'Нет текста'}</span>
            </div>
            <div class="control-buttons">
                <button class="btn-icon buffer-popup__btn--remove" title="Удалить из буфера" data-index="${index}">❌</button>
                <button class="btn-icon buffer-popup__btn--insert" title="Вставить" data-index="${index}">📌</button>
            </div>
        `;
        bufferList.appendChild(li);
    });

    // Навешиваем слушатели на кнопки удаления
    bufferList.querySelectorAll(".buffer-popup__btn--remove").forEach(button => {
        button.addEventListener("click", function () {
            const indexToRemove = parseInt(this.getAttribute("data-index"));
            removeFromBuffer(indexToRemove);
            refreshBufferPopup(); // Обновляем после удаления
        });
    });

    // Навешиваем слушатели на кнопки вставки
    bufferList.querySelectorAll(".buffer-popup__btn--insert").forEach(button => {
        button.addEventListener("click", function () {
            const indexToInsert = parseInt(this.getAttribute("data-index"));
            // Вставляем элемент в редактор, функция будет на соответствующей странице (edit_report.js, edit_paragraph.js, edit_head_sentence.js)
            insertFromBuffer(indexToInsert);
        });
    });
}
