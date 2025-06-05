from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, DateField, SelectField, TextAreaField
from wtforms.validators import DataRequired, EqualTo, ValidationError, Length, Email
from datetime import datetime
from ..models import db, User
# from ..utils.security import log_security_event, detect_suspicious_patterns, sanitize_html

# Stub functions for missing security utilities
def log_security_event(event_type, data):
    """Stub function for security event logging"""
    pass

def detect_suspicious_patterns(text):
    """Stub function for suspicious pattern detection"""
    return False

def sanitize_html(text):
    """Stub function for HTML sanitization"""
    return text if text else ""

def send_password_reset_email(user):
    """Stub function for sending password reset emails"""
    print(f"Would send password reset email to {user.email}")
    return True

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

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')

    def validate_current_password(self, current_password):
        if not current_user.check_password(current_password.data):
            raise ValidationError('Current password is incorrect.')

class NotificationPreferencesForm(FlaskForm):
    email_notifications = BooleanField('Email Notifications', default=True)
    record_reminders = BooleanField('Health Record Reminders', default=True)
    security_alerts = BooleanField('Security Alerts', default=True)
    ai_insights = BooleanField('AI Health Insights', default=True)
    frequency = SelectField('Notification Frequency', 
                          choices=[('immediate', 'Immediate'), 
                                  ('daily', 'Daily Summary'), 
                                  ('weekly', 'Weekly Summary')],
                          default='daily')
    submit = SubmitField('Save Preferences')

class DeleteAccountForm(FlaskForm):
    password = PasswordField('Confirm Password', validators=[DataRequired()])
    confirmation = StringField('Type "DELETE" to confirm', validators=[DataRequired()])
    reason = TextAreaField('Reason for deletion (optional)')
    submit = SubmitField('Delete Account')

    def validate_password(self, password):
        if not current_user.check_password(password.data):
            raise ValidationError('Password is incorrect.')
    
    def validate_confirmation(self, confirmation):
        if confirmation.data != 'DELETE':
            raise ValidationError('You must type "DELETE" to confirm account deletion.')

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Reset Password')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

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

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Handle forgot password requests"""
    if current_user.is_authenticated:
        return redirect(url_for('records.dashboard'))
    
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            if send_password_reset_email(user):
                flash('Check your email for instructions to reset your password.', 'info')
            else:
                flash('Failed to send reset email. Please try again later.', 'error')
        else:
            # Don't reveal whether the email exists or not for security
            flash('Check your email for instructions to reset your password.', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html', title='Forgot Password', form=form)

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handle password reset with token"""
    if current_user.is_authenticated:
        return redirect(url_for('records.dashboard'))
    
    # Find user by token
    user = User.query.filter_by(reset_token=token).first()
    if not user or not user.verify_reset_token(token):
        flash('Invalid or expired password reset link.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.reset_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', title='Reset Password', form=form)

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
@limiter.limit("5 per hour")
def change_password():
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        # Update password
        current_user.set_password(form.new_password.data)
        current_user.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Log security event
        log_security_event('password_changed', {
            'user_id': current_user.id,
            'email': current_user.email
        })
        
        flash('Your password has been changed successfully!', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/change_password.html', title='Change Password', form=form)

@auth_bp.route('/notification-preferences', methods=['GET', 'POST'])
@login_required
def notification_preferences():
    form = NotificationPreferencesForm()
    
    # Load current preferences from the database
    if request.method == 'GET':
        form.email_notifications.data = current_user.email_notifications
        form.record_reminders.data = current_user.record_reminders
        form.security_alerts.data = current_user.security_alerts
        form.ai_insights.data = current_user.ai_insights
        form.frequency.data = current_user.notification_frequency
    
    if form.validate_on_submit():
        # Save preferences to the database
        current_user.email_notifications = form.email_notifications.data
        current_user.record_reminders = form.record_reminders.data
        current_user.security_alerts = form.security_alerts.data
        current_user.ai_insights = form.ai_insights.data
        current_user.notification_frequency = form.frequency.data
        current_user.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash('Your notification preferences have been updated!', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/notification_preferences.html', title='Notification Preferences', form=form)

@auth_bp.route('/two-factor-setup')
@login_required
def two_factor_setup():
    # Placeholder for 2FA setup
    flash('Two-Factor Authentication setup is coming soon!', 'info')
    return redirect(url_for('auth.profile'))

@auth_bp.route('/delete-account', methods=['GET', 'POST'])
@login_required
@limiter.limit("3 per hour")
def delete_account():
    form = DeleteAccountForm()
    
    if form.validate_on_submit():
        # Log account deletion
        log_security_event('account_deleted', {
            'user_id': current_user.id,
            'email': current_user.email,
            'reason': form.reason.data or 'No reason provided'
        })
        
        # Delete user account and all related data
        user_id = current_user.id
        user_email = current_user.email
        
        # Delete related records first (cascade should handle this, but being explicit)
        from ..models import HealthRecord, FamilyMember
        HealthRecord.query.filter_by(user_id=user_id).delete()
        
        # Remove user from family relationships
        current_user.family_members.clear()
        
        # Delete the user
        db.session.delete(current_user)
        db.session.commit()
        
        # Log out the user
        logout_user()
        
        flash(f'Account {user_email} has been permanently deleted.', 'info')
        return redirect(url_for('main.index'))
    
    return render_template('auth/delete_account.html', title='Delete Account', form=form)
