/**
 * buffer_popup.js
 * 
 * Слушатели для управления попапом буфера обмена.
 * Предполагается, что логика работы с буфером находится в sentence_buffer.js
 */

document.addEventListener("DOMContentLoaded", function () {
    const bufferPopup = document.getElementById("bufferPopup");
    const openBufferBtn = document.getElementById("openBufferPopupButton");
    const closeBufferBtn = document.getElementById("closeBufferPopup");
    const clearBufferBtn = document.getElementById("clearBufferButton");
    const insertFromBufferBtn = document.getElementById("insertFromBufferButton");
    const bufferList = bufferPopup.querySelector(".buffer-popup__list");

    // Открыть попап
    openBufferBtn?.addEventListener("click", function () {
        refreshBufferPopup(); // Перед открытием — обновить содержимое
        bufferPopup.style.display = "block";
    });

    // Закрыть попап
    closeBufferBtn?.addEventListener("click", function () {
        bufferPopup.style.display = "none";
    });

    // Очистить буфер
    clearBufferBtn?.addEventListener("click", function () {
        if (confirm("Вы уверены, что хотите очистить буфер?")) {
            clearBuffer();
            refreshBufferPopup(); // Обновить содержимое после очистки
        }
    });

    


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
                <span><strong>${item.object_type === 'paragraph' ? 'Параграф' : 'Предложение'} (${item.object_type === 'sentence' ? item.sentence_type : item.object_id})</strong></span> — 
                <span>${item.object_text || 'Нет текста'}</span>
                <button class="btn btn-icon buffer-popup__btn--remove" title="Удалить из буфера" data-index="${index}">❌</button>
                <button class="btn btn-icon buffer-popup__btn--insert" title="Вставить" data-index="${index}">📌</button>
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
        bufferList.querySelectorAll(".buffer-popup__btn--insert").forEach(button => {
            button.addEventListener("click", function () {
                const indexToInsert = parseInt(this.getAttribute("data-index"));
                // Вставляем элемент в редактор, функция будет на соответствующей странице (edit_report.js, edit_paragraph.js, edit_head_sentence.js)
                insertFromBuffer(indexToInsert);
            });
        });
    }
});