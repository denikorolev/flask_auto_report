#forms.py

from flask_security.forms import RegisterForm
from wtforms import StringField
from wtforms.validators import DataRequired

class CustomRegisterForm(RegisterForm):
    user_name = StringField("User Name", validators=[DataRequired()])
