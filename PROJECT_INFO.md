# TaskFlow - Project Information

## Metadata

| Field | Value |
|---|---|
| **Project Name** | TaskFlow |
| **Version** | 1.0.0 |
| **Author** | [Your Name] |
| **Status** | Production Ready |
| **License** | MIT |
| **Repository** | [GitHub URL] |

## Technology Stack

| Layer | Technology |
|---|---|
| Backend Framework | Flask 3.0 (Python 3.13) |
| Database | MySQL 8+ |
| Real-Time | Flask-SocketIO 5.3 + gevent |
| Frontend | Bootstrap 5.3, Bootstrap Icons |
| Authentication | Flask-Login, Flask-Bcrypt |
| Forms & CSRF | Flask-WTF, WTForms |
| Deployment | gunicorn, Render |
| CI/CD | GitHub Actions |
| Code Quality | Black, isort, flake8, pre-commit |

## Features Summary

| Category | Features |
|---|---|
| Auth | Register, Login, Logout, Remember Me, Password Strength |
| Projects | Create, Edit, Delete, Member Management |
| Tasks | CRUD, Assignment, Priority, Status, Deadlines |
| Kanban | 3-Column Board, Drag-and-Drop, Real-Time Sync |
| Comments | Threaded Discussions, Relative Timestamps |
| Notifications | Auto-generated, Read/Unread, Center UI |
| Search | Full-Text, Filters, Pagination |
| Real-Time | WebSocket, Live Updates, Auto-Reconnect |
| Security | CSRF, SQL Injection Prevention, XSS, Authorization |
| Monitoring | Health Check, Metrics, Log Rotation, Backup |

## Database Schema

6 tables: `users`, `projects`, `project_members`, `tasks`, `comments`, `notifications`
17 indexes including composite indexes for query optimization.

## Test Coverage

128 tests across 9 suites — all passing.

## Deployment Platforms

- Render (primary)
- Railway (compatible)
- Local/self-hosted

## Project Structure

```
TASKFLOW/
├── app.py, config.py, models.py, forms.py, wsgi.py
├── routes/          # 5 route modules
├── templates/       # 19 Jinja2 templates
├── static/          # CSS + 3 JS files
├── tests/           # 9 test files
├── scripts/         # Backup, seed, reset
├── docs/            # Documentation
├── logs/            # Application logs
├── backups/         # Database dumps
└── .github/         # CI/CD pipeline
```
