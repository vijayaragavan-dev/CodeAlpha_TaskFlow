# 🚀 TaskFlow

<div align="center">

### Enterprise-Grade Project Management Platform

**A production-ready Trello/Asana-inspired project management system built with Flask, MySQL, and real-time WebSockets.**

[![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python\&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask)](https://flask.palletsprojects.com)
[![MySQL](https://img.shields.io/badge/MySQL-8+-orange?logo=mysql)](https://mysql.com)
[![Socket.IO](https://img.shields.io/badge/Socket.IO-5.3-white?logo=socket.io)](https://socket.io)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple?logo=bootstrap)](https://getbootstrap.com)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-success)](.github/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/Tests-137%20Passing-brightgreen)](tests/)
[![Security](https://img.shields.io/badge/Security-Hardened-success)](#security)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

</div>

---

## 🌟 Overview

TaskFlow is an **enterprise-grade project management platform** inspired by **Trello** and **Asana**, designed for efficient team collaboration, task tracking, and project organization.

Built using **Flask**, **MySQL**, and **WebSockets**, TaskFlow demonstrates modern software engineering practices including:

* Full-Stack Web Development
* Real-Time Collaboration
* Secure Authentication & Authorization
* Database Optimization
* CI/CD Automation
* Production Deployment
* Performance Engineering
* Scalable Architecture

The application enables teams to create projects, manage tasks using a Kanban board, collaborate through comments, and receive live updates in real time.

---

# 🔗 Live Demo

🌐 **Production Deployment:**

```text
https://taskflow-lz6r.onrender.com
```

> **Note:** The application is deployed on Render Free Tier. The first request after inactivity may take 20–60 seconds due to cold start behavior.

---

# ✨ Key Highlights

✅ Enterprise-grade architecture
✅ Real-time WebSocket communication
✅ Kanban-based task management
✅ Secure authentication system
✅ Role-based access control
✅ Database connection pooling
✅ Production-ready deployment
✅ CI/CD with GitHub Actions
✅ Automated testing suite
✅ Security hardening and rate limiting

---

# 🏗️ System Architecture

```text
                    ┌───────────────────┐
                    │   Client Browser  │
                    │ (Chrome/Firefox)  │
                    └─────────┬─────────┘
                              │ HTTPS
                              ▼
               ┌────────────────────────────┐
               │ Render Cloud Deployment    │
               │ Flask + Gunicorn + Gevent  │
               └─────────┬──────────────────┘
                         │
                         │ MySQL Connector
                         ▼
             ┌─────────────────────────────┐
             │ Railway MySQL Database      │
             │ Connection Pooling Enabled  │
             └─────────────────────────────┘
```

---

# 🧠 Core Features

## 🔐 Authentication & Security

* User Registration
* User Login & Logout
* Secure Session Management
* Password Hashing using Bcrypt
* Strong Password Validation
* CSRF Protection
* Secure Cookies
* Route-Level Authorization
* Role-Based Access Control
* Rate Limiting Protection

---

## 📊 Dashboard

Interactive dashboard displaying:

* Total Projects
* Total Tasks
* Completed Tasks
* Pending Tasks
* Tasks Due Today
* Recent Activities
* Notification Widget

---

## 📁 Project Management

Users can:

* Create Projects
* Edit Projects
* Delete Projects
* View Project Details
* Manage Team Members

Only project owners can modify project settings.

---

## 👥 Team Collaboration

Features include:

* Add Members to Projects
* Remove Members
* View Member List
* Prevent Duplicate Memberships
* Team-Based Collaboration

---

## ✅ Task Management

Task capabilities:

* Create Tasks
* Edit Tasks
* Delete Tasks
* Assign Tasks
* Set Deadlines
* Update Status
* Configure Priority Levels

### Priority Levels

```text
Low
Medium
High
```

### Task Status

```text
To Do
In Progress
Completed
```

---

## 📌 Kanban Board

TaskFlow provides a Trello-style Kanban board featuring:

* Drag and Drop Support
* AJAX Updates
* Persistent Database Sync
* Real-Time Task Movement
* Multi-User Collaboration

---

## 💬 Comment System

Each task supports collaborative discussions:

* Add Comments
* Delete Own Comments
* Timestamp Tracking
* User Attribution
* Live Comment Updates

---

## 🔔 Notification System

Users receive notifications for:

* Task Assignment
* Status Changes
* New Comments
* Member Additions
* Project Updates

Notification states:

```text
Read
Unread
```

---

## 🔎 Search & Filter

Powerful search capabilities:

* Search by Title
* Filter by Priority
* Filter by Status
* Filter by Assigned User
* Deadline Filtering
* Pagination Support

---

## ⚡ Real-Time Features

Powered by **Flask-SocketIO**:

* Live Kanban Updates
* Real-Time Comments
* Notification Broadcasting
* Member Activity Events
* Automatic Reconnection

---

# 🛡️ Security Features

TaskFlow implements defense-in-depth security:

### Authentication

* Flask-Login
* Bcrypt Password Hashing
* Session Expiration
* Remember Me Support

### Input Protection

* CSRF Protection
* SQL Injection Prevention
* XSS Protection
* HTML Escaping
* Input Validation

### Session Security

* HttpOnly Cookies
* SameSite Cookies
* Secure Cookies (HTTPS)
* Configurable Session Lifetime

### Rate Limiting

Protection against:

* Brute Force Login Attacks
* API Abuse
* Spam Requests

---

# ⚡ Performance Optimizations

TaskFlow is optimized for production workloads.

Implemented optimizations:

* MySQL Connection Pooling
* Database Pool Recycling
* Query Optimization
* Indexed Database Queries
* Browser Caching
* Gunicorn Worker Optimization
* Gevent Asynchronous Workers
* Efficient Dashboard Queries
* Static Asset Optimization
* Response Compression

---

# 🗄️ Database Design

Database: **MySQL 8+**

## Tables

| Table           | Description        |
| --------------- | ------------------ |
| users           | User accounts      |
| projects        | Project records    |
| project_members | Project membership |
| tasks           | Task management    |
| comments        | Task discussions   |
| notifications   | User notifications |

### Database Features

✅ Foreign Keys
✅ Cascading Deletes
✅ Query Indexing
✅ Connection Pooling
✅ Optimized Relationships
✅ Data Integrity Constraints

---

# 🧪 Testing & Quality Assurance

TaskFlow follows a test-driven approach.

### Test Coverage

* Authentication Tests
* Project Tests
* Task Tests
* Kanban Tests
* Comment Tests
* Notification Tests
* SocketIO Tests
* Integration Tests

```text
137/137 Tests Passing
```

Code Quality Tools:

* Black
* isort
* flake8
* pre-commit hooks

---

# 🚀 Deployment Infrastructure

Production deployment architecture:

```text
GitHub Repository
        │
        ▼
GitHub Actions CI/CD
        │
        ▼
Render (Flask Application)
        │
        ▼
Railway (MySQL Database)
```

Deployment Features:

* Automated Builds
* Health Checks
* Environment Variables
* Production Logging
* Secure Secrets Management
* Continuous Deployment

---

**End of README – Part 1**

Reply:

```text
Generate complete README Part 2
```

for:

* Tech Stack
* Installation
* Environment Variables
* API Documentation
* Project Structure
* Deployment Guide
* CI/CD
* Monitoring
* Troubleshooting
* Future Enhancements
* License
