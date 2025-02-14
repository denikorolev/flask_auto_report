# utils.py

from sqlalchemy import func



def ensure_list(value):
    """Преобразует значение в список, если оно не является списком."""
    if not isinstance(value, list):
        return [value]
    return value



def get_max_index(model, filter_field, filter_value, column):
    """
    Вычисляет максимальный индекс для указанного столбца модели для текущего пользователя.

    Args:
        model (db.Model): Модель, для которой нужно вычислить максимальный индекс.
        filter_field (str): Поле, по которому фильтруются данные.
        filter_value (Any): Значение для фильтрации.
        column (db.Column): Столбец, по которому вычисляется максимальный индекс.

    Returns:
        int: Максимальный индекс или 0, если данных нет.
    """
    
    # Динамическое создание фильтра через распаковку словаря
    filter_kwargs = {filter_field: filter_value}
    
    max_index = model.query.filter_by(**filter_kwargs).with_entities(func.max(column)).scalar() or 0
    return max_index + 1


# Проверка отсутствия лишних и возможной нехватки sentence_type для предложений
def check_main_sentences(report):
    from models import Paragraph, Sentence
    errors = []
    try:
            paragraphs = Paragraph.query.filter_by(report_id=report.id).all()
            for paragraph in paragraphs:
                sentences = Sentence.query.filter_by(paragraph_id=paragraph.id).all()
                
                # Группируем предложения по index
                sentence_groups = {}
                for sentence in sentences:
                    if sentence.sentence_type == "tail":
                        if sentence.index != 0:
                            errors.append({
                                "report": report.report_name,
                                "paragraph": paragraph.paragraph,
                                "paragraph_index": paragraph.paragraph_index,
                                "index": sentence.index,
                                "issue": "Предложение с типом 'tail' должно иметь индекс 0",
                                "extra_main_count": 0
                            })
                        else:
                            continue
                    if sentence.index not in sentence_groups:
                        sentence_groups[sentence.index] = []
                    sentence_groups[sentence.index].append(sentence)

                # Проверяем каждую группу предложений
                for index, group in sentence_groups.items():
                    if index == 0:
                        main_sentences = [s for s in group if s.sentence_type == "head"]
                        body_sentences = [s for s in group if s.sentence_type == "body"]
                        if len(main_sentences) + len(body_sentences) > 0:
                            errors.append({
                                "report": report.report_name,
                                "paragraph": paragraph.paragraph,
                                "paragraph_index": paragraph.paragraph_index,
                                "index": index,
                                "issue": "Главное предложение и обычные предложения не должны иметь индекс 0",
                                "extra_main_count": len(main_sentences) + len(body_sentences)
                            })
                        continue
                    main_sentences = [s for s in group if s.sentence_type == "head"]
                    # Должно быть ровно одно главное предложение
                    if len(main_sentences) == 0:
                        errors.append({
                            "report": report.report_name,
                            "paragraph": paragraph.paragraph,
                            "paragraph_index": paragraph.paragraph_index,
                            "index": index,
                            "issue": "Не определено главное предложение для данной группы",
                            "extra_main_count": 0
                        })
                    elif len(main_sentences) > 1:
                        errors.append({
                            "report": report.report_name,
                            "paragraph": paragraph.paragraph,
                            "paragraph_index": paragraph.paragraph_index,
                            "index": index,
                            "issue": "Слишком много главных предложений",
                            "extra_main_count": len(main_sentences) - 1
                        })

            return errors

    except Exception as e:
        errors = [
            {
                "report": report.report_name,
                "paragraph": "Ошибка",
                "paragraph_index": "Ошибка",
                "index": "Ошибка",
                "issue": e,
                "extra_main_count": "Ошибка"
            }
        ]
        return str(e)
    


