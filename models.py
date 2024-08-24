# models.py

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.orm import joinedload

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.BigInteger, primary_key=True)
    user_role = db.Column(db.String, nullable=False)
    user_email = db.Column(db.String, unique=True, nullable=False)
    user_name = db.Column(db.String, nullable=False)
    user_pass = db.Column(db.String, nullable=False)
    user_bio = db.Column(db.Text, nullable=True)
    user_avatar = db.Column(db.LargeBinary, nullable=True)

    def set_password(self, password):
        self.user_pass = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.user_pass, password)


class AppConfig(db.Model):
    __tablename__ = 'app_config'
    id = db.Column(db.Integer, primary_key=True)
    config_key = db.Column(db.String(50), unique=True, nullable=False)
    config_value = db.Column(db.String(200), nullable=False)
    config_user = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('configs', lazy=True))

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

class Report(BaseModel):
    __tablename__ = "reports"
    userid = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    comment = db.Column(db.String(255), nullable=True)
    report_name = db.Column(db.String(255), nullable=False)
    report_type = db.Column(db.Integer, db.ForeignKey('report_type.id'), nullable=False)
    report_subtype = db.Column(db.Integer, db.ForeignKey('report_subtype.id'), nullable=False)
    public = db.Column(db.Boolean, default=False, nullable=False)
    report_side = db.Column(db.Boolean, nullable=True, default=None)
    
    user = db.relationship('User', backref=db.backref('reports', lazy=True))
    report_type_rel = db.relationship('ReportType', backref=db.backref('reports', lazy=True), overlaps="report_type")
    report_subtype_rel = db.relationship('ReportSubtype', backref=db.backref('reports', lazy=True), overlaps="report_subtype")
    report_paragraphs = db.relationship('ReportParagraph', backref='report', cascade="all, delete-orphan", overlaps="paragraphs,report")

    @classmethod
    def create(cls, userid, report_name, report_type, report_subtype, comment=None, public=False, report_side=None):
        new_report = cls(
            userid=userid,
            report_name=report_name,
            report_type=report_type,
            report_subtype=report_subtype,
            comment=comment,
            public=public,
            report_side=report_side
        )
        db.session.add(new_report)
        db.session.commit()
        return new_report


class ReportType(BaseModel):
    __tablename__ = 'report_type'
    type = db.Column(db.String(50), nullable=False)
    
    subtypes_rel = db.relationship('ReportSubtype', back_populates='report_type_rel', lazy=True)
    
    @classmethod
    def create(cls, type):
        new_type = cls(
            type=type
        )
        db.session.add(new_type)
        db.session.commit()
        return new_type

class ReportSubtype(BaseModel):
    __tablename__ = "report_subtype"
    type = db.Column(db.SmallInteger, db.ForeignKey("report_type.id"), nullable=False)
    subtype = db.Column(db.String(250), nullable=False)
    
    report_type_rel = db.relationship('ReportType', back_populates='subtypes_rel', lazy=True)
    
    @classmethod
    def create(cls, type, subtype):
        new_subtype = cls(
            type=type,
            subtype=subtype
        )
        db.session.add(new_subtype)
        db.session.commit()
        return new_subtype

class ReportParagraph(BaseModel):
    __tablename__ = "report_paragraphs"
    paragraph_index = db.Column(db.Integer, nullable=False)
    report_id = db.Column(db.BigInteger, db.ForeignKey("reports.id"), nullable=False)
    paragraph = db.Column(db.String(255), nullable=False)
    paragraph_visible = db.Column(db.Boolean, default=False, nullable=False)

    report_rel = db.relationship("Report", backref=db.backref("report_paragraphs_list", lazy=True), overlaps="paragraphs,report")
    sentences = db.relationship('Sentence', backref='paragraph', cascade="all, delete-orphan", overlaps="paragraph,sentences")

    @classmethod
    def create(cls, paragraph_index, report_id, paragraph, paragraph_visible=False):
        new_paragraph = cls(
            paragraph_index=paragraph_index,
            report_id=report_id,
            paragraph=paragraph,
            paragraph_visible = paragraph_visible
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

    report_paragraph_rel = db.relationship("ReportParagraph", backref=db.backref("sentences_list", lazy=True), overlaps="paragraph,sentences")

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

class KeyWordsGroup(BaseModel):
    __tablename__ = 'key_words_group'

    group_index = db.Column(db.Integer, nullable=False)
    index = db.Column(db.Integer, nullable=False)
    key_word = db.Column(db.String(50), nullable=False)
    key_word_comment = db.Column(db.String(100), nullable=True)
    public = db.Column(db.Boolean, default=False, nullable=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('key_words_groups', lazy=True))

    @classmethod
    def create(cls, group_index, index, key_word, user_id, key_word_comment=None, public=False):
        """Creates a new keyword group entry."""
        new_key_word_group = cls(
            group_index=group_index,
            index=index,
            key_word=key_word,
            key_word_comment=key_word_comment,
            public=public,
            user_id=user_id
        )
        db.session.add(new_key_word_group)
        db.session.commit()
        return new_key_word_group

    @classmethod
    def find_by_user_id(cls, user_id):
        """Finds all keyword groups for a specific user."""
        return cls.query.filter_by(user_id=user_id).order_by(cls.group_index, cls.index).all()

    @classmethod
    def find_public(cls):
        """Finds all public keyword groups."""
        return cls.query.filter_by(public=True).all()
