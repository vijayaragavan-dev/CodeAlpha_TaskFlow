(function() {
    'use strict';

    var socket = null;
    var csrfToken = '';
    var csrfMeta = document.querySelector('meta[name="csrf-token"]');
    if (csrfMeta) {
        csrfToken = csrfMeta.getAttribute('content');
    }

    var connected = false;
    var reconnectAttempts = 0;
    var maxReconnectAttempts = 20;

    function initSocket() {
        if (socket && socket.connected) return;

        socket = io({
            reconnection: true,
            reconnectionAttempts: maxReconnectAttempts,
            reconnectionDelay: 1000,
            reconnectionDelayMax: 30000,
            randomizationFactor: 0.5,
            timeout: 10000
        });

        socket.on('connect', function() {
            connected = true;
            reconnectAttempts = 0;
            console.log('[SocketIO] Connected:', socket.id);

            var projectId = getProjectId();
            if (projectId) {
                socket.emit('join_project', { project_id: projectId });
            }
        });

        socket.on('disconnect', function(reason) {
            connected = false;
            console.log('[SocketIO] Disconnected:', reason);
        });

        socket.on('connect_error', function(error) {
            reconnectAttempts++;
            console.warn('[SocketIO] Connection error:', error.message);
        });

        socket.on('reconnect', function(attemptNumber) {
            connected = true;
            console.log('[SocketIO] Reconnected after', attemptNumber, 'attempts');

            var projectId = getProjectId();
            if (projectId) {
                socket.emit('join_project', { project_id: projectId });
            }
        });

        socket.on('reconnect_attempt', function(attemptNumber) {
            console.log('[SocketIO] Reconnect attempt:', attemptNumber);
        });

        socket.on('reconnect_error', function(error) {
            console.warn('[SocketIO] Reconnect error:', error.message);
        });

        socket.on('reconnect_failed', function() {
            console.error('[SocketIO] Reconnect failed after', maxReconnectAttempts, 'attempts');
        });

        socket.on('notification_event', function(data) {
            showToast(data.message || 'New notification', 'info');
            updateUnreadBadge();
        });

        socket.on('task_moved', function(data) {
            handleTaskMoved(data);
            showToast('Task "' + (data.title || '') + '" moved to ' + data.status, 'success');
        });

        socket.on('comment_added', function(data) {
            handleCommentAdded(data);
        });

        socket.on('member_added', function(data) {
            handleMemberAdded(data);
            showToast(data.added_by + ' added ' + (data.username || 'a member'), 'info');
        });

        socket.on('dashboard_update', function(data) {
            handleDashboardUpdate(data);
        });
    }

    function getProjectId() {
        var el = document.getElementById('socket-project-id');
        if (el) return parseInt(el.getAttribute('data-project-id'), 10);
        var kanbanBoard = document.getElementById('kanbanBoard');
        if (kanbanBoard) return parseInt(kanbanBoard.getAttribute('data-project-id'), 10);
        return null;
    }

    function handleTaskMoved(data) {
        var kanbanBoard = document.getElementById('kanbanBoard');
        if (!kanbanBoard) return;

        if (data.user_id && data.user_id === getCurrentUserId()) return;

        var card = document.querySelector('.kanban-card[data-task-id="' + data.task_id + '"]');
        if (!card) return;

        var oldStatus = card.dataset.taskStatus;
        if (oldStatus === data.status) return;

        card.dataset.taskStatus = data.status;
        var newColumnBody = document.querySelector('.kanban-body[data-status="' + data.status + '"]');
        if (newColumnBody) {
            newColumnBody.appendChild(card);
            updateColumnCounts();
        }
    }

    function handleCommentAdded(data) {
        var commentList = document.querySelector('.comment-list');
        if (!commentList) return;

        if (data.user_id && data.user_id === getCurrentUserId()) return;

        var avatarLetter = data.username ? data.username.charAt(0).toUpperCase() : '?';
        var escapedComment = escapeHtml(data.comment || '');
        var escapedUsername = escapeHtml(data.username || '');

        var commentHtml =
            '<div class="comment-card">' +
                '<div class="comment-header">' +
                    '<div class="comment-avatar">' + avatarLetter + '</div>' +
                    '<div class="comment-meta">' +
                        '<strong>' + escapedUsername + '</strong>' +
                        '<span class="comment-time">Just now</span>' +
                    '</div>' +
                '</div>' +
                '<div class="comment-body">' + escapedComment + '</div>' +
            '</div>';

        commentList.insertAdjacentHTML('beforeend', commentHtml);

        var countEl = document.getElementById('commentCount');
        if (countEl) {
            var current = parseInt(countEl.textContent, 10) || 0;
            countEl.textContent = current + 1;
        }

        var emptyMsg = document.querySelector('.comment-list ~ .text-center');
        if (emptyMsg) emptyMsg.style.display = 'none';
    }

    function handleMemberAdded(data) {
        var memberList = document.getElementById('memberList');
        if (!memberList) return;

        if (data.user_id && data.user_id === getCurrentUserId()) return;

        var avatarLetter = data.username ? data.username.charAt(0).toUpperCase() : '?';
        var escapedUsername = escapeHtml(data.username || '');

        var memberHtml =
            '<div class="list-group-item d-flex justify-content-between align-items-center member-item" data-user-id="' + data.user_id + '">' +
                '<div class="d-flex align-items-center gap-2">' +
                    '<div class="avatar bg-primary text-white">' + avatarLetter + '</div>' +
                    '<span>' + escapedUsername + '</span>' +
                '</div>' +
            '</div>';

        memberList.insertAdjacentHTML('beforeend', memberHtml);
    }

    function handleDashboardUpdate(data) {
        if (data.projects !== undefined) {
            var el = document.getElementById('stat-projects');
            if (el) el.textContent = data.projects;
        }
        if (data.tasks !== undefined) {
            var el = document.getElementById('stat-tasks');
            if (el) el.textContent = data.tasks;
        }
        if (data.completed !== undefined) {
            var el = document.getElementById('stat-completed');
            if (el) el.textContent = data.completed;
        }
        if (data.pending !== undefined) {
            var el = document.getElementById('stat-pending');
            if (el) el.textContent = data.pending;
        }
        if (data.due_today !== undefined) {
            var el = document.getElementById('stat-due-today');
            if (el) el.textContent = data.due_today;
        }
    }

    function updateUnreadBadge() {
        fetch('/notifications/unread-count')
            .then(function(r) { return r.json(); })
            .then(function(data) {
                var count = data.count || 0;
                var badges = document.querySelectorAll('.notification-badge, .sidebar .badge.bg-danger');
                badges.forEach(function(badge) {
                    badge.textContent = count;
                    if (count > 0) {
                        badge.style.display = 'inline';
                    } else {
                        badge.style.display = 'none';
                    }
                });
                var navbarBadge = document.querySelector('a[href*="notifications"] .badge');
                if (navbarBadge) {
                    navbarBadge.textContent = count;
                    if (count > 0) {
                        navbarBadge.style.display = 'inline';
                    } else {
                        navbarBadge.style.display = 'none';
                    }
                }
            })
            .catch(function() {});
    }

    function updateColumnCounts() {
        document.querySelectorAll('.kanban-column').forEach(function(col) {
            var body = col.querySelector('.kanban-body');
            var countBadge = col.querySelector('.kanban-count');
            if (body && countBadge) {
                countBadge.textContent = body.querySelectorAll('.kanban-card').length;
            }
        });
    }

    function showToast(message, type) {
        type = type || 'success';
        var container = document.getElementById('toastContainer');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            container.id = 'toastContainer';
            document.body.appendChild(container);
        }

        var icons = {
            'success': 'bi-check-circle-fill text-success',
            'danger': 'bi-x-circle-fill text-danger',
            'warning': 'bi-exclamation-triangle-fill text-warning',
            'info': 'bi-info-circle-fill text-info'
        };
        var iconClass = icons[type] || icons['info'];
        var bgClass = 'bg-' + type;

        var toastEl = document.createElement('div');
        toastEl.className = 'toast align-items-center text-white border-0 ' + bgClass;
        toastEl.setAttribute('role', 'alert');
        toastEl.setAttribute('aria-live', 'assertive');
        toastEl.setAttribute('aria-atomic', 'true');
        toastEl.innerHTML =
            '<div class="d-flex">' +
                '<div class="toast-body">' +
                    '<i class="bi ' + iconClass + ' me-2"></i>' + escapeHtml(message) +
                '</div>' +
                '<button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>' +
            '</div>';
        container.appendChild(toastEl);

        var bsToast = new bootstrap.Toast(toastEl, { delay: 5000 });
        bsToast.show();

        toastEl.addEventListener('hidden.bs.toast', function() {
            toastEl.remove();
        });
    }

    function getCurrentUserId() {
        var el = document.getElementById('current-user-id');
        return el ? parseInt(el.getAttribute('data-user-id'), 10) : null;
    }

    function escapeHtml(str) {
        if (!str) return '';
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }

    document.addEventListener('DOMContentLoaded', function() {
        if (document.querySelector('meta[name="csrf-token"]')) {
            initSocket();
        }
    });

    window.TaskFlowSocket = {
        init: initSocket,
        getSocket: function() { return socket; },
        isConnected: function() { return connected; },
        showToast: showToast
    };

})();
