# TaskFlow Deployment Guide

**Version:** 1.0.0  
**Updated:** June 2026  

---

## Prerequisites

- Python 3.13+
- MySQL 8.0+
- pip
- Git

---

## Local Development Deployment

### Step 1: Clone & Setup

```bash
git clone <repository-url> TASKFLOW
cd TASKFLOW
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### Step 2: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your MySQL credentials:
```
SECRET_KEY=your-strong-secret-key-min-32-chars
MYSQL_PASSWORD=your-mysql-password
```

### Step 3: Initialize Database

```bash
mysql -u root -p < database.sql
```

### Step 4: (Optional) Seed Demo Data

```bash
python scripts/seed_demo_data.py
```

### Step 5: Run Application

```bash
python app.py
```

Open http://localhost:5000

---

## Production Deployment (Render)

### Step 1: Push to GitHub

```bash
git add .
git commit -m "TaskFlow v1.0.0"
git push origin main
```

### Step 2: Create Render Web Service

1. Go to [render.com](https://render.com) → Dashboard → New Web Service
2. Connect your GitHub repository
3. Configure:

| Setting | Value |
|---------|-------|
| **Name** | taskflow |
| **Environment** | Python |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn --worker-class gevent --workers 1 --bind 0.0.0.0:$PORT wsgi:app` |
| **Plan** | Starter (free) or Professional |

### Step 3: Environment Variables

Add these in Render Dashboard → Environment:

| Key | Value |
|-----|-------|
| `SECRET_KEY` | Auto-generated (or set your own) |
| `MYSQL_HOST` | Your MySQL host (e.g., from Aiven, Clever Cloud) |
| `MYSQL_PORT` | 3306 |
| `MYSQL_USER` | Your MySQL user |
| `MYSQL_PASSWORD` | Your MySQL password |
| `MYSQL_DB` | taskflow |

### Step 4: Deploy

Render will automatically build and deploy. Monitor logs for any issues.

---

## Production Deployment (Railway)

### Step 1: Connect Repository

1. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub repo
2. Select your TaskFlow repository

### Step 2: Configure

Railway auto-detects Python. Set start command:
```
gunicorn --worker-class gevent --workers 1 --bind 0.0.0.0:$PORT wsgi:app
```

### Step 3: Add MySQL Plugin

In Railway dashboard:
- Add a MySQL database plugin
- Railway provides connection details as environment variables

### Step 4: Environment Variables

Set these in Railway dashboard:
```
SECRET_KEY=your-secret-key
MYSQL_HOST=<from-railway-mysql-plugin>
MYSQL_PORT=3306
MYSQL_USER=<from-railway-mysql-plugin>
MYSQL_PASSWORD=<from-railway-mysql-plugin>
MYSQL_DB=taskflow
```

---

## Production Deployment (VPS)

### Step 1: Server Setup

```bash
# Install Python 3.13, MySQL 8, nginx
sudo apt update
sudo apt install python3.13 python3.13-venv mysql-server nginx
```

### Step 2: Deploy Application

```bash
git clone <repository-url> /var/www/taskflow
cd /var/www/taskflow
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with production credentials
mysql -u root -p < database.sql
```

### Step 3: Configure Systemd Service

Create `/etc/systemd/system/taskflow.service`:

```ini
[Unit]
Description=TaskFlow Application
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/taskflow
Environment=PATH=/var/www/taskflow/venv/bin
ExecStart=/var/www/taskflow/venv/bin/gunicorn --worker-class gevent --workers 1 --bind 127.0.0.1:8000 wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable taskflow
sudo systemctl start taskflow
```

### Step 4: Configure Nginx

Create `/etc/nginx/sites-available/taskflow`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /static/ {
        alias /var/www/taskflow/static/;
        expires 30d;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/taskflow /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Post-Deployment Verification

```bash
# Health check
curl http://your-domain.com/health

# Metrics
curl http://your-domain.com/metrics

# Application loads
curl http://your-domain.com/
```

Expected health response:
```json
{"status": "healthy", "database": "connected", "version": "1.0.0", "tagline": "Manage projects efficiently with TaskFlow.", "timestamp": "..."}
```

---

## Database Backups

```bash
# Automated backup
python scripts/backup_db.py
```

Backups stored in `backups/` directory with timestamped filenames.

---

## Monitoring

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check with DB status |
| `GET /metrics` | App metrics (requests, errors, response time, active users) |

Logs are stored in `logs/` directory with rotation:
- app.log (10MB, 5 backups)
- auth.log, project.log, task.log
- socketio.log, notification.log
- database.log, backup.log

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| SECRET_KEY not set | Create `.env` with `SECRET_KEY=your-key` |
| MySQL connection refused | Verify MySQL is running and credentials are correct |
| Module not found | Run `pip install -r requirements.txt` |
| Port in use | Change port or kill existing process |
| SocketIO not connecting | Ensure gevent monkey_patch is first import |
| Missing tables | Run `mysql -u root -p < database.sql` |
| Tests failing | Run `python scripts/reset_database.py` to reset DB |

---

## Support

For issues and feature requests, please use the GitHub issue tracker.
