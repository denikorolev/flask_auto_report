# models.py

from flask_sqlalchemy import SQLAlchemy
from flask_security import UserMixin, RoleMixin
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy import Index, event, func
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

 
# ✅ быстрее 👉 🔥 📌 ❌ 🚀 😎 🔄 1️⃣ 2️⃣ 3️⃣ ⚠️


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
    db.Column("sentence_index", db.Integer, nullable=False),  # Храним индекс предложения в связи! Нужно для определяется положения предожения в протоколе
    db.Index("ix_head_sentence_group", "head_sentence_id", "group_id")
)

# Ассоциативная таблица для связи body предложений с группой body предложений
body_sentence_group_link = db.Table(
    "body_sentence_group_link",
    db.Column("body_sentence_id", db.BigInteger, db.ForeignKey("body_sentences.id", ondelete="CASCADE"), primary_key=True),
    db.Column("group_id", db.BigInteger, db.ForeignKey("body_sentence_groups.id", ondelete="CASCADE"), primary_key=True),
    db.Column("sentence_weight", db.Integer, nullable=False, server_default="1"),  # Храним вес в связи!
    db.Index("ix_body_sentence_group", "body_sentence_id", "group_id")  
)

# Ассоциативная таблица для связи tail предложений с группой tail предложений
tail_sentence_group_link = db.Table(
    "tail_sentence_group_link",
    db.Column("tail_sentence_id", db.BigInteger, db.ForeignKey("tail_sentences.id", ondelete="CASCADE"), primary_key=True),
    db.Column("group_id", db.BigInteger, db.ForeignKey("tail_sentence_groups.id", ondelete="CASCADE"), primary_key=True),
    db.Column("sentence_weight", db.Integer, nullable=False, server_default="1"),  # Храним вес в связи!
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
        
        
    def update(self, **kwargs):
        """
        Универсальный метод обновления модели.

        Args:
            **kwargs: Пары ключ-значение, где ключ — это имя поля модели, а значение — новое значение.
        
        Returns:
            bool: True, если обновление прошло успешно, иначе False.
        """
        logger.info(f"(базовый метод update) 🚀 Начинаю обновление {self.__class__.__name__}")
        allowed_columns = {column.name for column in self.__table__.columns}
        
        for key, value in kwargs.items():
            if key in allowed_columns:
                setattr(self, key, value)
            else:
                logger.warning(f"(update) ❌ Поле '{key}' отсутствует в {self.__class__.__name__} и будет проигнорировано")

        try:
            db.session.commit()
            logger.info(f"(update) ✅ Объект {self.__class__.__name__} ID={self.id} успешно обновлён")
            return 
        except Exception as e:
            db.session.rollback()
            logger.error(f"(update) ❌ Ошибка обновления {self.__class__.__name__} ID={self.id}: {e}")
            raise ValueError(f"Ошибка обновления {self.__class__.__name__} ID={self.id}: {e}")
        

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
    def get_report_info(cls, report_id):
        """
        Получает основные данные отчета.
        Args:
            report_id (int): ID отчета.
            profile_id (int): ID профиля пользователя.
        Returns:
            dict: Словарь с информацией об отчете или None, если отчет не найден.
        """
        logger.info(f"(get_report_info) 🚀 Начинаю выполнение запроса данных протокола report_id={report_id}")
        
        report = cls.query.filter_by(id=report_id).first()
        if not report:
            logger.error(f"(get_report_info)❌ Протокол не найден.")
            return None  

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
        logger.info(f"(get_report_info)✅ Получил данные отчета: report_id={report_id}. Возвращаю данные")
        return report_data
    
    
    @classmethod
    def get_report_data(cls, report_id):
        """
        Возвращает основные данные отчета и список параграфов.
        Args:
            report_id (int): ID отчета.
            profile_id (int): ID профиля пользователя.
        Returns:
            tuple: (dict, list) - (report_data, sorted_paragraphs)
        """
        logger.info(f"(get_report_data) 🚀 Начат процесс получения данных отчета: report_id={report_id}")  
        try:
            report_data = cls.get_report_info(report_id)
        except Exception as e:
            logger.error(f"(get_report_data) ❌ Ошибка при получении данных отчета из (get_report_info): {e}")
            raise e
        
        if report_data is None:
            logger.error(f"Отчет не найден: report_id={report_id}")
            return None, None
        try:
            sorted_paragraphs = Report.get_report_paragraphs(report_id)
        except Exception as e:
            logger.error(f"(get_report_data) ❌ Ошибка при получении параграфов отчета из (get_report_paragraphs): {e}")
            raise e
        logger.info(f"(get_report_data) ✅ Получил обобщенные данные отчета: report_id={report_id}. Возвращаю.")
        return report_data, sorted_paragraphs
    
    
    
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
        logger.info(f"(get_report_paragraphs)🚀 Начинаю выполнение запроса параграфов для отчета.")

        # Получаем все параграфы отчета и сортируем по paragraph_index
        paragraphs = Paragraph.query.filter_by(report_id=report_id).order_by(Paragraph.paragraph_index).all()
        sorted_paragraphs = []

        for paragraph in paragraphs:
            head_sentences = []
            has_linked_head = False
            has_linked_tail = False
            if paragraph.head_sentence_group_id:
                logger.info(f"(метод get_report_paragraphs класса Report) Подтверждено наличие группы head предложений для параграфа {paragraph.id}")
                if HeadSentenceGroup.is_linked(paragraph.head_sentence_group_id) > 1:
                    logger.info(f"(метод get_report_paragraphs класса Report) 📌 Подтверждено наличие >1 связей для head у данного параграфа. Информация добавлена в аттрибуты")
                    has_linked_head = True
                # Загружаем head-предложения
                for head_sentence in HeadSentenceGroup.get_group_sentences(paragraph.head_sentence_group_id):
                    body_sentences = []
                    has_linked_body = False
                    if head_sentence["body_sentence_group_id"]:
                        logger.info(f"(метод get_report_paragraphs класса Report) Подтверждено наличие группы body предложений для head-предложения {head_sentence['id']}.")
                        if BodySentenceGroup.is_linked(head_sentence["body_sentence_group_id"]) > 1:
                            logger.info(f"(метод get_report_paragraphs класса Report) 📌 Подтверждено наличие >1 связей для body у данного head-предложения. Информация добавлена в аттрибуты.")
                            has_linked_body = True
                        body_sentences = BodySentenceGroup.get_group_sentences(head_sentence["body_sentence_group_id"])

                    head_sentences.append({
                        "id": head_sentence["id"],
                        "index": head_sentence["sentence_index"],
                        "comment": head_sentence["comment"],
                        "sentence": head_sentence["sentence"],
                        "tags": head_sentence["tags"],
                        "report_type_id": head_sentence["report_type_id"],
                        "has_linked_body": has_linked_body,
                        "body_sentences": body_sentences  
                    })

            tail_sentences = []
            if paragraph.tail_sentence_group_id:
                logger.info(f"(метод get_report_paragraphs класса Report) Подтверждено наличие группы tail предложений для параграфа {paragraph.id}.")
                if TailSentenceGroup.is_linked(paragraph.tail_sentence_group_id) > 1:
                    logger.info(f"(метод get_report_paragraphs класса Report) 📌 Подтверждено наличие >1 связей для tail у данного параграфа. Информация добавлена в аттрибуты.")
                    has_linked_tail = True
                tail_sentences = TailSentenceGroup.get_group_sentences(paragraph.tail_sentence_group_id)

            # Формируем данные по параграфу
            logger.info(f"(метод get_report_paragraphs класса Report) Начало формирования финальных данных по параграфу {paragraph.id}.")
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
                "has_linked_head": has_linked_head,
                "has_linked_tail": has_linked_tail,
                "head_sentences": head_sentences,  # Теперь body_sentences внутри head
                "tail_sentences": tail_sentences
            }

            sorted_paragraphs.append(paragraph_data)
            logger.info(f"(метод get_report_paragraphs класса Report) Параграф {paragraph.id} обработан и добавлен в список параграфов.")

        logger.info(f"(метод get_report_paragraphs класса Report) ✅ Получил параграфы для отчета: report_id={report_id}. Возвращаю данные")
        return sorted_paragraphs  


    
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
        logger.info(f"(метод create класса Paragraph) 🚀 Начато создание нового параграфа для протокола: report_id={report_id}")
        try:
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
            
            logger.info(f"(метод create класса Paragraph) ✅ Параграф создан: paragraph_id={new_paragraph.id}")
            return new_paragraph
        
        except Exception as e:
            logger.error(f"(метод create класса Paragraph) ❌ Ошибка при создании параграфа: {e}")
            
            db.session.rollback()
            return None
        
    
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


class SentenceBase(BaseModel):
    __abstract__ = True  
    
    report_type_id = db.Column(db.SmallInteger, nullable=True)  
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=True)
    sentence = db.Column(db.String(600), nullable=False)
    tags = db.Column(db.String(100), nullable=True)
    comment = db.Column(db.String(255), nullable=True) 


    # Перед удалением предложения, удаляем связь с группами
    @classmethod
    def delete_sentence(cls, sentence_id, group_id=None):
        """
        Удаляет предложение или отвязывает его от группы, если оно связано с несколькими группами.
        Args:
            sentence_id (int): ID предложения, которое нужно удалить.
            group_id (int, optional): ID группы, от имени которой поступил запрос. Если None, удаляется само предложение.
        """
        logger.info(f"Удаление предложения ID={sentence_id} из группы ID={group_id}")
        sentence = cls.query.get(sentence_id)
        if not sentence:
            logger.info(f"Предложение ID={sentence_id} не найдено.")
            raise ValueError(f"Предложение ID={sentence_id} не найдено.")
        
        # Если предложению НЕ передали ID группы → удаляем его полностью
        if group_id is None:
            logger.info(f"Удаляем предложение ID={sentence_id}, так как не передана информация о группе.")
            sentence.delete()
            return 

        linked_count = cls.is_linked(sentence_id)
        logger.info(f"Предложение ID={sentence_id} связано с {linked_count} группами.")

        # Если у предложения только 1 или 0 связей → удаляем его полностью
        if linked_count <= 1: 
            if cls != HeadSentence:
                logger.info(f"Удаляем предложение ID={sentence_id}, так как у него {linked_count} связей.")
                sentence.delete()
                return 
            else:
                logger.info(f"Предложение ID={sentence_id} принадлежит только одной группе head. Запрашиваем наличие прикрепленния связанной группы body предложений.")
                related_body_group_id = sentence.body_sentence_group_id
                head_group_links_count = HeadSentenceGroup.is_linked(related_body_group_id)
                if head_group_links_count > 1:
                    logger.info(f"Связанная группа ID={group_id} принадлежит нескольким главным предложениям. Просто отвязываем группу.")
                    HeadSentenceGroup.unlink_group(related_body_group_id, sentence_id)
                    sentence.delete()
                    logger.info(f"head-предложение ID={sentence_id} удалено.")
                    return
                elif head_group_links_count == 0:
                    logger.info(f"У данного главного предложения нет привязанных body групп. Просто удаляю предложение ID={sentence_id}.")
                    sentence.delete()
                    logger.info(f"head-предложение ID={sentence_id} удалено.")
                    return
                else:
                    logger.info(f"Связанная группа ID={group_id} принадлежит только одному главному предложению. Удаляем группу.")
                    BodySentenceGroup.delete_group(related_body_group_id, sentence_id)
                    sentence.delete()
                    logger.info(f"head-предложение ID={sentence_id} удалено.")
                    return

        # Если предложению передали ID группы и у него больше 1 связи → просто отвязываем
        logger.info(f"🔗 Отвязываем предложение ID={sentence_id} от группы ID={group_id}, так как у него еще есть {linked_count} связей.")
        # Определяем соответствующую модель группы
        group_map = {
            HeadSentence: (HeadSentenceGroup, "head_sentences"),
            BodySentence: (BodySentenceGroup, "body_sentences"),
            TailSentence: (TailSentenceGroup, "tail_sentences"),
        }

        group_cls, group_attr = group_map.get(type(sentence), (None, None))
        if not group_cls:
            logger.info(f"Тип предложения {type(sentence).__name__} не поддерживается.")
            raise ValueError(f"Тип предложения {type(sentence).__name__} не поддерживается.")

        group = group_cls.query.get(group_id)  

        # Проверяем, есть ли предложение в группе
        if group and sentence in getattr(group, group_attr, []):
            cls.unlink_from_group(sentence, group)
            logger.info(f"Успешно отвязали предложение ID={sentence_id} от группы ID={group_id}.")
            return

        logger.info(f"Группа ID={group_id} не найдена или не содержит предложение ID={sentence_id}.")
        raise ValueError(f"Группа ID={group_id} не найдена или не содержит предложение ID={sentence_id}.")


    # def update(self, **kwargs):
    #     """
    #     Обновляет существующее предложение.
    #     """
    #     logger.info(f"Начато обновление предложения {self.id}")
    #     for key, value in kwargs.items():
    #         setattr(self, key, value)  # Устанавливаем новое значение в атрибут объекта
    #     db.session.commit()
    #     logger.info(f"Обновление завершено")
    #     return self

   
    @classmethod
    def edit_sentence(cls, 
                      sentence_id, 
                      group_id, 
                      related_id, 
                      new_text=None, 
                      new_index=None, 
                      new_weight=None, 
                      new_tags=None, 
                      new_comment=None, 
                      hard_edit=False):
        """
        Универсальный метод редактирования предложений (Head, Body, Tail).
        Возвращает:
            SentenceBase: Обновлённое или новое предложение.
        """
        sentence = cls.query.get(sentence_id)
        if not sentence:
            raise ValueError(f"{cls.__name__}: предложение ID={sentence_id} не найдено.")

        logger.info(f"Редактирование предложения {cls.__name__} ID={sentence_id}, hard_edit={hard_edit} начато 🚀")
        if new_text is None and new_index is not None:
            logger.info(f"📌 Предложение доставлено без изменений текста для изменения индекса")
        # Определяем тип предложения
        is_head = isinstance(sentence, HeadSentence)
        is_body_or_tail = isinstance(sentence, (BodySentence, TailSentence))

        # Если мягкое редактирование (обновляем существующую запись)
        if not hard_edit:
            if new_text is not None:
                sentence.sentence = new_text
            if new_tags is not None:
                sentence.tags = new_tags
            if new_comment is not None:
                sentence.comment = new_comment

            db.session.commit()
            
            return sentence

        # Жёсткое редактирование (создаём новое предложение через `create()`)
        new_sentence, used_group = cls.create(
            user_id=sentence.user_id,
            report_type_id=sentence.report_type_id,
            sentence=new_text,
            related_id=related_id,
            sentence_index=new_index if is_head else None,
            sentence_weight=new_weight if is_body_or_tail else None,
            tags=new_tags if new_tags is not None else sentence.tags,
            comment=new_comment if new_comment is not None else sentence.comment
        )

        # Удаляем старое предложение через delete_sentence, передавая правильный group_id
        cls.delete_sentence(sentence.id, group_id)

        return new_sentence
    
    
    @classmethod
    def create(cls, 
               user_id, 
               report_type_id, 
               sentence, 
               related_id, 
               sentence_index=None, 
               tags=None, 
               comment=None, 
               sentence_weight=1):
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

        logger.info(f"(метод create класса SentenceBase)(тип предложения: {cls.__name__}) Начато создание предложения с текстом: '{sentence}' (ID родительской сущности: {related_id})")

        # Определяем к какой группе относится предложение
        if cls == HeadSentence:
            if sentence_index is None:
                logger.error(f"(метод create класса SentenceBase) ❌ При создании главного предложения обязательно указывать индекс")
                raise ValueError(f"При создании главного предложения обязательно указывать индекс")
            paragraph = Paragraph.get_by_id(related_id)
            if not paragraph:
                logger.error(f"(метод create класса SentenceBase) ❌ Параграф с ID {related_id} не найден")
                raise ValueError(f"Параграф с ID {related_id} не найден")
            class_type = HeadSentence

            group = paragraph.head_sentence_group or HeadSentenceGroup.create()
            paragraph.head_sentence_group_id = group.id
            sentence_type = "head"

        elif cls == BodySentence:
            head_sentence = HeadSentence.get_by_id(related_id)
            if not head_sentence:
                logger.error(f"(метод create класса SentenceBase) ❌ head предложение с ID {related_id} не найдено")
                raise ValueError(f"head предложение с ID {related_id} не найдено")
            class_type = BodySentence

            group = head_sentence.body_sentence_group or BodySentenceGroup.create()
            head_sentence.body_sentence_group_id = group.id
            sentence_type = "body"

        elif cls == TailSentence:
            paragraph = Paragraph.get_by_id(related_id)
            if not paragraph:
                logger.error(f"(метод create класса SentenceBase) ❌ Параграф с ID {related_id} не найден")
                raise ValueError(f"Параграф с ID {related_id} не найден")
            class_type = TailSentence 

            group = paragraph.tail_sentence_group or TailSentenceGroup.create()
            paragraph.tail_sentence_group_id = group.id
            sentence_type = "tail"

        else:
            logger.error(f"(метод create класса SentenceBase) ❌ Неизвестный тип предложения")
            raise ValueError("Неизвестный тип предложения")

        # Импортируем функцию для поиска похожих предложений
        from sentence_processing import find_similar_exist_sentence
        logger.info(f"(метод create класса SentenceBase)🧩 Начат поиск похожего предложения в базе данных")
        similar_sentence = find_similar_exist_sentence(
            sentence_text=sentence, 
            sentence_type=sentence_type, 
            tags=tags, 
            user_id=user_id,
            report_type_id=report_type_id,
            comment=comment
        )

        if similar_sentence:
            logger.info(f"(метод create класса SentenceBase) 🧩🧩🧩 Найдено похожее предложение с ID {similar_sentence.id} в базе данных. Создание нового предложения не требуется.")
            db.session.add(similar_sentence)
            db.session.flush()
            logger.info(f"(метод create класса SentenceBase) Начато добавление предложения в группу")
            try:
                similar_sentence_linked, similar_sentence_group = cls.link_to_group(similar_sentence, group, sentence_weight, sentence_index)
            except Exception as e:
                logger.error(f"(метод create класса SentenceBase) ❌ Ошибка при добавлении предложения в группу: {e}")
                raise ValueError(f"Ошибка при добавлении предложения в группу: {e}")
            logger.info(f"(метод create класса SentenceBase) Найденное похожее предложение привязано к группе {similar_sentence_group.id}.")
            
            return similar_sentence_linked, similar_sentence_group
        
        logger.info(f"(метод create класса SentenceBase) Похожее предложение в базе данных не найдено. Создаю новое предложение.")
        # Формируем аргументы с общими для всех предложений полями
        sentence_data = {
            "sentence": sentence.strip(),
            "tags": tags,
            "comment": comment,
            "report_type_id": report_type_id,
            "user_id": user_id
        }
        
        # Создаем предложение, передавая только релевантные аргументы
        new_sentence = cls(**sentence_data)

        db.session.add(new_sentence)
        db.session.commit()  
        
        logger.info(f"(метод create класса SentenceBase)(тип предложения{cls.__name__}) ✅ Предложение создано.")

        logger.info(f"(метод create класса SentenceBase) Начато добавление предложения в группу")
        try:
            new_sentence_linked, new_sentence_group = cls.link_to_group(new_sentence, group, sentence_weight, sentence_index)
            logger.info(f"(метод create класса SentenceBase) ✅ Предложение успешно добавлено в группу")
            return new_sentence_linked, new_sentence_group
        except Exception as e:
            logger.error(f"(метод create класса SentenceBase) ❌ Ошибка при добавлении предложения в группу: {e}")
            raise ValueError(f"Ошибка при добавлении предложения в группу: {e}")
        
    
    @classmethod
    def link_to_group(cls, sentence, group, sentence_weight=None, sentence_index=None):
        """
        Добавляет предложение в указанную группу.

        Args:
            sentence (SentenceBase): Предложение для привязки.
            group (BaseModel): Группа, к которой привязываем предложение.

        Returns:
            tuple: (предложение, использованная группа)
        """
        logger.info(f"(метод link_to_group класса SentenceBase) 🚀 Начата привязка предложения к группе {group.id}")
        if not group:
            logger.info(f"(метод link_to_group класса SentenceBase) ❌ Группа не найдена")
            raise ValueError("Группа должна быть передана в метод link_to_group")

        logger.info(f"(метод link_to_group класса SentenceBase) Попытка привязать предложение {sentence.id} к группе {group.id}")

        # Проверяем, привязано ли уже предложение к группе
        if isinstance(sentence, HeadSentence) and sentence in group.head_sentences:
            logger.info(f"(метод link_to_group класса SentenceBase) ✅ Предложение {sentence.id} уже в группе {group.id}, пропускаем")
            return sentence, group
        elif isinstance(sentence, BodySentence) and sentence in group.body_sentences:
            logger.info(f"(метод link_to_group класса SentenceBase) ✅ Предложение {sentence.id} уже в группе {group.id}, пропускаем")
            return sentence, group
        elif isinstance(sentence, TailSentence) and sentence in group.tail_sentences:
            logger.info(f"(метод link_to_group класса SentenceBase) ✅ Предложение {sentence.id} уже в группе {group.id}, пропускаем")
            return sentence, group
        
        
        # Проверяем обязательные параметры
        if isinstance(sentence, HeadSentence) and sentence_index is None:
            logger.error(f"(метод link_to_group класса SentenceBase) ❌ Не указан индекс для HeadSentence")
            raise ValueError("Не указан sentence_index для HeadSentence")
        
        if isinstance(sentence, (BodySentence, TailSentence)) and sentence_weight is None:
            logger.error(f"(метод link_to_group класса SentenceBase) ❌ Не указан вес для Body/Tail предложения")
            raise ValueError("Не указан sentence_weight для Body/Tail предложения")
    
    
        # Добавляем предложение в группу
        if isinstance(sentence, HeadSentence):
            stmt = head_sentence_group_link.insert().values(
                head_sentence_id=sentence.id,
                group_id=group.id,
                sentence_index=sentence_index  # Сразу указываем индекс
            )
            db.session.execute(stmt)
        elif isinstance(sentence, BodySentence):
            stmt = body_sentence_group_link.insert().values(
                body_sentence_id=sentence.id,
                group_id=group.id,
                sentence_weight=sentence_weight  # Сразу указываем вес
            )
            db.session.execute(stmt)
        elif isinstance(sentence, TailSentence):
            stmt = tail_sentence_group_link.insert().values(
                tail_sentence_id=sentence.id,
                group_id=group.id,
                sentence_weight=sentence_weight  # Сразу указываем вес
            )
            db.session.execute(stmt)
        else:
            logger.error(f"(метод link_to_group класса SentenceBase) ❌ Неизвестный тип предложения: {type(sentence).__name__}")
            raise ValueError(f"Неизвестный тип предложения: {type(sentence).__name__}")

        db.session.commit()
        logger.info(f"(метод link_to_group класса SentenceBase) ✅ Предложение {sentence.id} успешно привязано к группе {group.id}")
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
    def is_linked(cls, sentence_id):
        """
        Проверяет, с каким количеством групп связано предложение.
        Args:
            sentence_id (int): ID предложения.
        Returns:
            int: Количество групп, с которыми связано предложение.
        """
        logger.info(f"Проверка количества связей для предложения ID={sentence_id}")
        sentence = cls.query.get(sentence_id)
        if not sentence:
            return 0
        logger.info(f"Предложение найдено: {sentence.id}")
        
        if isinstance(sentence, HeadSentence):
            return db.session.query(func.count(HeadSentenceGroup.id)).join(HeadSentence.groups).filter(HeadSentence.id == sentence_id).scalar()

        elif isinstance(sentence, BodySentence):
            return db.session.query(func.count(BodySentenceGroup.id)).join(BodySentence.groups).filter(BodySentence.id == sentence_id).scalar()

        elif isinstance(sentence, TailSentence):
            return db.session.query(func.count(TailSentenceGroup.id)).join(TailSentence.groups).filter(TailSentence.id == sentence_id).scalar()

        return 0
    
    
    @classmethod
    def get_sentence_index_or_weight(cls, sentence_id, group_id):
        """
        Получает индекс или вес предложения из таблицы связей.
        
        Args:
            sentence_id (int): ID предложения.
            group_id (int): ID группы.
        
        Returns:
            int | None: Значение индекса (для HeadSentence) или веса (для Body/Tail), либо None, если не найдено.
        """
        logger.info(f"(get_sentence_index_or_weight)(тип группы: {cls.__name__}) 🚀 Начат запрос {'индекса' if cls==HeadSentence else 'веса'} предложения ID={sentence_id} из группы ID={group_id}")

        # Определяем таблицу связи и нужное поле
        if cls == HeadSentence:
            link_table = head_sentence_group_link
            sentence_field = link_table.c.head_sentence_id
            index_field = link_table.c.sentence_index

        elif cls == BodySentence:
            link_table = body_sentence_group_link
            sentence_field = link_table.c.body_sentence_id
            index_field = link_table.c.sentence_weight

        elif cls == TailSentence:
            link_table = tail_sentence_group_link
            sentence_field = link_table.c.tail_sentence_id
            index_field = link_table.c.sentence_weight

        else:
            logger.error(f"(get_sentence_index_or_weight) ❌ Неизвестный тип предложения: {cls.__name__}")
            return None

        # Делаем запрос к базе
        result = (
            db.session.query(index_field)
            .filter(sentence_field == sentence_id, link_table.c.group_id == group_id)
            .scalar()
        )

        logger.info(f"(get_sentence_index_or_weight) ✅ {'индекс' if cls==HeadSentence else 'вес'} найден: {result}")
        return result
    
    
    @classmethod
    def set_sentence_index_or_weight(cls, sentence_id, group_id, new_weight=None, new_index=None):
        """
        Универсальный метод для обновления позиции предложения.
        
        - Если предложение `HeadSentence`, обновляет `sentence_index`.
        - Если предложение `BodySentence`, обновляет `sentence_weight` (свою логику).
        - Если предложение `TailSentence`, обновляет `sentence_weight` (свою логику).

        Args:
            sentence_id (int): ID предложения.
            group_id (int): ID группы.
            new_weight (int, optional): Новый вес (для `BodySentence` и `TailSentence`).
            new_index (int, optional): Новый индекс (для `HeadSentence`).
        """
        logger.info(f"(Обновление позиции - set_sentence_index_or_weight) (тип предложения {cls.__name__}) 🚀 Обновление позиции предложения ID={sentence_id} в группе ID={group_id} начато")
        print("Значение индекса или веса:", new_index or new_weight)
        if cls == HeadSentence:
            if new_index is None:
                logger.error(f"(Обновление позиции - set_sentence_index_or_weight) ❌ Обновление позиции для head предложения требует обязательного наличия new_index")
                raise ValueError("Обновление позиции для head предложения требует обязательного наличия new_index")

            try:
                db.session.execute(
                    head_sentence_group_link.update()
                    .where(
                        (head_sentence_group_link.c.head_sentence_id == sentence_id) &
                        (head_sentence_group_link.c.group_id == group_id)
                    )
                    .values({"sentence_index": new_index})
                )
                logger.info(f"(Обновление позиции - set_sentence_index_or_weight)(тип предложения 'HeadSentence') ✅  положение предложения с ID={sentence_id} обновлено: новый индекс предложения -> {new_index}")
            except Exception as e:
                logger.error(f"(Обновление позиции - set_sentence_index_or_weight) ❌ Ошибка при обновлении позиции: {e}")
                raise ValueError(f"Ошибка при обновлении позиции: {e}")

        elif cls == BodySentence:
            if new_weight is None:
                logger.error(f"❌ BodySentence требует new_weight")
                raise ValueError("BodySentence требует new_weight")

            db.session.execute(
                body_sentence_group_link.update()
                .where(
                    (body_sentence_group_link.c.body_sentence_id == sentence_id) &
                    (body_sentence_group_link.c.group_id == group_id)
                )
                .values({"sentence_weight": new_weight})
            )
            logger.info(f"(Обновление позиции - set_sentence_index_or_weight)(тип предложения 'BodySentence') ✅  положение предложения с ID={sentence_id} обновлено: новый вес предложения -> {new_weight}")

        elif cls == TailSentence:
            if new_weight is None:
                logger.error(f"(Обновление позиции - set_sentence_index_or_weight) ❌ TailSentence требует new_weight")
                raise ValueError("TailSentence требует new_weight")

            db.session.execute(
                tail_sentence_group_link.update()
                .where(
                    (tail_sentence_group_link.c.tail_sentence_id == sentence_id) &
                    (tail_sentence_group_link.c.group_id == group_id)
                )
                .values({"sentence_weight": new_weight})
            )
            logger.info(f"(Обновление позиции - set_sentence_index_or_weight)(тип предложения 'TailSentence') ✅  положение предложения с ID={sentence_id} обновлено: новый вес предложения -> {new_weight}")

        else:
            logger.error(f"(Обновление позиции - set_sentence_index_or_weight) ❌ Неизвестный тип предложения: {cls.__name__}")
            raise ValueError(f"Неизвестный тип предложения: {cls.__name__}")

        db.session.commit()
        logger.info(f"(Обновление позиции - set_sentence_index_or_weight)(тип предложения: {cls.__name__}) ✅ Обновление позиции завершено.")




class HeadSentence(SentenceBase):
    __tablename__ = "head_sentences"
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
    
    groups = db.relationship(
        "BodySentenceGroup",
        secondary="body_sentence_group_link",
        back_populates="body_sentences"
    )
    
    

class TailSentence(SentenceBase):
    __tablename__ = "tail_sentences"

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


    @classmethod
    def delete_group(cls, group_id, entity_id = None):
        """
        Удаляет группу, если она больше нигде не используется.
        Если у группы несколько связей, просто удаляет связь с переданной сущностью.
        Args:
            group_id (int): ID группы, которую нужно удалить.
            entity_id (int): ID сущности (параграфа или предложения), откуда поступил запрос.
        Raises:
            ValueError: Если группа не найдена или её нельзя удалить.
        """
        group = cls.query.get(group_id)
        if not group:
            logger.info(f"Группа ID={group_id} не найдена.")
            raise ValueError(f"Группа ID={group_id} не найдена.")

        logger.info(f"Попытка удаления группы ID={group_id} для параграфа/предложения ID={entity_id}")

        # Если не передана информация о сущности → удаляем группу полностью
        if entity_id is None:
            logger.info(f"Удаляем группу ID={group_id}, так как не передана информация о сущности.")
            group.delete()
            return
        
        # Проверяем, с каким количеством сущностей связана группа
        linked_count = cls.is_linked(group_id)
        logger.info(f"Группа ID={group_id} связана с {linked_count} сущностями.")

        # Если группа связана больше чем с одной сущностью → просто отвязываем entity_id
        if linked_count > 1:
            logger.info(f"Отвязываем группу ID={group_id} от сущности ID={entity_id}, так как у неё ещё есть {linked_count} связей.")
            
            # Определяем, что за сущность (параграф или предложение) и отвязываем
            if isinstance(group, HeadSentenceGroup):
                HeadSentenceGroup.unlink_groupe(group_id, entity_id)
            elif isinstance(group, TailSentenceGroup):
                TailSentenceGroup.unlink_groupe(group_id, entity_id)
            elif isinstance(group, BodySentenceGroup):
                BodySentenceGroup.unlink_groupe(group_id, entity_id)
            else:    
                logger.error(f"Неизвестный тип группы: {type(group).__name__}")
                raise ValueError(f"Неизвестный тип группы: {type(group).__name__}")

            db.session.commit()
            logger.info(f"Успешно отвязали группу ID={group_id} от сущности ID={entity_id}.")
            return  

        # Если у группы только 1 связь → удаляем все предложения внутри неё
        logger.info(f"Удаляем предложения из группы ID={group_id}, так как она больше нигде не используется.")
        
        # Определяем, какие предложения связаны с группой
        sentence_map = {
            HeadSentenceGroup: ("head_sentences", HeadSentence),
            BodySentenceGroup: ("body_sentences", BodySentence),
            TailSentenceGroup: ("tail_sentences", TailSentence),
        }

        sentence_attr, sentence_cls = sentence_map.get(type(group), (None, None))
        
        if not sentence_attr or not sentence_cls:
            logger.error(f"Неизвестный тип группы: {type(group).__name__}")
            raise ValueError(f"Неизвестный тип группы: {type(group).__name__}")

        sentences = getattr(group, sentence_attr, [])
        logger.debug(f"Найдено {len(sentences)} предложений для удаления.")
        
        for sentence in sentences:
            logger.info(f"Удаляем предложение ID={sentence.id} из группы ID={group_id}.")
            sentence_cls.delete_sentence(sentence.id, group_id)

        # Удаляем саму группу
        db.session.delete(group)
        db.session.commit()
        logger.info(f"Группа ID={group_id} успешно удалена.")


    @classmethod
    def is_linked(cls, group_id):
        """
        Проверяет, связана ли данная группа более чем с одним объектом.
        
        Args:
            group_id (int): ID группы.

        Returns:
            int: Количество объектов, с которыми связана группа.
        """
        logger.info(f"(метод is_linked класса SentenceGroupBase) 🚀 Начата проверка количества связей для группы ID={group_id}")
        if not group_id:
            return 0
        
        if cls == HeadSentenceGroup:
            return Paragraph.query.filter_by(head_sentence_group_id=group_id).count()

        elif cls == TailSentenceGroup:
            return Paragraph.query.filter_by(tail_sentence_group_id=group_id).count()

        elif cls == BodySentenceGroup:
            return HeadSentence.query.filter_by(body_sentence_group_id=group_id).count()
        
        logger.error(f"(метод is_linked класса SentenceGroupBase) ❌ Неизвестный тип группы: {cls.__name__}, возвращаю 0")
        return 0  
   
   
    # Метод для отвязывания группы от родительской сущности (параграфа или предложения)
    @classmethod
    def unlink_groupe(cls, group_id, related_id):
        """
        Отвязывает группу от родительской сущности (параграфа или предложения).
        Args:
            group_id (int): ID группы.
            related_id (int): ID родительской сущности (параграфа или предложения).
        Returns:
            bool: True, если отвязка прошла успешно, иначе False.
        """
        logger.info(f"Отвязываем группу ID={group_id} от сущности ID={related_id}")
        # Определяем, что за сущность (параграф или предложение) и отвязываем
        if cls == HeadSentenceGroup:
            Paragraph.query.filter_by(id=related_id).update({"head_sentence_group_id": None})
        elif cls == TailSentenceGroup:
            Paragraph.query.filter_by(id=related_id).update({"tail_sentence_group_id": None})
        elif cls == BodySentenceGroup:
            HeadSentence.query.filter_by(id=related_id).update({"body_sentence_group_id": None})
        else:
            logger.error(f"Неизвестный тип группы: {cls.__name__}")
            raise ValueError(f"Неизвестный тип группы: {cls.__name__}")

        db.session.commit()
        logger.info(f"Успешно отвязали группу ID={group_id} от сущности ID={related_id}.")
        return 


    # Метод для связывания группы с родительской сущностью (параграфом или предложением)
    @classmethod
    def link_group(cls, group_id, related_id):
        """
        Связывает группу с родительской сущностью (параграфом или предложением).
        Args:
            group_id (int): ID группы.
            related_id (int): ID родительской сущности (параграфа или предложения).
        Returns:
            bool: True, если связь прошла успешно, иначе False.
        """
        logger.info(f"Связываем группу ID={group_id} с сущностью ID={related_id}")
        # Определяем, что за сущность (параграф или предложение) и связываем
        if cls == HeadSentenceGroup:
            Paragraph.query.filter_by(id=related_id).update({"head_sentence_group_id": group_id})
        elif cls == TailSentenceGroup:
            Paragraph.query.filter_by(id=related_id).update({"tail_sentence_group_id": group_id})
        elif cls == BodySentenceGroup:
            HeadSentence.query.filter_by(id=related_id).update({"body_sentence_group_id": group_id})
        else:
            logger.error(f"Неизвестный тип группы: {cls.__name__}")
            raise ValueError(f"Неизвестный тип группы: {cls.__name__}")

        db.session.commit()
        logger.info(f"Успешно связали группу ID={group_id} с сущностью ID={related_id}.")
        return


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
    def get_group_sentences(cls, group_id):
        """
        Возвращает список предложений группы с добавлением индекса из таблицы связей.
        
        Args:
            group_id (int): ID группы.
        
        Returns:
            list[dict]: Список предложений в виде словарей с полными данными + индекс.
        """
        logger.info(f"(get_group_sentences)  🚀 (тип группы: {cls.__name__}) Начато получение предложений для группы ID={group_id}.")

        # Определяем модель предложений
        if cls == HeadSentenceGroup:
            sentence_model = HeadSentence
            index_name = "sentence_index"
        elif cls == BodySentenceGroup:
            sentence_model = BodySentence
            index_name = "sentence_weight"
        elif cls == TailSentenceGroup:
            sentence_model = TailSentence
            index_name = "sentence_weight"
        else:
            logger.error(f"(get_group_sentences) ❌ Неизвестный тип группы: {cls.__name__}")
            return []

        # Загружаем все предложения группы одним запросом
        sentences = sentence_model.query.join(sentence_model.groups).filter(cls.id == group_id).all()

        # Создаём список словарей с добавлением индекса/веса из связи
        sentence_data = []
        for s in sentences:
            index_or_weight = sentence_model.get_sentence_index_or_weight(s.id, group_id)  # Получаем индекс/вес

            sentence_dict = {
                "id": s.id,
                "sentence": s.sentence,
                "tags": s.tags,
                "comment": s.comment,
                "report_type_id": s.report_type_id,
                index_name: index_or_weight  # Добавляем индекс/вес
            }

            # Если предложение head, добавляем `body_sentence_group_id`
            if cls == HeadSentenceGroup:
                sentence_dict["body_sentence_group_id"] = getattr(s, "body_sentence_group_id", None)  # Безопасно

            sentence_data.append(sentence_dict)

        # Сортируем по `index_or_weight`
        sentence_data.sort(key=lambda x: x[f"{index_name}"] or 0)

        logger.info(f"(get_group_sentences) ✅ Получено {len(sentence_data)} предложений для группы ID={group_id}")
        return sentence_data   
        
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