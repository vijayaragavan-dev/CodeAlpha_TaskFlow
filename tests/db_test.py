import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models import (
    get_db_connection, close_connection,
    execute_query, fetch_one, fetch_all, Transaction
)
import mysql.connector

PASS = 0
FAIL = 0
TEST_USERNAME = 'test_user_crud'
TEST_EMAIL = 'test_crud@taskflow.local'


def print_result(name, passed):
    global PASS, FAIL
    if passed:
        print(f'  [PASS] {name}')
        PASS += 1
    else:
        print(f'  [FAIL] {name}')
        FAIL += 1


def cleanup_test_user():
    try:
        execute_query(
            'DELETE FROM users WHERE username=%s OR email=%s',
            (TEST_USERNAME, TEST_EMAIL)
        )
    except Exception:
        pass


def test_connection():
    global PASS, FAIL
    try:
        conn = get_db_connection()
        ok = conn.is_connected()
        close_connection(conn)
        print_result('Database connection', ok)
        return ok
    except Exception as e:
        print(f'  [FAIL] Database connection ({e})')
        FAIL += 1
        return False


def test_insert_user():
    global PASS, FAIL
    try:
        cleanup_test_user()
        affected = execute_query(
            'INSERT INTO users (username, email, password) VALUES (%s, %s, %s)',
            (TEST_USERNAME, TEST_EMAIL, 'hashed_password_placeholder')
        )
        print_result('Insert user', affected == 1)
        return affected == 1
    except Exception as e:
        print(f'  [FAIL] Insert user ({e})')
        FAIL += 1
        return False


def test_fetch_user():
    global PASS, FAIL
    try:
        user = fetch_one(
            'SELECT id, username, email FROM users WHERE username=%s',
            (TEST_USERNAME,)
        )
        ok = user is not None and user['username'] == TEST_USERNAME
        print_result('Fetch user', ok)
        return ok
    except Exception as e:
        print(f'  [FAIL] Fetch user ({e})')
        FAIL += 1
        return False


def test_update_user():
    global PASS, FAIL
    try:
        new_email = 'updated_' + TEST_EMAIL
        affected = execute_query(
            'UPDATE users SET email=%s WHERE username=%s',
            (new_email, TEST_USERNAME)
        )
        user = fetch_one(
            'SELECT email FROM users WHERE username=%s',
            (TEST_USERNAME,)
        )
        ok = affected == 1 and user and user['email'] == new_email
        print_result('Update user', ok)
        return ok
    except Exception as e:
        print(f'  [FAIL] Update user ({e})')
        FAIL += 1
        return False


def test_delete_user():
    global PASS, FAIL
    try:
        affected = execute_query(
            'DELETE FROM users WHERE username=%s',
            (TEST_USERNAME,)
        )
        user = fetch_one(
            'SELECT id FROM users WHERE username=%s',
            (TEST_USERNAME,)
        )
        ok = affected == 1 and user is None
        print_result('Delete user', ok)
        return ok
    except Exception as e:
        print(f'  [FAIL] Delete user ({e})')
        FAIL += 1
        return False


def test_transaction_rollback():
    global PASS, FAIL
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        conn.start_transaction()

        cursor.execute(
            'INSERT INTO users (username, email, password) VALUES (%s, %s, %s)',
            ('rollback_test_user', 'rollback@test.local', 'pw')
        )
        conn.rollback()
        cursor.close()
        close_connection(conn)
        conn = None

        user = fetch_one(
            'SELECT id FROM users WHERE username=%s',
            ('rollback_test_user',)
        )
        ok = user is None
        print_result('Transaction rollback', ok)
        return ok
    except Exception as e:
        print(f'  [FAIL] Transaction rollback ({e})')
        FAIL += 1
        return False
    finally:
        if conn:
            close_connection(conn)
        try:
            execute_query(
                'DELETE FROM users WHERE username=%s',
                ('rollback_test_user',)
            )
        except Exception:
            pass


def test_transaction_context():
    global PASS, FAIL
    try:
        with Transaction() as cursor:
            cursor.execute(
                'INSERT INTO users (username, email, password) VALUES (%s, %s, %s)',
                ('ctx_test_user', 'ctx@test.local', 'pw')
            )
        user = fetch_one(
            'SELECT id FROM users WHERE username=%s',
            ('ctx_test_user',)
        )
        ok = user is not None
        print_result('Transaction context manager', ok)
        execute_query('DELETE FROM users WHERE username=%s', ('ctx_test_user',))
        return ok
    except Exception as e:
        print(f'  [FAIL] Transaction context manager ({e})')
        FAIL += 1
        return False


def test_connection_pooling():
    global PASS, FAIL
    try:
        connections = []
        for i in range(3):
            conn = get_db_connection()
            connections.append(conn)
        for conn in connections:
            close_connection(conn)
        print_result('Connection pooling (3 connections)', True)
        return True
    except Exception as e:
        print(f'  [FAIL] Connection pooling ({e})')
        FAIL += 1
        return False


def test_fetch_all():
    global PASS, FAIL
    try:
        execute_query(
            'INSERT INTO users (username, email, password) VALUES (%s, %s, %s)',
            ('fetch_all_a', 'a@test.local', 'pw')
        )
        execute_query(
            'INSERT INTO users (username, email, password) VALUES (%s, %s, %s)',
            ('fetch_all_b', 'b@test.local', 'pw')
        )
        rows = fetch_all(
            'SELECT username FROM users WHERE username LIKE %s',
            ('fetch_all_%',)
        )
        ok = len(rows) == 2
        print_result('Fetch all', ok)
        execute_query(
            'DELETE FROM users WHERE username LIKE %s',
            ('fetch_all_%',)
        )
        return ok
    except Exception as e:
        print(f'  [FAIL] Fetch all ({e})')
        FAIL += 1
        return False


def run_tests():
    print('=' * 50)
    print('  TaskFlow Database CRUD Test Suite')
    print('=' * 50)
    print()
    print(f'  Host: localhost  Database: taskflow')
    print()

    has_connection = test_connection()
    if not has_connection:
        print()
        print('  WARNING: Cannot connect to MySQL. Ensure MySQL is running')
        print('  and the taskflow database exists. Run:')
        print()
        print('    mysql -u root -p < database.sql')
        print()
        print(f'  PASS: {PASS}  FAIL: {FAIL}')
        print('=' * 50)
        return

    test_insert_user()
    test_fetch_user()
    test_update_user()
    test_delete_user()
    cleanup_test_user()

    test_transaction_rollback()
    test_transaction_context()

    test_connection_pooling()
    test_fetch_all()

    print()
    print('=' * 50)
    print(f'  RESULTS:  PASS: {PASS}  FAIL: {FAIL}')
    print('=' * 50)

    if FAIL == 0:
        print('  All database tests passed.')
    else:
        print(f'  {FAIL} test(s) failed. Review errors above.')


if __name__ == '__main__':
    run_tests()
