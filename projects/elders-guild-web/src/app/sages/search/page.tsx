'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Search, Brain, BarChart3, Lightbulb, Plus, Settings } from 'lucide-react'
import { GlobalSearchInterface } from '@/components/sages/search/GlobalSearchInterface'
import { SemanticSearch } from '@/components/sages/search/SemanticSearch'
import { SearchVisualization } from '@/components/sages/search/SearchVisualization'
import { AISuggestionSystem } from '@/components/sages/search/AISuggestionSystem'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { cn } from '@/lib/utils'

// Sample data
const sampleSearchResults = [
  {
    id: '1',
    title: 'API認証システムの実装ガイド',
    content: 'JWT（JSON Web Token）を使用した認証システムの実装について詳しく解説します。セキュリティのベストプラクティスとパフォーマンス最適化のポイントを含めて説明します。',
    type: 'document' as const,
    source: 'Knowledge Base',
    relevanceScore: 0.95,
    lastModified: '2024-01-15T10:30:00Z',
    author: { id: '1', name: '山田太郎', avatar: '/avatars/yamada.jpg' },
    tags: ['API', 'Authentication', 'JWT', 'Security'],
    highlights: [
      { field: 'title', matches: ['API', '認証'] },
      { field: 'content', matches: ['JWT', 'セキュリティ', 'パフォーマンス'] }
    ],
    url: '/docs/api-auth'
  },
  {
    id: '2',
    title: 'データベース設計のベストプラクティス',
    content: 'スケーラブルなデータベース設計のための原則とパターン。インデックス戦略、正規化、パフォーマンスチューニングについて解説します。',
    type: 'document' as const,
    source: 'Documentation',
    relevanceScore: 0.87,
    lastModified: '2024-01-14T15:45:00Z',
    author: { id: '2', name: '佐藤花子', avatar: '/avatars/sato.jpg' },
    tags: ['Database', 'Design', 'Performance', 'Scaling'],
    highlights: [
      { field: 'title', matches: ['データベース', '設計'] },
      { field: 'content', matches: ['スケーラブル', 'パフォーマンス'] }
    ],
    url: '/docs/database-design'
  }
]

const sampleSemanticResults = [
  {
    id: '1',
    title: 'マイクロサービスアーキテクチャパターン',
    content: 'マイクロサービスアーキテクチャの設計パターンとベストプラクティス。サービス間通信、データ一貫性、モニタリング戦略について詳しく解説します。',
    semanticScore: 0.92,
    conceptMatch: ['アーキテクチャ', 'マイクロサービス', 'パターン'],
    contextualRelevance: 0.88,
    intentMatch: 'exact' as const,
    source: 'Architecture Guide',
    type: 'knowledge' as const,
    relatedConcepts: [
      { concept: 'サービスメッシュ', weight: 0.8 },
      { concept: 'API Gateway', weight: 0.7 },
      { concept: 'Event Sourcing', weight: 0.6 }
    ]
  }
]

const sampleConceptClusters = [
  {
    id: '1',
    name: 'アーキテクチャ',
    concepts: ['マイクロサービス', 'API Gateway', 'Load Balancer'],
    size: 45,
    relevance: 0.9,
    color: '#10b981'
  },
  {
    id: '2',
    name: 'セキュリティ',
    concepts: ['JWT', 'OAuth', 'HTTPS'],
    size: 32,
    relevance: 0.85,
    color: '#3b82f6'
  },
  {
    id: '3',
    name: 'データベース',
    concepts: ['SQL', 'NoSQL', 'ACID'],
    size: 28,
    relevance: 0.78,
    color: '#8b5cf6'
  }
]

const sampleAnalytics = {
  totalResults: 1247,
  searchTime: 0.234,
  categories: [
    { name: 'ドキュメント', count: 456, percentage: 36.6, color: '#10b981' },
    { name: 'コード', count: 321, percentage: 25.7, color: '#3b82f6' },
    { name: 'ディスカッション', count: 234, percentage: 18.8, color: '#8b5cf6' },
    { name: 'ユーザー', count: 236, percentage: 18.9, color: '#f59e0b' }
  ],
  relevanceDistribution: [
    { range: '90-100%', count: 123, percentage: 35 },
    { range: '80-89%', count: 98, percentage: 28 },
    { range: '70-79%', count: 87, percentage: 25 },
    { range: '60-69%', count: 42, percentage: 12 }
  ],
  temporalData: [
    { period: '月', searchCount: 1240, avgRelevance: 0.85 },
    { period: '火', searchCount: 1156, avgRelevance: 0.82 },
    { period: '水', searchCount: 1345, avgRelevance: 0.88 },
    { period: '木', searchCount: 1423, avgRelevance: 0.87 },
    { period: '金', searchCount: 1678, avgRelevance: 0.89 }
  ],
  topQueries: [
    { query: 'API認証', count: 245, avgRelevance: 0.91 },
    { query: 'データベース設計', count: 189, avgRelevance: 0.87 },
    { query: 'マイクロサービス', count: 167, avgRelevance: 0.89 }
  ],
  sourceDistribution: [
    { source: 'Knowledge Base', count: 456, avgResponseTime: 120 },
    { source: 'Code Repository', count: 321, avgResponseTime: 89 },
    { source: 'Documentation', count: 234, avgResponseTime: 156 },
    { source: 'Discussion Forum', count: 236, avgResponseTime: 201 }
  ]
}

const sampleSuggestions = [
  {
    id: '1',
    type: 'search_refinement' as const,
    title: '検索クエリの改善提案',
    description: '「API セキュリティ ベストプラクティス」で検索すると、より具体的な結果が得られます',
    confidence: 0.89,
    reasoning: 'あなたの過去の検索パターンと現在のクエリから、セキュリティ関連の情報を求めていると判断しました',
    actions: [
      { id: 'apply', label: '提案を適用', type: 'primary' as const, action: 'refine_search' }
    ],
    metadata: {
      source: 'Search Pattern Analysis',
      tags: ['search', 'optimization'],
      estimatedValue: 'high' as const,
      difficulty: 'easy' as const
    }
  },
  {
    id: '2',
    type: 'learning_path' as const,
    title: '推奨学習パス',
    description: 'APIセキュリティの基礎から応用まで、体系的な学習コースを提案します',
    confidence: 0.75,
    reasoning: 'あなたのスキルレベルと学習履歴に基づいて、最適な学習順序を提案しています',
    actions: [
      { id: 'start', label: '学習を開始', type: 'primary' as const, action: 'start_learning' },
      { id: 'save', label: '後で確認', type: 'secondary' as const, action: 'save_for_later' }
    ],
    metadata: {
      source: 'Learning Analytics',
      tags: ['learning', 'security', 'api'],
      estimatedValue: 'high' as const,
      difficulty: 'medium' as const
    }
  }
]

const sampleInsights = [
  {
    id: '1',
    pattern: 'セキュリティ関連のクエリが急増',
    frequency: 156,
    impact: 8,
    trend: 'rising' as const,
    examples: ['API セキュリティ', 'OWASP Top 10', 'JWT 脆弱性']
  },
  {
    id: '2',
    pattern: 'マイクロサービス関連の議論が活発',
    frequency: 98,
    impact: 7,
    trend: 'stable' as const,
    examples: ['サービスメッシュ', 'コンテナオーケストレーション', 'API Gateway']
  }
]

const userContext = {
  role: 'Senior Developer',
  department: 'Engineering',
  recentQueries: ['API認証', 'JWT実装', 'セキュリティテスト', 'OWASP', 'OAuth2.0'],
  preferences: ['技術ドキュメント', 'コード例', 'ベストプラクティス']
}

export default function SearchSagePage() {
  const [activeView, setActiveView] = useState<'search' | 'semantic' | 'analytics' | 'suggestions'>('search')
  const [currentQuery, setCurrentQuery] = useState('')

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
                <div className="w-10 h-10 bg-lime-600 rounded-full flex items-center justify-center text-2xl shadow-lg">
                  🔍
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">RAG賢者</h1>
                  <p className="text-sm text-lime-600">Search Mystic</p>
                </div>
              </div>
              <Badge variant="secondary" className="bg-lime-100 text-lime-800">
                <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse" />
                Active
              </Badge>
            </div>
            
            <div className="flex items-center space-x-3">
              <Button variant="outline" size="sm">
                <Search className="w-4 h-4 mr-2" />
                詳細検索
              </Button>
              <Button variant="outline" size="sm">
                <Plus className="w-4 h-4 mr-2" />
                保存された検索
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
            <Card className="p-6 bg-gradient-to-br from-lime-50 to-white border-lime-200">
              <div className="flex items-center justify-between mb-2">
                <Search className="w-8 h-8 text-lime-600" />
                <Badge variant="secondary" className="text-xs">今日</Badge>
              </div>
              <h3 className="text-2xl font-bold text-gray-900">2,847</h3>
              <p className="text-sm text-gray-600">総検索数</p>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card className="p-6 bg-gradient-to-br from-green-50 to-white border-green-200">
              <div className="flex items-center justify-between mb-2">
                <Brain className="w-8 h-8 text-green-600" />
                <span className="text-sm font-medium text-green-600">94.2%</span>
              </div>
              <h3 className="text-2xl font-bold text-gray-900">0.234s</h3>
              <p className="text-sm text-gray-600">平均応答時間</p>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Card className="p-6 bg-gradient-to-br from-blue-50 to-white border-blue-200">
              <div className="flex items-center justify-between mb-2">
                <BarChart3 className="w-8 h-8 text-blue-600" />
                <Badge variant="secondary" className="text-xs">+15%</Badge>
              </div>
              <h3 className="text-2xl font-bold text-gray-900">87.3%</h3>
              <p className="text-sm text-gray-600">平均関連度</p>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <Card className="p-6 bg-gradient-to-br from-purple-50 to-white border-purple-200">
              <div className="flex items-center justify-between mb-2">
                <Lightbulb className="w-8 h-8 text-purple-600" />
                <span className="text-sm font-medium text-purple-600">AI推奨</span>
              </div>
              <h3 className="text-2xl font-bold text-gray-900">156</h3>
              <p className="text-sm text-gray-600">アクティブ提案</p>
            </Card>
          </motion.div>
        </div>

        {/* View Tabs */}
        <div className="mb-8">
          <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg w-fit">
            {[
              { id: 'search', label: 'グローバル検索', icon: Search },
              { id: 'semantic', label: 'セマンティック検索', icon: Brain },
              { id: 'analytics', label: '検索分析', icon: BarChart3 },
              { id: 'suggestions', label: 'AI提案', icon: Lightbulb }
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveView(id as any)}
                className={cn(
                  'px-4 py-2 rounded-md flex items-center space-x-2 transition-all duration-200',
                  activeView === id
                    ? 'bg-white text-lime-600 shadow-sm'
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
          {activeView === 'search' && (
            <GlobalSearchInterface
              onSearch={(query, filters) => {
                setCurrentQuery(query)
                console.log('Search:', query, filters)
              }}
              initialResults={sampleSearchResults}
              isLoading={false}
            />
          )}
          
          {activeView === 'semantic' && (
            <SemanticSearch
              query={currentQuery || 'APIセキュリティ'}
              results={sampleSemanticResults}
              conceptClusters={sampleConceptClusters}
              onConceptClick={(concept) => console.log('Concept clicked:', concept)}
              onResultClick={(result) => console.log('Result clicked:', result)}
              isProcessing={false}
            />
          )}
          
          {activeView === 'analytics' && (
            <SearchVisualization
              analytics={sampleAnalytics}
              networkData={{
                nodes: [
                  { id: 'query', label: 'API認証', type: 'query', size: 25, color: '#10b981', x: 400, y: 200 },
                  { id: 'result1', label: 'JWTガイド', type: 'result', size: 15, color: '#3b82f6', x: 300, y: 150 },
                  { id: 'result2', label: 'OAuth実装', type: 'result', size: 12, color: '#3b82f6', x: 500, y: 150 },
                  { id: 'concept1', label: 'セキュリティ', type: 'concept', size: 10, color: '#8b5cf6', x: 350, y: 100 }
                ],
                links: [
                  { source: 'query', target: 'result1', strength: 0.9, type: 'semantic' },
                  { source: 'query', target: 'result2', strength: 0.7, type: 'semantic' },
                  { source: 'result1', target: 'concept1', strength: 0.8, type: 'categorical' }
                ]
              }}
            />
          )}
          
          {activeView === 'suggestions' && (
            <AISuggestionSystem
              currentQuery={currentQuery || 'APIセキュリティ'}
              userContext={userContext}
              suggestions={sampleSuggestions}
              insights={sampleInsights}
              onSuggestionClick={(suggestion) => console.log('Suggestion clicked:', suggestion)}
              onFeedback={(id, feedback) => console.log('Feedback:', id, feedback)}
            />
          )}
        </motion.div>
      </main>
    </div>
  )
}