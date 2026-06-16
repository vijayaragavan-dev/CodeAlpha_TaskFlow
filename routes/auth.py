import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from config import Config
from app import bcrypt, User, limiter
from forms import RegistrationForm, LoginForm
from models import create_user, get_user_by_email, get_user_by_id, get_dashboard_stats, get_user_projects

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

_auth_logger = None


def get_auth_logger():
    global _auth_logger
    if _auth_logger is None:
        _auth_logger = logging.getLogger('auth')
        log_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs'
        )
        os.makedirs(log_dir, exist_ok=True)
        handler = RotatingFileHandler(
            os.path.join(log_dir, 'auth.log'), maxBytes=1024 * 1024, backupCount=3
        )
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s [%(name)s] %(message)s'
        )
        handler.setFormatter(formatter)
        _auth_logger.addHandler(handler)
        _auth_logger.setLevel(logging.INFO)
    return _auth_logger


@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit(Config.RATELIMIT_REGISTER)
def register():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip()
        password = form.password.data
        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        try:
            user_id = create_user(username, email, hashed)
            get_auth_logger().info(
                'User registered: id=%d username=%s email=%s', user_id, username, email
            )
            flash('Account created! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            get_auth_logger().error('Registration failed: %s', e)
            flash('Registration error. Please try again.', 'danger')
    return render_template('register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit(Config.RATELIMIT_LOGIN)
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip()
        password = form.password.data
        user_data = get_user_by_email(email)
        if user_data and bcrypt.check_password_hash(user_data['password'], password):
            user = User(user_data)
            login_user(user, remember=form.remember.data)
            get_auth_logger().info(
                'Login successful: id=%d email=%s', user.id, email
            )
            next_page = request.args.get('next')
            return redirect(next_page or url_for('auth.dashboard'))
        get_auth_logger().warning('Login failed: email=%s', email)
        flash('Invalid email or password.', 'danger')
    return render_template('login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    get_auth_logger().info('Logout: id=%d email=%s', current_user.id, current_user.email)
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/dashboard')
@login_required
def dashboard():
    from app import cache_get, cache_set
    cache_key = f'dashboard_stats_{current_user.id}'
    stats = cache_get(cache_key)
    if stats is None:
        stats = get_dashboard_stats(current_user.id)
        cache_set(cache_key, stats)
    projects = get_user_projects(current_user.id)
    return render_template('dashboard.html', stats=stats, projects=projects)
