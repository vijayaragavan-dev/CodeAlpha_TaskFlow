import os
import time
import signal
import sys
import atexit
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

from gevent import monkey
monkey.patch_all()

from flask import Flask, render_template, jsonify, request, send_from_directory, make_response
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, current_user
from flask_wtf.csrf import CSRFProtect
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_compress import Compress

from config import Config, config_by_name
from models import get_user_by_id

_VERSION = '1.0.0'
_TAGLINE = 'Manage projects efficiently with TaskFlow.'
_version_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'VERSION')
if os.path.exists(_version_path):
    try:
        with open(_version_path, 'r') as f:
            _VERSION = f.read().strip()
    except Exception:
        pass

_request_count = 0
_error_count = 0
_request_times = []

bcrypt = Bcrypt()
login_manager = LoginManager()
csrf = CSRFProtect()
compress = Compress()
socketio = SocketIO(cors_allowed_origins=Config.ALLOWED_ORIGINS.split(',') if Config.ALLOWED_ORIGINS != '*' else '*', async_mode='gevent')

limiter = Limiter(
    get_remote_address,
    default_limits=[Config.RATELIMIT_GLOBAL],
    enabled=Config.RATELIMIT_ENABLED,
)

_cache = {}
_cache_timestamp = {}


def cache_get(key, max_age=30):
    if key in _cache and key in _cache_timestamp:
        age = (datetime.now() - _cache_timestamp[key]).total_seconds()
        if age < max_age:
            return _cache[key]
    return None


def cache_set(key, value):
    _cache[key] = value
    _cache_timestamp[key] = datetime.now()


class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['id']
        self.username = user_data['username']
        self.email = user_data['email']
        self.password = user_data['password']

    def get_id(self):
        return str(self.id)


@login_manager.user_loader
def load_user(user_id):
    user_data = get_user_by_id(int(user_id))
    if user_data:
        return User(user_data)
    return None


def create_app(config_class=None):
    if config_class is None:
        config_class = config_by_name
    app = Flask(
        __name__,
        static_folder='static',
        template_folder='templates'
    )
    app.config.from_object(config_class)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    bcrypt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    socketio.init_app(app)
    compress.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    setup_logging(app)

    limiter.init_app(app)

    _setup_metrics_middleware(app)
    _setup_static_cache_headers(app)

    register_error_handlers(app)

    register_blueprints(app)

    register_shutdown_handlers(app)

    _register_monitoring_routes(app)

    from routes import socket_events

    register_template_helpers(app)

    _ensure_indexes_at_startup(app)

    app.logger.info('TaskFlow application created successfully (v%s)', _VERSION)
    return app


def _setup_static_cache_headers(app):
    @app.after_request
    def add_cache_headers(response):
        if response.content_type and response.content_type.startswith(('text/css', 'text/javascript', 'application/javascript', 'image/')):
            response.headers.setdefault('Cache-Control', 'public, max-age=31536000, immutable')
        elif response.content_type and response.content_type.startswith('text/html'):
            response.headers.setdefault('Cache-Control', 'no-cache, private, must-revalidate')
        return response


def _ensure_indexes_at_startup(app):
    try:
        from models import ensure_optimal_indexes
        ensure_optimal_indexes()
        app.logger.info('Database indexes verified')
    except Exception as e:
        app.logger.warning('Could not verify indexes: %s', e)


def _setup_metrics_middleware(app):
    @app.before_request
    def before_request():
        global _request_count
        _request_count += 1
        request.start_time = time.time()

    @app.after_request
    def after_request(response):
        global _request_times
        if hasattr(request, 'start_time'):
            elapsed = time.time() - request.start_time
            _request_times.append(elapsed)
            if len(_request_times) > 1000:
                _request_times = _request_times[-500:]
        if response.status_code >= 500:
            global _error_count
            _error_count += 1
        return response


def _register_monitoring_routes(app):
    @app.route('/health')
    def health():
        db_status = 'connected'
        db_error = None
        try:
            from models import fetch_one
            fetch_one('SELECT 1')
        except Exception as e:
            db_status = 'disconnected'
            db_error = str(e)

        result = {
            'status': 'healthy' if db_status == 'connected' else 'degraded',
            'database': db_status,
            'version': _VERSION,
            'tagline': _TAGLINE,
            'timestamp': datetime.now().isoformat(),
        }
        if db_error:
            result['db_error'] = db_error
            return jsonify(result), 503
        return jsonify(result)

    @app.route('/metrics')
    def metrics():
        avg_time = 0.0
        if _request_times:
            avg_time = sum(_request_times) / len(_request_times)

        from models import get_db_pool
        pool_ok = True
        try:
            pool = get_db_pool()
        except Exception:
            pool_ok = False

        try:
            from routes.socket_events import active_users
            active_user_count = len(active_users)
        except Exception:
            active_user_count = 0

        return jsonify({
            'version': _VERSION,
            'uptime': time.time() - _start_time if '_start_time' in dir() else 0,
            'request_count': _request_count,
            'error_count': _error_count,
            'avg_response_time_ms': round(avg_time * 1000, 2),
            'active_users': active_user_count,
            'database_pool_ok': pool_ok,
            'timestamp': datetime.now().isoformat(),
        })


_start_time = time.time()


def setup_logging(app):
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, 'app.log')
    handler = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5
    )
    handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s [%(name)s] %(message)s'
    )
    handler.setFormatter(formatter)

    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    app.logger.addHandler(console_handler)

    app.logger.info('Logging configured')


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.error('404 error: %s', error)
        return render_template('404.html'), 404

    @app.errorhandler(403)
    def forbidden_error(error):
        app.logger.warning('403 error: %s', error)
        return render_template('403.html'), 403

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error('500 error: %s', error)
        return render_template('500.html'), 500

    @app.errorhandler(413)
    def request_entity_too_large(error):
        app.logger.warning('413 error: File too large')
        return render_template('error.html', error_code=413,
                               message='File too large. Maximum size is 5 MB.'), 413

    @app.errorhandler(Exception)
    def unhandled_exception(error):
        app.logger.critical('Unhandled exception: %s', error, exc_info=True)
        return render_template('500.html'), 500


def register_blueprints(app):
    from routes.auth import auth_bp
    from routes.projects import projects_bp
    from routes.tasks import tasks_bp
    from routes.notifications import notifications_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(notifications_bp)

    @app.route('/')
    def index():
        return render_template('index.html')


def relative_time(dt):
    if not dt:
        return ''
    now = datetime.now()
    if isinstance(dt, str):
        try:
            dt = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return ''
    diff = now - dt
    seconds = int(diff.total_seconds())
    if seconds < 60:
        return 'Just now'
    minutes = seconds // 60
    if minutes < 60:
        return f'{minutes} minute{"s" if minutes != 1 else ""} ago'
    hours = minutes // 60
    if hours < 24:
        return f'{hours} hour{"s" if hours != 1 else ""} ago'
    days = hours // 24
    if days == 1:
        return 'Yesterday'
    if days < 30:
        return f'{days} days ago'
    months = days // 30
    if months < 12:
        return f'{months} month{"s" if months != 1 else ""} ago'
    years = months // 12
    return f'{years} year{"s" if years != 1 else ""} ago'


def register_template_helpers(app):
    @app.context_processor
    def inject_now():
        return {'now': datetime.now, 'relative_time': relative_time, 'app_version': _VERSION, 'app_tagline': _TAGLINE}

    @app.context_processor
    def inject_notification_count():
        from models import count_unread_notifications, get_user_notifications as _raw_get_user_notifications
        unread = 0
        try:
            if current_user.is_authenticated:
                cache_key = f'unread_count_{current_user.id}'
                cached = cache_get(cache_key, max_age=5)
                if cached is not None:
                    unread = cached
                else:
                    unread = count_unread_notifications(current_user.id)
                    cache_set(cache_key, unread)
        except Exception:
            pass

        def _cached_get_user_notifications(user_id, limit=50):
            cache_key = f'notifications_{user_id}_{limit}'
            cached = cache_get(cache_key, max_age=5)
            if cached is not None:
                return cached
            result = _raw_get_user_notifications(user_id, limit)
            cache_set(cache_key, result)
            return result

        return {'unread_notifications': unread, 'get_user_notifications': _cached_get_user_notifications}


_shutdown_app = None
_shutdown_in_progress = False


def _cleanup():
    global _shutdown_in_progress
    if _shutdown_in_progress:
        return
    _shutdown_in_progress = True
    logger = logging.getLogger(__name__)
    logger.info('Shutdown signal received, cleaning up...')
    try:
        from models import _reset_pool
        _reset_pool()
        logger.info('Database connection pool closed')
    except Exception as e:
        logger.warning('Error closing database pool: %s', e)
    try:
        socketio.stop()
        logger.info('SocketIO stopped')
    except Exception as e:
        logger.warning('Error stopping SocketIO: %s', e)
    logger.info('Shutdown complete')


def _handle_signal(signum, frame):
    _cleanup()
    sys.exit(0)


def register_shutdown_handlers(app):
    global _shutdown_app
    _shutdown_app = app
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)
    app.logger.info('Shutdown handlers registered (SIGTERM, SIGINT)')


if __name__ == '__main__':
    from config import PORT, FLASK_ENV
    debug = FLASK_ENV == 'development'
    app = create_app()
    register_shutdown_handlers(app)
    atexit.register(_cleanup)
    print(f'  TaskFlow v{_VERSION} starting on 0.0.0.0:{PORT} (FLASK_ENV={FLASK_ENV})')
    socketio.run(app, host='0.0.0.0', port=PORT, debug=debug)
