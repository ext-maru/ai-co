'use client'

import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { AlertTriangle, Bell, BellOff, CheckCircle, Clock, User, Filter, Search, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Avatar } from '@/components/ui/Avatar'

interface Alert {
  id: string
  title: string
  description: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  category: 'system' | 'security' | 'performance' | 'availability'
  status: 'new' | 'acknowledged' | 'investigating' | 'resolved'
  createdAt: string
  acknowledgedAt?: string
  resolvedAt?: string
  assignee?: {
    id: string
    name: string
    avatar: string
  }
  source: string
  affectedServices: string[]
  metrics?: {
    current: number
    threshold: number
    unit: string
  }
  actions: {
    id: string
    label: string
    type: 'primary' | 'secondary' | 'danger'
  }[]
}

interface AlertManagerProps {
  alerts: Alert[]
  onAlertUpdate?: (alert: Alert) => void
  onAlertAction?: (alertId: string, actionId: string) => void
  className?: string
}

export function AlertManager({ alerts, onAlertUpdate, onAlertAction, className }: AlertManagerProps) {
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null)
  const [filterSeverity, setFilterSeverity] = useState<Alert['severity'] | 'all'>('all')
  const [filterStatus, setFilterStatus] = useState<Alert['status'] | 'all'>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [mutedAlerts, setMutedAlerts] = useState<Set<string>>(new Set())

  const getSeverityColor = (severity: Alert['severity']) => {
    switch (severity) {
      case 'low': return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-200'
      case 'critical': return 'bg-red-100 text-red-800 border-red-200'
    }
  }

  const getSeverityIcon = (severity: Alert['severity']) => {
    switch (severity) {
      case 'low': return 'ℹ️'
      case 'medium': return '⚠️'
      case 'high': return '🔶'
      case 'critical': return '🚨'
    }
  }

  const getStatusColor = (status: Alert['status']) => {
    switch (status) {
      case 'new': return 'bg-red-500 text-white'
      case 'acknowledged': return 'bg-yellow-500 text-white'
      case 'investigating': return 'bg-blue-500 text-white'
      case 'resolved': return 'bg-green-500 text-white'
    }
  }

  const getCategoryIcon = (category: Alert['category']) => {
    switch (category) {
      case 'system': return '🖥️'
      case 'security': return '🔒'
      case 'performance': return '⚡'
      case 'availability': return '🌐'
    }
  }

  const filteredAlerts = alerts.filter(alert => {
    const matchesSeverity = filterSeverity === 'all' || alert.severity === filterSeverity
    const matchesStatus = filterStatus === 'all' || alert.status === filterStatus
    const matchesSearch = searchQuery === '' || 
      alert.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      alert.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      alert.source.toLowerCase().includes(searchQuery.toLowerCase())
    
    return matchesSeverity && matchesStatus && matchesSearch
  })

  const toggleMute = (alertId: string) => {
    setMutedAlerts(prev => {
      const next = new Set(prev)
      if (next.has(alertId)) {
        next.delete(alertId)
      } else {
        next.add(alertId)
      }
      return next
    })
  }

  const getTimeAgo = (timestamp: string) => {
    const now = new Date()
    const then = new Date(timestamp)
    const diffMs = now.getTime() - then.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    
    if (diffMins < 1) return '今'
    if (diffMins < 60) return `${diffMins}分前`
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}時間前`
    return `${Math.floor(diffMins / 1440)}日前`
  }

  const handleAlertAction = (alert: Alert, actionId: string) => {
    onAlertAction?.(alert.id, actionId)
    
    // Auto-update status based on action
    if (actionId === 'acknowledge' && alert.status === 'new') {
      onAlertUpdate?.({
        ...alert,
        status: 'acknowledged',
        acknowledgedAt: new Date().toISOString()
      })
    } else if (actionId === 'resolve') {
      onAlertUpdate?.({
        ...alert,
        status: 'resolved',
        resolvedAt: new Date().toISOString()
      })
    }
  }

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header Controls */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="アラートを検索..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-crimson-500 focus:border-transparent"
          />
        </div>
        
        <div className="flex gap-2">
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
          
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value as any)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-crimson-500"
          >
            <option value="all">すべてのステータス</option>
            <option value="new">新規</option>
            <option value="acknowledged">確認済み</option>
            <option value="investigating">調査中</option>
            <option value="resolved">解決済み</option>
          </select>
        </div>
      </div>

      {/* Alert Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        {[
          { label: '新規', count: alerts.filter(a => a.status === 'new').length, color: 'bg-red-100 text-red-800' },
          { label: '確認済み', count: alerts.filter(a => a.status === 'acknowledged').length, color: 'bg-yellow-100 text-yellow-800' },
          { label: '調査中', count: alerts.filter(a => a.status === 'investigating').length, color: 'bg-blue-100 text-blue-800' },
          { label: '解決済み', count: alerts.filter(a => a.status === 'resolved').length, color: 'bg-green-100 text-green-800' }
        ].map((stat) => (
          <Card key={stat.label} className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">{stat.label}</span>
              <Badge className={stat.color}>{stat.count}</Badge>
            </div>
          </Card>
        ))}
      </div>

      {/* Alerts List */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <AnimatePresence mode="popLayout">
            {filteredAlerts.map((alert, index) => (
              <motion.div
                key={alert.id}
                layout
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ delay: index * 0.05 }}
              >
                <Card
                  className={cn(
                    'p-4 cursor-pointer transition-all duration-200',
                    'hover:shadow-lg',
                    alert.severity === 'critical' && alert.status !== 'resolved' && 'border-red-500',
                    selectedAlert?.id === alert.id && 'ring-2 ring-crimson-500',
                    mutedAlerts.has(alert.id) && 'opacity-50'
                  )}
                  onClick={() => setSelectedAlert(alert)}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      <span className="text-2xl">{getSeverityIcon(alert.severity)}</span>
                      <div>
                        <div className="flex items-center space-x-2">
                          <h3 className="font-semibold text-gray-900">{alert.title}</h3>
                          <Badge className={cn('text-xs', getSeverityColor(alert.severity))}>
                            {alert.severity}
                          </Badge>
                        </div>
                        <div className="flex items-center space-x-3 mt-1 text-sm text-gray-500">
                          <span className="flex items-center">
                            {getCategoryIcon(alert.category)}
                            <span className="ml-1">{alert.category}</span>
                          </span>
                          <span>•</span>
                          <span>{alert.source}</span>
                          <span>•</span>
                          <span>{getTimeAgo(alert.createdAt)}</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <Badge className={cn('text-xs', getStatusColor(alert.status))}>
                        {alert.status === 'new' ? '新規' :
                         alert.status === 'acknowledged' ? '確認済み' :
                         alert.status === 'investigating' ? '調査中' : '解決済み'}
                      </Badge>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          toggleMute(alert.id)
                        }}
                        className="p-1 hover:bg-gray-100 rounded"
                      >
                        {mutedAlerts.has(alert.id) ? (
                          <BellOff className="w-4 h-4 text-gray-400" />
                        ) : (
                          <Bell className="w-4 h-4 text-gray-600" />
                        )}
                      </button>
                    </div>
                  </div>
                  
                  <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                    {alert.description}
                  </p>
                  
                  {alert.metrics && (
                    <div className="bg-gray-50 rounded p-2 mb-3">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">現在値 / 閾値</span>
                        <span className="font-medium">
                          {alert.metrics.current} / {alert.metrics.threshold} {alert.metrics.unit}
                        </span>
                      </div>
                    </div>
                  )}
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {alert.affectedServices.slice(0, 3).map((service) => (
                        <Badge key={service} variant="outline" className="text-xs">
                          {service}
                        </Badge>
                      ))}
                      {alert.affectedServices.length > 3 && (
                        <span className="text-xs text-gray-500">
                          +{alert.affectedServices.length - 3}
                        </span>
                      )}
                    </div>
                    
                    {alert.assignee && (
                      <Avatar
                        src={alert.assignee.avatar}
                        alt={alert.assignee.name}
                        size="sm"
                        fallback={alert.assignee.name.slice(0, 2)}
                      />
                    )}
                  </div>
                </Card>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {/* Alert Details */}
        <div className="lg:col-span-1">
          <AnimatePresence mode="wait">
            {selectedAlert ? (
              <motion.div
                key={selectedAlert.id}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="sticky top-6"
              >
                <Card className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-semibold text-gray-900">アラート詳細</h2>
                    <button
                      onClick={() => setSelectedAlert(null)}
                      className="p-1 hover:bg-gray-100 rounded"
                    >
                      <X className="w-5 h-5 text-gray-500" />
                    </button>
                  </div>
                  
                  <div className="space-y-4">
                    <div>
                      <h3 className="font-medium text-gray-900 flex items-center space-x-2">
                        <span className="text-xl">{getSeverityIcon(selectedAlert.severity)}</span>
                        <span>{selectedAlert.title}</span>
                      </h3>
                      <p className="text-sm text-gray-600 mt-2">{selectedAlert.description}</p>
                    </div>
                    
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">重要度</span>
                        <Badge className={getSeverityColor(selectedAlert.severity)}>
                          {selectedAlert.severity}
                        </Badge>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">カテゴリ</span>
                        <span className="font-medium">{selectedAlert.category}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">ソース</span>
                        <span className="font-medium">{selectedAlert.source}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">発生時刻</span>
                        <span className="font-medium">
                          {new Date(selectedAlert.createdAt).toLocaleString('ja-JP')}
                        </span>
                      </div>
                    </div>
                    
                    {selectedAlert.metrics && (
                      <div className="bg-gray-50 rounded-lg p-3">
                        <h4 className="text-sm font-medium text-gray-700 mb-2">メトリクス</h4>
                        <div className="space-y-1 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-600">現在値</span>
                            <span className="font-medium text-red-600">
                              {selectedAlert.metrics.current} {selectedAlert.metrics.unit}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">閾値</span>
                            <span className="font-medium">
                              {selectedAlert.metrics.threshold} {selectedAlert.metrics.unit}
                            </span>
                          </div>
                        </div>
                      </div>
                    )}
                    
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-2">影響を受けるサービス</h4>
                      <div className="flex flex-wrap gap-1">
                        {selectedAlert.affectedServices.map((service) => (
                          <Badge key={service} variant="outline" className="text-xs">
                            {service}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    
                    {selectedAlert.assignee && (
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-2">担当者</h4>
                        <div className="flex items-center space-x-3">
                          <Avatar
                            src={selectedAlert.assignee.avatar}
                            alt={selectedAlert.assignee.name}
                            size="sm"
                            fallback={selectedAlert.assignee.name.slice(0, 2)}
                          />
                          <span className="text-sm font-medium">{selectedAlert.assignee.name}</span>
                        </div>
                      </div>
                    )}
                    
                    <div className="pt-4 space-y-2">
                      {selectedAlert.actions.map((action) => (
                        <Button
                          key={action.id}
                          variant={action.type === 'primary' ? 'primary' : action.type === 'danger' ? 'destructive' : 'outline'}
                          size="sm"
                          className="w-full"
                          onClick={() => handleAlertAction(selectedAlert, action.id)}
                        >
                          {action.label}
                        </Button>
                      ))}
                    </div>
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
                  <AlertTriangle className="w-12 h-12 mx-auto mb-2" />
                  <p>アラートを選択してください</p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}