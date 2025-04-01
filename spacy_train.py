# spacy_train.py

import spacy
from spacy.tokens import DocBin
from spacy.training import Example
import json
import os
from logger import logger
import glob
import random
import datetime

MODEL_NAME = "ru_core_news_sm"
OUTPUT_DIR = "models/custom_model"


def start_spacy_retrain() -> str:
    """
    Загружает кастомную или стандартную модель SpaCy, объединяет архив и новые примеры,
    обучает модель, сохраняет её и возвращает путь к сохранённой директории.
    """

    logger.info("🧠 Старт переобучения модели SpaCy")

    # Пути к данным
    data_dir = "spacy_training_data"
    current_path = os.path.join(data_dir, "sent_boundary.jsonl")
    archive_path = os.path.join(data_dir, "sent_boundary_all.jsonl")
    training_tmp = os.path.join(data_dir, "combined_training.jsonl")

    # Собираем все данные
    combined = []
    if os.path.exists(archive_path):
        with open(archive_path, "r", encoding="utf-8") as f:
            combined += f.readlines()
    if os.path.exists(current_path):
        with open(current_path, "r", encoding="utf-8") as f:
            combined += f.readlines()

    if len(combined) < 3:
        raise ValueError("Недостаточно данных для обучения")

    # Перемешиваем
    random.shuffle(combined)

    # Сохраняем объединённый датасет
    with open(training_tmp, "w", encoding="utf-8") as f:
        f.writelines(combined)

    logger.info(f"📦 Обучение на {len(combined)} строках")

    # Загружаем последнюю кастомную модель или дефолтную
    last_model_path = None
    try:
        last_model_path = sorted(
            glob.glob("spacy_models/custom_sentencizer_v*"),
            key=os.path.getmtime,
            reverse=True
        )[0]
    except IndexError:
        logger.warning("Кастомная модель не найдена, будет использована стандартная.")

    if last_model_path:
        logger.info(f"🔄 Загружаю кастомную модель из {last_model_path}")
        nlp = spacy.load(last_model_path)
    else:
        logger.info(f"🔄 Загружаю стандартную модель {MODEL_NAME}")
        nlp = spacy.load(MODEL_NAME)

    # Загружаем датасет
    doc_bin = DocBin()
    for line in combined:
        entry = json.loads(line)
        doc = nlp.make_doc(entry["text"])
        sent_starts = entry["sent_starts"]

        if len(sent_starts) != len(doc):
            logger.warning(f"⚠️ Расхождение токенов: текст: '{entry['text'][:60]}...' "
                        f"(токенов: {len(doc)}, разметки: {len(sent_starts)})")
            continue

        for i, token in enumerate(doc):
            token.is_sent_start = sent_starts[i]

        doc_bin.add(doc)

    examples = []
    for doc in doc_bin.get_docs(nlp.vocab):
        example = Example(doc, doc)
        examples.append(example)

    # Обучаем
    nlp.initialize(get_examples=lambda: examples)
    nlp.update(examples)

    # Сохраняем модель
    model_output_path = f"spacy_models/custom_sentencizer_v{int(datetime.datetime.now().timestamp())}"
    os.makedirs(model_output_path, exist_ok=True)
    nlp.to_disk(model_output_path)

    logger.info(f"✅ Модель обучена и сохранена в {model_output_path}")

    return model_output_path