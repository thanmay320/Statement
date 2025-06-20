from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length

class RegistrationForm(FlaskForm):
    user_name = StringField('Name', validators=[DataRequired(), Length(min=2, max=64)])
    user_email = StringField('Email', validators=[DataRequired(), Email(), Length(max=64)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email=StringField('Email:',validators=[DataRequired(),Email()])
    password=PasswordField('Password',validators=[DataRequired()])
    submit=SubmitField('Login')
