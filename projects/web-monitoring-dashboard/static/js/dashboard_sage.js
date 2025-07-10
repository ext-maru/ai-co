// AI Company Four Sages Dashboard JavaScript
const API_BASE = '/api';

// State management
const state = {
    currentSection: 'overview',
    quests: [],
    servants: [],
    wisdomChannels: [],
    sagesCouncil: {}
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
            case 'quests':
                await loadQuests();
                break;
            case 'servants':
                await loadServants();
                break;
            case 'wisdom-flow':
                await loadWisdomFlow();
                break;
            case 'four-sages':
                await loadSagesCouncil();
                break;
            case 'sage-administration':
                await loadAdministrationData();
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
            statusBadge.textContent = '評議会は健全に機能中';
            statusBadge.style.background = 'var(--success-color)';
        } else {
            statusBadge.textContent = '評議会に異変を感知';
            statusBadge.style.background = 'var(--error-color)';
        }
    } catch (error) {
        console.error('Error loading overview data:', error);
    }
}

// Quest management
async function loadQuests() {
    try {
        const response = await axios.get(`${API_BASE}/tasks`);
        state.quests = response.data.tasks || [];
        renderQuests();
    } catch (error) {
        console.error('Error loading quests:', error);
    }
}

function renderQuests() {
    const questList = document.getElementById('quest-list');
    const filterStatus = document.getElementById('quest-filter-status').value;
    const filterPriority = document.getElementById('quest-filter-priority').value;
    
    // Filter quests
    let filteredQuests = state.quests;
    if (filterStatus) {
        filteredQuests = filteredQuests.filter(quest => quest.status === filterStatus);
    }
    if (filterPriority) {
        filteredQuests = filteredQuests.filter(quest => quest.priority === filterPriority);
    }
    
    // Render quests
    questList.innerHTML = filteredQuests.map(quest => `
        <div class="quest-item" data-quest-id="${quest.id}">
            <div class="quest-info">
                <h4>${escapeHtml(quest.title)}</h4>
                <div class="quest-meta">
                    <span class="priority-badge priority-${quest.priority}">${getPriorityText(quest.priority)}</span>
                    <span>${getStatusText(quest.status)}</span>
                    <span>${quest.assignee || '修行者による選択'}</span>
                </div>
            </div>
            <div class="quest-actions">
                <button class="btn btn-sm" onclick="updateQuestStatus('${quest.id}', 'in_progress')">修行開始</button>
                <button class="btn btn-sm" onclick="updateQuestStatus('${quest.id}', 'completed')">悟得</button>
                <button class="btn btn-sm btn-danger" onclick="deleteQuest('${quest.id}')">破棄</button>
            </div>
        </div>
    `).join('');
}

// Servant monitoring
async function loadServants() {
    try {
        const response = await axios.get(`${API_BASE}/workers`);
        state.servants = response.data.workers || [];
        renderServants();
    } catch (error) {
        console.error('Error loading servants:', error);
    }
}

function renderServants() {
    const servantGrid = document.getElementById('servant-grid');
    
    servantGrid.innerHTML = state.servants.map(servant => `
        <div class="servant-card">
            <div class="servant-status">
                <div class="status-indicator status-${servant.status}"></div>
                <h3>${escapeHtml(servant.name)}</h3>
            </div>
            <p>従者ID: ${servant.pid}</p>
            <p>状態: ${getServantStatusText(servant.status)}</p>
            <p>指導中: ${servant.current_task || 'なし'}</p>
            <p>完了修行: ${servant.completed_tasks || 0}</p>
            <p>神力消費率: ${servant.cpu_usage || 0}%</p>
            <p>記憶の器: ${formatBytes(servant.memory_usage || 0)}</p>
        </div>
    `).join('');
}

// Wisdom flow monitoring
async function loadWisdomFlow() {
    try {
        const response = await axios.get(`${API_BASE}/queues`);
        state.wisdomChannels = response.data.queues || [];
        renderWisdomFlow();
    } catch (error) {
        console.error('Error loading wisdom flow:', error);
    }
}

function renderWisdomFlow() {
    const wisdomChannels = document.getElementById('wisdom-channels');
    
    wisdomChannels.innerHTML = state.wisdomChannels.map(channel => `
        <div class="wisdom-channel">
            <div class="channel-header">
                <h3>${escapeHtml(channel.name)}</h3>
                <span class="channel-type">${channel.durable ? '永続の流れ' : '一時の流れ'}</span>
            </div>
            <div class="channel-stats">
                <div class="channel-stat">
                    <div class="channel-stat-value">${channel.messages || 0}</div>
                    <div class="channel-stat-label">叡智の数</div>
                </div>
                <div class="channel-stat">
                    <div class="channel-stat-value">${channel.consumers || 0}</div>
                    <div class="channel-stat-label">受信者</div>
                </div>
                <div class="channel-stat">
                    <div class="channel-stat-value">${channel.publish_rate || 0}/秒</div>
                    <div class="channel-stat-label">送信速度</div>
                </div>
                <div class="channel-stat">
                    <div class="channel-stat-value">${channel.deliver_rate || 0}/秒</div>
                    <div class="channel-stat-label">配信速度</div>
                </div>
            </div>
        </div>
    `).join('');
}

// Four Sages Council monitoring
async function loadSagesCouncil() {
    try {
        const response = await axios.get(`${API_BASE}/elder/council`);
        state.sagesCouncil = response.data || {};
        renderSagesCouncil();
    } catch (error) {
        console.error('Error loading sages council:', error);
    }
}

function renderSagesCouncil() {
    // Update sage statuses
    const sages = ['knowledge-sage', 'task-oracle', 'crisis-sage', 'search-mystic'];
    
    sages.forEach(sage => {
        const statusElement = document.getElementById(`${sage}-status`);
        if (statusElement && state.sagesCouncil[sage]) {
            const sageData = state.sagesCouncil[sage];
            statusElement.textContent = sageData.status || '不明';
            statusElement.style.color = sageData.healthy ? 'var(--success-color)' : 'var(--error-color)';
        }
    });
    
    // Update efficiency metrics
    updateSageMetrics();
}

function updateSageMetrics() {
    // Knowledge Sage
    if (state.sagesCouncil['knowledge-sage']) {
        const efficiency = document.getElementById('knowledge-efficiency');
        if (efficiency) efficiency.textContent = '95%';
    }
    
    // Task Oracle
    if (state.sagesCouncil['task-oracle']) {
        const efficiency = document.getElementById('task-efficiency');
        const completed = document.getElementById('completed-quests');
        if (efficiency) efficiency.textContent = '88%';
        if (completed) completed.textContent = '12';
    }
    
    // Crisis Sage
    if (state.sagesCouncil['crisis-sage']) {
        const protection = document.getElementById('crisis-protection');
        const resolved = document.getElementById('resolved-incidents');
        if (protection) protection.textContent = '92%';
        if (resolved) resolved.textContent = '7';
    }
    
    // Search Mystic
    if (state.sagesCouncil['search-mystic']) {
        const accuracy = document.getElementById('search-accuracy');
        const discovery = document.getElementById('discovery-rate');
        if (accuracy) accuracy.textContent = '97%';
        if (discovery) discovery.textContent = '94%';
    }
}

// Quest creation modal
function initializeModals() {
    const modal = document.getElementById('quest-modal');
    const newQuestBtn = document.getElementById('new-quest-btn');
    const closeBtn = document.querySelector('.close');
    const questForm = document.getElementById('quest-form');
    
    if (newQuestBtn) {
        newQuestBtn.onclick = () => {
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
    
    if (questForm) {
        questForm.onsubmit = async (e) => {
            e.preventDefault();
            await createQuest();
        };
    }
}

// Create new quest
async function createQuest() {
    const formData = {
        title: document.getElementById('quest-title').value,
        description: document.getElementById('quest-description').value,
        priority: document.getElementById('quest-priority').value,
        assignee: document.getElementById('quest-assignee').value
    };
    
    try {
        await axios.post(`${API_BASE}/tasks`, formData);
        document.getElementById('quest-modal').style.display = 'none';
        document.getElementById('quest-form').reset();
        await loadQuests();
        showNotification('新たなる修行録を編纂いたしました', 'success');
    } catch (error) {
        console.error('Error creating quest:', error);
        showNotification('修行録の編纂に支障が生じました', 'error');
    }
}

// Update quest status
async function updateQuestStatus(questId, newStatus) {
    try {
        await axios.patch(`${API_BASE}/tasks/${questId}`, { status: newStatus });
        await loadQuests();
        showNotification('修行録を更新いたしました', 'success');
    } catch (error) {
        console.error('Error updating quest:', error);
        showNotification('修行録更新に支障が生じました', 'error');
    }
}

// Delete quest
async function deleteQuest(questId) {
    if (!confirm('この修行録を破棄いたしますか？')) {
        return;
    }
    
    try {
        await axios.delete(`${API_BASE}/tasks/${questId}`);
        await loadQuests();
        showNotification('修行録を破棄いたしました', 'success');
    } catch (error) {
        console.error('Error deleting quest:', error);
        showNotification('修行録破棄に支障が生じました', 'error');
    }
}

// Initialize filters
function initializeFilters() {
    const filterElements = document.querySelectorAll('.filter-select');
    filterElements.forEach(filter => {
        filter.addEventListener('change', renderQuests);
    });
}

// Administration functions
async function loadAdministrationData() {
    try {
        const response = await axios.get(`${API_BASE}/admin/users`);
        const members = response.data.users || [];
        renderSageMembers(members);
    } catch (error) {
        console.error('Error loading administration data:', error);
    }
}

function renderSageMembers(members) {
    const membersList = document.getElementById('sage-members-list');
    if (!membersList) return;
    
    membersList.innerHTML = members.map(member => `
        <div class="sage-member-item">
            <div>
                <strong>${escapeHtml(member.username)}賢者</strong>
                <span>(${member.role === 'admin' ? '最高位' : '評議員'})</span>
                <span>${member.email}</span>
            </div>
            <div>
                ${member.is_active ? 
                    `<button class="btn btn-sm" onclick="deactivateMember(${member.id})">退席</button>` :
                    `<button class="btn btn-sm" onclick="activateMember(${member.id})">復席</button>`
                }
            </div>
        </div>
    `).join('');
}

// Administration actions
document.getElementById('clear-sessions-btn')?.addEventListener('click', async () => {
    try {
        await axios.post(`${API_BASE}/admin/clear-sessions`);
        showNotification('古き記録を浄化いたしました', 'success');
    } catch (error) {
        showNotification('記録浄化に支障が生じました', 'error');
    }
});

document.getElementById('restart-servants-btn')?.addEventListener('click', async () => {
    if (!confirm('従者たちを再召喚いたしますか？')) return;
    
    try {
        await axios.post(`${API_BASE}/admin/restart-workers`);
        showNotification('従者たちを再召喚いたしました', 'success');
    } catch (error) {
        showNotification('従者再召喚に支障が生じました', 'error');
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
        high: '聖なる緊急',
        medium: '賢者推奨',
        low: '修行候補'
    };
    return map[priority] || priority;
}

function getStatusText(status) {
    const map = {
        pending: '待機中',
        in_progress: '修行中',
        completed: '悟得'
    };
    return map[status] || status;
}

function getServantStatusText(status) {
    const map = {
        active: '活動中',
        idle: '待機中',
        error: '異常'
    };
    return map[status] || status;
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Style the notification
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
        padding: 12px 24px;
        border-radius: 6px;
        font-weight: 500;
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    
    // Add to document
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);