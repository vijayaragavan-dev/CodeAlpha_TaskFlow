import logging
import os
from logging.handlers import RotatingFileHandler

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from forms import ProjectForm, MemberForm
from models import (
    create_project, get_project_by_id, get_user_projects,
    update_project, delete_project, get_dashboard_stats,
    add_member, remove_member, get_project_members,
    is_project_owner, get_user_by_email, fetch_one,
    get_project_tasks, count_project_tasks, is_project_member,
    get_kanban_tasks, create_notification
)
from app import socketio

projects_bp = Blueprint('projects', __name__, url_prefix='/projects')

_project_logger = None


def get_project_logger():
    global _project_logger
    if _project_logger is None:
        _project_logger = logging.getLogger('project')
        log_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs'
        )
        os.makedirs(log_dir, exist_ok=True)
        handler = RotatingFileHandler(
            os.path.join(log_dir, 'project.log'), maxBytes=1024 * 1024, backupCount=3
        )
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s [%(name)s] %(message)s'
        )
        handler.setFormatter(formatter)
        _project_logger.addHandler(handler)
        _project_logger.setLevel(logging.INFO)
    return _project_logger


@projects_bp.route('/')
@login_required
def list_projects():
    projects = get_user_projects(current_user.id)
    return render_template('projects.html', projects=projects)


@projects_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = ProjectForm()
    if form.validate_on_submit():
        name = form.name.data.strip()
        description = form.description.data.strip() if form.description.data else ''
        try:
            project_id = create_project(name, description, current_user.id)
            if project_id:
                get_project_logger().info(
                    'Project created: id=%d name=%s owner=%d',
                    project_id, name, current_user.id
                )
                flash('Project created successfully.', 'success')
                return redirect(url_for('projects.detail', id=project_id))
        except Exception as e:
            get_project_logger().error('Project creation failed: %s', e)
            flash('Error creating project. Please try again.', 'danger')
    return render_template('create_project.html', form=form)


@projects_bp.route('/<int:id>/kanban')
@login_required
def kanban(id):
    project = get_project_by_id(id)
    if not project:
        abort(404)
    if not is_project_member(id, current_user.id) and not is_project_owner(id, current_user.id):
        abort(403)
    tasks = get_kanban_tasks(id)
    return render_template('kanban.html', project=project, tasks=tasks)


@projects_bp.route('/<int:id>')
@login_required
def detail(id):
    project = get_project_by_id(id)
    if not project:
        abort(404)
    members = get_project_members(id)
    tasks = get_project_tasks(id)
    task_count = count_project_tasks(id)
    return render_template('project_detail.html', project=project,
                           members=members, tasks=tasks, task_count=task_count,
                           is_member=is_project_member(id, current_user.id))


@projects_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    project = get_project_by_id(id)
    if not project:
        abort(404)
    if project['owner_id'] != current_user.id:
        get_project_logger().warning(
            'Unauthorized edit attempt: user=%d project=%d', current_user.id, id
        )
        abort(403)
    form = ProjectForm(obj=project)
    if form.validate_on_submit():
        name = form.name.data.strip()
        description = form.description.data.strip() if form.description.data else ''
        try:
            update_project(id, name, description)
            get_project_logger().info(
                'Project updated: id=%d name=%s', id, name
            )
            flash('Project updated successfully.', 'success')
            return redirect(url_for('projects.detail', id=id))
        except Exception as e:
            get_project_logger().error('Project update failed: %s', e)
            flash('Error updating project. Please try again.', 'danger')
    return render_template('edit_project.html', form=form, project=project)


@projects_bp.route('/<int:id>/members')
@login_required
def members(id):
    project = get_project_by_id(id)
    if not project:
        abort(404)
    if not is_project_owner(id, current_user.id):
        abort(403)
    member_list = get_project_members(id)
    form = MemberForm()
    return render_template('project_members.html', project=project, members=member_list, form=form)


@projects_bp.route('/<int:id>/members/add', methods=['POST'])
@login_required
def add_member_route(id):
    project = get_project_by_id(id)
    if not project:
        abort(404)
    if not is_project_owner(id, current_user.id):
        abort(403)
    form = MemberForm()
    if form.validate_on_submit():
        query = form.username_or_email.data.strip()
        user = fetch_one(
            'SELECT id, username, email FROM users WHERE username=%s OR email=%s',
            (query, query)
        )
        if not user:
            flash('User not found.', 'danger')
        elif user['id'] == current_user.id:
            flash('You are already the project owner.', 'warning')
        elif is_project_owner(id, user['id']):
            flash('User is already the project owner.', 'warning')
        else:
            added = add_member(id, user['id'])
            if added:
                get_project_logger().info(
                    'Member added: project=%d user=%d', id, user['id']
                )
                create_notification(
                    user['id'],
                    f'{current_user.username} added you to project: {project["name"]}'
                )
                try:
                    socketio.emit('member_added', {
                        'project_id': id,
                        'user_id': user['id'],
                        'username': user['username'],
                        'added_by': current_user.username
                    }, room=f'project_{id}')
                except Exception:
                    pass
                flash(f'{user["username"]} added to project.', 'success')
            else:
                flash('User already exists in project.', 'warning')
    return redirect(url_for('projects.members', id=id))


@projects_bp.route('/<int:id>/members/remove/<int:user_id>', methods=['POST'])
@login_required
def remove_member_route(id, user_id):
    project = get_project_by_id(id)
    if not project:
        abort(404)
    if not is_project_owner(id, current_user.id):
        abort(403)
    if user_id == current_user.id:
        flash('You cannot remove yourself as the project owner.', 'danger')
        return redirect(url_for('projects.members', id=id))
    remove_member(id, user_id)
    get_project_logger().info('Member removed: project=%d user=%d', id, user_id)
    flash('Member removed from project.', 'success')
    return redirect(url_for('projects.members', id=id))


@projects_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    project = get_project_by_id(id)
    if not project:
        abort(404)
    if project['owner_id'] != current_user.id:
        get_project_logger().warning(
            'Unauthorized delete attempt: user=%d project=%d', current_user.id, id
        )
        abort(403)
    try:
        delete_project(id)
        get_project_logger().info(
            'Project deleted: id=%d name=%s', id, project['name']
        )
        flash('Project deleted successfully.', 'success')
    except Exception as e:
        get_project_logger().error('Project deletion failed: %s', e)
        flash('Error deleting project.', 'danger')
    return redirect(url_for('projects.list_projects'))
