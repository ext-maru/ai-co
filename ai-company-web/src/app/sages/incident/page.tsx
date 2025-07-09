'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Shield, AlertTriangle, Activity, Zap, Plus, Settings } from 'lucide-react'
import { MonitoringDashboard } from '@/components/sages/incident/MonitoringDashboard'
import { AlertManager } from '@/components/sages/incident/AlertManager'
import { IncidentHistory } from '@/components/sages/incident/IncidentHistory'
import { AutoResponseStatus } from '@/components/sages/incident/AutoResponseStatus'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { cn } from '@/lib/utils'

// Sample data
const sampleMetrics = [
  {
    id: '1',
    name: 'CPU使用率',
    value: 78,
    unit: '%',
    status: 'warning' as const,
    trend: 'up' as const,
    threshold: { warning: 70, critical: 90 },
    history: Array.from({ length: 20 }, (_, i) => ({
      time: new Date(Date.now() - i * 60000).toISOString(),
      value: 60 + Math.random() * 30
    }))
  },
  {
    id: '2',
    name: 'メモリ使用率',
    value: 45,
    unit: '%',
    status: 'normal' as const,
    trend: 'stable' as const,
    threshold: { warning: 80, critical: 95 },
    history: Array.from({ length: 20 }, (_, i) => ({
      time: new Date(Date.now() - i * 60000).toISOString(),
      value: 40 + Math.random() * 20
    }))
  },
  {
    id: '3',
    name: 'ネットワーク遅延',
    value: 245,
    unit: 'ms',
    status: 'critical' as const,
    trend: 'up' as const,
    threshold: { warning: 100, critical: 200 },
    history: Array.from({ length: 20 }, (_, i) => ({
      time: new Date(Date.now() - i * 60000).toISOString(),
      value: 80 + Math.random() * 200
    }))
  },
  {
    id: '4',
    name: 'ディスク使用率',
    value: 67,
    unit: '%',
    status: 'normal' as const,
    trend: 'down' as const,
    threshold: { warning: 80, critical: 95 },
    history: Array.from({ length: 20 }, (_, i) => ({
      time: new Date(Date.now() - i * 60000).toISOString(),
      value: 65 + Math.random() * 10
    }))
  }
]

const sampleServices = [
  {
    id: '1',
    name: 'API Gateway',
    status: 'operational' as const,
    uptime: 99.95,
    responseTime: 89,
    errorRate: 0.02,
    lastChecked: new Date().toISOString()
  },
  {
    id: '2',
    name: 'Database Cluster',
    status: 'degraded' as const,
    uptime: 99.1,
    responseTime: 340,
    errorRate: 0.8,
    lastChecked: new Date().toISOString()
  },
  {
    id: '3',
    name: 'Knowledge Service',
    status: 'operational' as const,
    uptime: 99.99,
    responseTime: 67,
    errorRate: 0.01,
    lastChecked: new Date().toISOString()
  },
  {
    id: '4',
    name: 'Task Service',
    status: 'down' as const,
    uptime: 0,
    responseTime: 0,
    errorRate: 100,
    lastChecked: new Date(Date.now() - 300000).toISOString()
  }
]

const sampleAlerts = [
  {
    id: '1',
    title: 'データベース接続エラー急増',
    description: 'データベースクラスターへの接続エラーが過去5分間で50%増加しています',
    severity: 'critical' as const,
    category: 'system' as const,
    status: 'new' as const,
    createdAt: new Date(Date.now() - 300000).toISOString(),
    source: 'Database Monitor',
    affectedServices: ['Task Service', 'API Gateway'],
    metrics: { current: 340, threshold: 200, unit: 'ms' },
    actions: [
      { id: 'ack', label: '確認', type: 'secondary' as const },
      { id: 'escalate', label: 'エスカレート', type: 'primary' as const },
      { id: 'resolve', label: '解決', type: 'danger' as const }
    ]
  },
  {
    id: '2',
    title: 'CPU使用率の上昇',
    description: 'プロダクションサーバーのCPU使用率が警告レベルに達しています',
    severity: 'warning' as const,
    category: 'performance' as const,
    status: 'acknowledged' as const,
    createdAt: new Date(Date.now() - 900000).toISOString(),
    acknowledgedAt: new Date(Date.now() - 600000).toISOString(),
    assignee: { id: '1', name: '山田太郎', avatar: '/avatars/yamada.jpg' },
    source: 'System Monitor',
    affectedServices: ['API Gateway'],
    metrics: { current: 78, threshold: 70, unit: '%' },
    actions: [
      { id: 'investigate', label: '調査開始', type: 'primary' as const },
      { id: 'scale', label: 'スケールアウト', type: 'secondary' as const },
      { id: 'resolve', label: '解決', type: 'danger' as const }
    ]
  }
]

const sampleIncidents = [
  {
    id: '1',
    title: 'プロダクションデータベース障害',
    description: 'メインデータベースクラスターの完全停止により、全サービスが影響を受けました',
    severity: 'critical' as const,
    category: 'system' as const,
    status: 'resolved' as const,
    startTime: '2024-01-10T14:30:00Z',
    endTime: '2024-01-10T16:45:00Z',
    duration: 135,
    impact: {
      users: 12500,
      services: ['API Gateway', 'Knowledge Service', 'Task Service'],
      revenue: 2500000
    },
    rootCause: 'ディスク容量不足によるデータベースの強制停止',
    resolution: 'ディスク領域の拡張とデータベースの再起動を実行',
    timeline: [
      { id: 't1', time: '2024-01-10T14:30:00Z', action: '障害検出', actor: 'System Monitor', type: 'detection' as const },
      { id: 't2', time: '2024-01-10T14:35:00Z', action: 'オンコール担当者への通知', actor: 'Alert System', type: 'escalation' as const },
      { id: 't3', time: '2024-01-10T15:00:00Z', action: '根本原因の特定', actor: '山田太郎', type: 'mitigation' as const },
      { id: 't4', time: '2024-01-10T16:45:00Z', action: 'サービス復旧完了', actor: '鈴木一郎', type: 'resolution' as const }
    ],
    metrics: { mttr: 135, mtta: 5, availability: 99.1 },
    postmortem: {
      id: 'pm1',
      url: '/postmortem/1',
      lessons: ['定期的なディスク監視の強化', '自動容量拡張の実装', 'アラート閾値の見直し']
    }
  }
]

const sampleAutoResponses = [
  {
    id: '1',
    name: 'CPUスケールアウト',
    description: 'CPU使用率が閾値を超えた場合に自動的にインスタンスを追加',
    trigger: { type: 'metric' as const, condition: 'CPU使用率 > 80%', threshold: 80 },
    actions: [
      { id: 'a1', type: 'scale' as const, target: 'Web Server Cluster', status: 'pending' as const },
      { id: 'a2', type: 'notify' as const, target: 'DevOps Team', status: 'pending' as const }
    ],
    status: 'active' as const,
    lastTriggered: '2024-01-15T10:30:00Z',
    successRate: 95,
    averageExecutionTime: 45,
    executionHistory: [
      { id: 'e1', timestamp: '2024-01-15T10:30:00Z', result: 'success' as const, duration: 42, triggeredBy: 'CPU Metric Alert' },
      { id: 'e2', timestamp: '2024-01-14T16:20:00Z', result: 'success' as const, duration: 38, triggeredBy: 'CPU Metric Alert' }
    ]
  },
  {
    id: '2',
    name: 'データベース再起動',
    description: '接続エラー率が高い場合にデータベースサービスを再起動',
    trigger: { type: 'alert' as const, condition: 'DB Connection Error > 5%', threshold: 5 },
    actions: [
      { id: 'b1', type: 'restart' as const, target: 'Database Service', status: 'pending' as const },
      { id: 'b2', type: 'notify' as const, target: 'Database Team', status: 'pending' as const }
    ],
    status: 'paused' as const,
    lastTriggered: '2024-01-12T08:15:00Z',
    successRate: 87,
    averageExecutionTime: 90,
    executionHistory: [
      { id: 'e3', timestamp: '2024-01-12T08:15:00Z', result: 'failure' as const, duration: 120, triggeredBy: 'DB Error Alert' }
    ]
  }
]

export default function IncidentSagePage() {
  const [activeView, setActiveView] = useState<'monitoring' | 'alerts' | 'history' | 'automation'>('monitoring')

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
                <div className="w-10 h-10 bg-crimson-600 rounded-full flex items-center justify-center text-2xl shadow-lg">
                  🚨
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">インシデント賢者</h1>
                  <p className="text-sm text-crimson-600">Crisis Sage</p>
                </div>
              </div>
              <Badge variant="secondary" className="bg-crimson-100 text-crimson-800">
                <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse" />
                Active
              </Badge>
            </div>
            
            <div className="flex items-center space-x-3">
              <Button variant="outline" size="sm">
                <AlertTriangle className="w-4 h-4 mr-2" />
                新規インシデント
              </Button>
              <Button variant="outline" size="sm">
                <Plus className="w-4 h-4 mr-2" />
                アラート追加
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
            <Card className="p-6 bg-gradient-to-br from-crimson-50 to-white border-crimson-200">
              <div className="flex items-center justify-between mb-2">
                <Shield className="w-8 h-8 text-crimson-600" />
                <Badge 
                  variant="secondary" 
                  className={cn(
                    sampleServices.some(s => s.status === 'down') ? 'bg-red-100 text-red-800' :
                    sampleServices.some(s => s.status === 'degraded') ? 'bg-yellow-100 text-yellow-800' :
                    'bg-green-100 text-green-800'
                  )}
                >
                  {sampleServices.some(s => s.status === 'down') ? '危険' :
                   sampleServices.some(s => s.status === 'degraded') ? '警告' : '正常'}
                </Badge>
              </div>
              <h3 className="text-2xl font-bold text-gray-900">
                {sampleServices.filter(s => s.status === 'operational').length}/{sampleServices.length}
              </h3>
              <p className="text-sm text-gray-600">正常サービス</p>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card className="p-6 bg-gradient-to-br from-orange-50 to-white border-orange-200">
              <div className="flex items-center justify-between mb-2">
                <AlertTriangle className="w-8 h-8 text-orange-600" />
                <span className="text-sm font-medium text-orange-600">
                  {sampleAlerts.filter(a => a.status === 'new').length > 0 ? '要対応' : '正常'}
                </span>
              </div>
              <h3 className="text-2xl font-bold text-gray-900">
                {sampleAlerts.filter(a => a.status === 'new').length}
              </h3>
              <p className="text-sm text-gray-600">新規アラート</p>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Card className="p-6 bg-gradient-to-br from-blue-50 to-white border-blue-200">
              <div className="flex items-center justify-between mb-2">
                <Activity className="w-8 h-8 text-blue-600" />
                <Badge variant="secondary" className="text-xs">24h</Badge>
              </div>
              <h3 className="text-2xl font-bold text-gray-900">0</h3>
              <p className="text-sm text-gray-600">アクティブインシデント</p>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <Card className="p-6 bg-gradient-to-br from-green-50 to-white border-green-200">
              <div className="flex items-center justify-between mb-2">
                <Zap className="w-8 h-8 text-green-600" />
                <span className="text-sm font-medium text-green-600">95%</span>
              </div>
              <h3 className="text-2xl font-bold text-gray-900">
                {sampleAutoResponses.filter(r => r.status === 'active').length}
              </h3>
              <p className="text-sm text-gray-600">自動対応アクティブ</p>
            </Card>
          </motion.div>
        </div>

        {/* View Tabs */}
        <div className="mb-8">
          <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg w-fit">
            {[
              { id: 'monitoring', label: 'リアルタイム監視', icon: Activity },
              { id: 'alerts', label: 'アラート管理', icon: AlertTriangle },
              { id: 'history', label: 'インシデント履歴', icon: Shield },
              { id: 'automation', label: '自動対応', icon: Zap }
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveView(id as any)}
                className={cn(
                  'px-4 py-2 rounded-md flex items-center space-x-2 transition-all duration-200',
                  activeView === id
                    ? 'bg-white text-crimson-600 shadow-sm'
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
          {activeView === 'monitoring' && (
            <MonitoringDashboard
              metrics={sampleMetrics}
              services={sampleServices}
              onMetricClick={(metric) => console.log('Metric clicked:', metric)}
              onServiceClick={(service) => console.log('Service clicked:', service)}
            />
          )}
          
          {activeView === 'alerts' && (
            <AlertManager
              alerts={sampleAlerts}
              onAlertUpdate={(alert) => console.log('Alert updated:', alert)}
              onAlertAction={(id, action) => console.log('Alert action:', id, action)}
            />
          )}
          
          {activeView === 'history' && (
            <IncidentHistory
              incidents={sampleIncidents}
              onIncidentSelect={(incident) => console.log('Incident selected:', incident)}
            />
          )}
          
          {activeView === 'automation' && (
            <AutoResponseStatus
              responses={sampleAutoResponses}
              onResponseToggle={(id, status) => console.log('Response toggle:', id, status)}
              onResponseExecute={(id) => console.log('Execute response:', id)}
            />
          )}
        </motion.div>
      </main>
    </div>
  )
}