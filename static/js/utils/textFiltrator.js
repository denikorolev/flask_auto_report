/**
 * Универсальная функция текстовой фильтрации элементов.
 * 
 * @param {string} inputSelector - Селектор поля ввода текста.
 * @param {string} itemsSelector - Селектор элементов, которые нужно фильтровать.
 * @param {function} [getTextFn] - (необязательно) функция получения текста из элемента.
 */
function setupTextFilter(inputSelector, itemsSelector, getTextFn = el => el.textContent) {
    const input = document.querySelector(inputSelector);
    const items = document.querySelectorAll(itemsSelector);

    if (!input || items.length === 0) return;

    input.addEventListener("input", () => {
        const searchText = input.value.toLowerCase().trim();
        const searchWords = searchText.split(/\s+/);

        items.forEach(item => {
            const itemText = getTextFn(item).toLowerCase();
            const isMatch = searchWords.every(word => itemText.includes(word));
            item.style.display = isMatch ? "" : "none";
        });
    });
}