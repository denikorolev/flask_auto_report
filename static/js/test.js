// test.js

// Первый список тестовых предложений
const testSentences1 = [
    "Это тестовое предложение 1",
    "Еще одно тестовое предложение",
    "Очередное тестовое предложение"
];

// Второй список тестовых предложений
const testSentences2 = [
    "Первое предложение второго списка",
    "Второе предложение второго списка",
    "Третье предложение второго списка"
];

// Третий список тестовых предложений
const testSentences3 = [
    "Первое предложение третьего списка",
    "Второе предложение третьего списка",
    "Третье предложение третьего списка"
];

// Четвертый список тестовых предложений
const testSentences4 = [
    "Четвертое тестовое предложение 1",
    "Четвертое тестовое предложение 2",
    "Четвертое тестовое предложение 3"
];

// Ассоциируем списки предложений с абзацами
document.addEventListener("DOMContentLoaded", function() {
    const sentence1 = document.getElementById("sentence1");
    const sentence2 = document.getElementById("sentence2");
    const sentence3 = document.getElementById("sentence3");
    const sentence4 = document.getElementById("sentence4");

    // Связываем списки с элементами через свойство объекта
    sentence1.sentenceList = testSentences1;
    sentence2.sentenceList = testSentences2;
    sentence3.sentenceList = testSentences3;
    sentence4.sentenceList = testSentences4;

    const sentences = [sentence1, sentence2, sentence3, sentence4];

    // Переменные для управления кружком и всплывающим окном
    const plusCircle = document.getElementById("plusCircle");
    const popup = document.getElementById("popup");
    const popupList = document.getElementById("popupList");
    let activeSentence = null;
    let hoverTimeout = null;
    let hideTimeout = null;

    // Функция для отображения кружка "+"
    function showPlusCircle(x, y, target) {
        activeSentence = target;
        plusCircle.style.left = `${x - 25}px`; // Чуть левее курсора
        plusCircle.style.top = `${y + 10}px`; // Чуть ниже курсора
        plusCircle.style.visibility = 'visible';
    }

    // Функция для скрытия кружка с задержкой
    function hidePlusCircle() {
        hideTimeout = setTimeout(() => {
            plusCircle.style.visibility = 'hidden';
        }, 500); // Задержка в 500 мс перед скрытием
    }

    // Функция для показа всплывающего окна со списком предложений
    function showPopup(x, y, sentenceList) {
        popupList.innerHTML = ''; // Очищаем старые предложения

        sentenceList.forEach(sentence => {
            const li = document.createElement("li");
            li.textContent = sentence;
            popupList.appendChild(li);

            // Обработка клика по предложению
            li.addEventListener("click", function() {
                if (activeSentence) {
                    activeSentence.textContent = sentence; // Заменяем текст абзаца
                    hidePopup(); // Закрываем всплывающее окно после выбора
                }
            });
        });

        popup.style.left = `${x}px`;
        popup.style.top = `${y + 30}px`; // Отображаем окно чуть ниже кружка
        popup.style.display = 'block';
    }

    // Функция для скрытия всплывающего окна
    function hidePopup() {
        popup.style.display = 'none';
    }

    // Наведение на абзац
    sentences.forEach(sentence => {
        sentence.addEventListener("mouseenter", function(event) {
            // Показываем кружок с задержкой в 500 мс
            hoverTimeout = setTimeout(() => {
                showPlusCircle(event.pageX, event.pageY, sentence);
            }, 500);
        });

        sentence.addEventListener("mouseleave", function() {
            clearTimeout(hoverTimeout); // Отменяем показ кружка, если мышь ушла с элемента
            hidePlusCircle(); // Скроем кружок с небольшой задержкой
        });
    });

    // Клик по кружку "+"
    plusCircle.addEventListener("mouseenter", function() {
        clearTimeout(hideTimeout); // Если мышь над кружком, не скрываем его
    });

    plusCircle.addEventListener("mouseleave", function() {
        hidePlusCircle(); // Скрываем кружок, если мышь ушла
    });

    plusCircle.addEventListener("click", function(event) {
        if (activeSentence && activeSentence.sentenceList) {
            showPopup(event.pageX, event.pageY, activeSentence.sentenceList);
        }
    });

    // Скрываем всплывающее окно при клике вне его
    document.addEventListener("click", function(event) {
        if (!popup.contains(event.target) && !plusCircle.contains(event.target)) {
            hidePopup();
        }
    });
});
