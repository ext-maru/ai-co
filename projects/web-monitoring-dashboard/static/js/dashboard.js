// AI Company Dashboard JavaScript
const API_BASE = '/api';

// State management
const state = {
    currentSection: 'overview',
    tasks: [],
    workers: [],
    queues: [],
    elderCouncil: {}
};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    initializeNavigation();
    initializeModals();
    initializeFilters();
    loadDashboardData();

    // Auto-refresh every 5 seconds
    setInterval(loadDashboardData, 5000);
});

// Navigation
function initializeNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const section = link.dataset.section;
            showSection(section);

            // Update active state
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
        });
    });
}

function showSection(sectionId) {
    const sections = document.querySelectorAll('.content-section');
    sections.forEach(section => {
        section.classList.remove('active');
    });

    const targetSection = document.getElementById(sectionId);
    if (targetSection) {
        targetSection.classList.add('active');
        state.currentSection = sectionId;
    }
}

// Load dashboard data
async function loadDashboardData() {
    try {
        // Load different data based on current section
        switch (state.currentSection) {
            case 'overview':
                await loadOverviewData();
                break;
            case 'tasks':
                await loadTasks();
                break;
            case 'workers':
                await loadWorkers();
                break;
            case 'queues':
                await loadQueues();
                break;
            case 'elder-council':
                await loadElderCouncil();
                break;
            case 'admin':
                await loadAdminData();
                break;
        }
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

// Overview data
async function loadOverviewData() {
    try {
        const response = await axios.get(`${API_BASE}/status`);
        const data = response.data;

        // Update stats
        document.getElementById('active-tasks').textContent = data.active_tasks || 0;
        document.getElementById('worker-utilization').textContent = `${data.worker_utilization || 0}%`;
        document.getElementById('queue-throughput').textContent = `${data.queue_throughput || 0}/分`;
        document.getElementById('uptime').textContent = formatUptime(data.uptime || 0);

        // Update system status
        const statusBadge = document.getElementById('system-status');
        if (data.system_healthy) {
            statusBadge.textContent = 'システム稼働中';
            statusBadge.style.background = 'var(--success-color)';
        } else {
            statusBadge.textContent = 'システム異常';
            statusBadge.style.background = 'var(--error-color)';
        }
    } catch (error) {
        console.error('Error loading overview data:', error);
    }
}

// Task management
async function loadTasks() {
    try {
        const response = await axios.get(`${API_BASE}/tasks`);
        state.tasks = response.data.tasks || [];
        renderTasks();
    } catch (error) {
        console.error('Error loading tasks:', error);
    }
}

function renderTasks() {
    const taskList = document.getElementById('task-list');
    const filterStatus = document.getElementById('task-filter-status').value;
    const filterPriority = document.getElementById('task-filter-priority').value;

    // Filter tasks
    let filteredTasks = state.tasks;
    if (filterStatus) {
        filteredTasks = filteredTasks.filter(task => task.status === filterStatus);
    }
    if (filterPriority) {
        filteredTasks = filteredTasks.filter(task => task.priority === filterPriority);
    }

    // Render tasks
    taskList.innerHTML = filteredTasks.map(task => `
        <div class="task-item" data-task-id="${task.id}">
            <div class="task-info">
                <h4>${escapeHtml(task.title)}</h4>
                <div class="task-meta">
                    <span class="priority-badge priority-${task.priority}">${getPriorityText(task.priority)}</span>
                    <span>${getStatusText(task.status)}</span>
                    <span>${task.assignee || '未割当'}</span>
                </div>
            </div>
            <div class="task-actions">
                <button class="btn btn-sm" onclick="updateTaskStatus('${task.id}', 'in_progress')">開始</button>
                <button class="btn btn-sm" onclick="updateTaskStatus('${task.id}', 'completed')">完了</button>
                <button class="btn btn-sm btn-danger" onclick="deleteTask('${task.id}')">削除</button>
            </div>
        </div>
    `).join('');
}

// Worker monitoring
async function loadWorkers() {
    try {
        const response = await axios.get(`${API_BASE}/workers`);
        state.workers = response.data.workers || [];
        renderWorkers();
    } catch (error) {
        console.error('Error loading workers:', error);
    }
}

function renderWorkers() {
    const workerGrid = document.getElementById('worker-grid');

    workerGrid.innerHTML = state.workers.map(worker => `
        <div class="worker-card">
            <div class="worker-status">
                <div class="status-indicator status-${worker.status}"></div>
                <h3>${escapeHtml(worker.name)}</h3>
            </div>
            <p>PID: ${worker.pid}</p>
            <p>状態: ${getWorkerStatusText(worker.status)}</p>
            <p>処理中: ${worker.current_task || 'なし'}</p>
            <p>完了タスク: ${worker.completed_tasks || 0}</p>
            <p>CPU使用率: ${worker.cpu_usage || 0}%</p>
            <p>メモリ: ${formatBytes(worker.memory_usage || 0)}</p>
        </div>
    `).join('');
}

// Queue monitoring
async function loadQueues() {
    try {
        const response = await axios.get(`${API_BASE}/queues`);
        state.queues = response.data.queues || [];
        renderQueues();
    } catch (error) {
        console.error('Error loading queues:', error);
    }
}

function renderQueues() {
    const queueList = document.getElementById('queue-list');

    queueList.innerHTML = state.queues.map(queue => `
        <div class="queue-item">
            <div class="queue-header">
                <h3>${escapeHtml(queue.name)}</h3>
                <span class="queue-type">${queue.durable ? '永続' : '一時'}</span>
            </div>
            <div class="queue-stats">
                <div class="queue-stat">
                    <div class="queue-stat-value">${queue.messages || 0}</div>
                    <div class="queue-stat-label">メッセージ</div>
                </div>
                <div class="queue-stat">
                    <div class="queue-stat-value">${queue.consumers || 0}</div>
                    <div class="queue-stat-label">コンシューマー</div>
                </div>
                <div class="queue-stat">
                    <div class="queue-stat-value">${queue.publish_rate || 0}/s</div>
                    <div class="queue-stat-label">送信レート</div>
                </div>
                <div class="queue-stat">
                    <div class="queue-stat-value">${queue.deliver_rate || 0}/s</div>
                    <div class="queue-stat-label">配信レート</div>
                </div>
            </div>
        </div>
    `).join('');
}

// Elder Council monitoring
async function loadElderCouncil() {
    try {
        const response = await axios.get(`${API_BASE}/elder/council`);
        state.elderCouncil = response.data || {};
        renderElderCouncil();
    } catch (error) {
        console.error('Error loading elder council:', error);
    }
}

function renderElderCouncil() {
    // Update elder statuses
    const elders = ['knowledge-sage', 'task-oracle', 'crisis-sage', 'search-mystic'];

    elders.forEach(elder => {
        const statusElement = document.getElementById(`${elder}-status`);
        if (statusElement && state.elderCouncil[elder]) {
            const elderData = state.elderCouncil[elder];
            statusElement.textContent = elderData.status || '不明';
            statusElement.style.color = elderData.healthy ? 'var(--success-color)' : 'var(--error-color)';
        }
    });
}

// Task creation modal
function initializeModals() {
    const modal = document.getElementById('task-modal');
    const newTaskBtn = document.getElementById('new-task-btn');
    const closeBtn = document.querySelector('.close');
    const taskForm = document.getElementById('task-form');

    if (newTaskBtn) {
        newTaskBtn.onclick = () => {
            modal.style.display = 'block';
        };
    }

    if (closeBtn) {
        closeBtn.onclick = () => {
            modal.style.display = 'none';
        };
    }

    window.onclick = (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    };

    if (taskForm) {
        taskForm.onsubmit = async (e) => {
            e.preventDefault();
            await createTask();
        };
    }
}

// Create new task
async function createTask() {
    const formData = {
        title: document.getElementById('task-title').value,
        description: document.getElementById('task-description').value,
        priority: document.getElementById('task-priority').value,
        assignee: document.getElementById('task-assignee').value
    };

    try {
        await axios.post(`${API_BASE}/tasks`, formData);
        document.getElementById('task-modal').style.display = 'none';
        document.getElementById('task-form').reset();
        await loadTasks();
        showNotification('タスクを作成しました', 'success');
    } catch (error) {
        console.error('Error creating task:', error);
        showNotification('タスク作成に失敗しました', 'error');
    }
}

// Update task status
async function updateTaskStatus(taskId, newStatus) {
    try {
        await axios.patch(`${API_BASE}/tasks/${taskId}`, { status: newStatus });
        await loadTasks();
        showNotification('タスクを更新しました', 'success');
    } catch (error) {
        console.error('Error updating task:', error);
        showNotification('タスク更新に失敗しました', 'error');
    }
}

// Delete task
async function deleteTask(taskId) {
    if (!confirm('このタスクを削除しますか？')) {
        return;
    }

    try {
        await axios.delete(`${API_BASE}/tasks/${taskId}`);
        await loadTasks();
        showNotification('タスクを削除しました', 'success');
    } catch (error) {
        console.error('Error deleting task:', error);
        showNotification('タスク削除に失敗しました', 'error');
    }
}

// Initialize filters
function initializeFilters() {
    const filterElements = document.querySelectorAll('.filter-select');
    filterElements.forEach(filter => {
        filter.addEventListener('change', renderTasks);
    });
}

// Admin functions
async function loadAdminData() {
    try {
        const response = await axios.get(`${API_BASE}/admin/users`);
        const users = response.data.users || [];
        renderUserList(users);
    } catch (error) {
        console.error('Error loading admin data:', error);
    }
}

function renderUserList(users) {
    const userList = document.getElementById('user-list');
    if (!userList) return;

    userList.innerHTML = users.map(user => `
        <div class="user-item">
            <div>
                <strong>${escapeHtml(user.username)}</strong>
                <span>(${user.role})</span>
                <span>${user.email}</span>
            </div>
            <div>
                ${user.is_active ?
                    `<button class="btn btn-sm" onclick="deactivateUser(${user.id})">無効化</button>` :
                    `<button class="btn btn-sm" onclick="activateUser(${user.id})">有効化</button>`
                }
            </div>
        </div>
    `).join('');
}

// Admin actions
document.getElementById('clear-sessions-btn')?.addEventListener('click', async () => {
    try {
        await axios.post(`${API_BASE}/admin/clear-sessions`);
        showNotification('期限切れセッションをクリアしました', 'success');
    } catch (error) {
        showNotification('セッションクリアに失敗しました', 'error');
    }
});

document.getElementById('restart-workers-btn')?.addEventListener('click', async () => {
    if (!confirm('ワーカーを再起動しますか？')) return;

    try {
        await axios.post(`${API_BASE}/admin/restart-workers`);
        showNotification('ワーカーを再起動しました', 'success');
    } catch (error) {
        showNotification('ワーカー再起動に失敗しました', 'error');
    }
});

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatUptime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}時間${minutes}分`;
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function getPriorityText(priority) {
    const map = {
        high: '高',
        medium: '中',
        low: '低'
    };
    return map[priority] || priority;
}

function getStatusText(status) {
    const map = {
        pending: '保留中',
        in_progress: '進行中',
        completed: '完了'
    };
    return map[status] || status;
}

function getWorkerStatusText(status) {
    const map = {
        active: '稼働中',
        idle: '待機中',
        error: 'エラー'
    };
    return map[status] || status;
}

function showNotification(message, type = 'info') {
    // TODO: Implement toast notification
    console.log(`[${type}] ${message}`);
}
