/**
 * Отображает всплывающее окно с предложениями для замены.
 * 
 * Функция создает и отображает всплывающее окно (popup) с предложениями для выбора. 
 * Пользователь может отфильтровать список предложений и выбрать нужное, после чего вызывается 
 * переданная callback-функция с выбранным элементом.
 * 
 * @param {number} x - Координата X для отображения окна (в пикселях).
 * @param {number} y - Координата Y для отображения окна (в пикселях).
 * @param {Array} sentenceList - Список предложений для выбора, где каждый элемент 
 * является объектом с текстом предложения (например, { sentence: "Текст предложения" }).
 * @param {Function} onSelect - Callback-функция, которая вызывается при выборе предложения. 
 * В функцию передается объект выбранного предложения.
 * 
 * @requires popup - Глобальный элемент, отвечающий за отображение всплывающего окна.
 * @requires popupList - Глобальный элемент списка внутри popup.
 * @requires hidePopupSentences - Глобальная функция для скрытия popup.
 */
function showPopupSentences(x, y, sentenceList, onSelect) {
    popupList.innerHTML = ''; // Очищаем старые предложения

    // Создаем поле ввода для фильтрации
    const filterInput = document.createElement("input");
    filterInput.type = "text";
    filterInput.placeholder = "Введите текст для фильтрации...";
    filterInput.classList.add("input", "popup-filter-input");

    // Добавляем поле ввода в начало popupList
    popupList.appendChild(filterInput);

    // Функция для отображения отфильтрованного списка
    function renderFilteredList() {
        const filterText = filterInput.value.toLowerCase(); // Текст фильтра, приведенный к нижнему регистру

        // Очищаем список перед обновлением
        popupList.querySelectorAll("li").forEach(li => li.remove());

        // Отфильтрованный список предложений
        const visibleSentences = sentenceList.filter(sentence =>
            matchesAllWords(sentence.sentence, filterText)
        );

        // Отображаем только те предложения, которые соответствуют фильтру
        visibleSentences.forEach((sentence, index) => {
            
            const li = document.createElement("li");
            li.textContent = sentence.sentence; // Используем текст предложения
            
            if (index === 0) {
                li.classList.add("selected-sentence");  
            }

            // Устанавливаем обработчик клика на элемент списка
            li.addEventListener("click", () => {
                onSelect(sentence); // Вызываем переданную функцию при выборе предложения
                hidePopupSentences();
            });

            popupList.appendChild(li);
            
        });
    }

    // Запускаем рендеринг отфильтрованного списка при вводе текста
    filterInput.addEventListener("input", renderFilteredList);

    // Слушатели на нажатие кнопок со стрелками и Tab и вставку выделенного текста
    filterInput.addEventListener("keydown", function (event) {
        event.stopPropagation();
        const listItems = popupList.querySelectorAll("li");
        const selectedLi = popupList.querySelector("li.selected-sentence");
        let currentIndex = Array.from(listItems).indexOf(selectedLi);
    
        if (event.key === "ArrowDown") {
            event.preventDefault();
            if (currentIndex < listItems.length - 1) {
                listItems[currentIndex]?.classList.remove("selected-sentence");
                listItems[currentIndex + 1]?.classList.add("selected-sentence");
            }
        }
    
        if (event.key === "ArrowUp") {
            event.preventDefault();
            if (currentIndex > 0) {
                listItems[currentIndex]?.classList.remove("selected-sentence");
                listItems[currentIndex - 1]?.classList.add("selected-sentence");
            }
        }
    
        if (event.key === "Tab" && selectedLi) {
            event.preventDefault();
            const selectedText = selectedLi.textContent;
            const selectedSentence = sentenceList.find(s => s.sentence === selectedText);
            if (selectedSentence) {
                onSelect(selectedSentence);
                hidePopupSentences();
            }
        }

        if (event.key === "Enter" && filterInput.value.trim()) {
            event.preventDefault();
            const newText = filterInput.value.trim();
            const customSentence = { sentence: newText };
            onSelect(customSentence);  // Вставляем текст в целевой элемент
            hidePopupSentences();
        }
        
    });

    // Изначально отображаем полный список
    renderFilteredList();

    // Устанавливаем позицию и отображаем popup
    popup.style.left = `${x}px`;
    popup.style.top = `${y + 10}px`; // Отображаем окно чуть ниже предложения
    popup.style.display = 'block';

    // **Добавляем обработчик клика для скрытия popup**
    document.addEventListener("click", function handleOutsideClick(event) {
        if (!popup.contains(event.target) && 
            !event.target.classList.contains("keyword-highlighted") && 
            !event.target.classList.contains("report__sentence") && 
            !event.target.classList.contains("icon-btn--add-sentence")) {
            hidePopupSentences();
            document.removeEventListener("click", handleOutsideClick);
        }
    });

    filterInput.focus();
}



// Скрывает всплывающее окно с предложениями.
function hidePopupSentences() {
    popup.style.display = 'none';
}