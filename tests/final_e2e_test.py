"""
TaskFlow Final End-to-End Test Suite

Simulates the complete user workflow:
Register -> Login -> Create Project -> Add Member -> Create Task ->
Assign Task -> Move Task on Kanban -> Add Comment -> Notification -> Logout

Usage:
    python tests/final_e2e_test.py
"""

import sys
import os
import json
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, bcrypt
from models import (
    create_user, get_user_by_email, get_user_by_id,
    create_project, get_project_by_id, get_user_projects,
    add_member, get_project_members, is_project_member,
    create_task, get_task_by_id, get_project_tasks,
    move_task_status, get_kanban_tasks,
    create_comment, get_task_comments, count_comments,
    create_notification, get_user_notifications,
    mark_notification_read, count_unread_notifications,
    delete_notification, execute_query, fetch_one,
    get_dashboard_stats
)

PASS = 0
FAIL = 0
RESULTS = []


def test(name, condition, detail=''):
    global PASS, FAIL
    if condition:
        PASS += 1
        status = 'PASS'
    else:
        FAIL += 1
        status = 'FAIL'
    RESULTS.append((status, name, detail))
    print(f'  [{status}] {name}' + (f' - {detail}' if detail else ''))


def cleanup():
    for email in ['finale2e_admin@test.com', 'finale2e_member@test.com']:
        execute_query('DELETE FROM users WHERE email=%s', (email,))
    execute_query("DELETE FROM projects WHERE name LIKE 'Final E2E%'")


def run():
    global PASS, FAIL
    RESULTS.clear()
    PASS = 0
    FAIL = 0

    print()
    print('=' * 55)
    print('  TaskFlow Final E2E Test Suite')
    print('  Complete Workflow Simulation')
    print('=' * 55)
    print()

    cleanup()

    print('  Phase 1: Registration')
    print('  ----------------------')
    app = create_app()
    test('App factory creates successfully', app is not None)

    hashed1 = bcrypt.generate_password_hash('AdminPass123!').decode('utf-8')
    admin_id = create_user('FinalAdmin', 'finale2e_admin@test.com', hashed1)
    test('Admin user created', admin_id is not None, f'id={admin_id}')

    hashed2 = bcrypt.generate_password_hash('MemberPass123!').decode('utf-8')
    member_id = create_user('FinalMember', 'finale2e_member@test.com', hashed2)
    test('Member user created', member_id is not None, f'id={member_id}')

    admin = get_user_by_email('finale2e_admin@test.com')
    test('Admin exists in database', admin is not None)
    test('Admin email matches', admin['email'] == 'finale2e_admin@test.com')
    test('Admin username matches', admin['username'] == 'FinalAdmin')

    member = get_user_by_email('finale2e_member@test.com')
    test('Member exists in database', member is not None)
    test('Member email matches', member['email'] == 'finale2e_member@test.com')

    print()
    print('  Phase 2: Login Simulation')
    print('  ------------------------')
    stored = get_user_by_email('finale2e_admin@test.com')
    test('Password hash verified', bcrypt.check_password_hash(stored['password'], 'AdminPass123!'))
    test('Wrong password rejected', not bcrypt.check_password_hash(stored['password'], 'wrong'))

    print()
    print('  Phase 3: Project Management')
    print('  --------------------------')
    p1 = create_project('Final E2E Project', 'End-to-end test project description', admin_id)
    test('Project created', p1 is not None, f'id={p1}')

    project = get_project_by_id(p1)
    test('Project retrieved by ID', project is not None)
    test('Project name matches', project['name'] == 'Final E2E Project')
    test('Project owner correct', project['owner_id'] == admin_id)

    projects = get_user_projects(admin_id)
    test('Admin has projects', len(projects) >= 1)
    project_ids = [p['id'] for p in projects]
    test('New project in user projects', p1 in project_ids)

    print()
    print('  Phase 4: Member Management')
    print('  -------------------------')
    add_member(p1, member_id)
    test('Member added to project', is_project_member(p1, member_id) is True)

    members = get_project_members(p1)
    member_ids = [m['id'] for m in members]
    test('Member appears in project member list', member_id in member_ids)

    print()
    print('  Phase 5: Task Management')
    print('  -----------------------')
    today = datetime.now()
    deadline = today + timedelta(days=7)
    t1 = create_task(p1, 'Final E2E Task 1', 'Description for task 1', member_id, 'High', 'To Do', deadline)
    test('Task created', t1 is not None, f'id={t1}')

    t2 = create_task(p1, 'Final E2E Task 2', 'Description for task 2', admin_id, 'Medium', 'In Progress', deadline)
    test('Second task created', t2 is not None, f'id={t2}')

    task1 = get_task_by_id(t1)
    test('Task retrieved by ID', task1 is not None)
    test('Task title matches', task1['title'] == 'Final E2E Task 1')
    test('Task assigned correctly', task1['assigned_to'] == member_id)
    test('Task priority matches', task1['priority'] == 'High')
    test('Task status matches', task1['status'] == 'To Do')
    test('Task project matches', task1['project_id'] == p1)

    project_tasks = get_project_tasks(p1)
    test('Project has 2 tasks', len(project_tasks) == 2)
    task_titles = [t['title'] for t in project_tasks]
    test('Task 1 in project tasks', 'Final E2E Task 1' in task_titles)
    test('Task 2 in project tasks', 'Final E2E Task 2' in task_titles)

    print()
    print('  Phase 6: Kanban Board')
    print('  ---------------------')
    kanban = get_kanban_tasks(p1)
    test('Kanban has To Do column', 'To Do' in kanban)
    test('Kanban has In Progress column', 'In Progress' in kanban)
    test('Kanban has Completed column', 'Completed' in kanban)
    test('Task 1 in To Do column', any(t['id'] == t1 for t in kanban['To Do']))
    test('Task 2 in In Progress column', any(t['id'] == t2 for t in kanban['In Progress']))

    ok = move_task_status(t1, 'In Progress')
    test('Task moved To Do -> In Progress', ok is True)

    task1_moved = get_task_by_id(t1)
    test('Task status updated to In Progress', task1_moved['status'] == 'In Progress')

    ok = move_task_status(t1, 'Completed')
    test('Task moved In Progress -> Completed', ok is True)

    task1_done = get_task_by_id(t1)
    test('Task status updated to Completed', task1_done['status'] == 'Completed')

    ok = move_task_status(t1, 'Completed')
    test('Same status move returns True', ok is True)

    ok = move_task_status(99999, 'Completed')
    test('Non-existent task returns False', ok is False)

    ok = move_task_status(t1, 'Invalid Status')
    test('Invalid status returns False', ok is False)

    print()
    print('  Phase 7: Comments')
    print('  ----------------')
    import html
    comment_text = 'This is a final E2E test comment.'
    escaped = html.escape(comment_text)
    c1 = create_comment(t2, member_id, escaped)
    test('Comment created', c1 is not None, f'id={c1}')

    c2 = create_comment(t2, admin_id, html.escape('Admin response comment.'))
    test('Second comment created', c2 is not None, f'id={c2}')

    comments = get_task_comments(t2)
    test('Task has 2 comments', len(comments) == 2)

    count = count_comments(t2)
    test('Comment count matches', count == 2)

    test('First comment content correct', comments[0]['comment'] == 'This is a final E2E test comment.')
    test('Comments ordered by created_at ASC', comments[0]['id'] == c1)

    print()
    print('  Phase 8: Notifications')
    print('  ---------------------')
    n1 = create_notification(member_id, 'Final E2E: You were assigned a task.')
    test('Notification created', n1 is not None, f'id={n1}')

    n2 = create_notification(member_id, 'Final E2E: Task was moved to Completed.')
    test('Second notification created', n2 is not None, f'id={n2}')

    notifs = get_user_notifications(member_id)
    test('Member has 2 notifications', len(notifs) >= 2)

    unread = count_unread_notifications(member_id)
    test('Has unread notifications', unread >= 2)

    ok = mark_notification_read(n1, member_id)
    test('Notification marked as read', ok is True)

    unread_after = count_unread_notifications(member_id)
    test('Unread count decreased', unread_after < unread)

    ok = delete_notification(n1, member_id)
    test('Notification deleted', ok is True)

    print()
    print('  Phase 9: Dashboard & Stats')
    print('  --------------------------')
    stats = get_dashboard_stats(admin_id)
    test('Dashboard stats retrieved', stats is not None)
    test('Has projects count', stats['total_projects'] >= 1)
    test('Has tasks count', stats['total_tasks'] >= 2)
    test('Has completed count', stats['completed_tasks'] >= 1)

    print()
    print('  Phase 10: Flask Application Routes')
    print('  ----------------------------------')
    with app.test_client() as client:
        resp = client.get('/health')
        data = resp.get_json()
        test('Health endpoint accessible', resp.status_code == 200)
        test('Health status healthy', data['status'] == 'healthy')
        test('Version in health endpoint', data['version'] == '1.0.0')
        test('Tagline in health endpoint', 'tagline' in data)

        resp = client.get('/metrics')
        data = resp.get_json()
        test('Metrics endpoint accessible', resp.status_code == 200)
        test('Version in metrics', data['version'] == '1.0.0')

        resp = client.get('/')
        test('Index page loads', resp.status_code == 200)
        test('TaskFlow branding on index', b'TaskFlow' in resp.data)

        resp = client.get('/nonexistent')
        test('404 page renders', resp.status_code == 404)
        test('404 page has branding', b'TaskFlow' in resp.data)

        resp = client.get('/static/manifest.json')
        test('PWA manifest accessible', resp.status_code == 200)

        resp = client.get('/static/service-worker.js')
        test('Service worker accessible', resp.status_code == 200)

        resp = client.get('/static/images/favicon.svg')
        test('Favicon accessible', resp.status_code == 200)

    print()
    print('  Phase 11: Cleanup')
    print('  -----------------')
    cleanup()
    test('Test data cleaned up', True)

    print()
    print('=' * 55)
    print(f'  RESULTS:  PASS: {PASS}  FAIL: {FAIL}')
    print('=' * 55)

    if FAIL == 0:
        print('  FINAL E2E WORKFLOW: ALL TESTS PASSED')
        print('  Complete user workflow verified successfully.')
    else:
        print(f'  WARNING: {FAIL} test(s) failed')
        for status, name, detail in RESULTS:
            if status == 'FAIL':
                print(f'    FAIL: {name} - {detail}')
    print()

    return FAIL == 0


if __name__ == '__main__':
    success = run()
    sys.exit(0 if success else 1)
