import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app
from models import (
    create_user, create_project, create_task, add_member,
    get_kanban_tasks, move_task_status, get_task_by_id,
    execute_query
)

PASS = 0
FAIL = 0

OWNER_EMAIL = 'kanban_owner@example.com'
OWNER_USERNAME = 'kanban_owner'
MEMBER_EMAIL = 'kanban_member@example.com'
MEMBER_USERNAME = 'kanban_member'
PASSWORD = 'TestPass123!'

_owner_id = None
_member_id = None
_project_id = None
_task_ids = []


def print_result(name, passed):
    global PASS, FAIL
    if passed:
        print(f'  [PASS] {name}')
        PASS += 1
    else:
        print(f'  [FAIL] {name}')
        FAIL += 1


def setup():
    global _owner_id, _member_id, _project_id, _task_ids
    for email in [OWNER_EMAIL, MEMBER_EMAIL]:
        execute_query('DELETE FROM users WHERE email=%s', (email,))
    execute_query('DELETE FROM projects WHERE name LIKE %s', ('Kanban Test%',))

    _owner_id = create_user(OWNER_USERNAME, OWNER_EMAIL, PASSWORD)
    _member_id = create_user(MEMBER_USERNAME, MEMBER_EMAIL, PASSWORD)
    _project_id = create_project('Kanban Test Project', 'Testing kanban', _owner_id)
    add_member(_project_id, _member_id)

    _task_ids = []
    tid1 = create_task(_project_id, 'Task To Do', 'Desc', _member_id, 'High', 'To Do', None)
    tid2 = create_task(_project_id, 'Task In Progress', 'Desc', _member_id, 'Medium', 'In Progress', None)
    tid3 = create_task(_project_id, 'Task Completed', 'Desc', _owner_id, 'Low', 'Completed', None)
    _task_ids = [t for t in [tid1, tid2, tid3] if t]


def test_kanban_groups_tasks():
    global PASS, FAIL
    try:
        grouped = get_kanban_tasks(_project_id)
        ok = grouped is not None
        ok = ok and 'To Do' in grouped
        ok = ok and 'In Progress' in grouped
        ok = ok and 'Completed' in grouped
        ok = ok and len(grouped['To Do']) >= 1
        ok = ok and len(grouped['In Progress']) >= 1
        ok = ok and len(grouped['Completed']) >= 1
        for tasks in grouped.values():
            for t in tasks:
                ok = ok and 'assigned_name' in t
        print_result('Kanban groups tasks by status', ok)
    except Exception as e:
        print(f'  [FAIL] Kanban groups tasks by status ({e})')
        FAIL += 1


def test_move_task_to_in_progress():
    global PASS, FAIL
    try:
        tid = _task_ids[0]
        result = move_task_status(tid, 'In Progress')
        task = get_task_by_id(tid)
        ok = result is True and task is not None and task['status'] == 'In Progress'
        print_result('Move task To Do -> In Progress', ok)
        move_task_status(tid, 'To Do')
    except Exception as e:
        print(f'  [FAIL] Move task To Do -> In Progress ({e})')
        FAIL += 1


def test_move_task_to_completed():
    global PASS, FAIL
    try:
        tid = _task_ids[0]
        result = move_task_status(tid, 'Completed')
        task = get_task_by_id(tid)
        ok = result is True and task is not None and task['status'] == 'Completed'
        print_result('Move task To Do -> Completed', ok)
        move_task_status(tid, 'To Do')
    except Exception as e:
        print(f'  [FAIL] Move task To Do -> Completed ({e})')
        FAIL += 1


def test_move_task_invalid_status():
    global PASS, FAIL
    try:
        tid = _task_ids[0]
        result = move_task_status(tid, 'Invalid Status')
        task = get_task_by_id(tid)
        ok = result is False and task is not None and task['status'] == 'To Do'
        print_result('Reject invalid status', ok)
    except Exception as e:
        print(f'  [FAIL] Reject invalid status ({e})')
        FAIL += 1


def test_move_task_same_status():
    global PASS, FAIL
    try:
        tid = _task_ids[0]
        result = move_task_status(tid, 'To Do')
        task = get_task_by_id(tid)
        ok = result is True and task is not None and task['status'] == 'To Do'
        print_result('Move task same status (no-op returns True)', ok)
    except Exception as e:
        print(f'  [FAIL] Move task same status ({e})')
        FAIL += 1


def test_kanban_page_loads():
    global PASS, FAIL
    try:
        app = create_app()
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['TESTING'] = True
        client = app.test_client()

        with client.session_transaction() as sess:
            sess['_user_id'] = str(_owner_id)
            sess['user_id'] = _owner_id

        response = client.get(f'/projects/{_project_id}/kanban', follow_redirects=True)
        body = response.data.decode('utf-8').lower()
        ok = response.status_code == 200
        ok = ok and 'kanban board' in body
        ok = ok and 'to do' in body
        ok = ok and 'in progress' in body
        ok = ok and 'completed' in body
        print_result('Kanban page loads for owner', ok)
    except Exception as e:
        print(f'  [FAIL] Kanban page loads for owner ({e})')
        FAIL += 1


def test_kanban_page_shows_tasks():
    global PASS, FAIL
    try:
        app = create_app()
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['TESTING'] = True
        client = app.test_client()

        with client.session_transaction() as sess:
            sess['_user_id'] = str(_member_id)
            sess['user_id'] = _member_id

        response = client.get(f'/projects/{_project_id}/kanban', follow_redirects=True)
        body = response.data.decode('utf-8')
        ok = 'Task To Do' in body
        ok = ok and 'Task In Progress' in body
        ok = ok and 'Task Completed' in body
        print_result('Kanban page shows all tasks', ok)
    except Exception as e:
        print(f'  [FAIL] Kanban page shows all tasks ({e})')
        FAIL += 1


def test_kanban_unauthorized():
    global PASS, FAIL
    try:
        external_id = create_user('kanban_ext', 'kanban_ext@example.com', PASSWORD)

        app = create_app()
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['TESTING'] = True
        client = app.test_client()

        with client.session_transaction() as sess:
            sess['_user_id'] = str(external_id)
            sess['user_id'] = external_id

        response = client.get(f'/projects/{_project_id}/kanban', follow_redirects=True)
        ok = response.status_code == 403 or response.status_code == 404
        print_result('Unauthorized user blocked from kanban', ok)
        execute_query('DELETE FROM users WHERE id=%s', (external_id,))
    except Exception as e:
        print(f'  [FAIL] Unauthorized user blocked from kanban ({e})')
        FAIL += 1


def test_move_api_endpoint():
    global PASS, FAIL
    try:
        app = create_app()
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['TESTING'] = True
        client = app.test_client()

        with client.session_transaction() as sess:
            sess['_user_id'] = str(_owner_id)
            sess['user_id'] = _owner_id

        tid = _task_ids[1]
        response = client.post(
            f'/tasks/{tid}/move',
            json={'status': 'Completed'},
            headers={'Content-Type': 'application/json'}
        )
        data = response.get_json()
        ok = response.status_code == 200 and data.get('success') is True
        task = get_task_by_id(tid)
        ok = ok and task['status'] == 'Completed'
        print_result('Move API endpoint succeeds', ok)
        move_task_status(tid, 'In Progress')
    except Exception as e:
        print(f'  [FAIL] Move API endpoint ({e})')
        FAIL += 1


def test_move_api_bad_status():
    global PASS, FAIL
    try:
        app = create_app()
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['TESTING'] = True
        client = app.test_client()

        with client.session_transaction() as sess:
            sess['_user_id'] = str(_owner_id)
            sess['user_id'] = _owner_id

        tid = _task_ids[1]
        response = client.post(
            f'/tasks/{tid}/move',
            json={'status': 'Fake Status'},
            headers={'Content-Type': 'application/json'}
        )
        ok = response.status_code == 400
        print_result('Move API rejects invalid status', ok)
    except Exception as e:
        print(f'  [FAIL] Move API rejects invalid status ({e})')
        FAIL += 1


def cleanup():
    execute_query('DELETE FROM tasks WHERE project_id=%s', (_project_id,))
    execute_query('DELETE FROM project_members WHERE project_id=%s', (_project_id,))
    execute_query('DELETE FROM projects WHERE id=%s', (_project_id,))
    for email in [OWNER_EMAIL, MEMBER_EMAIL, 'kanban_ext@example.com']:
        execute_query('DELETE FROM users WHERE email=%s', (email,))


def run_tests():
    global PASS, FAIL
    print('=' * 50)
    print('  TaskFlow Kanban Board Test Suite')
    print('=' * 50)
    print()

    cleanup()
    setup()

    if _project_id and len(_task_ids) >= 3:
        test_kanban_groups_tasks()
        test_move_task_to_in_progress()
        test_move_task_to_completed()
        test_move_task_invalid_status()
        test_move_task_same_status()
        test_kanban_page_loads()
        test_kanban_page_shows_tasks()
        test_kanban_unauthorized()
        test_move_api_endpoint()
        test_move_api_bad_status()
    else:
        print('  [SKIP] Tests (setup failed)')

    cleanup()

    print()
    print('=' * 50)
    print(f'  RESULTS:  PASS: {PASS}  FAIL: {FAIL}')
    print('=' * 50)

    if FAIL == 0:
        print('  All kanban tests passed.')
    else:
        print(f'  {FAIL} test(s) failed. Review errors above.')


if __name__ == '__main__':
    run_tests()
