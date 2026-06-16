# TaskFlow Release Notes

## v1.0.0 — June 2026

*Manage projects efficiently with TaskFlow.*

---

### Features

#### Authentication & User Management
- User registration with password strength validation
- Secure login with bcrypt hashing and remember-me support
- Session management with 8-hour timeout

#### Dashboard
- Real-time project statistics with caching (30s TTL)
- Recent projects widget
- Recent notifications sidebar
- Optimized query (1 JOIN replaces 5 subqueries)

#### Project Management
- Create, edit, and delete projects
- Owner-only controls for destructive actions
- Member management (add/remove team members)

#### Task Management
- Full CRUD with priority (Low/Medium/High), status (To Do/In Progress/Completed)
- Member assignment with deadlines
- Rich task detail view with comments

#### Kanban Board
- Native HTML5 drag-and-drop (no external libraries)
- 3-column layout (To Do / In Progress / Completed)
- Real-time multi-user sync via WebSockets (SocketIO)
- AJAX status updates with optimistic UI

#### Comments & Collaboration
- Threaded discussions on tasks
- HTML-escaped content with relative timestamps
- Real-time comment updates via WebSockets

#### Notifications
- Auto-generated for task assignment, status changes, comments, member additions
- Read/unread tracking with badge counts
- Notification center with bulk mark-as-read
- Unread count API endpoint

#### Search & Filtering
- Full-text search across task titles and descriptions
- Filters by status, priority, assignee, and deadline range
- Pagination with LIMIT/OFFSET

#### Real-Time Collaboration (WebSocket)
- Live Kanban updates across project members
- Live comment and member events
- Auto-reconnect with exponential backoff (up to 20 retries)
- Room-based architecture (project_<id>, user_<id>)

#### Security
- CSRF protection on all POST endpoints (forms + AJAX)
- SQL injection prevention via 100% parameterized queries
- XSS prevention via Jinja2 auto-escaping + html.escape()
- Bcrypt password hashing
- Authorization at route and model level
- Secure cookies (HttpOnly, SameSite=Lax)
- Error pages without stack traces
- File upload validation (size + extension whitelist)

#### DevOps & Monitoring
- CI/CD pipeline with GitHub Actions (13 steps)
- Health check endpoint (GET /health)
- Metrics endpoint (GET /metrics)
- Structured logging with rotation (10MB, 5 backups)
- Automated database backup script (mysqldump + Python fallback)
- Database reset + demo data seeding scripts
- gunicorn + gevent production deployment
- Render deployment manifest

#### Developer Experience
- 128 passing tests across 9 test suites
- Pre-commit hooks (black, isort, flake8)
- Comprehensive documentation (README, CONTRIBUTING, CHANGELOG)
- MIT License
- PWA support (manifest.json, service-worker.js)

---

### Bug Fixes

- Fixed `markupsafe.escape()` returning `Markup` object instead of string for DB storage
- Fixed `SECRET_KEY` fallback — now raises `RuntimeError` instead of using default
- Fixed MySQL BOOLEAN type mismatch (TINYINT(1) returns int, not bool)
- Fixed SocketIO eventlet incompatibility with Python 3.13 on Windows (switched to gevent)
- Fixed `gevent.monkey.patch_all()` import order (must be before all other imports)
- Fixed dashboard stats query from 5 subqueries to single optimized JOIN
- Fixed `get_user_projects` from correlated subquery to LEFT JOIN + GROUP BY
- Fixed log rotation from 1MB to 10MB with 5 backups
- Fixed session simulation in tests (session_transaction + manual user_id)

---

### Known Limitations

- No email notification system (SMTP not configured)
- No file attachments on tasks
- No dark mode theme toggle
- No OAuth2 social login
- No Docker containerization
- No Redis distributed caching
- Single-server WebSocket (not horizontally scalable without sticky sessions)
- `cors_allowed_origins='*'` — should be restricted in production
- In-memory cache (lost on process restart)
- No per-IP rate limiting

---

### Future Roadmap

#### v1.1.0 (Next Release)
- Email notification system (SMTP integration)
- File attachments on tasks with preview
- Dark mode theme toggle with persistent preference

#### v1.2.0
- Analytics dashboard with charts (Chart.js)
- OAuth2 social login (Google, GitHub)
- Docker containerization with docker-compose

#### v2.0.0
- Redis for distributed caching and session storage
- Mobile responsive PWA with offline support
- Internationalization (i18n) for multiple languages
- AI-powered task prioritization suggestions

---

### Contributors

- TaskFlow Development Team
- CodeAlpha Internship Program

---

### Feedback & Support

- Report issues: https://github.com/anomalyco/opencode/issues
- Documentation: https://opencode.ai
- License: MIT
