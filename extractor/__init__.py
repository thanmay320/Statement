from flask import Flask
from flask_sqlalchemy import SQLAlchemy

import os
from  flask_login import LoginManager

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Directories
UPLOAD_FOLDER = 'uploads'
EXCEL_FOLDER = 'excel_files'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXCEL_FOLDER, exist_ok=True)

# SQLite DB config
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Thanmay047%40@localhost/statement'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'users.login'

from extractor.core.views import core
from extractor.user.views import users
app.register_blueprint(core)
app.register_blueprint(users)