// static/js/utils/ai_handlers.js

// Предполагается что sendRequest подключен на всех страницах, где используется этот код

/**
 * Очищает текст через OpenAI и возвращает результат в ту же textarea.
 * @param {HTMLTextAreaElement} textarea - textarea для текста
 * @param {HTMLButtonElement} button - кнопка "Подготовить", чтобы блокировать/разблокировать на время запроса
 */
export async function prepareTextWithAI(textarea, button) {
    const rawText = textarea.value.trim();
    if (!rawText) {
        alert("Пожалуйста, введите текст для предварительной очистки.");
        return;
    }
    button.disabled = true;

    const response = await sendRequest({
        url: "/openai_api/clean_raw_text",
        data: { raw_text: rawText },
    });

    button.disabled = false;

    if (response && response.status === "success" && response.data) {
        textarea.value = response.data;
    }
}