#!/usr/bin/env python3
"""
TaskFlow Database Reset Script

Usage:
    python scripts/reset_database.py

Drops all tables, recreates schema, and seeds demo data.
WARNING: This will delete ALL existing data!
"""

import sys
import os
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import Config

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database.sql')
SEED_SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts', 'seed_demo_data.py')


def reset():
    print('=' * 50)
    print('  TaskFlow Database Reset')
    print('=' * 50)
    print()
    print(f'  Host:     {Config.MYSQL_HOST}')
    print(f'  Port:     {Config.MYSQL_PORT}')
    print(f'  Database: {Config.MYSQL_DB}')
    print(f'  User:     {Config.MYSQL_USER}')
    print()

    confirm = input('  WARNING: This will delete ALL data! Continue? (y/N): ')
    if confirm.lower() != 'y':
        print('  Aborted.')
        return

    print()
    print('  Step 1: Dropping all tables and recreating schema...')

    mysql_cmd = [
        'mysql',
        f'--host={Config.MYSQL_HOST}',
        f'--port={Config.MYSQL_PORT}',
        f'--user={Config.MYSQL_USER}',
    ]
    if Config.MYSQL_PASSWORD:
        mysql_cmd.append(f'--password={Config.MYSQL_PASSWORD}')

    try:
        with open(DB_FILE, 'r') as f:
            schema = f.read()

        result = subprocess.run(
            mysql_cmd,
            input=schema.encode('utf-8'),
            capture_output=True,
            timeout=30
        )

        if result.returncode == 0:
            print('  ✓ Schema recreated successfully')
        else:
            error = result.stderr.decode('utf-8', errors='replace')
            print(f'  ✗ Schema recreation failed: {error}')
            return
    except FileNotFoundError:
        print('  ✗ mysql client not found. Try running manually:')
        print(f'    mysql -u {Config.MYSQL_USER} -p < {DB_FILE}')
        return
    except subprocess.TimeoutExpired:
        print('  ✗ Command timed out')
        return

    print()
    print('  Step 2: Seeding demo data...')

    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location('seed_demo_data', SEED_SCRIPT)
        seed_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(seed_module)
        print('  ✓ Demo data seeded successfully')
    except Exception as e:
        print(f'  ✗ Demo data seeding failed: {e}')
        return

    print()
    print('=' * 50)
    print('  Database Reset Complete!')
    print('=' * 50)


if __name__ == '__main__':
    reset()
