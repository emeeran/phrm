from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, DateField
from wtforms.validators import DataRequired, EqualTo, ValidationError, Length, Email
from datetime import datetime
from ..models import db, User
from ..utils.security import log_security_event, detect_suspicious_patterns, sanitize_html

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Get limiter instance
from .. import limiter

# Forms
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')
    
    def validate_email(self, email):
        if detect_suspicious_patterns(email.data):
            raise ValidationError('Invalid email format.')
    
    def validate_password(self, password):
        if detect_suspicious_patterns(password.data):
            raise ValidationError('Invalid password format.')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    date_of_birth = DateField('Date of Birth', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_username(self, username):
        if detect_suspicious_patterns(username.data):
            raise ValidationError('Username contains invalid characters.')
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        if detect_suspicious_patterns(email.data):
            raise ValidationError('Invalid email format.')
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')
    
    def validate_first_name(self, first_name):
        if detect_suspicious_patterns(first_name.data):
            raise ValidationError('First name contains invalid characters.')
    
    def validate_last_name(self, last_name):
        if detect_suspicious_patterns(last_name.data):
            raise ValidationError('Last name contains invalid characters.')

class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    date_of_birth = DateField('Date of Birth', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Update Profile')

    def __init__(self, original_username, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')

# Routes
@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('records.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            log_security_event('failed_login_attempt', {
                'email': form.email.data,
                'user_agent': request.headers.get('User-Agent')
            })
            flash('Invalid email or password', 'danger')
            return redirect(url_for('auth.login'))

        login_user(user, remember=form.remember_me.data)
        log_security_event('successful_login', {'user_id': user.id})
        
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('records.dashboard')

        flash('Logged in successfully!', 'success')
        return redirect(next_page)

    return render_template('auth/login.html', title='Sign In', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    log_security_event('user_logout', {'user_id': current_user.id})
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def register():
    if current_user.is_authenticated:
        return redirect(url_for('records.dashboard'))

    form = RegistrationForm()
    if form.validate_on_submit():
        # Sanitize user inputs
        user = User(
            username=sanitize_html(form.username.data),
            email=form.email.data.lower().strip(),
            first_name=sanitize_html(form.first_name.data),
            last_name=sanitize_html(form.last_name.data),
            date_of_birth=form.date_of_birth.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        log_security_event('user_registration', {
            'user_id': user.id,
            'email': user.email
        })

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', title='Register', form=form)

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(original_username=current_user.username)

    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.date_of_birth = form.date_of_birth.data
        current_user.updated_at = datetime.utcnow()
        db.session.commit()

        flash('Your profile has been updated!', 'success')
        return redirect(url_for('auth.profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.date_of_birth.data = current_user.date_of_birth

    return render_template('auth/profile.html', title='Profile', form=form)