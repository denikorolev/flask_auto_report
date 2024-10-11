# sentence_processing.py

from flask_login import current_user
import re
from docx import Document
from models import Sentence, ReportParagraph, KeyWordsGroup, Report, User
from collections import defaultdict
from errors_processing import print_object_structure



def extract_keywords_from_doc(file_path, user_reports):
    """
    Извлекает ключевые слова из Word документа, группируя их по протоколам или глобально.
    
    Каждая строка в документе соответствует группе ключевых слов, а ключевые слова в строке разделены запятыми.
    Жирный текст в документе указывает на привязку ключевых слов к протоколу. Если текст жирным не совпадает с именем 
    протокола, ключевые слова считаются глобальными.
    
    Args:
        file_path (str): Путь к файлу документа Word.
        user_reports (list): Список протоколов пользователя для привязки ключевых слов.

    Returns:
        list: Список словарей, где каждый словарь содержит 'report_id' (ID протокола или None для глобальных ключевых слов) 
              и 'key_words' (список ключевых слов).
    """
    doc = Document(file_path)
    keywords = []
    current_protocol = None  # Текущий протокол (если жирным текстом обозначено имя протокола)

    # Получаем имена всех протоколов пользователя
    report_names = {report.report_name: report.id for report in user_reports}

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



def check_existing_keywords(key_words, user_id):
    """
    Проверяет, какие ключевые слова уже существуют у пользователя и возвращает информацию
    о том, являются ли они глобальными или привязаны к отчетам.
    
    Args:
        key_words (list): Список новых ключевых слов.
        user_id (int): ID текущего пользователя.

    Returns:
        dict: Словарь с информацией о существующих ключевых словах. Ключ - название отчета или "global",
              значение - список ключевых слов.
    """
    # Получаем все ключевые слова пользователя
    user_key_words = KeyWordsGroup.find_by_user(user_id)

    # Создаем словарь для хранения результатов
    existing_keywords = {}

    # Проходим по всем ключевым словам пользователя
    for kw in user_key_words:
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
    
    return existing_keywords


def extract_paragraphs_and_sentences(file_path):
    """
    Extracts paragraphs and sentences from a Word document, including additional paragraph attributes.

    This function processes a Word document (docx) and identifies paragraphs
    that start with bold text as section titles. Each title can include additional attributes
    specified within double parentheses `(( ))`, such as paragraph type (`text`, `scanparam`, etc.)
    and flags (`**` for invisible, `==` for bold, `++` for title). Sentences within the paragraphs
    can be split by the '!!' character to create additional sentences with the same index but incremented weight.

    Args:
        file_path (str): The file path of the Word document to be processed.

    Returns:
        list: A list of dictionaries, each representing a paragraph in the document.
              Each dictionary contains:
              - 'title' (str): The title of the paragraph (bold text).
              - 'sentences' (list): A list of sentences (str or list) belonging to that paragraph.
                                    If a sentence contains '!!', it will be represented as a list
                                    of sentences for further processing.
              - 'visible' (bool): Visibility of the paragraph (default is True).
              - 'bold' (bool): Whether the paragraph title is bold (default is False).
              - 'is_title' (bool): Whether the paragraph is marked as a title (default is False).
              - 'type_paragraph' (str): Type of the paragraph, extracted from double parentheses `(( ))`.
    
    Example:
        [
            {
                'title': 'Section 1',
                'sentences': ['Sentence 1.', ['Sentence 2.', 'Sentence 2 alternative.']],
                'visible': True,
                'bold': False,
                'is_title': True,
                'type_paragraph': 'text'
            }
        ]
    """
    document = Document(file_path)
    paragraphs_from_file = []
    current_paragraph = None

    # Valid types for paragraphs
    valid_types = {"text", "impression", "clincontext", "scanparam", "custom", "dinamics", "scanlimits", "title"}

    for para in document.paragraphs:
        # Check if paragraph has bold text indicating it's a new section
        if para.runs and para.runs[0].bold:
            # Handle previous paragraph before moving to the next one
            if current_paragraph:
                paragraphs_from_file.append(current_paragraph)
            
            # Extract flags, paragraph type, and title text
            title_text = para.text.strip()
            visible = True
            bold = False
            is_title = False
            type_paragraph = "text"  # Default type

            # Check for the presence of flags and paragraph type in the format: ((type, flags))
            if title_text.startswith("((") and "))" in title_text:
                # Extract the content inside double parentheses
                content = title_text[2:title_text.find("))")].split(',')
                # Identify the paragraph type if the first item matches a valid type
                potential_type = content[0].strip().lower()
                if potential_type in valid_types:
                    type_paragraph = potential_type
                    # Remove the type from content list to process the rest as flags
                    content = content[1:]
                
                # Process remaining flags in content
                for flag in content:
                    flag = flag.strip()
                    if flag == "**":
                        visible = False
                    elif flag == "==":
                        bold = True
                    elif flag == "++":
                        is_title = True
                
                # Remove the entire ((...)) block from the title text
                title_text = title_text[title_text.find("))") + 2:].strip()

            # Create a new paragraph entry with the extracted attributes
            current_paragraph = {
                'title': title_text,
                'sentences': [],
                'visible': visible,
                'bold': bold,
                'is_title': is_title,
                'type_paragraph': type_paragraph
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



def clean_text(sentence, key_words):
    """ Функция очистки текста от пробелов, знаков припенания, цифр и 
    ключевых слов с приведением всех слов предложения к нижнему 
    регистру """
    # Приводим текст к строчным буквам
    sentence = sentence.lower()
    # Удаляем ключевые слова
    for word in key_words:
        sentence = re.sub(rf'\b{re.escape(word)}\b', '', sentence, flags=re.IGNORECASE)
    # Удаляем лишние пробелы (больше одного пробела)
    sentence = re.sub(r'\s+', ' ', sentence)
    # Удаляем знаки препинания и цифры
    sentence = re.sub(r'[,.!?0-9]', '', sentence)
    # Удаляем пробелы в начале и конце строки
    return sentence.strip()


def split_sentences(paragraphs):
    """ Разделяем полученный текст на отдельные предложения 
    ориентируясь на знаки препинания .!? """
    split_paragraphs = []
    sentence_endings = re.compile(r'(?<=[.!?])\s+')

    for paragraph in paragraphs:
        paragraph_id = paragraph.get("paragraph_id")
        sentences = paragraph.get("sentences", [])
        split_sentences = []

        for sentence in sentences:
            # Разбиваем предложения по концам предложений (точка, восклицательный знак или вопросительный знак)
            split_sentences.extend(re.split(sentence_endings, sentence))

        # Удаляем пустые предложения после разбиения
        split_sentences = [s.strip() for s in split_sentences if s.strip()]

        split_paragraphs.append({
            "paragraph_id": paragraph_id,
            "sentences": split_sentences
        })

    return split_paragraphs


def get_new_sentences(processed_paragraphs):
    """ Получаем только новые предложения, игнорируя те, что уже 
    есть в базе данных, учитываем возможную разницу лишь в 
    ключевых словах key_words """
    new_sentences = []

    # Получаем ключевые слова для текущего пользователя
    key_words = []
    user_key_words = KeyWordsGroup.find_by_user(current_user.id)
    for kw in user_key_words:
        key_words.append(kw.key_word.lower())

    for paragraph in processed_paragraphs:
        paragraph_id = paragraph.get("paragraph_id")
        sentences = paragraph.get("sentences", [])

        # Получаем существующие предложения для данного параграфа из базы данных
        existing_sentences = Sentence.query.filter_by(paragraph_id=paragraph_id).all()

        # Приводим существующие предложения к форме для сравнения (очищаем их)
        existing_sentences_texts = []
        for s in existing_sentences:
            cleaned_sentence = clean_text(s.sentence.strip(), key_words)
            existing_sentences_texts.append(cleaned_sentence)

        # Получаем текст параграфа из базы данных
        paragraph_text = ReportParagraph.query.filter_by(id=paragraph_id).first().paragraph

        # Проверяем каждое предложение из обработанных, есть ли оно уже в базе данных
        for sentence in sentences:
            cleaned_sentence = clean_text(sentence.strip(), key_words)
            
            if cleaned_sentence not in existing_sentences_texts:
                new_sentences.append({
                    "paragraph_id": paragraph_id,
                    "paragraph_text": paragraph_text,  # Добавляем текст параграфа
                    "sentence": sentence.strip()  # Оригинальное предложение для вывода
                })

    return new_sentences


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

