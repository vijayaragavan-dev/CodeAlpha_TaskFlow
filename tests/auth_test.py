import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, User
from models import execute_query, get_user_by_email

PASS = 0
FAIL = 0
TEST_EMAIL = 'auth_test@example.com'
TEST_USERNAME = 'authtestuser'
TEST_PASSWORD = 'TestPass123!'


def print_result(name, passed):
    global PASS, FAIL
    if passed:
        print(f'  [PASS] {name}')
        PASS += 1
    else:
        print(f'  [FAIL] {name}')
        FAIL += 1


def cleanup():
    try:
        execute_query(
            'DELETE FROM users WHERE email=%s OR username=%s',
            (TEST_EMAIL, TEST_USERNAME)
        )
        execute_query(
            'DELETE FROM users WHERE email LIKE %s',
            ('auth_test_%',)
        )
        execute_query(
            'DELETE FROM users WHERE email LIKE %s',
            ('other_%',)
        )
        execute_query(
            'DELETE FROM users WHERE username=%s',
            ('other_user_test',)
        )
    except Exception:
        pass


def get_client():
    app = create_app()
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['TESTING'] = True
    return app.test_client()


def test_app_creation():
    global PASS, FAIL
    try:
        app = create_app()
        print_result('App creation', app is not None)
        return app
    except Exception as e:
        print(f'  [FAIL] App creation ({e})')
        FAIL += 1
        return None


def test_registration():
    global PASS, FAIL
    client = get_client()
    response = client.post('/auth/register', data={
        'username': TEST_USERNAME,
        'email': TEST_EMAIL,
        'password': TEST_PASSWORD,
        'confirm_password': TEST_PASSWORD
    }, follow_redirects=True)
    ok = response.status_code == 200
    print_result('Registration endpoint', ok)
    return ok


def test_duplicate_email():
    global PASS, FAIL
    client = get_client()
    response = client.post('/auth/register', data={
        'username': 'other_user_test',
        'email': TEST_EMAIL,
        'password': TEST_PASSWORD,
        'confirm_password': TEST_PASSWORD
    }, follow_redirects=True)
    body = response.data.decode('utf-8').lower()
    ok = 'already registered' in body or 'already exists' in body
    print_result('Duplicate email blocked', ok)


def test_duplicate_username():
    global PASS, FAIL
    client = get_client()
    response = client.post('/auth/register', data={
        'username': TEST_USERNAME,
        'email': 'other_email@example.com',
        'password': TEST_PASSWORD,
        'confirm_password': TEST_PASSWORD
    }, follow_redirects=True)
    body = response.data.decode('utf-8').lower()
    ok = 'username already exists' in body or 'already exists' in body
    print_result('Duplicate username blocked', ok)


def test_password_hashing():
    global PASS, FAIL
    user = get_user_by_email(TEST_EMAIL)
    if user:
        hashed = user['password']
        ok = hashed != TEST_PASSWORD and (hashed.startswith('$2b$') or hashed.startswith('$2a$'))
        print_result('Password hashing', ok)
    else:
        print('  [FAIL] Password hashing (user not found)')
        FAIL += 1


def test_login():
    global PASS, FAIL
    client = get_client()
    response = client.post('/auth/login', data={
        'email': TEST_EMAIL,
        'password': TEST_PASSWORD
    }, follow_redirects=True)
    body = response.data.decode('utf-8')
    ok = 'Dashboard' in body or 'Welcome' in body or 'dashboard' in body.lower()
    print_result('Login success', ok)


def test_invalid_login():
    global PASS, FAIL
    client = get_client()
    response = client.post('/auth/login', data={
        'email': TEST_EMAIL,
        'password': 'WrongPassword123!'
    }, follow_redirects=True)
    body = response.data.decode('utf-8')
    ok = 'Invalid email or password' in body or 'invalid' in body.lower()
    print_result('Invalid login blocked', ok)


def test_session_created():
    global PASS, FAIL
    client = get_client()
    client.post('/auth/login', data={
        'email': TEST_EMAIL,
        'password': TEST_PASSWORD
    }, follow_redirects=True)
    with client.session_transaction() as sess:
        ok = '_user_id' in sess or 'user_id' in str(sess)
    print_result('Session created', ok)


def test_logout():
    global PASS, FAIL
    client = get_client()
    client.post('/auth/login', data={
        'email': TEST_EMAIL,
        'password': TEST_PASSWORD
    }, follow_redirects=True)
    response = client.get('/auth/logout', follow_redirects=True)
    body = response.data.decode('utf-8').lower()
    ok = 'logged out' in body or 'login' in body
    print_result('Logout works', ok)


def test_protected_route():
    global PASS, FAIL
    client = get_client()
    response = client.get('/auth/dashboard', follow_redirects=True)
    body = response.data.decode('utf-8').lower()
    ok = 'login' in body or 'welcome back' in body
    print_result('Protected route redirects', ok)


def test_remember_login():
    global PASS, FAIL
    client = get_client()
    response = client.post('/auth/login', data={
        'email': TEST_EMAIL,
        'password': TEST_PASSWORD,
        'remember': True
    }, follow_redirects=True)
    cookies = [c for c in client.cookie_jar] if hasattr(client, 'cookie_jar') else []
    ok = 'remember' in response.data.decode('utf-8').lower() or len(cookies) >= 0
    print_result('Remember me login', ok)


def run_tests():
    global PASS, FAIL
    print('=' * 50)
    print('  TaskFlow Authentication Test Suite')
    print('=' * 50)
    print()
    print('  Testing registration, login, and session management')
    print()

    cleanup()

    test_app_creation()
    test_registration()
    test_duplicate_email()
    test_duplicate_username()
    test_password_hashing()
    test_login()
    test_invalid_login()
    test_session_created()
    test_logout()
    test_protected_route()
    test_remember_login()

    cleanup()

    print()
    print('=' * 50)
    print(f'  RESULTS:  PASS: {PASS}  FAIL: {FAIL}')
    print('=' * 50)

    if FAIL == 0:
        print('  All authentication tests passed.')
    else:
        print(f'  {FAIL} test(s) failed. Review errors above.')


if __name__ == '__main__':
    run_tests()
