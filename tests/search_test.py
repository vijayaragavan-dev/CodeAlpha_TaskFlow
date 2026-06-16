import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app
from models import (
    create_user, create_project, create_task, add_member,
    search_tasks, get_user_project_ids, execute_query
)
from datetime import datetime, timedelta

PASS = 0
FAIL = 0

OWNER_EMAIL = 'search_owner@example.com'
OWNER_USERNAME = 'search_owner'
MEMBER_EMAIL = 'search_member@example.com'
MEMBER_USERNAME = 'search_member'
PASSWORD = 'TestPass123!'

_owner_id = None
_member_id = None
_project_id = None
_project2_id = None
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
    global _owner_id, _member_id, _project_id, _project2_id, _task_ids
    for email in [OWNER_EMAIL, MEMBER_EMAIL]:
        execute_query('DELETE FROM users WHERE email=%s', (email,))
    execute_query('DELETE FROM projects WHERE name LIKE %s', ('Search Test%',))

    _owner_id = create_user(OWNER_USERNAME, OWNER_EMAIL, PASSWORD)
    _member_id = create_user(MEMBER_USERNAME, MEMBER_EMAIL, PASSWORD)
    _project_id = create_project('Search Test Project', 'Search testing project', _owner_id)
    _project2_id = create_project('Search Test Project 2', 'Another search project', _owner_id)
    add_member(_project_id, _member_id)

    _task_ids = []
    tid1 = create_task(_project_id, 'Login Feature', 'Implement user login page', _member_id, 'High', 'To Do', datetime.now() + timedelta(days=7))
    tid2 = create_task(_project_id, 'Dashboard UI', 'Build dashboard interface', _owner_id, 'Medium', 'In Progress', None)
    tid3 = create_task(_project_id, 'API Documentation', 'Write API docs', None, 'Low', 'Completed', None)
    tid4 = create_task(_project2_id, 'Search Feature', 'Implement search engine', _member_id, 'High', 'To Do', None)
    _task_ids = [t for t in [tid1, tid2, tid3, tid4] if t]


def test_search_by_keyword():
    global PASS, FAIL
    try:
        tasks, total = search_tasks(_owner_id, q='Login')
        ok = total >= 1
        ok = ok and any('Login' in t['title'] for t in tasks)
        print_result('Search by keyword', ok)
    except Exception as e:
        print(f'  [FAIL] Search by keyword ({e})')
        FAIL += 1


def test_search_by_description():
    global PASS, FAIL
    try:
        tasks, total = search_tasks(_owner_id, q='dashboard')
        ok = total >= 1
        ok = ok and any('Dashboard' in t['title'] for t in tasks)
        print_result('Search by description', ok)
    except Exception as e:
        print(f'  [FAIL] Search by description ({e})')
        FAIL += 1


def test_filter_by_status():
    global PASS, FAIL
    try:
        tasks, total = search_tasks(_owner_id, status='Completed')
        ok = total >= 1
        ok = ok and all(t['status'] == 'Completed' for t in tasks)
        print_result('Filter by status', ok)
    except Exception as e:
        print(f'  [FAIL] Filter by status ({e})')
        FAIL += 1


def test_filter_by_priority():
    global PASS, FAIL
    try:
        tasks, total = search_tasks(_owner_id, priority='High')
        ok = total >= 1
        ok = ok and all(t['priority'] == 'High' for t in tasks)
        print_result('Filter by priority', ok)
    except Exception as e:
        print(f'  [FAIL] Filter by priority ({e})')
        FAIL += 1


def test_filter_by_project():
    global PASS, FAIL
    try:
        tasks, total = search_tasks(_owner_id, project_id=_project2_id)
        ok = total >= 1
        ok = ok and all(t['project_id'] == _project2_id for t in tasks)
        print_result('Filter by project', ok)
    except Exception as e:
        print(f'  [FAIL] Filter by project ({e})')
        FAIL += 1


def test_filter_by_assigned():
    global PASS, FAIL
    try:
        tasks, total = search_tasks(_owner_id, assigned_to=_member_id)
        ok = total >= 1
        ok = ok and all(t['assigned_to'] == _member_id for t in tasks)
        print_result('Filter by assigned user', ok)
    except Exception as e:
        print(f'  [FAIL] Filter by assigned user ({e})')
        FAIL += 1


def test_combined_filters():
    global PASS, FAIL
    try:
        tasks, total = search_tasks(_owner_id, status='To Do', priority='High')
        ok = total >= 1
        ok = ok and all(t['status'] == 'To Do' and t['priority'] == 'High' for t in tasks)
        print_result('Combined filters', ok)
    except Exception as e:
        print(f'  [FAIL] Combined filters ({e})')
        FAIL += 1


def test_pagination():
    global PASS, FAIL
    try:
        tasks, total = search_tasks(_owner_id, page=1, per_page=2)
        ok = len(tasks) <= 2
        ok = ok and total >= 3
        tasks2, total2 = search_tasks(_owner_id, page=2, per_page=2)
        ok = ok and total == total2
        ok = ok and (len(tasks2) > 0 or total <= 2)
        print_result('Pagination works', ok)
    except Exception as e:
        print(f'  [FAIL] Pagination ({e})')
        FAIL += 1


def test_member_sees_project_tasks():
    global PASS, FAIL
    try:
        tasks, total = search_tasks(_member_id)
        ok = total >= 1
        ok = ok and any(t['project_id'] == _project_id for t in tasks)
        print_result('Member sees project tasks', ok)
    except Exception as e:
        print(f'  [FAIL] Member sees project tasks ({e})')
        FAIL += 1


def test_user_project_ids():
    global PASS, FAIL
    try:
        ids = get_user_project_ids(_owner_id)
        ok = len(ids) >= 2
        ok = ok and _project_id in ids
        ok = ok and _project2_id in ids
        print_result('Get user project ids', ok)
    except Exception as e:
        print(f'  [FAIL] Get user project ids ({e})')
        FAIL += 1


def test_search_page_loads():
    global PASS, FAIL
    try:
        app = create_app()
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['TESTING'] = True
        client = app.test_client()

        with client.session_transaction() as sess:
            sess['_user_id'] = str(_owner_id)
            sess['user_id'] = _owner_id

        response = client.get('/tasks/search', follow_redirects=True)
        body = response.data.decode('utf-8')
        ok = response.status_code == 200
        ok = ok and 'Search Tasks' in body or 'All Tasks' in body
        print_result('Search page loads', ok)
    except Exception as e:
        print(f'  [FAIL] Search page loads ({e})')
        FAIL += 1


def test_search_page_with_query():
    global PASS, FAIL
    try:
        app = create_app()
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['TESTING'] = True
        client = app.test_client()

        with client.session_transaction() as sess:
            sess['_user_id'] = str(_owner_id)
            sess['user_id'] = _owner_id

        response = client.get('/tasks/search?q=Login&status=To%20Do', follow_redirects=True)
        body = response.data.decode('utf-8')
        ok = response.status_code == 200
        ok = ok and 'Login' in body
        print_result('Search page with query/filters', ok)
    except Exception as e:
        print(f'  [FAIL] Search page with query/filters ({e})')
        FAIL += 1


def cleanup():
    execute_query('DELETE FROM tasks WHERE project_id IN (%s, %s)', (_project_id, _project2_id))
    execute_query('DELETE FROM project_members WHERE project_id IN (%s, %s)', (_project_id, _project2_id))
    execute_query('DELETE FROM projects WHERE id IN (%s, %s)', (_project_id, _project2_id))
    for email in [OWNER_EMAIL, MEMBER_EMAIL]:
        execute_query('DELETE FROM users WHERE email=%s', (email,))


def run_tests():
    global PASS, FAIL
    print('=' * 50)
    print('  TaskFlow Search & Filter Test Suite')
    print('=' * 50)
    print()

    cleanup()
    setup()

    if len(_task_ids) >= 4:
        test_search_by_keyword()
        test_search_by_description()
        test_filter_by_status()
        test_filter_by_priority()
        test_filter_by_project()
        test_filter_by_assigned()
        test_combined_filters()
        test_pagination()
        test_member_sees_project_tasks()
        test_user_project_ids()
        test_search_page_loads()
        test_search_page_with_query()
    else:
        print('  [SKIP] Tests (setup failed)')

    cleanup()

    print()
    print('=' * 50)
    print(f'  RESULTS:  PASS: {PASS}  FAIL: {FAIL}')
    print('=' * 50)

    if FAIL == 0:
        print('  All search & filter tests passed.')
    else:
        print(f'  {FAIL} test(s) failed. Review errors above.')


if __name__ == '__main__':
    run_tests()
