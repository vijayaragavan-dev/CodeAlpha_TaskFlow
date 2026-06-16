# TaskFlow

**Manage projects efficiently with TaskFlow.**  

*Full-Stack Project Management System with Real-Time Collaboration*

[![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask)](https://flask.palletsprojects.com)
[![MySQL](https://img.shields.io/badge/MySQL-8+-orange?logo=mysql)](https://mysql.com)
[![SocketIO](https://img.shields.io/badge/SocketIO-5.3-white?logo=socket.io)](https://socket.io)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple?logo=bootstrap)](https://getbootstrap.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Build](https://img.shields.io/badge/Build-Passing-brightgreen?logo=githubactions)](.github/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/Tests-128%20passing-brightgreen)](tests/)
[![Code Style](https://img.shields.io/badge/Code%20Style-Black-black)](https://github.com/psf/black)

---

TaskFlow is a production-ready project management platform that enables teams to manage projects efficiently, track tasks via an interactive Kanban board, collaborate through comments, and receive real-time updates — all without page refreshes.

Built with Flask, MySQL, and WebSockets, it demonstrates full-stack development best practices: clean MVC architecture, defense-in-depth security, database optimization, comprehensive testing (128 tests), CI/CD, and production deployment readiness.

---

## Features

### Core
- **Authentication** — User registration with password strength validation, secure login with bcrypt, session management, remember me
- **Dashboard** — Real-time statistics, recent projects, notification widget with caching
- **Projects** — Create, edit, delete with owner-only controls
- **Tasks** — Full CRUD with priority (Low/Medium/High), status (To Do/In Progress/Completed), deadlines, and member assignment
- **Kanban Board** — Native HTML5 drag-and-drop, 3-column layout, real-time multi-user sync via WebSockets
- **Comments** — Threaded discussions with relative timestamps, HTML-sanitized storage
- **Notifications** — Auto-generated for task assignment, status changes, comments, member additions; read/unread tracking
- **Search & Filter** — Full-text search with filters by status, priority, assignee, deadline range; pagination

### Real-Time (WebSocket)
- Live Kanban updates — task moves reflected instantly for all project members
- Live comments — new comments appear without page refresh
- Live member events — member additions broadcast to the project room
- Auto-reconnect with exponential backoff

### Security
- **CSRF** protection on all POST endpoints (forms + AJAX)
- **SQL injection** prevention via parameterized queries
- **XSS** prevention via Jinja2 auto-escaping + `html.escape()`
- **Bcrypt** password hashing
- **Authorization** at route and model level (owner/member checks)
- **Secure cookies** (HttpOnly, SameSite=Lax, 8-hour session lifetime)
- **Error pages** without stack traces

### DevOps
- CI/CD pipeline with GitHub Actions (13 steps)
- Health check endpoint (`GET /health`)
- Metrics endpoint (`GET /metrics`)
- Structured logging with rotation (10MB, 5 backups)
- Automated database backup script
- Database reset + demo data seeding scripts
- gunicorn + gevent production deployment

---

## Screenshots

| Dashboard | Kanban Board |
|---|---|
| ![Dashboard](docs/screenshots/dashboard.png) | ![Kanban](docs/screenshots/kanban.png) |

| Project Detail | Task Detail |
|---|---|
| ![Projects](docs/screenshots/projects.png) | ![Tasks](docs/screenshots/tasks.png) |

| Notifications Center |
|---|
| ![Notifications](docs/screenshots/notifications.png) |

> *Screenshots are placeholders. Run the application to see the live UI.*

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.13, Flask 3.0 |
| **Database** | MySQL 8+ (mysql-connector-python, connection pooling) |
| **Real-Time** | Flask-SocketIO 5.3, gevent (WebSocket) |
| **Frontend** | Bootstrap 5.3, Bootstrap Icons, HTML5 Drag-and-Drop |
| **Authentication** | Flask-Login, Flask-Bcrypt |
| **Forms & Security** | Flask-WTF, WTForms, CSRF |
| **Deployment** | gunicorn, gevent, Render |
| **CI/CD** | GitHub Actions |
| **Code Quality** | Black, isort, flake8, pre-commit |

---

## Quick Start

### Prerequisites

- Python 3.13
- MySQL 8+
- pip

### Setup

```bash
# Clone and enter directory
cd TASKFLOW

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your MySQL credentials:
#   SECRET_KEY=your-secret-key
#   MYSQL_PASSWORD=your-mysql-password

# Initialize database
mysql -u root -p < database.sql

# (Optional) Seed demo data
python scripts/seed_demo_data.py

# Run application
python app.py
```

Open **http://localhost:5000** in your browser.

### Demo Credentials (after seeding)

| Role | Email | Password |
|---|---|---|
| Admin | `demo@taskflow.com` | `DemoPass123!` |
| Member | `member@taskflow.com` | `MemberPass123!` |

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|---|
| `SECRET_KEY` | **Yes** | — | Flask secret key (min 32 chars) |
| `FLASK_ENV` | No | `production` | `development`, `production`, or `testing` |
| `PORT` | No | `5000` | Server port (cloud platforms set this automatically) |
| `SESSION_COOKIE_SECURE` | No | `false` | Set `true` when using HTTPS |
| `MYSQL_HOST` | No | `localhost` | MySQL host |
| `MYSQL_PORT` | No | `3306` | MySQL port |
| `MYSQL_USER` | No | `root` | MySQL user |
| `MYSQL_PASSWORD` | **Yes** | — | MySQL password |
| `MYSQL_DB` | No | `taskflow` | Database name |
| `DB_POOL_NAME` | No | `taskflow_pool` | Connection pool name |
| `DB_POOL_SIZE` | No | `5` | Connection pool size |

---

## API Endpoints

| Method | Path | Description | Auth |
|---|---|---|---|
| `GET` | `/health` | Health check (DB, version, status) | No |
| `GET` | `/metrics` | Application metrics | No |
| `GET` | `/` | Landing page | No |
| `GET/POST` | `/auth/register` | User registration | No |
| `GET/POST` | `/auth/login` | User login | No |
| `GET` | `/auth/logout` | Logout | Yes |
| `GET` | `/auth/dashboard` | Dashboard with stats | Yes |
| `GET/POST` | `/projects/create` | Create project | Yes |
| `GET` | `/projects/<id>` | Project detail | Yes |
| `GET/POST` | `/projects/<id>/edit` | Edit project | Owner |
| `POST` | `/projects/<id>/delete` | Delete project | Owner |
| `GET` | `/projects/<id>/kanban` | Kanban board | Yes |
| `GET` | `/projects/<id>/members` | Manage members | Owner |
| `POST` | `/projects/<id>/members/add` | Add member | Owner |
| `POST` | `/projects/<id>/members/remove/<uid>` | Remove member | Owner |
| `GET/POST` | `/projects/<pid>/tasks/create` | Create task | Yes |
| `GET` | `/tasks/<tid>` | Task detail with comments | Yes |
| `GET/POST` | `/tasks/<tid>/edit` | Edit task | Yes |
| `POST` | `/tasks/<tid>/delete` | Delete task | Yes |
| `POST` | `/tasks/<tid>/move` | Move task (Kanban AJAX) | Yes |
| `POST` | `/tasks/<tid>/comments/add` | Add comment | Yes |
| `POST` | `/comments/<cid>/delete` | Delete comment | Yes |
| `GET` | `/tasks/search` | Search tasks | Yes |
| `GET` | `/notifications/` | Notification center | Yes |
| `POST` | `/notifications/<nid>/read` | Mark notification read | Yes |
| `POST` | `/notifications/read-all` | Mark all read | Yes |
| `POST` | `/notifications/<nid>/delete` | Delete notification | Yes |
| `GET` | `/notifications/unread-count` | Unread count (JSON API) | Yes |

---

## Project Structure

```
TASKFLOW/
├── app.py                    # Application factory, SocketIO, health/metrics
├── config.py                 # Configuration & environment variables
├── models.py                 # Database models, queries, connection pooling
├── forms.py                  # WTForm definitions
├── wsgi.py                   # Production WSGI entry point
├── database.sql              # Database schema (6 tables, 17 indexes)
├── VERSION                   # Application version
├── requirements.txt          # Python dependencies
├── Procfile                  # Render/gunicorn deployment
├── render.yaml               # Render manifest
├── runtime.txt               # Python version
├── pyproject.toml            # Black, isort, pytest config
├── .pre-commit-config.yaml   # Pre-commit hooks
├── .env.example              # Environment template
├── .gitignore
├── LICENSE                   # MIT License
├── README.md                 # This file
├── CHANGELOG.md              # Version history
├── CONTRIBUTING.md           # Contribution guide
├── PROJECT_INFO.md           # Project metadata
│
├── routes/                   # Flask blueprints
│   ├── auth.py               # Authentication routes
│   ├── projects.py           # Project CRUD, members
│   ├── tasks.py              # Task CRUD, comments, search, kanban move
│   ├── notifications.py      # Notification center routes
│   └── socket_events.py      # SocketIO event handlers
│
├── templates/                # Jinja2 templates (19 files)
│   ├── base.html             # Layout, navbar, sidebar, footer
│   ├── dashboard.html        # Dashboard with stats & notifications
│   ├── kanban.html           # Kanban board with drag-and-drop
│   ├── task_detail.html      # Task detail with comments
│   ├── notifications.html    # Notification center
│   ├── projects.html         # Project listing
│   ├── project_detail.html   # Project detail
│   ├── project_members.html  # Member management
│   ├── search_results.html   # Search & filter results
│   ├── login.html, register.html
│   ├── create_project.html, edit_project.html
│   ├── create_task.html, edit_task.html
│   └── 403.html, 404.html, 500.html, error.html
│
├── static/
│   ├── css/style.css         # Custom styles
│   └── js/
│       ├── main.js           # Auto-dismiss alerts
│       ├── kanban.js         # Drag-and-drop, AJAX
│       └── socket.js         # SocketIO client, real-time DOM updates
│
├── tests/                    # 128 tests (9 files)
│   ├── auth_test.py          # 11 tests
│   ├── project_test.py       # 7 tests
│   ├── task_test.py          # 10 tests
│   ├── kanban_test.py        # 10 tests
│   ├── comment_test.py       # 11 tests
│   ├── search_test.py        # 12 tests
│   ├── notification_test.py  # 16 tests
│   ├── socketio_test.py      # 16 tests
│   └── integration_test.py   # 35 tests
│
├── scripts/
│   ├── backup_db.py          # Database backup (mysqldump + Python)
│   ├── seed_demo_data.py     # Demo data seeder
│   └── reset_database.py     # Full database reset + seed
│
├── docs/
│   ├── screenshots/          # Screenshot placeholders
│   ├── resume_description.md
│   ├── linkedin_post.md
│   ├── interview_questions.md
│   ├── project_stats.md
│   └── codealpha_submission.md
│
├── logs/                     # Application logs (rotated)
├── backups/                  # Database dumps
└── .github/workflows/ci.yml  # CI/CD pipeline
```

---

## Deployment

TaskFlow supports multiple deployment platforms. The `render.yaml` file in the root provides automated Render configuration.

### Render (Recommended)

1. Push to GitHub
2. Create new **Web Service** on Render
3. Connect your repository
4. Render auto-detects `render.yaml` — or manually configure:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn --worker-class gevent --workers 1 --bind 0.0.0.0:$PORT wsgi:app`
   - **Health Check Path:** `/health`
5. Add environment variables (see `.env.example`):
   - `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DB` — for your Render MySQL database
   - `SECRET_KEY` — Render can auto-generate this
   - `SESSION_COOKIE_SECURE` — set to `true`
   - `FLASK_ENV` — set to `production`
6. Deploy

The included `render.yaml` pre-configures all settings. You only need to add the MySQL credentials via Render dashboard.

### Railway

1. Push to GitHub
2. Create new project on Railway
3. Connect repository
4. Add a **MySQL** database service via Railway dashboard
5. Set build command: `pip install -r requirements.txt`
6. Set start command: `gunicorn --worker-class gevent --workers 1 --bind 0.0.0.0:$PORT wsgi:app`
7. Add environment variables (Railway auto-injects `PORT`):
   - `SECRET_KEY` — generate a random key
   - `MYSQL_HOST` — from Railway MySQL service
   - `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DB` — from Railway MySQL
   - `SESSION_COOKIE_SECURE` — set to `true`
   - `FLASK_ENV` — set to `production`
8. Deploy

Railway automatically provides `PORT`. The app binds to `0.0.0.0:$PORT` at startup.

### Vercel (Static & API)

> **Note:** Vercel supports Flask via serverless functions (`@vercel/python`), but SocketIO real-time features will NOT work on Vercel's serverless infrastructure.

To deploy the app (without real-time features):

1. Push to GitHub
2. Import project on Vercel
3. Vercel auto-detects `vercel.json`
4. Add environment variables in Vercel dashboard
5. Deploy

The included `vercel.json` configures the Flask app as a serverless function and serves static files.

### Local Production

```bash
gunicorn --worker-class gevent --workers 1 --bind 0.0.0.0:8000 wsgi:app
```

### Docker (Manual)

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "--worker-class", "gevent", "--workers", "1", "--bind", "0.0.0.0:8000", "wsgi:app"]
```

---

## CI/CD Pipeline

The GitHub Actions pipeline (`.github/workflows/ci.yml`) runs on every push/PR to `main`:

1. Checkout code
2. Setup Python 3.13 with MySQL 8 service
3. Install dependencies
4. Syntax check (py_compile)
5. Lint with flake8
6. Format check with black
7. Run 8 unit test suites (auth, project, task, kanban, comment, search, notification, socketio)
8. Run integration tests
9. Verify app creation
10. Health endpoint verification
11. Deployment file validation

---

## Testing

```bash
# Run all test suites
python tests/auth_test.py
python tests/project_test.py
python tests/task_test.py
python tests/kanban_test.py
python tests/comment_test.py
python tests/search_test.py
python tests/notification_test.py
python tests/socketio_test.py
python tests/integration_test.py

# Run all tests with pytest
pytest tests/
```

**128 tests — all passing.**

---

## Database Backup

```bash
# Automated backup (uses mysqldump, falls back to Python)
python scripts/backup_db.py
```

Backup files stored in `backups/` with timestamped names: `taskflow_YYYYMMDD_HHMMSS.sql`

---

## Code Quality

```bash
# Install pre-commit hooks
pre-commit install

# Lint
flake8 .

# Format
black .

# Sort imports
isort .
```

---

## Monitoring

### Health Check
```bash
curl http://localhost:5000/health
```
```json
{"status": "healthy", "database": "connected", "version": "1.0.0", "timestamp": "..."}
```

### Metrics
```bash
curl http://localhost:5000/metrics
```
```json
{"version": "1.0.0", "request_count": 150, "error_count": 2, "avg_response_time_ms": 45.3, "active_users": 3, "database_pool_ok": true}
```

---

## Troubleshooting

| Issue | Solution |
|---|---|
| `SECRET_KEY not set` | Create `.env` with `SECRET_KEY=your-secret-key` |
| MySQL connection refused | Verify MySQL running and `.env` credentials correct |
| ModuleNotFoundError | Run `pip install -r requirements.txt` |
| Port in use | Change port or kill existing process |
| SocketIO not connecting | Ensure gevent monkey_patch is first import |
| Database table missing | Run `mysql -u root -p < database.sql` |
| Tests failing | Run `python scripts/reset_database.py` to reset |

---

## Future Improvements

- AI-powered task prioritization and assignment suggestions
- Email notification system (SMTP integration)
- Analytics dashboard with charts and reporting
- File attachments on tasks
- Dark mode theme toggle
- OAuth2 social login (Google, GitHub)
- Docker containerization
- Redis for distributed caching
- Mobile responsive PWA
- Internationalization (i18n)

---

## License

[MIT](LICENSE) &copy; 2026 TaskFlow

---

<div align="center">
  <sub>Built with ❤️ for CodeAlpha Internship Program</sub>
</div>
