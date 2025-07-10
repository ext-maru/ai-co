'use client'

import React from 'react'
import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown, Minus, Calendar, Clock, Target, Award } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Progress } from '@/components/ui/Progress'

interface TimelineEvent {
  id: string
  date: string
  type: 'milestone' | 'task' | 'update' | 'risk'
  title: string
  description?: string
  impact?: 'positive' | 'negative' | 'neutral'
  progress?: number
}

interface ProgressMetric {
  label: string
  value: number
  target: number
  unit: string
  trend: 'up' | 'down' | 'stable'
  change: number
}

interface ProgressTrackerProps {
  projectId: string
  currentProgress: number
  targetProgress: number
  startDate: string
  endDate: string
  metrics: ProgressMetric[]
  timeline: TimelineEvent[]
  className?: string
}

export function ProgressTracker({
  projectId,
  currentProgress,
  targetProgress,
  startDate,
  endDate,
  metrics,
  timeline,
  className
}: ProgressTrackerProps) {
  const getTrendIcon = (trend: ProgressMetric['trend']) => {
    switch (trend) {
      case 'up': return <TrendingUp className="w-4 h-4 text-green-500" />
      case 'down': return <TrendingDown className="w-4 h-4 text-red-500" />
      case 'stable': return <Minus className="w-4 h-4 text-gray-500" />
    }
  }

  const getEventIcon = (type: TimelineEvent['type']) => {
    switch (type) {
      case 'milestone': return '🎯'
      case 'task': return '✅'
      case 'update': return '📝'
      case 'risk': return '⚠️'
    }
  }

  const getEventColor = (type: TimelineEvent['type'], impact?: TimelineEvent['impact']) => {
    if (impact === 'positive') return 'bg-green-100 text-green-800 border-green-200'
    if (impact === 'negative') return 'bg-red-100 text-red-800 border-red-200'

    switch (type) {
      case 'milestone': return 'bg-purple-100 text-purple-800 border-purple-200'
      case 'task': return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'update': return 'bg-gray-100 text-gray-800 border-gray-200'
      case 'risk': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
    }
  }

  const calculateDaysProgress = () => {
    const start = new Date(startDate)
    const end = new Date(endDate)
    const now = new Date()

    const totalDays = Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24))
    const elapsedDays = Math.ceil((now.getTime() - start.getTime()) / (1000 * 60 * 60 * 24))

    return {
      total: totalDays,
      elapsed: Math.max(0, Math.min(elapsedDays, totalDays)),
      remaining: Math.max(0, totalDays - elapsedDays),
      percentage: Math.round((elapsedDays / totalDays) * 100)
    }
  }

  const days = calculateDaysProgress()
  const progressDiff = currentProgress - targetProgress
  const isAhead = progressDiff > 0
  const isBehind = progressDiff < -5

  return (
    <div className={cn('space-y-6', className)}>
      {/* Overall Progress */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">全体進捗</h3>
          <Badge
            variant="secondary"
            className={cn(
              isAhead ? 'bg-green-100 text-green-800' :
              isBehind ? 'bg-red-100 text-red-800' :
              'bg-gray-100 text-gray-800'
            )}
          >
            {isAhead ? `予定より${Math.abs(progressDiff)}%先行` :
             isBehind ? `予定より${Math.abs(progressDiff)}%遅延` :
             '予定通り'}
          </Badge>
        </div>

        <div className="space-y-4">
          {/* Current Progress */}
          <div>
            <div className="flex justify-between text-sm mb-2">
              <span className="text-gray-600">実際の進捗</span>
              <span className="font-semibold text-gray-900">{currentProgress}%</span>
            </div>
            <Progress value={currentProgress} className="h-3 bg-gray-200">
              <div className="h-full bg-goldenrod-500 rounded-full relative">
                <div className="absolute right-2 top-1/2 transform -translate-y-1/2 text-xs text-white font-medium">
                  {currentProgress}%
                </div>
              </div>
            </Progress>
          </div>

          {/* Target Progress */}
          <div>
            <div className="flex justify-between text-sm mb-2">
              <span className="text-gray-600">目標進捗</span>
              <span className="font-medium text-gray-700">{targetProgress}%</span>
            </div>
            <div className="relative">
              <Progress value={100} className="h-2 bg-gray-100" />
              <div
                className="absolute top-0 left-0 h-2 bg-gray-400 rounded-full"
                style={{ width: `${targetProgress}%` }}
              />
              <div
                className="absolute top-1/2 transform -translate-y-1/2 w-0.5 h-4 bg-gray-600"
                style={{ left: `${targetProgress}%` }}
              />
            </div>
          </div>

          {/* Time Progress */}
          <div className="pt-4 border-t border-gray-200">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                <Calendar className="w-4 h-4 text-gray-500" />
                <span className="text-sm text-gray-600">経過日数</span>
              </div>
              <span className="text-sm font-medium text-gray-900">
                {days.elapsed} / {days.total} 日 ({days.percentage}%)
              </span>
            </div>
            <Progress value={days.percentage} className="h-2" />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>{new Date(startDate).toLocaleDateString('ja-JP')}</span>
              <span className="font-medium">残り{days.remaining}日</span>
              <span>{new Date(endDate).toLocaleDateString('ja-JP')}</span>
            </div>
          </div>
        </div>
      </Card>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {metrics.map((metric) => (
          <motion.div
            key={metric.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            whileHover={{ scale: 1.02 }}
          >
            <Card className="p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">{metric.label}</span>
                {getTrendIcon(metric.trend)}
              </div>

              <div className="flex items-baseline space-x-2 mb-2">
                <span className="text-2xl font-bold text-gray-900">{metric.value}</span>
                <span className="text-sm text-gray-500">/ {metric.target} {metric.unit}</span>
              </div>

              <Progress
                value={(metric.value / metric.target) * 100}
                className="h-1.5 mb-2"
              />

              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-500">
                  達成率: {Math.round((metric.value / metric.target) * 100)}%
                </span>
                <span className={cn(
                  'font-medium',
                  metric.trend === 'up' ? 'text-green-600' :
                  metric.trend === 'down' ? 'text-red-600' :
                  'text-gray-600'
                )}>
                  {metric.trend === 'up' ? '+' : metric.trend === 'down' ? '-' : ''}{metric.change}%
                </span>
              </div>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Timeline */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Clock className="w-5 h-5 mr-2 text-goldenrod-600" />
          進捗タイムライン
        </h3>

        <div className="relative">
          {/* Timeline line */}
          <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-200" />

          <div className="space-y-4">
            {timeline.map((event, index) => (
              <motion.div
                key={event.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className="relative flex items-start"
              >
                {/* Timeline node */}
                <div className="absolute left-6 w-3 h-3 bg-white border-2 border-goldenrod-400 rounded-full transform -translate-x-1/2" />

                {/* Event content */}
                <div className="ml-12 flex-1">
                  <div className={cn(
                    'p-3 rounded-lg border',
                    getEventColor(event.type, event.impact)
                  )}>
                    <div className="flex items-start justify-between mb-1">
                      <div className="flex items-center space-x-2">
                        <span className="text-lg">{getEventIcon(event.type)}</span>
                        <h4 className="font-medium text-gray-900">{event.title}</h4>
                      </div>
                      <span className="text-xs text-gray-500">
                        {new Date(event.date).toLocaleDateString('ja-JP')}
                      </span>
                    </div>

                    {event.description && (
                      <p className="text-sm text-gray-600 mt-1">{event.description}</p>
                    )}

                    {event.progress !== undefined && (
                      <div className="flex items-center mt-2 space-x-2">
                        <Progress value={event.progress} className="h-1.5 flex-1" />
                        <span className="text-xs font-medium text-gray-700">
                          {event.progress}%
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </Card>

      {/* Achievement Banner */}
      {currentProgress >= 100 && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-gradient-to-r from-goldenrod-400 to-goldenrod-600 rounded-lg p-6 text-white"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Award className="w-12 h-12" />
              <div>
                <h3 className="text-xl font-bold">プロジェクト完了！</h3>
                <p className="text-goldenrod-100">
                  すべてのタスクが完了しました。お疲れ様でした！
                </p>
              </div>
            </div>
            <Badge className="bg-white text-goldenrod-600 text-lg px-4 py-2">
              100% 達成
            </Badge>
          </div>
        </motion.div>
      )}
    </div>
  )
}
