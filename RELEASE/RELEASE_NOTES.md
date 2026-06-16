# TaskFlow v1.0.0 Release Notes

**Release Date:** June 16, 2026  
**Status:** Production Ready  

---

## Overview

TaskFlow is a full-stack project management platform with real-time collaboration. This is the initial production release.

---

## What's New

### Authentication & Security
- User registration with bcrypt password hashing
- CSRF protection on all POST endpoints
- SQL injection prevention via parameterized queries
- XSS prevention via Jinja2 auto-escaping
- Session management with 8-hour timeout

### Project Management
- Create, edit, delete projects with owner-only controls
- Team member management (add/remove)
- Dashboard with real-time statistics and caching

### Task Management
- Full CRUD with priority, status, and deadlines
- Member assignment with notifications
- Kanban board with native HTML5 drag-and-drop
- Real-time multi-user sync via WebSockets

### Collaboration
- Task comments with HTML sanitization
- Auto-generated notifications for assignments, status changes, and comments
- Notification center with read/unread tracking

### Search & Filtering
- Full-text search across task titles and descriptions
- Filter by status, priority, assignee, and deadline
- Pagination for large result sets

### Real-Time Features (WebSocket)
- Live kanban updates for all project members
- Live comments and member events
- Auto-reconnect with exponential backoff
- Room-based architecture for scalable multi-project support

### DevOps & Monitoring
- CI/CD pipeline with GitHub Actions (13 steps)
- Health check and metrics endpoints
- Structured logging with rotation
- Automated database backup script
- Database reset and demo data seeding

### PWA & Accessibility
- Service worker for offline support
- Web app manifest for installable PWA
- WCAG 2.1 AA accessibility compliance
- Skip-to-content, ARIA attributes, keyboard navigation

---

## Features at a Glance

| Category | Count |
|----------|-------|
| Flask Routes | 30 |
| Database Tables | 6 |
| Database Indexes | 13 |
| Jinja2 Templates | 20 |
| SocketIO Events | 9 |
| Total Tests | 142 |
| Test Pass Rate | 100% |

---

## Bug Fixes

- Fixed `get_user_projects()` to include member projects (not just owned)
- Fixed `get_dashboard_stats()` to include member project data
- Fixed inconsistent indentation in health endpoint JSON building
- Removed unused `sys` and `timedelta` imports from app.py

---

## Known Limitations

- No email notification system
- No file attachments on tasks
- No dark mode toggle
- No OAuth2 social login
- Single-server WebSocket (requires sticky sessions for horizontal scaling)
- In-memory cache (lost on restart)

---

## Future Roadmap

| Version | Features |
|---------|----------|
| v1.1.0 | Email notifications, file attachments, dark mode |
| v1.2.0 | Analytics dashboard, OAuth2 login, Docker |
| v2.0.0 | Redis caching, PWA offline, i18n, AI prioritization |

---

## Installation

```bash
git clone <repo-url>
cd TASKFLOW
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
# Edit .env with MySQL credentials
mysql -u root -p < database.sql
python app.py
```

---

## License

MIT License — see LICENSE file for details.
