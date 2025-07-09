'use client'

import React from 'react'
import { motion } from 'framer-motion'
import { BookOpen, Brain, Database, TrendingUp } from 'lucide-react'
import { KnowledgeSage as KnowledgeSageType } from '@/types/sages'
import { cn, getSageThemeClasses, formatMetricValue, formatJapaneseDateTime } from '@/lib/utils'

interface KnowledgeSageProps {
  sage: KnowledgeSageType
  isSelected?: boolean
  onSelect?: () => void
  className?: string
}

export function KnowledgeSage({ sage, isSelected = false, onSelect, className }: KnowledgeSageProps) {
  const theme = getSageThemeClasses('knowledge')
  
  return (
    <motion.div
      className={cn(
        'relative bg-white border rounded-lg p-6 cursor-pointer transition-all duration-300',
        theme.shadow,
        isSelected ? `ring-2 ${theme.ring} ${theme.border}` : 'border-gray-200 hover:border-knowledge-300',
        'hover:shadow-lg transform hover:-translate-y-1',
        className
      )}
      onClick={onSelect}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className={cn(
            'w-12 h-12 rounded-full flex items-center justify-center text-2xl',
            theme.primary,
            sage.status === 'active' && theme.glow
          )}>
            📚
          </div>
          <div>
            <h3 className="font-sage font-bold text-lg text-gray-900">
              {sage.name}
            </h3>
            <p className={cn('text-sm font-medium', theme.accent)}>
              {sage.title}
            </p>
          </div>
        </div>
        <div className={cn(
          'px-3 py-1 rounded-full text-xs font-medium',
          sage.status === 'active' ? 'bg-green-100 text-green-800' :
          sage.status === 'busy' ? 'bg-yellow-100 text-yellow-800' :
          'bg-gray-100 text-gray-800'
        )}>
          {sage.status === 'active' ? '活動中' : 
           sage.status === 'busy' ? '修行中' : '休息中'}
        </div>
      </div>

      {/* Activity Status */}
      <div className="mb-4">
        <p className="text-sm text-gray-600 mb-2">現在の活動:</p>
        <p className="text-base font-medium text-gray-900">{sage.activity}</p>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className={cn('p-3 rounded-lg', theme.secondary)}>
          <div className="flex items-center space-x-2 mb-1">
            <Brain className="w-4 h-4" />
            <span className="text-sm font-medium">{sage.metrics.primary.label}</span>
          </div>
          <p className="text-xl font-bold">{sage.metrics.primary.value}</p>
        </div>
        <div className={cn('p-3 rounded-lg', theme.secondary)}>
          <div className="flex items-center space-x-2 mb-1">
            <TrendingUp className="w-4 h-4" />
            <span className="text-sm font-medium">{sage.metrics.secondary.label}</span>
          </div>
          <p className="text-xl font-bold">{sage.metrics.secondary.value}</p>
        </div>
      </div>

      {/* Knowledge Base Stats */}
      <div className="mb-4">
        <div className="flex items-center space-x-2 mb-2">
          <Database className="w-4 h-4 text-knowledge-600" />
          <span className="text-sm font-medium text-gray-700">知識ベース統計</span>
        </div>
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">総文書数</span>
            <span className="font-medium">{formatMetricValue(sage.knowledgeBase.total)}</span>
          </div>
          <div className="space-y-1">
            {Object.entries(sage.knowledgeBase.categories).slice(0, 3).map(([category, count]) => (
              <div key={category} className="flex justify-between items-center">
                <span className="text-xs text-gray-500">{category}</span>
                <span className="text-xs font-medium">{formatMetricValue(count)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Updates */}
      <div className="mb-4">
        <div className="flex items-center space-x-2 mb-2">
          <BookOpen className="w-4 h-4 text-knowledge-600" />
          <span className="text-sm font-medium text-gray-700">最近の更新</span>
        </div>
        <div className="space-y-2">
          {sage.knowledgeBase.recentUpdates.slice(0, 2).map((update) => (
            <div key={update.id} className="p-2 bg-gray-50 rounded text-xs">
              <p className="font-medium text-gray-900 line-clamp-1">{update.title}</p>
              <div className="flex justify-between items-center mt-1">
                <span className="text-gray-500">{update.category}</span>
                <span className="text-gray-500">
                  {formatJapaneseDateTime(update.timestamp)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Specialties */}
      <div className="mb-4">
        <p className="text-sm font-medium text-gray-700 mb-2">専門分野:</p>
        <div className="flex flex-wrap gap-1">
          {sage.specialties.map((specialty, index) => (
            <span
              key={index}
              className={cn(
                'px-2 py-1 rounded text-xs font-medium',
                theme.secondary
              )}
            >
              {specialty}
            </span>
          ))}
        </div>
      </div>

      {/* Experience Bar */}
      <div className="mb-4">
        <div className="flex justify-between items-center mb-1">
          <span className="text-sm font-medium text-gray-700">レベル {sage.level}</span>
          <span className="text-xs text-gray-500">{sage.experience} XP</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className={cn('h-2 rounded-full', theme.primary)}
            style={{ width: `${Math.min((sage.experience % 1000) / 10, 100)}%` }}
          />
        </div>
      </div>

      {/* Last Active */}
      <div className="text-xs text-gray-500 text-center">
        最終活動: {formatJapaneseDateTime(sage.lastActive)}
      </div>

      {/* Floating Animation Elements */}
      {sage.status === 'active' && (
        <>
          <motion.div
            className="absolute -top-1 -right-1 w-3 h-3 bg-knowledge-400 rounded-full opacity-60"
            animate={{ scale: [1, 1.2, 1], opacity: [0.6, 1, 0.6] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
          <motion.div
            className="absolute top-2 right-8 w-2 h-2 bg-knowledge-300 rounded-full opacity-40"
            animate={{ scale: [1, 1.3, 1], opacity: [0.4, 0.8, 0.4] }}
            transition={{ duration: 2.5, repeat: Infinity, delay: 0.5 }}
          />
        </>
      )}
    </motion.div>
  )
}