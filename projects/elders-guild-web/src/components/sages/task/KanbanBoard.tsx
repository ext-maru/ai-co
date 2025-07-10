'use client'

import React, { useState } from 'react'
import { motion, AnimatePresence, Reorder } from 'framer-motion'
import { Plus, MoreVertical, Clock, User, Tag, Calendar, AlertCircle, CheckCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Avatar } from '@/components/ui/Avatar'

interface Task {
  id: string
  title: string
  description: string
  status: 'todo' | 'in_progress' | 'review' | 'done'
  priority: 'low' | 'medium' | 'high' | 'urgent'
  assignee: {
    id: string
    name: string
    avatar: string
  }
  tags: string[]
  dueDate: string
  createdAt: string
  estimatedHours: number
  completedHours: number
}

interface Column {
  id: string
  title: string
  status: Task['status']
  color: string
  icon: React.ReactNode
}

interface KanbanBoardProps {
  tasks: Task[]
  onTaskUpdate?: (task: Task) => void
  onTaskCreate?: (status: Task['status']) => void
  className?: string
}

const columns: Column[] = [
  {
    id: 'todo',
    title: 'To Do',
    status: 'todo',
    color: 'bg-gray-100 border-gray-300',
    icon: <AlertCircle className="w-5 h-5 text-gray-600" />
  },
  {
    id: 'in_progress',
    title: '進行中',
    status: 'in_progress',
    color: 'bg-blue-50 border-blue-300',
    icon: <Clock className="w-5 h-5 text-blue-600" />
  },
  {
    id: 'review',
    title: 'レビュー',
    status: 'review',
    color: 'bg-yellow-50 border-yellow-300',
    icon: <User className="w-5 h-5 text-yellow-600" />
  },
  {
    id: 'done',
    title: '完了',
    status: 'done',
    color: 'bg-green-50 border-green-300',
    icon: <CheckCircle className="w-5 h-5 text-green-600" />
  }
]

export function KanbanBoard({ tasks, onTaskUpdate, onTaskCreate, className }: KanbanBoardProps) {
  const [draggedTask, setDraggedTask] = useState<Task | null>(null)
  const [dragOverColumn, setDragOverColumn] = useState<string | null>(null)

  const getPriorityColor = (priority: Task['priority']) => {
    switch (priority) {
      case 'low': return 'bg-gray-100 text-gray-700'
      case 'medium': return 'bg-yellow-100 text-yellow-700'
      case 'high': return 'bg-orange-100 text-orange-700'
      case 'urgent': return 'bg-red-100 text-red-700'
    }
  }

  const getPriorityIcon = (priority: Task['priority']) => {
    switch (priority) {
      case 'low': return '▽'
      case 'medium': return '◇'
      case 'high': return '△'
      case 'urgent': return '🔥'
    }
  }

  const handleDragStart = (task: Task) => {
    setDraggedTask(task)
  }

  const handleDragEnd = () => {
    setDraggedTask(null)
    setDragOverColumn(null)
  }

  const handleDragOver = (e: React.DragEvent, columnId: string) => {
    e.preventDefault()
    setDragOverColumn(columnId)
  }

  const handleDrop = (e: React.DragEvent, status: Task['status']) => {
    e.preventDefault()
    if (draggedTask && onTaskUpdate) {
      onTaskUpdate({
        ...draggedTask,
        status
      })
    }
    setDraggedTask(null)
    setDragOverColumn(null)
  }

  const getTasksByStatus = (status: Task['status']) => {
    return tasks.filter(task => task.status === status)
  }

  const getDaysUntilDue = (dueDate: string) => {
    const now = new Date()
    const due = new Date(dueDate)
    const diffTime = due.getTime() - now.getTime()
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    return diffDays
  }

  return (
    <div className={cn('h-full', className)}>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 h-full">
        {columns.map((column) => (
          <div
            key={column.id}
            className={cn(
              'flex flex-col h-full rounded-lg border-2 transition-all duration-200',
              column.color,
              dragOverColumn === column.id && 'ring-2 ring-goldenrod-400 border-goldenrod-400'
            )}
            onDragOver={(e) => handleDragOver(e, column.id)}
            onDrop={(e) => handleDrop(e, column.status)}
          >
            {/* Column Header */}
            <div className="flex items-center justify-between p-4 border-b">
              <div className="flex items-center space-x-2">
                {column.icon}
                <h3 className="font-semibold text-gray-900">{column.title}</h3>
                <Badge variant="secondary" className="text-xs">
                  {getTasksByStatus(column.status).length}
                </Badge>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onTaskCreate?.(column.status)}
                className="text-gray-500 hover:text-gray-700"
              >
                <Plus className="w-4 h-4" />
              </Button>
            </div>

            {/* Tasks */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              <AnimatePresence mode="popLayout">
                {getTasksByStatus(column.status).map((task) => {
                  const daysUntilDue = getDaysUntilDue(task.dueDate)
                  const isOverdue = daysUntilDue < 0
                  const isDueSoon = daysUntilDue >= 0 && daysUntilDue <= 3

                  return (
                    <motion.div
                      key={task.id}
                      layout
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, scale: 0.8 }}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      draggable
                      onDragStart={() => handleDragStart(task)}
                      onDragEnd={handleDragEnd}
                      className="cursor-move"
                    >
                      <Card className={cn(
                        'p-4 bg-white hover:shadow-lg transition-all duration-200',
                        draggedTask?.id === task.id && 'opacity-50',
                        isOverdue && 'border-red-300',
                        isDueSoon && !isOverdue && 'border-yellow-300'
                      )}>
                        {/* Task Header */}
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center space-x-2">
                            <span className="text-lg">{getPriorityIcon(task.priority)}</span>
                            <Badge className={cn('text-xs', getPriorityColor(task.priority))}>
                              {task.priority === 'urgent' ? '緊急' :
                               task.priority === 'high' ? '高' :
                               task.priority === 'medium' ? '中' : '低'}
                            </Badge>
                          </div>
                          <button className="text-gray-400 hover:text-gray-600">
                            <MoreVertical className="w-4 h-4" />
                          </button>
                        </div>

                        {/* Task Title */}
                        <h4 className="font-medium text-gray-900 mb-2 line-clamp-2">
                          {task.title}
                        </h4>

                        {/* Task Description */}
                        {task.description && (
                          <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                            {task.description}
                          </p>
                        )}

                        {/* Tags */}
                        {task.tags.length > 0 && (
                          <div className="flex flex-wrap gap-1 mb-3">
                            {task.tags.slice(0, 2).map((tag) => (
                              <span
                                key={tag}
                                className="px-2 py-1 bg-goldenrod-50 text-goldenrod-700 text-xs rounded"
                              >
                                #{tag}
                              </span>
                            ))}
                            {task.tags.length > 2 && (
                              <span className="text-xs text-gray-500">
                                +{task.tags.length - 2}
                              </span>
                            )}
                          </div>
                        )}

                        {/* Progress Bar */}
                        {task.estimatedHours > 0 && (
                          <div className="mb-3">
                            <div className="flex justify-between text-xs text-gray-500 mb-1">
                              <span>進捗</span>
                              <span>{task.completedHours}/{task.estimatedHours}h</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-1.5">
                              <div
                                className="bg-goldenrod-500 h-1.5 rounded-full transition-all duration-300"
                                style={{ width: `${Math.min((task.completedHours / task.estimatedHours) * 100, 100)}%` }}
                              />
                            </div>
                          </div>
                        )}

                        {/* Task Footer */}
                        <div className="flex items-center justify-between">
                          <Avatar
                            src={task.assignee.avatar}
                            alt={task.assignee.name}
                            size="sm"
                            fallback={task.assignee.name.slice(0, 2)}
                          />
                          <div className="flex items-center space-x-2 text-xs text-gray-500">
                            <Calendar className="w-3 h-3" />
                            <span className={cn(
                              isOverdue && 'text-red-600 font-medium',
                              isDueSoon && !isOverdue && 'text-yellow-600 font-medium'
                            )}>
                              {isOverdue ? `${Math.abs(daysUntilDue)}日遅延` :
                               daysUntilDue === 0 ? '今日' :
                               daysUntilDue === 1 ? '明日' :
                               `${daysUntilDue}日後`}
                            </span>
                          </div>
                        </div>
                      </Card>
                    </motion.div>
                  )
                })}
              </AnimatePresence>

              {/* Empty State */}
              {getTasksByStatus(column.status).length === 0 && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-center py-8 text-gray-400"
                >
                  <p className="text-sm">タスクがありません</p>
                  <Button
                    variant="link"
                    size="sm"
                    onClick={() => onTaskCreate?.(column.status)}
                    className="mt-2 text-goldenrod-600"
                  >
                    タスクを追加
                  </Button>
                </motion.div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
