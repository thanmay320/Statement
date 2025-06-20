from extractor import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

class User(db.Model, UserMixin):
    __tablename__ = 'user'

    user_id = db.Column(db.String(64), primary_key=True)
    user_name = db.Column(db.String(64), index=True)
    user_email = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.Text)

    def __init__(self, user_email, user_name, password, user_id=None):
        self.user_id = user_id or str(uuid.uuid4())  # Auto-generate UUID if not provided
        self.user_email = user_email
        self.user_name = user_name
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return self.user_id  # Required by Flask-Login

    def __repr__(self):
        return f'<User {self.user_name}>'
