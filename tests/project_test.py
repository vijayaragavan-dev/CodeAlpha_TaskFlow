import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models import (
    create_project, get_project_by_id, get_user_projects,
    update_project, delete_project, get_dashboard_stats,
    create_user, execute_query
)

PASS = 0
FAIL = 0
TEST_USERNAME = 'proj_test_user'
TEST_EMAIL = 'proj_test@example.com'
TEST_PASSWORD = 'TestPass123!'
TEST_PROJECT_NAME = 'Test Project Phase 3'
TEST_PROJECT_DESC = 'This is a test project for Phase 3 validation.'
_created_project_id = None
_test_user_id = None


def print_result(name, passed):
    global PASS, FAIL
    if passed:
        print(f'  [PASS] {name}')
        PASS += 1
    else:
        print(f'  [FAIL] {name}')
        FAIL += 1


def setup():
    global _test_user_id
    execute_query('DELETE FROM projects WHERE name LIKE %s', ('Test Project%',))
    execute_query('DELETE FROM users WHERE email=%s', (TEST_EMAIL,))
    _test_user_id = create_user(TEST_USERNAME, TEST_EMAIL, TEST_PASSWORD)


def test_create_project():
    global PASS, FAIL, _created_project_id
    try:
        pid = create_project(TEST_PROJECT_NAME, TEST_PROJECT_DESC, _test_user_id)
        _created_project_id = pid
        ok = pid is not None and pid > 0
        print_result('Create project', ok)
        return ok
    except Exception as e:
        print(f'  [FAIL] Create project ({e})')
        FAIL += 1
        return False


def test_get_project():
    global PASS, FAIL
    try:
        project = get_project_by_id(_created_project_id)
        ok = project is not None and project['name'] == TEST_PROJECT_NAME
        if ok:
            ok = ok and project['owner_id'] == _test_user_id
            ok = ok and 'owner_name' in project
        print_result('Get project by id', ok)
    except Exception as e:
        print(f'  [FAIL] Get project by id ({e})')
        FAIL += 1


def test_update_project():
    global PASS, FAIL
    try:
        new_name = 'Updated Test Project'
        affected = update_project(_created_project_id, new_name, 'Updated description')
        project = get_project_by_id(_created_project_id)
        ok = affected >= 0 and project['name'] == new_name
        print_result('Update project', ok)
    except Exception as e:
        print(f'  [FAIL] Update project ({e})')
        FAIL += 1


def test_get_user_projects():
    global PASS, FAIL
    try:
        projects = get_user_projects(_test_user_id)
        ok = len(projects) >= 1
        if ok:
            ok = any(p['id'] == _created_project_id for p in projects)
            ok = ok and 'task_count' in projects[0]
        print_result('Get user projects', ok)
    except Exception as e:
        print(f'  [FAIL] Get user projects ({e})')
        FAIL += 1


def test_dashboard_stats():
    global PASS, FAIL
    try:
        stats = get_dashboard_stats(_test_user_id)
        ok = stats is not None
        if ok:
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


def test_project_owner():
    global PASS, FAIL
    try:
        project = get_project_by_id(_created_project_id)
        ok = project is not None and project['owner_id'] == _test_user_id
        another_user = create_user(
            'another_test_user', 'another@example.com', 'AnotherPass1!'
        )
        if another_user:
            ok = ok and project['owner_id'] != another_user
            execute_query('DELETE FROM users WHERE id=%s', (another_user,))
        print_result('Project owner correct', ok)
    except Exception as e:
        print(f'  [FAIL] Project owner correct ({e})')
        FAIL += 1


def test_delete_project():
    global PASS, FAIL
    try:
        affected = delete_project(_created_project_id)
        project = get_project_by_id(_created_project_id)
        ok = affected >= 0 and project is None
        print_result('Delete project', ok)
    except Exception as e:
        print(f'  [FAIL] Delete project ({e})')
        FAIL += 1


def cleanup():
    execute_query('DELETE FROM projects WHERE name LIKE %s', ('Test Project%',))
    execute_query('DELETE FROM projects WHERE name LIKE %s', ('Updated Test%',))
    execute_query('DELETE FROM users WHERE email=%s', (TEST_EMAIL,))
    execute_query('DELETE FROM users WHERE email=%s', ('another@example.com',))


def run_tests():
    global PASS, FAIL
    print('=' * 50)
    print('  TaskFlow Project CRUD Test Suite')
    print('=' * 50)
    print()
    print('  Testing project creation, retrieval, update, deletion')
    print()

    cleanup()
    setup()

    test_create_project()
    if _created_project_id:
        test_get_project()
        test_update_project()
        test_get_user_projects()
        test_dashboard_stats()
        test_project_owner()
        test_delete_project()
    else:
        print('  [SKIP] Remaining tests (no project created)')

    cleanup()

    print()
    print('=' * 50)
    print(f'  RESULTS:  PASS: {PASS}  FAIL: {FAIL}')
    print('=' * 50)

    if FAIL == 0:
        print('  All project tests passed.')
    else:
        print(f'  {FAIL} test(s) failed. Review errors above.')


if __name__ == '__main__':
    run_tests()
