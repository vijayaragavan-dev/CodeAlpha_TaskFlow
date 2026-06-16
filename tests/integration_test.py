import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, relative_time, cache_get, cache_set
from models import (
    create_user, get_user_by_email, get_user_by_id,
    create_project, get_project_by_id, update_project, delete_project,
    add_member, remove_member, get_project_members, is_project_member, is_project_owner,
    create_task, update_task, delete_task, get_task_by_id, get_project_tasks,
    count_project_tasks, move_task_status, get_kanban_tasks,
    create_comment, delete_comment, get_task_comments, count_comments,
    search_tasks, get_user_project_ids,
    get_dashboard_stats, get_user_projects,
    execute_query
)
from datetime import datetime, timedelta

PASS = 0
FAIL = 0

TEST_EMAIL = 'integration_test@example.com'
TEST_USERNAME = 'integration_user'
TEST_PASSWORD = 'TestPass123!'
TEST_EMAIL2 = 'integration_member@example.com'
TEST_USERNAME2 = 'integration_member'

_user_id = None
_user_id2 = None
_project_id = None
_task_ids = []
_comment_ids = []


def print_result(name, passed):
    global PASS, FAIL
    if passed:
        print(f'  [PASS] {name}')
        PASS += 1
    else:
        print(f'  [FAIL] {name}')
        FAIL += 1


def cleanup():
    for cid in _comment_ids:
        execute_query('DELETE FROM comments WHERE id=%s', (cid,))
    for tid in _task_ids:
        execute_query('DELETE FROM tasks WHERE id=%s', (tid,))
    if _project_id:
        execute_query('DELETE FROM project_members WHERE project_id=%s', (_project_id,))
        execute_query('DELETE FROM projects WHERE id=%s', (_project_id,))
    for email in [TEST_EMAIL, TEST_EMAIL2]:
        execute_query('DELETE FROM users WHERE email=%s', (email,))


def setup():
    global _user_id, _user_id2, _project_id
    cleanup()

    _user_id = create_user(TEST_USERNAME, TEST_EMAIL, TEST_PASSWORD)
    _user_id2 = create_user(TEST_USERNAME2, TEST_EMAIL2, TEST_PASSWORD)
    _project_id = create_project('Integration Test Project', 'Full workflow test', _user_id)


def test_01_user_creation():
    global PASS, FAIL
    try:
        user = get_user_by_email(TEST_EMAIL)
        ok = user is not None and user['username'] == TEST_USERNAME
        print_result('User registration', ok)
    except Exception as e:
        print(f'  [FAIL] User registration ({e})')
        FAIL += 1


def test_02_user_lookup():
    global PASS, FAIL
    try:
        user = get_user_by_id(_user_id)
        ok = user is not None and user['id'] == _user_id
        print_result('User lookup by ID', ok)
    except Exception as e:
        print(f'  [FAIL] User lookup by ID ({e})')
        FAIL += 1


def test_03_project_creation():
    global PASS, FAIL
    try:
        project = get_project_by_id(_project_id)
        ok = project is not None
        ok = ok and project['name'] == 'Integration Test Project'
        ok = ok and project['owner_id'] == _user_id
        ok = ok and project['owner_name'] == TEST_USERNAME
        print_result('Project creation', ok)
    except Exception as e:
        print(f'  [FAIL] Project creation ({e})')
        FAIL += 1


def test_04_project_update():
    global PASS, FAIL
    try:
        affected = update_project(_project_id, 'Updated Integration Project', 'Updated description')
        project = get_project_by_id(_project_id)
        ok = affected >= 0 and project['name'] == 'Updated Integration Project'
        print_result('Project update', ok)
        update_project(_project_id, 'Integration Test Project', 'Full workflow test')
    except Exception as e:
        print(f'  [FAIL] Project update ({e})')
        FAIL += 1


def test_05_user_projects():
    global PASS, FAIL
    try:
        projects = get_user_projects(_user_id)
        ok = len(projects) >= 1
        ok = ok and any(p['id'] == _project_id for p in projects)
        ok = ok and 'task_count' in projects[0]
        print_result('User projects', ok)
    except Exception as e:
        print(f'  [FAIL] User projects ({e})')
        FAIL += 1


def test_06_dashboard_stats():
    global PASS, FAIL
    try:
        stats = get_dashboard_stats(_user_id)
        ok = stats is not None
        ok = ok and 'total_projects' in stats
        ok = ok and 'total_tasks' in stats
        ok = ok and 'completed_tasks' in stats
        ok = ok and 'pending_tasks' in stats
        ok = ok and 'due_today' in stats
        ok = ok and stats['total_projects'] >= 1
        print_result('Dashboard stats', ok)
    except Exception as e:
        print(f'  [FAIL] Dashboard stats ({e})')
        FAIL += 1


def test_07_add_member():
    global PASS, FAIL
    try:
        result = add_member(_project_id, _user_id2)
        ok = result is True
        members = get_project_members(_project_id)
        ok = ok and any(m['id'] == _user_id2 for m in members)
        print_result('Add member', ok)
    except Exception as e:
        print(f'  [FAIL] Add member ({e})')
        FAIL += 1


def test_08_member_check():
    global PASS, FAIL
    try:
        ok = is_project_member(_project_id, _user_id2) is True
        ok = ok and is_project_member(_project_id, 99999) is False
        ok = ok and is_project_owner(_project_id, _user_id) is True
        ok = ok and is_project_owner(_project_id, _user_id2) is False
        print_result('Member and owner checks', ok)
    except Exception as e:
        print(f'  [FAIL] Member and owner checks ({e})')
        FAIL += 1


def test_09_create_tasks():
    global PASS, FAIL, _task_ids
    try:
        tid1 = create_task(_project_id, 'Task Alpha', 'First task', _user_id2, 'High', 'To Do', None)
        tid2 = create_task(_project_id, 'Task Beta', 'Second task', _user_id, 'Medium', 'In Progress', None)
        tid3 = create_task(_project_id, 'Task Gamma', 'Third task', None, 'Low', 'Completed', datetime.now() + timedelta(days=3))
        _task_ids = [t for t in [tid1, tid2, tid3] if t]
        ok = len(_task_ids) == 3
        print_result('Create tasks', ok)
    except Exception as e:
        print(f'  [FAIL] Create tasks ({e})')
        FAIL += 1


def test_10_get_tasks():
    global PASS, FAIL
    try:
        tasks = get_project_tasks(_project_id)
        ok = len(tasks) >= 3
        ok = ok and 'assigned_name' in tasks[0]
        print_result('Get project tasks', ok)
    except Exception as e:
        print(f'  [FAIL] Get project tasks ({e})')
        FAIL += 1


def test_11_task_detail():
    global PASS, FAIL
    try:
        task = get_task_by_id(_task_ids[0])
        ok = task is not None
        ok = ok and task['title'] == 'Task Alpha'
        ok = ok and task['assigned_name'] == TEST_USERNAME2
        ok = ok and task['project_name'] == 'Integration Test Project'
        ok = ok and task['project_owner_id'] == _user_id
        print_result('Task detail with relations', ok)
    except Exception as e:
        print(f'  [FAIL] Task detail ({e})')
        FAIL += 1


def test_12_update_task():
    global PASS, FAIL
    try:
        affected = update_task(_task_ids[2], 'Task Gamma Updated', 'Updated desc', _user_id2, 'High', 'Completed', None)
        task = get_task_by_id(_task_ids[2])
        ok = affected >= 0
        ok = ok and task['title'] == 'Task Gamma Updated'
        ok = ok and task['priority'] == 'High'
        print_result('Update task', ok)
        update_task(_task_ids[2], 'Task Gamma', 'Third task', None, 'Low', 'Completed', datetime.now() + timedelta(days=3))
    except Exception as e:
        print(f'  [FAIL] Update task ({e})')
        FAIL += 1


def test_13_count_tasks():
    global PASS, FAIL
    try:
        total = count_project_tasks(_project_id)
        ok = total >= 3
        print_result('Count project tasks', ok)
    except Exception as e:
        print(f'  [FAIL] Count project tasks ({e})')
        FAIL += 1


def test_14_kanban_tasks():
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
        print_result('Kanban task grouping', ok)
    except Exception as e:
        print(f'  [FAIL] Kanban task grouping ({e})')
        FAIL += 1


def test_15_move_task():
    global PASS, FAIL
    try:
        result = move_task_status(_task_ids[0], 'In Progress')
        task = get_task_by_id(_task_ids[0])
        ok = result is True and task['status'] == 'In Progress'
        print_result('Move task status', ok)
        move_task_status(_task_ids[0], 'To Do')
    except Exception as e:
        print(f'  [FAIL] Move task status ({e})')
        FAIL += 1


def test_16_create_comments():
    global PASS, FAIL, _comment_ids
    try:
        cid1 = create_comment(_task_ids[0], _user_id, 'This is a comment from owner')
        cid2 = create_comment(_task_ids[0], _user_id2, 'This is a reply from member')
        _comment_ids = [cid1, cid2]
        ok = cid1 is not None and cid2 is not None
        print_result('Create comments', ok)
    except Exception as e:
        print(f'  [FAIL] Create comments ({e})')
        FAIL += 1


def test_17_get_comments():
    global PASS, FAIL
    try:
        comments = get_task_comments(_task_ids[0])
        ok = len(comments) >= 2
        ok = ok and comments[0]['username'] in [TEST_USERNAME, TEST_USERNAME2]
        print_result('Get task comments', ok)
    except Exception as e:
        print(f'  [FAIL] Get task comments ({e})')
        FAIL += 1


def test_18_count_comments():
    global PASS, FAIL
    try:
        cnt = count_comments(_task_ids[0])
        ok = cnt >= 2
        print_result('Count comments', ok)
    except Exception as e:
        print(f'  [FAIL] Count comments ({e})')
        FAIL += 1


def test_19_delete_comment():
    global PASS, FAIL
    try:
        affected = delete_comment(_comment_ids[1])
        ok = affected > 0
        comments = get_task_comments(_task_ids[0])
        ok = ok and len(comments) >= 1
        print_result('Delete comment', ok)
    except Exception as e:
        print(f'  [FAIL] Delete comment ({e})')
        FAIL += 1


def test_20_search():
    global PASS, FAIL
    try:
        tasks, total = search_tasks(_user_id, q='Alpha')
        ok = total >= 1
        ok = ok and any('Alpha' in t['title'] for t in tasks)
        print_result('Search by keyword', ok)
    except Exception as e:
        print(f'  [FAIL] Search by keyword ({e})')
        FAIL += 1


def test_21_search_by_description():
    global PASS, FAIL
    try:
        tasks, total = search_tasks(_user_id, q='second')
        ok = total >= 1
        print_result('Search by description', ok)
    except Exception as e:
        print(f'  [FAIL] Search by description ({e})')
        FAIL += 1


def test_22_filter_status():
    global PASS, FAIL
    try:
        tasks, total = search_tasks(_user_id, status='Completed')
        ok = total >= 1
        ok = ok and all(t['status'] == 'Completed' for t in tasks)
        print_result('Filter by status', ok)
    except Exception as e:
        print(f'  [FAIL] Filter by status ({e})')
        FAIL += 1


def test_23_filter_priority():
    global PASS, FAIL
    try:
        tasks, total = search_tasks(_user_id, priority='High')
        ok = total >= 1
        ok = ok and all(t['priority'] == 'High' for t in tasks)
        print_result('Filter by priority', ok)
    except Exception as e:
        print(f'  [FAIL] Filter by priority ({e})')
        FAIL += 1


def test_24_filter_assigned():
    global PASS, FAIL
    try:
        tasks, total = search_tasks(_user_id, assigned_to=_user_id2)
        ok = total >= 1
        ok = ok and all(t['assigned_to'] == _user_id2 for t in tasks)
        print_result('Filter by assigned user', ok)
    except Exception as e:
        print(f'  [FAIL] Filter by assigned user ({e})')
        FAIL += 1


def test_25_combined_filters():
    global PASS, FAIL
    try:
        tasks, total = search_tasks(_user_id, status='To Do', priority='High')
        ok = total >= 1
        ok = ok and all(t['status'] == 'To Do' and t['priority'] == 'High' for t in tasks)
        print_result('Combined filters', ok)
    except Exception as e:
        print(f'  [FAIL] Combined filters ({e})')
        FAIL += 1


def test_26_pagination():
    global PASS, FAIL
    try:
        tasks, total = search_tasks(_user_id, page=1, per_page=2)
        ok = len(tasks) <= 2
        ok = ok and total >= 3
        tasks2, total2 = search_tasks(_user_id, page=2, per_page=2)
        ok = ok and total == total2
        print_result('Pagination', ok)
    except Exception as e:
        print(f'  [FAIL] Pagination ({e})')
        FAIL += 1


def test_27_user_project_ids():
    global PASS, FAIL
    try:
        ids = get_user_project_ids(_user_id)
        ok = len(ids) >= 1
        ok = ok and _project_id in ids
        ids2 = get_user_project_ids(_user_id2)
        ok = ok and _project_id in ids2
        print_result('User project IDs', ok)
    except Exception as e:
        print(f'  [FAIL] User project IDs ({e})')
        FAIL += 1


def test_28_relative_time():
    global PASS, FAIL
    try:
        now = datetime.now()
        ok = relative_time(now) == 'Just now'
        ok = ok and relative_time(now - timedelta(minutes=5)) == '5 minutes ago'
        ok = ok and relative_time(now - timedelta(hours=3)) == '3 hours ago'
        ok = ok and relative_time(now - timedelta(days=1)) == 'Yesterday'
        ok = ok and relative_time(None) == ''
        print_result('Relative time function', ok)
    except Exception as e:
        print(f'  [FAIL] Relative time function ({e})')
        FAIL += 1


def test_29_delete_tasks():
    global PASS, FAIL
    try:
        for tid in _task_ids[1:]:
            delete_task(tid)
        tasks = get_project_tasks(_project_id)
        ok = len(tasks) >= 1
        print_result('Delete tasks', ok)
    except Exception as e:
        print(f'  [FAIL] Delete tasks ({e})')
        FAIL += 1


def test_30_remove_member():
    global PASS, FAIL
    try:
        remove_member(_project_id, _user_id2)
        members = get_project_members(_project_id)
        ok = not any(m['id'] == _user_id2 for m in members)
        print_result('Remove member', ok)
    except Exception as e:
        print(f'  [FAIL] Remove member ({e})')
        FAIL += 1


def test_31_caching():
    global PASS, FAIL
    try:
        cache_set('test_key', 'test_value')
        val = cache_get('test_key', max_age=30)
        ok = val == 'test_value'
        print_result('Caching mechanism', ok)
    except Exception as e:
        print(f'  [FAIL] Caching ({e})')
        FAIL += 1


def test_32_flask_app_creation():
    global PASS, FAIL
    try:
        app = create_app()
        app.config['TESTING'] = True
        client = app.test_client()
        response = client.get('/')
        ok = response.status_code == 200
        print_result('Flask app creation and index page', ok)
    except Exception as e:
        print(f'  [FAIL] Flask app creation ({e})')
        FAIL += 1


def test_33_auth_endpoint():
    global PASS, FAIL
    try:
        app = create_app()
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['TESTING'] = True
        client = app.test_client()

        with client.session_transaction() as sess:
            sess['_user_id'] = str(_user_id)
            sess['user_id'] = _user_id

        response = client.get('/auth/dashboard', follow_redirects=True)
        ok = response.status_code == 200
        body = response.data.decode('utf-8').lower()
        ok = ok and ('dashboard' in body or 'welcome' in body)
        print_result('Authenticated dashboard access', ok)
    except Exception as e:
        print(f'  [FAIL] Authenticated dashboard access ({e})')
        FAIL += 1


def test_34_protected_route_redirect():
    global PASS, FAIL
    try:
        app = create_app()
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['TESTING'] = True
        client = app.test_client()

        response = client.get('/auth/dashboard', follow_redirects=True)
        body = response.data.decode('utf-8').lower()
        ok = 'login' in body or 'welcome back' in body
        print_result('Protected route redirects to login', ok)
    except Exception as e:
        print(f'  [FAIL] Protected route redirect ({e})')
        FAIL += 1


def test_35_error_page():
    global PASS, FAIL
    try:
        app = create_app()
        app.config['TESTING'] = True
        client = app.test_client()
        response = client.get('/nonexistent-route')
        ok = response.status_code == 404
        body = response.data.decode('utf-8').lower()
        ok = ok and ('not found' in body or '404' in body)
        print_result('404 error page', ok)
    except Exception as e:
        print(f'  [FAIL] 404 error page ({e})')
        FAIL += 1


def run_tests():
    global PASS, FAIL
    print('=' * 60)
    print('  TaskFlow End-to-End Integration Test Suite')
    print('=' * 60)
    print()
    print('  Testing full workflow: Registration -> Login -> Projects')
    print('  -> Members -> Tasks -> Kanban -> Comments -> Search')
    print()

    setup()

    test_01_user_creation()
    test_02_user_lookup()
    test_03_project_creation()
    test_04_project_update()
    test_05_user_projects()
    test_06_dashboard_stats()
    test_07_add_member()
    test_08_member_check()
    test_09_create_tasks()
    test_10_get_tasks()
    test_11_task_detail()
    test_12_update_task()
    test_13_count_tasks()
    test_14_kanban_tasks()
    test_15_move_task()
    test_16_create_comments()
    test_17_get_comments()
    test_18_count_comments()
    test_19_delete_comment()
    test_20_search()
    test_21_search_by_description()
    test_22_filter_status()
    test_23_filter_priority()
    test_24_filter_assigned()
    test_25_combined_filters()
    test_26_pagination()
    test_27_user_project_ids()
    test_28_relative_time()
    test_29_delete_tasks()
    test_30_remove_member()
    test_31_caching()
    test_32_flask_app_creation()
    test_33_auth_endpoint()
    test_34_protected_route_redirect()
    test_35_error_page()

    cleanup()

    print()
    print('=' * 60)
    print(f'  RESULTS:  PASS: {PASS}  FAIL: {FAIL}')
    print('=' * 60)

    if FAIL == 0:
        print('  All integration tests passed. System is production-ready.')
    else:
        print(f'  {FAIL} test(s) failed. Review errors above.')


if __name__ == '__main__':
    run_tests()
