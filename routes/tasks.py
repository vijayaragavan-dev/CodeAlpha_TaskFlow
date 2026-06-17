import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user

from forms import TaskForm, CommentForm
from models import (
    create_task, update_task, delete_task, get_task_by_id, get_project_tasks,
    get_project_by_id, get_project_members, is_project_member,
    move_task_status, create_comment, delete_comment,
    get_task_comments, search_tasks, get_user_project_ids,
    create_notification, fetch_one
)
from app import socketio

tasks_bp = Blueprint('tasks', __name__)

_task_logger = None


def get_task_logger():
    global _task_logger
    if _task_logger is None:
        _task_logger = logging.getLogger('task')
        log_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs'
        )
        os.makedirs(log_dir, exist_ok=True)
        handler = RotatingFileHandler(
            os.path.join(log_dir, 'task.log'), maxBytes=1024 * 1024, backupCount=3
        )
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s [%(name)s] %(message)s'
        )
        handler.setFormatter(formatter)
        _task_logger.addHandler(handler)
        _task_logger.setLevel(logging.INFO)
    return _task_logger


def _get_project_member_choices(project_id, project=None):
    members = get_project_members(project_id)
    choices = [(0, 'Unassigned')]
    for m in members:
        choices.append((str(m['id']), m['username']))
    if project is None:
        project = get_project_by_id(project_id)
    if project:
        already = [m['id'] for m in members]
        if project['owner_id'] not in already:
            choices.append((str(project['owner_id']), project['owner_name'] + ' (owner)'))
    return choices


def _can_modify_task(task):
    if not task:
        return False
    return (
        current_user.id == task['project_owner_id'] or
        current_user.id == task['assigned_to']
    )


@tasks_bp.route('/projects/<int:project_id>/tasks/create', methods=['GET', 'POST'])
@login_required
def create(project_id):
    project = get_project_by_id(project_id)
    if not project:
        abort(404)
    is_owner = current_user.id == project['owner_id']
    if not is_owner and not is_project_member(project_id, current_user.id):
        abort(403)
    form = TaskForm()
    form.assigned_to.choices = _get_project_member_choices(project_id, project)
    if form.validate_on_submit():
        title = form.title.data.strip()
        description = form.description.data.strip() if form.description.data else ''
        assigned_to = form.assigned_to.data if form.assigned_to.data else None
        priority = form.priority.data
        status = form.status.data
        deadline = form.deadline.data
        try:
            task_id = create_task(project_id, title, description, assigned_to, priority, status, deadline)
            if task_id:
                get_task_logger().info(
                    'Task created: id=%d project=%d title=%s', task_id, project_id, title
                )
                if assigned_to and assigned_to != current_user.id:
                    assignee = fetch_one('SELECT username FROM users WHERE id=%s', (assigned_to,))
                    if assignee:
                        create_notification(
                            assigned_to,
                            f'{current_user.username} assigned you task: {title}'
                        )
                flash('Task created successfully.', 'success')
                return redirect(url_for('projects.detail', id=project_id))
        except Exception as e:
            get_task_logger().error('Task creation failed: %s', e)
            flash('Error creating task.', 'danger')
    return render_template('create_task.html', form=form, project=project)


@tasks_bp.route('/tasks/<int:task_id>')
@login_required
def detail(task_id):
    task = get_task_by_id(task_id)
    if not task:
        abort(404)
    project = get_project_by_id(task['project_id'])
    if not project:
        abort(404)
    if (current_user.id != task['project_owner_id'] and
        not is_project_member(task['project_id'], current_user.id)):
        abort(403)
    comments = get_task_comments(task_id)
    comment_count = len(comments)
    form = CommentForm()
    return render_template('task_detail.html', task=task, project=project,
                           comments=comments, comment_count=comment_count, form=form)


@tasks_bp.route('/tasks/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(task_id):
    task = get_task_by_id(task_id)
    if not task:
        abort(404)
    project = get_project_by_id(task['project_id'])
    if not project:
        abort(404)
    if not _can_modify_task(task) and current_user.id != task['project_owner_id']:
        get_task_logger().warning(
            'Unauthorized edit attempt: user=%d task=%d', current_user.id, task_id
        )
        abort(403)
    form = TaskForm(obj=task)
    form.assigned_to.choices = _get_project_member_choices(task['project_id'], project)
    if form.validate_on_submit():
        title = form.title.data.strip()
        description = form.description.data.strip() if form.description.data else ''
        assigned_to = form.assigned_to.data if form.assigned_to.data else None
        priority = form.priority.data
        status = form.status.data
        deadline = form.deadline.data
        try:
            old_task = get_task_by_id(task_id)
            update_task(task_id, title, description, assigned_to, priority, status, deadline)
            get_task_logger().info('Task updated: id=%d', task_id)

            if assigned_to and assigned_to != current_user.id and assigned_to != old_task.get('assigned_to'):
                assignee = fetch_one('SELECT username FROM users WHERE id=%s', (assigned_to,))
                if assignee:
                    create_notification(
                        assigned_to,
                        f'{current_user.username} assigned you task: {title}'
                    )

            if status != old_task.get('status') and old_task.get('assigned_to') and old_task['assigned_to'] != current_user.id:
                create_notification(
                    old_task['assigned_to'],
                    f"Task '{title}' moved to {status}"
                )

            flash('Task updated successfully.', 'success')
            return redirect(url_for('tasks.detail', task_id=task_id))
        except Exception as e:
            get_task_logger().error('Task update failed: %s', e)
            flash('Error updating task.', 'danger')
    return render_template('edit_task.html', form=form, task=task, project=project)


@tasks_bp.route('/tasks/<int:task_id>/delete', methods=['POST'])
@login_required
def delete(task_id):
    task = get_task_by_id(task_id)
    if not task:
        abort(404)
    project = get_project_by_id(task['project_id'])
    if not project:
        abort(404)
    if not _can_modify_task(task) and current_user.id != task['project_owner_id']:
        get_task_logger().warning(
            'Unauthorized delete attempt: user=%d task=%d', current_user.id, task_id
        )
        abort(403)
    try:
        delete_task(task_id)
        get_task_logger().info('Task deleted: id=%d project=%d', task_id, task['project_id'])
        flash('Task deleted successfully.', 'success')
    except Exception as e:
        get_task_logger().error('Task deletion failed: %s', e)
        flash('Error deleting task.', 'danger')
    return redirect(url_for('projects.detail', id=task['project_id']))


@tasks_bp.route('/tasks/<int:task_id>/comments/add', methods=['POST'])
@login_required
def add_comment(task_id):
    task = get_task_by_id(task_id)
    if not task:
        abort(404)
    if (current_user.id != task['project_owner_id'] and
        not is_project_member(task['project_id'], current_user.id)):
        abort(403)
    form = CommentForm()
    if form.validate_on_submit():
        comment = form.comment.data.strip()
        if comment:
            import html
            comment = html.escape(comment)
            try:
                create_comment(task_id, current_user.id, comment)
                get_task_logger().info(
                    'Comment added: task=%d user=%d', task_id, current_user.id
                )
                if task.get('assigned_to') and task['assigned_to'] != current_user.id:
                    create_notification(
                        task['assigned_to'],
                        f'{current_user.username} commented on your task: {task["title"]}'
                    )
                elif task.get('project_owner_id') and task['project_owner_id'] != current_user.id and task['project_owner_id'] != task.get('assigned_to'):
                    create_notification(
                        task['project_owner_id'],
                        f'{current_user.username} commented on task: {task["title"]}'
                    )
                try:
                    socketio.emit('comment_added', {
                        'task_id': task_id,
                        'username': current_user.username,
                        'comment': comment,
                        'project_id': task['project_id'],
                        'user_id': current_user.id
                    }, room=f'project_{task["project_id"]}')
                except Exception:
                    pass
                flash('Comment added successfully.', 'success')
            except Exception as e:
                get_task_logger().error('Comment creation failed: %s', e)
                flash('Error adding comment.', 'danger')
        else:
            flash('Comment cannot be empty.', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(error, 'danger')
    return redirect(url_for('tasks.detail', task_id=task_id))


@tasks_bp.route('/comments/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment_route(comment_id):
    from models import fetch_one
    comment = fetch_one(
        'SELECT c.*, t.project_id, p.owner_id AS project_owner_id FROM comments c '
        'JOIN tasks t ON c.task_id = t.id '
        'JOIN projects p ON t.project_id = p.id WHERE c.id=%s',
        (comment_id,)
    )
    if not comment:
        abort(404)
    can_delete = (
        current_user.id == comment['user_id'] or
        current_user.id == comment['project_owner_id']
    )
    if not can_delete:
        get_task_logger().warning(
            'Unauthorized comment delete attempt: user=%d comment=%d',
            current_user.id, comment_id
        )
        flash('Permission denied.', 'danger')
        return redirect(url_for('tasks.detail', task_id=comment['task_id']))
    try:
        delete_comment(comment_id)
        get_task_logger().info(
            'Comment deleted: id=%d user=%d', comment_id, current_user.id
        )
        flash('Comment deleted successfully.', 'success')
    except Exception as e:
        get_task_logger().error('Comment deletion failed: %s', e)
        flash('Error deleting comment.', 'danger')
    return redirect(url_for('tasks.detail', task_id=comment['task_id']))


@tasks_bp.route('/tasks/search')
@login_required
def search():
    q = request.args.get('q', '').strip()
    status = request.args.get('status', '').strip()
    priority = request.args.get('priority', '').strip()
    assigned_to = request.args.get('assigned_to', '').strip()
    project_id = request.args.get('project', '').strip()
    deadline_from = request.args.get('deadline_from', '').strip()
    deadline_to = request.args.get('deadline_to', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 10

    filters = {
        'q': q,
        'status': status if status else None,
        'priority': priority if priority else None,
        'assigned_to': assigned_to if assigned_to else None,
        'project_id': project_id if project_id else None,
        'deadline_from': deadline_from if deadline_from else None,
        'deadline_to': deadline_to if deadline_to else None,
    }

    get_task_logger().info(
        'Search: user=%d q=%s filters=%s', current_user.id, q,
        {k: v for k, v in filters.items() if v}
    )

    try:
        tasks, total = search_tasks(
            current_user.id, page=page, per_page=per_page, **filters
        )
    except Exception as e:
        get_task_logger().error('Search failed: %s', e)
        flash('Search failed. Please try again.', 'danger')
        tasks, total = [], 0

    total_pages = max(1, (total + per_page - 1) // per_page)

    return render_template(
        'search_results.html',
        tasks=tasks,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        filters=filters,
        q=q
    )


@tasks_bp.route('/tasks/<int:task_id>/move', methods=['POST'])
@login_required
def move_task(task_id):
    task = get_task_by_id(task_id)
    if not task:
        return jsonify({'success': False, 'error': 'Task not found'}), 404

    if (current_user.id != task['project_owner_id'] and
        not is_project_member(task['project_id'], current_user.id)):
        get_task_logger().warning(
            'Unauthorized move attempt: user=%d task=%d', current_user.id, task_id
        )
        return jsonify({'success': False, 'error': 'Forbidden'}), 403

    if current_user.id != task['assigned_to'] and current_user.id != task['project_owner_id']:
        return jsonify({'success': False, 'error': 'Only the assigned user or project owner can move tasks'}), 403

    data = request.get_json()
    if not data or 'status' not in data:
        return jsonify({'success': False, 'error': 'Status is required'}), 400

    new_status = data['status'].strip()
    valid_statuses = ['To Do', 'In Progress', 'Completed']
    if new_status not in valid_statuses:
        return jsonify({'success': False, 'error': 'Invalid status'}), 400

    try:
        ok = move_task_status(task_id, new_status)
        if ok:
            get_task_logger().info(
                'Task moved: id=%d status=%s user=%d', task_id, new_status, current_user.id
            )
            if task.get('assigned_to') and task['assigned_to'] != current_user.id:
                create_notification(
                    task['assigned_to'],
                    f"Task '{task['title']}' moved to {new_status}"
                )
            try:
                socketio.emit('task_moved', {
                    'task_id': task_id,
                    'status': new_status,
                    'title': task['title'],
                    'project_id': task['project_id'],
                    'user_id': current_user.id,
                    'username': current_user.username
                }, room=f'project_{task["project_id"]}')
            except Exception:
                pass
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to move task'}), 500
    except Exception as e:
        get_task_logger().error('Task move failed: id=%d error=%s', task_id, e)
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
