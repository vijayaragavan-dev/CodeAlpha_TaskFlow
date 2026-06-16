# Changelog

## v1.0.0 (2026-06-16)

### Phase 13 — SaaS Packaging, Release & Professional Launch
- Application branding: consistent tagline, navbar, footer, browser titles across all pages
- SEO meta tags: description, keywords, author, robots, theme-color
- OpenGraph tags (og:title, og:description, og:image, og:type, og:url, og:site_name)
- Twitter Card tags (summary_large_image, title, description, image)
- Favicon (SVG + ICO) and apple-touch-icon
- PWA support: manifest.json (name, icons, theme_color, display) + service-worker.js (offline caching)
- Enhanced error pages (403, 404, 500, error.html) with branded UI, dual navigation buttons
- Accessibility: skip-to-main link, ARIA attributes, aria-label, aria-current, role attributes
- Keyboard navigation: focus-visible styles, visually-hidden-focusable
- prefers-reduced-motion media query for accessibility
- Responsive design audit with mobile breakpoints (575px)
- CSS optimization: removed unused `.error-card` hover, added reduced-motion, focus styles, mobile error card sizing
- Added docs/security_audit.md (full security audit across 10 categories, 40+ checks)
- Added docs/performance_report.md (benchmark across 6 areas, optimization details)
- Added RELEASE_NOTES.md (features, bug fixes, known limitations, roadmap)
- Added docs/project_certificate.md (certification with 60/60 feature inventory, test results, deployment status)
- Service worker registration in base template
- Tagline exposed in /health endpoint JSON response
- Tagline available in all templates via context processor

### Phase 12 — Portfolio & Documentation
- Added LICENSE (MIT)
- Added CONTRIBUTING.md with guidelines
- Added CHANGELOG.md
- Added PROJECT_INFO.md with metadata
- Added docs/screenshots/ directory
- Added docs/resume_description.md
- Added docs/linkedin_post.md
- Added docs/interview_questions.md (30 Q&A)
- Added docs/project_stats.md
- Added docs/codealpha_submission.md
- Added scripts/seed_demo_data.py
- Added scripts/reset_database.py
- Updated README.md with badges, screenshots, full documentation

### Phase 11 — CI/CD, Monitoring & Maintenance
- Added GitHub Actions CI/CD pipeline
- Added health check endpoint (GET /health)
- Added metrics endpoint (GET /metrics)
- Added VERSION file (v1.0.0)
- Added pyproject.toml (black, isort, pytest config)
- Added .pre-commit-config.yaml
- Added scripts/backup_db.py
- Updated log rotation to 10MB
- Updated requirements.txt with dev dependencies
- Updated README.md with production docs

### Phase 10 — Real-Time SocketIO
- Integrated Flask-SocketIO with gevent
- Added routes/socket_events.py (connection, room management)
- Added static/js/socket.js (client-side handlers)
- Live Kanban updates (task_moved event)
- Live comments (comment_added event)
- Live member events (member_added event)
- Auto-reconnect with exponential backoff
- Room-based authorization (project_<id> rooms)
- Bootstrap toast notifications for real-time events

### Phase 9 — Notifications & Activity
- Added notification model functions
- Added routes/notifications.py (list, read, read-all, delete, unread-count)
- Added templates/notifications.html (notification center)
- Auto-generated notifications for task assignment, status changes, comments, member additions
- Notification badge in navbar with unread count
- Recent notifications widget on dashboard
- Notification logging

### Phase 8 — Security Hardening & Performance
- config.py: SECRET_KEY required, secure session cookies, CSRF timeout
- Optimized dashboard query (single JOIN vs 5 subqueries)
- Optimized get_user_projects (LEFT JOIN + GROUP BY)
- In-memory caching for dashboard stats (30s TTL)
- Dedicated error templates (403, 404, 500)
- Deployment files: Procfile, runtime.txt, render.yaml

### Phase 7 — Notification Database Schema
- Added notifications table with indexes
- Database optimization

### Phase 6 — Comments & Search
- Comment CRUD with HTML escaping
- Full-text search with LIKE
- Filters: status, priority, assigned, deadline
- Pagination with LIMIT/OFFSET
- Dynamic WHERE builder in search_tasks()

### Phase 5 — Kanban Board
- Native HTML5 Drag-and-Drop API
- 3-column layout (To Do / In Progress / Completed)
- AJAX status updates via fetch()
- Bootstrap Toasts for feedback
- CSRF via X-CSRFToken header

### Phase 4 — Members & Tasks
- Add/remove project members
- Task CRUD with priority, status, deadline
- Task assignment to members

### Phase 3 — Dashboard & Projects
- Project CRUD operations
- Dashboard with statistics
- Dark-blue Bootstrap theme

### Phase 2 — Authentication
- User registration with password strength validation
- Secure login with bcrypt
- Session management via Flask-Login
- Remember Me functionality

### Phase 0-1 — Project Setup & Database
- Flask project structure with app factory
- MySQL database with 6 tables
- Foreign keys and indexes
