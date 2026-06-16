import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user

from models import (
    get_user_notifications, mark_notification_read, mark_all_notifications_read,
    delete_notification, count_unread_notifications
)

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')

_notif_route_logger = None


def get_notif_route_logger():
    global _notif_route_logger
    if _notif_route_logger is None:
        _notif_route_logger = logging.getLogger('notification.route')
        log_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs'
        )
        os.makedirs(log_dir, exist_ok=True)
        handler = RotatingFileHandler(
            os.path.join(log_dir, 'notification_route.log'), maxBytes=1024 * 1024, backupCount=3
        )
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s %(levelname)s [%(name)s] %(message)s')
        handler.setFormatter(formatter)
        _notif_route_logger.addHandler(handler)
        _notif_route_logger.setLevel(logging.INFO)
    return _notif_route_logger


@notifications_bp.route('/')
@login_required
def list_notifications():
    notifications = get_user_notifications(current_user.id)
    unread_count = count_unread_notifications(current_user.id)
    return render_template('notifications.html', notifications=notifications, unread_count=unread_count)


@notifications_bp.route('/<int:notification_id>/read', methods=['POST'])
@login_required
def read(notification_id):
    ok = mark_notification_read(notification_id, current_user.id)
    if not ok:
        get_notif_route_logger().warning(
            'Authorization failure: user=%d tried to read notification=%d',
            current_user.id, notification_id
        )
        abort(403)
    flash('Notification marked as read.', 'success')
    return redirect(url_for('notifications.list_notifications'))


@notifications_bp.route('/read-all', methods=['POST'])
@login_required
def read_all():
    count = mark_all_notifications_read(current_user.id)
    flash('All notifications cleared.' if count else 'No unread notifications.', 'success')
    return redirect(url_for('notifications.list_notifications'))


@notifications_bp.route('/<int:notification_id>/delete', methods=['POST'])
@login_required
def delete(notification_id):
    ok = delete_notification(notification_id, current_user.id)
    if not ok:
        get_notif_route_logger().warning(
            'Authorization failure: user=%d tried to delete notification=%d',
            current_user.id, notification_id
        )
        abort(403)
    flash('Notification deleted.', 'success')
    return redirect(url_for('notifications.list_notifications'))


@notifications_bp.route('/unread-count')
@login_required
def unread_count():
    count = count_unread_notifications(current_user.id)
    return jsonify({'count': count})
