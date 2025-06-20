# app/extensions.py

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_security import Security

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
security = Security()
