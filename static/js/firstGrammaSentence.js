// Очищает текст по заданным правилам
function firstGrammaSentence(sentence) {
    sentence = sentence.trim();
    if (!sentence) return sentence; // Если пустая строка — ничего не делаем

    sentence = sentence.replace(/\.{2,}$/g, ".") // Убираем двойные точки в конце предложения
    
    // Ставим точку в конце предложения, если ее нет 
    if (!/[.!?:,]$/.test(sentence)) {
        sentence += ".";
    }

    
    sentence = sentence.charAt(0).toUpperCase() + sentence.slice(1); //  Делаем первую букву заглавной
    sentence = sentence.replace(/(\d)\s*[гГ][р](?=[^\p{L}]|$)/gu, "$1°"); // `Гр и гр` после цифры → заменяем на `°`

    sentence = sentence.replace(/(\S+)\s*[.]?\s*\)/g, "$1)"); // Убираем точку и пробел перед `)`
    sentence = sentence.replace(/\)/g, ") "); // Добавляем пробел после `)`
    sentence = sentence.replace(/\(\s+/g, "("); // Убираем пробел после `(`

    sentence = sentence.replace(/([,.!?:;])(?=\p{L})/gu, "$1 "); // Добавляем пробел после знаков, если его нет, но только перед буквой, например 1,5 останется неизменным
    sentence = sentence.replace(/\s([,.!?:;])/g, "$1"); // Убираем пробел перед знаками препинания
    sentence = sentence.replace(/\s+/g, " "); // Заменяем несколько пробелов на один

    const abbreviations = userSettings.EXCEPTIONS_AFTER_PUNCTUATION;
    // Если слово в нижнем регистре и является аббревиатурой, то делаем его заглавным
    sentence = sentence.replace(/(?<!\p{L})[а-яёa-z-]+(?!\p{L})/giu, (match) => {
        const upperMatch = match.toUpperCase();
        return abbreviations.includes(upperMatch) ? upperMatch : match;
    });
    
    // Если слова стоит после `:`, то делаем его с маленькой буквы кроме аббревиатур из списка
    sentence = sentence.replace(/:\s*([А-ЯЁA-Z][а-яёa-z]+)/g, (match, word) =>
        abbreviations.includes(word.toUpperCase()) ? match : `: ${word.toLowerCase()}`
    );

    return sentence.trim();
}