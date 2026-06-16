import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, bcrypt
from models import (
    create_user, create_project, get_project_by_id,
    add_member, get_project_members,
    get_project_tasks, execute_query, fetch_one
)

PASS = 0
FAIL = 0

OWNER_EMAIL = 'ct_owner@example.com'
OWNER_USERNAME = 'ct_owner'
MEMBER_EMAIL = 'ct_member@example.com'
MEMBER_USERNAME = 'ct_member'
PASSWORD = 'TestPass123!'

_owner_id = None
_member_id = None
_project_id = None


def print_result(name, passed):
    global PASS, FAIL
    if passed:
        print(f'  [PASS] {name}')
        PASS += 1
    else:
        print(f'  [FAIL] {name}')
        FAIL += 1


def get_client():
    app = create_app()
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['TESTING'] = True
    app.config['SERVER_NAME'] = 'localhost'
    with app.app_context():
        pass
    return app.test_client()


def cleanup():
    execute_query('DELETE FROM tasks WHERE title LIKE %s', ('CT Test%',))
    execute_query('DELETE FROM project_members WHERE project_id IN (SELECT id FROM projects WHERE name LIKE %s)', ('CT Test%',))
    execute_query('DELETE FROM projects WHERE name LIKE %s', ('CT Test%',))
    for email in [OWNER_EMAIL, MEMBER_EMAIL]:
        execute_query('DELETE FROM users WHERE email=%s', (email,))


def setup():
    global _owner_id, _member_id, _project_id
    cleanup()
    hashed = bcrypt.generate_password_hash(PASSWORD).decode('utf-8')
    _owner_id = create_user(OWNER_USERNAME, OWNER_EMAIL, hashed)
    _member_id = create_user(MEMBER_USERNAME, MEMBER_EMAIL, hashed)
    _project_id = create_project('CT Test Project', 'Testing create task', _owner_id)
    add_member(_project_id, _member_id)


def login(client, email=OWNER_EMAIL):
    resp = client.post('/auth/login', data={
        'email': email,
        'password': PASSWORD
    }, follow_redirects=True)
    return client


def test_01_get_create_task_page_as_owner():
    global PASS, FAIL
    client = get_client()
    login(client, OWNER_EMAIL)
    resp = client.get(f'/projects/{_project_id}/tasks/create', follow_redirects=True)
    ok = resp.status_code == 200
    if ok:
        body = resp.data.decode('utf-8').lower()
        ok = ok and 'create task' in body
        ok = ok and 'unassigned' in body
    print_result('GET create task page (owner) returns 200 with form', ok)


def test_02_get_create_task_page_as_member():
    global PASS, FAIL
    client = get_client()
    login(client, MEMBER_EMAIL)
    resp = client.get(f'/projects/{_project_id}/tasks/create', follow_redirects=True)
    ok = resp.status_code == 200
    if ok:
        body = resp.data.decode('utf-8').lower()
        ok = ok and 'create task' in body
        ok = ok and 'unassigned' in body
    print_result('GET create task page (member) returns 200 with form', ok)


def test_03_get_create_task_page_unauthenticated():
    global PASS, FAIL
    client = get_client()
    resp = client.get(f'/projects/{_project_id}/tasks/create', follow_redirects=True)
    ok = resp.status_code == 200
    body = resp.data.decode('utf-8').lower()
    ok = ok and ('login' in body or 'register' in body)
    print_result('GET create task (unauthenticated) redirects to login', ok)


def test_04_create_task_post_owner():
    global PASS, FAIL
    client = get_client()
    login(client, OWNER_EMAIL)
    resp = client.post(f'/projects/{_project_id}/tasks/create', data={
        'title': 'CT Test Task Alpha',
        'description': 'Testing task creation via POST',
        'assigned_to': _member_id,
        'priority': 'High',
        'status': 'To Do',
        'deadline': ''
    }, follow_redirects=True)
    ok = resp.status_code == 200
    body = resp.data.decode('utf-8').lower()
    ok = ok and ('success' in body or 'task created' in body)
    tasks = get_project_tasks(_project_id)
    ok = ok and any(t['title'] == 'CT Test Task Alpha' for t in tasks)
    print_result('POST create task (owner) succeeds', ok)


def test_05_create_task_post_member():
    global PASS, FAIL
    execute_query('DELETE FROM tasks WHERE title LIKE %s', ('CT Test%',))
    client = get_client()
    login(client, MEMBER_EMAIL)
    resp = client.post(f'/projects/{_project_id}/tasks/create', data={
        'title': 'CT Test Task Beta',
        'description': 'Task created by member',
        'assigned_to': '',
        'priority': 'Medium',
        'status': 'In Progress',
        'deadline': ''
    }, follow_redirects=True)
    ok = resp.status_code == 200
    body = resp.data.decode('utf-8').lower()
    ok = ok and ('success' in body or 'task created' in body)
    tasks = get_project_tasks(_project_id)
    ok = ok and any(t['title'] == 'CT Test Task Beta' for t in tasks)
    print_result('POST create task (member, unassigned) succeeds', ok)


def test_06_create_task_post_unauthenticated():
    global PASS, FAIL
    client = get_client()
    resp = client.post(f'/projects/{_project_id}/tasks/create', data={
        'title': 'CT Test Task Gamma',
        'description': 'Should not be created',
        'assigned_to': '',
        'priority': 'Low',
        'status': 'To Do',
        'deadline': ''
    }, follow_redirects=True)
    ok = resp.status_code == 200
    body = resp.data.decode('utf-8').lower()
    ok = ok and ('login' in body or 'register' in body)
    tasks = get_project_tasks(_project_id)
    ok = ok and not any(t['title'] == 'CT Test Task Gamma' for t in tasks)
    print_result('POST create task (unauthenticated) blocked', ok)


def test_07_create_task_with_deadline():
    global PASS, FAIL
    execute_query('DELETE FROM tasks WHERE title LIKE %s', ('CT Test%',))
    client = get_client()
    login(client, OWNER_EMAIL)
    resp = client.post(f'/projects/{_project_id}/tasks/create', data={
        'title': 'CT Test Task With Deadline',
        'description': 'Task with deadline',
        'assigned_to': _member_id,
        'priority': 'High',
        'status': 'To Do',
        'deadline': '2026-12-31'
    }, follow_redirects=True)
    ok = resp.status_code == 200
    body = resp.data.decode('utf-8').lower()
    ok = ok and ('success' in body or 'task created' in body)
    tasks = get_project_tasks(_project_id)
    matching = [t for t in tasks if t['title'] == 'CT Test Task With Deadline']
    ok = ok and len(matching) > 0
    if matching:
        ok = ok and matching[0]['deadline'] is not None
    print_result('POST create task with deadline succeeds', ok)


def test_08_create_task_validation_fails():
    global PASS, FAIL
    client = get_client()
    login(client, OWNER_EMAIL)
    resp = client.post(f'/projects/{_project_id}/tasks/create', data={
        'title': 'ab',
        'description': '',
        'assigned_to': '',
        'priority': 'Medium',
        'status': 'To Do',
        'deadline': ''
    }, follow_redirects=True)
    ok = resp.status_code == 200
    body = resp.data.decode('utf-8').lower()
    ok = ok and ('invalid' in body or 'error' in body or 'is-invalid' in body or 'must be' in body)
    print_result('Task validation rejects short title', ok)


def test_09_create_task_non_member_blocked():
    global PASS, FAIL
    hashed = bcrypt.generate_password_hash(PASSWORD).decode('utf-8')
    non_member_email = 'ct_none@example.com'
    non_member_id = create_user('ct_nonmember', non_member_email, hashed)
    client = get_client()
    login(client, non_member_email)
    resp = client.get(f'/projects/{_project_id}/tasks/create', follow_redirects=True)
    ok = resp.status_code == 403
    print_result('Non-member blocked from create task', ok)
    execute_query('DELETE FROM users WHERE email=%s', (non_member_email,))


def test_10_database_verification():
    global PASS, FAIL
    try:
        project = get_project_by_id(_project_id)
        ok = project is not None and 'CT Test Project' in project['name']
        members = get_project_members(_project_id)
        ok = ok and len(members) >= 1
        ok = ok and any(m['id'] == _member_id for m in members)
        print_result('Database state verified', ok)
    except Exception as e:
        print(f'  [FAIL] Database state verified ({e})')
        FAIL += 1


def run_tests():
    global PASS, FAIL
    print('=' * 55)
    print('  TaskFlow Create Task Route Test Suite')
    print('=' * 55)
    print()
    print('  Testing create task page load, form render, and POST')
    print()

    setup()

    test_01_get_create_task_page_as_owner()
    test_02_get_create_task_page_as_member()
    test_03_get_create_task_page_unauthenticated()
    test_04_create_task_post_owner()
    test_05_create_task_post_member()
    test_06_create_task_post_unauthenticated()
    test_07_create_task_with_deadline()
    test_08_create_task_validation_fails()
    test_09_create_task_non_member_blocked()
    test_10_database_verification()

    cleanup()

    print()
    print('=' * 55)
    print(f'  RESULTS:  PASS: {PASS}  FAIL: {FAIL}')
    print('=' * 55)

    if FAIL == 0:
        print('  All create task tests passed.')
    else:
        print(f'  {FAIL} test(s) failed. Review errors above.')


if __name__ == '__main__':
    run_tests()
