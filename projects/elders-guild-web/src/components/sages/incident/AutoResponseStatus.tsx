'use client'

import React, { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Zap, Play, Pause, CheckCircle, XCircle, RefreshCw, Settings, Clock } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Progress } from '@/components/ui/Progress'

interface AutoResponse {
  id: string
  name: string
  description: string
  trigger: {
    type: 'metric' | 'alert' | 'schedule'
    condition: string
    threshold?: number
  }
  actions: {
    id: string
    type: 'scale' | 'restart' | 'failover' | 'notify' | 'script'
    target: string
    status: 'pending' | 'running' | 'completed' | 'failed'
    progress?: number
    output?: string
  }[]
  status: 'active' | 'paused' | 'disabled'
  lastTriggered?: string
  successRate: number
  averageExecutionTime: number // seconds
  executionHistory: {
    id: string
    timestamp: string
    result: 'success' | 'failure' | 'partial'
    duration: number
    triggeredBy: string
  }[]
}

interface AutoResponseStatusProps {
  responses: AutoResponse[]
  onResponseToggle?: (responseId: string, status: AutoResponse['status']) => void
  onResponseExecute?: (responseId: string) => void
  className?: string
}

export function AutoResponseStatus({
  responses,
  onResponseToggle,
  onResponseExecute,
  className
}: AutoResponseStatusProps) {
  const [selectedResponse, setSelectedResponse] = useState<AutoResponse | null>(null)
  const [executingResponses, setExecutingResponses] = useState<Set<string>>(new Set())
  const [realtimeMetrics, setRealtimeMetrics] = useState<{ [key: string]: number }>({})

  // Simulate real-time metrics update
  useEffect(() => {
    const interval = setInterval(() => {
      setRealtimeMetrics(prev => {
        const next = { ...prev }
        responses.forEach(response => {
          if (response.status === 'active') {
            next[response.id] = Math.random() * 100
          }
        })
        return next
      })
    }, 2000)

    return () => clearInterval(interval)
  }, [responses])

  const getStatusColor = (status: AutoResponse['status']) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800 border-green-200'
      case 'paused': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'disabled': return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getActionIcon = (type: AutoResponse['actions'][0]['type']) => {
    switch (type) {
      case 'scale': return '⚡'
      case 'restart': return '🔄'
      case 'failover': return '🔀'
      case 'notify': return '📢'
      case 'script': return '📜'
    }
  }

  const getActionStatusColor = (status: AutoResponse['actions'][0]['status']) => {
    switch (status) {
      case 'pending': return 'text-gray-500'
      case 'running': return 'text-blue-500'
      case 'completed': return 'text-green-500'
      case 'failed': return 'text-red-500'
    }
  }

  const getTriggerIcon = (type: AutoResponse['trigger']['type']) => {
    switch (type) {
      case 'metric': return '📊'
      case 'alert': return '🚨'
      case 'schedule': return '📅'
    }
  }

  const handleExecute = async (responseId: string) => {
    setExecutingResponses(prev => new Set(prev).add(responseId))
    onResponseExecute?.(responseId)

    // Simulate execution
    setTimeout(() => {
      setExecutingResponses(prev => {
        const next = new Set(prev)
        next.delete(responseId)
        return next
      })
    }, 3000)
  }

  const activeResponses = responses.filter(r => r.status === 'active')
  const totalExecutions = responses.reduce((acc, r) => acc + r.executionHistory.length, 0)
  const avgSuccessRate = responses.reduce((acc, r) => acc + r.successRate, 0) / responses.length || 0

  return (
    <div className={cn('space-y-6', className)}>
      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-6 bg-gradient-to-br from-green-50 to-white border-green-200">
          <div className="flex items-center justify-between mb-2">
            <Zap className="w-8 h-8 text-green-600" />
            <Badge variant="secondary" className="bg-green-100 text-green-800">
              アクティブ
            </Badge>
          </div>
          <h3 className="text-2xl font-bold text-gray-900">{activeResponses.length}</h3>
          <p className="text-sm text-gray-600">有効な自動対応</p>
        </Card>

        <Card className="p-6 bg-gradient-to-br from-blue-50 to-white border-blue-200">
          <div className="flex items-center justify-between mb-2">
            <RefreshCw className="w-8 h-8 text-blue-600" />
            <span className="text-sm font-medium text-blue-600">今日</span>
          </div>
          <h3 className="text-2xl font-bold text-gray-900">{totalExecutions}</h3>
          <p className="text-sm text-gray-600">総実行回数</p>
        </Card>

        <Card className="p-6 bg-gradient-to-br from-purple-50 to-white border-purple-200">
          <div className="flex items-center justify-between mb-2">
            <CheckCircle className="w-8 h-8 text-purple-600" />
            <span className="text-sm font-medium text-green-600">
              {avgSuccessRate >= 90 ? '良好' : avgSuccessRate >= 70 ? '普通' : '要改善'}
            </span>
          </div>
          <h3 className="text-2xl font-bold text-gray-900">{avgSuccessRate.toFixed(1)}%</h3>
          <p className="text-sm text-gray-600">平均成功率</p>
        </Card>

        <Card className="p-6 bg-gradient-to-br from-orange-50 to-white border-orange-200">
          <div className="flex items-center justify-between mb-2">
            <Clock className="w-8 h-8 text-orange-600" />
            <Badge variant="secondary" className="text-xs">
              平均
            </Badge>
          </div>
          <h3 className="text-2xl font-bold text-gray-900">
            {responses.reduce((acc, r) => acc + r.averageExecutionTime, 0) / responses.length || 0}s
          </h3>
          <p className="text-sm text-gray-600">実行時間</p>
        </Card>
      </div>

      {/* Auto Response List */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          {responses.map((response) => {
            const isExecuting = executingResponses.has(response.id)
            const currentMetric = realtimeMetrics[response.id] || 0

            return (
              <motion.div
                key={response.id}
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
              >
                <Card
                  className={cn(
                    'p-6 cursor-pointer transition-all duration-200',
                    'hover:shadow-lg',
                    response.status === 'active' && 'border-green-300',
                    selectedResponse?.id === response.id && 'ring-2 ring-crimson-500'
                  )}
                  onClick={() => setSelectedResponse(response)}
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <h3 className="font-semibold text-gray-900">{response.name}</h3>
                        <Badge className={cn('text-xs', getStatusColor(response.status))}>
                          {response.status === 'active' ? '有効' :
                           response.status === 'paused' ? '一時停止' : '無効'}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-600">{response.description}</p>
                    </div>

                    <div className="flex items-center space-x-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation()
                          onResponseToggle?.(
                            response.id,
                            response.status === 'active' ? 'paused' : 'active'
                          )
                        }}
                      >
                        {response.status === 'active' ? (
                          <Pause className="w-4 h-4" />
                        ) : (
                          <Play className="w-4 h-4" />
                        )}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleExecute(response.id)
                        }}
                        disabled={response.status !== 'active' || isExecuting}
                      >
                        {isExecuting ? (
                          <RefreshCw className="w-4 h-4 animate-spin" />
                        ) : (
                          <Zap className="w-4 h-4" />
                        )}
                      </Button>
                    </div>
                  </div>

                  {/* Trigger Info */}
                  <div className="mb-4 p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center space-x-2">
                        <span className="text-lg">{getTriggerIcon(response.trigger.type)}</span>
                        <span className="text-gray-600">トリガー:</span>
                        <span className="font-medium text-gray-900">{response.trigger.condition}</span>
                      </div>
                      {response.trigger.type === 'metric' && response.status === 'active' && (
                        <div className="flex items-center space-x-2">
                          <span className="text-xs text-gray-500">現在値:</span>
                          <span className={cn(
                            'font-medium',
                            currentMetric > (response.trigger.threshold || 0) ? 'text-red-600' : 'text-green-600'
                          )}>
                            {currentMetric.toFixed(1)}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="mb-4">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">実行アクション</h4>
                    <div className="space-y-1">
                      {response.actions.map((action) => (
                        <div
                          key={action.id}
                          className="flex items-center justify-between p-2 bg-gray-50 rounded text-sm"
                        >
                          <div className="flex items-center space-x-2">
                            <span className="text-lg">{getActionIcon(action.type)}</span>
                            <span className="font-medium">{action.type}</span>
                            <span className="text-gray-500">→</span>
                            <span className="text-gray-600">{action.target}</span>
                          </div>
                          {action.status === 'running' && action.progress && (
                            <div className="w-24">
                              <Progress value={action.progress} className="h-1.5" />
                            </div>
                          )}
                          {action.status !== 'running' && (
                            <span className={cn('font-medium', getActionStatusColor(action.status))}>
                              {action.status === 'completed' ? '✓' :
                               action.status === 'failed' ? '✗' :
                               action.status === 'pending' ? '•' : ''}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Metrics */}
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center space-x-4">
                      <div className="flex items-center space-x-1">
                        <CheckCircle className="w-4 h-4 text-green-500" />
                        <span className="text-gray-600">成功率:</span>
                        <span className="font-medium">{response.successRate}%</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Clock className="w-4 h-4 text-gray-400" />
                        <span className="text-gray-600">平均実行時間:</span>
                        <span className="font-medium">{response.averageExecutionTime}s</span>
                      </div>
                    </div>
                    {response.lastTriggered && (
                      <span className="text-xs text-gray-500">
                        最終実行: {new Date(response.lastTriggered).toLocaleString('ja-JP')}
                      </span>
                    )}
                  </div>
                </Card>
              </motion.div>
            )
          })}
        </div>

        {/* Response Details */}
        <div className="lg:col-span-1">
          <AnimatePresence mode="wait">
            {selectedResponse ? (
              <motion.div
                key={selectedResponse.id}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="sticky top-6"
              >
                <Card className="p-6">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">実行履歴</h2>

                  <div className="space-y-3">
                    {selectedResponse.executionHistory.slice(0, 10).map((execution) => (
                      <div
                        key={execution.id}
                        className={cn(
                          'p-3 rounded-lg border',
                          execution.result === 'success' && 'bg-green-50 border-green-200',
                          execution.result === 'failure' && 'bg-red-50 border-red-200',
                          execution.result === 'partial' && 'bg-yellow-50 border-yellow-200'
                        )}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium text-gray-900">
                            {execution.result === 'success' ? '成功' :
                             execution.result === 'failure' ? '失敗' : '部分的成功'}
                          </span>
                          <span className="text-xs text-gray-500">
                            {execution.duration}s
                          </span>
                        </div>
                        <div className="text-xs text-gray-600">
                          <div>{new Date(execution.timestamp).toLocaleString('ja-JP')}</div>
                          <div>トリガー: {execution.triggeredBy}</div>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="mt-4 pt-4 border-t">
                    <Button variant="outline" size="sm" className="w-full">
                      <Settings className="w-4 h-4 mr-2" />
                      設定を編集
                    </Button>
                  </div>
                </Card>
              </motion.div>
            ) : (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="h-full flex items-center justify-center text-gray-400"
              >
                <div className="text-center">
                  <Zap className="w-12 h-12 mx-auto mb-2" />
                  <p>自動対応を選択してください</p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}
