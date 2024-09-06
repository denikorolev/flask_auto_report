# sentence_processing.py

from flask_login import current_user
import re
from models import Sentence, ReportParagraph, KeyWordsGroup


def clean_text(sentence, key_words):
    """ Функция очистки текста от пробелов, знаков припенания и ключевых слов с приведением всех слов предложения к нижнему регистру """
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
    """ Разделяем полученный текст на отдельные предложения ориентируясь на знаки припенания .!? """
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
    """ Получаем только новые предложения, игнорируя те, что уже есть в базе данных, учитываем возможную разницу лишь в ключевых словах key_words """
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
