import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, relative_time
from models import (
    create_user, create_project, create_task, add_member,
    create_comment, delete_comment, get_task_comments, count_comments,
    is_project_owner, execute_query
)
from datetime import datetime, timedelta

PASS = 0
FAIL = 0

OWNER_EMAIL = 'comment_owner@example.com'
OWNER_USERNAME = 'comment_owner'
MEMBER_EMAIL = 'comment_member@example.com'
MEMBER_USERNAME = 'comment_member'
EXTERNAL_EMAIL = 'comment_ext@example.com'
EXTERNAL_USERNAME = 'comment_ext'
PASSWORD = 'TestPass123!'

_owner_id = None
_member_id = None
_external_id = None
_project_id = None
_task_id = None
_comment_ids = []


def print_result(name, passed):
    global PASS, FAIL
    if passed:
        print(f'  [PASS] {name}')
        PASS += 1
    else:
        print(f'  [FAIL] {name}')
        FAIL += 1


def setup():
    global _owner_id, _member_id, _external_id, _project_id, _task_id
    for email in [OWNER_EMAIL, MEMBER_EMAIL, EXTERNAL_EMAIL]:
        execute_query('DELETE FROM users WHERE email=%s', (email,))
    execute_query('DELETE FROM projects WHERE name LIKE %s', ('Comment Test%',))

    _owner_id = create_user(OWNER_USERNAME, OWNER_EMAIL, PASSWORD)
    _member_id = create_user(MEMBER_USERNAME, MEMBER_EMAIL, PASSWORD)
    _external_id = create_user(EXTERNAL_USERNAME, EXTERNAL_EMAIL, PASSWORD)
    _project_id = create_project('Comment Test Project', 'Testing comments', _owner_id)
    add_member(_project_id, _member_id)
    _task_id = create_task(_project_id, 'Comment Test Task', 'Desc', _member_id, 'High', 'To Do', None)


def test_create_comment():
    global PASS, FAIL, _comment_ids
    try:
        cid = create_comment(_task_id, _owner_id, 'This is a test comment')
        _comment_ids.append(cid)
        ok = cid is not None and cid > 0
        print_result('Create comment', ok)
    except Exception as e:
        print(f'  [FAIL] Create comment ({e})')
        FAIL += 1


def test_create_comment_member():
    global PASS, FAIL, _comment_ids
    try:
        cid = create_comment(_task_id, _member_id, 'Comment from member')
        _comment_ids.append(cid)
        ok = cid is not None and cid > 0
        print_result('Create comment as member', ok)
    except Exception as e:
        print(f'  [FAIL] Create comment as member ({e})')
        FAIL += 1


def test_get_task_comments():
    global PASS, FAIL
    try:
        comments = get_task_comments(_task_id)
        ok = len(comments) >= 2
        if ok:
            ok = ok and all('username' in c for c in comments)
            ok = ok and all('email' in c for c in comments)
            ok = ok and any(c['user_id'] == _owner_id for c in comments)
            ok = ok and any(c['user_id'] == _member_id for c in comments)
        print_result('Get task comments', ok)
    except Exception as e:
        print(f'  [FAIL] Get task comments ({e})')
        FAIL += 1


def test_count_comments():
    global PASS, FAIL
    try:
        cnt = count_comments(_task_id)
        ok = cnt >= 2
        print_result('Count comments', ok)
    except Exception as e:
        print(f'  [FAIL] Count comments ({e})')
        FAIL += 1


def test_delete_own_comment():
    global PASS, FAIL
    try:
        cid = _comment_ids[0]
        affected = delete_comment(cid)
        ok = affected > 0
        comments = get_task_comments(_task_id)
        ok = ok and not any(c['id'] == cid for c in comments)
        print_result('Delete own comment', ok)
    except Exception as e:
        print(f'  [FAIL] Delete own comment ({e})')
        FAIL += 1


def test_comment_not_found():
    global PASS, FAIL
    try:
        affected = delete_comment(99999)
        ok = affected == 0
        print_result('Delete non-existent comment', ok)
    except Exception as e:
        print(f'  [FAIL] Delete non-existent comment ({e})')
        FAIL += 1


def test_comment_order():
    global PASS, FAIL
    try:
        comments = get_task_comments(_task_id)
        ok = True
        for i in range(len(comments) - 1):
            if comments[i]['created_at'] and comments[i + 1]['created_at']:
                if comments[i]['created_at'] > comments[i + 1]['created_at']:
                    ok = False
                    break
        print_result('Comments ordered by created_at ASC', ok)
    except Exception as e:
        print(f'  [FAIL] Comments ordered by created_at ASC ({e})')
        FAIL += 1


def test_relative_time():
    global PASS, FAIL
    try:
        now = datetime.now()
        ok = relative_time(now) == 'Just now'
        ok = ok and relative_time(now - timedelta(minutes=5)) == '5 minutes ago'
        ok = ok and relative_time(now - timedelta(hours=3)) == '3 hours ago'
        ok = ok and relative_time(now - timedelta(days=1)) == 'Yesterday'
        ok = ok and relative_time(now - timedelta(days=7)) == '7 days ago'
        ok = ok and relative_time(None) == ''
        print_result('Relative time function', ok)
    except Exception as e:
        print(f'  [FAIL] Relative time function ({e})')
        FAIL += 1


def test_comment_page_loads():
    global PASS, FAIL
    try:
        app = create_app()
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['TESTING'] = True
        client = app.test_client()

        with client.session_transaction() as sess:
            sess['_user_id'] = str(_owner_id)
            sess['user_id'] = _owner_id

        response = client.get(f'/tasks/{_task_id}', follow_redirects=True)
        body = response.data.decode('utf-8').lower()
        ok = response.status_code == 200
        ok = ok and 'comments' in body
        ok = ok and 'add comment' in body
        ok = ok and 'comment from member' in body
        print_result('Comment page loads with comments', ok)
    except Exception as e:
        print(f'  [FAIL] Comment page loads ({e})')
        FAIL += 1


def test_comment_endpoint():
    global PASS, FAIL
    try:
        app = create_app()
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['TESTING'] = True
        client = app.test_client()

        with client.session_transaction() as sess:
            sess['_user_id'] = str(_member_id)
            sess['user_id'] = _member_id

        response = client.post(
            f'/tasks/{_task_id}/comments/add',
            data={'comment': 'Comment via endpoint'},
            follow_redirects=True
        )
        ok = response.status_code == 200
        body = response.data.decode('utf-8')
        ok = ok and 'Comment added successfully' in body
        comments = get_task_comments(_task_id)
        ok = ok and any('Comment via endpoint' in c['comment'] for c in comments)
        print_result('Comment endpoint works', ok)
    except Exception as e:
        print(f'  [FAIL] Comment endpoint ({e})')
        FAIL += 1


def test_comment_unauthorized():
    global PASS, FAIL
    try:
        app = create_app()
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['TESTING'] = True
        client = app.test_client()

        with client.session_transaction() as sess:
            sess['_user_id'] = str(_external_id)
            sess['user_id'] = _external_id

        response = client.get(f'/tasks/{_task_id}', follow_redirects=True)
        ok = response.status_code == 403
        print_result('Unauthorized user blocked from comments', ok)
    except Exception as e:
        print(f'  [FAIL] Unauthorized user blocked from comments ({e})')
        FAIL += 1


def cleanup():
    execute_query('DELETE FROM comments WHERE task_id=%s', (_task_id,))
    execute_query('DELETE FROM tasks WHERE id=%s', (_task_id,))
    execute_query('DELETE FROM project_members WHERE project_id=%s', (_project_id,))
    execute_query('DELETE FROM projects WHERE id=%s', (_project_id,))
    for email in [OWNER_EMAIL, MEMBER_EMAIL, EXTERNAL_EMAIL]:
        execute_query('DELETE FROM users WHERE email=%s', (email,))


def run_tests():
    global PASS, FAIL, _comment_ids
    print('=' * 50)
    print('  TaskFlow Comments Test Suite')
    print('=' * 50)
    print()

    cleanup()
    _comment_ids = []
    setup()

    if _task_id:
        test_create_comment()
        test_create_comment_member()
        test_get_task_comments()
        test_count_comments()
        test_delete_own_comment()
        test_comment_not_found()
        test_comment_order()
        test_relative_time()
        test_comment_page_loads()
        test_comment_endpoint()
        test_comment_unauthorized()
    else:
        print('  [SKIP] Tests (setup failed)')

    cleanup()

    print()
    print('=' * 50)
    print(f'  RESULTS:  PASS: {PASS}  FAIL: {FAIL}')
    print('=' * 50)

    if FAIL == 0:
        print('  All comment tests passed.')
    else:
        print(f'  {FAIL} test(s) failed. Review errors above.')


if __name__ == '__main__':
    run_tests()
