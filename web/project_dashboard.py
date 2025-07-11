#!/usr/bin/env python3
"""
🏛️ エルダーズギルド プロジェクトダッシュボード
Redmineライクなプロジェクト管理Web UI
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# プロジェクトルート設定
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from flask import Flask, jsonify, redirect, render_template_string, request, url_for
from flask_cors import CORS

from libs.project_manager_elder import ElderGuildIntegration, ProjectManagerElder

app = Flask(__name__)
CORS(app)

# プロジェクトマネージャー初期化
pm = ProjectManagerElder()
guild = ElderGuildIntegration(pm)

# HTMLテンプレート
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🏛️ エルダーズギルド プロジェクト管理</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e4e4e7;
            line-height: 1.6;
            min-height: 100vh;
        }

        /* ヘッダー */
        .header {
            background: rgba(30, 30, 60, 0.8);
            padding: 1rem 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            position: sticky;
            top: 0;
            z-index: 100;
            backdrop-filter: blur(10px);
        }

        .header h1 {
            font-size: 1.8rem;
            background: linear-gradient(45deg, #9333ea, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        /* メインコンテナ */
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }

        /* グリッドレイアウト */
        .dashboard-grid {
            display: grid;
            grid-template-columns: 250px 1fr;
            gap: 2rem;
            margin-top: 2rem;
        }

        /* サイドバー */
        .sidebar {
            background: rgba(30, 30, 60, 0.5);
            border-radius: 12px;
            padding: 1.5rem;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }

        .sidebar h2 {
            font-size: 1.2rem;
            margin-bottom: 1rem;
            color: #c084fc;
        }

        .project-list {
            list-style: none;
        }

        .project-item {
            padding: 0.8rem 1rem;
            margin-bottom: 0.5rem;
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
            border: 1px solid transparent;
        }

        .project-item:hover {
            background: rgba(147, 51, 234, 0.2);
            border-color: #9333ea;
            transform: translateX(5px);
        }

        .project-item.active {
            background: rgba(147, 51, 234, 0.3);
            border-color: #c084fc;
        }

        /* メインコンテンツ */
        .main-content {
            background: rgba(30, 30, 60, 0.5);
            border-radius: 12px;
            padding: 2rem;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }

        /* タブ */
        .tabs {
            display: flex;
            gap: 1rem;
            margin-bottom: 2rem;
            border-bottom: 2px solid rgba(255,255,255,0.1);
        }

        .tab {
            padding: 0.8rem 1.5rem;
            background: none;
            border: none;
            color: #a1a1aa;
            cursor: pointer;
            font-size: 1rem;
            transition: all 0.3s ease;
            position: relative;
        }

        .tab:hover {
            color: #e4e4e7;
        }

        .tab.active {
            color: #c084fc;
        }

        .tab.active::after {
            content: '';
            position: absolute;
            bottom: -2px;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, #9333ea, #c084fc);
        }

        /* ガントチャート */
        .gantt-container {
            overflow-x: auto;
            margin-top: 2rem;
        }

        .gantt-chart {
            min-width: 1000px;
            position: relative;
        }

        .gantt-row {
            display: flex;
            align-items: center;
            padding: 0.5rem 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }

        .gantt-task-name {
            width: 300px;
            padding-right: 1rem;
            font-size: 0.9rem;
        }

        .gantt-timeline {
            flex: 1;
            position: relative;
            height: 30px;
        }

        .gantt-bar {
            position: absolute;
            height: 24px;
            background: linear-gradient(90deg, #9333ea, #c084fc);
            border-radius: 4px;
            display: flex;
            align-items: center;
            padding: 0 0.5rem;
            font-size: 0.8rem;
            white-space: nowrap;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        }

        /* タスクカード */
        .task-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1.5rem;
        }

        .task-card {
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
            padding: 1.5rem;
            border: 1px solid rgba(255,255,255,0.1);
            transition: all 0.3s ease;
            cursor: pointer;
        }

        .task-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(147, 51, 234, 0.3);
            border-color: #9333ea;
        }

        .task-header {
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 1rem;
        }

        .task-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: #e4e4e7;
        }

        .task-fantasy {
            font-size: 1.2rem;
        }

        .task-meta {
            display: flex;
            gap: 1rem;
            font-size: 0.85rem;
            color: #a1a1aa;
        }

        .task-status {
            padding: 0.2rem 0.8rem;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 500;
            background: rgba(255,255,255,0.1);
        }

        .status-pending { background: rgba(251, 191, 36, 0.2); color: #fbbf24; }
        .status-in_progress { background: rgba(59, 130, 246, 0.2); color: #3b82f6; }
        .status-completed { background: rgba(34, 197, 94, 0.2); color: #22c55e; }

        /* 統計カード */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .stat-card {
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
            padding: 1.5rem;
            border: 1px solid rgba(255,255,255,0.1);
            text-align: center;
        }

        .stat-value {
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(45deg, #9333ea, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .stat-label {
            font-size: 0.9rem;
            color: #a1a1aa;
            margin-top: 0.5rem;
        }

        /* 新規作成ボタン */
        .fab {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #9333ea, #c084fc);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            box-shadow: 0 5px 20px rgba(147, 51, 234, 0.5);
            transition: all 0.3s ease;
            font-size: 2rem;
            color: white;
            border: none;
        }

        .fab:hover {
            transform: scale(1.1);
            box-shadow: 0 8px 30px rgba(147, 51, 234, 0.7);
        }

        /* エルダー割り当て表示 */
        .elder-badge {
            display: inline-block;
            padding: 0.3rem 0.8rem;
            border-radius: 16px;
            font-size: 0.85rem;
            background: rgba(147, 51, 234, 0.2);
            color: #c084fc;
            margin-left: 0.5rem;
        }

        /* プログレスバー */
        .progress-bar {
            width: 100%;
            height: 8px;
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
            overflow: hidden;
            margin-top: 0.5rem;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #22c55e, #16a34a);
            transition: width 0.5s ease;
        }

        /* モーダル */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }

        .modal-content {
            background: #1a1a2e;
            border-radius: 12px;
            padding: 2rem;
            max-width: 600px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
            border: 1px solid rgba(147, 51, 234, 0.3);
        }

        .form-group {
            margin-bottom: 1.5rem;
        }

        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            color: #c084fc;
            font-weight: 500;
        }

        .form-group input,
        .form-group textarea,
        .form-group select {
            width: 100%;
            padding: 0.8rem;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            color: #e4e4e7;
            font-size: 1rem;
        }

        .form-group input:focus,
        .form-group textarea:focus,
        .form-group select:focus {
            outline: none;
            border-color: #9333ea;
            box-shadow: 0 0 0 3px rgba(147, 51, 234, 0.2);
        }

        .button-group {
            display: flex;
            gap: 1rem;
            margin-top: 2rem;
        }

        .btn {
            padding: 0.8rem 1.5rem;
            border-radius: 8px;
            border: none;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 500;
        }

        .btn-primary {
            background: linear-gradient(135deg, #9333ea, #c084fc);
            color: white;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(147, 51, 234, 0.4);
        }

        .btn-secondary {
            background: rgba(255,255,255,0.1);
            color: #e4e4e7;
        }

        .btn-secondary:hover {
            background: rgba(255,255,255,0.15);
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏛️ エルダーズギルド プロジェクト管理システム</h1>
    </div>

    <div class="container">
        <div class="dashboard-grid">
            <!-- サイドバー -->
            <aside class="sidebar">
                <h2>📋 プロジェクト一覧</h2>
                <ul class="project-list" id="projectList">
                    <!-- プロジェクトリストが動的に追加される -->
                </ul>
                <button class="btn btn-primary" style="width: 100%; margin-top: 1rem;" onclick="showNewProjectModal()">
                    ＋ 新規プロジェクト
                </button>
            </aside>

            <!-- メインコンテンツ -->
            <main class="main-content">
                <!-- タブ -->
                <div class="tabs">
                    <button class="tab active" onclick="switchTab('overview')">概要</button>
                    <button class="tab" onclick="switchTab('tasks')">タスク</button>
                    <button class="tab" onclick="switchTab('gantt')">ガントチャート</button>
                    <button class="tab" onclick="switchTab('milestones')">マイルストーン</button>
                    <button class="tab" onclick="switchTab('stats')">統計</button>
                </div>

                <!-- タブコンテンツ -->
                <div id="tabContent">
                    <!-- 動的に内容が追加される -->
                </div>
            </main>
        </div>
    </div>

    <!-- 新規タスク作成ボタン -->
    <button class="fab" onclick="showNewTaskModal()">＋</button>

    <!-- モーダル -->
    <div id="modal" class="modal">
        <div class="modal-content" id="modalContent">
            <!-- モーダル内容が動的に追加される -->
        </div>
    </div>

    <script>
        let currentProject = null;
        let currentTab = 'overview';

        // 初期化
        document.addEventListener('DOMContentLoaded', () => {
            loadProjects();
            setInterval(refreshData, 30000); // 30秒ごとに更新
        });

        // プロジェクト一覧の読み込み
        async function loadProjects() {
            try {
                const response = await fetch('/api/projects');
                const projects = await response.json();

                const listEl = document.getElementById('projectList');
                listEl.innerHTML = projects.map(p => `
                    <li class="project-item ${currentProject?.id === p.id ? 'active' : ''}"
                        onclick="selectProject(${p.id})">
                        <div>${p.fantasy_rank} ${p.name}</div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${p.progress}%"></div>
                        </div>
                    </li>
                `).join('');

                // 最初のプロジェクトを選択
                if (!currentProject && projects.length > 0) {
                    selectProject(projects[0].id);
                }
            } catch (error) {
                console.error('Failed to load projects:', error);
            }
        }

        // プロジェクト選択
        async function selectProject(projectId) {
            try {
                const response = await fetch(`/api/projects/${projectId}`);
                currentProject = await response.json();

                // サイドバーの選択状態を更新
                document.querySelectorAll('.project-item').forEach(item => {
                    item.classList.remove('active');
                });
                event.currentTarget.classList.add('active');

                // コンテンツを更新
                updateTabContent();
            } catch (error) {
                console.error('Failed to load project:', error);
            }
        }

        // タブ切り替え
        function switchTab(tabName) {
            currentTab = tabName;

            // タブのアクティブ状態を更新
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            event.currentTarget.classList.add('active');

            updateTabContent();
        }

        // タブコンテンツの更新
        function updateTabContent() {
            if (!currentProject) return;

            const contentEl = document.getElementById('tabContent');

            switch(currentTab) {
                case 'overview':
                    showOverview(contentEl);
                    break;
                case 'tasks':
                    showTasks(contentEl);
                    break;
                case 'gantt':
                    showGantt(contentEl);
                    break;
                case 'milestones':
                    showMilestones(contentEl);
                    break;
                case 'stats':
                    showStats(contentEl);
                    break;
            }
        }

        // 概要表示
        function showOverview(container) {
            container.innerHTML = `
                <div class="project-overview">
                    <h2>${currentProject.name} <span class="elder-badge">${currentProject.elder_assignment}</span></h2>
                    <p>${currentProject.description || 'プロジェクトの説明がありません'}</p>

                    <div class="stats-grid" style="margin-top: 2rem;">
                        <div class="stat-card">
                            <div class="stat-value">${currentProject.progress.toFixed(1)}%</div>
                            <div class="stat-label">進捗率</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${currentProject.task_count || 0}</div>
                            <div class="stat-label">タスク数</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${currentProject.milestone_count || 0}</div>
                            <div class="stat-label">マイルストーン</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${currentProject.days_remaining || '---'}</div>
                            <div class="stat-label">残り日数</div>
                        </div>
                    </div>

                    <h3 style="margin-top: 2rem;">最近のアクティビティ</h3>
                    <div id="recentActivity">
                        <!-- アクティビティが表示される -->
                    </div>
                </div>
            `;

            loadRecentActivity();
        }

        // タスク表示
        async function showTasks(container) {
            try {
                const response = await fetch(`/api/projects/${currentProject.id}/tasks`);
                const tasks = await response.json();

                container.innerHTML = `
                    <div class="task-grid">
                        ${tasks.map(task => `
                            <div class="task-card" onclick="showTaskDetail(${task.id})">
                                <div class="task-header">
                                    <div>
                                        <div class="task-title">${task.task_name}</div>
                                        <div class="task-fantasy">${task.fantasy_classification || '✨'}</div>
                                    </div>
                                    <div class="task-status status-${task.status}">${task.status}</div>
                                </div>
                                <div class="task-meta">
                                    <span>${task.assigned_team || '未割当'}</span>
                                    <span>優先度: ${task.priority}</span>
                                    <span>${task.estimated_hours || '---'}h</span>
                                </div>
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: ${task.completion_rate}%"></div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `;
            } catch (error) {
                console.error('Failed to load tasks:', error);
                container.innerHTML = '<p>タスクの読み込みに失敗しました</p>';
            }
        }

        // ガントチャート表示
        async function showGantt(container) {
            try {
                const response = await fetch(`/api/projects/${currentProject.id}/gantt`);
                const ganttData = await response.json();

                container.innerHTML = `
                    <div class="gantt-container">
                        <div class="gantt-chart">
                            ${renderGanttChart(ganttData)}
                        </div>
                    </div>
                `;
            } catch (error) {
                console.error('Failed to load gantt:', error);
                container.innerHTML = '<p>ガントチャートの読み込みに失敗しました</p>';
            }
        }

        // ガントチャートのレンダリング
        function renderGanttChart(data) {
            // 簡易的なガントチャート実装
            const startDate = new Date(data.project.start_date || new Date());
            const endDate = new Date(data.project.end_date || new Date(startDate.getTime() + 30 * 24 * 60 * 60 * 1000));
            const totalDays = Math.ceil((endDate - startDate) / (24 * 60 * 60 * 1000));

            let html = '<div class="gantt-rows">';

            // タスクをレンダリング
            data.tasks.forEach(task => {
                const taskStart = new Date(task.start_date || startDate);
                const taskEnd = new Date(task.due_date || taskStart);
                const startOffset = Math.ceil((taskStart - startDate) / (24 * 60 * 60 * 1000));
                const duration = Math.ceil((taskEnd - taskStart) / (24 * 60 * 60 * 1000));

                const leftPercent = (startOffset / totalDays) * 100;
                const widthPercent = (duration / totalDays) * 100;

                html += `
                    <div class="gantt-row">
                        <div class="gantt-task-name">${task.fantasy_classification} ${task.name}</div>
                        <div class="gantt-timeline">
                            <div class="gantt-bar" style="left: ${leftPercent}%; width: ${widthPercent}%;">
                                ${task.completion_rate}%
                            </div>
                        </div>
                    </div>
                `;
            });

            html += '</div>';
            return html;
        }

        // 統計表示
        async function showStats(container) {
            try {
                const response = await fetch('/api/stats');
                const stats = await response.json();

                container.innerHTML = `
                    <div>
                        <h3>システム全体統計</h3>
                        <div class="stats-grid">
                            <div class="stat-card">
                                <div class="stat-value">${stats.projects.total}</div>
                                <div class="stat-label">総プロジェクト数</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-value">${stats.tasks.total}</div>
                                <div class="stat-label">総タスク数</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-value">${stats.tasks.completed}</div>
                                <div class="stat-label">完了タスク</div>
                            </div>
                            <div class="stat-card">
                                <div class="stat-value">${stats.projects.avg_progress.toFixed(1)}%</div>
                                <div class="stat-label">平均進捗率</div>
                            </div>
                        </div>

                        <h3 style="margin-top: 2rem;">ファンタジー分類分布</h3>
                        <div>
                            ${stats.fantasy_distribution.map(([type, count]) => `
                                <div style="margin: 0.5rem 0;">
                                    <span>${type}</span>: <strong>${count}</strong>件
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            } catch (error) {
                console.error('Failed to load stats:', error);
                container.innerHTML = '<p>統計の読み込みに失敗しました</p>';
            }
        }

        // モーダル表示
        function showModal(content) {
            document.getElementById('modalContent').innerHTML = content;
            document.getElementById('modal').style.display = 'flex';
        }

        function closeModal() {
            document.getElementById('modal').style.display = 'none';
        }

        // 新規プロジェクトモーダル
        function showNewProjectModal() {
            showModal(`
                <h2>新規プロジェクト作成</h2>
                <form onsubmit="createProject(event)">
                    <div class="form-group">
                        <label>プロジェクト名</label>
                        <input type="text" name="name" required>
                    </div>
                    <div class="form-group">
                        <label>説明</label>
                        <textarea name="description" rows="3"></textarea>
                    </div>
                    <div class="form-group">
                        <label>ファンタジーランク</label>
                        <select name="fantasy_rank">
                            <option value="🏆 EPIC">🏆 EPIC (史詩級)</option>
                            <option value="⭐ HIGH" selected>⭐ HIGH (英雄級)</option>
                            <option value="🌟 MEDIUM">🌟 MEDIUM (冒険者級)</option>
                            <option value="✨ LOW">✨ LOW (見習い級)</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>開始日</label>
                        <input type="date" name="start_date">
                    </div>
                    <div class="form-group">
                        <label>終了予定日</label>
                        <input type="date" name="end_date">
                    </div>
                    <div class="button-group">
                        <button type="submit" class="btn btn-primary">作成</button>
                        <button type="button" class="btn btn-secondary" onclick="closeModal()">キャンセル</button>
                    </div>
                </form>
            `);
        }

        // 新規タスクモーダル
        function showNewTaskModal() {
            if (!currentProject) {
                alert('プロジェクトを選択してください');
                return;
            }

            showModal(`
                <h2>新規タスク作成</h2>
                <form onsubmit="createTask(event)">
                    <div class="form-group">
                        <label>タスク名</label>
                        <input type="text" name="task_name" required>
                    </div>
                    <div class="form-group">
                        <label>説明</label>
                        <textarea name="description" rows="3"></textarea>
                    </div>
                    <div class="form-group">
                        <label>カテゴリ</label>
                        <select name="category">
                            <option value="development">開発</option>
                            <option value="bug_fix">バグ修正</option>
                            <option value="research">調査</option>
                            <option value="documentation">ドキュメント</option>
                            <option value="testing">テスト</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>優先度 (1-10)</label>
                        <input type="number" name="priority" min="1" max="10" value="5">
                    </div>
                    <div class="form-group">
                        <label>見積工数（時間）</label>
                        <input type="number" name="estimated_hours" step="0.5" min="0">
                    </div>
                    <div class="form-group">
                        <label>担当チーム</label>
                        <select name="assigned_team">
                            <option value="">未割当</option>
                            <option value="🛡️ インシデント騎士団">🛡️ インシデント騎士団</option>
                            <option value="🔨 ドワーフ工房">🔨 ドワーフ工房</option>
                            <option value="🧙‍♂️ RAGウィザーズ">🧙‍♂️ RAGウィザーズ</option>
                            <option value="🧝‍♂️ エルフの森">🧝‍♂️ エルフの森</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>期限</label>
                        <input type="date" name="due_date">
                    </div>
                    <div class="button-group">
                        <button type="submit" class="btn btn-primary">作成</button>
                        <button type="button" class="btn btn-secondary" onclick="closeModal()">キャンセル</button>
                    </div>
                </form>
            `);
        }

        // プロジェクト作成
        async function createProject(event) {
            event.preventDefault();
            const formData = new FormData(event.target);

            try {
                const response = await fetch('/api/projects', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(Object.fromEntries(formData))
                });

                if (response.ok) {
                    closeModal();
                    loadProjects();
                } else {
                    alert('プロジェクトの作成に失敗しました');
                }
            } catch (error) {
                console.error('Failed to create project:', error);
                alert('エラーが発生しました');
            }
        }

        // タスク作成
        async function createTask(event) {
            event.preventDefault();
            const formData = new FormData(event.target);

            try {
                const response = await fetch(`/api/projects/${currentProject.id}/tasks`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(Object.fromEntries(formData))
                });

                if (response.ok) {
                    closeModal();
                    updateTabContent();
                } else {
                    alert('タスクの作成に失敗しました');
                }
            } catch (error) {
                console.error('Failed to create task:', error);
                alert('エラーが発生しました');
            }
        }

        // データの自動更新
        function refreshData() {
            if (currentProject) {
                updateTabContent();
            }
        }

        // モーダルの外側クリックで閉じる
        document.getElementById('modal').addEventListener('click', (e) => {
            if (e.target.id === 'modal') {
                closeModal();
            }
        });
    </script>
</body>
</html>
"""


# APIルート
@app.route("/")
def index():
    """ダッシュボードのメインページ"""
    return render_template_string(DASHBOARD_TEMPLATE)


@app.route("/api/projects", methods=["GET", "POST"])
def projects():
    """プロジェクト一覧の取得・作成"""
    if request.method == "GET":
        # プロジェクト一覧を取得
        conn = pm.db_path
        cursor = pm.db_path
        # 実際の実装では、データベースから取得
        projects = []
        return jsonify(projects)

    elif request.method == "POST":
        # 新規プロジェクト作成
        data = request.json
        project_id = pm.create_project(
            name=data["name"],
            description=data.get("description"),
            owner=data.get("owner", "Grand Elder maru"),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            fantasy_rank=data.get("fantasy_rank", "⭐ HIGH"),
        )
        return jsonify({"id": project_id, "status": "created"})


@app.route("/api/projects/<int:project_id>")
def get_project(project_id):
    """特定プロジェクトの詳細取得"""
    # 実装省略
    return jsonify(
        {"id": project_id, "name": "サンプルプロジェクト", "progress": 45.5, "elder_assignment": "🔨 ドワーフ工房"}
    )


@app.route("/api/projects/<int:project_id>/tasks", methods=["GET", "POST"])
def project_tasks(project_id):
    """プロジェクトのタスク一覧取得・作成"""
    if request.method == "GET":
        # タスク一覧を取得
        return jsonify([])

    elif request.method == "POST":
        # 新規タスク作成
        data = request.json
        task_id = pm.create_task(
            project_id=project_id,
            task_name=data["task_name"],
            category=data.get("category", "development"),
            description=data.get("description"),
            priority=int(data.get("priority", 5)),
            estimated_hours=float(data.get("estimated_hours", 0))
            if data.get("estimated_hours")
            else None,
            assigned_team=data.get("assigned_team"),
            due_date=data.get("due_date"),
        )
        return jsonify({"id": task_id, "status": "created"})


@app.route("/api/projects/<int:project_id>/gantt")
def project_gantt(project_id):
    """ガントチャートデータ取得"""
    gantt_data = pm.get_project_gantt_data(project_id)
    return jsonify(gantt_data)


@app.route("/api/stats")
def stats():
    """統計情報取得"""
    stats_data = pm.get_dashboard_stats()
    return jsonify(stats_data)


@app.route("/api/tasks/<int:task_id>/status", methods=["PUT"])
def update_task_status(task_id):
    """タスクステータス更新"""
    data = request.json
    success = pm.update_task_status(
        task_id=task_id,
        new_status=data["status"],
        comment=data.get("comment"),
        changed_by=data.get("changed_by", "Task Elder"),
    )
    return jsonify({"success": success})


if __name__ == "__main__":
    print("🏛️ エルダーズギルド プロジェクトダッシュボード起動中...")
    print("http://localhost:5000 でアクセスしてください")
    app.run(debug=True, host="0.0.0.0", port=5000)
