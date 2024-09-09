# sentence_processing.py

from flask_login import current_user
import re
from models import Sentence, ReportParagraph, KeyWordsGroup

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
    user_key_words = KeyWordsGroup.find_by_user_id(current_user.id)
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
    """ Сортировка групп ключевых слов по первой букве ключевого слова """
    key_words_group_with_first_letter = []
    
    for group_index, group_data in unsorted_key_words_group.items():
        keywords = group_data.get("keywords", [])
        if keywords and keywords[0]["key_word"]:  # Проверяем, что ключевые слова существуют
            first_letter = keywords[0]["key_word"].lower()  # Получаем первую букву первого ключевого слова
        else:
            first_letter = ""  # Если ключевых слов нет, используем пустую строку

        # Добавляем первую букву и саму группу данных для сортировки
        key_words_group_with_first_letter.append((first_letter, group_data))

    # Сортируем список по первой букве
    sorted_key_words_group = sorted(key_words_group_with_first_letter, key=lambda x: x[0])

    # Извлекаем только отсортированные группы (без первой буквы)
    return [group_data for _, group_data in sorted_key_words_group]



def group_key_words_by_index(user_id, report_ids=None):
    """ Ищем ключевые слова для данного пользователя, группируем их по group_index
    и включаем информацию о связанных отчетах. Если нет связи с отчетами, добавляем None.
    
    Args:
        user_id (int): Идентификатор пользователя.
        report_ids (list): Список идентификаторов отчетов, с которыми связаны ключевые слова (может быть пустым или None).
    
    Returns:
        list: Отсортированный список групп ключевых слов с информацией о связанных отчетах.
    """
    unsorted_key_words_group = {}

    # Обрабатываем ключевые слова для каждого отчета
    if report_ids:
        for report_id in report_ids:
            if isinstance(report_id, KeyWordsGroup):
                report_id = report_id.id
            else:
                # Получаем ключевые слова, связанные с конкретным отчетом
                keywords_linked_to_report = KeyWordsGroup.find_by_report(report_id)
                
                if not keywords_linked_to_report:
                    continue  # Пропускаем, если для отчета нет связанных ключевых слов

                for key_word in keywords_linked_to_report:
                    if key_word.group_index not in unsorted_key_words_group:
                        unsorted_key_words_group[key_word.group_index] = {
                            "keywords": [],
                            "linked_reports": []
                        }

                    unsorted_key_words_group[key_word.group_index]["keywords"].append({
                        'key_word': key_word.key_word,
                        'group_index': key_word.group_index,
                        'index': key_word.index
                    })

                    # Добавляем отчет, с которым связана группа ключевых слов
                    if report_id not in unsorted_key_words_group[key_word.group_index]["linked_reports"]:
                        unsorted_key_words_group[key_word.group_index]["linked_reports"].append(report_id)
    
    # Получаем ключевые слова без отчетов
    keywords_without_reports = KeyWordsGroup.find_without_reports(user_id)
    
    for key_word in keywords_without_reports:
        if key_word.group_index not in unsorted_key_words_group:
            unsorted_key_words_group[key_word.group_index] = {
                "keywords": [],
                "linked_reports": []
            }

        unsorted_key_words_group[key_word.group_index]["keywords"].append({
            'key_word': key_word.key_word,
            'group_index': key_word.group_index,
            'index': key_word.index
        })

    # Сортировка групп ключевых слов
    key_words_group = sort_key_words_group(unsorted_key_words_group)
    print(key_words_group)

    return key_words_group
