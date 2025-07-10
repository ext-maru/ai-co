'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { ListChecks, LayoutGrid, TrendingUp, Flag, Plus, Filter, Settings } from 'lucide-react'
import { KanbanBoard } from '@/components/sages/task/KanbanBoard'
import { ProjectDashboard } from '@/components/sages/task/ProjectDashboard'
import { ProgressTracker } from '@/components/sages/task/ProgressTracker'
import { PriorityManager } from '@/components/sages/task/PriorityManager'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { cn } from '@/lib/utils'

// Sample data
const sampleTasks = [
  {
    id: '1',
    title: 'API認証システムの実装',
    description: 'JWT基づいた認証システムを実装し、全エンドポイントに適用する',
    status: 'in_progress' as const,
    priority: 'high' as const,
    assignee: {
      id: '1',
      name: '山田太郎',
      avatar: '/avatars/yamada.jpg'
    },
    tags: ['backend', 'security', 'api'],
    dueDate: '2024-01-20T00:00:00Z',
    createdAt: '2024-01-10T00:00:00Z',
    estimatedHours: 24,
    completedHours: 16
  },
  {
    id: '2',
    title: 'ダッシュボードUIの改善',
    description: 'ユーザビリティテストの結果を基にダッシュボードを再設計',
    status: 'todo' as const,
    priority: 'medium' as const,
    assignee: {
      id: '2',
      name: '佐藤花子',
      avatar: '/avatars/sato.jpg'
    },
    tags: ['frontend', 'ui/ux', 'dashboard'],
    dueDate: '2024-01-25T00:00:00Z',
    createdAt: '2024-01-12T00:00:00Z',
    estimatedHours: 16,
    completedHours: 0
  },
  {
    id: '3',
    title: 'パフォーマンス最適化',
    description: 'データベースクエリの最適化とキャッシング戦略の実装',
    status: 'review' as const,
    priority: 'urgent' as const,
    assignee: {
      id: '3',
      name: '鈴木一郎',
      avatar: '/avatars/suzuki.jpg'
    },
    tags: ['performance', 'database', 'optimization'],
    dueDate: '2024-01-18T00:00:00Z',
    createdAt: '2024-01-05T00:00:00Z',
    estimatedHours: 32,
    completedHours: 30
  }
]

const sampleProjects = [
  {
    id: '1',
    name: 'AI Company Platform v2.0',
    description: '次世代AIプラットフォームの開発。4賢者システムの完全統合を目指す',
    status: 'active' as const,
    priority: 'high' as const,
    startDate: '2024-01-01T00:00:00Z',
    endDate: '2024-03-31T00:00:00Z',
    progress: 65,
    team: [
      { id: '1', name: '山田太郎', avatar: '/avatars/yamada.jpg', role: 'プロジェクトリーダー' },
      { id: '2', name: '佐藤花子', avatar: '/avatars/sato.jpg', role: 'フロントエンド開発' },
      { id: '3', name: '鈴木一郎', avatar: '/avatars/suzuki.jpg', role: 'バックエンド開発' }
    ],
    tasks: {
      total: 48,
      completed: 31,
      inProgress: 12,
      todo: 5
    },
    milestones: [
      { id: 'm1', name: 'Phase 1 完了', date: '2024-01-31T00:00:00Z', completed: true },
      { id: 'm2', name: 'Phase 2 完了', date: '2024-02-29T00:00:00Z', completed: false },
      { id: 'm3', name: 'リリース', date: '2024-03-31T00:00:00Z', completed: false }
    ],
    budget: {
      allocated: 5000000,
      spent: 3250000,
      currency: '¥'
    },
    risks: [
      { id: 'r1', title: 'スケジュール遅延リスク', severity: 'medium' as const, status: 'open' as const },
      { id: 'r2', title: '技術的負債', severity: 'low' as const, status: 'mitigated' as const }
    ]
  }
]

const samplePriorityItems = [
  {
    id: 'p1',
    title: 'セキュリティ監査の実施',
    description: '外部セキュリティ専門家によるコード監査とペネトレーションテスト',
    priority: 'urgent' as const,
    impact: 'critical' as const,
    effort: 'large' as const,
    status: 'in_progress' as const,
    assignee: { id: '1', name: '山田太郎', avatar: '/avatars/yamada.jpg' },
    deadline: '2024-01-20T00:00:00Z',
    dependencies: [],
    score: 95
  },
  {
    id: 'p2',
    title: 'ユーザードキュメントの更新',
    description: 'API仕様書とユーザーガイドの最新化',
    priority: 'medium' as const,
    impact: 'medium' as const,
    effort: 'medium' as const,
    status: 'pending' as const,
    deadline: '2024-01-30T00:00:00Z',
    dependencies: ['p1'],
    score: 60
  }
]

const sampleMetrics = [
  { label: 'タスク完了', value: 31, target: 48, unit: '件', trend: 'up' as const, change: 12 },
  { label: '開発速度', value: 24, target: 20, unit: 'ポイント/週', trend: 'up' as const, change: 8 },
  { label: 'バグ修正', value: 15, target: 20, unit: '件', trend: 'down' as const, change: -5 },
  { label: 'コードレビュー', value: 89, target: 95, unit: '%', trend: 'stable' as const, change: 0 },
  { label: 'テストカバレッジ', value: 78, target: 85, unit: '%', trend: 'up' as const, change: 3 },
  { label: 'デプロイ頻度', value: 4, target: 5, unit: '回/週', trend: 'stable' as const, change: 0 }
]

const sampleTimeline = [
  {
    id: 't1',
    date: '2024-01-15T10:00:00Z',
    type: 'milestone' as const,
    title: 'Phase 1 完了',
    description: '基本機能の実装が完了し、初期テストを開始',
    impact: 'positive' as const,
    progress: 100
  },
  {
    id: 't2',
    date: '2024-01-14T15:00:00Z',
    type: 'task' as const,
    title: 'API認証システム実装開始',
    progress: 67
  },
  {
    id: 't3',
    date: '2024-01-13T09:00:00Z',
    type: 'risk' as const,
    title: 'パフォーマンス問題を検出',
    description: 'データベースクエリの最適化が必要',
    impact: 'negative' as const
  }
]

export default function TaskSagePage() {
  const [activeView, setActiveView] = useState<'kanban' | 'projects' | 'progress' | 'priority'>('kanban')

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-goldenrod-600 rounded-full flex items-center justify-center text-2xl shadow-lg">
                  📋
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">タスク賢者</h1>
                  <p className="text-sm text-goldenrod-600">Task Oracle</p>
                </div>
              </div>
              <Badge variant="secondary" className="bg-goldenrod-100 text-goldenrod-800">
                <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse" />
                Active
              </Badge>
            </div>
            
            <div className="flex items-center space-x-3">
              <Button variant="outline" size="sm">
                <Filter className="w-4 h-4 mr-2" />
                フィルター
              </Button>
              <Button variant="outline" size="sm">
                <Plus className="w-4 h-4 mr-2" />
                新規タスク
              </Button>
              <Button variant="ghost" size="sm">
                <Settings className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </motion.header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Card className="p-6 bg-gradient-to-br from-goldenrod-50 to-white border-goldenrod-200">
              <div className="flex items-center justify-between mb-2">
                <ListChecks className="w-8 h-8 text-goldenrod-600" />
                <TrendingUp className="w-5 h-5 text-green-500" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900">156</h3>
              <p className="text-sm text-gray-600">アクティブタスク</p>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card className="p-6 bg-gradient-to-br from-blue-50 to-white border-blue-200">
              <div className="flex items-center justify-between mb-2">
                <LayoutGrid className="w-8 h-8 text-blue-600" />
                <span className="text-sm font-medium text-blue-600">+23%</span>
              </div>
              <h3 className="text-2xl font-bold text-gray-900">12</h3>
              <p className="text-sm text-gray-600">進行中プロジェクト</p>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Card className="p-6 bg-gradient-to-br from-green-50 to-white border-green-200">
              <div className="flex items-center justify-between mb-2">
                <TrendingUp className="w-8 h-8 text-green-600" />
                <Badge variant="secondary" className="text-xs">今週</Badge>
              </div>
              <h3 className="text-2xl font-bold text-gray-900">89%</h3>
              <p className="text-sm text-gray-600">完了率</p>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <Card className="p-6 bg-gradient-to-br from-red-50 to-white border-red-200">
              <div className="flex items-center justify-between mb-2">
                <Flag className="w-8 h-8 text-red-600" />
                <span className="text-sm font-medium text-red-600">要対応</span>
              </div>
              <h3 className="text-2xl font-bold text-gray-900">7</h3>
              <p className="text-sm text-gray-600">緊急タスク</p>
            </Card>
          </motion.div>
        </div>

        {/* View Tabs */}
        <div className="mb-8">
          <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg w-fit">
            {[
              { id: 'kanban', label: 'カンバンボード', icon: LayoutGrid },
              { id: 'projects', label: 'プロジェクト', icon: ListChecks },
              { id: 'progress', label: '進捗トラッキング', icon: TrendingUp },
              { id: 'priority', label: '優先度管理', icon: Flag }
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveView(id as any)}
                className={cn(
                  'px-4 py-2 rounded-md flex items-center space-x-2 transition-all duration-200',
                  activeView === id
                    ? 'bg-white text-goldenrod-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                )}
              >
                <Icon className="w-4 h-4" />
                <span className="text-sm font-medium">{label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Active View Content */}
        <motion.div
          key={activeView}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {activeView === 'kanban' && (
            <KanbanBoard
              tasks={sampleTasks}
              onTaskUpdate={(task) => console.log('Task updated:', task)}
              onTaskCreate={(status) => console.log('Create task with status:', status)}
            />
          )}
          
          {activeView === 'projects' && (
            <ProjectDashboard
              projects={sampleProjects}
              onProjectSelect={(project) => console.log('Selected project:', project)}
            />
          )}
          
          {activeView === 'progress' && (
            <ProgressTracker
              projectId="1"
              currentProgress={65}
              targetProgress={70}
              startDate="2024-01-01T00:00:00Z"
              endDate="2024-03-31T00:00:00Z"
              metrics={sampleMetrics}
              timeline={sampleTimeline}
            />
          )}
          
          {activeView === 'priority' && (
            <PriorityManager
              items={samplePriorityItems}
              onItemUpdate={(item) => console.log('Item updated:', item)}
              onPriorityChange={(id, priority) => console.log('Priority changed:', id, priority)}
            />
          )}
        </motion.div>
      </main>
    </div>
  )
}