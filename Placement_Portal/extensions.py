from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager,login_user,logout_user,login_required,current_user

db = SQLAlchemy()
login_manager = LoginManager()