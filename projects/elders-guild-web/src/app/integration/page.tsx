'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Crown, MessageSquare, TrendingUp, Users, Settings, Bell } from 'lucide-react'
import { ElderCouncilMode } from '@/components/integration/ElderCouncilMode'
import { SageCommunication } from '@/components/integration/SageCommunication'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { cn } from '@/lib/utils'

// Sample data
const sampleSages = [
  {
    id: '1',
    name: 'Knowledge Sage',
    title: 'Chief Knowledge Officer',
    avatar: '/avatars/knowledge-sage.jpg',
    status: 'active' as const,
    activity: '新しいAPIドキュメントを分析中',
    performance: {
      efficiency: 94,
      accuracy: 98,
      responseTime: 0.234
    },
    recentActions: [
      { id: '1', action: 'ドキュメント更新', timestamp: '2024-01-15T10:30:00Z', impact: 'high' as const },
      { id: '2', action: '知識ベース同期', timestamp: '2024-01-15T10:15:00Z', impact: 'medium' as const }
    ],
    currentLoad: 76,
    specialization: ['ドキュメント管理', 'ナレッジマイニング', 'バージョン管理']
  },
  {
    id: '2',
    name: 'Task Oracle',
    title: 'Chief Task Coordinator',
    avatar: '/avatars/task-oracle.jpg',
    status: 'busy' as const,
    activity: 'プロジェクトスケジュールを最適化中',
    performance: {
      efficiency: 89,
      accuracy: 95,
      responseTime: 0.156
    },
    recentActions: [
      { id: '3', action: 'タスク優先度調整', timestamp: '2024-01-15T10:25:00Z', impact: 'high' as const },
      { id: '4', action: 'リソース再配分', timestamp: '2024-01-15T10:10:00Z', impact: 'medium' as const }
    ],
    currentLoad: 85,
    specialization: ['プロジェクト管理', 'リソース最適化', 'スケジューリング']
  },
  {
    id: '3',
    name: 'Crisis Sage',
    title: 'Chief Crisis Manager',
    avatar: '/avatars/crisis-sage.jpg',
    status: 'active' as const,
    activity: 'システムヘルスを監視中',
    performance: {
      efficiency: 96,
      accuracy: 99,
      responseTime: 0.089
    },
    recentActions: [
      { id: '5', action: 'アラート処理', timestamp: '2024-01-15T10:20:00Z', impact: 'high' as const },
      { id: '6', action: '自動復旧実行', timestamp: '2024-01-15T10:05:00Z', impact: 'high' as const }
    ],
    currentLoad: 62,
    specialization: ['インシデント管理', '自動復旧', 'リアルタイム監視']
  },
  {
    id: '4',
    name: 'Search Mystic',
    title: 'Chief Information Retrieval Officer',
    avatar: '/avatars/search-mystic.jpg',
    status: 'active' as const,
    activity: 'セマンティック検索エンジンを調整中',
    performance: {
      efficiency: 92,
      accuracy: 97,
      responseTime: 0.123
    },
    recentActions: [
      { id: '7', action: '検索インデックス更新', timestamp: '2024-01-15T10:28:00Z', impact: 'medium' as const },
      { id: '8', action: 'AI提案最適化', timestamp: '2024-01-15T10:12:00Z', impact: 'high' as const }
    ],
    currentLoad: 70,
    specialization: ['セマンティック検索', 'AI推奨', 'データマイニング']
  }
]

const sampleDecisions = [
  {
    id: '1',
    topic: 'APIセキュリティ強化プロトコル',
    description: '新しいセキュリティ脅威に対応するため、API認証システムの強化を提案します',
    priority: 'high' as const,
    participants: ['1', '2', '3', '4'],
    status: 'voting' as const,
    proposal: {
      summary: 'JWT有効期限の短縮、2FA必須化、レート制限の強化を実装',
      requiredActions: [
        '認証システムの更新',
        'セキュリティテストの実施',
        'ドキュメントの更新',
        'チーム研修の実施'
      ],
      expectedOutcome: 'APIセキュリティレベルの大幅向上',
      risksAndMitigation: [
        'ユーザビリティ低下 → 段階的導入で緩和',
        'システム負荷増加 → インフラスケーリング'
      ]
    },
    votes: [
      { sageId: '1', vote: 'approve' as const, reasoning: '知識ベースの整合性に有益' },
      { sageId: '2', vote: 'approve' as const, reasoning: 'プロジェクトスケジュールに組み込み可能' },
      { sageId: '3', vote: 'approve' as const, reasoning: 'セキュリティリスクの大幅軽減' }
    ],
    timeline: {
      proposed: '2024-01-15T09:00:00Z',
      discussionStart: '2024-01-15T09:30:00Z',
      votingStart: '2024-01-15T10:00:00Z'
    }
  },
  {
    id: '2',
    topic: 'マイクロサービス分割戦略',
    description: 'モノリシックアーキテクチャからマイクロサービスへの段階的移行計画',
    priority: 'medium' as const,
    participants: ['1', '2', '4'],
    status: 'discussing' as const,
    proposal: {
      summary: '機能別にサービスを分割し、独立デプロイを可能にする',
      requiredActions: [
        'アーキテクチャ設計',
        'データベース分離',
        'CI/CDパイプライン構築',
        '段階的移行実行'
      ],
      expectedOutcome: 'スケーラビリティとメンテナビリティの向上',
      risksAndMitigation: [
        '複雑性増加 → 適切な監視・ログシステム',
        'データ整合性 → 分散トランザクション設計'
      ]
    },
    votes: [
      { sageId: '1', vote: 'approve' as const, reasoning: 'アーキテクチャドキュメントの体系化に貢献' }
    ],
    timeline: {
      proposed: '2024-01-15T08:00:00Z',
      discussionStart: '2024-01-15T08:30:00Z'
    }
  }
]

const sampleMessages = [
  {
    id: '1',
    from: 'Crisis Sage',
    to: ['Task Oracle'],
    type: 'escalation' as const,
    priority: 'high' as const,
    subject: 'データベース負荷急増',
    content: 'データベースのCPU使用率が90%を超えました。緊急対応が必要です。',
    timestamp: '2024-01-15T10:30:00Z',
    status: 'read' as const,
    relatedContext: {
      type: 'incident',
      id: 'inc-001',
      title: 'データベース性能劣化'
    }
  },
  {
    id: '2',
    from: 'Task Oracle',
    to: ['Crisis Sage', 'Knowledge Sage'],
    type: 'response' as const,
    priority: 'high' as const,
    subject: 'Re: データベース負荷急増',
    content: 'スケールアウトタスクを最優先に設定しました。Knowledge Sageに運用手順の確認を依頼します。',
    timestamp: '2024-01-15T10:32:00Z',
    status: 'delivered' as const
  },
  {
    id: '3',
    from: 'Knowledge Sage',
    to: ['Task Oracle', 'Crisis Sage'],
    type: 'collaboration' as const,
    priority: 'medium' as const,
    subject: '運用手順ドキュメント更新',
    content: 'データベースヘルスチェック手順を最新化しました。自動化スクリプトも添付します。',
    timestamp: '2024-01-15T10:35:00Z',
    status: 'processed' as const
  },
  {
    id: '4',
    from: 'Search Mystic',
    to: ['Knowledge Sage'],
    type: 'request' as const,
    priority: 'low' as const,
    subject: '検索インデックス同期',
    content: '新しいドキュメントが追加されたため、検索インデックスの同期をお願いします。',
    timestamp: '2024-01-15T10:28:00Z',
    status: 'read' as const
  }
]

const sampleChannels = [
  {
    id: '1',
    name: '全体調整',
    participants: ['Knowledge Sage', 'Task Oracle', 'Crisis Sage', 'Search Mystic'],
    isActive: true,
    messageCount: 156,
    lastActivity: '2024-01-15T10:35:00Z',
    purpose: '4賢者間の主要コミュニケーションチャンネル'
  },
  {
    id: '2',
    name: '緊急対応',
    participants: ['Crisis Sage', 'Task Oracle'],
    isActive: true,
    messageCount: 89,
    lastActivity: '2024-01-15T10:32:00Z',
    purpose: 'インシデント対応とタスク調整'
  },
  {
    id: '3',
    name: '知識共有',
    participants: ['Knowledge Sage', 'Search Mystic'],
    isActive: false,
    messageCount: 234,
    lastActivity: '2024-01-15T09:45:00Z',
    purpose: 'ドキュメントと検索の連携'
  }
]

const systemMetrics = {
  overallHealth: 94,
  coveragePercentage: 67,
  collaborationIndex: 8.7,
  emergingIssues: 3
}

export default function IntegrationPage() {
  const [activeView, setActiveView] = useState<'council' | 'communication' | 'analytics'>('council')

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-r from-purple-900 via-blue-900 to-indigo-900 shadow-lg sticky top-0 z-50"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-r from-yellow-400 to-yellow-600 rounded-full flex items-center justify-center shadow-lg">
                  <Crown className="w-6 h-6 text-yellow-900" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-white">AI Company統合システム</h1>
                  <p className="text-sm text-purple-200">4賢者システム完全統合ダッシュボード</p>
                </div>
              </div>
              <Badge variant="secondary" className="bg-green-100 text-green-800">
                <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse" />
                66.7% 統合完了
              </Badge>
            </div>
            
            <div className="flex items-center space-x-3">
              <Button variant="ghost" size="sm" className="text-white hover:bg-white hover:bg-opacity-10">
                <Bell className="w-4 h-4 mr-2" />
                通知
              </Button>
              <Button variant="ghost" size="sm" className="text-white hover:bg-white hover:bg-opacity-10">
                <Settings className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </motion.header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Card className="p-6 bg-gradient-to-br from-purple-50 to-white border-purple-200">
              <div className="flex items-center justify-between mb-2">
                <Crown className="w-8 h-8 text-purple-600" />
                <Badge variant="secondary" className="text-xs bg-purple-100 text-purple-800">
                  統合中
                </Badge>
              </div>
              <h3 className="text-2xl font-bold text-gray-900">{systemMetrics.overallHealth}%</h3>
              <p className="text-sm text-gray-600">システム健全性</p>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card className="p-6 bg-gradient-to-br from-blue-50 to-white border-blue-200">
              <div className="flex items-center justify-between mb-2">
                <Users className="w-8 h-8 text-blue-600" />
                <span className="text-sm font-medium text-blue-600">+8.2%</span>
              </div>
              <h3 className="text-2xl font-bold text-gray-900">{systemMetrics.collaborationIndex}</h3>
              <p className="text-sm text-gray-600">協調指数</p>
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
                <Badge variant="secondary" className="text-xs">進行中</Badge>
              </div>
              <h3 className="text-2xl font-bold text-gray-900">{systemMetrics.coveragePercentage}%</h3>
              <p className="text-sm text-gray-600">知識カバレッジ</p>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <Card className="p-6 bg-gradient-to-br from-orange-50 to-white border-orange-200">
              <div className="flex items-center justify-between mb-2">
                <MessageSquare className="w-8 h-8 text-orange-600" />
                <span className="text-sm font-medium text-orange-600">リアルタイム</span>
              </div>
              <h3 className="text-2xl font-bold text-gray-900">{sampleMessages.length}</h3>
              <p className="text-sm text-gray-600">アクティブメッセージ</p>
            </Card>
          </motion.div>
        </div>

        {/* View Tabs */}
        <div className="mb-8">
          <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg w-fit">
            {[
              { id: 'council', label: 'エルダー評議会', icon: Crown },
              { id: 'communication', label: '賢者間通信', icon: MessageSquare },
              { id: 'analytics', label: '統合分析', icon: TrendingUp }
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveView(id as any)}
                className={cn(
                  'px-4 py-2 rounded-md flex items-center space-x-2 transition-all duration-200',
                  activeView === id
                    ? 'bg-white text-purple-600 shadow-sm'
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
          {activeView === 'council' && (
            <ElderCouncilMode
              sages={sampleSages}
              currentDecisions={sampleDecisions}
              systemMetrics={systemMetrics}
              onCouncilAction={(action, data) => console.log('Council action:', action, data)}
            />
          )}
          
          {activeView === 'communication' && (
            <SageCommunication
              messages={sampleMessages}
              channels={sampleChannels}
              activeSages={['Knowledge Sage', 'Task Oracle', 'Crisis Sage', 'Search Mystic']}
              onSendMessage={(message) => console.log('Send message:', message)}
              onJoinChannel={(channelId) => console.log('Join channel:', channelId)}
            />
          )}
          
          {activeView === 'analytics' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">統合システム分析</h3>
                <div className="space-y-4">
                  <div className="text-center p-8 bg-gradient-to-r from-purple-100 to-blue-100 rounded-lg">
                    <Crown className="w-16 h-16 text-purple-600 mx-auto mb-4" />
                    <h4 className="text-xl font-bold text-gray-900 mb-2">
                      Phase 2: 4賢者システム完全統合
                    </h4>
                    <p className="text-gray-600 mb-4">
                      統合度 66.7% - Week 3-4 実装完了
                    </p>
                    <div className="text-sm text-gray-500 space-y-1">
                      <p>✅ ナレッジ賢者 UI実装完了</p>
                      <p>✅ タスク賢者 UI実装完了</p>
                      <p>✅ インシデント賢者 UI実装完了</p>
                      <p>✅ RAG賢者 UI実装完了</p>
                      <p>✅ 統合機能実装完了</p>
                    </div>
                  </div>
                </div>
              </Card>
              
              <Card className="p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Next Steps</h3>
                <div className="space-y-3">
                  <div className="p-3 bg-blue-50 rounded-lg">
                    <h4 className="font-medium text-blue-900">Phase 3: Advanced Integration</h4>
                    <p className="text-sm text-blue-700 mt-1">
                      賢者間の高度な連携機能とAI駆動の自動化
                    </p>
                  </div>
                  <div className="p-3 bg-green-50 rounded-lg">
                    <h4 className="font-medium text-green-900">Phase 4: Production Deployment</h4>
                    <p className="text-sm text-green-700 mt-1">
                      本番環境への段階的デプロイとスケーリング
                    </p>
                  </div>
                  <div className="p-3 bg-purple-50 rounded-lg">
                    <h4 className="font-medium text-purple-900">Phase 5: Continuous Evolution</h4>
                    <p className="text-sm text-purple-700 mt-1">
                      継続的な学習と進化システムの構築
                    </p>
                  </div>
                </div>
              </Card>
            </div>
          )}
        </motion.div>
      </main>
    </div>
  )
}