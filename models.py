import logging
import os
import time
from logging.handlers import RotatingFileHandler

import mysql.connector
from mysql.connector import pooling

from config import Config

logger = logging.getLogger(__name__)

_db_log_handler_setup = False


def _setup_db_logging():
    global _db_log_handler_setup
    if not _db_log_handler_setup:
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'database.log')
        handler = RotatingFileHandler(
            log_file, maxBytes=1024 * 1024, backupCount=3
        )
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s [%(name)s] %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(formatter)
        logger.addHandler(console)

        _db_log_handler_setup = True


_setup_db_logging()

_pool = None
_pool_created_at = 0


def _build_pool_kwargs():
    kwargs = dict(
        pool_name=Config.DB_POOL_NAME,
        pool_size=Config.DB_POOL_SIZE,
        pool_reset_session=True,
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
    )
    if Config.MYSQL_SSL_CA:
        kwargs['use_pure'] = True
        kwargs['ssl_ca'] = Config.MYSQL_SSL_CA
        kwargs['ssl_verify_cert'] = Config.MYSQL_SSL_VERIFY_SERVER_CERT
    return kwargs


def _reset_pool():
    global _pool, _pool_created_at
    try:
        if _pool is not None:
            old_pool = _pool
            _pool = None
            del old_pool
    except Exception:
        _pool = None
    _pool_created_at = 0


def get_db_pool():
    global _pool, _pool_created_at
    now = time.time()
    if _pool is not None and _pool_created_at > 0:
        age = now - _pool_created_at
        if age > Config.DB_POOL_RECYCLE:
            logger.info('Pool recycle triggered (age=%.1fs > recycle=%ds)', age, Config.DB_POOL_RECYCLE)
            _reset_pool()
    if _pool is None:
        try:
            _pool = pooling.MySQLConnectionPool(**_build_pool_kwargs())
            _pool_created_at = time.time()
            logger.info('Database connection pool created (size=%d, recycle=%ds)',
                        Config.DB_POOL_SIZE, Config.DB_POOL_RECYCLE)
        except mysql.connector.Error as e:
            logger.error('Failed to create connection pool: %s', e)
            raise
    return _pool


def _is_connection_alive(conn):
    try:
        conn.ping(reconnect=False, attempts=1)
        return True
    except mysql.connector.Error:
        return False


def get_db_connection():
    max_attempts = 3
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            pool = get_db_pool()
            conn = pool.get_connection()

            if not _is_connection_alive(conn):
                logger.warning('Database connection stale (attempt %d/%d)', attempt, max_attempts)
                try:
                    conn.close()
                except Exception:
                    pass
                _reset_pool()
                if attempt < max_attempts:
                    time.sleep(2 ** (attempt - 1))
                continue

            logger.debug('Database connection acquired from pool')
            return conn

        except mysql.connector.Error as e:
            last_error = e
            logger.error('Database connection failed (attempt %d/%d): %s', attempt, max_attempts, e)
            _reset_pool()
            if attempt < max_attempts:
                time.sleep(2 ** (attempt - 1))

    logger.critical('All %d database connection attempts failed', max_attempts)
    raise last_error


def close_connection(conn):
    if conn:
        try:
            if conn.is_connected():
                conn.close()
                logger.debug('Database connection returned to pool')
        except mysql.connector.Error as e:
            logger.error('Error closing connection: %s', e)


def execute_query(query, params=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        conn.commit()
        affected = cursor.rowcount
        logger.debug('Query executed: %s | affected=%d', query[:80], affected)
        return affected
    except mysql.connector.Error as e:
        conn.rollback()
        logger.error('Query failed: %s | params=%s | error=%s', query[:80], params, e)
        raise
    finally:
        cursor.close()
        close_connection(conn)


def fetch_one(query, params=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        row = cursor.fetchone()
        logger.debug('Fetch one: %s', query[:80])
        return row
    except mysql.connector.Error as e:
        logger.error('Fetch failed: %s | params=%s | error=%s', query[:80], params, e)
        raise
    finally:
        cursor.close()
        close_connection(conn)


def fetch_all(query, params=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        rows = cursor.fetchall()
        logger.debug('Fetch all: %s | rows=%d', query[:80], len(rows))
        return rows
    except mysql.connector.Error as e:
        logger.error('Fetch all failed: %s | params=%s | error=%s', query[:80], params, e)
        raise
    finally:
        cursor.close()
        close_connection(conn)


def create_user(username, email, password):
    affected = execute_query(
        'INSERT INTO users (username, email, password) VALUES (%s, %s, %s)',
        (username, email, password)
    )
    if affected:
        user = fetch_one('SELECT id FROM users WHERE email=%s', (email,))
        return user['id'] if user else None
    return None


def get_user_by_email(email):
    return fetch_one(
        'SELECT id, username, email, password FROM users WHERE email=%s',
        (email,)
    )


def get_user_by_id(user_id):
    return fetch_one(
        'SELECT id, username, email, password FROM users WHERE id=%s',
        (user_id,)
    )


def verify_password(stored_hash, password):
    from app import bcrypt
    return bcrypt.check_password_hash(stored_hash, password)


class Transaction:
    def __init__(self):
        self.conn = None
        self.cursor = None

    def __enter__(self):
        self.conn = get_db_connection()
        self.conn.start_transaction()
        self.cursor = self.conn.cursor(dictionary=True)
        logger.debug('Transaction started')
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                self.conn.commit()
                logger.debug('Transaction committed')
            else:
                self.conn.rollback()
                logger.error('Transaction rolled back: %s', exc_val)
        finally:
            if self.cursor:
                self.cursor.close()
            close_connection(self.conn)
        return False


def create_project(name, description, owner_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            'INSERT INTO projects (name, description, owner_id) VALUES (%s, %s, %s)',
            (name, description, owner_id)
        )
        conn.commit()
        project_id = cursor.lastrowid
        logger.info('Project created: id=%d', project_id)
        return project_id
    except mysql.connector.Error as e:
        conn.rollback()
        logger.error('Failed to create project: %s', e)
        raise
    finally:
        cursor.close()
        close_connection(conn)


def get_project_by_id(project_id):
    return fetch_one(
        'SELECT p.id, p.name, p.description, p.owner_id, p.created_at, '
        'u.username AS owner_name '
        'FROM projects p JOIN users u ON p.owner_id = u.id '
        'WHERE p.id=%s',
        (project_id,)
    )


def get_user_projects(user_id):
    return fetch_all(
        'SELECT p.id, p.name, p.description, p.owner_id, p.created_at, '
        'u.username AS owner_name, '
        'COALESCE(t.task_count, 0) AS task_count '
        'FROM projects p '
        'JOIN users u ON p.owner_id = u.id '
        'LEFT JOIN project_members pm ON p.id = pm.project_id '
        'LEFT JOIN (SELECT project_id, COUNT(*) AS task_count FROM tasks GROUP BY project_id) t ON t.project_id = p.id '
        'WHERE p.owner_id=%s OR pm.user_id=%s '
        'GROUP BY p.id, p.name, p.description, p.owner_id, p.created_at, u.username, t.task_count '
        'ORDER BY p.created_at DESC',
        (user_id, user_id)
    )


def update_project(project_id, name, description):
    return execute_query(
        'UPDATE projects SET name=%s, description=%s WHERE id=%s',
        (name, description, project_id)
    )


def delete_project(project_id):
    return execute_query('DELETE FROM projects WHERE id=%s', (project_id,))


def add_member(project_id, user_id):
    existing = fetch_one(
        'SELECT id FROM project_members WHERE project_id=%s AND user_id=%s',
        (project_id, user_id)
    )
    if existing:
        return False
    execute_query(
        'INSERT INTO project_members (project_id, user_id) VALUES (%s, %s)',
        (project_id, user_id)
    )
    return True


def remove_member(project_id, user_id):
    execute_query(
        'DELETE FROM project_members WHERE project_id=%s AND user_id=%s',
        (project_id, user_id)
    )


def get_project_members(project_id):
    return fetch_all(
        'SELECT u.id, u.username, u.email '
        'FROM project_members pm JOIN users u ON pm.user_id = u.id '
        'WHERE pm.project_id=%s '
        'ORDER BY u.username',
        (project_id,)
    )


def is_project_member(project_id, user_id):
    row = fetch_one(
        'SELECT id FROM project_members WHERE project_id=%s AND user_id=%s',
        (project_id, user_id)
    )
    return row is not None


def is_project_owner(project_id, user_id):
    row = fetch_one(
        'SELECT id FROM projects WHERE id=%s AND owner_id=%s',
        (project_id, user_id)
    )
    return row is not None


def create_task(project_id, title, description, assigned_to, priority, status, deadline):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            'INSERT INTO tasks (project_id, title, description, assigned_to, priority, status, deadline) '
            'VALUES (%s, %s, %s, %s, %s, %s, %s)',
            (project_id, title, description, assigned_to, priority, status, deadline)
        )
        conn.commit()
        task_id = cursor.lastrowid
        logger.info('Task created: id=%d project=%d', task_id, project_id)
        return task_id
    except mysql.connector.Error as e:
        conn.rollback()
        logger.error('Failed to create task: %s', e)
        raise
    finally:
        cursor.close()
        close_connection(conn)


def update_task(task_id, title, description, assigned_to, priority, status, deadline):
    return execute_query(
        'UPDATE tasks SET title=%s, description=%s, assigned_to=%s, priority=%s, status=%s, deadline=%s '
        'WHERE id=%s',
        (title, description, assigned_to, priority, status, deadline, task_id)
    )


def delete_task(task_id):
    return execute_query('DELETE FROM tasks WHERE id=%s', (task_id,))


def get_task_by_id(task_id):
    return fetch_one(
        'SELECT t.id, t.project_id, t.title, t.description, t.assigned_to, '
        't.priority, t.status, t.deadline, t.created_at, '
        'u.username AS assigned_name, p.name AS project_name, p.owner_id AS project_owner_id '
        'FROM tasks t '
        'LEFT JOIN users u ON t.assigned_to = u.id '
        'JOIN projects p ON t.project_id = p.id '
        'WHERE t.id=%s',
        (task_id,)
    )


def get_project_tasks(project_id):
    return fetch_all(
        'SELECT t.id, t.project_id, t.title, t.description, t.assigned_to, '
        't.priority, t.status, t.deadline, t.created_at, '
        'u.username AS assigned_name '
        'FROM tasks t '
        'LEFT JOIN users u ON t.assigned_to = u.id '
        'WHERE t.project_id=%s '
        'ORDER BY t.created_at DESC',
        (project_id,)
    )


def get_tasks_by_user(user_id):
    return fetch_all(
        'SELECT t.id, t.project_id, t.title, t.description, t.assigned_to, '
        't.priority, t.status, t.deadline, t.created_at, '
        'p.name AS project_name '
        'FROM tasks t JOIN projects p ON t.project_id = p.id '
        'WHERE t.assigned_to=%s '
        'ORDER BY t.created_at DESC',
        (user_id,)
    )


def count_project_tasks(project_id):
    row = fetch_one(
        'SELECT COUNT(*) AS cnt FROM tasks WHERE project_id=%s',
        (project_id,)
    )
    return row['cnt'] if row else 0


def count_completed_tasks(project_id):
    row = fetch_one(
        "SELECT COUNT(*) AS cnt FROM tasks WHERE project_id=%s AND status='Completed'",
        (project_id,)
    )
    return row['cnt'] if row else 0


def count_pending_tasks(project_id):
    row = fetch_one(
        "SELECT COUNT(*) AS cnt FROM tasks WHERE project_id=%s AND status!='Completed'",
        (project_id,)
    )
    return row['cnt'] if row else 0


def create_comment(task_id, user_id, comment):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            'INSERT INTO comments (task_id, user_id, comment) VALUES (%s, %s, %s)',
            (task_id, user_id, comment)
        )
        conn.commit()
        comment_id = cursor.lastrowid
        logger.info('Comment created: id=%d task=%d user=%d', comment_id, task_id, user_id)
        return comment_id
    except mysql.connector.Error as e:
        conn.rollback()
        logger.error('Failed to create comment: %s', e)
        raise
    finally:
        cursor.close()
        close_connection(conn)


def delete_comment(comment_id):
    return execute_query('DELETE FROM comments WHERE id=%s', (comment_id,))


def get_task_comments(task_id):
    return fetch_all(
        'SELECT c.*, u.username, u.email '
        'FROM comments c JOIN users u ON c.user_id = u.id '
        'WHERE c.task_id=%s '
        'ORDER BY c.created_at ASC',
        (task_id,)
    )


def count_comments(task_id):
    row = fetch_one('SELECT COUNT(*) AS cnt FROM comments WHERE task_id=%s', (task_id,))
    return row['cnt'] if row else 0


_project_ids_cache = {}

def get_user_project_ids(user_id):
    from app import cache_get, cache_set
    cache_key = f'project_ids_{user_id}'
    cached = cache_get(cache_key, max_age=30)
    if cached is not None:
        return cached
    rows = fetch_all(
        'SELECT id FROM projects WHERE owner_id=%s '
        'UNION '
        'SELECT project_id FROM project_members WHERE user_id=%s',
        (user_id, user_id)
    )
    result = [r['id'] for r in rows]
    cache_set(cache_key, result)
    return result


def search_tasks(user_id, q=None, status=None, priority=None,
                 assigned_to=None, project_id=None,
                 deadline_from=None, deadline_to=None,
                 page=1, per_page=10):
    project_ids = get_user_project_ids(user_id)
    if not project_ids:
        return [], 0

    conditions = ['t.project_id IN (' + ','.join(['%s'] * len(project_ids)) + ')']
    params = list(project_ids)

    if q:
        conditions.append('(t.title LIKE %s OR t.description LIKE %s)')
        params.extend(['%' + q + '%', '%' + q + '%'])
    if status:
        conditions.append('t.status=%s')
        params.append(status)
    if priority:
        conditions.append('t.priority=%s')
        params.append(priority)
    if assigned_to:
        conditions.append('t.assigned_to=%s')
        params.append(int(assigned_to))
    if project_id:
        conditions.append('t.project_id=%s')
        params.append(int(project_id))
    if deadline_from:
        conditions.append('t.deadline>=%s')
        params.append(deadline_from)
    if deadline_to:
        conditions.append('t.deadline<=%s')
        params.append(deadline_to)

    where_clause = ' AND '.join(conditions)

    count_row = fetch_one(
        'SELECT COUNT(*) AS cnt FROM tasks t WHERE ' + where_clause,
        params
    )
    total = count_row['cnt'] if count_row else 0

    offset = (page - 1) * per_page
    tasks = fetch_all(
        'SELECT t.id, t.project_id, t.title, t.description, t.assigned_to, '
        't.priority, t.status, t.deadline, t.created_at, '
        'u.username AS assigned_name, p.name AS project_name '
        'FROM tasks t '
        'LEFT JOIN users u ON t.assigned_to = u.id '
        'JOIN projects p ON t.project_id = p.id '
        'WHERE ' + where_clause + ' '
        'ORDER BY t.created_at DESC '
        'LIMIT %s OFFSET %s',
        params + [per_page, offset]
    )

    return tasks, total


def move_task_status(task_id, new_status):
    valid_statuses = ['To Do', 'In Progress', 'Completed']
    if new_status not in valid_statuses:
        logger.warning('Invalid status for move_task_status: %s', new_status)
        return False
    task = fetch_one('SELECT status FROM tasks WHERE id=%s', (task_id,))
    if not task:
        logger.warning('Task not found for move: id=%d', task_id)
        return False
    if task['status'] == new_status:
        return True
    affected = execute_query(
        'UPDATE tasks SET status=%s WHERE id=%s',
        (new_status, task_id)
    )
    return affected > 0


def get_kanban_tasks(project_id):
    tasks = fetch_all(
        'SELECT t.id, t.project_id, t.title, t.description, t.assigned_to, '
        't.priority, t.status, t.deadline, t.created_at, '
        'u.username AS assigned_name '
        'FROM tasks t '
        'LEFT JOIN users u ON t.assigned_to = u.id '
        'WHERE t.project_id=%s '
        'ORDER BY t.priority DESC, t.created_at ASC',
        (project_id,)
    )
    grouped = {'To Do': [], 'In Progress': [], 'Completed': []}
    for task in tasks:
        status = task['status']
        if status in grouped:
            grouped[status].append(task)
        else:
            grouped['To Do'].append(task)
    return grouped


def create_notification(user_id, message):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            'INSERT INTO notifications (user_id, message) VALUES (%s, %s)',
            (user_id, message)
        )
        conn.commit()
        notif_id = cursor.lastrowid
        logger.info('Notification created: id=%d user=%d message="%s"', notif_id, user_id, message[:50])
        _log_notification('CREATE', notif_id, user_id, message)
        return notif_id
    except mysql.connector.Error as e:
        conn.rollback()
        logger.error('Failed to create notification: %s', e)
        raise
    finally:
        cursor.close()
        close_connection(conn)


def get_user_notifications(user_id, limit=50):
    return fetch_all(
        'SELECT id, user_id, message, is_read, created_at '
        'FROM notifications WHERE user_id=%s '
        'ORDER BY created_at DESC LIMIT %s',
        (user_id, limit)
    )


def mark_notification_read(notification_id, user_id):
    affected = execute_query(
        'UPDATE notifications SET is_read=TRUE WHERE id=%s AND user_id=%s',
        (notification_id, user_id)
    )
    if affected:
        _log_notification('READ', notification_id, user_id, '')
        logger.info('Notification marked read: id=%d user=%d', notification_id, user_id)
    return affected > 0


def mark_all_notifications_read(user_id):
    affected = execute_query(
        'UPDATE notifications SET is_read=TRUE WHERE user_id=%s AND is_read=FALSE',
        (user_id,)
    )
    if affected:
        logger.info('All notifications marked read: user=%d count=%d', user_id, affected)
    return affected


def delete_notification(notification_id, user_id):
    affected = execute_query(
        'DELETE FROM notifications WHERE id=%s AND user_id=%s',
        (notification_id, user_id)
    )
    if affected:
        _log_notification('DELETE', notification_id, user_id, '')
        logger.info('Notification deleted: id=%d user=%d', notification_id, user_id)
    return affected > 0


def count_unread_notifications(user_id):
    row = fetch_one(
        'SELECT COUNT(*) AS cnt FROM notifications WHERE user_id=%s AND is_read=FALSE',
        (user_id,)
    )
    return row['cnt'] if row else 0


_notification_logger = None


def _get_notification_logger():
    global _notification_logger
    if _notification_logger is None:
        _notification_logger = logging.getLogger('notification')
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        handler = RotatingFileHandler(
            os.path.join(log_dir, 'notification.log'), maxBytes=1024 * 1024, backupCount=3
        )
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s %(levelname)s [%(name)s] %(message)s')
        handler.setFormatter(formatter)
        _notification_logger.addHandler(handler)
        _notification_logger.setLevel(logging.INFO)
    return _notification_logger


def _log_notification(action, notif_id, user_id, message):
    try:
        _get_notification_logger().info(
            'ACTION=%s NOTIF_ID=%d USER=%d MESSAGE="%s"', action, notif_id, user_id, message[:100]
        )
    except Exception:
        pass


def _ensure_index(index_name, table, columns, db=None):
    if db is None:
        db = Config.MYSQL_DB
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT COUNT(*) FROM information_schema.statistics '
            'WHERE table_schema=%s AND table_name=%s AND index_name=%s',
            (db, table, index_name)
        )
        exists = cursor.fetchone()[0] > 0
        cursor.close()
        close_connection(conn)
        if not exists:
            cols = ', '.join(columns)
            execute_query(f'CREATE INDEX {index_name} ON {table} ({cols})')
            logger.info('Index %s created on %s (%s)', index_name, table, cols)
    except Exception as e:
        logger.warning('Could not create index %s: %s', index_name, e)


def ensure_optimal_indexes():
    _ensure_index('idx_notifications_user_read', 'notifications', ['user_id', 'is_read'])
    _ensure_index('idx_notifications_user_created', 'notifications', ['user_id', 'created_at'])
    _ensure_index('idx_notifications_created_at', 'notifications', ['created_at'])
    _ensure_index('idx_tasks_project_status', 'tasks', ['project_id', 'status'])


def get_dashboard_stats(user_id):
    row = fetch_one(
        'SELECT '
        'COALESCE(COUNT(DISTINCT p.id), 0) AS total_projects, '
        'COALESCE(COUNT(DISTINCT t.id), 0) AS total_tasks, '
        'COALESCE(SUM(CASE WHEN t.status=%s THEN 1 ELSE 0 END), 0) AS completed_tasks, '
        'COALESCE(SUM(CASE WHEN t.status!=%s THEN 1 ELSE 0 END), 0) AS pending_tasks, '
        'COALESCE(SUM(CASE WHEN DATE(t.deadline)=CURDATE() THEN 1 ELSE 0 END), 0) AS due_today '
        'FROM projects p '
        'LEFT JOIN project_members pm ON p.id = pm.project_id '
        'LEFT JOIN tasks t ON t.project_id = p.id '
        'WHERE p.owner_id=%s OR pm.user_id=%s',
        ('Completed', 'Completed', user_id, user_id)
    )
    if row:
        return {
            'total_projects': row['total_projects'] or 0,
            'total_tasks': row['total_tasks'] or 0,
            'completed_tasks': row['completed_tasks'] or 0,
            'pending_tasks': row['pending_tasks'] or 0,
            'due_today': row['due_today'] or 0,
        }
    return {
        'total_projects': 0,
        'total_tasks': 0,
        'completed_tasks': 0,
        'pending_tasks': 0,
        'due_today': 0,
    }
