'use client'

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Sparkles, Lightbulb, TrendingUp, ArrowRight, ThumbsUp, ThumbsDown, BookOpen, Users, Code } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'

interface Suggestion {
  id: string
  type: 'search_refinement' | 'related_content' | 'learning_path' | 'collaboration' | 'automation'
  title: string
  description: string
  confidence: number
  reasoning: string
  actions: {
    id: string
    label: string
    type: 'primary' | 'secondary'
    action: string
  }[]
  metadata: {
    source: string
    tags: string[]
    estimatedValue: 'high' | 'medium' | 'low'
    difficulty: 'easy' | 'medium' | 'hard'
  }
}

interface InsightPattern {
  id: string
  pattern: string
  frequency: number
  impact: number
  trend: 'rising' | 'stable' | 'declining'
  examples: string[]
}

interface AISuggestionSystemProps {
  currentQuery?: string
  userContext: {
    role: string
    department: string
    recentQueries: string[]
    preferences: string[]
  }
  suggestions: Suggestion[]
  insights: InsightPattern[]
  onSuggestionClick?: (suggestion: Suggestion) => void
  onFeedback?: (suggestionId: string, feedback: 'positive' | 'negative') => void
  className?: string
}

export function AISuggestionSystem({
  currentQuery,
  userContext,
  suggestions,
  insights,
  onSuggestionClick,
  onFeedback,
  className
}: AISuggestionSystemProps) {
  const [activeTab, setActiveTab] = useState<'suggestions' | 'insights' | 'patterns'>('suggestions')
  const [feedbackGiven, setFeedbackGiven] = useState<Set<string>>(new Set())
  const [processingFeedback, setProcessingFeedback] = useState<Set<string>>(new Set())

  const getSuggestionIcon = (type: Suggestion['type']) => {
    switch (type) {
      case 'search_refinement': return <Sparkles className="w-5 h-5" />
      case 'related_content': return <BookOpen className="w-5 h-5" />
      case 'learning_path': return <TrendingUp className="w-5 h-5" />
      case 'collaboration': return <Users className="w-5 h-5" />
      case 'automation': return <Code className="w-5 h-5" />
    }
  }

  const getSuggestionColor = (type: Suggestion['type']) => {
    switch (type) {
      case 'search_refinement': return 'bg-lime-100 text-lime-800'
      case 'related_content': return 'bg-blue-100 text-blue-800'
      case 'learning_path': return 'bg-purple-100 text-purple-800'
      case 'collaboration': return 'bg-orange-100 text-orange-800'
      case 'automation': return 'bg-gray-100 text-gray-800'
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600'
    if (confidence >= 0.6) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getValueColor = (value: Suggestion['metadata']['estimatedValue']) => {
    switch (value) {
      case 'high': return 'bg-green-100 text-green-800'
      case 'medium': return 'bg-yellow-100 text-yellow-800'
      case 'low': return 'bg-gray-100 text-gray-800'
    }
  }

  const handleFeedback = async (suggestionId: string, feedback: 'positive' | 'negative') => {
    setProcessingFeedback(prev => new Set(prev).add(suggestionId))
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 500))
    
    setFeedbackGiven(prev => new Set(prev).add(suggestionId))
    setProcessingFeedback(prev => {
      const next = new Set(prev)
      next.delete(suggestionId)
      return next
    })
    
    onFeedback?.(suggestionId, feedback)
  }

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900 flex items-center">
            <Lightbulb className="w-5 h-5 mr-2 text-lime-600" />
            AI提案システム
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            あなたの検索パターンと文脈に基づいたパーソナライズされた提案
          </p>
        </div>
        
        <Badge variant="secondary" className="bg-lime-100 text-lime-800">
          {userContext.role} • {userContext.department}
        </Badge>
      </div>

      {/* Context Banner */}
      {currentQuery && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gradient-to-r from-lime-50 to-green-50 border border-lime-200 rounded-lg p-4"
        >
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium text-lime-900">現在のクエリ: "{currentQuery}"</h3>
              <p className="text-sm text-lime-700 mt-1">
                あなたの検索履歴と役割に基づいて、以下の提案を生成しました
              </p>
            </div>
            <div className="flex items-center space-x-2 text-sm text-lime-600">
              <Sparkles className="w-4 h-4" />
              <span>AI分析中</span>
            </div>
          </div>
        </motion.div>
      )}

      {/* Tabs */}
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg w-fit">
        {[
          { id: 'suggestions', label: '提案' },
          { id: 'insights', label: 'インサイト' },
          { id: 'patterns', label: 'パターン分析' }
        ].map(({ id, label }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id as any)}
            className={cn(
              'px-4 py-2 rounded-md text-sm font-medium transition-all duration-200',
              activeTab === id
                ? 'bg-white text-lime-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            )}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Content */}
      <AnimatePresence mode="wait">
        {activeTab === 'suggestions' && (
          <motion.div
            key="suggestions"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {suggestions.map((suggestion, index) => (
                <motion.div
                  key={suggestion.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Card className="p-6 h-full flex flex-col hover:shadow-lg transition-all duration-200">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center space-x-3">
                        <div className={cn('p-2 rounded-lg', getSuggestionColor(suggestion.type))}>
                          {getSuggestionIcon(suggestion.type)}
                        </div>
                        <div>
                          <h3 className="font-semibold text-gray-900">{suggestion.title}</h3>
                          <div className="flex items-center space-x-2 mt-1">
                            <Badge className={cn('text-xs', getSuggestionColor(suggestion.type))}>
                              {suggestion.type.replace('_', ' ')}
                            </Badge>
                            <Badge className={cn('text-xs', getValueColor(suggestion.metadata.estimatedValue))}>
                              {suggestion.metadata.estimatedValue} value
                            </Badge>
                          </div>
                        </div>
                      </div>
                      
                      <div className="text-right">
                        <div className={cn('text-sm font-semibold', getConfidenceColor(suggestion.confidence))}>
                          {Math.round(suggestion.confidence * 100)}%
                        </div>
                        <div className="text-xs text-gray-500">信頼度</div>
                      </div>
                    </div>
                    
                    <p className="text-gray-600 mb-4 flex-1">{suggestion.description}</p>
                    
                    <div className="mb-4 p-3 bg-gray-50 rounded-lg">
                      <h4 className="text-sm font-medium text-gray-700 mb-1">AIの推論:</h4>
                      <p className="text-sm text-gray-600">{suggestion.reasoning}</p>
                    </div>
                    
                    {suggestion.metadata.tags.length > 0 && (
                      <div className="mb-4">
                        <div className="flex flex-wrap gap-1">
                          {suggestion.metadata.tags.map((tag) => (
                            <span
                              key={tag}
                              className="px-2 py-1 bg-lime-50 text-lime-700 text-xs rounded"
                            >
                              #{tag}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    <div className="space-y-3">
                      <div className="flex space-x-2">
                        {suggestion.actions.map((action) => (
                          <Button
                            key={action.id}
                            variant={action.type === 'primary' ? 'primary' : 'outline'}
                            size="sm"
                            onClick={() => onSuggestionClick?.(suggestion)}
                            className={action.type === 'primary' ? 'bg-lime-600 hover:bg-lime-700' : ''}
                          >
                            {action.label}
                            <ArrowRight className="w-3 h-3 ml-1" />
                          </Button>
                        ))}
                      </div>
                      
                      {!feedbackGiven.has(suggestion.id) && (
                        <div className="flex items-center justify-between pt-3 border-t">
                          <span className="text-sm text-gray-600">この提案は役に立ちましたか？</span>
                          <div className="flex space-x-2">
                            <button
                              onClick={() => handleFeedback(suggestion.id, 'positive')}
                              disabled={processingFeedback.has(suggestion.id)}
                              className="p-1 text-gray-400 hover:text-green-500 transition-colors"
                            >
                              <ThumbsUp className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleFeedback(suggestion.id, 'negative')}
                              disabled={processingFeedback.has(suggestion.id)}
                              className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                            >
                              <ThumbsDown className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      )}
                      
                      {feedbackGiven.has(suggestion.id) && (
                        <div className="text-center text-sm text-green-600 pt-3 border-t">
                          フィードバックありがとうございます！
                        </div>
                      )}
                    </div>
                  </Card>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}

        {activeTab === 'insights' && (
          <motion.div
            key="insights"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-6"
          >
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">パーソナライズされたインサイト</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="space-y-4">
                  <h4 className="font-medium text-gray-700">あなたの検索パターン</h4>
                  <div className="space-y-2">
                    {userContext.recentQueries.slice(0, 5).map((query, index) => (
                      <div key={index} className="text-sm p-2 bg-gray-50 rounded">
                        "{query}"
                      </div>
                    ))}
                  </div>
                </div>
                
                <div className="space-y-4">
                  <h4 className="font-medium text-gray-700">推奨される探索領域</h4>
                  <div className="space-y-2">
                    {['APIドキュメント', 'セキュリティガイド', 'パフォーマンス最適化'].map((area) => (
                      <div key={area} className="flex items-center justify-between text-sm p-2 bg-lime-50 rounded">
                        <span>{area}</span>
                        <Badge variant="secondary" className="text-xs">関連度高</Badge>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div className="space-y-4">
                  <h4 className="font-medium text-gray-700">チーム内トレンド</h4>
                  <div className="space-y-2">
                    {[
                      { topic: 'マイクロサービス', trend: 'rising' },
                      { topic: 'Kubernetes', trend: 'stable' },
                      { topic: 'GraphQL', trend: 'rising' }
                    ].map((item) => (
                      <div key={item.topic} className="flex items-center justify-between text-sm p-2 bg-blue-50 rounded">
                        <span>{item.topic}</span>
                        <TrendingUp className={cn(
                          'w-4 h-4',
                          item.trend === 'rising' ? 'text-green-500' : 'text-blue-500'
                        )} />
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </Card>
          </motion.div>
        )}

        {activeTab === 'patterns' && (
          <motion.div
            key="patterns"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-6"
          >
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {insights.map((insight, index) => (
                <motion.div
                  key={insight.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Card className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h3 className="font-semibold text-gray-900">{insight.pattern}</h3>
                        <div className="flex items-center space-x-3 mt-2 text-sm text-gray-600">
                          <span>出現頻度: {insight.frequency}回</span>
                          <span>•</span>
                          <span>影響度: {insight.impact}/10</span>
                        </div>
                      </div>
                      <Badge
                        className={cn(
                          'text-xs',
                          insight.trend === 'rising' ? 'bg-green-100 text-green-800' :
                          insight.trend === 'declining' ? 'bg-red-100 text-red-800' :
                          'bg-gray-100 text-gray-800'
                        )}
                      >
                        {insight.trend === 'rising' ? '上昇' :
                         insight.trend === 'declining' ? '下降' : '安定'}
                      </Badge>
                    </div>
                    
                    <div className="mb-4">
                      <h4 className="text-sm font-medium text-gray-700 mb-2">例:</h4>
                      <div className="space-y-1">
                        {insight.examples.slice(0, 3).map((example, i) => (
                          <div key={i} className="text-sm text-gray-600 p-2 bg-gray-50 rounded">
                            "{example}"
                          </div>
                        ))}
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-lime-500 h-2 rounded-full"
                            style={{ width: `${(insight.impact / 10) * 100}%` }}
                          />
                        </div>
                      </div>
                      <Button variant="ghost" size="sm">
                        詳細を見る
                      </Button>
                    </div>
                  </Card>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}