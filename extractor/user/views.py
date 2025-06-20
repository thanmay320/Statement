from extractor.user.forms import RegistrationForm,LoginForm
from extractor.models import User
from extractor import db
from flask import  render_template, redirect, url_for, flash,  Blueprint
from flask_login import login_user, logout_user, login_required,current_user

users = Blueprint('users', __name__)
@users.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if the email already exists
        existing_email = User.query.filter_by(user_email=form.user_email.data).first()
        if existing_email:
            flash('Email is already registered. Please use a different email.', 'danger')
            return render_template('register.html', form=form)

        # Create user (user_id auto-generated in model)
        new_user = User(
            user_name=form.user_name.data,
            user_email=form.user_email.data,
            password=form.password.data
        )

        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully!', 'success')
        return redirect(url_for('users.login'))  # Adjust if blueprint name is different

    return render_template('register.html', form=form, current_user=current_user)


@users.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(user_email=form.email.data).first()  # Corrected this line
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('core.index'))
        else:
            flash('Invalid email or password.', 'danger')
    return render_template('login.html', form=form,current_user=current_user)

@users.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('core.index'))
