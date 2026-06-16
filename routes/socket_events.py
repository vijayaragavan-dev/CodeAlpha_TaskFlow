import logging
import os
from logging.handlers import RotatingFileHandler

from flask import request
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room

from app import socketio
from models import is_project_member, is_project_owner, get_user_by_id

_socket_logger = None


def get_socket_logger():
    global _socket_logger
    if _socket_logger is None:
        _socket_logger = logging.getLogger('socketio')
        log_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs'
        )
        os.makedirs(log_dir, exist_ok=True)
        handler = RotatingFileHandler(
            os.path.join(log_dir, 'socketio.log'), maxBytes=1024 * 1024, backupCount=3
        )
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s %(levelname)s [%(name)s] %(message)s')
        handler.setFormatter(formatter)
        _socket_logger.addHandler(handler)
        _socket_logger.setLevel(logging.INFO)
    return _socket_logger


active_users = {}


@socketio.on('connect')
def handle_connect():
    user_id = _get_authenticated_user()
    if user_id is None:
        get_socket_logger().warning('Unauthenticated connection attempt rejected')
        return False
    active_users[user_id] = request.sid
    join_room(f'user_{user_id}')
    get_socket_logger().info('User connected: id=%d sid=%s', user_id, request.sid)


@socketio.on('disconnect')
def handle_disconnect():
    user_id = _get_authenticated_user()
    if user_id and user_id in active_users:
        del active_users[user_id]
    for room in list(request.namespace.rooms):
        if room.startswith('project_'):
            leave_room(room)
    get_socket_logger().info('User disconnected: id=%s sid=%s', user_id, request.sid)


@socketio.on('join_project')
def handle_join_project(data):
    user_id = _get_authenticated_user()
    if user_id is None:
        return
    project_id = data.get('project_id')
    if not project_id:
        return
    if not is_project_member(project_id, user_id) and not is_project_owner(project_id, user_id):
        get_socket_logger().warning(
            'Unauthorized room join attempt: user=%d project=%d', user_id, project_id
        )
        return
    room = f'project_{project_id}'
    join_room(room)
    get_socket_logger().info('User joined room: user=%d room=%s', user_id, room)


@socketio.on('leave_project')
def handle_leave_project(data):
    user_id = _get_authenticated_user()
    if user_id is None:
        return
    project_id = data.get('project_id')
    if project_id:
        room = f'project_{project_id}'
        leave_room(room)
        get_socket_logger().info('User left room: user=%d room=%s', user_id, room)


def _get_authenticated_user():
    try:
        if current_user.is_authenticated:
            return current_user.id
    except Exception:
        pass
    try:
        from flask import session
        user_id = session.get('user_id') or session.get('_user_id')
        if user_id:
            return int(user_id)
    except Exception:
        pass
    return None
