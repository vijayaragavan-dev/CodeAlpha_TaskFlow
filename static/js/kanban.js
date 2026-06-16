(function() {
    'use strict';

    var csrfToken = '';
    var csrfMeta = document.querySelector('meta[name="csrf-token"]');
    if (csrfMeta) {
        csrfToken = csrfMeta.getAttribute('content');
    }

    var kanbanBoard = document.getElementById('kanbanBoard');
    if (!kanbanBoard) return;

    function getCSRFToken() {
        if (csrfToken) return csrfToken;
        var meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.getAttribute('content') : '';
    }

    function showToast(message, type) {
        type = type || 'success';
        var container = document.getElementById('toastContainer');
        if (!container) return;

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
                    '<i class="bi ' + iconClass + ' me-2"></i>' + message +
                '</div>' +
                '<button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>' +
            '</div>';
        container.appendChild(toastEl);

        var bsToast = new bootstrap.Toast(toastEl, { delay: 3000 });
        bsToast.show();

        toastEl.addEventListener('hidden.bs.toast', function() {
            toastEl.remove();
        });
    }

    function updateColumnCounts() {
        document.querySelectorAll('.kanban-column').forEach(function(col) {
            var body = col.querySelector('.kanban-body');
            var countBadge = col.querySelector('.kanban-count');
            if (body && countBadge) {
                var count = body.querySelectorAll('.kanban-card').length;
                countBadge.textContent = count;
            }
        });
    }

    var dragSrcEl = null;

    function handleDragStart(e) {
        dragSrcEl = this;
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', this.dataset.taskId);
        this.classList.add('dragging');
        document.querySelectorAll('.kanban-body').forEach(function(body) {
            body.classList.add('drag-active');
        });
    }

    function handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        var body = this.closest('.kanban-body') || this;
        if (body.classList.contains('kanban-body')) {
            body.classList.add('drag-over');
        }
    }

    function handleDragLeave(e) {
        var body = this.closest('.kanban-body') || this;
        if (body.classList.contains('kanban-body')) {
            body.classList.remove('drag-over');
        }
    }

    function handleDrop(e) {
        e.preventDefault();
        var targetBody = this.closest('.kanban-body');
        if (!targetBody) return;

        targetBody.classList.remove('drag-over');

        if (!dragSrcEl) return;

        var taskId = dragSrcEl.dataset.taskId;
        var newStatus = targetBody.dataset.status;
        var oldStatus = dragSrcEl.dataset.taskStatus;

        if (oldStatus === newStatus) {
            dragSrcEl.classList.remove('dragging');
            document.querySelectorAll('.kanban-body').forEach(function(body) {
                body.classList.remove('drag-active');
            });
            dragSrcEl = null;
            return;
        }

        var card = dragSrcEl;
        card.dataset.taskStatus = newStatus;
        targetBody.appendChild(card);
        card.classList.remove('dragging');
        document.querySelectorAll('.kanban-body').forEach(function(body) {
            body.classList.remove('drag-active');
        });

        updateColumnCounts();

        showToast('Moving task to "' + newStatus + '"...', 'info');

        fetch('/tasks/' + taskId + '/move', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({ status: newStatus })
        })
        .then(function(response) {
            return response.json().then(function(data) {
                return { status: response.status, data: data };
            });
        })
        .then(function(result) {
            if (result.data.success) {
                showToast('Task moved to "' + newStatus + '"', 'success');
            } else {
                showToast(result.data.error || 'Failed to move task', 'danger');
                targetBody.removeChild(card);
                var srcBody = document.querySelector('.kanban-body[data-status="' + oldStatus + '"]');
                if (srcBody) {
                    srcBody.appendChild(card);
                    card.dataset.taskStatus = oldStatus;
                }
                updateColumnCounts();
            }
        })
        .catch(function() {
            showToast('Network error. Please try again.', 'danger');
            targetBody.removeChild(card);
            var srcBody = document.querySelector('.kanban-body[data-status="' + oldStatus + '"]');
            if (srcBody) {
                srcBody.appendChild(card);
                card.dataset.taskStatus = oldStatus;
            }
            updateColumnCounts();
        })
        .finally(function() {
            dragSrcEl = null;
        });
    }

    function handleDragEnd(e) {
        this.classList.remove('dragging');
        document.querySelectorAll('.kanban-body').forEach(function(body) {
            body.classList.remove('drag-active');
            body.classList.remove('drag-over');
        });
    }

    document.querySelectorAll('.kanban-card').forEach(function(card) {
        card.addEventListener('dragstart', handleDragStart);
        card.addEventListener('dragend', handleDragEnd);
    });

    document.querySelectorAll('.kanban-body').forEach(function(body) {
        body.addEventListener('dragover', handleDragOver);
        body.addEventListener('dragleave', handleDragLeave);
        body.addEventListener('drop', handleDrop);
    });

})();
