# models.py

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy import Index
from utils import ensure_list
import uuid

db = SQLAlchemy()

# Association table between KeyWord and Report
key_word_report_link = db.Table(
    'key_word_report_link',
    db.Column('key_word_id', db.BigInteger, db.ForeignKey('key_words_group.id', ondelete="CASCADE"), primary_key=True),
    db.Column('report_id', db.BigInteger, db.ForeignKey('reports.id', ondelete="CASCADE"), primary_key=True),
    Index('ix_key_word_report_link_keyword_report', 'key_word_id', 'report_id')
)

# Association table between Users and Roles
roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.BigInteger, db.ForeignKey('users.id', ondelete="CASCADE"), primary_key=True),
    db.Column('role_id', db.BigInteger, db.ForeignKey('roles.id', ondelete="CASCADE"), primary_key=True),
    Index('ix_roles_users_user_id_role_id', 'user_id', 'role_id')
)

class AppConfig(db.Model):
    __tablename__ = 'app_config'
    id = db.Column(db.Integer, primary_key=True)
    config_key = db.Column(db.String(50), unique=True, nullable=False)
    config_value = db.Column(db.String(200), nullable=False)
    config_user = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)

    user = db.relationship('User', lazy=True, backref=db.backref('app_config'))

    @staticmethod
    def get_config_value(key, user_id):
        config = AppConfig.query.filter_by(config_key=key, config_user=user_id).first()
        return config.config_value if config else None

    @staticmethod
    def set_config_value(key, value, user_id):
        config = AppConfig.query.filter_by(config_key=key, config_user=user_id).first()
        if config:
            config.config_value = value
        else:
            config = AppConfig(config_key=key, config_value=value, config_user=user_id)
        db.session.add(config)
        db.session.commit()


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
            db.session.delete(obj)
            db.session.commit()
            return True
        return False


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)  
    description = db.Column(db.String(255), nullable=True) 


class User(BaseModel, db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.BigInteger, primary_key=True)
    user_name = db.Column(db.String, nullable=False)
    user_pass = db.Column(db.String, nullable=False)
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



    def set_password(self, password):
        self.user_pass = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.user_pass, password)
    
    @classmethod
    def create(cls, email, username, password, active=True):
        """
        Creates a new user and saves them to the database.
        Args:
            email (str): The email of the user.
            username (str): The username.
            password (str): The password (will be hashed).
            role (str): The role of the user, defaults to 'user'.
        Returns:
            User: The created user object.
        """
        # Проверяем, существует ли пользователь с таким email
        if cls.query.filter_by(email=email).first():
            raise ValueError("A user with that email already exists")
        
        user = cls(
            email=email,
            user_name=username,
            active=active,
            fs_uniquifier=str(uuid.uuid4())
        )
        user.set_password(password)  # Хэшируем пароль
        db.session.add(user)
        db.session.commit()
        return user


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
        new_profile = cls(
            user_id=user_id,
            profile_name=profile_name,
            description=description,
            default_profile=default_profile
        )
        new_profile.save()  # Используем метод save для сохранения профиля с логикой проверки
        return new_profile

    def save(self):
        """
        Сохраняет профиль в базу данных с проверкой на наличие другого профиля по умолчанию.
        
        Raises:
            ValueError: Если профиль по умолчанию уже существует для данного пользователя.
        """
        # Проверка на наличие другого профиля по умолчанию, если флаг default установлен в True
        if self.default_profile:
            existing_default_profile = UserProfile.get_default_profile(self.user_id)
            if existing_default_profile and existing_default_profile.id != self.id:
                raise ValueError("Профиль по умолчанию уже существует для данного пользователя.")
        
        # Вызываем метод save из базовой модели
        super(UserProfile, self).save()
        
    @classmethod
    def get_default_profile(cls, user_id):
        """
        Возвращает профиль по умолчанию для пользователя.
        Args:
            user_id (int): ID пользователя.
        Returns:
            UserProfile: Профиль по умолчанию или None, если его нет.
        """
        return cls.query.filter_by(user_id=user_id, default_profile=True).first()


    @classmethod
    def get_user_profiles(cls, user_id):
        """Возвращает все профили, принадлежащие пользователю."""
        return cls.query.filter_by(user_id=user_id).all()

    @classmethod
    def find_by_id(cls, profile_id):
        """Ищет профиль по его ID."""
        return cls.query.get(profile_id)
    
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
    def find_by_subtypes(cls, report_subtype):
        """Возвращает все отчеты, связанные с данным подтипом"""
        return cls.query.filter_by(report_subtype=report_subtype).all()
    
    def get_impression(self):
        """
        Возвращает заключение (impression) по отчету.
        Ищет параграф с типом 'impression' в связанных параграфах отчета.
        
        Returns:
            str: Текст параграфа с типом 'impression' или None, если такого параграфа нет.
        """
        # Ищем тип параграфа 'impression'
        impression_type = ParagraphType.query.filter_by(type_name="impression").first()

        if not impression_type:
            # Если тип 'impression' не найден, возвращаем None
            return []

        # Ищем параграф с этим типом для данного отчета
        impression_paragraph = Paragraph.query.filter_by(
            report_id=self.id, 
            type_paragraph_id=impression_type.id
        ).first()

        # Возвращаем текст параграфа, если найден
        return impression_paragraph.paragraph_to_sentences if impression_paragraph else []

    @classmethod
    def get_report_data(cls, report_id, profile_id):
        """
        Возвращает отчет с указанными связанными данными в виде словаря.
        
        Args:
            report_id (int): ID отчета.
            user_id (int): ID пользователя (для проверки безопасности).
        
        Returns:
            dict: Данные отчета, включая параграфы, предложения и ключевые слова.
        """
        # Ищем отчет по ID и пользователю
        report = cls.query.filter_by(id=report_id, profile_id=profile_id).first()
        
        if not report:
            return None  # Если отчет не найден или принадлежит другому пользователю
        
        # Получаем параграфы и предложения
        paragraphs = Paragraph.query.filter_by(report_id=report_id).order_by(Paragraph.paragraph_index).all()

        # Преобразуем параграфы и предложения в словари
        paragraph_data = []
        for paragraph in paragraphs:
            sentences = Sentence.query.filter_by(paragraph_id=paragraph.id).order_by(Sentence.index, Sentence.weight).all()
            
            grouped_sentences = {}
            for sentence in sentences:
                index = sentence.index
                if index not in grouped_sentences:
                    grouped_sentences[index] = []
                grouped_sentences[index].append({
                    "id": sentence.id,
                    "index": sentence.index,
                    "weight": sentence.weight,
                    "comment": sentence.comment,
                    "sentence": sentence.sentence
                })
            
            paragraph_data.append({
                "id": paragraph.id,
                "paragraph_index": paragraph.paragraph_index,
                "paragraph": paragraph.paragraph,
                "paragraph_visible": paragraph.paragraph_visible,
                "title_paragraph": paragraph.title_paragraph,
                "bold_paragraph": paragraph.bold_paragraph,
                "paragraph_type": paragraph.paragraph_to_types.type_name,
                "paragraph_comment": paragraph.comment,
                "sentences": grouped_sentences
            })
        
        # Получаем ключевые слова, связанные с отчетом
        key_words = KeyWord.get_keywords_for_report(profile_id, report_id)

        keywords_data = []
        for key_word in key_words:
            keywords_data.append({
                "group_index": key_word.group_index,
                "index": key_word.index,
                "key_word": key_word.key_word,
                "key_word_comment": key_word.key_word_comment
            })

        # Формируем структуру данных для отчета
        report_data = {
            "report": {
                "id": report.id,
                "report_name": report.report_name,
                "report_type": report.report_to_subtype.subtype_to_type.type_text,
                "report_subtype": report.report_to_subtype.subtype_text,
                "comment": report.comment,
                "report_side": report.report_side,
                "user_id": report.user_id,
                "report_public": report.public
            },
            "paragraphs": paragraph_data,
            "keywords": keywords_data
        }

        return report_data


class Paragraph(BaseModel):
    __tablename__ = "report_paragraphs"
    report_id = db.Column(db.BigInteger, db.ForeignKey("reports.id"), nullable=False)
    type_paragraph_id = db.Column(db.Integer, db.ForeignKey('paragraph_types.id'), nullable=False)
    paragraph_index = db.Column(db.Integer, nullable=False)
    paragraph = db.Column(db.String(255), nullable=False)
    paragraph_visible = db.Column(db.Boolean, default=False, nullable=False)
    title_paragraph = db.Column(db.Boolean, default=False, nullable=False)
    bold_paragraph = db.Column(db.Boolean, default=False, nullable=False)
    comment = db.Column(db.String(255), nullable=True)
    paragraph_weight = db.Column(db.SmallInteger, nullable=False) 

    paragraph_to_sentences = db.relationship('Sentence', lazy=True, backref=db.backref("sentence_to_paragraph"), cascade="all, delete-orphan")
    paragraph_to_types = db.relationship('ParagraphType')
    
    
    @classmethod
    def create(cls, paragraph_index, report_id, paragraph, paragraph_visible, title_paragraph, bold_paragraph, type_paragraph_id, comment=None, paragraph_weight=1):
        new_paragraph = cls(
            paragraph_index=paragraph_index,
            report_id=report_id,
            paragraph=paragraph,
            paragraph_visible = paragraph_visible,
            title_paragraph=title_paragraph,
            bold_paragraph=bold_paragraph,
            type_paragraph_id=type_paragraph_id,
            comment=comment,
            paragraph_weight=paragraph_weight
        )
        db.session.add(new_paragraph)
        db.session.commit()
        return new_paragraph


class Sentence(BaseModel):
    __tablename__ = "sentences"
    paragraph_id = db.Column(db.BigInteger, db.ForeignKey("report_paragraphs.id"), nullable=False)
    index = db.Column(db.SmallInteger, nullable=False)
    weight = db.Column(db.SmallInteger, nullable=False)
    comment = db.Column(db.String(100), nullable=False)
    sentence = db.Column(db.String(400), nullable=False)



    @classmethod
    def create(cls, paragraph_id, index, weight, comment, sentence):
        new_sentence = cls(
            paragraph_id=paragraph_id,
            index=index,
            weight=weight,
            comment=comment,
            sentence=sentence
        )
        db.session.add(new_sentence)
        db.session.commit()
        return new_sentence
    
    @classmethod
    def find_by_paragraph_id(cls, paragraph_id):
        return cls.query.filter_by(paragraph_id=paragraph_id).all()





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


class ParagraphType(db.Model):
    __tablename__ = "paragraph_types"
    id = db.Column(db.Integer, primary_key=True)
    type_name = db.Column(db.String(50), nullable=False, unique=True)

    @classmethod
    def create(cls, type_name):
        """Creates a new paragraph type."""
        new_type = cls(type_name=type_name)
        db.session.add(new_type)
        db.session.commit()
        return new_type
    
    
    @classmethod
    def find_by_name(cls, name):
        """
        Возвращает ID типа параграфа по его имени.
        Args:
            name (str): Имя типа параграфа.
        Returns:
            int: ID типа параграфа или None, если не найден.
        """
        paragraph_type = cls.query.filter_by(type_name=name).first()
        return paragraph_type.id if paragraph_type else None


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

