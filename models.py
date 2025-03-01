# models.py

from flask_sqlalchemy import SQLAlchemy
from flask_security import UserMixin, RoleMixin
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy import Index, event
from utils import ensure_list
from datetime import datetime, timezone  # Добавим для временных меток
import json
from logger import logger


db = SQLAlchemy()

# Проверяет перед удалением группы предложений, можно ли её удалить
def prevent_group_deletion(mapper, connection, target):
    """
    Проверяет перед удалением группы предложений, можно ли её удалить.
    Если группа всё ещё используется, прерывает удаление.
    """
    logger.info("Стартовала надстройка для контроля возможности удаления группы предложений")
    if isinstance(target, HeadSentenceGroup):
        # Проверяем, есть ли параграфы, использующие эту группу
        used_in_paragraphs = Paragraph.query.filter_by(head_sentence_group_id=target.id).count()
        if used_in_paragraphs > 0:
            raise Exception(f"Группа HeadSentenceGroup (ID={target.id}) всё ещё используется в параграфах, удаление отменено.")
    
    elif isinstance(target, TailSentenceGroup):
        # Проверяем, есть ли параграфы, использующие эту группу
        used_in_paragraphs = Paragraph.query.filter_by(tail_sentence_group_id=target.id).count()
        if used_in_paragraphs > 0:
            raise Exception(f"Группа TailSentenceGroup (ID={target.id}) всё ещё используется в параграфах, удаление отменено.")
    
    elif isinstance(target, BodySentenceGroup):
        # Проверяем, есть ли предложения, использующие эту группу
        used_in_head_sentences = HeadSentence.query.filter_by(body_sentence_group_id=target.id).count()
        if used_in_head_sentences > 0:
            raise Exception(f"Группа BodySentenceGroup (ID={target.id}) всё ещё используется в head-предложениях, удаление отменено.")





sentence_type_enum = ENUM(
    "head", "body", "tail",
    name="sentence_type_enum",
    create_type=True  # Создаст тип в PostgreSQL
)

paragraph_type_enum = ENUM(
    "text", "custom", "impression", "clincontext", 
    "scanparam", "dinamics", "scanlimits", "title",
    name="paragraph_type_enum",
    create_type=True  # Создаст тип в PostgreSQL
)



# Ассоциативная таблица для связи ключевых слов с отчетами
key_word_report_link = db.Table(
    'key_word_report_link',
    db.Column('key_word_id', db.BigInteger, db.ForeignKey('key_words_group.id', ondelete="CASCADE"), primary_key=True),
    db.Column('report_id', db.BigInteger, db.ForeignKey('reports.id', ondelete="CASCADE"), primary_key=True),
    Index('ix_key_word_report_link_keyword_report', 'key_word_id', 'report_id')
)

# Ассоциативная таблица для связи пользователей и ролей
roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.BigInteger, db.ForeignKey('users.id', ondelete="CASCADE"), primary_key=True),
    db.Column('role_id', db.BigInteger, db.ForeignKey('roles.id', ondelete="CASCADE"), primary_key=True),
    Index('ix_roles_users_user_id_role_id', 'user_id', 'role_id')
)


# Ассоциативная таблица для связи head предложений с группой head предложений   
head_sentence_group_link = db.Table(
    "head_sentence_group_link",
    db.Column("head_sentence_id", db.BigInteger, db.ForeignKey("head_sentences.id", ondelete="CASCADE"), primary_key=True),
    db.Column("group_id", db.BigInteger, db.ForeignKey("head_sentence_groups.id", ondelete="CASCADE"), primary_key=True),
    db.Index("ix_head_sentence_group", "head_sentence_id", "group_id")
)

# Ассоциативная таблица для связи body предложений с группой body предложений
body_sentence_group_link = db.Table(
    "body_sentence_group_link",
    db.Column("body_sentence_id", db.BigInteger, db.ForeignKey("body_sentences.id", ondelete="CASCADE"), primary_key=True),
    db.Column("group_id", db.BigInteger, db.ForeignKey("body_sentence_groups.id", ondelete="CASCADE"), primary_key=True),
    db.Index("ix_body_sentence_group", "body_sentence_id", "group_id")
)

# Ассоциативная таблица для связи tail предложений с группой tail предложений
tail_sentence_group_link = db.Table(
    "tail_sentence_group_link",
    db.Column("tail_sentence_id", db.BigInteger, db.ForeignKey("tail_sentences.id", ondelete="CASCADE"), primary_key=True),
    db.Column("group_id", db.BigInteger, db.ForeignKey("tail_sentence_groups.id", ondelete="CASCADE"), primary_key=True),
    db.Index("ix_tail_sentence_group", "tail_sentence_id", "group_id")
)



class AppConfig(db.Model):
    __tablename__ = 'app_config'
    __table_args__ = (db.UniqueConstraint("profile_id", "config_key", name="uq_profile_config"),)
    
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.BigInteger, db.ForeignKey('user_profiles.id', ondelete="CASCADE"), nullable=False) 
    config_key = db.Column(db.String(50), nullable=False)
    config_value = db.Column(db.String(200), nullable=False)
    config_type = db.Column(db.String(50), nullable=True)  # необязательный
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)  
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)  


    @staticmethod
    def get_setting(profile_id, key, default=None):
        """Возвращает значение настройки для профиля."""
        try:
            config = AppConfig.query.filter_by(profile_id=profile_id, config_key=key).first()
            return config.config_value if config else default
        except Exception as e:
            print(f"Ошибка получения настройки: {e}")
            return default
    

    @staticmethod
    def set_setting(profile_id, key, value):
        """
        Устанавливает или обновляет значение настройки для указанного профиля и ключа.
        Автоматически определяет тип и выполняет нужные преобразования.

        Args:
            profile_id (int): ID профиля.
            key (str): Ключ настройки.
            value (Any): Значение настройки (любого типа).
        """
        # Определяем тип данных
        if isinstance(value, bool):
            config_type = "boolean"
            value = str(value).lower()  # True → "true", False → "false"
        elif isinstance(value, int):
            config_type = "integer"
            value = str(value)
        elif isinstance(value, float):
            config_type = "float"
            value = str(value)
        elif isinstance(value, (dict, list)):
            config_type = "json"
            value = json.dumps(value, ensure_ascii=False)  # Храним JSON строкой
        else:
            config_type = "string"
            value = str(value)

        try:
            # Ищем существующую настройку
            config = AppConfig.query.filter_by(profile_id=profile_id, config_key=key).first()

            if config:
                # Обновляем существующую настройку
                config.config_value = value
                config.config_type = config_type
            else:
                # Создаем новую настройку
                config = AppConfig(
                    profile_id=profile_id,
                    config_key=key,
                    config_value=value,
                    config_type=config_type
                )
                db.session.add(config)

            db.session.commit()
        except Exception as e:
            print(f"Ошибка при сохранении настройки ({key}): {e}")
            db.session.rollback()
            return False
        return True


class BaseModel(db.Model):
    __abstract__ = True
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def delete_by_id(cls, object_id):
        obj = cls.query.get(object_id)
        if obj:
            obj.delete()
            return True
        return False

    @classmethod
    def get_by_id(cls, object_id):
        return cls.query.get(object_id)


class Role(db.Model, RoleMixin):
    __tablename__ = 'roles'
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)  
    description = db.Column(db.String(255), nullable=True) 
    rank = db.Column(db.Integer, nullable=False)  


class User(BaseModel, db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.BigInteger, primary_key=True)
    user_name = db.Column(db.String, nullable=False, default="User")
    password = db.Column(db.String, nullable=False)
    user_bio = db.Column(db.Text, nullable=True)
    user_avatar = db.Column(db.LargeBinary, nullable=True)
    active = db.Column(db.Boolean, default=True, nullable=False)
    fs_uniquifier = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    confirmed_at = db.Column(db.DateTime, nullable=True)  # Время подтверждения email
    last_login_at = db.Column(db.DateTime, nullable=True)  # Последняя авторизация
    current_login_at = db.Column(db.DateTime, nullable=True)  # Текущая авторизация
    last_login_ip = db.Column(db.String(45), nullable=True)  # Последний IP-адрес
    current_login_ip = db.Column(db.String(45), nullable=True)  # Текущий IP-адрес
    login_count = db.Column(db.Integer, default=0, nullable=False)  # Счетчик входов



    roles = db.relationship(
        'Role',
        secondary=roles_users,
        backref=db.backref('users', lazy='dynamic')
    )
    user_to_profiles = db.relationship('UserProfile', lazy="joined", backref=db.backref("profile_to_user"), cascade="all, delete-orphan")
    user_to_reports = db.relationship('Report', lazy=True)


    def get_max_rank(self):
        """
        Возвращает максимальный ранг пользователя на основе его ролей.
        
        Returns:
            int: Максимальный ранг пользователя, если роли есть.
            None: Если у пользователя нет ролей.
        """
        if not self.roles:
            return None  # У пользователя нет ролей
        return max(role.rank for role in self.roles if role.rank is not None)
    

    def has_role(self, role_name):
        """Проверяет, есть ли у пользователя определенная роль."""
        return any(role.name == role_name for role in self.roles)


    def add_role(self, role_name):
        """Добавляет роль пользователю, если её еще нет."""
        role = Role.query.filter_by(name=role_name).first()
        if role and role not in self.roles:
            self.roles.append(role)
            db.session.commit()


class UserProfile(BaseModel):
    __tablename__ = 'user_profiles'
    
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    profile_name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    default_profile = db.Column(db.Boolean, default=False, nullable=False)
    
    profile_to_configs = db.relationship("AppConfig", lazy=True, backref="profile", cascade="all, delete-orphan")
    profile_to_reports = db.relationship('Report', lazy=True, backref=db.backref("report_to_profile"), cascade="all, delete-orphan")
    profile_to_files = db.relationship("FileMetadata", lazy=True, backref=db.backref("file_to_profile"), cascade="all, delete-orphan")
    profile_to_key_words = db.relationship("KeyWord", lazy=True, backref=db.backref("key_word_to_profile"), cascade="all, delete-orphan")
    profile_to_report_types = db.relationship("ReportType", lazy=True, backref=db.backref("report_type_to_profile"), cascade="all, delete-orphan")

    @classmethod
    def create(cls, user_id, profile_name, description=None, default_profile=False):
        """
        Создание нового профиля.
        Args:
            user_id (int): ID пользователя.
            profile_name (str): Имя профиля.
            description (str, optional): Описание профиля. Defaults to None.
            default (bool, optional): Является ли профиль профилем по умолчанию. Defaults to False.
        
        Raises:
            ValueError: Если профиль по умолчанию уже существует для данного пользователя.
        """
        if default_profile:
            existing_default_profile = cls.get_default_profile(user_id)
            if existing_default_profile:
                existing_default_profile.default_profile = False
        
        new_profile = cls(
            user_id=user_id,
            profile_name=profile_name,
            description=description,
            default_profile=default_profile
        )
        new_profile.save()  
        return new_profile
        
    @classmethod
    def get_default_profile(cls, user_id):
        """
        Возвращает профиль по умолчанию для пользователя.
        Args:
            user_id (int): ID пользователя.
        Returns:
            UserProfile: Профиль по умолчанию или None, если его нет.
        """
        return cls.query.filter_by(user_id=user_id, default_profile=True).first() or None


    @classmethod
    def get_user_profiles(cls, user_id):
        """Возвращает все профили, принадлежащие пользователю."""
        return cls.query.filter_by(user_id=user_id).all()
    
    @classmethod
    def find_by_id_and_user(cls, profile_id, user_id):
        """Ищет профиль по его ID и ID пользователя."""
        return cls.query.filter_by(id=profile_id, user_id=user_id).first()


class ReportType(BaseModel):
    __tablename__ = 'report_type'
    profile_id = db.Column(db.BigInteger, db.ForeignKey('user_profiles.id'), nullable=False)
    type_text = db.Column(db.String(50), nullable=False)
    type_index = db.Column(db.Integer, nullable=False)
    
    type_to_subtypes = db.relationship("ReportSubtype", lazy=True, backref=db.backref("subtype_to_type"), cascade="all, delete-orphan")
    
    @classmethod
    def create(cls, type_text, profile_id, type_index=None):
        """
        Creates a new report type.
        
        Args:
            type (str): The type of the report.
            profile_id (int): The ID of the user creating the report type.
            type_index (int, optional): The index of the type. If not provided, it will be set automatically.

        Returns:
            ReportType: The newly created report type object.
        """
        # If type_index is not provided, set it to the next available index
        if type_index is None:
            max_index = db.session.query(db.func.max(cls.type_index)).scalar() or 0
            type_index = max_index + 1

        new_type = cls(
            type_text=type_text,
            profile_id=profile_id,
            type_index=type_index
        )
        db.session.add(new_type)
        db.session.commit()
        return new_type
    
    @classmethod
    def find_by_profile(cls, profile_id):
        """
        Find all report types created by a specific user.
        """
        return cls.query.filter_by(profile_id=profile_id).all()
    
    @classmethod
    def get_types_with_subtypes(cls, profile_id):
        """
        Собирает список словарей с типами и их подтипами для указанного пользователя.
        Args:
            user_id (int): ID пользователя.
        Returns:
            list: Список словарей с типами и подтипами.
        """
        types = cls.query.filter_by(profile_id=profile_id).all()
        result = []
        
        for report_type in types:
            subtypes = [
                {
                    "subtype_id": subtype.id,
                    "subtype_text": subtype.subtype_text
                } 
                for subtype in report_type.type_to_subtypes
            ]
            result.append({
                "type_id": report_type.id,
                "type_text": report_type.type_text,
                "subtypes": subtypes
            })
        return result


class ReportSubtype(BaseModel):
    __tablename__ = "report_subtype"
    type_id = db.Column(db.SmallInteger, db.ForeignKey("report_type.id"), nullable=False)
    subtype_text = db.Column(db.String(250), nullable=False)
    subtype_index = db.Column(db.Integer, nullable=False)
    
    subtype_to_reports = db.relationship('Report', lazy=True, backref=db.backref("report_to_subtype"), cascade="all, delete-orphan")
    
    @classmethod
    def create(cls, type_id, subtype_text, subtype_index=None): # subtype_index должен быть None чтобы ниже зайти в if и вычислить его
        """
        Creates a new report subtype.

        Args:
            type (int): The ID of the report type.
            subtype (str): The subtype text.
            subtype_index (int, optional): The index of the subtype. If not provided, it will be set automatically.

        Returns:
            ReportSubtype: The newly created report subtype object.
        """
        # If subtype_index is not provided, set it to the next available index
        if subtype_index is None:
            max_index = db.session.query(db.func.max(cls.subtype_index)).scalar() or 0
            subtype_index = max_index + 1

        new_subtype = cls(
            type_id=type_id,
            subtype_text=subtype_text,
            subtype_index=subtype_index
        )
        db.session.add(new_subtype)
        db.session.commit()
        return new_subtype
    
    @classmethod
    def find_by_report_type(cls, type_id):
        """Возвращает все подтипы, связанные с профилем."""
        return cls.query.filter_by(type_id=type_id).all()


class Report(BaseModel):
    __tablename__ = "reports"
    profile_id = db.Column(db.BigInteger, db.ForeignKey('user_profiles.id'), nullable=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    report_subtype = db.Column(db.Integer, db.ForeignKey('report_subtype.id'), nullable=False)
    comment = db.Column(db.String(255), nullable=True)
    report_name = db.Column(db.String(255), nullable=False)
    public = db.Column(db.Boolean, default=False, nullable=False)
    report_side = db.Column(db.Boolean, nullable=False, default=False)
    
   
    report_to_paragraphs = db.relationship('Paragraph', lazy=True, backref=db.backref("paragraph_to_report"), cascade="all, delete-orphan")

    
    @classmethod
    def create(cls, profile_id, report_subtype, report_name,  user_id, comment=None, public=False, report_side=False):
        new_report = cls(
            profile_id=profile_id,
            report_subtype=report_subtype,
            report_name=report_name,
            user_id=user_id,
            comment=comment,
            public=public,
            report_side=report_side
        )
        db.session.add(new_report)
        db.session.commit()
        return new_report
    
    
    @classmethod
    def find_by_profile(cls, profile_id):
        """Возвращает все отчеты, связанные с данным профилем."""
        return cls.query.filter_by(profile_id=profile_id).all()
    
    
    @classmethod
    def get_report_type (cls, report_id):
        """Возвращает тип отчета"""
        report = cls.query.filter_by(id=report_id).first()
        return report.report_to_subtype.subtype_to_type.id
    
    
    @classmethod
    def find_by_subtypes(cls, report_subtype):
        """Возвращает все отчеты, связанные с данным подтипом"""
        return cls.query.filter_by(report_subtype=report_subtype).all()
    
    
    @classmethod
    def get_report_data(cls, report_id, profile_id):
        """
        Возвращает кортеж данных отчета:
        1) Словарь с основной информацией об отчете.
        2) Словарь параграфов, сгруппированных по типу и индексу, с head_sentence (группировка по index) и tail_sentence.
        Args:
            report_id (int): ID отчета.
            profile_id (int): ID профиля пользователя.
        Returns:
            tuple: (dict, dict) - (report_data, paragraphs_by_type)
        """
        # Ищем отчет по ID и профилю
        logger.info(f"Получил данные report_id: {report_id}, profile_id: {profile_id} начинаю выборку данных протокола")
        report = cls.query.filter_by(id=report_id, profile_id=profile_id).first()
        if not report:
            return None, None  # Если отчет не найден или принадлежит другому пользователю

        # Формируем словарь с основной информацией об отчете
        report_data = {
            "id": report.id,
            "report_name": report.report_name,
            "report_type": report.report_to_subtype.subtype_to_type.type_text,
            "report_subtype": report.report_to_subtype.subtype_text,
            "comment": report.comment,
            "report_side": report.report_side,
            "user_id": report.user_id,
            "report_public": report.public
        }

        # Получаем все параграфы отчета и группируем их по типу и индексу
        paragraphs = Paragraph.query.filter_by(report_id=report_id).all()

        paragraphs_by_type = {}
        for paragraph in sorted(paragraphs, key=lambda p: p.paragraph_index):
            paragraph_type = paragraph.paragraph_type

            # Получаем head-предложения через HeadSentenceGroup
            head_sentence = {}
            if paragraph.head_sentence_group_id:
                head_sentence_group = HeadSentenceGroup.query.get(paragraph.head_sentence_group_id)
                if head_sentence_group:
                    sorted_head_sentences = sorted(head_sentence_group.head_sentences, key=lambda s: s.sentence_index)
                    for sentence in sorted_head_sentences:
                        index = sentence.sentence_index

                        # Получаем body-предложения через body_sentence_group у каждого head
                        body_sentences = []
                        if sentence.body_sentence_group:
                            body_sentences = [{
                                "id": body_sentence.id,
                                "weight": body_sentence.sentence_weight,
                                "comment": body_sentence.comment,
                                "sentence": body_sentence.sentence,
                                "tags": body_sentence.tags
                            } for body_sentence in sentence.body_sentence_group.body_sentences]

                        
                        head_sentence[index] = {
                            "id": sentence.id,
                            "index": index,
                            "comment": sentence.comment,
                            "sentence": sentence.sentence,
                            "tags": sentence.tags,
                            "body_sentences": body_sentences  
                        }

            # Получаем tail-предложения через TailSentenceGroup
            tail_sentence = []
            if paragraph.tail_sentence_group_id:
                tail_sentence_group = TailSentenceGroup.query.get(paragraph.tail_sentence_group_id)
                if tail_sentence_group:
                    tail_sentence = [{
                        "id": sentence.id,
                        "weight": sentence.sentence_weight,
                        "comment": sentence.comment,
                        "sentence": sentence.sentence,
                        "tags": sentence.tags
                    } for sentence in tail_sentence_group.tail_sentences]

            # Формируем данные по параграфу
            paragraph_data = {
                "id": paragraph.id,
                "paragraph_index": paragraph.paragraph_index,
                "paragraph": paragraph.paragraph,
                "paragraph_visible": paragraph.paragraph_visible,
                "title_paragraph": paragraph.title_paragraph,
                "bold_paragraph": paragraph.bold_paragraph,
                "paragraph_type": paragraph_type,
                "paragraph_comment": paragraph.comment,
                "paragraph_weight": paragraph.paragraph_weight,
                "tags": paragraph.tags,
                "head_sentences": head_sentence,  
                "tail_sentences": tail_sentence  
            }

            # Группируем параграфы по типу
            if paragraph_type not in paragraphs_by_type:
                paragraphs_by_type[paragraph_type] = {}

            # Группируем параграфы внутри типа по index
            paragraphs_by_type[paragraph_type][paragraph.paragraph_index] = paragraph_data

           
        logger.info(f"Получил данные report_id: {report_id}, profile_id: {profile_id} возвращаю данные протокола")
        return report_data, paragraphs_by_type
    
    
    @classmethod
    def get_report_info(cls, report_id, profile_id):
        """
        Получает основные данные отчета.
        Args:
            report_id (int): ID отчета.
            profile_id (int): ID профиля пользователя.
        Returns:
            dict: Словарь с информацией об отчете или None, если отчет не найден.
        """
        logger.info(f"Запрос данных отчета: report_id={report_id}, profile_id={profile_id}")
        
        report = cls.query.filter_by(id=report_id, profile_id=profile_id).first()
        if not report:
            return None  # Если отчет не найден или принадлежит другому пользователю

        report_data = {
            "id": report.id,
            "report_name": report.report_name,
            "report_type": report.report_to_subtype.subtype_to_type.type_text,
            "report_subtype": report.report_to_subtype.subtype_text,
            "comment": report.comment,
            "report_side": report.report_side,
            "user_id": report.user_id,
            "report_public": report.public
        }
        logger.info(f"Получил данные отчета: report_id={report_id}, profile_id={profile_id}. Возвращаю данные")
        return report_data
    
    
    @classmethod
    def get_report_data(cls, report_id, profile_id):
        """
        Возвращает основные данные отчета и список параграфов.
        Args:
            report_id (int): ID отчета.
            profile_id (int): ID профиля пользователя.
        Returns:
            tuple: (dict, list) - (report_data, sorted_paragraphs)
        """
        try:
            report_data = cls.get_report_info(report_id, profile_id)
        except Exception as e:
            logger.error(f"Ошибка при получении данных отчета: {e}")
            raise e
        
        if report_data is None:
            logger.error(f"Отчет не найден: report_id={report_id}, profile_id={profile_id}")
            return None, None
        try:
            sorted_paragraphs = Paragraph.get_report_paragraphs(report_id)
        except Exception as e:
            logger.error(f"Ошибка при получении параграфов отчета: {e}")
            raise e
        logger.info(f"Получил обобщенные данные отчета: report_id={report_id}. Возвращаю.")
        return report_data, sorted_paragraphs
    
    
    # Упрощенная версия метода get_report_data для получения легковесной структуры отчета для использования в edit_report
    @classmethod
    def get_report_structure(cls, report_id, profile_id):
        """
        Возвращает структуру отчета: список параграфов с их head-предложениями.
        Args:
            report_id (int): ID отчета.
            profile_id (int): ID профиля пользователя.
        Returns:
            list: Отсортированный список параграфов, где head_sentences содержат только id, index и sentence.
        """
        logger.info(f"Получение структуры отчета: report_id={report_id}, profile_id={profile_id}")

        report = cls.query.filter_by(id=report_id, profile_id=profile_id).first()
        if not report:
            return None  # Если отчет не найден или принадлежит другому пользователю

        paragraphs = Paragraph.query.filter_by(report_id=report_id).order_by(Paragraph.paragraph_index).all()
        report_structure = []

        for paragraph in paragraphs:
            head_sentences = []
            if paragraph.head_sentence_group_id:
                head_sentence_group = HeadSentenceGroup.query.get(paragraph.head_sentence_group_id)
                if head_sentence_group:
                    head_sentences = sorted(
                        [{"id": s.id, "index": s.sentence_index, "sentence": s.sentence} for s in head_sentence_group.head_sentences],
                        key=lambda s: s["index"]
                    )

            report_structure.append({
                "id": paragraph.id,
                "paragraph_index": paragraph.paragraph_index,
                "paragraph": paragraph.paragraph,
                "paragraph_visible": paragraph.paragraph_visible,
                "title_paragraph": paragraph.title_paragraph,
                "bold_paragraph": paragraph.bold_paragraph,
                "paragraph_type": paragraph.paragraph_type,
                "paragraph_comment": paragraph.comment,
                "paragraph_weight": paragraph.paragraph_weight,
                "tags": paragraph.tags,
                "head_sentences": head_sentences  # Только id, index, sentence
            })

        return report_structure
    
    
class Paragraph(BaseModel):
    __tablename__ = "report_paragraphs"
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    report_id = db.Column(db.BigInteger, db.ForeignKey("reports.id"), nullable=False)
    paragraph_type = db.Column(paragraph_type_enum, nullable=True, default="text")
    paragraph_index = db.Column(db.Integer, nullable=False)
    paragraph = db.Column(db.String(255), nullable=False)
    paragraph_visible = db.Column(db.Boolean, default=False, nullable=False)
    title_paragraph = db.Column(db.Boolean, default=False, nullable=False)
    bold_paragraph = db.Column(db.Boolean, default=False, nullable=False)
    comment = db.Column(db.String(255), nullable=True)
    paragraph_weight = db.Column(db.SmallInteger, nullable=False) 
    tags = db.Column(db.String(255), nullable=True)
    head_sentence_group_id = db.Column(db.BigInteger, db.ForeignKey("head_sentence_groups.id", ondelete="SET NULL"))
    tail_sentence_group_id = db.Column(db.BigInteger, db.ForeignKey("tail_sentence_groups.id", ondelete="SET NULL"))

    paragraph_to_sentences = db.relationship("Sentence", lazy=True, backref=db.backref("sentence_to_paragraph"), cascade="all, delete-orphan")
    head_sentence_group = db.relationship("HeadSentenceGroup", backref="paragraphs")
    tail_sentence_group = db.relationship("TailSentenceGroup", backref="paragraphs")
    
    
    def delete(self):
        """
        Удаляет параграф и сразу удаляет связанные группы head/tail.
        Если группа больше нигде не используется, она удалится триггером.
        Если группа ещё нужна, триггер отменит её удаление.
        """
        # if self.head_sentence_group:
        #     db.session.delete(self.head_sentence_group)  # Попытка удалить head-группу

        # if self.tail_sentence_group:
        #     db.session.delete(self.tail_sentence_group)  # Попытка удалить tail-группу

        db.session.delete(self)
        db.session.commit()
    
    # Метод нужен для переноса протоколов из старой логики в новую
    def get_paragraph_sentences_grouped_by_type(self):
        """
        Возвращает предложения данного параграфа, сгруппированные по их типам.
        
        Returns:
            dict: {
                "head": [Sentence, ...],
                "body": [Sentence, ...],
                "tail": [Sentence, ...]
            }
        """
        sentences = Sentence.query.filter_by(paragraph_id=self.id).all()
        
        grouped_sentences = {
            "head": [],
            "body": [],
            "tail": []
        }
        
        for sentence in sentences:
            sentence_type = sentence.sentence_type
            if sentence_type in grouped_sentences:
                grouped_sentences[sentence_type].append(sentence)
        
        return grouped_sentences
    
    
    @classmethod
    def create(cls, 
               report_id, 
               paragraph_index, 
               paragraph, 
               paragraph_type = "text", 
               paragraph_visible=True, 
               title_paragraph=False, 
               bold_paragraph=False, 
               paragraph_weight=1, 
               tags=None, 
               comment=None, 
               head_sentence_group_id = None, 
               tail_sentence_group_id = None
        ):
        """
        Создает новый параграф.
        """
        new_paragraph = cls(
            report_id=report_id,
            paragraph_index=paragraph_index,
            paragraph=paragraph,
            paragraph_type=paragraph_type,
            paragraph_visible=paragraph_visible,
            title_paragraph=title_paragraph,
            bold_paragraph=bold_paragraph,
            paragraph_weight=paragraph_weight,
            tags=tags,
            comment=comment,
            head_sentence_group_id=head_sentence_group_id,
            tail_sentence_group_id=tail_sentence_group_id
        )
        db.session.add(new_paragraph)
        db.session.commit()
        return new_paragraph
    
    # Метод для получения параграфов отчета, отсортированных 
    # по index (использю его в методе get_report_data)
    @classmethod
    def get_report_paragraphs(cls, report_id):
        """
        Получает список параграфов отчета, отсортированных по index.
        Args:
            report_id (int): ID отчета.
        Returns:
            list: Список параграфов, отсортированных по index.
        """
        logger.info(f"Запрос параграфов для отчета: report_id={report_id}")

        paragraphs = Paragraph.query.filter_by(report_id=report_id).all()
        sorted_paragraphs = []

        for paragraph in sorted(paragraphs, key=lambda p: p.paragraph_index):
            # Получаем head-предложения, сортируем по index
            head_sentences = []
            if paragraph.head_sentence_group_id:
                head_sentence_group = HeadSentenceGroup.query.get(paragraph.head_sentence_group_id)
                if head_sentence_group:
                    for sentence in sorted(head_sentence_group.head_sentences, key=lambda s: s.sentence_index):
                        # Получаем body-предложения, сортируем по weight
                        body_sentences = sorted(
                            [{
                                "id": body_sentence.id,
                                "weight": body_sentence.sentence_weight,
                                "comment": body_sentence.comment,
                                "sentence": body_sentence.sentence,
                                "tags": body_sentence.tags
                            } for body_sentence in sentence.body_sentence_group.body_sentences],
                            key=lambda s: s["weight"]
                        ) if sentence.body_sentence_group else []

                        head_sentences.append({
                            "id": sentence.id,
                            "index": sentence.sentence_index,
                            "comment": sentence.comment,
                            "sentence": sentence.sentence,
                            "tags": sentence.tags,
                            "body_sentences": body_sentences
                        })

            # Получаем tail-предложения, сортируем по weight
            tail_sentences = sorted(
                [{
                    "id": sentence.id,
                    "weight": sentence.sentence_weight,
                    "comment": sentence.comment,
                    "sentence": sentence.sentence,
                    "tags": sentence.tags
                } for sentence in TailSentenceGroup.query.get(paragraph.tail_sentence_group_id).tail_sentences],
                key=lambda s: s["weight"]
            ) if paragraph.tail_sentence_group_id else []

            # Формируем данные по параграфу
            paragraph_data = {
                "id": paragraph.id,
                "paragraph_index": paragraph.paragraph_index,
                "paragraph": paragraph.paragraph,
                "paragraph_visible": paragraph.paragraph_visible,
                "title_paragraph": paragraph.title_paragraph,
                "bold_paragraph": paragraph.bold_paragraph,
                "paragraph_type": paragraph.paragraph_type,
                "paragraph_comment": paragraph.comment,
                "paragraph_weight": paragraph.paragraph_weight,
                "tags": paragraph.tags,
                "head_sentences": head_sentences,
                "tail_sentences": tail_sentences
            }

            sorted_paragraphs.append(paragraph_data)
        logger.info(f"Получил параграфы для отчета: report_id={report_id}. Возвращаю данные")
        return sorted_paragraphs
    
        


    # Метод для получения групп предложений параграфа. Возвращает кортеж (head_group, tail_group)
    @classmethod
    def get_paragraph_groups(cls, paragraph_id):
        """
        Возвращает группы предложений параграфа.
        Args:
            paragraph_id (int): ID параграфа.
        Returns:
            tuple: (HeadSentenceGroup, TailSentenceGroup) - Группы предложений параграфа.
        """
        paragraph = cls.query.get(paragraph_id)
        return paragraph.head_sentence_group, paragraph.tail_sentence_group


class Sentence(BaseModel):
    __tablename__ = "sentences"
    paragraph_id = db.Column(db.BigInteger, db.ForeignKey("report_paragraphs.id"), nullable=False)
    index = db.Column(db.SmallInteger, nullable=False)
    weight = db.Column(db.SmallInteger, nullable=False)
    comment = db.Column(db.String(100), nullable=False)
    sentence = db.Column(db.String(600), nullable=False)
    sentence_type = db.Column(sentence_type_enum, nullable=False, default="body")
    tags = db.Column(db.String(255), nullable=True)
    report_type_id = db.Column(db.SmallInteger, nullable=False)



    def save(self, old_index=None):
        """
        Сохраняет предложение и синхронизирует его в связанных параграфах, если связь equivalent.
        Если изменяется индекс главного предложения, обновляет индекс у всех предложений с таким же индексом.
        """
        super().save()
        return


    @classmethod
    def create(cls, paragraph_id, index, weight, sentence, sentence_type="tail", tags=None, comment=None):
        """
        Создает новое предложение.

        Args:
            paragraph_id (int): ID параграфа.
            index (int): Индекс предложения в параграфе.
            weight (int): Вес предложения.
            sentence (str): Текст предложения.
            sentence_type (str): Может принимать значение "head", "body","tail". Default="tail".
            tags (str, optional): Теги в виде строки. Default=None.
            comment (str, optional): Комментарий. Default=None.

        Returns:
            Sentence: Созданный объект предложения.
        """
        # Проверка наличия уже существующего главного предложения для данного index в данном paragraph_id
        if sentence_type == "head":
            existing_main_sentence = cls.query.filter_by(paragraph_id=paragraph_id, index=index, sentence_type="head").first()
            if existing_main_sentence:
                logger.error(f"Предложение с индексом {index} уже является основным в параграфе {paragraph_id}")
                sentence_type = "body"  # Если уже есть основное предложение, устанавливаем предложение как обычное
            else:
                logger.info(f"Предложение с индексом {index} установлено как основное в параграфе {paragraph_id}")
                logger.debug("НУЖНО НАСТРОИТЬ ЛОГИКУ СОЗДАНИЯ НОВЫХ ПРЕДЛОЖЕНИЙ В СВЯЗАННЫХ ПАРАГРАФАХ")
            
        if len(sentence) > 600:
            logger.error(f"Предложение слишком длинное ({len(sentence)} символов)")
            raise ValueError("Предложение слишком длинное (больше 600 символов)")
           
        
        new_sentence = cls(
            paragraph_id=paragraph_id,
            index=index,
            weight=weight,
            sentence_type=sentence_type,
            tags=tags,
            comment=comment,
            sentence=sentence
        )
        db.session.add(new_sentence)
        db.session.commit()
        return new_sentence
    
    
    @classmethod
    def find_by_paragraph_id(cls, paragraph_id):
        return cls.query.filter_by(paragraph_id=paragraph_id).all()

    
    
  
  
  
    
class SentenceBase(BaseModel):
    __abstract__ = True  
    
    report_type_id = db.Column(db.SmallInteger, nullable=True)  
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=True)
    sentence = db.Column(db.String(600), nullable=False)
    tags = db.Column(db.String(100), nullable=True)
    comment = db.Column(db.String(255), nullable=True)


    # Перед удалением предложения, удаляем связь с группами
    def delete(self):
        # Удаляем связь с группами
        self.groups = []
        db.session.commit()
        # Удаляем сам объект
        db.session.delete(self)
        db.session.commit()


    def update(self, **kwargs):
        """
        Обновляет существующее предложение.
        """
        logger.info(f"Начато обновление предложения {self.id}")
        for key, value in kwargs.items():
            setattr(self, key, value)  # Устанавливаем новое значение в атрибут объекта
        db.session.commit()
        logger.info(f"Обновление завершено")
        return self

    
    @classmethod
    def create(cls, user_id, report_type_id, sentence, related_id, sentence_index=None, tags=None, comment=None, sentence_weight=1):
        """
        Универсальный метод создания предложений (head, body, tail).

        Args:
            user_id (int): ID пользователя.
            report_type_id (int): ID типа отчета.
            sentence (str): Текст предложения.
            related_id (int): ID родительской сущности (параграфа для head/tail, head-предложения для body).
            sentence_index (int, optional): Индекс предложения (только для head).
            tags (str, optional): Теги предложения.
            comment (str, optional): Комментарий.
            sentence_weight (int, optional): Вес предложения (только для body/tail).

        Returns:
            tuple: (созданное предложение, использованная группа)
        """
        if not sentence.strip():
            sentence = "Пустое предложение"

        logger.info(f"Создание {cls.__name__} - '{sentence}' (related_id: {related_id})")

        # Определяем к какой группе относится предложение
        if cls == HeadSentence:
            paragraph = Paragraph.get_by_id(related_id)
            if not paragraph:
                raise ValueError(f"Параграф с ID {related_id} не найден")

            group = paragraph.head_sentence_group or HeadSentenceGroup.create()
            paragraph.head_sentence_group_id = group.id
            sentence_type = "head"

        elif cls == BodySentence:
            head_sentence = HeadSentence.get_by_id(related_id)
            if not head_sentence:
                raise ValueError(f"Head-предложение с ID {related_id} не найдено")

            group = head_sentence.body_sentence_group or BodySentenceGroup.create()
            head_sentence.body_sentence_group_id = group.id
            sentence_type = "body"

        elif cls == TailSentence:
            paragraph = Paragraph.get_by_id(related_id)
            if not paragraph:
                raise ValueError(f"Параграф с ID {related_id} не найден")

            group = paragraph.tail_sentence_group or TailSentenceGroup.create()
            paragraph.tail_sentence_group_id = group.id
            sentence_type = "tail"

        else:
            raise ValueError("Этот метод не поддерживает создание других типов предложений")

        # Импортируем функцию для поиска похожих предложений
        from sentence_processing import find_similar_exist_sentence
        
        similar_sentence = find_similar_exist_sentence(
            sentence_text=sentence, 
            sentence_type=sentence_type, 
            tags=tags, 
            user_id=user_id,
            report_type_id=report_type_id,
            comment=comment,
            sentence_index=sentence_index
        )

        if similar_sentence:
            db.session.add(similar_sentence)
            db.session.flush()
            logger.info(f"Похожее предложение уже существует и привязано к группе {group.id}")
            return cls.link_to_group(similar_sentence, group)

        # Формируем аргументы с общими для всех предложений полями
        sentence_data = {
            "sentence": sentence.strip(),
            "tags": tags,
            "comment": comment,
            "report_type_id": report_type_id,
            "user_id": user_id
        }
        # Добавляем специфичные поля для каждого типа предложения
        if cls == HeadSentence:
            sentence_data["sentence_index"] = sentence_index  # Только для HeadSentence
        elif cls in [BodySentence, TailSentence]:
            sentence_data["sentence_weight"] = sentence_weight  # Только для BodySentence и TailSentence

        # Создаем предложение, передавая только релевантные аргументы
        new_sentence = cls(**sentence_data)

        db.session.add(new_sentence)
        db.session.flush()  # Чтобы получить ID

        logger.info(f"Создано {cls.__name__} (ID={new_sentence.id}), привязываем к группе {group.id}")

        return cls.link_to_group(new_sentence, group)
    
    
    @classmethod
    def link_to_group(cls, sentence, group):
        """
        Добавляет предложение в указанную группу.

        Args:
            sentence (SentenceBase): Предложение для привязки.
            group (BaseModel): Группа, к которой привязываем предложение.

        Returns:
            tuple: (предложение, использованная группа)
        """
        if not group:
            raise ValueError("Группа должна быть передана в метод link_to_group")

        logger.info(f"Привязываем предложение {sentence.id} к группе {group.id}")

        # Проверяем, привязано ли уже предложение к группе
        if isinstance(sentence, HeadSentence) and sentence in group.head_sentences:
            logger.info(f"Предложение {sentence.id} уже в группе {group.id}, пропускаем")
            return sentence, group
        elif isinstance(sentence, BodySentence) and sentence in group.body_sentences:
            logger.info(f"Предложение {sentence.id} уже в группе {group.id}, пропускаем")
            return sentence, group
        elif isinstance(sentence, TailSentence) and sentence in group.tail_sentences:
            logger.info(f"Предложение {sentence.id} уже в группе {group.id}, пропускаем")
            return sentence, group
        
        # Привязываем предложение, если оно еще не в группе
        if isinstance(sentence, HeadSentence):
            group.head_sentences.append(sentence)
        elif isinstance(sentence, BodySentence):
            group.body_sentences.append(sentence)
        elif isinstance(sentence, TailSentence):
            group.tail_sentences.append(sentence)
        else:
            raise ValueError(f"Неизвестный тип предложения: {type(sentence).__name__}")

        db.session.commit()
        logger.info(f"Предложение {sentence.id} успешно привязано к группе {group.id}")
        return sentence, group
    
    
    @classmethod
    def unlink_from_group(cls, sentence, group):
        """
        Удаляет связь существующего предложения с конкретной группой.

        Args:
            sentence (SentenceBase): Предложение для отвязки.
            group (BaseModel): Группа, от которой отвязываем предложение.

        Returns:
            bool: True, если изменение было внесено, иначе False.
        """
        if not isinstance(sentence, SentenceBase) or not isinstance(group, SentenceGroupBase):
            raise ValueError("Должно быть передано предложение (SentenceBase) и группа (SentenceGroupBase)")

        logger.info(f"Отвязка предложения {sentence.id} от группы {group.id}")

        changes_made = False

        if isinstance(sentence, HeadSentence) and sentence in group.head_sentences:
            group.head_sentences.remove(sentence)
            changes_made = True
        elif isinstance(sentence, BodySentence) and sentence in group.body_sentences:
            group.body_sentences.remove(sentence)
            changes_made = True
        elif isinstance(sentence, TailSentence) and sentence in group.tail_sentences:
            group.tail_sentences.remove(sentence)
            changes_made = True

        if changes_made:
            db.session.commit()
            logger.info(f"Отвязка успешна. Предложение {sentence.id} удалено из группы {group.id}")
        else:
            logger.info(f"Отвязка не выполнена: предложение {sentence.id} не найдено в группе {group.id}")

        return changes_made
    
    
    @classmethod
    def get_groups(cls, sentence):
        """
        Возвращает список групп, с которыми связано предложение.

        Args:
            sentence (SentenceBase): Предложение, для которого ищем группы.

        Returns:
            list[BaseModel]: Список групп, связанных с данным предложением.
        """
        logger.info(f"Поиск групп для предложения {sentence.id}")
        if isinstance(sentence, HeadSentence):
            logger.info(f"Поиск групп для head-предложения. Найдены группы: {sentence.groups}")
            return sentence.groups or []  # head_sentences связаны с HeadSentenceGroup
        elif isinstance(sentence, BodySentence):
            logger.info(f"Поиск групп для body-предложения. Найдены группы: {sentence.groups}")
            return sentence.groups or []  # body_sentences связаны с BodySentenceGroup
        elif isinstance(sentence, TailSentence):
            logger.info(f"Поиск групп для tail-предложения. Найдены группы: {sentence.groups}")
            return sentence.groups or []  # tail_sentences связаны с TailSentenceGroup
        else:
            raise ValueError("Не удалось определить тип предложения")
    
    
    def get_sentence_type(self):
        """
        Возвращает строковый тип предложения (head, body, tail).
        """
        if isinstance(self, HeadSentence):
            return "head"
        elif isinstance(self, BodySentence):
            return "body"
        elif isinstance(self, TailSentence):
            return "tail"
        return "unknown"


    @classmethod
    def cleanup_orphan_sentences(cls):
        """
        Удаляет предложения, которые больше не привязаны ни к одной группе.
        Запускать периодически или при входе пользователя в систему.
        """
        session = db.session

        # Проверяем для каждого типа предложений
        for model, link_table, sentence_column in [
            (HeadSentence, head_sentence_group_link, head_sentence_group_link.c.head_sentence_id),
            (BodySentence, body_sentence_group_link, body_sentence_group_link.c.body_sentence_id),
            (TailSentence, tail_sentence_group_link, tail_sentence_group_link.c.tail_sentence_id)
        ]:
            # Находим предложения, у которых нет записей в таблице связей
            orphan_sentences = session.query(model.id).filter(
                ~session.query(sentence_column)
                .filter(sentence_column == model.id)
                .exists()
            ).subquery()

            logger.info(f"Найдено {session.query(orphan_sentences).count()} висячих предложений типа {model.__name__}")
            # Удаляем найденные висячие предложения
            session.query(model).filter(model.id.in_(session.query(orphan_sentences))).delete(synchronize_session=False)

        session.commit()




class HeadSentence(SentenceBase):
    __tablename__ = "head_sentences"
    sentence_index = db.Column(db.SmallInteger, nullable=False)
    body_sentence_group_id = db.Column(db.BigInteger, db.ForeignKey("body_sentence_groups.id", ondelete="SET NULL"))
    
    body_sentence_group = db.relationship(
        "BodySentenceGroup", 
        backref="head_sentences"
    )
    
    groups = db.relationship(
        "HeadSentenceGroup",
        secondary="head_sentence_group_link",
        back_populates="head_sentences"
    )
    
    
class BodySentence(SentenceBase):
    __tablename__ = "body_sentences"
    sentence_weight = db.Column(db.SmallInteger, nullable=False, server_default="1")
    
    groups = db.relationship(
        "BodySentenceGroup",
        secondary="body_sentence_group_link",
        back_populates="body_sentences"
    )
    
    

class TailSentence(SentenceBase):
    __tablename__ = "tail_sentences"
    sentence_weight = db.Column(db.SmallInteger, nullable=False, server_default="1")

    groups = db.relationship(
        "TailSentenceGroup",
        secondary="tail_sentence_group_link",
        back_populates="tail_sentences"
    )
    
    
  
  
        
class SentenceGroupBase(BaseModel):
    """
    Базовый класс для групп предложений (HeadSentenceGroup, BodySentenceGroup, TailSentenceGroup).
    """
    __abstract__ = True  


    def delete(self):
        """
        Удаляет группу, если она больше нигде не используется.
        Если в группе остались предложения – удаление отменяется.

        Returns:
            bool: True, если группа удалена, иначе False.
        """
        logger.info(f"Попытка удаления группы {self.id}")

        # Проверяем, есть ли связанные предложения
        if hasattr(self, "head_sentences") and self.head_sentences:
            logger.info(f"Группа {self.id} содержит head-предложения, не удаляем")
            return False
        elif hasattr(self, "body_sentences") and self.body_sentences:
            logger.info(f"Группа {self.id} содержит body-предложения, не удаляем")
            return False
        elif hasattr(self, "tail_sentences") and self.tail_sentences:
            logger.info(f"Группа {self.id} содержит tail-предложения, не удаляем")
            return False

        # Проверяем использование группы в других таблицах
        if isinstance(self, HeadSentenceGroup):
            used_in_paragraphs = Paragraph.query.filter_by(head_sentence_group_id=self.id).count()
            if used_in_paragraphs > 0:
                logger.info(f"Группа {self.id} используется в параграфах, не удаляем")
                return False

        elif isinstance(self, TailSentenceGroup):
            used_in_paragraphs = Paragraph.query.filter_by(tail_sentence_group_id=self.id).count()
            if used_in_paragraphs > 0:
                logger.info(f"Группа {self.id} используется в параграфах, не удаляем")
                return False

        elif isinstance(self, BodySentenceGroup):
            used_in_head_sentences = HeadSentence.query.filter_by(body_sentence_group_id=self.id).count()
            if used_in_head_sentences > 0:
                logger.info(f"Группа {self.id} используется в head-предложениях, не удаляем")
                return False

        # Удаляем группу
        db.session.delete(self)
        db.session.commit()
        logger.info(f"Группа {self.id} успешно удалена")
        return True

    @classmethod
    def create(cls):
        """
        Создает новую группу предложений.

        Returns:
            SentenceGroupBase: Созданная группа.
        """
        new_group = cls()
        db.session.add(new_group)
        db.session.commit()
        return new_group


    @classmethod
    def get_sentences(cls, group):
        """
        Возвращает список предложений, связанных с данной группой.
        Args:
            group (SentenceGroupBase): Группа, для которой ищем предложения.
        Returns:
            list[SentenceBase]: Список предложений.
        """
        logger.info(f"Поиск предложений для группы {group.id}")
        if isinstance(group, HeadSentenceGroup):
            logger.info(f"Поиск head-предложений. Найдены предложения: {group.head_sentences}")
            return group.head_sentences
        elif isinstance(group, BodySentenceGroup):
            logger.info(f"Поиск body-предложений. Найдены предложения: {group.body_sentences}")
            return group.body_sentences
        elif isinstance(group, TailSentenceGroup):
            logger.info(f"Поиск tail-предложений. Найдены предложения: {group.tail_sentences}")
            return group.tail_sentences
        else:
            raise ValueError("Не удалось определить тип группы")


    @classmethod
    def get_all_groups(cls):
        """
        Возвращает все группы данного типа.
        Returns:
            list[SentenceGroupBase]: Список всех групп.
        """
        return cls.query.all()
        
        
class HeadSentenceGroup(SentenceGroupBase):
    __tablename__ = "head_sentence_groups"

    head_sentences = db.relationship(
        "HeadSentence",
        secondary="head_sentence_group_link",
        back_populates="groups"
    )
    
class BodySentenceGroup(SentenceGroupBase):
    __tablename__ = "body_sentence_groups"

    body_sentences = db.relationship(
        "BodySentence",
        secondary="body_sentence_group_link",
        back_populates="groups"
    )
    
        
class TailSentenceGroup(SentenceGroupBase):
    __tablename__ = "tail_sentence_groups"

    tail_sentences = db.relationship(
        "TailSentence",
        secondary="tail_sentence_group_link",
        back_populates="groups"
    )
       
       
       
       
       
       
        
class KeyWord(BaseModel):
    __tablename__ = 'key_words_group'
    profile_id = db.Column(db.BigInteger, db.ForeignKey('user_profiles.id'), nullable=False)
    group_index = db.Column(db.Integer, nullable=False)
    index = db.Column(db.Integer, nullable=False)
    key_word = db.Column(db.String(50), nullable=False)
    key_word_comment = db.Column(db.String(100), nullable=True)
    public = db.Column(db.Boolean, default=False, nullable=False)
    
    # Связь многие ко многим с таблицей reports
    key_word_reports = db.relationship('Report', lazy=True, secondary='key_word_report_link', backref='key_words')

    @classmethod
    def create(cls, group_index, index, key_word, profile_id, key_word_comment=None, public=False, reports=None):
        """Creates a new keyword group entry."""
        new_key_word_group = cls(
            group_index=group_index,
            index=index,
            key_word=key_word,
            key_word_comment=key_word_comment,
            public=public,
            profile_id=profile_id
        )
        # Если переданы отчеты, добавляем связи с ними
        if reports:
            reports = Report.query.filter(Report.id.in_(reports), Report.profile_id == profile_id).all()
            for report in reports:
                new_key_word_group.key_word_reports.append(report)

        db.session.add(new_key_word_group)
        db.session.commit()
        return new_key_word_group

    @classmethod
    def find_by_profile(cls, profile_id):
        """Finds all keyword groups for a specific profile."""
        return cls.query.filter_by(profile_id=profile_id).order_by(cls.group_index, cls.index).all()
    
    @classmethod
    def find_without_reports(cls, profile_id):
        """Возвращает все ключевые слова профиля, не связанные с отчетами."""
        return cls.query.outerjoin(cls.key_word_reports).filter(
            cls.key_word_reports == None,  # Нет связей с отчетами
            cls.profile_id == profile_id  # Фильтр по пользователю
        ).all()
        
    @classmethod
    def find_by_report(cls, report_id):
        """Возвращает все ключевые слова, связанные с данным отчетом."""
        return cls.query.join(cls.key_word_reports).filter(
            Report.id == report_id
        ).all()
        
    @classmethod
    def get_keywords_for_report(cls, profile_id, report_id):
        """ Функция получения списка всех ключевых слов необходимых 
        для конкретного отчета, включает как связанные с отчетом 
        ключевые слова так и общие ключевые слова конкретного профиля """
        
        keywords_linked_to_report = cls.find_by_report(report_id)
        keywords_without_reports = cls.find_without_reports(profile_id)
        
        # Объединяем списки
        all_keywords = keywords_linked_to_report + keywords_without_reports
        # Убираем дубликаты (на случай если один и тот же ключевое слово было и там, и там)
        all_keywords = list({keyword.id: keyword for keyword in all_keywords}.values())

        return all_keywords
    
    @classmethod
    def find_by_group_index(cls, group_index, profile_id):
        """
        Поиск ключевых слов по значению group_index для конкретного пользователя.

        Args:
            group_index (int): Индекс группы ключевых слов.
            profile_id (int): ID пользователя.

        Returns:
            list[KeyWord]: Найденные записи слов данной группы. Возвращает пустой список, если ничего не найдено.
        """
        # Проверка существования индексов на полях group_index и user_id для повышения производительности
        # Запрос по фильтрации ключевых слов для конкретного пользователя с указанным group_index
        return cls.query.filter_by(group_index=group_index, profile_id=profile_id).all()

        
    @classmethod
    def find_public(cls):
        """Finds all public keyword groups."""
        return cls.query.filter_by(public=True).all()

    @classmethod
    def add_reports_to_keywords(cls, keywords, reports):
        """Добавляет отчеты к одному или нескольким ключевым словам."""
        # Если keywords не список, преобразуем его в список
        keywords = ensure_list(keywords)
        reports = ensure_list(reports)

        # Добавляем отчеты к каждому ключевому слову
        for keyword in keywords:
            for report in reports:
                if report not in keyword.key_word_reports:
                    keyword.key_word_reports.append(report)

        db.session.commit()

    @classmethod
    def remove_reports_from_keywords(cls, keywords, reports):
        """Удаляет отчеты у одного или нескольких ключевых слов."""
        # Если keywords не список, преобразуем его в список
        keywords = ensure_list(keywords)
        reports = ensure_list(reports)

        # Удаляем отчеты у каждого ключевого слова
        for keyword in keywords:
            for report in reports:
                if report in keyword.key_word_reports:
                    keyword.key_word_reports.remove(report)

        db.session.commit()
        
    @classmethod
    def remove_all_reports_from_keywords(cls, keywords):
        """Удаляет все связи с отчетами для одного или нескольких ключевых слов."""
        keywords = ensure_list(keywords)

        for keyword in keywords:
            keyword.key_word_reports = []  

        db.session.commit()


class FileMetadata(BaseModel):
    __tablename__ = "file_metadata"
    
    profile_id = db.Column(db.BigInteger, db.ForeignKey("user_profiles.id"), nullable=False)  # Связь с профилем
    file_name = db.Column(db.String(255), nullable=False)  # Имя файла
    file_path = db.Column(db.String(500), nullable=False)  # Путь к файлу
    file_type = db.Column(db.String(50), nullable=False)  # Тип файла (например, "docx", "jpg")
    uploaded_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)  # Время загрузки файла
    file_description = db.Column(db.String(500), nullable=False)
    

    @classmethod
    def create(cls, profile_id, file_name, file_path, file_type, file_description):
        new_file = cls(
            profile_id=profile_id,
            file_name=file_name,
            file_path=file_path,
            file_type=file_type,
            file_description=file_description
        )
        db.session.add(new_file)
        db.session.commit()
        return new_file
    
    @classmethod
    def get_file_by_description(cls, profile_id, file_description):
        """
        Возвращает полный путь к файлу, который относится к данному профилю, на основе его описания.
        
        Args:
            profile_id (int): ID профиля.
            file_description (str): Описание файла.
        
        Returns:
            str: Путь к файлу, если найден, иначе None.
        """
        file = cls.query.filter_by(profile_id=profile_id, file_description=file_description).first()
        if file:
            return file
        else:
            return None




# Вешаем триггер перед удалением группы предложений
event.listen(HeadSentenceGroup, "before_delete", prevent_group_deletion)
event.listen(TailSentenceGroup, "before_delete", prevent_group_deletion)
event.listen(BodySentenceGroup, "before_delete", prevent_group_deletion)


# Индексы для ускорения поиска по группам
db.Index("ix_tail_sentence_group_id", TailSentenceGroup.id)
db.Index("ix_body_sentence_group_id", BodySentenceGroup.id)

# Индексы для связей предложений и групп
db.Index("ix_tail_sentence_group_link_group", tail_sentence_group_link.c.group_id)
db.Index("ix_body_sentence_group_link_group", body_sentence_group_link.c.group_id)

# Индексы для ускорения поиска предложений по группам в параграфах и head_sentences
db.Index("ix_paragraph_tail_sentence_group", Paragraph.tail_sentence_group_id)
db.Index("ix_head_sentence_body_sentence_group", HeadSentence.body_sentence_group_id)

# Индексы для связей параграфов и групп
db.Index("ix_paragraph_head_sentence_group", Paragraph.head_sentence_group_id)
db.Index("ix_head_sentence_group_link_group", head_sentence_group_link.c.group_id)