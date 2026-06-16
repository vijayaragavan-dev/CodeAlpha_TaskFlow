#!/usr/bin/env python3
"""
TaskFlow Database Backup Script

Usage:
    python scripts/backup_db.py

Creates timestamped SQL dump in the backups/ directory.
Supports MySQL via mysqldump or pure Python export.
"""

import os
import sys
import subprocess
import datetime
import logging
from logging.handlers import RotatingFileHandler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import Config

BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backups')
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')

_logger = None


def get_logger():
    global _logger
    if _logger is None:
        _logger = logging.getLogger('backup')
        os.makedirs(LOG_DIR, exist_ok=True)
        handler = RotatingFileHandler(
            os.path.join(LOG_DIR, 'backup.log'), maxBytes=1024 * 1024, backupCount=3
        )
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s %(levelname)s [%(name)s] %(message)s')
        handler.setFormatter(formatter)
        _logger.addHandler(handler)
        _logger.setLevel(logging.INFO)
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(formatter)
        _logger.addHandler(console)
    return _logger


def backup_via_mysqldump():
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'taskflow_{timestamp}.sql'
    filepath = os.path.join(BACKUP_DIR, filename)

    os.makedirs(BACKUP_DIR, exist_ok=True)

    cmd = [
        'mysqldump',
        f'--host={Config.MYSQL_HOST}',
        f'--port={Config.MYSQL_PORT}',
        f'--user={Config.MYSQL_USER}',
        f'--password={Config.MYSQL_PASSWORD}',
        '--routines',
        '--single-transaction',
        '--quick',
        Config.MYSQL_DB,
    ]

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, timeout=120)

        if result.returncode == 0:
            size_kb = os.path.getsize(filepath) / 1024
            get_logger().info(
                'Backup created: %s (%.2f KB)', filename, size_kb
            )
            return filepath
        else:
            error = result.stderr.decode('utf-8', errors='replace')
            get_logger().error('mysqldump failed: %s', error)
            return None
    except FileNotFoundError:
        get_logger().warning('mysqldump not found, falling back to Python export')
        return backup_via_python()
    except subprocess.TimeoutExpired:
        get_logger().error('Backup timed out after 120 seconds')
        return None
    except Exception as e:
        get_logger().error('Backup failed: %s', e)
        return None


def backup_via_python():
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'taskflow_{timestamp}.sql'
    filepath = os.path.join(BACKUP_DIR, filename)

    os.makedirs(BACKUP_DIR, exist_ok=True)

    try:
        import mysql.connector

        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
        )
        cursor = conn.cursor()

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f'-- TaskFlow Database Backup\n')
            f.write(f'-- Date: {datetime.datetime.now()}\n')
            f.write(f'-- Database: {Config.MYSQL_DB}\n\n')

            cursor.execute('SHOW TABLES')
            tables = [row[0] for row in cursor.fetchall()]

            for table in tables:
                cursor.execute(f'SHOW CREATE TABLE `{table}`')
                create_stmt = cursor.fetchone()[1]
                f.write(f'\n{create_stmt};\n\n')

                cursor.execute(f'SELECT * FROM `{table}`')
                rows = cursor.fetchall()
                if rows:
                    col_count = len(cursor.description)
                    placeholders = ', '.join(['%s'] * col_count)
                    for row in rows:
                        values = []
                        for val in row:
                            if val is None:
                                values.append('NULL')
                            elif isinstance(val, (int, float)):
                                values.append(str(val))
                            elif isinstance(val, bytes):
                                values.append(f"'{val.decode('utf-8', errors='replace')}'")
                            else:
                                escaped = str(val).replace("'", "''").replace('\\', '\\\\')
                                values.append(f"'{escaped}'")
                        f.write(f'INSERT INTO `{table}` VALUES ({", ".join(values)});\n')

        size_kb = os.path.getsize(filepath) / 1024
        get_logger().info('Backup created (Python): %s (%.2f KB)', filename, size_kb)

        cursor.close()
        conn.close()
        return filepath
    except Exception as e:
        get_logger().error('Python backup failed: %s', e)
        return None


def cleanup_old_backups(keep=10):
    try:
        files = sorted(
            [f for f in os.listdir(BACKUP_DIR) if f.startswith('taskflow_') and f.endswith('.sql')],
            reverse=True
        )
        if len(files) > keep:
            for f in files[keep:]:
                os.remove(os.path.join(BACKUP_DIR, f))
                get_logger().info('Removed old backup: %s', f)
    except Exception as e:
        get_logger().warning('Cleanup failed: %s', e)


def main():
    get_logger().info('Starting database backup...')
    result = backup_via_mysqldump()
    if result:
        cleanup_old_backups()
        get_logger().info('Backup completed successfully: %s', result)
        return 0
    else:
        get_logger().error('Backup failed')
        return 1


if __name__ == '__main__':
    sys.exit(main())
