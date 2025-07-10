'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { BookOpen, Brain, Database, TrendingUp, Plus, Search, Settings } from 'lucide-react'
import { KnowledgeBaseViewer } from '@/components/sages/knowledge/KnowledgeBaseViewer'
import { MarkdownRenderer } from '@/components/sages/knowledge/MarkdownRenderer'
import { KnowledgeGraph } from '@/components/sages/knowledge/KnowledgeGraph'
import { VersionHistory } from '@/components/sages/knowledge/VersionHistory'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { cn } from '@/lib/utils'

// Sample data
const sampleKnowledgeItems = [
  {
    id: '1',
    title: 'AI Company アーキテクチャ概要',
    content: 'AI Companyのシステムアーキテクチャは、4つの賢者システムを中心に構築されています。各賢者は独立したマイクロサービスとして動作し、相互に連携します。',
    category: 'アーキテクチャ',
    tags: ['システム設計', 'マイクロサービス', '賢者システム'],
    lastModified: '2024-01-15T10:30:00Z',
    version: '2.1.0',
    author: '山田太郎',
    type: 'document' as const,
    connections: ['賢者間通信プロトコル', 'APIゲートウェイ設計']
  },
  {
    id: '2',
    title: '賢者間通信プロトコル',
    content: '賢者間の通信はgRPCを使用し、Protocol Buffersで定義されたスキーマに基づいています。非同期通信にはRabbitMQを使用します。',
    category: 'プロトコル',
    tags: ['gRPC', 'Protocol Buffers', 'RabbitMQ'],
    lastModified: '2024-01-14T15:45:00Z',
    version: '1.3.2',
    author: '佐藤花子',
    type: 'reference' as const,
    connections: ['AI Company アーキテクチャ概要', 'メッセージング設計']
  },
  {
    id: '3',
    title: 'デプロイメントガイド',
    content: 'Kubernetesクラスターへのデプロイメント手順。各賢者サービスは独立したPodとして動作し、Helmチャートで管理されます。',
    category: 'DevOps',
    tags: ['Kubernetes', 'Helm', 'CI/CD'],
    lastModified: '2024-01-13T09:00:00Z',
    version: '3.0.0',
    author: '鈴木一郎',
    type: 'guide' as const,
    connections: ['Kubernetes設定', 'CI/CDパイプライン']
  }
]

const sampleVersions = [
  {
    id: 'v1',
    version: '3.0.0',
    timestamp: '2024-01-13T09:00:00Z',
    author: '鈴木一郎',
    message: 'メジャーアップデート: Kubernetes v1.28対応とHelm v3移行',
    changes: {
      additions: 245,
      deletions: 89,
      files: ['deployment.yaml', 'values.yaml', 'README.md']
    },
    type: 'major' as const
  },
  {
    id: 'v2',
    version: '2.1.0',
    timestamp: '2024-01-10T14:30:00Z',
    author: '山田太郎',
    message: '新機能: オートスケーリング設定の追加',
    changes: {
      additions: 67,
      deletions: 12,
      files: ['hpa.yaml', 'deployment.yaml']
    },
    type: 'minor' as const
  },
  {
    id: 'v3',
    version: '2.0.1',
    timestamp: '2024-01-08T11:00:00Z',
    author: '佐藤花子',
    message: 'バグ修正: リソース制限の調整',
    changes: {
      additions: 5,
      deletions: 3,
      files: ['deployment.yaml']
    },
    type: 'patch' as const
  }
]

const sampleGraphNodes = [
  { id: '1', label: 'AI Company アーキテクチャ', type: 'document' as const, size: 20, color: '#9333ea' },
  { id: '2', label: '賢者間通信プロトコル', type: 'document' as const, size: 15, color: '#9333ea' },
  { id: '3', label: 'デプロイメントガイド', type: 'document' as const, size: 18, color: '#9333ea' },
  { id: 'cat1', label: 'アーキテクチャ', type: 'category' as const, size: 12, color: '#3b82f6' },
  { id: 'cat2', label: 'DevOps', type: 'category' as const, size: 12, color: '#3b82f6' },
  { id: 'tag1', label: 'Kubernetes', type: 'tag' as const, size: 8, color: '#10b981' },
  { id: 'tag2', label: 'gRPC', type: 'tag' as const, size: 8, color: '#10b981' },
  { id: 'author1', label: '山田太郎', type: 'author' as const, size: 10, color: '#f59e0b' }
]

const sampleGraphLinks = [
  { source: '1', target: '2', strength: 0.8 },
  { source: '1', target: 'cat1', strength: 1 },
  { source: '2', target: 'cat1', strength: 0.7 },
  { source: '3', target: 'cat2', strength: 1 },
  { source: '3', target: 'tag1', strength: 0.9 },
  { source: '2', target: 'tag2', strength: 0.9 },
  { source: '1', target: 'author1', strength: 0.6 }
]

export default function KnowledgeSagePage() {
  const [activeView, setActiveView] = useState<'base' | 'markdown' | 'graph' | 'history'>('base')
  const [selectedDocument, setSelectedDocument] = useState<string | null>(null)

  const sampleMarkdown = `# AI Company 技術ドキュメント

## 概要

AI Companyは、**4つの賢者システム**を中心とした革新的なアーキテクチャを採用しています。

> [!NOTE] このドキュメントは、システム全体の設計思想と実装詳細を説明します。

## 賢者システムの特徴

各賢者は以下の特徴を持ちます：

- **独立性**: マイクロサービスとして独立動作
- **協調性**: gRPCによる高速通信
- **拡張性**: 水平スケーリング対応

### コード例

\`\`\`typescript
// 賢者間通信の例
const response = await knowledgeSage.query({
  topic: "アーキテクチャ",
  depth: "detailed"
});
\`\`\`

## 技術スタック

1. **バックエンド**
   - Node.js + TypeScript
   - gRPC / Protocol Buffers
   - PostgreSQL / Redis

2. **フロントエンド**
   - Next.js 14
   - Tailwind CSS
   - Framer Motion

> [!SUCCESS] この構成により、高性能かつ保守性の高いシステムを実現しています。

---

詳細な実装ガイドは、個別のドキュメントを参照してください。`

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
                <div className="w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center text-2xl shadow-lg">
                  📚
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">ナレッジ賢者</h1>
                  <p className="text-sm text-purple-600">Knowledge Sage</p>
                </div>
              </div>
              <Badge variant="secondary" className="bg-purple-100 text-purple-800">
                <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse" />
                Active
              </Badge>
            </div>

            <div className="flex items-center space-x-3">
              <Button variant="outline" size="sm">
                <Search className="w-4 h-4 mr-2" />
                検索
              </Button>
              <Button variant="outline" size="sm">
                <Plus className="w-4 h-4 mr-2" />
                新規作成
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
            <Card className="p-6 bg-gradient-to-br from-purple-50 to-white border-purple-200">
              <div className="flex items-center justify-between mb-2">
                <Brain className="w-8 h-8 text-purple-600" />
                <TrendingUp className="w-5 h-5 text-green-500" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900">1,247</h3>
              <p className="text-sm text-gray-600">総ドキュメント数</p>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card className="p-6 bg-gradient-to-br from-indigo-50 to-white border-indigo-200">
              <div className="flex items-center justify-between mb-2">
                <Database className="w-8 h-8 text-indigo-600" />
                <span className="text-sm font-medium text-indigo-600">+23%</span>
              </div>
              <h3 className="text-2xl font-bold text-gray-900">89</h3>
              <p className="text-sm text-gray-600">今週の更新</p>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Card className="p-6 bg-gradient-to-br from-violet-50 to-white border-violet-200">
              <div className="flex items-center justify-between mb-2">
                <BookOpen className="w-8 h-8 text-violet-600" />
                <Badge variant="secondary" className="text-xs">新着</Badge>
              </div>
              <h3 className="text-2xl font-bold text-gray-900">15</h3>
              <p className="text-sm text-gray-600">アクティブな編集者</p>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <Card className="p-6 bg-gradient-to-br from-purple-50 to-white border-purple-200">
              <div className="flex items-center justify-between mb-2">
                <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                  <span className="text-lg">🎯</span>
                </div>
                <span className="text-sm font-medium text-purple-600">98.5%</span>
              </div>
              <h3 className="text-2xl font-bold text-gray-900">66.7%</h3>
              <p className="text-sm text-gray-600">知識カバレッジ</p>
            </Card>
          </motion.div>
        </div>

        {/* View Tabs */}
        <div className="mb-8">
          <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg w-fit">
            {[
              { id: 'base', label: '知識ベース', icon: Database },
              { id: 'markdown', label: 'マークダウン', icon: BookOpen },
              { id: 'graph', label: '知識グラフ', icon: Brain },
              { id: 'history', label: 'バージョン履歴', icon: BookOpen }
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
          {activeView === 'base' && (
            <KnowledgeBaseViewer items={sampleKnowledgeItems} />
          )}

          {activeView === 'markdown' && (
            <Card className="p-8">
              <MarkdownRenderer content={sampleMarkdown} />
            </Card>
          )}

          {activeView === 'graph' && (
            <Card className="p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">知識グラフビュー</h2>
              <div className="h-[600px]">
                <KnowledgeGraph
                  nodes={sampleGraphNodes}
                  links={sampleGraphLinks}
                  onNodeClick={(node) => console.log('Clicked:', node)}
                />
              </div>
            </Card>
          )}

          {activeView === 'history' && (
            <Card className="p-6">
              <VersionHistory
                documentId="3"
                versions={sampleVersions}
                currentVersion="3.0.0"
                onVersionSelect={(version) => console.log('Selected version:', version)}
                onCompare={(v1, v2) => console.log('Compare:', v1, v2)}
              />
            </Card>
          )}
        </motion.div>
      </main>
    </div>
  )
}
