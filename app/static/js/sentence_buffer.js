/**
 * sentence_buffer.js
 * 
 * Универсальная работа с буфером предложений и групп предложений.
 * Хранение в localStorage с автоочисткой по времени.
 */

const BUFFER_KEY = "sentenceBuffer";   // Ключ хранения в localStorage
const BUFFER_TTL = 60 * 60 * 1000;     // Время жизни буфера: 1 час (в миллисекундах)
const TIMESTAMP_KEY = "sentenceBufferTimestamp"; // Ключ для хранения времени создания буфера


/**
 * Добавить элемент в буфер.
 * @param {Object} item - Элемент для добавления (со всеми обязательными полями).
 */
function addToBuffer(item) {
    const buffer = getBuffer();

    // Добавляем новый элемент
    buffer.push(item);

    // Обновляем хранилище
    localStorage.setItem(BUFFER_KEY, JSON.stringify(buffer));
    localStorage.setItem(TIMESTAMP_KEY, Date.now().toString());

}

// Взять элемент из буфера по индексу
function getFromBuffer(index) {
    const buffer = getBuffer();
    return buffer[index];
}


/**
 * Получить текущий буфер (с учетом автоочистки по TTL).
 * @returns {Array} - Массив объектов буфера или пустой массив.
 */
function getBuffer() {
    const timestamp = parseInt(localStorage.getItem(TIMESTAMP_KEY), 10);
    const now = Date.now();

    // Если прошло больше TTL — очистить буфер
    if (isNaN(timestamp) || now - timestamp > BUFFER_TTL) {
        clearBuffer();
        return [];
    }

    // Иначе вернуть актуальные данные
    const buffer = JSON.parse(localStorage.getItem(BUFFER_KEY)) || [];
    return buffer;
}


/**
 * Очистить буфер полностью.
 */
function clearBuffer() {
    localStorage.removeItem(BUFFER_KEY);
    localStorage.removeItem(TIMESTAMP_KEY);
}


/**
 * Удалить конкретный элемент из буфера по индексу.
 * @param {number} index - Индекс элемента для удаления.
 */
function removeFromBuffer(index) {
    const buffer = getBuffer();

    if (index >= 0 && index < buffer.length) {
        const removed = buffer.splice(index, 1); // Удаляем элемент
        localStorage.setItem(BUFFER_KEY, JSON.stringify(buffer)); // Обновляем хранилище
    } else {
        console.warn("Индекс вне диапазона буфера:", index);
    }
}


/**
 * Проверить, есть ли что-то в буфере.
 * @returns {boolean} - true, если буфер не пустой.
 */
function isBufferNotEmpty() {
    const buffer = getBuffer();
    return buffer.length > 0;
}

