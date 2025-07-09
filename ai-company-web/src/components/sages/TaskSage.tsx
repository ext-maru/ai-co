'use client'

import React from 'react'
import { motion } from 'framer-motion'
import { CheckCircle, Clock, AlertTriangle, Target } from 'lucide-react'
import { TaskSage as TaskSageType } from '@/types/sages'
import { cn, getSageThemeClasses, formatJapaneseDateTime, getPriorityColor } from '@/lib/utils'

interface TaskSageProps {
  sage: TaskSageType
  isSelected?: boolean
  onSelect?: () => void
  className?: string
}

export function TaskSage({ sage, isSelected = false, onSelect, className }: TaskSageProps) {
  const theme = getSageThemeClasses('task')
  
  const completionRate = sage.completedTasks / (sage.activeTasks + sage.completedTasks) * 100

  return (
    <motion.div
      className={cn(
        'relative bg-white border rounded-lg p-6 cursor-pointer transition-all duration-300',
        theme.shadow,
        isSelected ? `ring-2 ${theme.ring} ${theme.border}` : 'border-gray-200 hover:border-task-300',
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
            📋
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
          {sage.status === 'active' ? '指導中' : 
           sage.status === 'busy' ? '修行監督中' : '休息中'}
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
            <Target className="w-4 h-4" />
            <span className="text-sm font-medium">{sage.metrics.primary.label}</span>
          </div>
          <p className="text-xl font-bold">{sage.metrics.primary.value}</p>
        </div>
        <div className={cn('p-3 rounded-lg', theme.secondary)}>
          <div className="flex items-center space-x-2 mb-1">
            <CheckCircle className="w-4 h-4" />
            <span className="text-sm font-medium">{sage.metrics.secondary.label}</span>
          </div>
          <p className="text-xl font-bold">{sage.metrics.secondary.value}</p>
        </div>
      </div>

      {/* Task Statistics */}
      <div className="mb-4">
        <div className="flex items-center space-x-2 mb-2">
          <Clock className="w-4 h-4 text-task-600" />
          <span className="text-sm font-medium text-gray-700">修行録統計</span>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center p-2 bg-blue-50 rounded">
            <p className="text-2xl font-bold text-blue-600">{sage.activeTasks}</p>
            <p className="text-xs text-blue-600">進行中</p>
          </div>
          <div className="text-center p-2 bg-green-50 rounded">
            <p className="text-2xl font-bold text-green-600">{sage.completedTasks}</p>
            <p className="text-xs text-green-600">完了</p>
          </div>
        </div>
      </div>

      {/* Completion Rate */}
      <div className="mb-4">
        <div className="flex justify-between items-center mb-1">
          <span className="text-sm font-medium text-gray-700">修行完了率</span>
          <span className="text-sm font-bold text-task-600">{completionRate.toFixed(1)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className={cn('h-2 rounded-full', theme.primary)}
            style={{ width: `${completionRate}%` }}
          />
        </div>
      </div>

      {/* Task Queue */}
      <div className="mb-4">
        <div className="flex items-center space-x-2 mb-2">
          <AlertTriangle className="w-4 h-4 text-task-600" />
          <span className="text-sm font-medium text-gray-700">修行録キュー</span>
        </div>
        <div className="space-y-2">
          {sage.taskQueue.slice(0, 3).map((task) => (
            <div key={task.id} className="p-2 bg-gray-50 rounded text-xs">
              <div className="flex justify-between items-start mb-1">
                <p className="font-medium text-gray-900 line-clamp-1 flex-1">{task.title}</p>
                <span className={cn(
                  'px-2 py-1 rounded text-xs font-medium ml-2 flex-shrink-0',
                  getPriorityColor(task.priority)
                )}>
                  {task.priority === 'high' ? '緊急' : 
                   task.priority === 'medium' ? '通常' : '低'}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className={cn(
                  'px-2 py-1 rounded text-xs',
                  task.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                  task.status === 'completed' ? 'bg-green-100 text-green-800' :
                  'bg-gray-100 text-gray-800'
                )}>
                  {task.status === 'in_progress' ? '修行中' :
                   task.status === 'completed' ? '悟得' : '待機中'}
                </span>
                {task.deadline && (
                  <span className="text-gray-500">
                    期限: {new Date(task.deadline).toLocaleDateString('ja-JP')}
                  </span>
                )}
              </div>
              {task.assignedTo && (
                <p className="text-gray-500 mt-1">担当: {task.assignedTo}</p>
              )}
            </div>
          ))}
          {sage.taskQueue.length > 3 && (
            <p className="text-center text-xs text-gray-500">
              他 {sage.taskQueue.length - 3} 件の修行録...
            </p>
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
            className="absolute -top-1 -right-1 w-3 h-3 bg-task-400 rounded-full opacity-60"
            animate={{ scale: [1, 1.2, 1], opacity: [0.6, 1, 0.6] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
          <motion.div
            className="absolute top-2 right-8 w-2 h-2 bg-task-300 rounded-full opacity-40"
            animate={{ x: [-2, 2, -2], opacity: [0.4, 0.8, 0.4] }}
            transition={{ duration: 3, repeat: Infinity }}
          />
        </>
      )}
    </motion.div>
  )
}