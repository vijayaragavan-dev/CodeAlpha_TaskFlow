import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

ERRORS = []
PASS = 0
FAIL = 0


def check(description, condition, detail=''):
    global PASS, FAIL
    if condition:
        print(f'  [PASS] {description}')
        PASS += 1
    else:
        print(f'  [FAIL] {description} — {detail}')
        FAIL += 1
        ERRORS.append(description)


def main():
    global PASS, FAIL
    print('=' * 55)
    print('  TaskFlow Pre-Deployment Validation')
    print('=' * 55)
    print()

    import dotenv
    dotenv.load_dotenv()
    if not os.getenv('SECRET_KEY'):
        os.environ['SECRET_KEY'] = 'deploy-check-key-12345678901234567890'
    if not os.getenv('MYSQL_HOST'):
        os.environ['MYSQL_HOST'] = 'localhost'
    if not os.getenv('MYSQL_USER'):
        os.environ['MYSQL_USER'] = 'root'
    if not os.getenv('MYSQL_DB'):
        os.environ['MYSQL_DB'] = 'taskflow'
    if not os.getenv('FLASK_ENV'):
        os.environ['FLASK_ENV'] = 'development'

    import logging
    logging.disable(logging.CRITICAL)

    # 1. Compile checks
    print('  --- Syntax / Compile ---')
    modules = ['app', 'config', 'models', 'forms', 'wsgi']
    for m in modules:
        try:
            __import__(m)
            check(f'py_compile {m}.py', True)
        except Exception as e:
            check(f'py_compile {m}.py', False, str(e))

    # 2. Config validation
    print()
    print('  --- Configuration ---')
    from config import Config, config_by_name, PORT, FLASK_ENV
    check('SECRET_KEY set', bool(Config.SECRET_KEY))
    check('ALLOWED_ORIGINS default *', Config.ALLOWED_ORIGINS == '*')
    check('MYSQL_SSL_CA defaults empty', Config.MYSQL_SSL_CA == '')
    check('DB_POOL_RECYCLE defaults 3600', Config.DB_POOL_RECYCLE == 3600)
    check('RATELIMIT_ENABLED default True', Config.RATELIMIT_ENABLED)
    check('RATELIMIT_GLOBAL set', bool(Config.RATELIMIT_GLOBAL))
    check('RATELIMIT_LOGIN set', bool(Config.RATELIMIT_LOGIN))
    check('RATELIMIT_REGISTER set', bool(Config.RATELIMIT_REGISTER))
    check('Config dispatch works', config_by_name.__name__ == 'DevelopmentConfig')
    check('PORT defaults 5000', PORT == 5000)

    # 3. App creation
    print()
    print('  --- App Factory ---')
    from app import create_app, socketio, limiter, _cleanup, _handle_signal, register_shutdown_handlers
    app = create_app()
    check('App created', app is not None)
    check('SocketIO gevent mode', socketio.async_mode == 'gevent')
    check('Limiter initialized', limiter is not None)
    check('Cleanup function exists', callable(_cleanup))
    check('Signal handler exists', callable(_handle_signal))
    check('register_shutdown_handlers exists', callable(register_shutdown_handlers))
    check('Upload folder exists', os.path.exists(Config.UPLOAD_FOLDER))

    # 4. Database
    print()
    print('  --- Database ---')
    from models import get_db_pool, get_db_connection, close_connection, fetch_one
    pool = get_db_pool()
    check('Connection pool created', pool is not None)
    conn = get_db_connection()
    check('Connection acquired', conn is not None)
    check('Connection alive', conn.is_connected())
    row = fetch_one('SELECT 1 AS test')
    check('SELECT 1 query', row and row['test'] == 1)
    close_connection(conn)

    # Test reconnect
    conn2 = get_db_connection()
    check('Reconnect works', conn2.is_connected())
    close_connection(conn2)

    # 5. Routes
    print()
    print('  --- Routes ---')
    expected_routes = ['/health', '/metrics', '/', '/auth/login', '/auth/register',
                       '/auth/dashboard', '/projects/', '/tasks/search']
    rule_map = {r.rule: r for r in app.url_map.iter_rules()}
    for route in expected_routes:
        check(f'Route {route}', route in rule_map)

    # 6. Endpoints
    print()
    print('  --- HTTP Endpoints ---')
    with app.test_client() as c:
        r = c.get('/health')
        check('GET /health 200', r.status_code == 200)
        if r.status_code == 200:
            data = r.get_json()
            check('/health status healthy', data.get('status') == 'healthy')
            check('/health has version', 'version' in data)
            check('/health has database', 'database' in data)

        r = c.get('/metrics')
        check('GET /metrics 200', r.status_code == 200)

        r = c.get('/')
        check('GET / 200', r.status_code == 200)

        r = c.get('/auth/login')
        check('GET /auth/login 200', r.status_code == 200)

        r = c.get('/auth/register')
        check('GET /auth/register 200', r.status_code == 200)

        r = c.get('/nonexistent')
        check('GET /nonexistent 404', r.status_code == 404)

    # 7. Templates
    print()
    print('  --- Templates ---')
    required_templates = [
        'base.html', 'index.html', 'login.html', 'register.html',
        'dashboard.html', 'projects.html', 'create_project.html',
        'project_detail.html', 'edit_project.html', 'project_members.html',
        'kanban.html', 'create_task.html', 'edit_task.html', 'task_detail.html',
        'search_results.html', 'notifications.html',
        '403.html', '404.html', '500.html', 'error.html'
    ]
    template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
    for t in required_templates:
        check(f'Template {t}', os.path.exists(os.path.join(template_dir, t)))

    # 8. Static files
    print()
    print('  --- Static Assets ---')
    static_dir = os.path.join(os.path.dirname(__file__), '..', 'static')
    required_static = [
        'css/style.css', 'js/main.js', 'js/kanban.js', 'js/socket.js',
        'images/favicon.svg', 'images/favicon.ico', 'manifest.json',
        'service-worker.js'
    ]
    for s in required_static:
        check(f'Static {s}', os.path.exists(os.path.join(static_dir, s)))

    # 9. Deployment files
    print()
    print('  --- Deployment Files ---')
    project_root = os.path.join(os.path.dirname(__file__), '..')
    deploy_files = ['Procfile', 'runtime.txt', 'render.yaml', 'vercel.json',
                    '.env.example', 'requirements.txt', 'wsgi.py', 'database.sql']
    for f in deploy_files:
        check(f'Deploy file {f}', os.path.exists(os.path.join(project_root, f)))

    with open(os.path.join(project_root, 'requirements.txt')) as f:
        reqs = f.read()
    check('Flask-Limiter in requirements', 'Flask-Limiter' in reqs)

    # 10. Procfile content
    with open(os.path.join(project_root, 'Procfile')) as f:
        proc = f.read().strip()
    check('Procfile has gunicorn gevent', 'gunicorn' in proc and 'gevent' in proc)
    check('Procfile has wsgi:app', 'wsgi:app' in proc)

    # Summary
    print()
    print('=' * 55)
    print(f'  RESULTS:  PASS: {PASS}  FAIL: {FAIL}')
    print('=' * 55)
    if FAIL == 0:
        print('  All deployment checks passed.')
    else:
        print(f'  {FAIL} check(s) failed. Review errors above.')
        for e in ERRORS:
            print(f'    - {e}')

    return 0 if FAIL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
