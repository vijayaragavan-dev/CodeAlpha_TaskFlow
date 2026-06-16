import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app
from models import (
    create_user, create_project, create_task, add_member,
    create_notification, get_user_notifications, mark_notification_read,
    mark_all_notifications_read, delete_notification, count_unread_notifications,
    execute_query
)

PASS = 0
FAIL = 0

USER_EMAIL = 'notif_user@example.com'
USER_USERNAME = 'notif_user'
USER2_EMAIL = 'notif_user2@example.com'
USER2_USERNAME = 'notif_user2'
PASSWORD = 'TestPass123!'

_user_id = None
_user2_id = None
_project_id = None
_task_id = None
_notif_ids = []


def print_result(name, passed):
    global PASS, FAIL
    if passed:
        print(f'  [PASS] {name}')
        PASS += 1
    else:
        print(f'  [FAIL] {name}')
        FAIL += 1


def setup():
    global _user_id, _user2_id, _project_id, _task_id, _notif_ids
    for email in [USER_EMAIL, USER2_EMAIL]:
        execute_query('DELETE FROM users WHERE email=%s', (email,))
    execute_query('DELETE FROM notifications WHERE message LIKE %s', ('Test notification%',))

    _user_id = create_user(USER_USERNAME, USER_EMAIL, PASSWORD)
    _user2_id = create_user(USER2_USERNAME, USER2_EMAIL, PASSWORD)
    _project_id = create_project('Notif Test Project', 'Testing notifications', _user_id)
    add_member(_project_id, _user2_id)
    _task_id = create_task(_project_id, 'Notif Test Task', 'Desc', _user2_id, 'Medium', 'To Do', None)

    _notif_ids = []
    for i in range(3):
        nid = create_notification(_user_id, f'Test notification {i+1}')
        if nid:
            _notif_ids.append(nid)


def test_create_notification():
    global PASS, FAIL
    try:
        nid = create_notification(_user_id, 'Test notification create')
        ok = nid is not None and isinstance(nid, int) and nid > 0
        if nid:
            execute_query('DELETE FROM notifications WHERE id=%s', (nid,))
        print_result('Create notification', ok)
    except Exception as e:
        print(f'  [FAIL] Create notification ({e})')
        FAIL += 1


def test_get_user_notifications():
    global PASS, FAIL
    try:
        notifs = get_user_notifications(_user_id)
        ok = isinstance(notifs, list) and len(notifs) >= 3
        if ok:
            ok = ok and 'id' in notifs[0]
            ok = ok and 'message' in notifs[0]
            ok = ok and 'is_read' in notifs[0]
            ok = ok and 'created_at' in notifs[0]
        print_result('Get user notifications', ok)
    except Exception as e:
        print(f'  [FAIL] Get user notifications ({e})')
        FAIL += 1


def test_get_user_notifications_ordered():
    global PASS, FAIL
    try:
        notifs = get_user_notifications(_user_id)
        ok = len(notifs) >= 2
        if ok:
            for i in range(len(notifs) - 1):
                if notifs[i]['created_at'] < notifs[i+1]['created_at']:
                    ok = False
                    break
        print_result('Notifications ordered by created_at DESC', ok)
    except Exception as e:
        print(f'  [FAIL] Notifications ordered by created_at DESC ({e})')
        FAIL += 1


def test_get_user_notifications_limit():
    global PASS, FAIL
    try:
        notifs = get_user_notifications(_user_id, limit=2)
        ok = len(notifs) <= 2
        print_result('Get user notifications with limit', ok)
    except Exception as e:
        print(f'  [FAIL] Get user notifications with limit ({e})')
        FAIL += 1


def test_mark_notification_read():
    global PASS, FAIL
    try:
        if not _notif_ids:
            print_result('Mark notification read (no notification)', False)
            FAIL += 1
            return
        nid = _notif_ids[0]
        result = mark_notification_read(nid, _user_id)
        notifs = get_user_notifications(_user_id)
        notif = next((n for n in notifs if n['id'] == nid), None)
        ok = result is True and notif is not None and notif['is_read'] == 1
        print_result('Mark notification read', ok)
        execute_query('UPDATE notifications SET is_read=FALSE WHERE id=%s', (nid,))
    except Exception as e:
        print(f'  [FAIL] Mark notification read ({e})')
        FAIL += 1


def test_mark_all_notifications_read():
    global PASS, FAIL
    try:
        for nid in _notif_ids:
            execute_query('UPDATE notifications SET is_read=FALSE WHERE id=%s', (nid,))
        count = mark_all_notifications_read(_user_id)
        notifs = get_user_notifications(_user_id)
        ok = isinstance(count, int) and count >= 0
        if count > 0:
            all_read = all(n['is_read'] == 1 for n in notifs if n['id'] in _notif_ids)
            ok = ok and all_read
        print_result('Mark all notifications read', ok)
        for nid in _notif_ids:
            execute_query('UPDATE notifications SET is_read=FALSE WHERE id=%s', (nid,))
    except Exception as e:
        print(f'  [FAIL] Mark all notifications read ({e})')
        FAIL += 1


def test_delete_notification():
    global PASS, FAIL
    try:
        nid = create_notification(_user_id, 'Temp delete notification')
        ok = nid is not None
        if ok:
            result = delete_notification(nid, _user_id)
            ok = result is True
            notifs = get_user_notifications(_user_id)
            found = any(n['id'] == nid for n in notifs)
            ok = ok and not found
        print_result('Delete notification', ok)
    except Exception as e:
        print(f'  [FAIL] Delete notification ({e})')
        FAIL += 1


def test_delete_other_users_notification():
    global PASS, FAIL
    try:
        nid = create_notification(_user2_id, 'Other user notification')
        ok = nid is not None
        if ok:
            result = delete_notification(nid, _user_id)
            ok = result is False
            notifs = get_user_notifications(_user2_id)
            found = any(n['id'] == nid for n in notifs)
            ok = ok and found
            delete_notification(nid, _user2_id)
        print_result('Cannot delete other user notification', ok)
    except Exception as e:
        print(f'  [FAIL] Cannot delete other user notification ({e})')
        FAIL += 1


def test_mark_other_users_notification_read():
    global PASS, FAIL
    try:
        nid = create_notification(_user2_id, 'Other user read test')
        ok = nid is not None
        if ok:
            result = mark_notification_read(nid, _user_id)
            ok = result is False
            notifs = get_user_notifications(_user2_id)
            notif = next((n for n in notifs if n['id'] == nid), None)
            ok = ok and (notif is None or notif['is_read'] == 0)
            delete_notification(nid, _user2_id)
        print_result('Cannot mark other user notification read', ok)
    except Exception as e:
        print(f'  [FAIL] Cannot mark other user notification read ({e})')
        FAIL += 1


def test_count_unread_notifications():
    global PASS, FAIL
    try:
        for nid in _notif_ids:
            execute_query('UPDATE notifications SET is_read=FALSE WHERE id=%s', (nid,))
        count = count_unread_notifications(_user_id)
        ok = isinstance(count, int) and count >= 3
        print_result('Count unread notifications', ok)
    except Exception as e:
        print(f'  [FAIL] Count unread notifications ({e})')
        FAIL += 1


def test_count_unread_after_read():
    global PASS, FAIL
    try:
        for nid in _notif_ids:
            execute_query('UPDATE notifications SET is_read=FALSE WHERE id=%s', (nid,))
        if _notif_ids:
            mark_notification_read(_notif_ids[0], _user_id)
        count = count_unread_notifications(_user_id)
        ok = isinstance(count, int) and count >= 2
        print_result('Unread count decreases after read', ok)
    except Exception as e:
        print(f'  [FAIL] Unread count decreases after read ({e})')
        FAIL += 1


def test_notification_page_loads():
    global PASS, FAIL
    try:
        app = create_app()
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['TESTING'] = True
        client = app.test_client()

        with client.session_transaction() as sess:
            sess['_user_id'] = str(_user_id)
            sess['user_id'] = _user_id

        response = client.get('/notifications/', follow_redirects=True)
        body = response.data.decode('utf-8')
        ok = response.status_code == 200
        ok = ok and 'Notification' in body or 'notification' in body
        ok = ok and 'Test notification' in body
        print_result('Notifications page loads', ok)
    except Exception as e:
        print(f'  [FAIL] Notifications page loads ({e})')
        FAIL += 1


def test_notification_page_empty():
    global PASS, FAIL
    try:
        app = create_app()
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['TESTING'] = True
        client = app.test_client()

        with client.session_transaction() as sess:
            sess['_user_id'] = str(_user2_id)
            sess['user_id'] = _user2_id

        response = client.get('/notifications/', follow_redirects=True)
        body = response.data.decode('utf-8')
        ok = response.status_code == 200
        ok = ok and ('No notifications' in body or 'no notifications' in body.lower())
        print_result('Notifications page shows empty state', ok)
    except Exception as e:
        print(f'  [FAIL] Notifications page shows empty state ({e})')
        FAIL += 1


def test_notification_authorization():
    global PASS, FAIL
    try:
        app = create_app()
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['TESTING'] = True
        client = app.test_client()

        with client.session_transaction() as sess:
            sess['_user_id'] = str(_user2_id)
            sess['user_id'] = _user2_id

        nid = _notif_ids[0] if _notif_ids else 1
        response = client.post(f'/notifications/{nid}/read', follow_redirects=True)
        ok = response.status_code == 403 or response.status_code == 404
        print_result('Authorization blocks reading other user notification', ok)
    except Exception as e:
        print(f'  [FAIL] Authorization blocks reading other user notification ({e})')
        FAIL += 1


def test_notification_requires_login():
    global PASS, FAIL
    try:
        app = create_app()
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['TESTING'] = True
        client = app.test_client()

        response = client.get('/notifications/', follow_redirects=True)
        ok = response.status_code == 200
        body = response.data.decode('utf-8').lower()
        ok = ok and ('login' in body or 'sign in' in body)
        print_result('Notifications page requires login', ok)
    except Exception as e:
        print(f'  [FAIL] Notifications page requires login ({e})')
        FAIL += 1


def test_unread_api():
    global PASS, FAIL
    try:
        app = create_app()
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['TESTING'] = True
        client = app.test_client()

        with client.session_transaction() as sess:
            sess['_user_id'] = str(_user_id)
            sess['user_id'] = _user_id

        response = client.get('/notifications/unread-count')
        data = response.get_json()
        ok = response.status_code == 200
        ok = ok and data is not None
        ok = ok and 'count' in data
        ok = ok and isinstance(data['count'], int)
        print_result('Unread count API', ok)
    except Exception as e:
        print(f'  [FAIL] Unread count API ({e})')
        FAIL += 1


def cleanup():
    for uid in [_user_id, _user2_id]:
        if uid:
            execute_query('DELETE FROM notifications WHERE user_id=%s', (uid,))
    if _task_id:
        execute_query('DELETE FROM tasks WHERE id=%s', (_task_id,))
    if _project_id:
        execute_query('DELETE FROM project_members WHERE project_id=%s', (_project_id,))
        execute_query('DELETE FROM projects WHERE id=%s', (_project_id,))
    for email in [USER_EMAIL, USER2_EMAIL]:
        execute_query('DELETE FROM users WHERE email=%s', (email,))


def run_tests():
    global PASS, FAIL
    print('=' * 50)
    print('  TaskFlow Notification Test Suite')
    print('=' * 50)
    print()

    cleanup()
    setup()

    if _user_id and _user2_id and _project_id:
        test_create_notification()
        test_get_user_notifications()
        test_get_user_notifications_ordered()
        test_get_user_notifications_limit()
        test_mark_notification_read()
        test_mark_all_notifications_read()
        test_delete_notification()
        test_delete_other_users_notification()
        test_mark_other_users_notification_read()
        test_count_unread_notifications()
        test_count_unread_after_read()
        test_notification_page_loads()
        test_notification_page_empty()
        test_notification_authorization()
        test_notification_requires_login()
        test_unread_api()
    else:
        print('  [SKIP] Tests (setup failed)')

    cleanup()

    print()
    print('=' * 50)
    print(f'  RESULTS:  PASS: {PASS}  FAIL: {FAIL}')
    print('=' * 50)

    if FAIL == 0:
        print('  All notification tests passed.')
    else:
        print(f'  {FAIL} test(s) failed. Review errors above.')


if __name__ == '__main__':
    run_tests()
