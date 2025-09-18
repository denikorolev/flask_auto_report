# sentence_processing.py

from flask_security import current_user
from rapidfuzz import fuzz
import re
import json
from docx import Document
from app.utils.spacy_manager import SpacyModel
from app.models.models import db, Paragraph, KeyWord, HeadSentence, BodySentence, TailSentence, HeadSentenceGroup, BodySentenceGroup, TailSentenceGroup, AppConfig
from app.utils.logger import logger
from collections import defaultdict



# Функция для обработки строки ключевых слов, разделенных запятой
def process_keywords(key_word_input: str) -> list:
    """Обрабатываем строку ключевых слов, разделенных запятой, 
    и возвращаем список"""
    
    key_words = []
    for word in key_word_input.split(','):
        stripped_word = word.strip()
        if stripped_word:
            key_words.append(stripped_word)
    return key_words


def check_existing_keywords(key_words, profile_id):
    """
    Проверяет, какие ключевые слова уже существуют у текущего профиля и возвращает сообщение об ошибке
    в случае дублирования, или None, если ключевые слова уникальны.
    
    Args:
        key_words (list): Список новых ключевых слов.

    Returns:
        string or None: Сообщение об ошибке, если дублирующиеся ключевые слова найдены, или None, если ключевые слова уникальны.
    """
    profile_key_words = KeyWord.find_by_profile(profile_id)

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


# Функция для извлечения абзацев и предложений из документа Word.
# Используется в new_report_creation.py
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
        logger.info(f"(preprocess_sentence) ⚠️ Пропускаю некорректные данные: {text}")
        return ""

    if len(text.strip()) < 3:
        logger.info(f"(preprocess_sentence) ⚠️ Пропускаю слишком короткий текст: {text}")
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
    """ Функция очистки текста от лишних пробелов, знаков припенания, 
    цифр, слов исключений и ключевых слов с приведением всех слов 
    предложения к нижнему регистру """
    
    
    
    
    # Приводим текст к строчным буквам
    sentence = str(sentence).lower()
    
    # Удаляем ключевые слова
    if key_words:
        for word in key_words:
            sentence = re.sub(rf'(?<!\w){re.escape(word)}(?!\w)', '', sentence, flags=re.IGNORECASE)
    
    # Удаляем все кроме букв цифр и робелов
    sentence = re.sub(r"[^\w\s]", "", sentence)
    # Убираем цифры
    sentence = re.sub(r"\d+", "", sentence)
    # Удаляем лишние пробелы
    sentence = re.sub(r"\s+", " ", sentence).strip()
    # Убираем дополнительные слова
    if except_words:
        for word in except_words:
            sentence = re.sub(rf"(?<!\w){re.escape(word)}(?!\w)", "", sentence, flags=re.IGNORECASE)
    
    return sentence


# это функция для окончательной очистки предложения перед сохранением в базу данных
# в working_with_reports.py.
# Она не очищает двойные знаки, лишние пробелы и не проверяется текст на наличие
# Должна применяться после функции preprocess_sentence
def clean_and_normalize_text(text, profile_id):
    """
    Cleans the input text by handling punctuation, spaces, and formatting issues.
    Args:
        text (str): The text to be cleaned.
    Returns:
        str: The cleaned and normalized text.
    """
    
    # Исключения для слов, которые должны начинаться с заглавной буквы
    exeptions_after_punctuation = AppConfig.get_setting(profile_id, "EXCEPTIONS_AFTER_PUNCTUATION", "").split(",")

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


# разделяет текс по предложениям, функция используется в working_with_reports.py
def split_sentences_if_needed(text, language=None):
    """
    Splits a sentence into multiple sentences using SpaCy tokenizer.
    Args:
        text (str): The input sentence text.
    Returns:
        tuple: (list of valid sentences, list of excluded sentences).
    """
    logger.info(f"(функция split_sentences_if_needed) -----------------------------------------")
    logger.info(f"(функция split_sentences_if_needed) 🚀 Начато разбиение текста на предложения")
    logger.info(f"(функция split_sentences_if_needed) получен текст: {text}")
    # Загружаем модель SpaCy для текущего языка
    try:
        nlp = SpacyModel.get_instance(language)
    except ValueError as e:
        logger.error(f"(функция split_sentences_if_needed) ❌ Ошибка загрузки модели SpaCy: {e}")
        return [], []
    
    doc = nlp(text)
    sentences = [sent.text for sent in doc.sents]
    splited_sentences = []
    for sentence in sentences:
        if re.search(r'[a-zA-Zа-яА-ЯёЁ0-9]', sentence) and len(sentence.strip()) > 2:
            logger.info(f"(функция split_sentences_if_needed) ✅ добавляю предложение в список: ({sentence})")
            splited_sentences.append(sentence.strip())
        else:
            logger.info(f"(функция split_sentences_if_needed) ❌ Пропускаю предложение: ({sentence}) - не содержит букв или слишком короткое")
    logger.info(f"(функция split_sentences_if_needed) После разделения предложений мы получили -  ({splited_sentences}) ")
    if len(splited_sentences) > 1:
        # Если найдено более одного предложения, добавляем в исключения
        return [], splited_sentences # Splitted sentences
    return splited_sentences, [] # Unsplitted sentences



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


# Сравниваю 2 предложения. Используется в working_with_report/save_modified_sentences. 
# Ищет совпадения с заданным порогом, также очищает текст от чисел и ключевых слов
def compare_sentences_by_paragraph(new_sentences, report_id, profile_id=None):    
    """
    Compares new sentences with existing sentences in their respective paragraphs to determine uniqueness.
    """
    logger.info(f"(функция compare_sentences_by_paragraph) 🚀 Начато сравнение новых предложений с существующими в базе данных")
    logger.debug(f"(функция compare_sentences_by_paragraph) Получены новые предложения - ({new_sentences})")
    similarity_threshold_fuzz = int(AppConfig.get_setting(profile_id, "SIMILARITY_THRESHOLD_FUZZ", 80))
    except_words = AppConfig.get_setting(profile_id, "EXCEPT_WORDS", "").split(",")
    logger.debug(f"(функция compare_sentences_by_paragraph) Порог схожести: {similarity_threshold_fuzz}")
    logger.info(f"(функция compare_sentences_by_paragraph) Исключаемые слова: {except_words}")
    
    existing_paragraphs = Paragraph.query.filter_by(report_id=report_id).all()
    key_words_obj = KeyWord.get_keywords_for_report(profile_id, report_id)
    key_words = [keyword.key_word for keyword in key_words_obj]
    logger.debug(f"(функция compare_sentences_by_paragraph) Получено {len(key_words)} ключевых слов.")
    
    duplicates = []
    unique_sentences = []
    errors_count = 0
    # Итерируем по новым предложениям
    for new_sentence in new_sentences:
        new_paragraph_id = int(new_sentence.get("paragraph_id"))
        new_text = new_sentence.get("text")
        new_sentence_type = new_sentence.get("sentence_type")
        new_sentence_head_sentence_id = new_sentence.get("head_sentence_id") or None
        
        if not new_paragraph_id or not new_text.strip():
            errors_count += 1
            logger.warning(f"(функция compare_sentences_by_paragraph) ⚠️ Пропускаю предложение ({new_sentence}) с пустым текстом или пустым id параграфа")
            continue  # Пропускаем некорректные данные
        
        # Находим соответствующий параграф
        paragraph = next((p for p in existing_paragraphs if p.id == new_paragraph_id), None)
        # Находим соответствующую группу для предложения
        related_group_id = None
        sentence_group_class = None
        
        if new_sentence_type == "body":
            head_sentence = HeadSentence.query.get(new_sentence_head_sentence_id)
            if not head_sentence:
                logger.warning(f"(функция compare_sentences_by_paragraph) ⚠️ Главное предложение с id={new_sentence_head_sentence_id} не найдено. Пропускаю предложение ({new_sentence})")
                errors_count += 1
                continue
            related_group_id = head_sentence.body_sentence_group_id or None
            existing_sentences = BodySentenceGroup.get_group_sentences(related_group_id) or []
            logger.debug(f"(функция compare_sentences_by_paragraph) {existing_sentences}")
            existing_sentences.append({"id": head_sentence.id, "sentence": head_sentence.sentence})
            
        else:
            if not paragraph:
                logger.warning(f"(функция compare_sentences_by_paragraph) ⚠️ Параграф с id={new_paragraph_id} не найден. Пропускаю предложение ({new_sentence})")
                errors_count += 1
                continue
            related_group_id = paragraph.tail_sentence_group_id or None
            if not related_group_id:
                logger.warning(f"(функция compare_sentences_by_paragraph) Группа хвостовых предложений не найдена. Добавляю в уникальные")
                unique_sentences.append(new_sentence)
                continue
            existing_sentences = TailSentenceGroup.get_group_sentences(related_group_id)
            
            logger.debug(f"(функция compare_sentences_by_paragraph) {existing_sentences}")
        
        # Очищаем существующие предложения
        cleaned_existing = []
        for sent in existing_sentences:
            cleaned_item = {
                "id": sent.get("id"),
                "original_text": sent["sentence"],
                "cleaned_text": clean_text_with_keywords(sent.get("sentence"), key_words, except_words)
            }
            cleaned_existing.append(cleaned_item)
            
        # Очищаем новое предложение
        cleaned_new_text = clean_text_with_keywords(new_text, key_words, except_words)
        # Проверяем на схожесть с существующими предложениями
        is_duplicate = False
        for existing in cleaned_existing:
            similarity_rapidfuzz = fuzz.ratio(cleaned_new_text, existing["cleaned_text"])
            if similarity_rapidfuzz >= similarity_threshold_fuzz:
                duplicates.append({
                    "new_sentence": new_sentence,
                   
                    "new_sentence_paragraph": new_sentence.get("paragraph_id"),
                    "matched_with": {
                                "id": existing["id"],
                                "text": existing["original_text"]
                            },
                    "similarity_rapidfuzz": similarity_rapidfuzz
                })
                is_duplicate = True
                logger.debug(f"(функция compare_sentences_by_paragraph) 🔄 Найдено дублирующее предложение ({new_sentence}) с существующим ({existing['original_text']}) с похожестью {similarity_rapidfuzz}")
                break

        if not is_duplicate:
            unique_sentences.append(new_sentence)

    return {"duplicates": duplicates, "unique": unique_sentences, "errors_count": errors_count}



# Функция для поиска существующих аналогичных предложений того же типа в базе данных 
# использую в models.py. Ищет 100% совпадения
def find_similar_exist_sentence(sentence_text, sentence_type, report_global_modality_id):
    """
    Ищет похожие предложения в базе данных.
    """
    user_id = current_user.id
    tags = None
    logger.info(f"(функция find_similar_exist_sentence)(тип предложения: '{sentence_type}') 🚀 Начат поиск существующих аналогичных предложений в базе данных")
    
    # Получаем все предложения того же типа и с такими же базовыми параметрами из базы данных
    if sentence_type == "head":
        similar_type_sentences = HeadSentence.query.filter_by(tags=tags, report_global_modality_id=report_global_modality_id, user_id = user_id).all()
    elif sentence_type == "body":
        similar_type_sentences = BodySentence.query.filter_by(tags=tags, report_global_modality_id=report_global_modality_id, user_id = user_id).all()
    elif sentence_type == "tail":
        similar_type_sentences = TailSentence.query.filter_by(tags=tags, report_global_modality_id=report_global_modality_id, user_id = user_id).all()
    else:
        raise ValueError(f"Invalid sentence type: {sentence_type}")

    print(f"-----тип {sentence_type}------найдено предложений для данного пользователя {len(similar_type_sentences)} --------------------")
    # Сравниваем входное предложение с каждым из существующих
    for exist_sentence in similar_type_sentences:
        if exist_sentence.sentence == sentence_text:
            logger.info(f"(функция find_similar_exist_sentence) 🧩 Найдено совпадение с предложением '{exist_sentence.sentence}' в базе данных. Возвращаю предложение")
            return exist_sentence
    logger.info(f"(функция find_similar_exist_sentence) Совпадений не найдено. Возвращаю None")
    return None
    
      
      
# Функция для оценки уникальности индексов в главных предложениях параграфа. Номера индексов не должны повторяться
def check_head_sentence_indexes(paragraph_id):
    """
    Проверяет уникальность индексов главных предложений в параграфе.
    """
    head_sentences_groupe, _ = Paragraph.get_paragraph_groups(paragraph_id)
    
    head_sentences = HeadSentenceGroup.get_sentences(head_sentences_groupe)
    indexes = [sent.index for sent in head_sentences]
    duplicates = [index for index in indexes if indexes.count(index) > 1]
    return duplicates

        

# Функция проверяет предложение на уникальность и добавляет его 
# в результат, если оно уникально. Работает со списком по ссылке, 
# ничего не возвращает, просто меняет предоставленные список и множество
def _add_if_unique(raw_text, key_words, except_words, cleaned_list, result_set, threshold):
    """
    Проверяет, является ли предложение уникальным, и добавляет его в результат.

    Args:
        raw_text (str): Оригинальный текст.
        key_words (list): Ключевые слова для очистки.
        except_words (list): Слова-исключения.
        cleaned_list (list): Уже очищенные тексты.
        result_set (set): Уникальные предложения (результат).
        threshold (int): Порог схожести.
    """
    cleaned = clean_text_with_keywords(raw_text, key_words, except_words)
    for existing in cleaned_list:
        if fuzz.ratio(cleaned, existing) >= threshold:
            return
    cleaned_list.append(cleaned)
    result_set.add(raw_text)
   


def convert_template_json_to_text(template_json: list) -> str:
    """
    Преобразует шаблон отчета из JSON-структуры (список параграфов с head_sentences)
    в обычный текст с заголовками и предложениями для ассистента.

    Args:
        template_json (list): Список параграфов с ключами "paragraph" и "head_sentences".

    Returns:
        str: Простой текст с заголовками параграфов и предложениями под ними.
    """
    lines = []
    for block in template_json:
        paragraph = block.get("paragraph", "").strip()
        if paragraph:
            lines.append(f"{paragraph}:")
        for sentence in block.get("head_sentences", []):
            sentence_text = sentence.get("sentence", "").strip()
            if sentence_text:
                lines.append(sentence_text)
        lines.append("")  # Пустая строка между параграфами
    return "\n".join(lines).strip()



def split_report_structure_for_ai(report_data: list) -> tuple:
    """
    Формирует две структуры:
    - skeleton: полная структура + id параграфов и head_sentences
    - ai_input: только editable параграфы (is_active=True, is_additional=False, head_sentences not empty) + "Miscellaneous"
      (В ai_input нет ключей is_active и is_additional!)

    Пример:
        skeleton = [
            {
                "id": 1,
                "paragraph": "ОРГАНЫ ГРУДНОЙ КЛЕТКИ:",
                "is_active": True,
                "is_additional": False,
                "head_sentences": []
            },
            ...
        ]
        ai_input = [
            {
                "id": 2,
                "paragraph": "Легкие",
                "head_sentences": [{"id": 11, "sentence": "Инфильтрация не выявлена."}]
            },
            {
                "id": "miscellaneous",
                "paragraph": "Miscellaneous",
                "head_sentences": []
            }
        ]

    Args:
        report_data (list): Список параграфов отчета.
    Returns:
        tuple: (skeleton, ai_input)
    """
    skeleton = []
    ai_input = []

    # Build skeleton
    for para in report_data:
        scel = {
            "id": para["id"],
            "paragraph": para["paragraph"],
            "is_active": para.get("is_active", True),
            "is_additional": para.get("is_additional", False),
            "head_sentences": [
                {
                    "id": hs["id"],
                    "sentence": hs["sentence"]
                }
                for hs in para.get("head_sentences", [])
            ]
        }
        skeleton.append(scel)

    # Build ai_input: only paragraphs with is_active==True, is_additional==False, and head_sentences not empty
    for para in skeleton:
        if (
            para.get("is_active", True)
            and not para.get("is_additional", False)
            and len(para.get("head_sentences", [])) > 0
        ):
            ai_para = dict(para)  # shallow copy is enough, head_sentences is list of dicts
            ai_para.pop("is_active", None)
            ai_para.pop("is_additional", None)
            ai_input.append(ai_para)

    # Add "Miscellaneous" paragraph to ai_input
    misc_paragraph = {
        "id": "miscellaneous",
        "paragraph": "Miscellaneous",
        "head_sentences": []
    }
    ai_input.append(misc_paragraph)

    return skeleton, ai_input



def replace_head_sentences_with_fuzzy_check(main_data, ai_data, threshold=95):
    """
    Обновляет тексты head_sentences в main_data на основе ai_data.
    Структура параграфов и head_sentences должна совпадать по id.
    Если кол-во параграфов не совпадает — логируем и возвращаем main_data как есть.
    Если заголовки параграфов отличаются более чем на threshold — бросаем ValueError.
    """
    logger.info("(replace_head_sentences_with_fuzzy_check) 🚀  Начат процесс замены главных предложений синтезированными")
    logger.info(f"(replace_head_sentences_with_fuzzy_check) main_data: {len(main_data)} параграфов, ai_data: {len(ai_data)} параграфов")

    if not isinstance(main_data, list) or not isinstance(ai_data, list):
        logger.error("(replace_head_sentences_with_fuzzy_check) ❌ Входные данные не являются списками.")
        raise ValueError("основные данные и обработанные данные должны быть списками параграфов.")

    # 1. Быстрая сверка количества параграфов
    if len(main_data) != len(ai_data):
        logger.error(f"(replace_head_sentences_with_fuzzy_check) ❌ Количество параграфов не совпадает: main={len(main_data)} / ai={len(ai_data)}")
        # Не рейзим, продолжаем попытку подстановки

    # 2. Индексируем AI-параграфы по id для быстрого доступа
    ai_paragraphs_by_id = {str(p["id"]): p for p in ai_data}

    # 3. Обрабатываем каждый параграф main_data
    for main_par in main_data:
        para_id = str(main_par["id"])
        main_title = main_par.get("paragraph", "").strip()
        ai_par = ai_paragraphs_by_id.get(para_id)
        if not ai_par:
            logger.warning(f"(replace_head_sentences_with_fuzzy_check) Не найден параграф id={para_id} в AI-ответе, пропускаю")
            continue

        ai_title = ai_par.get("paragraph", "").strip()
        ratio = fuzz.ratio(main_title, ai_title)
        if ratio < threshold:
            logger.error(f"(replace_head_sentences_with_fuzzy_check) ❌ Заголовок параграфа '{main_title}' не совпадает с AI '{ai_title}' (совпадение {ratio}%)")
            raise ValueError(
                f"Несовпадение текста параграфа id={para_id}\n"
                f"Ожидалось: '{main_title}'\n"
                f"Найдено:    '{ai_title}'\n"
            )

        # Индексируем head_sentences по id для замены
        ai_head_by_id = {str(hs["id"]): hs.get("sentence", "") for hs in ai_par.get("head_sentences", [])}
        for main_hs in main_par.get("head_sentences", []):
            hs_id = str(main_hs["id"])
            if hs_id in ai_head_by_id:
                main_hs["sentence"] = ai_head_by_id[hs_id]
            # если нет — не меняем (оставляем оригинал)

    return main_data


def merge_ai_response_into_skeleton(skeleton, ai_response):
    """
    Восстанавливает полную структуру отчета:
    - Основные параграфы: id, paragraph, is_active, is_additional, head_sentences с новыми текстами
    - Miscellaneous возвращается отдельно (список head_sentences)
    """
    # Быстрая индексация AI-параграфов по id
    ai_paragraphs_by_id = {str(p["id"]): p for p in ai_response if str(p["id"]) != "miscellaneous"}
    misc_sentences = []
    for p in ai_response:
        if str(p["id"]) == "miscellaneous":
            misc_sentences = p.get("head_sentences", [])
            break

    # Идем по скелету и подменяем предложения
    merged = []
    for para in skeleton:
        para_id = str(para["id"])
        # Копируем параграф из скелета
        merged_para = dict(para)
        # Обновляем только текст предложений
        ai_para = ai_paragraphs_by_id.get(para_id)
        if ai_para:
            # Маппинг head_sentences по id для скорости
            ai_head_by_id = {str(hs["id"]): hs["sentence"] for hs in ai_para.get("head_sentences", [])}
            # Обновляем предложения только по id (не меняя структуру)
            new_head_sentences = []
            for hs in merged_para["head_sentences"]:
                hs_id = str(hs["id"])
                if hs_id in ai_head_by_id:
                    # Обновляем только текст
                    new_hs = dict(hs)
                    new_hs["sentence"] = ai_head_by_id[hs_id]
                    new_head_sentences.append(new_hs)
                else:
                    # Не найдено в AI — оставляем оригинал
                    new_head_sentences.append(hs)
            merged_para["head_sentences"] = new_head_sentences
        # Если нет ai_para — ничего не трогаем, копия скелета
        merged.append(merged_para)
    return merged, misc_sentences


# Превращает JSON-строки в объекты Python, если они сериализованы НИГДЕ НЕ ИСПОЛЬЗУЮТСЯ
def deep_json_deserialize_if_needed(data, context="root"):
    """
    Рекурсивно десериализует строки на всех уровнях, если они являются JSON-строкой
    (например, список или словарь, сериализованный дважды).
    """
    # 1. Попытка распарсить JSON, если это строка
    logger.info(f"(deep_json_deserialize_if_needed) 🚀 Начата десериализация данных в контексте: {context}")
    if isinstance(data, str):
        try:
            parsed = json.loads(data)
            logger.warning(f"(deep_json_deserialize_if_needed) ⚠️ В '{context}' десериализована строка в JSON.")
            return deep_json_deserialize_if_needed(parsed, context)
        except json.JSONDecodeError:
            logger.info(f"(deep_json_deserialize_if_needed) ❌ Данные в '{context}' не являются JSON-строкой, возвращаю как есть.")
            return data  # обычная строка, не JSON

    # 2. Обработка словаря
    elif isinstance(data, dict):
        return {
            key: deep_json_deserialize_if_needed(value, context + f".{key}")
            for key, value in data.items()
        }

    # 3. Обработка списка
    elif isinstance(data, list):
        return [
            deep_json_deserialize_if_needed(item, context + f"[{i}]")
            for i, item in enumerate(data)
        ]

    # 4. Всё остальное возвращаем как есть (int, float, None и пр.)
    return data

