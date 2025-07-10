'use client'

import React, { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { AlertTriangle, Activity, Server, Database, Wifi, Shield, TrendingUp, TrendingDown } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Progress } from '@/components/ui/Progress'

interface SystemMetric {
  id: string
  name: string
  value: number
  unit: string
  status: 'normal' | 'warning' | 'critical'
  trend: 'up' | 'down' | 'stable'
  threshold: {
    warning: number
    critical: number
  }
  history: { time: string; value: number }[]
}

interface ServiceHealth {
  id: string
  name: string
  status: 'operational' | 'degraded' | 'down'
  uptime: number
  responseTime: number
  errorRate: number
  lastChecked: string
}

interface MonitoringDashboardProps {
  metrics: SystemMetric[]
  services: ServiceHealth[]
  onMetricClick?: (metric: SystemMetric) => void
  onServiceClick?: (service: ServiceHealth) => void
  className?: string
}

export function MonitoringDashboard({
  metrics,
  services,
  onMetricClick,
  onServiceClick,
  className
}: MonitoringDashboardProps) {
  const [currentTime, setCurrentTime] = useState(new Date())
  const [selectedMetric, setSelectedMetric] = useState<SystemMetric | null>(null)

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date())
    }, 1000)
    return () => clearInterval(timer)
  }, [])

  const getStatusColor = (status: SystemMetric['status'] | ServiceHealth['status']) => {
    switch (status) {
      case 'normal':
      case 'operational':
        return 'text-green-600 bg-green-100 border-green-200'
      case 'warning':
      case 'degraded':
        return 'text-yellow-600 bg-yellow-100 border-yellow-200'
      case 'critical':
      case 'down':
        return 'text-red-600 bg-red-100 border-red-200'
    }
  }

  const getStatusIcon = (status: ServiceHealth['status']) => {
    switch (status) {
      case 'operational': return '✅'
      case 'degraded': return '⚠️'
      case 'down': return '🔴'
    }
  }

  const getTrendIcon = (trend: SystemMetric['trend']) => {
    switch (trend) {
      case 'up': return <TrendingUp className="w-4 h-4 text-green-500" />
      case 'down': return <TrendingDown className="w-4 h-4 text-red-500" />
      case 'stable': return <Activity className="w-4 h-4 text-gray-500" />
    }
  }

  const getMetricIcon = (metricName: string) => {
    if (metricName.includes('CPU')) return <Server className="w-5 h-5" />
    if (metricName.includes('メモリ')) return <Database className="w-5 h-5" />
    if (metricName.includes('ネットワーク')) return <Wifi className="w-5 h-5" />
    if (metricName.includes('セキュリティ')) return <Shield className="w-5 h-5" />
    return <Activity className="w-5 h-5" />
  }

  const calculateOverallHealth = () => {
    const criticalCount = metrics.filter(m => m.status === 'critical').length
    const warningCount = metrics.filter(m => m.status === 'warning').length
    const downServices = services.filter(s => s.status === 'down').length
    const degradedServices = services.filter(s => s.status === 'degraded').length

    if (criticalCount > 0 || downServices > 0) return 'critical'
    if (warningCount > 0 || degradedServices > 0) return 'warning'
    return 'normal'
  }

  const overallHealth = calculateOverallHealth()

  // Simulate real-time sparkline
  const generateSparkline = (history: SystemMetric['history']) => {
    const values = history.map(h => h.value)
    const max = Math.max(...values)
    const min = Math.min(...values)
    const range = max - min || 1

    const points = values.map((value, index) => {
      const x = (index / (values.length - 1)) * 100
      const y = 100 - ((value - min) / range) * 100
      return `${x},${y}`
    }).join(' ')

    return `M ${points}`
  }

  return (
    <div className={cn('space-y-6', className)}>
      {/* Overall System Health */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <Card className={cn(
          'p-6 border-2 transition-all duration-300',
          overallHealth === 'critical' && 'border-red-500 bg-red-50',
          overallHealth === 'warning' && 'border-yellow-500 bg-yellow-50',
          overallHealth === 'normal' && 'border-green-500 bg-green-50'
        )}>
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">システム全体の状態</h2>
              <p className="text-sm text-gray-600 mt-1">
                最終更新: {currentTime.toLocaleTimeString('ja-JP')}
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <Badge className={cn('text-lg px-4 py-2', getStatusColor(overallHealth))}>
                {overallHealth === 'critical' ? '危険' :
                 overallHealth === 'warning' ? '警告' : '正常'}
              </Badge>
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
                className={cn(
                  'w-4 h-4 rounded-full',
                  overallHealth === 'critical' && 'bg-red-500',
                  overallHealth === 'warning' && 'bg-yellow-500',
                  overallHealth === 'normal' && 'bg-green-500'
                )}
              />
            </div>
          </div>
        </Card>
      </motion.div>

      {/* System Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((metric, index) => (
          <motion.div
            key={metric.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            whileHover={{ scale: 1.02 }}
          >
            <Card
              className={cn(
                'p-4 cursor-pointer transition-all duration-200',
                'hover:shadow-lg',
                metric.status === 'critical' && 'border-red-300',
                metric.status === 'warning' && 'border-yellow-300',
                selectedMetric?.id === metric.id && 'ring-2 ring-crimson-500'
              )}
              onClick={() => {
                setSelectedMetric(metric)
                onMetricClick?.(metric)
              }}
            >
              <div className="flex items-start justify-between mb-3">
                <div className={cn(
                  'p-2 rounded-lg',
                  metric.status === 'critical' && 'bg-red-100 text-red-600',
                  metric.status === 'warning' && 'bg-yellow-100 text-yellow-600',
                  metric.status === 'normal' && 'bg-gray-100 text-gray-600'
                )}>
                  {getMetricIcon(metric.name)}
                </div>
                {getTrendIcon(metric.trend)}
              </div>

              <h3 className="font-medium text-gray-900 text-sm mb-1">{metric.name}</h3>

              <div className="flex items-baseline space-x-1 mb-3">
                <span className="text-2xl font-bold text-gray-900">{metric.value}</span>
                <span className="text-sm text-gray-500">{metric.unit}</span>
              </div>

              {/* Mini sparkline */}
              <div className="h-8 relative">
                <svg className="w-full h-full">
                  <path
                    d={generateSparkline(metric.history.slice(-10))}
                    fill="none"
                    stroke={
                      metric.status === 'critical' ? '#dc2626' :
                      metric.status === 'warning' ? '#f59e0b' : '#10b981'
                    }
                    strokeWidth="2"
                  />
                </svg>
              </div>

              <div className="mt-2">
                <div className="flex justify-between text-xs text-gray-500 mb-1">
                  <span>閾値</span>
                  <span>{metric.threshold.warning} / {metric.threshold.critical}</span>
                </div>
                <Progress
                  value={(metric.value / metric.threshold.critical) * 100}
                  className="h-1.5"
                >
                  <div
                    className={cn(
                      'h-full rounded-full transition-all duration-300',
                      metric.status === 'critical' && 'bg-red-500',
                      metric.status === 'warning' && 'bg-yellow-500',
                      metric.status === 'normal' && 'bg-green-500'
                    )}
                  />
                </Progress>
              </div>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Service Health Status */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Activity className="w-5 h-5 mr-2 text-crimson-600" />
          サービスヘルスステータス
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {services.map((service) => (
            <motion.div
              key={service.id}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <div
                className={cn(
                  'p-4 border rounded-lg cursor-pointer transition-all duration-200',
                  'hover:shadow-md',
                  service.status === 'down' && 'border-red-300 bg-red-50',
                  service.status === 'degraded' && 'border-yellow-300 bg-yellow-50',
                  service.status === 'operational' && 'border-green-300 bg-green-50'
                )}
                onClick={() => onServiceClick?.(service)}
              >
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium text-gray-900">{service.name}</h4>
                  <span className="text-2xl">{getStatusIcon(service.status)}</span>
                </div>

                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">稼働率</span>
                    <span className={cn(
                      'font-medium',
                      service.uptime >= 99.9 ? 'text-green-600' :
                      service.uptime >= 99 ? 'text-yellow-600' : 'text-red-600'
                    )}>
                      {service.uptime}%
                    </span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-gray-600">応答時間</span>
                    <span className={cn(
                      'font-medium',
                      service.responseTime <= 100 ? 'text-green-600' :
                      service.responseTime <= 500 ? 'text-yellow-600' : 'text-red-600'
                    )}>
                      {service.responseTime}ms
                    </span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-gray-600">エラー率</span>
                    <span className={cn(
                      'font-medium',
                      service.errorRate <= 0.1 ? 'text-green-600' :
                      service.errorRate <= 1 ? 'text-yellow-600' : 'text-red-600'
                    )}>
                      {service.errorRate}%
                    </span>
                  </div>
                </div>

                <div className="mt-3 pt-3 border-t border-gray-200">
                  <p className="text-xs text-gray-500">
                    最終チェック: {new Date(service.lastChecked).toLocaleTimeString('ja-JP')}
                  </p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </Card>

      {/* Real-time Alerts */}
      <AnimatePresence>
        {(overallHealth === 'critical' || overallHealth === 'warning') && (
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className={cn(
              'fixed bottom-4 right-4 max-w-sm p-4 rounded-lg shadow-lg',
              overallHealth === 'critical' ? 'bg-red-600' : 'bg-yellow-600'
            )}
          >
            <div className="flex items-start space-x-3 text-white">
              <AlertTriangle className="w-6 h-6 flex-shrink-0" />
              <div>
                <h4 className="font-semibold">
                  {overallHealth === 'critical' ? '緊急アラート' : '警告'}
                </h4>
                <p className="text-sm mt-1 opacity-90">
                  システムに{overallHealth === 'critical' ? '重大な' : ''}問題が検出されました。
                  確認してください。
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
