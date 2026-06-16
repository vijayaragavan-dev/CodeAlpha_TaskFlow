import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models import (
    create_user, create_project, get_project_by_id,
    add_member, remove_member, get_project_members, is_project_member,
    create_task, update_task, delete_task, get_task_by_id,
    get_project_tasks, count_project_tasks,
    execute_query
)

PASS = 0
FAIL = 0

OWNER_USERNAME = 'task_owner'
OWNER_EMAIL = 'task_owner@example.com'
MEMBER_USERNAME = 'task_member'
MEMBER_EMAIL = 'task_member@example.com'
EXTERNAL_USERNAME = 'task_external'
EXTERNAL_EMAIL = 'task_external@example.com'
PASSWORD = 'TestPass123!'

_owner_id = None
_member_id = None
_external_id = None
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
    global _owner_id, _member_id, _external_id, _project_id
    execute_query('DELETE FROM tasks WHERE title LIKE %s', ('Test Task%',))
    execute_query('DELETE FROM project_members WHERE project_id IN (SELECT id FROM projects WHERE name LIKE %s)', ('Phase4%',))
    execute_query('DELETE FROM projects WHERE name LIKE %s', ('Phase4%',))
    for email in [OWNER_EMAIL, MEMBER_EMAIL, EXTERNAL_EMAIL]:
        execute_query('DELETE FROM users WHERE email=%s', (email,))

    _owner_id = create_user(OWNER_USERNAME, OWNER_EMAIL, PASSWORD)
    _member_id = create_user(MEMBER_USERNAME, MEMBER_EMAIL, PASSWORD)
    _external_id = create_user(EXTERNAL_USERNAME, EXTERNAL_EMAIL, PASSWORD)
    _project_id = create_project('Phase4 Test Project', 'Testing members and tasks', _owner_id)


def test_add_member():
    global PASS, FAIL
    try:
        result = add_member(_project_id, _member_id)
        ok = result is True
        members = get_project_members(_project_id)
        ok = ok and any(m['id'] == _member_id for m in members)
        print_result('Add member', ok)
    except Exception as e:
        print(f'  [FAIL] Add member ({e})')
        FAIL += 1


def test_duplicate_member():
    global PASS, FAIL
    try:
        result = add_member(_project_id, _member_id)
        ok = result is False
        print_result('Duplicate member prevented', ok)
    except Exception as e:
        print(f'  [FAIL] Duplicate member prevented ({e})')
        FAIL += 1


def test_is_project_member():
    global PASS, FAIL
    try:
        ok = is_project_member(_project_id, _member_id) is True
        ok = ok and is_project_member(_project_id, _external_id) is False
        print_result('Project member check', ok)
    except Exception as e:
        print(f'  [FAIL] Project member check ({e})')
        FAIL += 1


def test_remove_member():
    global PASS, FAIL
    try:
        remove_member(_project_id, _member_id)
        members = get_project_members(_project_id)
        ok = not any(m['id'] == _member_id for m in members)
        print_result('Remove member', ok)
        add_member(_project_id, _member_id)
    except Exception as e:
        print(f'  [FAIL] Remove member ({e})')
        FAIL += 1


def test_create_task():
    global PASS, FAIL, _task_id
    try:
        tid = create_task(_project_id, 'Test Task Alpha', 'Description', _member_id, 'High', 'To Do', None)
        _task_id = tid
        ok = tid is not None and tid > 0
        print_result('Create task', ok)
    except Exception as e:
        print(f'  [FAIL] Create task ({e})')
        FAIL += 1


def test_get_task():
    global PASS, FAIL
    try:
        task = get_task_by_id(_task_id)
        ok = task is not None
        ok = ok and task['title'] == 'Test Task Alpha'
        ok = ok and task['assigned_name'] == MEMBER_USERNAME
        ok = ok and task['project_name'] is not None
        print_result('Get task by id', ok)
    except Exception as e:
        print(f'  [FAIL] Get task by id ({e})')
        FAIL += 1


def test_update_task():
    global PASS, FAIL
    try:
        affected = update_task(_task_id, 'Updated Task', 'Updated desc', None, 'Low', 'Completed', None)
        task = get_task_by_id(_task_id)
        ok = affected >= 0
        ok = ok and task['title'] == 'Updated Task'
        ok = ok and task['status'] == 'Completed'
        ok = ok and task['priority'] == 'Low'
        print_result('Update task', ok)
    except Exception as e:
        print(f'  [FAIL] Update task ({e})')
        FAIL += 1


def test_get_project_tasks():
    global PASS, FAIL
    try:
        tasks = get_project_tasks(_project_id)
        ok = len(tasks) >= 1
        ok = ok and any(t['id'] == _task_id for t in tasks)
        ok = ok and 'assigned_name' in tasks[0]
        print_result('Get project tasks', ok)
    except Exception as e:
        print(f'  [FAIL] Get project tasks ({e})')
        FAIL += 1


def test_count_tasks():
    global PASS, FAIL
    try:
        total = count_project_tasks(_project_id)
        ok = total >= 1
        print_result('Count project tasks', ok)
    except Exception as e:
        print(f'  [FAIL] Count project tasks ({e})')
        FAIL += 1


def test_delete_task():
    global PASS, FAIL
    try:
        affected = delete_task(_task_id)
        task = get_task_by_id(_task_id)
        ok = affected >= 0 and task is None
        print_result('Delete task', ok)
    except Exception as e:
        print(f'  [FAIL] Delete task ({e})')
        FAIL += 1


def cleanup():
    execute_query('DELETE FROM tasks WHERE title LIKE %s', ('Test Task%',))
    execute_query('DELETE FROM tasks WHERE title LIKE %s', ('Updated Task%',))
    execute_query('DELETE FROM project_members WHERE project_id=%s', (_project_id,))
    execute_query('DELETE FROM projects WHERE id=%s', (_project_id,))
    for email in [OWNER_EMAIL, MEMBER_EMAIL, EXTERNAL_EMAIL]:
        execute_query('DELETE FROM users WHERE email=%s', (email,))


def run_tests():
    global PASS, FAIL
    print('=' * 50)
    print('  TaskFlow Members & Task CRUD Test Suite')
    print('=' * 50)
    print()

    cleanup()
    setup()

    test_add_member()
    test_duplicate_member()
    test_is_project_member()
    test_remove_member()
    test_create_task()
    if _task_id:
        test_get_task()
        test_update_task()
        test_get_project_tasks()
        test_count_tasks()
        test_delete_task()
    else:
        print('  [SKIP] Remaining tests (no task created)')

    cleanup()

    print()
    print('=' * 50)
    print(f'  RESULTS:  PASS: {PASS}  FAIL: {FAIL}')
    print('=' * 50)

    if FAIL == 0:
        print('  All member & task tests passed.')
    else:
        print(f'  {FAIL} test(s) failed. Review errors above.')


if __name__ == '__main__':
    run_tests()
