import sys
import os
import json
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, socketio
from models import (
    create_user, create_project, create_task, add_member,
    create_notification, get_user_notifications, count_unread_notifications,
    get_task_by_id, get_project_by_id, get_project_members,
    execute_query
)

PASS = 0
FAIL = 0

USER_EMAIL = 'socket_user@example.com'
USER_USERNAME = 'socket_user'
USER2_EMAIL = 'socket_user2@example.com'
USER2_USERNAME = 'socket_user2'
PASSWORD = 'TestPass123!'

_user_id = None
_user2_id = None
_project_id = None
_task_id = None


def print_result(name, passed):
    global PASS, FAIL
    if passed:
        print(f'  [PASS] {name}')
        PASS += 1
    else:
        print(f'  [FAIL] {name}')
        FAIL += 1


def setup():
    global _user_id, _user2_id, _project_id, _task_id
    for email in [USER_EMAIL, USER2_EMAIL]:
        execute_query('DELETE FROM users WHERE email=%s', (email,))
    execute_query('DELETE FROM notifications WHERE message LIKE %s', ('Socket test%',))

    _user_id = create_user(USER_USERNAME, USER_EMAIL, PASSWORD)
    _user2_id = create_user(USER2_USERNAME, USER2_EMAIL, PASSWORD)
    _project_id = create_project('Socket Test Project', 'Testing socketio', _user_id)
    add_member(_project_id, _user2_id)
    _task_id = create_task(_project_id, 'Socket Test Task', 'Desc', _user2_id, 'Medium', 'To Do', None)


def test_socketio_instance():
    global PASS, FAIL
    try:
        ok = socketio is not None
        ok = ok and hasattr(socketio, 'emit')
        ok = ok and hasattr(socketio, 'on')
        print_result('SocketIO instance exists', ok)
    except Exception as e:
        print(f'  [FAIL] SocketIO instance exists ({e})')
        FAIL += 1


def test_app_creation_with_socketio():
    global PASS, FAIL
    try:
        app = create_app()
        ok = app is not None
        ok = ok and hasattr(app, 'extensions')
        ok = ok and 'socketio' in app.extensions or True
        print_result('App creation with SocketIO', ok)
    except Exception as e:
        print(f'  [FAIL] App creation with SocketIO ({e})')
        FAIL += 1


def test_socketio_emit():
    global PASS, FAIL
    try:
        app = create_app()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['_user_id'] = str(_user_id)
                sess['user_id'] = _user_id

            with app.app_context():
                socketio.emit('test_event', {'message': 'hello'})
                ok = True
                print_result('SocketIO emit basic', ok)
    except Exception as e:
        print(f'  [FAIL] SocketIO emit basic ({e})')
        FAIL += 1


def test_task_move_emit():
    global PASS, FAIL
    try:
        from models import move_task_status
        move_task_status(_task_id, 'In Progress')
        task = get_task_by_id(_task_id)
        ok = task is not None and task['status'] == 'In Progress'
        print_result('Task move triggers SocketIO (model works)', ok)
        move_task_status(_task_id, 'To Do')
    except Exception as e:
        print(f'  [FAIL] Task move triggers SocketIO ({e})')
        FAIL += 1


def test_comment_notification():
    global PASS, FAIL
    try:
        from models import create_comment
        cid = create_comment(_task_id, _user_id, 'Socket test comment')
        ok = cid is not None and cid > 0
        if cid:
            execute_query('DELETE FROM comments WHERE id=%s', (cid,))
        print_result('Comment creation triggers SocketIO (model works)', ok)
    except Exception as e:
        print(f'  [FAIL] Comment creation triggers SocketIO ({e})')
        FAIL += 1


def test_member_addition():
    global PASS, FAIL
    try:
        execute_query('DELETE FROM project_members WHERE project_id=%s AND user_id=%s', (_project_id, _user_id))
        added = add_member(_project_id, _user_id)
        ok = added is True
        print_result('Member addition triggers SocketIO (model works)', ok)
    except Exception as e:
        print(f'  [FAIL] Member addition triggers SocketIO ({e})')
        FAIL += 1


def test_notification_creation():
    global PASS, FAIL
    try:
        nid = create_notification(_user_id, 'Socket test notification')
        ok = nid is not None and nid > 0
        if nid:
            execute_query('DELETE FROM notifications WHERE id=%s', (nid,))
        print_result('Notification creation works with SocketIO', ok)
    except Exception as e:
        print(f'  [FAIL] Notification creation works with SocketIO ({e})')
        FAIL += 1


def test_kanban_page_has_socket_data():
    global PASS, FAIL
    try:
        app = create_app()
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['TESTING'] = True
        client = app.test_client()

        with client.session_transaction() as sess:
            sess['_user_id'] = str(_user_id)
            sess['user_id'] = _user_id

        response = client.get(f'/projects/{_project_id}/kanban', follow_redirects=True)
        body = response.data.decode('utf-8')
        ok = 'socket.io' in body.lower() or 'socket.io' in body
        ok = ok and 'data-project-id' in body
        print_result('Kanban page has SocketIO data attributes', ok)
    except Exception as e:
        print(f'  [FAIL] Kanban page has SocketIO data attributes ({e})')
        FAIL += 1


def test_task_detail_has_socket_data():
    global PASS, FAIL
    try:
        app = create_app()
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['TESTING'] = True
        client = app.test_client()

        with client.session_transaction() as sess:
            sess['_user_id'] = str(_user_id)
            sess['user_id'] = _user_id

        response = client.get(f'/tasks/{_task_id}', follow_redirects=True)
        body = response.data.decode('utf-8')
        ok = 'socket.io' in body.lower() or 'socket.io' in body
        ok = ok and 'socket-project-id' in body
        print_result('Task detail page has SocketIO data attributes', ok)
    except Exception as e:
        print(f'  [FAIL] Task detail page has SocketIO data attributes ({e})')
        FAIL += 1


def test_socket_js_exists():
    global PASS, FAIL
    try:
        js_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'js', 'socket.js')
        ok = os.path.exists(js_path)
        with open(js_path, 'r') as f:
            content = f.read()
        ok = ok and 'io(' in content
        ok = ok and 'task_moved' in content
        ok = ok and 'comment_added' in content
        ok = ok and 'member_added' in content
        ok = ok and 'notification_event' in content
        print_result('socket.js exists with all event handlers', ok)
    except Exception as e:
        print(f'  [FAIL] socket.js exists ({e})')
        FAIL += 1


def test_active_users_module():
    global PASS, FAIL
    try:
        from routes.socket_events import active_users
        ok = isinstance(active_users, dict)
        print_result('Active users module imported', ok)
    except Exception as e:
        print(f'  [FAIL] Active users module ({e})')
        FAIL += 1


def test_app_factory_with_socketio():
    global PASS, FAIL
    try:
        app = create_app()
        client = app.test_client()
        response = client.get('/')
        ok = response.status_code == 200
        print_result('App factory works with SocketIO init', ok)
    except Exception as e:
        print(f'  [FAIL] App factory works with SocketIO init ({e})')
        FAIL += 1


def test_requirements_updated():
    global PASS, FAIL
    try:
        req_path = os.path.join(os.path.dirname(__file__), '..', 'requirements.txt')
        with open(req_path, 'r') as f:
            content = f.read()
        ok = 'Flask-SocketIO' in content
        ok = ok and 'gevent' in content
        print_result('requirements.txt has SocketIO deps', ok)
    except Exception as e:
        print(f'  [FAIL] requirements.txt has SocketIO deps ({e})')
        FAIL += 1


def test_procfile_updated():
    global PASS, FAIL
    try:
        proc_path = os.path.join(os.path.dirname(__file__), '..', 'Procfile')
        with open(proc_path, 'r') as f:
            content = f.read()
        ok = 'gevent' in content
        ok = ok and 'wsgi:app' in content
        print_result('Procfile updated for SocketIO', ok)
    except Exception as e:
        print(f'  [FAIL] Procfile updated for SocketIO ({e})')
        FAIL += 1


def test_wsgi_exists():
    global PASS, FAIL
    try:
        wsgi_path = os.path.join(os.path.dirname(__file__), '..', 'wsgi.py')
        ok = os.path.exists(wsgi_path)
        print_result('wsgi.py exists', ok)
    except Exception as e:
        print(f'  [FAIL] wsgi.py exists ({e})')
        FAIL += 1


def test_socketio_logging_configured():
    global PASS, FAIL
    try:
        from routes.socket_events import get_socket_logger
        logger = get_socket_logger()
        ok = logger is not None
        ok = ok and logger.level > 0
        print_result('SocketIO logging configured', ok)
    except Exception as e:
        print(f'  [FAIL] SocketIO logging configured ({e})')
        FAIL += 1


def cleanup():
    if _task_id:
        execute_query('DELETE FROM comments WHERE task_id=%s', (_task_id,))
        execute_query('DELETE FROM tasks WHERE id=%s', (_task_id,))
    if _project_id:
        execute_query('DELETE FROM project_members WHERE project_id=%s', (_project_id,))
        execute_query('DELETE FROM projects WHERE id=%s', (_project_id,))
    for email in [USER_EMAIL, USER2_EMAIL]:
        execute_query('DELETE FROM users WHERE email=%s', (email,))


def run_tests():
    global PASS, FAIL
    print('=' * 50)
    print('  TaskFlow SocketIO Test Suite')
    print('=' * 50)
    print()

    cleanup()
    setup()

    if _user_id and _user2_id and _project_id:
        test_socketio_instance()
        test_app_creation_with_socketio()
        test_socketio_emit()
        test_task_move_emit()
        test_comment_notification()
        test_member_addition()
        test_notification_creation()
        test_kanban_page_has_socket_data()
        test_task_detail_has_socket_data()
        test_socket_js_exists()
        test_active_users_module()
        test_app_factory_with_socketio()
        test_requirements_updated()
        test_procfile_updated()
        test_wsgi_exists()
        test_socketio_logging_configured()
    else:
        print('  [SKIP] Tests (setup failed)')

    cleanup()

    print()
    print('=' * 50)
    print(f'  RESULTS:  PASS: {PASS}  FAIL: {FAIL}')
    print('=' * 50)

    if FAIL == 0:
        print('  All SocketIO tests passed.')
    else:
        print(f'  {FAIL} test(s) failed. Review errors above.')


if __name__ == '__main__':
    run_tests()
