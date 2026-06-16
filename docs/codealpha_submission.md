# TaskFlow - CodeAlpha Internship Submission

## Project Summary

TaskFlow is a full-stack project management system built with Flask and MySQL, featuring real-time collaboration via WebSockets. It enables teams to manage projects, track tasks with a Kanban board, collaborate through comments, and receive instant notifications — all updated in real-time without page refreshes.

## Features

- **Authentication**: Secure registration/login with bcrypt password hashing, session management, remember me
- **Dashboard**: Real-time statistics, recent projects, notification widget
- **Projects**: Create, edit, delete projects with member management
- **Tasks**: Full CRUD with priority, status, deadlines, and assignment
- **Kanban Board**: Drag-and-drop interface with real-time multi-user sync
- **Comments**: Threaded discussions on tasks with relative timestamps
- **Notifications**: Automatic alerts for assignments, status changes, comments, member additions
- **Search**: Advanced filtering by status, priority, assignee, deadlines with pagination
- **Real-Time**: WebSocket-powered live updates for Kanban, comments, and member lists
- **Security**: CSRF protection, SQL injection prevention, XSS sanitization, role-based access

## Technology Stack

| Component | Technology |
|---|---|
| Backend | Python 3.13, Flask 3.0 |
| Database | MySQL 8+ |
| Real-Time | Flask-SocketIO, gevent |
| Frontend | Bootstrap 5.3, Bootstrap Icons |
| Auth | Flask-Login, Flask-Bcrypt |
| Forms | Flask-WTF, WTForms |
| Deployment | gunicorn, Render |
| CI/CD | GitHub Actions |

## How to Run

### Prerequisites
- Python 3.13
- MySQL 8+
- pip

### Steps

```bash
# 1. Clone the repository
git clone <repository-url>
cd TASKFLOW

# 2. Set up virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your MySQL credentials

# 5. Initialize database
mysql -u root -p < database.sql

# 6. (Optional) Seed demo data
python scripts/seed_demo_data.py

# 7. Run the application
python app.py
```

Visit **http://localhost:5000**

### Demo Credentials (after seeding)

- **Email**: demo@taskflow.com
- **Password**: DemoPass123!

## GitHub Repository

[Link to GitHub Repository]

## Demo Video

[Link to Demo Video]

## Project Structure

```
TASKFLOW/
├── app.py                  # Application factory & SocketIO
├── config.py               # Configuration & environment
├── models.py               # Database models & queries
├── forms.py                # WTForm definitions
├── wsgi.py                 # Production entry point
├── database.sql            # Schema
├── requirements.txt
├── Procfile / render.yaml  # Deployment
├── VERSION
├── routes/                 # Blueprints
│   ├── auth.py
│   ├── projects.py
│   ├── tasks.py
│   ├── notifications.py
│   └── socket_events.py
├── templates/              # 19 Jinja2 templates
├── static/                 # CSS, JS
├── tests/                  # 128 tests (9 files)
├── scripts/                # Backup, seed, reset
├── docs/                   # Documentation
└── logs/                   # Application logs
```

## Test Results

All **128 tests** pass across 9 test suites covering authentication, projects, tasks, Kanban, comments, search, notifications, SocketIO, and full integration.

## Contact

[Your Name]
[Your Email]
[LinkedIn Profile]
