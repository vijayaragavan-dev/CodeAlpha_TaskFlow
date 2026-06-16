#!/usr/bin/env python3
"""
TaskFlow Demo Data Seeder

Usage:
    python scripts/seed_demo_data.py

Creates demo users, projects, tasks, comments, and notifications
for testing and portfolio demonstration purposes.
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, bcrypt
from models import (
    create_user, create_project, create_task, add_member,
    create_comment, create_notification, execute_query, fetch_one
)

app = create_app()

DEMO_EMAIL = 'demo@taskflow.com'
DEMO_PASSWORD = 'DemoPass123!'
DEMO_USERNAME = 'Demo User'

MEMBER_EMAIL = 'member@taskflow.com'
MEMBER_PASSWORD = 'MemberPass123!'
MEMBER_USERNAME = 'Jane Member'


def seed():
    print('=' * 50)
    print('  TaskFlow Demo Data Seeder')
    print('=' * 50)
    print()

    print('Cleaning existing demo data...')
    for email in [DEMO_EMAIL, MEMBER_EMAIL]:
        execute_query('DELETE FROM users WHERE email=%s', (email,))
    execute_query("DELETE FROM projects WHERE name LIKE 'Demo%'")
    execute_query("DELETE FROM notifications WHERE message LIKE 'Demo%'")

    print('Creating demo users...')
    hashed = bcrypt.generate_password_hash(DEMO_PASSWORD).decode('utf-8')
    demo_id = create_user(DEMO_USERNAME, DEMO_EMAIL, hashed)
    print(f'  Demo user created: id={demo_id}')

    hashed2 = bcrypt.generate_password_hash(MEMBER_PASSWORD).decode('utf-8')
    member_id = create_user(MEMBER_USERNAME, MEMBER_EMAIL, hashed2)
    print(f'  Member user created: id={member_id}')

    print('Creating demo projects...')
    p1 = create_project(
        'Demo Project - Website Redesign',
        'Complete redesign of the company website with modern UI/UX principles, responsive design, and performance optimization.',
        demo_id
    )
    print(f'  Project created: id={p1}')

    p2 = create_project(
        'Demo Project - Mobile App',
        'Cross-platform mobile application for task management with push notifications and offline support.',
        demo_id
    )
    print(f'  Project created: id={p2}')

    p3 = create_project(
        'Demo Project - API Gateway',
        'Microservices API gateway with rate limiting, authentication, and request routing.',
        demo_id
    )
    print(f'  Project created: id={p3}')

    print('Adding members...')
    add_member(p1, member_id)
    add_member(p2, member_id)
    print(f'  Member {member_id} added to projects {p1}, {p2}')

    print('Creating demo tasks...')
    today = datetime.now()

    tasks_data = [
        (p1, 'Design homepage mockup', 'Create Figma mockups for the new homepage layout', member_id, 'High', 'To Do', today + timedelta(days=3)),
        (p1, 'Implement responsive navbar', 'Build a responsive navigation bar using Bootstrap 5', member_id, 'Medium', 'In Progress', today + timedelta(days=5)),
        (p1, 'Set up CI/CD pipeline', 'Configure GitHub Actions for automated deployment', demo_id, 'High', 'Completed', today - timedelta(days=1)),
        (p1, 'Write unit tests', 'Achieve 90% test coverage for all backend routes', member_id, 'Medium', 'To Do', today + timedelta(days=7)),
        (p2, 'Design database schema', 'Design the core database tables for the mobile app', demo_id, 'High', 'Completed', today - timedelta(days=2)),
        (p2, 'Build REST API', 'Implement RESTful API endpoints for task CRUD operations', member_id, 'High', 'In Progress', today + timedelta(days=4)),
        (p2, 'Implement push notifications', 'Add Firebase Cloud Messaging for push notifications', member_id, 'Low', 'To Do', today + timedelta(days=14)),
        (p3, 'Implement rate limiting', 'Add token bucket rate limiting to the API gateway', demo_id, 'High', 'To Do', today + timedelta(days=6)),
        (p3, 'Add JWT authentication', 'Implement JWT-based authentication middleware', member_id, 'High', 'In Progress', today + timedelta(days=3)),
        (p3, 'Write API documentation', 'Document all API endpoints with OpenAPI/Swagger', member_id, 'Medium', 'To Do', today + timedelta(days=10)),
    ]

    task_ids = []
    for (proj_id, title, desc, assigned, priority, status, deadline) in tasks_data:
        tid = create_task(proj_id, title, desc, assigned, priority, status, deadline)
        task_ids.append(tid)
        print(f'  Task created: id={tid} title="{title}"')

    print('Creating demo comments...')
    import html
    comments_data = [
        (task_ids[0], member_id, 'I have started working on the Figma mockups. Will share the first draft soon.'),
        (task_ids[1], demo_id, 'The navbar looks great on desktop. Please ensure mobile responsiveness is tested.'),
        (task_ids[1], member_id, 'Mobile version is working well. I tested on iPhone 14 and Pixel 7.'),
        (task_ids[2], demo_id, 'CI/CD pipeline is fully green. All 128 tests passing.'),
        (task_ids[5], member_id, 'The REST API endpoints are ready for review.'),
        (task_ids[5], demo_id, 'Great work! I left some comments on the PR.'),
        (task_ids[8], member_id, 'JWT implementation is complete. Tokens expire after 8 hours.'),
    ]
    for (tid, uid, text) in comments_data:
        escaped = html.escape(text)
        cid = create_comment(tid, uid, escaped)
        print(f'  Comment created: id={cid}')

    print('Creating demo notifications...')
    notification_data = [
        (member_id, f'Demo: You were added to project: Demo Project - Website Redesign'),
        (member_id, f'Demo: You were added to project: Demo Project - Mobile App'),
        (member_id, f'Demo: {DEMO_USERNAME} assigned you task: Design homepage mockup'),
        (member_id, f'Demo: {DEMO_USERNAME} assigned you task: Implement responsive navbar'),
        (demo_id, f'Demo: {MEMBER_USERNAME} commented on your task: Implement responsive navbar'),
        (member_id, f'Demo: Task \'Set up CI/CD pipeline\' moved to Completed'),
    ]
    for (uid, msg) in notification_data:
        nid = create_notification(uid, msg)
        print(f'  Notification created: id={nid}')

    print()
    print('=' * 50)
    print('  Demo Data Seeded Successfully!')
    print('=' * 50)
    print()
    print('  Demo Credentials:')
    print(f'    Email:    {DEMO_EMAIL}')
    print(f'    Password: {DEMO_PASSWORD}')
    print()
    print(f'  Member Credentials:')
    print(f'    Email:    {MEMBER_EMAIL}')
    print(f'    Password: {MEMBER_PASSWORD}')
    print()
    print(f'  Created:')
    print(f'    Users:         2')
    print(f'    Projects:      3')
    print(f'    Tasks:         10')
    print(f'    Comments:      7')
    print(f'    Notifications: 6')
    print('=' * 50)


if __name__ == '__main__':
    seed()
