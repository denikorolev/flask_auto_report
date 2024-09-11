# sentence_processing.py
#v0.1.2

from flask_login import current_user
import re
from models import Sentence, ReportParagraph, KeyWordsGroup, Report, User
from collections import defaultdict

def clean_text(sentence, key_words):
    """ Функция очистки текста от пробелов, знаков припенания и 
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
    """ Сортировка групп ключевых слов по первой букве первого ключевого слова в группе """
    key_words_group_with_first_letter = []

    for group_data in unsorted_key_words_group:
        key_words = group_data.get("key_words", [])
        if key_words:
            first_letter = key_words[0][0].lower()  # Получаем первую букву первого ключевого слова
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
        list of dict: Список словарей с ключами group_index и key_words.
    with_index=False:
        list of lists: Список списков с отсортированными по group_index ключевыми словами.
    with_report=True:
        list of dict: Список словарей, где ключи report_id, report_name, group_index и key_words.
    """

    if with_report:
        report_key_words = defaultdict(lambda: {'report_name': '', 'key_words': [], 'group_indexes': set()})

        for keyword in keywords:
            # Проверяем, связан ли ключ с отчетом
            for report in keyword.key_word_reports:
                report_data = report_key_words[report.id]
                report_data['report_name'] = report.report_name
                report_data['key_words'].append(keyword.key_word)
                report_data['group_indexes'].add(keyword.group_index)  # Добавляем group_index
                
        # Преобразуем defaultdict в обычный список словарей, где group_indexes преобразуются в список
        return [{'report_id': report_id, 
                 'report_name': data['report_name'], 
                 'key_words': data['key_words'], 
                 'group_indexes': list(data['group_indexes'])} 
                for report_id, data in report_key_words.items()]
    
    # Группируем ключевые слова по group_index
    grouped_keywords = defaultdict(list)
    for keyword in keywords:
        grouped_keywords[keyword.group_index].append(keyword.key_word)
    
    # Если with_index=True, возвращаем список словарей с group_index
    if with_index:
        grouped_keywords_with_index = []
        for group_index, words in grouped_keywords.items():
            grouped_keywords_with_index.append({'group_index': group_index, 'key_words': words})
        return grouped_keywords_with_index
    
    # Если with_index=False, возвращаем просто сгруппированные ключевые слова
    return list(grouped_keywords.values())

