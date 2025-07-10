'use client'

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Crown, Users, MessageCircle, TrendingUp, AlertTriangle, Target, Brain, Activity } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Avatar } from '@/components/ui/Avatar'
import { Progress } from '@/components/ui/Progress'

interface SageStatus {
  id: string
  name: string
  title: string
  avatar: string
  status: 'active' | 'busy' | 'idle'
  activity: string
  performance: {
    efficiency: number
    accuracy: number
    responseTime: number
  }
  recentActions: {
    id: string
    action: string
    timestamp: string
    impact: 'low' | 'medium' | 'high'
  }[]
  currentLoad: number
  specialization: string[]
}

interface CouncilDecision {
  id: string
  topic: string
  description: string
  priority: 'low' | 'medium' | 'high' | 'critical'
  participants: string[]
  status: 'proposed' | 'discussing' | 'voting' | 'decided' | 'implemented'
  proposal: {
    summary: string
    requiredActions: string[]
    expectedOutcome: string
    risksAndMitigation: string[]
  }
  votes: {
    sageId: string
    vote: 'approve' | 'reject' | 'abstain'
    reasoning: string
  }[]
  timeline: {
    proposed: string
    discussionStart?: string
    votingStart?: string
    decided?: string
    implemented?: string
  }
}

interface ElderCouncilModeProps {
  sages: SageStatus[]
  currentDecisions: CouncilDecision[]
  systemMetrics: {
    overallHealth: number
    coveragePercentage: number
    collaborationIndex: number
    emergingIssues: number
  }
  onCouncilAction?: (action: string, data: any) => void
  className?: string
}

export function ElderCouncilMode({
  sages,
  currentDecisions,
  systemMetrics,
  onCouncilAction,
  className
}: ElderCouncilModeProps) {
  const [selectedDecision, setSelectedDecision] = useState<CouncilDecision | null>(null)
  const [councilMode, setCouncilMode] = useState<'overview' | 'decisions' | 'performance' | 'insights'>('overview')
  const [realTimeUpdates, setRealTimeUpdates] = useState(true)

  // Simulate real-time updates
  useEffect(() => {
    if (!realTimeUpdates) return

    const interval = setInterval(() => {
      // Simulate sage activity updates
      // This would be connected to real WebSocket data in production
    }, 2000)

    return () => clearInterval(interval)
  }, [realTimeUpdates])

  const getSageIcon = (sageName: string) => {
    switch (sageName.toLowerCase()) {
      case 'knowledge sage': return '📚'
      case 'task oracle': return '📋'
      case 'crisis sage': return '🚨'
      case 'search mystic': return '🔍'
      default: return '🧙‍♂️'
    }
  }

  const getSageTheme = (sageName: string) => {
    switch (sageName.toLowerCase()) {
      case 'knowledge sage': return 'from-purple-500 to-purple-700'
      case 'task oracle': return 'from-yellow-500 to-yellow-700'
      case 'crisis sage': return 'from-red-500 to-red-700'
      case 'search mystic': return 'from-green-500 to-green-700'
      default: return 'from-gray-500 to-gray-700'
    }
  }

  const getStatusColor = (status: SageStatus['status']) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800'
      case 'busy': return 'bg-yellow-100 text-yellow-800'
      case 'idle': return 'bg-gray-100 text-gray-800'
    }
  }

  const getPriorityColor = (priority: CouncilDecision['priority']) => {
    switch (priority) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-300'
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-300'
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      case 'low': return 'bg-blue-100 text-blue-800 border-blue-300'
    }
  }

  const getDecisionStatusColor = (status: CouncilDecision['status']) => {
    switch (status) {
      case 'proposed': return 'bg-gray-100 text-gray-800'
      case 'discussing': return 'bg-blue-100 text-blue-800'
      case 'voting': return 'bg-purple-100 text-purple-800'
      case 'decided': return 'bg-green-100 text-green-800'
      case 'implemented': return 'bg-emerald-100 text-emerald-800'
    }
  }

  const calculateCouncilConsensus = (decision: CouncilDecision) => {
    const totalVotes = decision.votes.length
    if (totalVotes === 0) return 0
    
    const approveVotes = decision.votes.filter(v => v.vote === 'approve').length
    return (approveVotes / totalVotes) * 100
  }

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-r from-purple-900 via-blue-900 to-indigo-900 rounded-xl p-6 text-white"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-16 h-16 bg-gradient-to-r from-yellow-400 to-yellow-600 rounded-full flex items-center justify-center">
              <Crown className="w-8 h-8 text-yellow-900" />
            </div>
            <div>
              <h1 className="text-2xl font-bold">エルダー評議会</h1>
              <p className="text-purple-200">4賢者統合指揮所 - 総合知能システム</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="text-right">
              <div className="text-sm opacity-80">システム統合度</div>
              <div className="text-2xl font-bold">{systemMetrics.coveragePercentage}%</div>
            </div>
            <div className="text-right">
              <div className="text-sm opacity-80">協調指数</div>
              <div className="text-2xl font-bold">{systemMetrics.collaborationIndex}/10</div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Navigation */}
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg w-fit">
        {[
          { id: 'overview', label: '概要', icon: Crown },
          { id: 'decisions', label: '評議会決定', icon: Users },
          { id: 'performance', label: '賢者パフォーマンス', icon: TrendingUp },
          { id: 'insights', label: '統合インサイト', icon: Brain }
        ].map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setCouncilMode(id as any)}
            className={cn(
              'px-4 py-2 rounded-md flex items-center space-x-2 transition-all duration-200',
              councilMode === id
                ? 'bg-white text-purple-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            )}
          >
            <Icon className="w-4 h-4" />
            <span className="text-sm font-medium">{label}</span>
          </button>
        ))}
      </div>

      {/* Content */}
      <AnimatePresence mode="wait">
        {councilMode === 'overview' && (
          <motion.div
            key="overview"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Sage Status Grid */}
              <div className="lg:col-span-2">
                <Card className="p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">賢者ステータス概要</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {sages.map((sage, index) => (
                      <motion.div
                        key={sage.id}
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: index * 0.1 }}
                        className="relative"
                      >
                        <div className={cn(
                          'p-4 rounded-lg bg-gradient-to-r text-white relative overflow-hidden',
                          getSageTheme(sage.name)
                        )}>
                          <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center space-x-3">
                              <span className="text-2xl">{getSageIcon(sage.name)}</span>
                              <div>
                                <h4 className="font-semibold">{sage.name}</h4>
                                <p className="text-xs opacity-80">{sage.title}</p>
                              </div>
                            </div>
                            <Badge className={getStatusColor(sage.status)}>
                              {sage.status === 'active' ? '活動中' :
                               sage.status === 'busy' ? '処理中' : '待機中'}
                            </Badge>
                          </div>
                          
                          <p className="text-sm mb-3 opacity-90">{sage.activity}</p>
                          
                          <div className="space-y-2">
                            <div className="flex justify-between text-xs">
                              <span>効率性</span>
                              <span>{sage.performance.efficiency}%</span>
                            </div>
                            <Progress value={sage.performance.efficiency} className="h-1 bg-white bg-opacity-20" />
                          </div>
                          
                          {/* Load indicator */}
                          <div className="absolute top-2 right-2">
                            <div className={cn(
                              'w-3 h-3 rounded-full',
                              sage.currentLoad > 80 ? 'bg-red-400' :
                              sage.currentLoad > 60 ? 'bg-yellow-400' : 'bg-green-400'
                            )} />
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </Card>
              </div>

              {/* System Health */}
              <div className="space-y-6">
                <Card className="p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">システム健全性</h3>
                  
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span>総合健全性</span>
                        <span className="font-medium">{systemMetrics.overallHealth}%</span>
                      </div>
                      <Progress value={systemMetrics.overallHealth} className="h-2" />
                    </div>
                    
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span>知識カバレッジ</span>
                        <span className="font-medium">{systemMetrics.coveragePercentage}%</span>
                      </div>
                      <Progress value={systemMetrics.coveragePercentage} className="h-2" />
                    </div>
                    
                    <div className="pt-4 border-t">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-gray-700">新興課題</span>
                        <Badge variant="secondary" className="bg-orange-100 text-orange-800">
                          {systemMetrics.emergingIssues}件
                        </Badge>
                      </div>
                      
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-600">要対応</span>
                          <AlertTriangle className="w-4 h-4 text-orange-500" />
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-600">監視中</span>
                          <Activity className="w-4 h-4 text-blue-500" />
                        </div>
                      </div>
                    </div>
                  </div>
                </Card>
                
                <Card className="p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">アクティブ評議会決定</h3>
                  
                  <div className="space-y-3">
                    {currentDecisions.slice(0, 3).map((decision) => (
                      <div
                        key={decision.id}
                        className="p-3 border border-gray-200 rounded-lg cursor-pointer hover:border-purple-300 transition-colors"
                        onClick={() => setSelectedDecision(decision)}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <h4 className="text-sm font-medium text-gray-900">{decision.topic}</h4>
                          <Badge className={cn('text-xs', getPriorityColor(decision.priority))}>
                            {decision.priority}
                          </Badge>
                        </div>
                        <p className="text-xs text-gray-600 line-clamp-2">{decision.description}</p>
                        <div className="flex items-center justify-between mt-2">
                          <Badge className={cn('text-xs', getDecisionStatusColor(decision.status))}>
                            {decision.status}
                          </Badge>
                          <span className="text-xs text-gray-500">
                            {calculateCouncilConsensus(decision).toFixed(0)}% 合意
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              </div>
            </div>
          </motion.div>
        )}

        {councilMode === 'decisions' && (
          <motion.div
            key="decisions"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-4">
                {currentDecisions.map((decision) => (
                  <Card
                    key={decision.id}
                    className={cn(
                      'p-6 cursor-pointer transition-all duration-200',
                      selectedDecision?.id === decision.id && 'ring-2 ring-purple-500'
                    )}
                    onClick={() => setSelectedDecision(decision)}
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h3 className="font-semibold text-gray-900 text-lg">{decision.topic}</h3>
                        <p className="text-gray-600 mt-1">{decision.description}</p>
                      </div>
                      <div className="flex flex-col items-end space-y-1">
                        <Badge className={cn('text-xs', getPriorityColor(decision.priority))}>
                          {decision.priority}
                        </Badge>
                        <Badge className={cn('text-xs', getDecisionStatusColor(decision.status))}>
                          {decision.status}
                        </Badge>
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Users className="w-4 h-4 text-gray-400" />
                        <span className="text-sm text-gray-600">
                          {decision.participants.length} 参加者
                        </span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Target className="w-4 h-4 text-gray-400" />
                        <span className="text-sm text-gray-600">
                          合意度: {calculateCouncilConsensus(decision).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>

              <div>
                {selectedDecision && (
                  <Card className="p-6 sticky top-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">決定詳細</h3>
                    
                    <div className="space-y-4">
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-2">提案概要</h4>
                        <p className="text-sm text-gray-600">{selectedDecision.proposal.summary}</p>
                      </div>
                      
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-2">必要なアクション</h4>
                        <ul className="text-sm text-gray-600 space-y-1">
                          {selectedDecision.proposal.requiredActions.map((action, index) => (
                            <li key={index} className="flex items-start space-x-2">
                              <span className="text-purple-500">•</span>
                              <span>{action}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                      
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-2">投票状況</h4>
                        <div className="space-y-2">
                          {selectedDecision.votes.map((vote) => {
                            const sage = sages.find(s => s.id === vote.sageId)
                            return (
                              <div key={vote.sageId} className="flex items-center justify-between">
                                <div className="flex items-center space-x-2">
                                  <span className="text-lg">{getSageIcon(sage?.name || '')}</span>
                                  <span className="text-sm font-medium">{sage?.name}</span>
                                </div>
                                <Badge
                                  className={cn(
                                    'text-xs',
                                    vote.vote === 'approve' ? 'bg-green-100 text-green-800' :
                                    vote.vote === 'reject' ? 'bg-red-100 text-red-800' :
                                    'bg-gray-100 text-gray-800'
                                  )}
                                >
                                  {vote.vote === 'approve' ? '賛成' :
                                   vote.vote === 'reject' ? '反対' : '棄権'}
                                </Badge>
                              </div>
                            )
                          })}
                        </div>
                      </div>
                      
                      <div className="pt-4">
                        <Button
                          className="w-full bg-purple-600 hover:bg-purple-700"
                          onClick={() => onCouncilAction?.('view_decision', selectedDecision)}
                        >
                          詳細ビューで開く
                        </Button>
                      </div>
                    </div>
                  </Card>
                )}
              </div>
            </div>
          </motion.div>
        )}

        {/* Other view modes would be implemented similarly */}
      </AnimatePresence>
    </div>
  )
}