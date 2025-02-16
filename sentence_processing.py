# sentence_processing.py

from flask import g, current_app
from flask_login import current_user
from rapidfuzz import fuzz, process
import re
from docx import Document
from spacy_manager import SpacyModel
from models import Sentence, Paragraph, KeyWord, Report, User
from collections import defaultdict
from errors_processing import print_object_structure



def extract_keywords_from_doc(file_path):
    """
    Извлекает ключевые слова из Word документа, группируя их по протоколам или глобально.
    
    Каждая строка в документе соответствует группе ключевых слов, а ключевые слова в строке разделены запятыми.
    Жирный текст в документе указывает на привязку ключевых слов к протоколу. Если текст жирным не совпадает с именем 
    протокола, ключевые слова считаются глобальными.
    
    Args:
        file_path (str): Путь к файлу документа Word.

    Returns:
        list: Список словарей, где каждый словарь содержит 'report_id' (ID протокола или None для глобальных ключевых слов) 
              и 'key_words' (список ключевых слов).
    """
    doc = Document(file_path)
    keywords = []
    current_protocol = None  # Текущий протокол (если жирным текстом обозначено имя протокола)
    current_profile_reports = Report.find_by_profile(g.current_profile.id)
    # Получаем имена всех протоколов пользователя
    report_names = {report.report_name: report.id for report in current_profile_reports}

    for para in doc.paragraphs:
        if para.runs and para.runs[0].bold:  # Если параграф содержит жирный текст
            potential_report_name = para.text.strip()
            if potential_report_name in report_names:
                current_protocol = report_names[potential_report_name]  # Запоминаем ID протокола
            else:
                current_protocol = None  # Сброс, так как это глобальные ключевые слова

        else:
            # Разделяем ключевые слова по запятой
            key_words = process_keywords(para.text)
            if key_words:
                keywords.append({
                    'report_id': current_protocol,  # Если current_protocol = None, это глобальные ключевые слова
                    'key_words': key_words
                })

    return keywords


def process_keywords(key_word_input):
    """Обрабатываем строку ключевых слов, разделенных запятой, 
    и возвращаем список"""
    
    key_words = []
    for word in key_word_input.split(','):
        stripped_word = word.strip()
        if stripped_word:
            key_words.append(stripped_word)
    return key_words


def check_existing_keywords(key_words):
    """
    Проверяет, какие ключевые слова уже существуют у текущего профиля и возвращает сообщение об ошибке
    в случае дублирования, или None, если ключевые слова уникальны.
    
    Args:
        key_words (list): Список новых ключевых слов.

    Returns:
        string or None: Сообщение об ошибке, если дублирующиеся ключевые слова найдены, или None, если ключевые слова уникальны.
    """
    
    profile_key_words = KeyWord.find_by_profile(g.current_profile.id)

    # Создаем словарь для хранения результатов
    existing_keywords = {}

    # Проходим по всем ключевым словам пользователя
    for kw in profile_key_words:
        key_word_lower = kw.key_word.lower()
        if key_word_lower in [kw.lower() for kw in key_words]:
            # Проверяем, связаны ли ключевые слова с отчетами
            if kw.key_word_reports:
                for report in kw.key_word_reports:
                    report_name = report.report_name
                    if report_name not in existing_keywords:
                        existing_keywords[report_name] = []
                    existing_keywords[report_name].append(kw.key_word)
            else:
                # Если слово не связано с отчетом, оно является глобальным
                if "global" not in existing_keywords:
                    existing_keywords["global"] = []
                existing_keywords["global"].append(kw.key_word)

    # Если дублирующиеся ключевые слова найдены, формируем сообщение
    if existing_keywords:
        existing_keywords_message = []
        for key, words in existing_keywords.items():
            words_list = ", ".join(words)
            if key == "global":
                existing_keywords_message.append(f"global: {words_list}")
            else:
                existing_keywords_message.append(f"{key}: {words_list}")

        message = "The following keywords already exist:\n" + "\n".join(existing_keywords_message)
        return message

    return None


def extract_paragraphs_and_sentences(file_path):
    """
    Извлекает заголовки и предложения из документа Word.

    Функция обрабатывает документ .docx, определяя абзацы, начинающиеся с жирного текста, как заголовки разделов. 
    Остальные строки считаются содержимым этих разделов. Предложения внутри абзацев могут разделяться символом '!!', 
    формируя альтернативные варианты одного и того же предложения.

    Args:
        file_path (str): Путь к файлу Word.

    Returns:
        list: Список словарей, представляющих абзацы документа. 
              Каждый словарь содержит:
              - 'title' (str): Заголовок абзаца (если есть).
              - 'sentences' (list): Список предложений (или списков альтернативных предложений).
              - 'visible' (bool): Видимость абзаца (по умолчанию True).
              - 'bold' (bool): Является ли заголовок жирным (по умолчанию False).
              - 'is_title' (bool): Помечен ли абзац как заголовок (по умолчанию False).
              - 'type_paragraph' (str): Тип абзаца (по умолчанию "text").
    """
    document = Document(file_path)
    # Проверяю не пустой ли документ
    if not document.paragraphs:
        return []
    
    paragraphs_from_file = []
    current_paragraph = None

    for para in document.paragraphs:
        # Check if paragraph has bold text indicating it's a new section
        if para.runs and para.runs[0].bold:
            # Handle previous paragraph before moving to the next one
            if current_paragraph:
                paragraphs_from_file.append(current_paragraph)
            
            # Create a new paragraph entry
            current_paragraph = {
                'title': para.text.strip(),
                'sentences': []
            }
        else:
            # Append sentences to the current paragraph
            if current_paragraph:
                sentences = para.text.strip().split('!!')
                # If there are multiple parts, store them as a nested list
                if len(sentences) > 1:
                    current_paragraph['sentences'].append([s.strip() for s in sentences])
                else:
                    current_paragraph['sentences'].append(sentences[0].strip())

    # Append the last paragraph
    if current_paragraph:
        paragraphs_from_file.append(current_paragraph)

    return paragraphs_from_file



# Предварительная очистка. Проверяю на наличие предложения. 
# Убираю только повторяющиеся знаки и лишние пробелы. 
# Исключение - многоточие, обрабатывается отдельно. 
# Добавляю пробелы после знаков препинания, если их нет
def preprocess_sentence(text):
    """
    Performs a rough cleanup of the text to prepare it for further processing.
    Args:
        text (str): The input sentence or text.
    Returns:
        str: The preprocessed text.
    """
    # Проверяем, содержит ли текст хотя бы одну букву или цифру
    if not re.search(r'[a-zA-Zа-яА-ЯёЁ0-9]', text):
        return ""

   # Обрабатываем повторяющиеся знаки, кроме точки
    text = re.sub(r'([,!?:;"\'\(\)])\1+', r'\1', text)  # Повторяющиеся знаки → один

    # Обрабатываем многоточия отдельно
    text = re.sub(r'\.\.\.\.+', '...', text)  # Четыре и более точек → многоточие
    text = re.sub(r'(?<!\.)\.\.(?!\.)', '.', text)  # Две точки → одна
    
    # Добавляю пробелы после знаков препинания, если их нет
    text = re.sub(r'([.!?,;:])(?!\s)', r'\1 ', text)
    
    # Убираем лишние пробелы
    text = re.sub(r'\s+', ' ', text)  # Заменяем любые пробельные символы на один пробел

    return text


# это функция очистки текста перед сравнением 
# используется в working_with_reports.py дважды
def clean_text_with_keywords(sentence, key_words, except_words=None):
    """ Функция очистки текста от пробелов, знаков припенания, цифр и 
    ключевых слов с приведением всех слов предложения к нижнему 
    регистру """
    # Приводим текст к строчным буквам
    sentence = str(sentence)
    
    sentence = sentence.lower()
    # Удаляем ключевые слова
    if key_words:
        for word in key_words:
            sentence = re.sub(rf'\b{re.escape(word)}\b', '', sentence, flags=re.IGNORECASE)
    
    # Удаляем все кроме букв цифр и робелов
    sentence = re.sub(r"[^\w\s]", "", sentence)
    # Убираем цифры
    sentence = re.sub(r"\d+", "", sentence)
    # Удаляем лишние пробелы
    sentence = re.sub(r"\s+", " ", sentence).strip()
    # Убираем дополнительные слова
    if except_words:
        for word in except_words:
            sentence = re.sub(rf"\b{re.escape(word)}\b", "", sentence)
    
    return sentence


# это функция для окончательной очистки предложения 
# в working_with_reports.py.
# Она не очищает двойные знаки, лишние пробелы и не проверяется текст на наличие
# Должна применяться после функции preprocess_sentence
def clean_and_normalize_text(text):
    """
    Cleans the input text by handling punctuation, spaces, and formatting issues.
    Args:
        text (str): The text to be cleaned.
    Returns:
        str: The cleaned and normalized text.
    """
    
    # Исключения для слов, которые должны начинаться с заглавной буквы
    exeptions_after_punctuation =current_app.config["PROFILE_SETTINGS"]["EXCEPTIONS_AFTER_PUNCTUATION"]

    # Убираем пронумерованные элементы с точкой или скобкой в начале строки
    # Это в тему именно тут, так как ниже я обрабатываю скобки
    text = re.sub(r'^\s*\d+[\.\)]\s*', '', text)
    
    # Убираем лишние пробелы
    text = re.sub(r'\s+([.,!?;:])', r'\1', text)  # Пробел перед знаками препинания
    text = re.sub(r'\(\s+', r'(', text)  # Пробел после открывающей скобки
    text = re.sub(r'\s+\)', r')', text)  # Пробел перед закрывающей скобкой

    # Убираем пробелы в начале и конце строки. 
    # Это в тему именну тут, так как выше мы добавляем пробелы.
    text = text.strip()

    # Проверяем, начинается ли предложение с заглавной буквы
    if text and text[0].islower():
        text = text[0].upper() + text[1:]
        
    # Проверяем слова после двоеточий и запятых
    def process_after_punctuation(match):
        """
        Обрабатывает слово после знака препинания.
        Если слово не в исключениях, переводит его в нижний регистр.
        """
        punctuation = match.group(1)
        word = match.group(2)
        if word in exeptions_after_punctuation:
            return f"{punctuation} {word}"  # Оставляем слово как есть
        return f"{punctuation} {word.lower()}"  # Приводим к нижнему регистру
    
    # Регулярное выражение для поиска знаков препинания и последующего слова
    text = re.sub(r'([,:]) (\w+)', process_after_punctuation, text)
        
    if not re.search(r'[.!?]$', text):
        text += '.'

    return text

# # Это СТАРАЯ функция ее нужно будет заменить на split_sentences_if_needed
# def split_sentences(paragraphs):
#     """ Разделяем полученный текст на отдельные предложения 
#     ориентируясь на знаки препинания .!? """
#     split_paragraphs = []
#     sentence_endings = re.compile(r'(?<=[.!?])\s+')

#     for paragraph in paragraphs:
#         paragraph_id = paragraph.get("paragraph_id")
#         sentences = paragraph.get("sentences", [])
#         split_sentences = []

#         for sentence in sentences:
#             # Разбиваем предложения по концам предложений (точка, восклицательный знак или вопросительный знак)
#             split_sentences.extend(re.split(sentence_endings, sentence))

#         # Удаляем пустые предложения после разбиения
#         split_sentences = [s.strip() for s in split_sentences if s.strip()]

#         split_paragraphs.append({
#             "paragraph_id": paragraph_id,
#             "sentences": split_sentences
#         })

#     return split_paragraphs

# это новая функция используется в working_with_reports.py
def split_sentences_if_needed(text):
    """
    Splits a sentence into multiple sentences using SpaCy tokenizer.
    Args:
        text (str): The input sentence text.
    Returns:
        tuple: (list of valid sentences, list of excluded sentences).
    """
    language = current_app.config.get("PROFILE_SETTINGS", {}).get("APP_LANGUAGE", "ru")
    print(f"APP_LANGUAGE: {language}")
    
    # Загружаем модель SpaCy для текущего языка
    try:
        nlp = SpacyModel.get_instance(language)
    except ValueError as e:
        current_app.logger.error(f"Unsupported language '{language}' for SpaCy model: {e}")
        return [], []
    
    doc = nlp(text)
    sentences = [sent.text for sent in doc.sents]
    for sentence in sentences:
        if not re.search(r'[a-zA-Zа-яА-ЯёЁ0-9]', sentence):
            sentences.remove(sentence)

    if len(sentences) > 1:
        # Если найдено более одного предложения, добавляем в исключения
        return [], sentences # Splitted sentences
    return sentences, [] # Unsplitted sentences


# def get_new_sentences(processed_paragraphs):
#     """ Получаем только новые предложения, игнорируя те, что уже 
#     есть в базе данных, учитываем возможную разницу лишь в 
#     ключевых словах key_words """
#     except_words = current_app.config["PROFILE_SETTINGS"]["EXCEPT_WORDS"]
#     print(f"EXCEPT_WORDS: {except_words}")
#     new_sentences = []

#     # Получаем ключевые слова для текущего пользователя
#     key_words = []
#     profile_key_words = KeyWord.find_by_profile(g.current_profile.id)
#     for kw in profile_key_words:
#         key_words.append(kw.key_word.lower())

#     for paragraph in processed_paragraphs:
#         paragraph_id = paragraph.get("paragraph_id")
#         sentences = paragraph.get("sentences", [])

#         # Получаем существующие предложения для данного параграфа из базы данных
#         existing_sentences = Sentence.query.filter_by(paragraph_id=paragraph_id).all()

#         # Приводим существующие предложения к форме для сравнения (очищаем их)
#         existing_sentences_texts = []
#         for s in existing_sentences:
#             cleaned_sentence = clean_text_with_keywords(s.sentence.strip(), key_words, except_words)
#             existing_sentences_texts.append(cleaned_sentence)

#         # Получаем текст параграфа из базы данных
#         paragraph_text = Paragraph.query.filter_by(id=paragraph_id).first().paragraph

#         # Проверяем каждое предложение из обработанных, есть ли оно уже в базе данных
#         for sentence in sentences:
#             cleaned_sentence = clean_text_with_keywords(sentence.strip(), key_words, except_words)
            
#             if cleaned_sentence not in existing_sentences_texts:
#                 new_sentences.append({
#                     "paragraph_id": paragraph_id,
#                     "paragraph_text": paragraph_text,  # Добавляем текст параграфа
#                     "sentence": sentence.strip()  # Оригинальное предложение для вывода
#                 })

#     return new_sentences


def sort_key_words_group(unsorted_key_words_group):
    """
    Сортировка групп ключевых слов по первой букве первого ключевого слова в группе.
    Работает для всех вариантов структуры: с отчетами, с индексами и без них.
    """
    key_words_group_with_first_letter = []

    for group_data in unsorted_key_words_group:
        # В зависимости от структуры данных выбираем ключевые слова
        key_words = group_data.get("key_words", [])

        if key_words:
            # Проверяем, как представлены ключевые слова — как строки или объекты с полем "word"
            if isinstance(key_words[0], dict):
                # Если ключевые слова — это словари, берем поле "word"
                first_letter = key_words[0]["word"][0].lower() if key_words[0]["word"] else ""
            else:
                # Если ключевые слова — это строки
                first_letter = key_words[0][0].lower() if key_words[0] else ""
        else:
            first_letter = ""  # Если ключевых слов нет, используем пустую строку

        # Добавляем первую букву и саму группу данных для сортировки
        key_words_group_with_first_letter.append((first_letter, group_data))

    # Сортируем список по первой букве
    sorted_key_words_group = sorted(key_words_group_with_first_letter, key=lambda x: x[0])

    # Извлекаем только отсортированные группы (без первой буквы)
    return [group_data for _, group_data in sorted_key_words_group]


def group_keywords(keywords, with_index=False, with_report=False):
    """
    Создаем список сгруппированных слов или список словарей 
    с ключами group_index и key_words в зависимости от полученных 
    на входе аргументов, а также список ключевых слов с отчетами,
    если with_report=True.

    Args:
        keywords (list): Список объектов класса KeyWordGroup.
        with_index (boolean): Флаг для определения результата с или без добавления индекса.
        with_report (boolean): Флаг для группировки ключевых слов по отчетам.
    
    Returns:
    with_index=True:
        list of dict: Список словарей с ключами group_index и key_words (включает id и слово).
    with_index=False:
        list of lists: Список списков с отсортированными по group_index ключевыми словами (включает id и слово).
    with_report=True:
        list of dict: Список словарей, где ключи report_id, report_name, group_index и key_words (включает id и слово).
    """
    
    # Группируем ключевые слова по group_index, добавляя их id и слово
    grouped_keywords = defaultdict(list)
    for keyword in keywords:
        grouped_keywords[keyword.group_index].append({'id': keyword.id, 'word': keyword.key_word})

    if with_report:
        # Используем список для хранения данных по отчетам
        report_key_words = []
        seen_groups = set()  # Множество для хранения уникальных групп

        for keyword in keywords:
            group_index = keyword.group_index
            group_words = grouped_keywords[group_index]

            # Для каждого отчета, связанного с ключевым словом
            for report in keyword.key_word_reports:
                # Проверяем, не была ли группа уже добавлена для этого отчета
                if (report.id, group_index) not in seen_groups:
                    # Добавляем всю группу ключевых слов, если её еще не добавили
                    report_key_words.append({
                        'report_id': report.id,
                        'report_name': report.report_name,
                        'group_index': group_index,
                        'key_words': group_words  # Добавляем всю группу ключевых слов с их id
                    })
                    # Отмечаем, что группа с этим group_index уже добавлена для данного отчета
                    seen_groups.add((report.id, group_index))

        return report_key_words

    # Если with_index=True, возвращаем список словарей с group_index
    if with_index:
        grouped_keywords_with_index = []
        for group_index, words in grouped_keywords.items():
            grouped_keywords_with_index.append({'group_index': group_index, 'key_words': words})
        return grouped_keywords_with_index
    
    # Если with_index=False, возвращаем просто сгруппированные ключевые слова с их id
    return list(grouped_keywords.values())

# Алгоритм для сравнения предложений и вычисления их схожести в %. Используется в compare_sentences_by_paragraph()
def calculate_similarity_rapidfuzz(sentence1, sentence2):
    """
    Calculates the similarity between two sentences using the RapidFuzz library.

    Args:
        sentence1 (str): The first sentence.
        sentence2 (str): The second sentence.

    Returns:
        float: The similarity as a percentage.
    """
    from rapidfuzz import fuzz

    return fuzz.ratio(sentence1, sentence2)

# Сравниваю 2 предложения. Используется в working_with_report/save_modified_sentences %
def compare_sentences_by_paragraph(new_sentences, report_id):    
    """
    Compares new sentences with existing sentences in their respective paragraphs to determine uniqueness.

    Args:
        existing_paragraphs (list[Paragraph]): List of Paragraph objects with related sentences.
        new_sentences (list[dict]): List of new sentences to be added.
            Each dictionary should have the structure {"paragraph_id": int, "text": str}.
        key_words (list[str]): List of key words to remove during cleaning.

    Returns:
        dict: Contains "duplicates" and "unique" lists:
            - "duplicates": List of new sentences that match existing ones.
            - "unique": List of new sentences considered unique.
    """
    similarity_threshold_fuzz = float(current_app.config["PROFILE_SETTINGS"]["SIMILARITY_THRESHOLD_FUZZ"])
    except_words = current_app.config["PROFILE_SETTINGS"]["EXCEPT_WORDS"]
    print(f"SIMILARITY_THRESHOLD_FUZZ: {similarity_threshold_fuzz}")
    print(f"EXCEPT_WORDS: {except_words}")
    
    existing_paragraphs = Paragraph.query.filter_by(report_id=report_id).all()
    key_words_obj = KeyWord.get_keywords_for_report(g.current_profile.id, report_id)
    key_words = [keyword.key_word for keyword in key_words_obj]
    
    duplicates = []
    unique_sentences = []
    errors_count = 0
    # Итерируем по новым предложениям
    for new_sentence in new_sentences:
        new_paragraph_id = int(new_sentence.get("paragraph_id"))
        new_text = new_sentence.get("text")
        new_text_index = new_sentence.get("sentence_index")
        
        if not new_paragraph_id or not new_text:
            errors_count += 1
            continue  # Пропускаем некорректные данные
        
        # Находим соответствующий параграф
        paragraph = next((p for p in existing_paragraphs if p.id == new_paragraph_id), None)
        
        if not paragraph:
            unique_sentences.append(new_sentence)  # Если параграф не найден, считаем предложение уникальным
            continue

        # Получаем те предложения этого параграфа чей индекс равен индексу нового предложения
        existing_sentences = [
            {"id": sent.id, "index": sent.index, "text": sent.sentence} for sent in paragraph.paragraph_to_sentences if sent.index == new_text_index
        ]
        # Очищаем существующие предложения
        cleaned_existing = [
            {"id": sent.get("id"), "original_text": sent["text"], "cleaned_text": clean_text_with_keywords(sent.get("text"), key_words, except_words)} for sent in existing_sentences
            ]
        # Очищаем новое предложение
        cleaned_new_text = clean_text_with_keywords(new_text, key_words, except_words)
        # Проверяем на схожесть с существующими предложениями
        is_duplicate = False
        for existing in cleaned_existing:
            similarity_rapidfuzz = calculate_similarity_rapidfuzz(cleaned_new_text, existing["cleaned_text"])
            if similarity_rapidfuzz >= similarity_threshold_fuzz:
                duplicates.append({
                    "new_sentence": new_sentence,
                    "new_sentence_index": new_sentence.get("sentence_index"),
                    "new_sentence_paragraph": new_sentence.get("paragraph_id"),
                    "matched_with": {
                                "id": existing["id"],
                                "text": existing["original_text"]
                            },
                    "similarity_rapidfuzz": similarity_rapidfuzz
                })
                is_duplicate = True
                break

        if not is_duplicate:
            unique_sentences.append(new_sentence)

    return {"duplicates": duplicates, "unique": unique_sentences, "errors_count": errors_count}
