// textFiltrator.js

/**
 * Универсальная функция текстовой фильтрации массива элементов,
 * с поддержкой detach и debounce. Работает с любым числом input'ов на странице.
 * 
 * @param {string|HTMLElement} inputSelector - селектор или сам input-элемент
 * @param {Array<Element>} items - список элементов для фильтрации
 * @param {function} [getTextFn] - функция получения текста из элемента
 * @param {number} [debounceMs=100] - задержка debounce
 * @returns {function} detach - функция удаления обработчика фильтрации
 */
function setupTextFilter(inputSelector, items, getTextFn = el => el.textContent, debounceMs = 150) {
    const input = typeof inputSelector === 'string'
        ? document.querySelector(inputSelector)
        : inputSelector;

    if (!input || !items || !items.length) return () => {};

    // --- Снимаем старый обработчик, если был ---
    if (input._textFilterDetach) {
        input._textFilterDetach();
    }

    // --- Debounce ---
    let debounceTimer;
    function debounce(fn, ms) {
        return function(...args) {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => fn.apply(this, args), ms);
        };
    }

    function filterItems() {
        const searchText = input.value.toLowerCase().trim();
        const searchWords = searchText.split(/\s+/);
        items.forEach(item => {
            const itemText = getTextFn(item).toLowerCase();
            const isMatch = searchWords.every(word => itemText.includes(word));
            item.style.display = isMatch ? "" : "none";
        });
    }

    const debouncedFilter = debounce(filterItems, debounceMs);

    // --- Вешаем обработчик на input ---
    input.addEventListener('input', debouncedFilter);
    filterItems(); // сразу фильтруем при инициализации

    // --- Возвращаем detach-функцию ---
    function detach() {
        input.removeEventListener('input', debouncedFilter);
        delete input._textFilterDetach;
    }
    // Храним detach на самом input
    input._textFilterDetach = detach;

    return detach;
}