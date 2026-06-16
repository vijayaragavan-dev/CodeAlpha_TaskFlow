# TaskFlow - Top 30 Interview Questions & Answers

## Architecture & Design

### 1. Explain the overall architecture of TaskFlow.

TaskFlow follows the MVC (Model-View-Controller) pattern using Flask's app factory. The `app.py` creates the Flask application, `models.py` handles all database interactions, `routes/` contain blueprint-based controllers, and `templates/` are Jinja2 views. SocketIO is initialized alongside Flask for real-time features. The database layer uses connection pooling for MySQL with parameterized queries.

### 2. Why did you choose Flask over Django?

Flask was chosen for its lightweight, flexible nature — perfect for a project where we wanted full control over the architecture without Django's heavy ORM and admin overhead. Flask's blueprint system allows clean route organization, and the extensive ecosystem (Flask-Login, Flask-SocketIO, Flask-WTF) provides exactly what we need without bloat.

### 3. How does the app factory pattern work?

`create_app()` in `app.py` accepts a Config class, initializes extensions (bcrypt, login_manager, csrf, socketio), sets up logging, registers blueprints, configures error handlers, and returns the Flask instance. This pattern allows multiple app instances (e.g., for testing with different configs) and clean separation of concerns.

### 4. How are blueprints organized?

Four blueprints: `auth` (authentication routes at `/auth`), `projects` (project CRUD at `/projects`), `tasks` (task operations, comments, search, kanban moves), and `notifications` (notification center at `/notifications`). Each blueprint has its own URL prefix and logger.

## Database

### 5. How does connection pooling work?

MySQL connection pooling via `mysql.connector.pooling` creates a pool of 5 reusable connections. `get_db_connection()` acquires from the pool, and `close_connection()` returns it. This avoids the overhead of creating new connections per request. Pool size is configurable via `DB_POOL_SIZE` environment variable.

### 6. How do you prevent SQL injection?

All queries use parameterized placeholders (`%s`) with separate parameters tuple. Never use f-strings or string concatenation for SQL. Even dynamic query building (e.g., `search_tasks()`) builds the WHERE clause with `%s` placeholders and appends parameters separately.

### 7. What indexes are optimized for performance?

Composite indexes: `idx_tasks_status_project (status, project_id)` for Kanban queries. Single-column indexes on foreign keys (`project_id`, `assigned_to`, `user_id`), status, priority, deadline, and notification fields (`user_id`, `is_read`, `created_at`).

## Authentication & Security

### 8. How does authentication work?

Flask-Login manages user sessions. On login, bcrypt verifies the password hash, Flask-Login creates a session, and the `user_loader` callback loads the User object from the database on each request. "Remember Me" uses a separate cookie with 30-day duration.

### 9. How is CSRF protected?

Flask-WTF generates a unique CSRF token per session. All POST forms include `{{ csrf_token() }}`. AJAX requests (Kanban moves) read the token from a `<meta>` tag and send it via `X-CSRFToken` header. Server validates on every POST.

### 10. How is XSS prevented?

Jinja2 auto-escapes all `{{ }}` expressions. For dynamic content like comments, `html.escape()` is applied before database storage as a defense-in-depth measure. The `|safe` filter is only used for trusted content like the CSRF token.

### 11. How is authorization enforced?

Two layers: route-level (e.g., `@login_required`, `is_project_owner()` checks) and model-level (queries include `WHERE user_id=%s` to ensure users only access their data). Unauthorized access returns 403.

## Real-Time (SocketIO)

### 12. How does real-time collaboration work?

Flask-SocketIO with gevent async mode. On connect, users join personal rooms (`user_<id>`). On visiting a project page, they join `project_<id>` rooms via `join_project` SocketIO event. Server emits `task_moved`, `comment_added`, `member_added` to project rooms. Clients update DOM without page refresh.

### 13. How do you prevent unauthorized SocketIO events?

The `join_project` handler validates project membership using `is_project_member()` before allowing room joins. The `connect` handler rejects unauthenticated users. All route-based emits happen within authenticated route handlers.

### 14. How does auto-reconnect work?

SocketIO client configures reconnection with exponential backoff: initial delay 1s, max delay 30s, randomization factor 0.5, max 20 attempts. On reconnect, the client re-joins project rooms automatically.

## Features

### 15. How does the Kanban board work?

Three-column layout (To Do / In Progress / Completed) using native HTML5 Drag and Drop API. `dragstart` captures the task element, `dragover`/`drop` on column bodies handle the move. On drop, an AJAX POST to `/tasks/<id>/move` updates the database, and the server emits `task_moved` via SocketIO to all room members for real-time sync.

### 16. How does the notification system work?

Automatic generation on key events: task assignment, status changes, comments on assigned tasks, member additions. `create_notification()` inserts into the `notifications` table. The notification center displays them with read/unread state. Unread count badge in navbar is updated via context processor and AJAX polling.

### 17. How does search work?

`search_tasks()` builds a dynamic WHERE clause based on user-provided filters (query text, status, priority, assigned user, deadline range). Uses LIKE for text search, LIMIT/OFFSET for pagination. Results are scoped to the user's projects via `get_user_project_ids()`.

### 18. How is the dashboard optimized?

Dashboard stats use a single optimized query with `COUNT(DISTINCT)`, `SUM(CASE...)` patterns instead of 5 separate queries. Results are cached in-memory with 30-second TTL via `cache_get()`/`cache_set()`.

## Performance

### 19. How do you handle database performance?

Connection pooling (5 connections), composite indexes for frequent query patterns, optimized dashboard query (single JOIN instead of 5 subqueries), LIMIT on all list queries, and in-memory caching for expensive dashboard stats.

### 20. How many concurrent users can TaskFlow handle?

With connection pooling (5 connections), gevent async workers, and in-memory caching, TaskFlow can handle 50-100 concurrent users comfortably. For higher loads, increasing pool size, adding more gunicorn workers, and implementing Redis caching would scale further.

## Testing

### 21. How many tests does TaskFlow have?

128 tests across 9 test files: auth (11), project (7), task (10), kanban (10), comment (11), search (12), notification (16), socketio (16), integration (35). All pass with PASS/FAIL output.

### 22. How do tests handle database isolation?

Tests clean up data before and after execution using `execute_query('DELETE FROM ... WHERE email=%s', ...)`. Session simulation uses `client.session_transaction()` to set `_user_id` and `user_id` directly.

## Deployment

### 23. How is TaskFlow deployed?

gunicorn with gevent worker class, serving the Flask app via `wsgi.py`. Render deployment uses the `render.yaml` manifest. Health and metrics endpoints allow monitoring. Log rotation at 10MB prevents disk exhaustion.

### 24. What environment variables are required?

`SECRET_KEY` is required (RuntimeError if missing). Optional: `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DB`, `DB_POOL_NAME`, `DB_POOL_SIZE`.

## Security

### 25. How are passwords stored?

Bcrypt with Flask-Bcrypt. `generate_password_hash()` creates a salted hash, stored in the `password` column. On login, `check_password_hash()` compares. Never store plaintext or use weak hashes like MD5/SHA1.

### 26. How are session cookies configured?

HttpOnly (prevents JavaScript access), SameSite=Lax (CSRF protection), 8-hour lifetime. Remember Me cookie: HttpOnly, 30-day duration, SameSite=Lax. Secure flag is configurable (False in dev, True in production with HTTPS).

## Code Quality

### 27. What code quality tools are used?

Flake8 for linting, Black for formatting (line length 88), isort for import sorting, pre-commit hooks for automated checks. CI pipeline enforces these on every push.

### 28. How is logging structured?

Per-module loggers with `RotatingFileHandler` (10MB, 5 backups). Separate log files: app.log, database.log, auth.log, project.log, task.log, notification.log, socketio.log, backup.log. Each includes timestamp, level, module name, and message.

## General

### 29. What would you improve in TaskFlow?

AI-powered task prioritization, email notification system, analytics dashboard with charts, mobile responsive enhancements, Docker containerization, Redis for distributed caching, Kubernetes for orchestration, and OAuth2 social login.

### 30. Why is TaskFlow a good portfolio project?

It demonstrates full-stack development (frontend, backend, database), real-time systems (WebSockets), security (auth, CSRF, XSS, SQL injection), performance optimization (caching, indexing, connection pooling), testing (128 tests), DevOps (CI/CD, deployment, monitoring), and clean architecture (MVC, app factory, blueprints) — all skills employers actively seek.
