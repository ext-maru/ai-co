'use client'

import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronUp, ChevronDown, Flag, Clock, AlertTriangle, Zap, Filter, SortAsc } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Avatar } from '@/components/ui/Avatar'

interface PriorityItem {
  id: string
  title: string
  description: string
  priority: 'low' | 'medium' | 'high' | 'urgent'
  impact: 'low' | 'medium' | 'high' | 'critical'
  effort: 'small' | 'medium' | 'large' | 'extra-large'
  status: 'pending' | 'in_progress' | 'blocked' | 'completed'
  assignee?: {
    id: string
    name: string
    avatar: string
  }
  deadline?: string
  dependencies: string[]
  score: number // Calculated priority score
}

interface PriorityManagerProps {
  items: PriorityItem[]
  onItemUpdate?: (item: PriorityItem) => void
  onPriorityChange?: (itemId: string, newPriority: PriorityItem['priority']) => void
  className?: string
}

export function PriorityManager({ items, onItemUpdate, onPriorityChange, className }: PriorityManagerProps) {
  const [sortBy, setSortBy] = useState<'score' | 'deadline' | 'impact' | 'effort'>('score')
  const [filterStatus, setFilterStatus] = useState<PriorityItem['status'] | 'all'>('all')
  const [selectedItem, setSelectedItem] = useState<PriorityItem | null>(null)

  const getPriorityColor = (priority: PriorityItem['priority']) => {
    switch (priority) {
      case 'low': return 'bg-gray-100 text-gray-700 border-gray-300'
      case 'medium': return 'bg-yellow-100 text-yellow-700 border-yellow-300'
      case 'high': return 'bg-orange-100 text-orange-700 border-orange-300'
      case 'urgent': return 'bg-red-100 text-red-700 border-red-300'
    }
  }

  const getPriorityIcon = (priority: PriorityItem['priority']) => {
    switch (priority) {
      case 'low': return '▽'
      case 'medium': return '◇'
      case 'high': return '△'
      case 'urgent': return '🔥'
    }
  }

  const getImpactColor = (impact: PriorityItem['impact']) => {
    switch (impact) {
      case 'low': return 'text-gray-500'
      case 'medium': return 'text-blue-500'
      case 'high': return 'text-orange-500'
      case 'critical': return 'text-red-500'
    }
  }

  const getEffortSize = (effort: PriorityItem['effort']) => {
    switch (effort) {
      case 'small': return 'XS'
      case 'medium': return 'M'
      case 'large': return 'L'
      case 'extra-large': return 'XL'
    }
  }

  const getStatusColor = (status: PriorityItem['status']) => {
    switch (status) {
      case 'pending': return 'bg-gray-100 text-gray-700'
      case 'in_progress': return 'bg-blue-100 text-blue-700'
      case 'blocked': return 'bg-red-100 text-red-700'
      case 'completed': return 'bg-green-100 text-green-700'
    }
  }

  const sortedItems = [...items]
    .filter(item => filterStatus === 'all' || item.status === filterStatus)
    .sort((a, b) => {
      switch (sortBy) {
        case 'score': return b.score - a.score
        case 'deadline':
          if (!a.deadline) return 1
          if (!b.deadline) return -1
          return new Date(a.deadline).getTime() - new Date(b.deadline).getTime()
        case 'impact':
          const impactOrder = { critical: 4, high: 3, medium: 2, low: 1 }
          return impactOrder[b.impact] - impactOrder[a.impact]
        case 'effort':
          const effortOrder = { 'extra-large': 4, large: 3, medium: 2, small: 1 }
          return effortOrder[a.effort] - effortOrder[b.effort]
        default: return 0
      }
    })

  const handlePriorityChange = (itemId: string, direction: 'up' | 'down') => {
    const item = items.find(i => i.id === itemId)
    if (!item) return

    const priorities: PriorityItem['priority'][] = ['low', 'medium', 'high', 'urgent']
    const currentIndex = priorities.indexOf(item.priority)
    const newIndex = direction === 'up' 
      ? Math.min(currentIndex + 1, priorities.length - 1)
      : Math.max(currentIndex - 1, 0)
    
    if (currentIndex !== newIndex) {
      onPriorityChange?.(itemId, priorities[newIndex])
    }
  }

  const getDaysUntilDeadline = (deadline?: string) => {
    if (!deadline) return null
    const now = new Date()
    const due = new Date(deadline)
    const diffTime = due.getTime() - now.getTime()
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    return diffDays
  }

  // Priority Matrix
  const getMatrixPosition = (item: PriorityItem) => {
    const impactScore = { low: 1, medium: 2, high: 3, critical: 4 }[item.impact]
    const effortScore = { small: 1, medium: 2, large: 3, 'extra-large': 4 }[item.effort]
    return { x: effortScore, y: impactScore }
  }

  return (
    <div className={cn('space-y-6', className)}>
      {/* Controls */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-gray-500" />
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value as any)}
              className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-goldenrod-500"
            >
              <option value="all">すべて</option>
              <option value="pending">保留中</option>
              <option value="in_progress">進行中</option>
              <option value="blocked">ブロック</option>
              <option value="completed">完了</option>
            </select>
          </div>
          
          <div className="flex items-center space-x-2">
            <SortAsc className="w-4 h-4 text-gray-500" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-goldenrod-500"
            >
              <option value="score">優先度スコア</option>
              <option value="deadline">締切日</option>
              <option value="impact">影響度</option>
              <option value="effort">作業量</option>
            </select>
          </div>
        </div>
        
        <Badge variant="secondary" className="bg-goldenrod-100 text-goldenrod-800">
          {sortedItems.filter(i => i.status !== 'completed').length} 件のアクティブタスク
        </Badge>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Priority List */}
        <div className="lg:col-span-2 space-y-4">
          <AnimatePresence mode="popLayout">
            {sortedItems.map((item, index) => {
              const daysUntil = getDaysUntilDeadline(item.deadline)
              const isOverdue = daysUntil !== null && daysUntil < 0
              const isDueSoon = daysUntil !== null && daysUntil >= 0 && daysUntil <= 3

              return (
                <motion.div
                  key={item.id}
                  layout
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Card
                    className={cn(
                      'p-4 cursor-pointer transition-all duration-200',
                      'hover:shadow-lg hover:border-goldenrod-300',
                      selectedItem?.id === item.id && 'ring-2 ring-goldenrod-500 border-goldenrod-500',
                      item.status === 'blocked' && 'bg-red-50',
                      item.status === 'completed' && 'opacity-60'
                    )}
                    onClick={() => setSelectedItem(item)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <div className="flex items-center space-x-1">
                            <span className="text-xl">{getPriorityIcon(item.priority)}</span>
                            <Badge className={cn('text-xs border', getPriorityColor(item.priority))}>
                              {item.priority === 'urgent' ? '緊急' :
                               item.priority === 'high' ? '高' :
                               item.priority === 'medium' ? '中' : '低'}
                            </Badge>
                          </div>
                          
                          <Badge className={cn('text-xs', getStatusColor(item.status))}>
                            {item.status === 'pending' ? '保留' :
                             item.status === 'in_progress' ? '進行中' :
                             item.status === 'blocked' ? 'ブロック' : '完了'}
                          </Badge>
                          
                          {item.dependencies.length > 0 && (
                            <Badge variant="outline" className="text-xs">
                              依存: {item.dependencies.length}
                            </Badge>
                          )}
                        </div>
                        
                        <h3 className="font-medium text-gray-900 mb-1">{item.title}</h3>
                        
                        {item.description && (
                          <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                            {item.description}
                          </p>
                        )}
                        
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-4 text-sm">
                            <div className="flex items-center space-x-1">
                              <Zap className={cn('w-4 h-4', getImpactColor(item.impact))} />
                              <span className="text-gray-600">
                                影響: <span className="font-medium">{item.impact}</span>
                              </span>
                            </div>
                            
                            <div className="flex items-center space-x-1">
                              <Clock className="w-4 h-4 text-gray-400" />
                              <span className="text-gray-600">
                                作業量: <span className="font-medium">{getEffortSize(item.effort)}</span>
                              </span>
                            </div>
                            
                            {item.deadline && (
                              <div className={cn(
                                'flex items-center space-x-1',
                                isOverdue && 'text-red-600',
                                isDueSoon && !isOverdue && 'text-yellow-600'
                              )}>
                                <AlertTriangle className="w-4 h-4" />
                                <span className="font-medium">
                                  {isOverdue ? `${Math.abs(daysUntil)}日遅延` :
                                   daysUntil === 0 ? '今日' :
                                   `${daysUntil}日後`}
                                </span>
                              </div>
                            )}
                          </div>
                          
                          {item.assignee && (
                            <Avatar
                              src={item.assignee.avatar}
                              alt={item.assignee.name}
                              size="sm"
                              fallback={item.assignee.name.slice(0, 2)}
                            />
                          )}
                        </div>
                      </div>
                      
                      {/* Priority Controls */}
                      <div className="flex flex-col ml-4">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handlePriorityChange(item.id, 'up')
                          }}
                          disabled={item.priority === 'urgent' || item.status === 'completed'}
                          className={cn(
                            'p-1 rounded hover:bg-gray-100 transition-colors',
                            (item.priority === 'urgent' || item.status === 'completed') && 'opacity-50 cursor-not-allowed'
                          )}
                        >
                          <ChevronUp className="w-4 h-4" />
                        </button>
                        <div className="text-center text-xs font-bold text-gray-600 my-1">
                          {item.score}
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handlePriorityChange(item.id, 'down')
                          }}
                          disabled={item.priority === 'low' || item.status === 'completed'}
                          className={cn(
                            'p-1 rounded hover:bg-gray-100 transition-colors',
                            (item.priority === 'low' || item.status === 'completed') && 'opacity-50 cursor-not-allowed'
                          )}
                        >
                          <ChevronDown className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </Card>
                </motion.div>
              )
            })}
          </AnimatePresence>
        </div>

        {/* Priority Matrix */}
        <div className="lg:col-span-1">
          <Card className="p-6 sticky top-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">優先度マトリクス</h3>
            
            <div className="relative bg-gray-50 rounded-lg p-4 h-80">
              {/* Matrix Grid */}
              <div className="absolute inset-4 grid grid-cols-4 grid-rows-4 gap-px bg-gray-200">
                {Array.from({ length: 16 }).map((_, i) => {
                  const row = Math.floor(i / 4)
                  const col = i % 4
                  const isHighImpactLowEffort = row < 2 && col < 2
                  
                  return (
                    <div
                      key={i}
                      className={cn(
                        'bg-white',
                        isHighImpactLowEffort && 'bg-green-50'
                      )}
                    />
                  )
                })}
              </div>
              
              {/* Axis Labels */}
              <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 text-xs text-gray-500">
                作業量 →
              </div>
              <div className="absolute left-0 top-1/2 transform -translate-y-1/2 -rotate-90 text-xs text-gray-500">
                影響度 →
              </div>
              
              {/* Items on Matrix */}
              {sortedItems.map((item) => {
                const pos = getMatrixPosition(item)
                return (
                  <motion.div
                    key={item.id}
                    className="absolute w-8 h-8 transform -translate-x-1/2 -translate-y-1/2"
                    style={{
                      left: `${(pos.x - 0.5) * 25}%`,
                      bottom: `${(pos.y - 0.5) * 25}%`
                    }}
                    whileHover={{ scale: 1.2 }}
                  >
                    <div
                      className={cn(
                        'w-full h-full rounded-full flex items-center justify-center text-white font-bold text-xs cursor-pointer shadow-lg',
                        item.priority === 'urgent' && 'bg-red-500',
                        item.priority === 'high' && 'bg-orange-500',
                        item.priority === 'medium' && 'bg-yellow-500',
                        item.priority === 'low' && 'bg-gray-500'
                      )}
                      onClick={() => setSelectedItem(item)}
                    >
                      {item.title.slice(0, 2)}
                    </div>
                  </motion.div>
                )
              })}
              
              {/* Quadrant Labels */}
              <div className="absolute top-2 left-2 text-xs font-medium text-green-700">
                Quick Wins
              </div>
              <div className="absolute top-2 right-2 text-xs font-medium text-yellow-700">
                Major Projects
              </div>
              <div className="absolute bottom-2 left-2 text-xs font-medium text-gray-600">
                Fill Ins
              </div>
              <div className="absolute bottom-2 right-2 text-xs font-medium text-gray-600">
                Time Sinks
              </div>
            </div>
            
            {/* Legend */}
            <div className="mt-4 space-y-2">
              <h4 className="text-sm font-medium text-gray-700">凡例</h4>
              <div className="grid grid-cols-2 gap-2 text-xs">
                {[
                  { priority: 'urgent' as const, label: '緊急' },
                  { priority: 'high' as const, label: '高' },
                  { priority: 'medium' as const, label: '中' },
                  { priority: 'low' as const, label: '低' }
                ].map(({ priority, label }) => (
                  <div key={priority} className="flex items-center space-x-2">
                    <div className={cn(
                      'w-3 h-3 rounded-full',
                      priority === 'urgent' && 'bg-red-500',
                      priority === 'high' && 'bg-orange-500',
                      priority === 'medium' && 'bg-yellow-500',
                      priority === 'low' && 'bg-gray-500'
                    )} />
                    <span className="text-gray-600">{label}優先度</span>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}