'use client'

import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Brain, Zap, Target, TrendingUp, MessageSquare, FileText, Code, Users } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Progress } from '@/components/ui/Progress'

interface SemanticResult {
  id: string
  title: string
  content: string
  semanticScore: number
  conceptMatch: string[]
  contextualRelevance: number
  intentMatch: 'exact' | 'partial' | 'related'
  source: string
  type: 'knowledge' | 'code' | 'discussion' | 'documentation'
  embedding?: {
    similarity: number
    dimensions: number[]
  }
  relatedConcepts: {
    concept: string
    weight: number
  }[]
}

interface ConceptCluster {
  id: string
  name: string
  concepts: string[]
  size: number
  relevance: number
  color: string
}

interface SemanticSearchProps {
  query: string
  results: SemanticResult[]
  conceptClusters: ConceptCluster[]
  onConceptClick?: (concept: string) => void
  onResultClick?: (result: SemanticResult) => void
  isProcessing?: boolean
  className?: string
}

export function SemanticSearch({
  query,
  results,
  conceptClusters,
  onConceptClick,
  onResultClick,
  isProcessing = false,
  className
}: SemanticSearchProps) {
  const [selectedCluster, setSelectedCluster] = useState<ConceptCluster | null>(null)
  const [viewMode, setViewMode] = useState<'results' | 'concepts' | 'analysis'>('results')

  const getIntentColor = (intent: SemanticResult['intentMatch']) => {
    switch (intent) {
      case 'exact': return 'bg-green-100 text-green-800'
      case 'partial': return 'bg-yellow-100 text-yellow-800'
      case 'related': return 'bg-blue-100 text-blue-800'
    }
  }

  const getTypeIcon = (type: SemanticResult['type']) => {
    switch (type) {
      case 'knowledge': return <Brain className="w-4 h-4" />
      case 'code': return <Code className="w-4 h-4" />
      case 'discussion': return <MessageSquare className="w-4 h-4" />
      case 'documentation': return <FileText className="w-4 h-4" />
    }
  }

  const getTypeColor = (type: SemanticResult['type']) => {
    switch (type) {
      case 'knowledge': return 'bg-purple-100 text-purple-800'
      case 'code': return 'bg-gray-100 text-gray-800'
      case 'discussion': return 'bg-blue-100 text-blue-800'
      case 'documentation': return 'bg-green-100 text-green-800'
    }
  }

  const extractKeyPhrases = (text: string, concepts: string[]): string => {
    // Simple keyword highlighting simulation
    let highlighted = text
    concepts.forEach(concept => {
      const regex = new RegExp(`(${concept})`, 'gi')
      highlighted = highlighted.replace(regex, '<span class="bg-lime-200 text-lime-900 px-1 rounded">$1</span>')
    })
    return highlighted
  }

  return (
    <div className={cn('space-y-6', className)}>
      {/* Processing Indicator */}
      <AnimatePresence>
        {isProcessing && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="bg-lime-50 border border-lime-200 rounded-lg p-4"
          >
            <div className="flex items-center space-x-3">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              >
                <Brain className="w-6 h-6 text-lime-600" />
              </motion.div>
              <div>
                <h3 className="font-medium text-lime-900">セマンティック分析中...</h3>
                <p className="text-sm text-lime-700">「{query}」の意味的関連性を解析しています</p>
              </div>
            </div>
            <Progress value={75} className="mt-3 h-2 bg-lime-100" />
          </motion.div>
        )}
      </AnimatePresence>

      {/* View Mode Tabs */}
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg w-fit">
        {[
          { id: 'results', label: '検索結果', icon: Target },
          { id: 'concepts', label: '概念マップ', icon: Brain },
          { id: 'analysis', label: '分析詳細', icon: TrendingUp }
        ].map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setViewMode(id as any)}
            className={cn(
              'px-4 py-2 rounded-md flex items-center space-x-2 transition-all duration-200',
              viewMode === id
                ? 'bg-white text-lime-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            )}
          >
            <Icon className="w-4 h-4" />
            <span className="text-sm font-medium">{label}</span>
          </button>
        ))}
      </div>

      {/* Content based on view mode */}
      <AnimatePresence mode="wait">
        {viewMode === 'results' && (
          <motion.div
            key="results"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              {/* Results List */}
              <div className="lg:col-span-3 space-y-4">
                <h2 className="text-lg font-semibold text-gray-900 flex items-center">
                  <Zap className="w-5 h-5 mr-2 text-lime-600" />
                  セマンティック検索結果 ({results.length}件)
                </h2>
                
                {results.map((result, index) => (
                  <motion.div
                    key={result.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                  >
                    <Card
                      className="p-6 cursor-pointer hover:shadow-lg transition-all duration-200"
                      onClick={() => onResultClick?.(result)}
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center space-x-3">
                          <div className={cn('p-2 rounded-lg', getTypeColor(result.type))}>
                            {getTypeIcon(result.type)}
                          </div>
                          <div>
                            <h3 className="font-semibold text-gray-900">{result.title}</h3>
                            <div className="flex items-center space-x-2 mt-1">
                              <Badge className={cn('text-xs', getTypeColor(result.type))}>
                                {result.type}
                              </Badge>
                              <Badge className={cn('text-xs', getIntentColor(result.intentMatch))}>
                                {result.intentMatch === 'exact' ? '完全一致' :
                                 result.intentMatch === 'partial' ? '部分一致' : '関連'}
                              </Badge>
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex flex-col items-end space-y-1">
                          <Badge variant="outline" className="text-xs">
                            {Math.round(result.semanticScore * 100)}% 意味的類似度
                          </Badge>
                          <Badge variant="outline" className="text-xs">
                            {Math.round(result.contextualRelevance * 100)}% 文脈適合度
                          </Badge>
                        </div>
                      </div>
                      
                      <div className="mb-4">
                        <div
                          className="text-gray-600"
                          dangerouslySetInnerHTML={{
                            __html: extractKeyPhrases(
                              result.content.slice(0, 300) + (result.content.length > 300 ? '...' : ''),
                              result.conceptMatch
                            )
                          }}
                        />
                      </div>
                      
                      {/* Concept Matches */}
                      {result.conceptMatch.length > 0 && (
                        <div className="mb-3">
                          <h4 className="text-sm font-medium text-gray-700 mb-2">一致する概念:</h4>
                          <div className="flex flex-wrap gap-1">
                            {result.conceptMatch.map((concept) => (
                              <button
                                key={concept}
                                onClick={(e) => {
                                  e.stopPropagation()
                                  onConceptClick?.(concept)
                                }}
                                className="px-2 py-1 bg-lime-100 text-lime-800 text-xs rounded hover:bg-lime-200 transition-colors"
                              >
                                {concept}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {/* Related Concepts */}
                      {result.relatedConcepts.length > 0 && (
                        <div>
                          <h4 className="text-sm font-medium text-gray-700 mb-2">関連概念:</h4>
                          <div className="space-y-1">
                            {result.relatedConcepts.slice(0, 3).map((related) => (
                              <div key={related.concept} className="flex items-center justify-between text-xs">
                                <span className="text-gray-600">{related.concept}</span>
                                <div className="flex items-center space-x-2">
                                  <div className="w-16 bg-gray-200 rounded-full h-1">
                                    <div
                                      className="bg-lime-500 h-1 rounded-full"
                                      style={{ width: `${related.weight * 100}%` }}
                                    />
                                  </div>
                                  <span className="text-gray-500">{Math.round(related.weight * 100)}%</span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </Card>
                  </motion.div>
                ))}
              </div>

              {/* Concept Clusters Sidebar */}
              <div className="lg:col-span-1">
                <Card className="p-4 sticky top-6">
                  <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
                    <Brain className="w-4 h-4 mr-2" />
                    概念クラスター
                  </h3>
                  
                  <div className="space-y-2">
                    {conceptClusters.map((cluster) => (
                      <button
                        key={cluster.id}
                        onClick={() => setSelectedCluster(cluster)}
                        className={cn(
                          'w-full text-left p-3 rounded-lg border transition-all duration-200',
                          selectedCluster?.id === cluster.id
                            ? 'border-lime-500 bg-lime-50'
                            : 'border-gray-200 hover:border-gray-300'
                        )}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <h4 className="text-sm font-medium text-gray-900">{cluster.name}</h4>
                          <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: cluster.color }}
                          />
                        </div>
                        <div className="text-xs text-gray-500">
                          {cluster.size} 項目 • {Math.round(cluster.relevance * 100)}% 関連
                        </div>
                        <div className="mt-2">
                          <div className="flex flex-wrap gap-1">
                            {cluster.concepts.slice(0, 3).map((concept) => (
                              <span
                                key={concept}
                                className="px-1.5 py-0.5 bg-gray-100 text-gray-600 text-xs rounded"
                              >
                                {concept}
                              </span>
                            ))}
                            {cluster.concepts.length > 3 && (
                              <span className="text-xs text-gray-400">
                                +{cluster.concepts.length - 3}
                              </span>
                            )}
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                </Card>
              </div>
            </div>
          </motion.div>
        )}

        {viewMode === 'concepts' && (
          <motion.div
            key="concepts"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <Card className="p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <Brain className="w-5 h-5 mr-2 text-lime-600" />
                概念マップ
              </h2>
              
              {/* Concept Visualization */}
              <div className="relative bg-gray-50 rounded-lg h-96 p-4">
                <div className="absolute inset-0 flex items-center justify-center">
                  {/* Central Query Node */}
                  <div className="relative">
                    <div className="w-32 h-32 bg-lime-500 rounded-full flex items-center justify-center text-white font-bold text-lg shadow-lg">
                      クエリ
                    </div>
                    
                    {/* Concept Clusters around the center */}
                    {conceptClusters.map((cluster, index) => {
                      const angle = (index / conceptClusters.length) * 2 * Math.PI
                      const radius = 150
                      const x = Math.cos(angle) * radius
                      const y = Math.sin(angle) * radius
                      
                      return (
                        <motion.div
                          key={cluster.id}
                          className="absolute"
                          style={{
                            left: `calc(50% + ${x}px)`,
                            top: `calc(50% + ${y}px)`,
                            transform: 'translate(-50%, -50%)'
                          }}
                          initial={{ scale: 0, opacity: 0 }}
                          animate={{ scale: 1, opacity: 1 }}
                          transition={{ delay: index * 0.1 }}
                        >
                          <div
                            className="w-20 h-20 rounded-full flex items-center justify-center text-white text-sm font-medium shadow-md cursor-pointer hover:scale-110 transition-transform"
                            style={{ backgroundColor: cluster.color }}
                            onClick={() => setSelectedCluster(cluster)}
                          >
                            {cluster.name}
                          </div>
                          
                          {/* Connection line */}
                          <svg
                            className="absolute inset-0 pointer-events-none"
                            style={{
                              width: `${Math.abs(x) * 2 + 80}px`,
                              height: `${Math.abs(y) * 2 + 80}px`,
                              left: x < 0 ? `${x}px` : '-40px',
                              top: y < 0 ? `${y}px` : '-40px'
                            }}
                          >
                            <line
                              x1={x < 0 ? Math.abs(x) + 40 : 40}
                              y1={y < 0 ? Math.abs(y) + 40 : 40}
                              x2={x < 0 ? 40 : Math.abs(x) + 40}
                              y2={y < 0 ? 40 : Math.abs(y) + 40}
                              stroke="#94a3b8"
                              strokeWidth="2"
                              strokeDasharray={`${cluster.relevance * 10}, 5`}
                            />
                          </svg>
                        </motion.div>
                      )
                    })}
                  </div>
                </div>
              </div>
              
              {/* Legend */}
              <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                <h4 className="text-sm font-medium text-gray-700 mb-2">凡例</h4>
                <div className="grid grid-cols-2 gap-4 text-xs">
                  <div>
                    <div className="flex items-center space-x-2 mb-1">
                      <div className="w-3 h-3 bg-lime-500 rounded-full" />
                      <span>メインクエリ</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-1 bg-gray-400" />
                      <span>関連度（線の太さ）</span>
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center space-x-2 mb-1">
                      <div className="w-3 h-3 bg-blue-500 rounded-full" />
                      <span>概念クラスター</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 border-2 border-gray-400 rounded-full" />
                      <span>ノードサイズ = 項目数</span>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          </motion.div>
        )}

        {viewMode === 'analysis' && (
          <motion.div
            key="analysis"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">検索品質分析</h3>
                
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>平均意味的類似度</span>
                      <span className="font-medium">
                        {Math.round((results.reduce((acc, r) => acc + r.semanticScore, 0) / results.length) * 100)}%
                      </span>
                    </div>
                    <Progress
                      value={(results.reduce((acc, r) => acc + r.semanticScore, 0) / results.length) * 100}
                      className="h-2"
                    />
                  </div>
                  
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>平均文脈適合度</span>
                      <span className="font-medium">
                        {Math.round((results.reduce((acc, r) => acc + r.contextualRelevance, 0) / results.length) * 100)}%
                      </span>
                    </div>
                    <Progress
                      value={(results.reduce((acc, r) => acc + r.contextualRelevance, 0) / results.length) * 100}
                      className="h-2"
                    />
                  </div>
                  
                  <div className="pt-4 border-t space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>完全一致</span>
                      <span>{results.filter(r => r.intentMatch === 'exact').length} 件</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>部分一致</span>
                      <span>{results.filter(r => r.intentMatch === 'partial').length} 件</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>関連項目</span>
                      <span>{results.filter(r => r.intentMatch === 'related').length} 件</span>
                    </div>
                  </div>
                </div>
              </Card>
              
              <Card className="p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">コンテンツ分布</h3>
                
                <div className="space-y-3">
                  {['knowledge', 'documentation', 'code', 'discussion'].map((type) => {
                    const count = results.filter(r => r.type === type).length
                    const percentage = (count / results.length) * 100
                    
                    return (
                      <div key={type}>
                        <div className="flex justify-between text-sm mb-1">
                          <span className="capitalize">{type}</span>
                          <span className="font-medium">{count} 件 ({percentage.toFixed(1)}%)</span>
                        </div>
                        <Progress value={percentage} className="h-2" />
                      </div>
                    )
                  })}
                </div>
                
                <div className="mt-6 pt-4 border-t">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">推奨アクション</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• より具体的なキーワードで絞り込み</li>
                    <li>• 関連概念を使用した拡張検索</li>
                    <li>• フィルターを使用した結果の最適化</li>
                  </ul>
                </div>
              </Card>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}