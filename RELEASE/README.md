# TaskFlow v1.0.0 Release Package

**Manage projects efficiently with TaskFlow.**

This directory contains the official release package for TaskFlow v1.0.0.

## Contents

| File | Description |
|------|-------------|
| `README.md` | This file |
| `VERSION` | Version file (1.0.0) |
| `CHANGELOG.md` | Full version history |
| `LICENSE` | MIT License |
| `DEPLOYMENT_GUIDE.md` | Production deployment instructions |
| `RELEASE_NOTES.md` | Official release notes |

## Quick Start

```bash
# 1. Clone the repository
git clone <repo-url> TASKFLOW
cd TASKFLOW

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 5. Initialize database
mysql -u root -p < database.sql

# 6. (Optional) Seed demo data
python scripts/seed_demo_data.py

# 7. Run application
python app.py
```

## Documentation

- Full README: `/TASKFLOW/README.md`
- Security Audit: `/TASKFLOW/docs/final_security_audit.md`
- Performance Report: `/TASKFLOW/docs/final_performance_report.md`
- Accessibility Report: `/TASKFLOW/docs/accessibility_report.md`
- Production Certificate: `/TASKFLOW/docs/production_certificate.md`
