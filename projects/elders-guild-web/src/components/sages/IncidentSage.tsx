'use client'

import React from 'react'
import { motion } from 'framer-motion'
import { Shield, AlertCircle, CheckCircle2, Activity } from 'lucide-react'
import { IncidentSage as IncidentSageType } from '@/types/sages'
import { cn, getSageThemeClasses, formatJapaneseDateTime } from '@/lib/utils'

interface IncidentSageProps {
  sage: IncidentSageType
  isSelected?: boolean
  onSelect?: () => void
  className?: string
}

export function IncidentSage({ sage, isSelected = false, onSelect, className }: IncidentSageProps) {
  const theme = getSageThemeClasses('incident')

  const resolutionRate = sage.resolvedIncidents / (sage.activeIncidents + sage.resolvedIncidents) * 100

  const getAlertLevelColor = (level: string) => {
    switch (level) {
      case 'critical': return 'bg-red-500 text-white'
      case 'high': return 'bg-red-400 text-white'
      case 'medium': return 'bg-yellow-400 text-white'
      case 'low': return 'bg-green-400 text-white'
      default: return 'bg-gray-400 text-white'
    }
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical': return '🔴'
      case 'high': return '🟠'
      case 'medium': return '🟡'
      case 'low': return '🟢'
      default: return '⚪'
    }
  }

  return (
    <motion.div
      className={cn(
        'relative bg-white border rounded-lg p-6 cursor-pointer transition-all duration-300',
        theme.shadow,
        isSelected ? `ring-2 ${theme.ring} ${theme.border}` : 'border-gray-200 hover:border-incident-300',
        'hover:shadow-lg transform hover:-translate-y-1',
        sage.alertLevel === 'high' || sage.alertLevel === 'critical' ? 'ring-2 ring-red-500 animate-pulse' : '',
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
            🚨
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
          {sage.status === 'active' ? '監視中' :
           sage.status === 'busy' ? '対応中' : '休息中'}
        </div>
      </div>

      {/* Alert Level Banner */}
      <div className={cn(
        'mb-4 p-3 rounded-lg text-center font-bold',
        getAlertLevelColor(sage.alertLevel)
      )}>
        <div className="flex items-center justify-center space-x-2">
          <Shield className="w-5 h-5" />
          <span>
            警戒レベル: {
              sage.alertLevel === 'critical' ? '最高' :
              sage.alertLevel === 'high' ? '高' :
              sage.alertLevel === 'medium' ? '中' : '低'
            }
          </span>
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
            <Shield className="w-4 h-4" />
            <span className="text-sm font-medium">{sage.metrics.primary.label}</span>
          </div>
          <p className="text-xl font-bold">{sage.metrics.primary.value}</p>
        </div>
        <div className={cn('p-3 rounded-lg', theme.secondary)}>
          <div className="flex items-center space-x-2 mb-1">
            <CheckCircle2 className="w-4 h-4" />
            <span className="text-sm font-medium">{sage.metrics.secondary.label}</span>
          </div>
          <p className="text-xl font-bold">{sage.metrics.secondary.value}</p>
        </div>
      </div>

      {/* Incident Statistics */}
      <div className="mb-4">
        <div className="flex items-center space-x-2 mb-2">
          <Activity className="w-4 h-4 text-incident-600" />
          <span className="text-sm font-medium text-gray-700">危機対応統計</span>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center p-2 bg-red-50 rounded">
            <p className="text-2xl font-bold text-red-600">{sage.activeIncidents}</p>
            <p className="text-xs text-red-600">対応中</p>
          </div>
          <div className="text-center p-2 bg-green-50 rounded">
            <p className="text-2xl font-bold text-green-600">{sage.resolvedIncidents}</p>
            <p className="text-xs text-green-600">解決済み</p>
          </div>
        </div>
      </div>

      {/* Resolution Rate */}
      <div className="mb-4">
        <div className="flex justify-between items-center mb-1">
          <span className="text-sm font-medium text-gray-700">解決率</span>
          <span className="text-sm font-bold text-incident-600">
            {isNaN(resolutionRate) ? '100' : resolutionRate.toFixed(1)}%
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={cn('h-2 rounded-full', theme.primary)}
            style={{ width: `${isNaN(resolutionRate) ? 100 : resolutionRate}%` }}
          />
        </div>
      </div>

      {/* Recent Incidents */}
      <div className="mb-4">
        <div className="flex items-center space-x-2 mb-2">
          <AlertCircle className="w-4 h-4 text-incident-600" />
          <span className="text-sm font-medium text-gray-700">最近の事案</span>
        </div>
        <div className="space-y-2">
          {sage.recentIncidents.slice(0, 3).map((incident) => (
            <div key={incident.id} className="p-2 bg-gray-50 rounded text-xs">
              <div className="flex justify-between items-start mb-1">
                <div className="flex items-center space-x-2 flex-1">
                  <span className="text-base">{getSeverityIcon(incident.severity)}</span>
                  <p className="font-medium text-gray-900 line-clamp-1">{incident.title}</p>
                </div>
                <span className={cn(
                  'px-2 py-1 rounded text-xs font-medium ml-2 flex-shrink-0',
                  incident.status === 'resolved' ? 'bg-green-100 text-green-800' :
                  incident.status === 'investigating' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-red-100 text-red-800'
                )}>
                  {incident.status === 'resolved' ? '解決' :
                   incident.status === 'investigating' ? '調査中' : '発生'}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-500">
                  重要度: {
                    incident.severity === 'critical' ? '緊急' :
                    incident.severity === 'high' ? '高' :
                    incident.severity === 'medium' ? '中' : '低'
                  }
                </span>
                <span className="text-gray-500">
                  {formatJapaneseDateTime(incident.timestamp)}
                </span>
              </div>
            </div>
          ))}
          {sage.recentIncidents.length === 0 && (
            <div className="text-center p-4 text-gray-500">
              <Shield className="w-8 h-8 mx-auto mb-2 text-green-500" />
              <p>現在、危機は発生していません</p>
              <p className="text-xs">平穏を維持しています</p>
            </div>
          )}
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
            className={cn(
              'absolute -top-1 -right-1 w-3 h-3 rounded-full opacity-60',
              sage.alertLevel === 'high' || sage.alertLevel === 'critical' ? 'bg-red-500' : 'bg-incident-400'
            )}
            animate={{
              scale: [1, 1.3, 1],
              opacity: [0.6, 1, 0.6],
              backgroundColor: sage.alertLevel === 'high' || sage.alertLevel === 'critical'
                ? ['#ef4444', '#dc2626', '#ef4444']
                : ['#DC143C', '#b91c1c', '#DC143C']
            }}
            transition={{ duration: 1.5, repeat: Infinity }}
          />
          {(sage.alertLevel === 'high' || sage.alertLevel === 'critical') && (
            <motion.div
              className="absolute top-2 right-8 w-2 h-2 bg-red-400 rounded-full opacity-60"
              animate={{ scale: [1, 1.5, 1], opacity: [0.6, 1, 0.6] }}
              transition={{ duration: 1, repeat: Infinity, delay: 0.3 }}
            />
          )}
        </>
      )}
    </motion.div>
  )
}
