# models.py
# Я сделал так, что при удалении пользовате 
# его предложения остаются в базе данных. Сделал я это 
# чтобы иметь возможность анализировать и возможно переиспользовать 
# их в будущем. Однако этот функционал не реальизван. Нужно будет либо 
# его реализовать либо сделать ondelete cascade и вычистить базу данных 
# от старых "осиротевших" предложений. Кроме того нужно подумать 
# относительно того, чтобы не удалять не только предложения, 
# но и отчеты и параграфы.


from flask_sqlalchemy import SQLAlchemy
from flask_security import UserMixin, RoleMixin, current_user
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy import Index, event, func, cast, Date
from utils.common import ensure_list
from datetime import datetime, timezone  # Добавим для временных меток
import json
from logger import logger



db = SQLAlchemy()

 
# ✅ быстрее 👉 🔥 📌 ❌ 🚀 😎 🔄 1️⃣ 2️⃣ 3️⃣ ⚠️ 💻 🧠 💥 🙌 🗑 ✏️ 🔙 🕘 ➕ 📨

    
class DatabaseDuplicateError(Exception):
    pass    


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
                logger.warning(f"(базовый метод update) ❌ Поле '{key}' отсутствует в {self.__class__.__name__} и будет проигнорировано")

        try:
            db.session.commit()
            logger.info(f"(базовый метод update) ✅ Объект {self.__class__.__name__} ID={self.id} успешно обновлён")
            return 
        except Exception as e:
            db.session.rollback()
            logger.error(f"(базовый метод update) ❌ Ошибка обновления {self.__class__.__name__} ID={self.id}: {e}")
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
    username = db.Column(db.String(80), nullable=True, default='User')
    password = db.Column(db.String, nullable=False)
    user_bio = db.Column(db.Text, nullable=True)
    user_avatar = db.Column(db.LargeBinary, nullable=True)
    active = db.Column(db.Boolean, default=True, nullable=False)
    fs_uniquifier = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    confirmed_at = db.Column(db.DateTime, nullable=True) 
    last_login_at = db.Column(db.DateTime, nullable=True) 
    current_login_at = db.Column(db.DateTime, nullable=True) 
    last_login_ip = db.Column(db.String(45), nullable=True) 
    current_login_ip = db.Column(db.String(45), nullable=True)  
    login_count = db.Column(db.Integer, default=0, nullable=False)  # Счетчик входов


    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))
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


    def find_by_email(email):
        return User.query.filter_by(email=email).first()


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
    
    def __repr__(self):
        return f"<UserProfile - {self.profile_name}>"

    def get_profile_data(self):
        user = self.profile_to_user
        return {
            "id": self.id,
            "profile_name": self.profile_name,
            "description": self.description,
            "default_profile": self.default_profile,
            "username": user.username if user else "No data",
            "email": user.email if user else "No data",
            "login_count": user.login_count if user else "No data"
        }

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
        existing_default_profile = cls.get_default_profile(user_id)
        if default_profile:
            if existing_default_profile:
                logger.warning(f"(create) ❌ Профиль по умолчанию уже существует для пользователя {user_id}. Удаляю старый профиль по умолчанию.")  
                existing_default_profile.default_profile = False
        else:
            if not existing_default_profile:
                default_profile = True
        
        new_profile = cls(
            user_id=user_id,
            profile_name=profile_name,
            description=description,
            default_profile=default_profile
        )
        new_profile.save()  
        logger.info(f"(create) ✅ Профиль {profile_name} успешно создан для пользователя {user_id}.")
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
    
    
    def __repr__(self):
        return f"<ReportType - {self.type_text}>"
        
     
    @classmethod
    def create(cls, type_text, profile_id, type_index=None):
        existing_type = cls.query.filter_by(type_text=type_text, profile_id=profile_id).first()
        if existing_type:
            logger.warning(f"(create) ❌ Тип {type_text} уже существует для профиля {profile_id}.")
            raise DatabaseDuplicateError(f"Тип {type_text} уже существует для профиля {profile_id}.")
        # If type_index is not provided, set it to the next available index
        all_types = cls.query.filter_by(profile_id=profile_id).all()
        if type_index is None:
            all_indexes = [t.type_index for t in all_types if t.type_index is not None]
            max_index = max(all_indexes, default=0)
            type_index = max_index + 1
        
        new_type = cls(
            type_text=type_text,
            profile_id=profile_id,
            type_index=type_index,
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
            subtypes = [{
                    "subtype_id": subtype.id,
                    "subtype_text": subtype.subtype_text,
                    "subtype_index": subtype.subtype_index
                } for subtype in report_type.type_to_subtypes]
            result.append({
                "type_id": report_type.id,
                "type_text": report_type.type_text,
                "subtypes": subtypes,
                "type_index": report_type.type_index 
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
        existing_subtype = cls.query.filter_by(type_id=type_id, subtype_text=subtype_text).first()
        if existing_subtype:
            logger.warning(f"(create) ❌ Подтип {subtype_text} уже существует для типа {type_id}.")
            raise DatabaseDuplicateError(f"Подтип '{subtype_text}' уже существует для типа ID={type_id}.")

        if subtype_index is None:
            all_subtypes = cls.query.filter_by(type_id=type_id).all()
            all_indexes = [s.subtype_index for s in all_subtypes if s.subtype_index is not None]
            max_index = max(all_indexes, default=0)
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
        """Возвращает все подтипы, заданного типа."""
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
        """Ищет все отчеты, принадлежащие конкретному профилю конкретного пользователя."""
        
        reports = cls.query.filter_by(profile_id=profile_id, user_id=current_user.id).all()
        return reports
    
    
    @classmethod
    def get_report_type_id (cls, report_id):
        """Возвращает тип отчета"""
        report = cls.query.filter_by(id=report_id).first()
        return report.report_to_subtype.subtype_to_type.id
    
    @classmethod
    def get_report_type_name (cls, report_id):
        """Возвращает текстовое представление типа отчета"""
        report = cls.query.filter_by(id=report_id).first()
        return report.report_to_subtype.subtype_to_type.type_text
    
    
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
        logger.debug(f"(get_report_info) 🚀 Начинаю выполнение запроса данных протокола report_id={report_id}")
        
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
        logger.debug(f"(get_report_info)✅ Получил данные отчета: report_id={report_id}. Возвращаю данные")
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
        logger.debug(f"(get_report_data) 🚀 Начат процесс получения данных отчета: report_id={report_id}")  
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
        logger.debug(f"(get_report_data) ✅ Получил обобщенные данные отчета: report_id={report_id}. Возвращаю.")
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
        logger.debug(f"(get_report_paragraphs)🚀 Начинаю выполнение запроса параграфов для отчета.")

        # Получаем все параграфы отчета и сортируем по paragraph_index
        paragraphs = Paragraph.query.filter_by(report_id=report_id).order_by(Paragraph.paragraph_index).all()
        sorted_paragraphs = []

        for paragraph in paragraphs:
            
            paragraph_data = paragraph.get_paragraph_data(paragraph.id)
            if paragraph_data is None:
                logger.error(f"(get_report_paragraphs) ❌ Параграф {paragraph.id} не найден.")
                continue

            sorted_paragraphs.append(paragraph_data)
            logger.debug(f"(метод get_report_paragraphs класса Report) Параграф {paragraph.id} обработан и добавлен в список параграфов.")

        logger.debug(f"(метод get_report_paragraphs класса Report) ✅ Получил параграфы для отчета: report_id={report_id}. Возвращаю данные")
        return sorted_paragraphs  


class ReportShare(db.Model):
    __tablename__ = "report_shares"

    id = db.Column(db.BigInteger, primary_key=True)
    report_id = db.Column(db.BigInteger, db.ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    shared_by_user_id = db.Column(db.BigInteger, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    shared_with_user_id = db.Column(db.BigInteger, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    report = db.relationship("Report", backref="shares")
    shared_by = db.relationship("User", foreign_keys=[shared_by_user_id])
    shared_with = db.relationship("User", foreign_keys=[shared_with_user_id])


    from flask_login import current_user

    @classmethod
    def create(cls, report_id, shared_with_user_id):
        """
        Создает объект ReportShare — пользователь current_user делится отчетом с другим пользователем.

        Args:
            report_id (int): ID отчета, которым делятся.
            shared_with_user_id (int): ID пользователя, с которым делятся.

        Returns:
            ReportShare: Созданный объект, если успех. None в случае ошибки.
        """
        logger.info(f"[ReportShare.create] 🚀 Начинаю создание записи о шаринге отчета {report_id} с пользователем {shared_with_user_id}")
        try:
            new_share = cls(
                report_id=report_id,
                shared_by_user_id=current_user.id,
                shared_with_user_id=shared_with_user_id
            )
            db.session.add(new_share)
            db.session.commit()
            return new_share
        except Exception as e:
            logger.error(f"[ReportShare.create] ❌ Ошибка при создании записи о шаринге: {e}")
            db.session.rollback()
            return None


    
class Paragraph(BaseModel):
    __tablename__ = "report_paragraphs"
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    report_id = db.Column(db.BigInteger, db.ForeignKey("reports.id"), nullable=False)
    paragraph_index = db.Column(db.Integer, nullable=False)
    paragraph = db.Column(db.String(255), nullable=False)
    
    paragraph_visible = db.Column(db.Boolean, default=False, nullable=False)
    title_paragraph = db.Column(db.Boolean, default=False, nullable=False)
    bold_paragraph = db.Column(db.Boolean, default=False, nullable=False)
    str_before = db.Column(db.Boolean, nullable=False)
    str_after = db.Column(db.Boolean, nullable=False)
    is_additional = db.Column(db.Boolean, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_impression = db.Column(db.Boolean, default=False, nullable=False)
    
    comment = db.Column(db.String(255), nullable=True)
    paragraph_weight = db.Column(db.SmallInteger, nullable=False) 
    tags = db.Column(db.String(255), nullable=True)
    head_sentence_group_id = db.Column(db.BigInteger, db.ForeignKey("head_sentence_groups.id", ondelete="SET NULL"))
    tail_sentence_group_id = db.Column(db.BigInteger, db.ForeignKey("tail_sentence_groups.id", ondelete="SET NULL"))

    head_sentence_group = db.relationship("HeadSentenceGroup", backref="paragraphs")
    tail_sentence_group = db.relationship("TailSentenceGroup", backref="paragraphs")
    
    
    
    @classmethod
    def create(cls, 
               report_id, 
               paragraph_index, 
               paragraph, 
               is_impression = False, 
               paragraph_visible=True, 
               title_paragraph=False, 
               bold_paragraph=False, 
               str_before=False,
               str_after=False,
               is_additional=False,
               paragraph_weight=1, 
               tags=None, 
               comment=None, 
               is_active=True,
               head_sentence_group_id = None, 
               tail_sentence_group_id = None
        ):
        """
        Создает новый параграф.
        """
        logger.debug(f"(метод create класса Paragraph) 🚀 Начато создание нового параграфа для протокола: report_id={report_id}")
        try:
            new_paragraph = cls(
                report_id=report_id,
                paragraph_index=paragraph_index,
                paragraph=paragraph,
                is_impression=is_impression,
                paragraph_visible=paragraph_visible,
                title_paragraph=title_paragraph,
                bold_paragraph=bold_paragraph,
                paragraph_weight=paragraph_weight,
                str_before=str_before,
                str_after=str_after,
                is_additional=is_additional,
                tags=tags,
                comment=comment,
                is_active=is_active,
                head_sentence_group_id=head_sentence_group_id,
                tail_sentence_group_id=tail_sentence_group_id
            )
            db.session.add(new_paragraph)
            db.session.commit()
            
            logger.debug(f"(метод create класса Paragraph) ✅ Параграф создан: paragraph_id={new_paragraph.id}")
            return new_paragraph
        
        except Exception as e:
            logger.error(f"(метод create класса Paragraph) ❌ Ошибка при создании параграфа: {e}")
            
            db.session.rollback()
            return None
        
    
    @classmethod
    def get_paragraph_data(cls, paragraph_id):
        """
        Получает данные параграфа.
        Args:
            paragraph_id (int): ID параграфа.
        Returns:
            dict: Словарь с данными параграфа или None, если параграф не найден.
        """
        logger.debug(f"(метод get_paragraph_data класса Paragraph) 🚀 Начинаю выполнение запроса данных параграфа: paragraph_id={paragraph_id}")
        
        paragraph = cls.query.filter_by(id=paragraph_id).first()
        if not paragraph:
            logger.error(f"(метод get_paragraph_data класса Paragraph) ❌ Параграф не найден.")
            return None
        
        # Проверяем наличие связанных еще с каким либо параграфом групп head и tail
        has_linked_head = False
        has_linked_tail = False
        if paragraph.head_sentence_group_id:
            logger.debug(f"(метод get_paragraph_data класса Paragraph) Подтверждено наличие группы head предложений для параграфа {paragraph_id}")
            if HeadSentenceGroup.is_linked(paragraph.head_sentence_group_id) > 1:
                logger.debug(f"(метод get_paragraph_data класса Paragraph) 📌 Подтверждено наличие >1 связей для head у данного параграфа. Информация добавлена в аттрибуты")
                has_linked_head = True
        if paragraph.tail_sentence_group_id:
            logger.debug(f"(метод get_paragraph_data класса Paragraph) Подтверждено наличие группы tail предложений для параграфа {paragraph_id}.")
            if TailSentenceGroup.is_linked(paragraph.tail_sentence_group_id) > 1:
                logger.debug(f"(метод get_paragraph_data класса Paragraph) 📌 Подтверждено наличие >1 связей для tail у данного параграфа. Информация добавлена в аттрибуты.")
                has_linked_tail = True


        paragraph_data = {
            "id": paragraph.id,
            "report_id": paragraph.report_id,
            "paragraph_index": paragraph.paragraph_index,
            "paragraph": paragraph.paragraph,
            "paragraph_visible": paragraph.paragraph_visible,
            "title_paragraph": paragraph.title_paragraph,
            "bold_paragraph": paragraph.bold_paragraph,
            "is_impression": paragraph.is_impression,
            "is_active": paragraph.is_active,
            "str_before": paragraph.str_before,
            "str_after": paragraph.str_after,
            "is_additional": paragraph.is_additional,
            "comment": paragraph.comment,
            "paragraph_weight": paragraph.paragraph_weight,
            "tags": paragraph.tags,
            "has_linked_head": has_linked_head,
            "has_linked_tail": has_linked_tail,
            "head_sentence_group_id": paragraph.head_sentence_group_id or None, 
            "tail_sentence_group_id": paragraph.tail_sentence_group_id or None,
            "head_sentences": HeadSentenceGroup.get_group_sentences(paragraph.head_sentence_group_id) if paragraph.head_sentence_group_id else [],
            "tail_sentences": TailSentenceGroup.get_group_sentences(paragraph.tail_sentence_group_id) if paragraph.tail_sentence_group_id else []
        }
        
        logger.debug(f"(метод get_paragraph_data класса Paragraph) ✅ Получил данные параграфа: paragraph_id={paragraph_id}. Возвращаю данные")
        return paragraph_data
    
    
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
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
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
        logger.debug(f"(метод delete_sentence класса SentenceBase) 🚀 Начато удаление предложения ID={sentence_id}. Предложение относится к группе {group_id}")
        sentence = cls.query.get(sentence_id)
        if not sentence:
            logger.error(f"(метод delete_sentence класса SentenceBase) ❌ Предложение ID={sentence_id} не найдено.")
            raise ValueError(f"Предложение ID={sentence_id} не найдено.")
        
        # Если вместе с предложением НЕ передали ID группы → удаляем его полностью
        if group_id is None:
            logger.error(f"(метод delete_sentence класса SentenceBase) ❌ Не передана ID группы предложения. Удаление остановлено.")
            raise ValueError("Не передана ID группы предложения. Удаление остановлено.")

        linked_count = cls.is_linked(sentence_id)
        logger.debug(f"(метод delete_sentence класса SentenceBase) Количество связей предложения ID={sentence_id}: {linked_count}")

        # Если у предложения только 1 или 0 связей → удаляем его полностью
        if linked_count <= 1: 
            if cls != HeadSentence:
                logger.debug(f"(метод delete_sentence класса SentenceBase) ✅ Просто удаляю предложение ID={sentence_id}, так как у него 0 или 1 связь.")
                sentence.delete()
                return 
            else:
                logger.debug(f"(метод delete_sentence класса SentenceBase) Предложение относится к группе head. Проверяю наличие body группы.")
                related_body_group_id = sentence.body_sentence_group_id
                body_group_links_count = BodySentenceGroup.is_linked(related_body_group_id)
                if body_group_links_count > 1:
                    logger.debug(f"(метод delete_sentence класса SentenceBase) body группа данного предложения связана с другими главными предложениями. Отвязываю группу и удаляю предложение.")
                    BodySentenceGroup.unlink_group(related_body_group_id, sentence_id)
                    sentence.delete()
                    logger.info(f"(метод delete_sentence класса SentenceBase) ✅ head-предложение ID={sentence_id} удалено.")
                    return
                else:
                    logger.debug(f"(метод delete_sentence класса SentenceBase) body группа данного предложения связана только с этим главным предложением. Удаляю группу и предложение.")
                    try:
                        BodySentenceGroup.delete_group(related_body_group_id, sentence_id)
                    except Exception as e:
                        logger.error(f"(метод delete_sentence класса SentenceBase) ❌ Ошибка при удалении body группы: {e}")
                    sentence.delete()
                    logger.info(f"(метод delete_sentence класса SentenceBase) ✅ head-предложение ID={sentence_id} удалено.")
                    return

        # Если предложению передали ID группы и у него больше 1 связи → просто отвязываем
        logger.info(f"(метод delete_sentence класса SentenceBase) ⚠️ Данное предложение связано с другими группами, удаление отменено, просто отвязываю его от группы ID={group_id}")
        try:
            cls.unlink_from_group(sentence_id, group_id)
            logger.info(f"(метод delete_sentence класса SentenceBase) ✅ Предложение ID={sentence_id} успешно отвязано от группы ID={group_id}")
            return
        except Exception as e:
            logger.error(f"(метод delete_sentence класса SentenceBase) ❌ Ошибка при отвязке предложения ID={sentence_id} от группы ID={group_id}: {e}")
            raise ValueError(f"Ошибка при отвязке предложения ID={sentence_id} от группы ID={group_id}: {e}")
        

    @classmethod
    def get_sentence_data(cls, sentence_id, group_id):
        """
        Получает данные предложения.
        Args:
            sentence_id (int): ID предложения.
            related_id (int, optional): ID связанного предложения (для head/body/tail).
        Returns:
            dict: Словарь с данными предложения.
        """
        logger.debug(f"(метод get_sentence_data класса SentenceBase) 🚀 Начинаю получение данных предложения ID={sentence_id}")
        sentence = cls.query.get(sentence_id)
        if not sentence:
            logger.error(f"(метод get_sentence_data класса SentenceBase) ❌ Предложение ID={sentence_id} не найдено.")
            return None
        
        index_or_weight = cls.get_sentence_index_or_weight(sentence_id, group_id)
        sentence_data = {
            "id": sentence.id,
            "sentence": sentence.sentence,
            "tags": sentence.tags,
            "comment": sentence.comment,
            "is_linked": cls.is_linked(sentence_id) > 1,
            "group_id": group_id
        }
            
        if cls == HeadSentence:
            has_linked_body = False
            body_sentence_group_id = None
            body_sentences = []
            
            if sentence.body_sentence_group_id:
                body_sentence_group_id = sentence.body_sentence_group_id
                
                logger.debug(f"(метод get_sentence_data класса SentenceBase) Подтверждено наличие группы body предложений для head-предложения {sentence_id}.")
                if BodySentenceGroup.is_linked(sentence.body_sentence_group_id) > 1:
                    logger.debug(f"(метод get_sentence_data класса SentenceBase) 📌 Подтверждено наличие >1 связей для body у данного head-предложения. Информация добавлена в аттрибуты.")
                    has_linked_body = True
                else:
                    logger.debug(f"(метод get_sentence_data класса SentenceBase) 📌 Подтверждено наличие только 1 связи для body у данного head-предложения. Информация добавлена в аттрибуты.")
                    
                body_sentences = BodySentenceGroup.get_group_sentences(sentence.body_sentence_group_id)
                
            sentence_data["body_sentences"] = body_sentences
            sentence_data["body_sentence_group_id"] = body_sentence_group_id
            sentence_data["has_linked_body"] = has_linked_body
            sentence_data["sentence_index"] = index_or_weight
            
        elif cls == BodySentence or cls == TailSentence:
            sentence_data["sentence_weight"] = index_or_weight
        elif cls == TailSentence:
            sentence_data["sentence_weight"] = index_or_weight
            
        logger.debug(f"(метод get_sentence_data класса SentenceBase) ✅ Получил данные предложения ID={sentence_id}. Возвращаю данные.")
        return sentence_data
   
   
    @classmethod
    def edit_sentence(cls, 
                      sentence_id, 
                      group_id, 
                      related_id, 
                      new_text=None, 
                      new_tags=None, 
                      new_comment=None, 
                      use_dublicate=True,
                      ):
        """
        Универсальный метод редактирования предложений (Head, Body, Tail).
        Возвращает:
            SentenceBase: Обновлённое или новое предложение.
        """
        logger.debug(f"(метод edit_sentence класса SentenceBase) 🔧 Начато редактирование предложения {cls.__name__} ID={sentence_id}")
        if not related_id or not group_id:
            logger.error(f"(метод edit_sentence класса SentenceBase) ❌ Не переданы обязательные аргументы related_id или group_id.")
            raise ValueError(f"Не переданы обязательные аргументы related_id или group_id.")
        
        sentence = cls.query.get(sentence_id)
        
        if not sentence:
            logger.error(f"(метод edit_sentence класса SentenceBase) ❌ Предложение ID={sentence_id} не найдено.")
            raise ValueError(f"{cls.__name__}: предложение ID={sentence_id} не найдено.")

        if new_text is None and new_tags is None and new_comment is None:
            logger.debug(f"(метод edit_sentence класса SentenceBase) ⚠️ Не переданы новые данные для редактирования. Возвращаю предложение без изменений.")
            return sentence
    
        from sentence_processing import find_similar_exist_sentence 
        logger.info(f"(метод edit_sentence класса SentenceBase) 🛠 Начинаю 'мягкое' редактирование предложения ID={sentence_id}")
        # определяем тип предложения
        if cls == HeadSentence:
            sentence_type = "head"
        elif cls == BodySentence:
            sentence_type = "body"
        elif cls == TailSentence:
            sentence_type = "tail"
        else:
            logger.error(f"(метод edit_sentence класса SentenceBase) ❌ Неизвестный тип предложения.")
            raise ValueError("Неизвестный тип предложения.")
        # Проверяем наличие уже в базе такого предложения каким должно стать предложение после редактирования
        new_sentence_data = {
            "sentence_text": new_text if new_text is not None else sentence.sentence,
            "sentence_type": sentence_type,
            "report_type_id": sentence.report_type_id
            }
        similar_sentence = None
        if use_dublicate:
            similar_sentence = find_similar_exist_sentence(**new_sentence_data)
            
        if similar_sentence and similar_sentence.id != int(sentence_id):
            logger.debug(f"(метод edit_sentence класса SentenceBase) 🧩 Предложение уже существует в базе данных. Привязываю найденное предложение.")
            index_or_weight = cls.get_sentence_index_or_weight(sentence_id, group_id)
            cls.link_to_group(similar_sentence.id, group_id, sentence_weight=index_or_weight, sentence_index=index_or_weight)
            cls.delete_sentence(sentence_id, group_id)
            logger.info(f"(метод edit_sentence класса SentenceBase) ✅ Предложение ID={sentence_id} успешно отредактировано ('Мягкое' редактирование).")
            return similar_sentence
        else:
            logger.debug(f"(метод edit_sentence класса SentenceBase) Аналога предложения с новыми данными не найдено. Продолжаю редактирование.")
            if new_text is not None:
                sentence.sentence = new_text
            if new_tags is not None:
                sentence.tags = new_tags
            if new_comment is not None:
                sentence.comment = new_comment
            logger.info(f"(метод edit_sentence класса SentenceBase) ✅ Предложение ID={sentence_id} успешно отредактировано ('Мягкое' редактирование).")
            db.session.commit()
            return sentence
        
        
    
    
    @classmethod
    def create(cls, 
               user_id, 
               report_type_id, 
               sentence, 
               related_id, 
               sentence_index=None, 
               tags=None, 
               comment=None, 
               sentence_weight=1,
               unique=False,
        ):
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
        from sentence_processing import find_similar_exist_sentence 
        
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
       

        # Проверяем наличие уже в базе такого предложения
        if not unique:
            logger.info(f"(метод create класса SentenceBase)🧩 Начат поиск похожего предложения в базе данных")
            similar_sentence = find_similar_exist_sentence(
                sentence_text=sentence, 
                sentence_type=sentence_type, 
                report_type_id=report_type_id
            )
            if similar_sentence:
                logger.info(f"(метод create класса SentenceBase) 🧩🧩🧩 Найдено похожее предложение с ID {similar_sentence.id} в базе данных. Создание нового предложения не требуется.")
                db.session.add(similar_sentence)
                db.session.flush()
                logger.info(f"(метод create класса SentenceBase) Начато добавление предложения в группу")
                
                similar_sentence_linked, similar_sentence_group = cls.link_to_group(sentence_id=similar_sentence.id, group_id=group.id, sentence_weight=sentence_weight, sentence_index=sentence_index)
                
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
            new_sentence_linked, new_sentence_group = cls.link_to_group(new_sentence.id, group.id, sentence_weight, sentence_index)
            logger.info(f"(метод create класса SentenceBase) ✅ Предложение успешно добавлено в группу")
            return new_sentence_linked, new_sentence_group
        except Exception as e:
            logger.error(f"(метод create класса SentenceBase) ❌ Ошибка при добавлении предложения в группу: {e}")
            raise ValueError(f"Ошибка при добавлении предложения в группу: {e}")
        
    
    @classmethod
    def link_to_group(cls, sentence_id, group_id, sentence_weight=None, sentence_index=None):
        """
        Добавляет предложение в указанную группу.

        Args:
            sentence (SentenceBase): Предложение для привязки.
            group (BaseModel): Группа, к которой привязываем предложение.

        Returns:
            tuple: (предложение, использованная группа)
        """
        logger.debug(f"(метод link_to_group класса SentenceBase) 🚀 Начата привязка предложения к группе {group_id}")
        sentence = cls.query.get(sentence_id)
        
        if not sentence:
            logger.error(f"(метод link_to_group класса SentenceBase) ❌ Предложение ID={sentence_id} не найдено.")
            raise ValueError(f"Предложение ID={sentence_id} не найдено.")

        # Проверяем, привязано ли уже предложение к группе
        if cls == HeadSentence:
            group = HeadSentenceGroup.query.get(group_id)
            if group and sentence in group.head_sentences:
                logger.debug(f"(метод link_to_group класса SentenceBase) ✅ Предложение {sentence.id} уже в группе {group.id}, пропускаем")
                return sentence, group
            elif group:
                logger.debug(f"(метод link_to_group класса SentenceBase) 📌 Группа {group.id} уже существует, но предложение {sentence.id} не привязано к ней.")
                # Проверяем обязательные параметры
                if sentence_index is None:
                    logger.error(f"(метод link_to_group класса SentenceBase) ❌ Не указан индекс для HeadSentence")
                    raise ValueError("Не указан sentence_index для HeadSentence")
                stmt = head_sentence_group_link.insert().values(
                head_sentence_id=sentence.id,
                group_id=group.id,
                sentence_index=sentence_index  
                )
                db.session.execute(stmt)
                
        elif cls == BodySentence:
            group = BodySentenceGroup.query.get(group_id)
            if group and sentence in group.body_sentences:
                logger.debug(f"(метод link_to_group класса SentenceBase) ✅ Предложение {sentence.id} уже в группе {group.id}, пропускаем")
                return sentence, group
            elif group:
                logger.debug(f"(метод link_to_group класса SentenceBase) 📌 Группа {group.id} уже существует, но предложение {sentence.id} не привязано к ней.")
                # Проверяем обязательные параметры
                if sentence_weight is None:
                    logger.error(f"(метод link_to_group класса SentenceBase) ❌ Не указан вес для Body предложения")
                    raise ValueError("Не указан sentence_weight для Body предложения")
                stmt = body_sentence_group_link.insert().values(
                body_sentence_id=sentence.id,
                group_id=group.id,
                sentence_weight=sentence_weight  
                )
                db.session.execute(stmt)
                
        elif cls == TailSentence:
            group = TailSentenceGroup.query.get(group_id)
            if group and sentence in group.tail_sentences:
                logger.debug(f"(метод link_to_group класса SentenceBase) ✅ Предложение {sentence.id} уже в группе {group.id}, пропускаем")
                return sentence, group
            elif group:
                logger.debug(f"(метод link_to_group класса SentenceBase) 📌 Группа {group.id} уже существует, но предложение {sentence.id} не привязано к ней.")
                if sentence_weight is None:
                    logger.error(f"(метод link_to_group класса SentenceBase) ❌ Не указан вес для Tail предложения")
                    raise ValueError("Не указан sentence_weight для Tail предложения")
                stmt = tail_sentence_group_link.insert().values(
                tail_sentence_id=sentence.id,
                group_id=group.id,
                sentence_weight=sentence_weight 
                )
                db.session.execute(stmt)
                
        else:
            logger.error(f"(метод link_to_group класса SentenceBase) ❌ Неизвестный тип предложения")
            raise ValueError("Неизвестный тип предложения")
        
        db.session.commit()
        logger.debug(f"(метод link_to_group класса SentenceBase) ✅ Предложение {sentence.id} успешно привязано к группе {group.id}")
        return sentence, group
    
    

    @classmethod
    def unlink_from_group(cls, sentence_id, group_id):
        """
        Удаляет связь существующего предложения с конкретной группой.

        Args:
            sentence (SentenceBase): Предложение для отвязки.
            group (BaseModel): Группа, от которой отвязываем предложение.

        Returns:
            bool: True, если изменение было внесено, иначе False.
        """
        logger.debug(f"(метод unlink_fro_group класса SentenceBase) 🚀 Начата отвязка предложения {sentence_id} от группы {group_id}")

        sentence = cls.query.get(sentence_id)
        if not sentence:
            logger.error(f"(метод unlink_fro_group класса SentenceBase) ❌ Предложение ID={sentence_id} не найдено.")
            raise ValueError(f"Предложение ID={sentence_id} не найдено.")
        
        if isinstance(sentence, HeadSentence):
            group = HeadSentenceGroup.query.get(group_id)
            if group and sentence in group.head_sentences:
                group.head_sentences.remove(sentence)
                logger.debug(f"(метод unlink_fro_group класса SentenceBase) ✅ Предложение {cls.__name__} с ID: {sentence.id} удалено из группы {group.id}")
                db.session.commit()
                return True
        elif isinstance(sentence, BodySentence):
            group = BodySentenceGroup.query.get(group_id)
            if group and sentence in group.body_sentences:
                group.body_sentences.remove(sentence)
                logger.debug(f"(метод unlink_fro_group класса SentenceBase) ✅ Предложение {cls.__name__} с ID: {sentence.id} удалено из группы {group.id}")
                db.session.commit()
                return True
        elif isinstance(sentence, TailSentence):
            group = TailSentenceGroup.query.get(group_id)
            if group and sentence in group.tail_sentences:
                group.tail_sentences.remove(sentence)
                logger.debug(f"(метод unlink_fro_group класса SentenceBase) ✅ Предложение {cls.__name__} с ID: {sentence.id} удалено из группы {group.id}")
                db.session.commit()
                return True
        else:
            logger.error(f"(метод unlink_fro_group класса SentenceBase) ❌ Изменения не были внесены")
            return False


    
    @classmethod
    def is_linked(cls, sentence_id):
        """
        Проверяет, с каким количеством групп связано предложение.
        Args:
            sentence_id (int): ID предложения.
        Returns:
            int: Количество групп, с которыми связано предложение.
        """
        logger.debug(f"Проверка количества связей для предложения ID={sentence_id}")
        sentence = cls.query.get(sentence_id)
        if not sentence:
            return 0
        
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
        logger.debug(f"(get_sentence_index_or_weight)(тип группы: {cls.__name__}) 🚀 Начат запрос {'индекса' if cls==HeadSentence else 'веса'} предложения ID={sentence_id} из группы ID={group_id}")

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

        logger.debug(f"(get_sentence_index_or_weight) ✅ {'индекс' if cls==HeadSentence else 'вес'} найден: {result}")
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
        logger.debug(f"(Обновление позиции - set_sentence_index_or_weight) (тип предложения {cls.__name__}) 🚀 Обновление позиции предложения ID={sentence_id} в группе ID={group_id} начато")
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
                logger.debug(f"(Обновление позиции - set_sentence_index_or_weight)(тип предложения 'HeadSentence') ✅  положение предложения с ID={sentence_id} обновлено: новый индекс предложения -> {new_index}")
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
            logger.debug(f"(Обновление позиции - set_sentence_index_or_weight)(тип предложения 'BodySentence') ✅  положение предложения с ID={sentence_id} обновлено: новый вес предложения -> {new_weight}")

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
            logger.debug(f"(Обновление позиции - set_sentence_index_or_weight)(тип предложения 'TailSentence') ✅  положение предложения с ID={sentence_id} обновлено: новый вес предложения -> {new_weight}")

        else:
            logger.error(f"(Обновление позиции - set_sentence_index_or_weight) ❌ Неизвестный тип предложения: {cls.__name__}")
            raise ValueError(f"Неизвестный тип предложения: {cls.__name__}")

        db.session.commit()
        logger.debug(f"(Обновление позиции - set_sentence_index_or_weight)(тип предложения: {cls.__name__}) ✅ Обновление позиции завершено.")




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
    
    
    @staticmethod
    def increase_weight(sentence_id, group_id):
        logger.debug(f"(increase_weight) 🚀 Начато увеличение веса предложения ID={sentence_id} в группе ID={group_id}")
        link_table = body_sentence_group_link
        try:
            stmt = (
                link_table.update()
                .where(link_table.c.group_id == group_id)
                .where(link_table.c.body_sentence_id == sentence_id)
                .values(sentence_weight=link_table.c.sentence_weight + 1)
            )

            db.session.execute(stmt)
            db.session.commit()
            logger.debug(f"(increase_weight) ✅ Вес предложения ID={sentence_id} увеличен на 1 в группе ID={group_id}")
        except Exception as e:
            logger.error(f"(increase_weight) ❌ Ошибка при увеличении веса предложения ID={sentence_id} в группе ID={group_id}: {e}")
            raise ValueError(f"Ошибка при увеличении веса предложения ID={sentence_id} в группе ID={group_id}: {e}")
    
    

class TailSentence(SentenceBase):
    __tablename__ = "tail_sentences"

    groups = db.relationship(
        "TailSentenceGroup",
        secondary="tail_sentence_group_link",
        back_populates="tail_sentences"
    )
    
    
    @staticmethod
    def increase_weight(sentence_id, group_id):
        logger.debug(f"(increase_weight) 🚀 Начато увеличение веса предложения ID={sentence_id} в группе ID={group_id}")
        link_table = tail_sentence_group_link
        try:
            stmt = (
                link_table.update()
                .where(link_table.c.group_id == group_id)
                .where(link_table.c.tail_sentence_id == sentence_id)
                .values(sentence_weight=link_table.c.sentence_weight + 1)
            )

            db.session.execute(stmt)
            db.session.commit()
            logger.debug(f"(increase_weight) ✅ Вес предложения ID={sentence_id} увеличен на 1 в группе ID={group_id}")
        except Exception as e:
            logger.error(f"(increase_weight) ❌ Ошибка при увеличении веса предложения ID={sentence_id} в группе ID={group_id}: {e}")
            raise ValueError(f"Ошибка при увеличении веса предложения ID={sentence_id} в группе ID={group_id}: {e}")
    
    
  
  
        
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
        logger.info(f"(метод delete_group класса SentenceGroupBase) 🚀 Начата попытка удаления группы ID={group_id} для родительской сущности ID={entity_id}")
        group = cls.query.get(group_id)
        if not group:
            logger.info(f"(метод delete_group класса SentenceGroupBase) ❌ Группа ID={group_id} не найдена.")
            raise ValueError(f"Группа ID={group_id} не найдена.")


        # Если не передана информация о сущности → удаляем группу полностью
        if entity_id is None:
            logger.info(f"(метод delete_group класса SentenceGroupBase) ❌ Не передана информация о родительской сущности. Ошибка.")
            raise ValueError("Удаление группы невозможно так как не передана информация о родительской сущности.")
        
        # Проверяем, с каким количеством сущностей связана группа
        linked_count = cls.is_linked(group_id)
        logger.info(f"(метод delete_group класса SentenceGroupBase) Группа ID={group_id} связана с {linked_count} сущностями.")

        # Если группа связана больше чем с одной сущностью → просто отвязываем entity_id
        if linked_count > 1:
            logger.info(f"(метод delete_group класса SentenceGroupBase) ⚠️ Группа связана с несколькими сущностями. Удаление остановлено, просто отвязываем группу.")
            
            # Определяем, что за сущность (параграф или предложение) и отвязываем
            if cls == HeadSentenceGroup:
                cls.unlink_group(group_id, entity_id)
            elif cls == BodySentenceGroup:
                cls.unlink_group(group_id, entity_id)
            elif cls == TailSentenceGroup:
                cls.unlink_group(group_id, entity_id)
            else:    
                logger.error(f"(метод delete_group класса SentenceGroupBase) ❌ Неизвестный тип группы: {type(group).__name__}")
                raise ValueError(f"Неизвестный тип группы: {type(group).__name__}")

            db.session.commit()
            logger.info(f"(метод delete_group класса SentenceGroupBase)({cls.__name__}) ✅ Группа ID={group_id} успешно отвязана от сущности ID={entity_id}. Операция завершена.")
            return  

        # Если у группы только 1 связь → удаляем все предложения внутри неё
        logger.info(f"(метод delete_group класса SentenceGroupBase) 🚀 Группа связана только с одной сущностью. Начинаем удаление всех предложений внутри группы.")
        
        # Определяем, какие предложения связаны с группой
        sentence_map = {
            HeadSentenceGroup: ("head_sentences", HeadSentence),
            BodySentenceGroup: ("body_sentences", BodySentence),
            TailSentenceGroup: ("tail_sentences", TailSentence),
        }

        sentence_attr, sentence_cls = sentence_map.get(type(group), (None, None))
        
        if not sentence_attr or not sentence_cls:
            logger.error(f"(метод delete_group класса SentenceGroupBase) ❌ Неизвестный тип группы: {type(group).__name__}")
            raise ValueError(f"Неизвестный тип группы: {type(group).__name__}")

        sentences = getattr(group, sentence_attr, [])
        logger.debug(f"(метод delete_group класса SentenceGroupBase) Найдено {len(sentences)} предложений в группе ID={group_id} для удаления.")
        
        for sentence in sentences:
            logger.info(f"(метод delete_group класса SentenceGroupBase) Удаляем предложение ID={sentence.id} из группы ID={group_id}")
            try:
                sentence_cls.delete_sentence(sentence.id, group_id)
            except Exception as e:
                logger.error(f"(метод delete_group класса SentenceGroupBase) ❌ Ошибка при удалении предложения: {e}")
                raise ValueError(f"Ошибка при удалении предложения: {e}")

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
        logger.debug(f"(метод is_linked класса SentenceGroupBase) 🚀 Начата проверка количества связей для группы ID={group_id}")
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
    def unlink_group(cls, group_id, related_id):
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
    def copy_group(cls, group_id, new_group_id=None):
        """
        Создает копию указанной группы и привязывает туда все предложения из заданной группы.

        Args:
            group (BaseModel): Группа, из которой перепривязываем.
            new_group (BaseModel): Группа, в которую перепривязываем.
        """
        logger.info(f"(метод relink_all_to_group класса SentenceBase) 🚀 Начата перепривязка всех предложений из группы {group_id} в группу {new_group_id}")
        group = cls.query.get(group_id)
        if new_group_id:
            new_group = cls.query.get(new_group_id)
        else:
            new_group = cls.create()
            new_group_id = new_group.id
        
        if not group or not new_group:
            logger.error(f"(метод relink_all_to_group класса SentenceBase) ❌ Группа {group_id} или {new_group_id} не найдена.")
            raise ValueError(f"Группа {group_id} или {new_group_id} не найдена.")
        
        if isinstance(group, HeadSentenceGroup):
            sentences = group.head_sentences
            for sentence in sentences:
                sentence_index = HeadSentence.get_sentence_index_or_weight(sentence.id, group_id)
                db.session.execute(
                    head_sentence_group_link.insert().values(
                    head_sentence_id=sentence.id,
                    group_id=new_group_id,
                    sentence_index=sentence_index)
                )
        elif isinstance(group, BodySentenceGroup):
            sentences = group.body_sentences
            for sentence in sentences:
                sentence_weight = BodySentence.get_sentence_index_or_weight(sentence.id, group_id)
                db.session.execute(
                    body_sentence_group_link.insert().values(
                    body_sentence_id=sentence.id,
                    group_id=new_group_id,
                    sentence_weight=sentence_weight)
                )
        elif isinstance(group, TailSentenceGroup):
            sentences = group.tail_sentences
            for sentence in sentences:
                sentence_weight = TailSentence.get_sentence_index_or_weight(sentence.id, group_id)
                db.session.execute(
                    tail_sentence_group_link.insert().values(
                    tail_sentence_id=sentence.id,
                    group_id=new_group_id,
                    sentence_weight=sentence_weight)
                )
        else:
            logger.error(f"(метод relink_all_to_group класса SentenceBase) ❌ Изменения не были внесены так как не была идентифицирована группа")
            raise ValueError(f"Изменения не были внесены так как не была идентифицирована группа")
        
        db.session.commit()
        logger.info(f"(метод relink_all_to_group класса SentenceBase) ✅ Все предложения из группы {group_id} успешно перепривязаны в группу {new_group_id}")
        return new_group_id
    

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
        logger.debug(f"(get_group_sentences)  🚀 (тип группы: {cls.__name__}) Начато получение предложений для группы ID={group_id}.")

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
            s_data = sentence_model.get_sentence_data(s.id, group_id)
            sentence_data.append(s_data)

        # Сортируем по `index_or_weight`
        if index_name == "sentence_index":
            sentence_data.sort(key=lambda x: x[f"{index_name}"] or 0)
        else:
            # Для Body и Tail предложений сортируем по весу в обратном порядке
            sentence_data.sort(key=lambda x: x[f"{index_name}"] or 0, reverse=True)

        logger.debug(f"(get_group_sentences) ✅ Получено {len(sentence_data)} предложений для группы ID={group_id}")
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
    ai_file_id = db.Column(db.String(100), nullable=True)
    

    @classmethod
    def create(cls, profile_id, file_name, file_path, file_type, file_description, ai_file_id=None):
        new_file = cls(
            profile_id=profile_id,
            file_name=file_name,
            file_path=file_path,
            file_type=file_type,
            file_description=file_description,
            ai_file_id=ai_file_id
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


class ReportTextSnapshot(BaseModel):
    __tablename__ = "report_text_snapshots"

    report_id = db.Column(db.BigInteger, db.ForeignKey("reports.id", ondelete="SET NULL"), nullable=True)
    report_type = db.Column(db.SmallInteger, nullable=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    text = db.Column(db.Text, nullable=False)  
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    report = db.relationship("Report", backref=db.backref("snapshots", lazy=True))
    user = db.relationship("User", backref=db.backref("text_snapshots", lazy=True))

    def __repr__(self):
        return f"<ReportTextSnapshot id={self.id} report_id={self.report_id} created_at={self.created_at}>"


    @classmethod
    def create(cls, report_id, user_id, text):
        """
        Создает и сохраняет снапшот текста отчета.

        Args:
            report_id (int): ID отчета, к которому относится снапшот.
            user_id (int): ID пользователя, сохранившего снапшот.
            text (str): Текст отчета на момент создания снапшота.

        Returns:
            ReportTextSnapshot: созданный объект снапшота.
        """
        try:
            from models import Report  # избегаем циклического импорта
            logger.info(f"(ReportTextSnapshot.create) 🚀 Начато создание снапшота текста отчета ID={report_id}")
            report = Report.query.get(report_id)
            if not report:
                logger.error(f"(ReportTextSnapshot.create) ❌ Report с id={report_id} не найден")
                raise ValueError(f"Report с id={report_id} не найден")

            report_type = report.report_to_subtype.subtype_to_type.id

            snapshot = cls(
                report_id=report_id,
                report_type=report_type,
                user_id=user_id,
                text=text
            )
            db.session.add(snapshot)
            db.session.commit()
            logger.info(f"(ReportTextSnapshot.create) ✅ Создан снапшот текста отчета ID={report_id}")
            return snapshot
        except Exception as e:
            db.session.rollback()
            logger.error(f"(ReportTextSnapshot.create) ❌ Ошибка при создании снапшота: {e}")
            raise ValueError(f"Ошибка при создании снапшота: {e}")



    @classmethod
    def find_by_date_and_type(cls, user_id, date, report_type):
        """
        Ищет снапшоты по пользователю, дате и типу протокола.
        Args:
            user_id (int): ID пользователя.
            date (datetime.date): Дата создания снапшота.
            report_type (int): Тип протокола.
        Returns:
            list[ReportTextSnapshot]: Список найденных снапшотов.
        """
        

        return (
            cls.query
            .filter(
                cls.user_id == user_id,
                cast(cls.created_at, Date) == date,
                cls.report_type == report_type
            )
            .order_by(cls.created_at.desc())
            .all()
        )




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