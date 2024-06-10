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

class Report(db.Model):
    __tablename__ = 'reports'
    id = db.Column(db.BigInteger, primary_key=True)
    userid = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    comment = db.Column(db.String(255), nullable=True)
    report_name = db.Column(db.String(255), nullable=False)
    report_type = db.Column(db.Integer, db.ForeignKey('report_type.id'), nullable=False)
    report_subtype = db.Column(db.Integer, db.ForeignKey('report_subtype.id'), nullable=False)
    public = db.Column(db.Boolean, default=False, nullable=False)
    
    user = db.relationship('User', backref=db.backref('reports', lazy=True))
    report_type_rel = db.relationship('ReportType', backref=db.backref('reports', lazy=True))
    report_subtype_rel = db.relationship('ReportSubtype', backref=db.backref('reports', lazy=True))

    @classmethod
    def create(cls, userid, report_name, report_type, report_subtype, comment=None, public=False):
        new_report = cls(
            userid=userid,
            report_name=report_name,
            report_type=report_type,
            report_subtype=report_subtype,
            comment=comment,
            public=public
        )
        db.session.add(new_report)
        db.session.commit()
        return new_report

    @classmethod
    def delete(cls, report_id):
        report_to_delete = cls.query.get(report_id)
        if report_to_delete:
            db.session.delete(report_to_delete)
            db.session.commit()
            return True
        return False

    def save(self):
        db.session.commit()
        
    @classmethod
    def get_reports_with_relations(cls, user_id):
        return cls.query.filter_by(userid=user_id).options(
            joinedload(cls.report_type_rel),
            joinedload(cls.report_subtype_rel)
        ).all()

class ReportType(db.Model):
    __tablename__ = 'report_type'
    id = db.Column(db.SmallInteger, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    
    subtypes_rel = db.relationship('ReportSubtype', backref='report_type', lazy=True)

class ReportSubtype(db.Model):
    __tablename__ = 'report_subtype'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.SmallInteger, db.ForeignKey('report_type.id'), nullable=False)
    subtype = db.Column(db.String(250), nullable=False)

class ReportParagraph(db.Model):
    __tablename__ = "report_paragraphs"
    
    id = db.Column(db.BigInteger, primary_key=True)
    paragraph_index = db.Column(db.Integer, nullable=False)
    report = db.Column(db.BigInteger, db.ForeignKey("reports.id"), nullable=False)
    paragraph = db.Column(db.String(255), nullable=False)

    report_rel = db.relationship("Report", backref=db.backref("report_paragraphs_list", lazy=True))

    @classmethod
    def create(cls, paragraph_index, report, paragraph):
        new_paragraph = cls(
            paragraph_index=paragraph_index,
            report=report,
            paragraph=paragraph
        )
        db.session.add(new_paragraph)
        db.session.commit()
        return new_paragraph

    @classmethod
    def delete(cls, paragraph_id):
        paragraph_to_delete = cls.query.get(paragraph_id)
        if paragraph_to_delete:
            db.session.delete(paragraph_to_delete)
            db.session.commit()
            return True
        return False

    def save(self):
        db.session.commit()

class Sentence(db.Model):
    __tablename__ = "sentences"
    
    id = db.Column(db.BigInteger, primary_key=True)
    paragraph = db.Column(db.BigInteger, db.ForeignKey("report_paragraphs.id"), nullable=False)
    index = db.Column(db.SmallInteger, nullable=False)
    weight = db.Column(db.SmallInteger, nullable=False)
    comment = db.Column(db.String(100), nullable=False)
    sentence = db.Column(db.String(400), nullable=False)

    report_paragraph_rel = db.relationship("ReportParagraph", backref=db.backref("sentences", lazy=True))

    @classmethod
    def create(cls, paragraph, index, weight, comment, sentence):
        new_sentence = cls(
            paragraph=paragraph,
            index=index,
            weight=weight,
            comment=comment,
            sentence=sentence
        )
        db.session.add(new_sentence)
        db.session.commit()
        return new_sentence

    @classmethod
    def delete(cls, sentence_id):
        sentence_to_delete = cls.query.get(sentence_id)
        if sentence_to_delete:
            db.session.delete(sentence_to_delete)
            db.session.commit()
            return True
        return False

    def save(self):
        db.session.commit()
