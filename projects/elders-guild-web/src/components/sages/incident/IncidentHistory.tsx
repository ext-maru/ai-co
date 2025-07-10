'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Clock, TrendingUp, TrendingDown, Calendar, FileText, User, AlertTriangle, CheckCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Avatar } from '@/components/ui/Avatar'

interface Incident {
  id: string
  title: string
  description: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  category: 'system' | 'security' | 'performance' | 'availability'
  status: 'resolved' | 'mitigated' | 'ongoing'
  startTime: string
  endTime?: string
  duration?: number // in minutes
  impact: {
    users: number
    services: string[]
    revenue?: number
  }
  rootCause?: string
  resolution?: string
  timeline: {
    id: string
    time: string
    action: string
    actor: string
    type: 'detection' | 'escalation' | 'mitigation' | 'resolution'
  }[]
  metrics: {
    mttr: number // Mean Time To Recovery
    mtta: number // Mean Time To Acknowledge
    availability: number
  }
  postmortem?: {
    id: string
    url: string
    lessons: string[]
  }
}

interface IncidentHistoryProps {
  incidents: Incident[]
  onIncidentSelect?: (incident: Incident) => void
  className?: string
}

export function IncidentHistory({ incidents, onIncidentSelect, className }: IncidentHistoryProps) {
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null)
  const [timeRange, setTimeRange] = useState<'24h' | '7d' | '30d' | '90d'>('7d')
  const [filterSeverity, setFilterSeverity] = useState<Incident['severity'] | 'all'>('all')

  const getSeverityColor = (severity: Incident['severity']) => {
    switch (severity) {
      case 'low': return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-200'
      case 'critical': return 'bg-red-100 text-red-800 border-red-200'
    }
  }

  const getStatusColor = (status: Incident['status']) => {
    switch (status) {
      case 'resolved': return 'bg-green-100 text-green-800'
      case 'mitigated': return 'bg-yellow-100 text-yellow-800'
      case 'ongoing': return 'bg-red-100 text-red-800'
    }
  }

  const getTimelineIcon = (type: Incident['timeline'][0]['type']) => {
    switch (type) {
      case 'detection': return '🔍'
      case 'escalation': return '📢'
      case 'mitigation': return '🛠️'
      case 'resolution': return '✅'
    }
  }

  const formatDuration = (minutes?: number) => {
    if (!minutes) return 'N/A'
    if (minutes < 60) return `${minutes}分`
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return `${hours}時間${mins > 0 ? ` ${mins}分` : ''}`
  }

  const filteredIncidents = incidents.filter(incident => {
    const matchesSeverity = filterSeverity === 'all' || incident.severity === filterSeverity

    // Filter by time range
    const now = new Date()
    const incidentDate = new Date(incident.startTime)
    const daysDiff = (now.getTime() - incidentDate.getTime()) / (1000 * 60 * 60 * 24)

    let matchesTimeRange = true
    switch (timeRange) {
      case '24h': matchesTimeRange = daysDiff <= 1; break
      case '7d': matchesTimeRange = daysDiff <= 7; break
      case '30d': matchesTimeRange = daysDiff <= 30; break
      case '90d': matchesTimeRange = daysDiff <= 90; break
    }

    return matchesSeverity && matchesTimeRange
  })

  // Calculate statistics
  const stats = {
    total: filteredIncidents.length,
    critical: filteredIncidents.filter(i => i.severity === 'critical').length,
    avgMTTR: filteredIncidents.reduce((acc, i) => acc + i.metrics.mttr, 0) / filteredIncidents.length || 0,
    avgAvailability: filteredIncidents.reduce((acc, i) => acc + i.metrics.availability, 0) / filteredIncidents.length || 0
  }

  const handleIncidentClick = (incident: Incident) => {
    setSelectedIncident(incident)
    onIncidentSelect?.(incident)
  }

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header Controls */}
      <div className="flex flex-col sm:flex-row justify-between gap-4">
        <div className="flex items-center space-x-4">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value as any)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-crimson-500"
          >
            <option value="24h">過去24時間</option>
            <option value="7d">過去7日間</option>
            <option value="30d">過去30日間</option>
            <option value="90d">過去90日間</option>
          </select>

          <select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value as any)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-crimson-500"
          >
            <option value="all">すべての重要度</option>
            <option value="critical">緊急</option>
            <option value="high">高</option>
            <option value="medium">中</option>
            <option value="low">低</option>
          </select>
        </div>

        <Button variant="outline" size="sm">
          <FileText className="w-4 h-4 mr-2" />
          レポートをエクスポート
        </Button>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="p-6 bg-gradient-to-br from-crimson-50 to-white border-crimson-200">
            <div className="flex items-center justify-between mb-2">
              <AlertTriangle className="w-8 h-8 text-crimson-600" />
              <Badge variant="secondary" className="text-xs">
                {timeRange}
              </Badge>
            </div>
            <h3 className="text-2xl font-bold text-gray-900">{stats.total}</h3>
            <p className="text-sm text-gray-600">総インシデント数</p>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="p-6 bg-gradient-to-br from-red-50 to-white border-red-200">
            <div className="flex items-center justify-between mb-2">
              <span className="text-2xl">🚨</span>
              <span className="text-sm font-medium text-red-600">
                {stats.critical > 0 ? `+${stats.critical}` : '0'}
              </span>
            </div>
            <h3 className="text-2xl font-bold text-gray-900">{stats.critical}</h3>
            <p className="text-sm text-gray-600">緊急インシデント</p>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card className="p-6 bg-gradient-to-br from-blue-50 to-white border-blue-200">
            <div className="flex items-center justify-between mb-2">
              <Clock className="w-8 h-8 text-blue-600" />
              {stats.avgMTTR <= 30 ? (
                <TrendingDown className="w-5 h-5 text-green-500" />
              ) : (
                <TrendingUp className="w-5 h-5 text-red-500" />
              )}
            </div>
            <h3 className="text-2xl font-bold text-gray-900">
              {Math.round(stats.avgMTTR)}分
            </h3>
            <p className="text-sm text-gray-600">平均復旧時間</p>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <Card className="p-6 bg-gradient-to-br from-green-50 to-white border-green-200">
            <div className="flex items-center justify-between mb-2">
              <CheckCircle className="w-8 h-8 text-green-600" />
              <span className="text-sm font-medium text-green-600">
                {stats.avgAvailability.toFixed(2)}%
              </span>
            </div>
            <h3 className="text-2xl font-bold text-gray-900">
              {stats.avgAvailability.toFixed(1)}%
            </h3>
            <p className="text-sm text-gray-600">平均可用性</p>
          </Card>
        </motion.div>
      </div>

      {/* Incidents Timeline */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">インシデントタイムライン</h3>

            <div className="relative">
              {/* Timeline line */}
              <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-200" />

              <div className="space-y-6">
                {filteredIncidents.map((incident, index) => (
                  <motion.div
                    key={incident.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className="relative"
                  >
                    {/* Timeline node */}
                    <div className={cn(
                      'absolute left-6 w-4 h-4 rounded-full border-4 border-white transform -translate-x-1/2',
                      incident.severity === 'critical' ? 'bg-red-500' :
                      incident.severity === 'high' ? 'bg-orange-500' :
                      incident.severity === 'medium' ? 'bg-yellow-500' : 'bg-blue-500'
                    )} />

                    {/* Incident card */}
                    <div
                      className={cn(
                        'ml-12 p-4 bg-white border rounded-lg cursor-pointer transition-all duration-200',
                        'hover:shadow-md hover:border-crimson-300',
                        selectedIncident?.id === incident.id && 'ring-2 ring-crimson-500 border-crimson-500'
                      )}
                      onClick={() => handleIncidentClick(incident)}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <h4 className="font-semibold text-gray-900">{incident.title}</h4>
                          <p className="text-sm text-gray-600 mt-1">{incident.description}</p>
                        </div>
                        <Badge className={cn('text-xs', getSeverityColor(incident.severity))}>
                          {incident.severity}
                        </Badge>
                      </div>

                      <div className="flex items-center space-x-4 text-sm text-gray-500">
                        <span className="flex items-center">
                          <Calendar className="w-4 h-4 mr-1" />
                          {new Date(incident.startTime).toLocaleDateString('ja-JP')}
                        </span>
                        <span className="flex items-center">
                          <Clock className="w-4 h-4 mr-1" />
                          {formatDuration(incident.duration)}
                        </span>
                        <Badge className={cn('text-xs', getStatusColor(incident.status))}>
                          {incident.status === 'resolved' ? '解決済み' :
                           incident.status === 'mitigated' ? '緩和済み' : '継続中'}
                        </Badge>
                      </div>

                      {incident.impact && (
                        <div className="mt-3 flex items-center space-x-4 text-xs text-gray-600">
                          <span>影響: {incident.impact.users.toLocaleString()}ユーザー</span>
                          <span>•</span>
                          <span>{incident.impact.services.length}サービス</span>
                          {incident.impact.revenue && (
                            <>
                              <span>•</span>
                              <span className="text-red-600 font-medium">
                                ¥{incident.impact.revenue.toLocaleString()}
                              </span>
                            </>
                          )}
                        </div>
                      )}
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </Card>
        </div>

        {/* Incident Details */}
        <div className="lg:col-span-1">
          {selectedIncident ? (
            <motion.div
              key={selectedIncident.id}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="sticky top-6"
            >
              <Card className="p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">インシデント詳細</h2>

                <div className="space-y-4">
                  <div>
                    <h3 className="font-medium text-gray-900">{selectedIncident.title}</h3>
                    <p className="text-sm text-gray-600 mt-1">{selectedIncident.description}</p>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <span className="text-gray-600">重要度</span>
                      <Badge className={cn('mt-1', getSeverityColor(selectedIncident.severity))}>
                        {selectedIncident.severity}
                      </Badge>
                    </div>
                    <div>
                      <span className="text-gray-600">ステータス</span>
                      <Badge className={cn('mt-1', getStatusColor(selectedIncident.status))}>
                        {selectedIncident.status === 'resolved' ? '解決済み' :
                         selectedIncident.status === 'mitigated' ? '緩和済み' : '継続中'}
                      </Badge>
                    </div>
                    <div>
                      <span className="text-gray-600">MTTR</span>
                      <p className="font-medium">{selectedIncident.metrics.mttr}分</p>
                    </div>
                    <div>
                      <span className="text-gray-600">MTTA</span>
                      <p className="font-medium">{selectedIncident.metrics.mtta}分</p>
                    </div>
                  </div>

                  {selectedIncident.rootCause && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-1">根本原因</h4>
                      <p className="text-sm text-gray-600">{selectedIncident.rootCause}</p>
                    </div>
                  )}

                  {selectedIncident.resolution && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-1">解決方法</h4>
                      <p className="text-sm text-gray-600">{selectedIncident.resolution}</p>
                    </div>
                  )}

                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">アクションタイムライン</h4>
                    <div className="space-y-2">
                      {selectedIncident.timeline.slice(0, 4).map((event) => (
                        <div key={event.id} className="flex items-start space-x-2 text-xs">
                          <span className="text-lg">{getTimelineIcon(event.type)}</span>
                          <div className="flex-1">
                            <p className="font-medium text-gray-900">{event.action}</p>
                            <p className="text-gray-500">
                              {event.actor} • {new Date(event.time).toLocaleTimeString('ja-JP')}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {selectedIncident.postmortem && (
                    <div className="pt-4 border-t">
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full"
                        onClick={() => window.open(selectedIncident.postmortem!.url, '_blank')}
                      >
                        <FileText className="w-4 h-4 mr-2" />
                        ポストモーテムを見る
                      </Button>
                    </div>
                  )}
                </div>
              </Card>
            </motion.div>
          ) : (
            <div className="h-full flex items-center justify-center text-gray-400">
              <div className="text-center">
                <AlertTriangle className="w-12 h-12 mx-auto mb-2" />
                <p>インシデントを選択してください</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
