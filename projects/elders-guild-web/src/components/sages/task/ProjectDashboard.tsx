'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Briefcase, Users, Target, TrendingUp, Clock, AlertTriangle, CheckCircle, Activity } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Progress } from '@/components/ui/Progress'
import { Avatar } from '@/components/ui/Avatar'
import { Button } from '@/components/ui/Button'

interface Project {
  id: string
  name: string
  description: string
  status: 'planning' | 'active' | 'review' | 'completed' | 'on_hold'
  priority: 'low' | 'medium' | 'high'
  startDate: string
  endDate: string
  progress: number
  team: {
    id: string
    name: string
    avatar: string
    role: string
  }[]
  tasks: {
    total: number
    completed: number
    inProgress: number
    todo: number
  }
  milestones: {
    id: string
    name: string
    date: string
    completed: boolean
  }[]
  budget: {
    allocated: number
    spent: number
    currency: string
  }
  risks: {
    id: string
    title: string
    severity: 'low' | 'medium' | 'high'
    status: 'open' | 'mitigated' | 'closed'
  }[]
}

interface ProjectDashboardProps {
  projects: Project[]
  onProjectSelect?: (project: Project) => void
  className?: string
}

export function ProjectDashboard({ projects, onProjectSelect, className }: ProjectDashboardProps) {
  const [selectedProject, setSelectedProject] = useState<Project | null>(projects[0] || null)
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')

  const getStatusColor = (status: Project['status']) => {
    switch (status) {
      case 'planning': return 'bg-gray-100 text-gray-700 border-gray-300'
      case 'active': return 'bg-blue-100 text-blue-700 border-blue-300'
      case 'review': return 'bg-yellow-100 text-yellow-700 border-yellow-300'
      case 'completed': return 'bg-green-100 text-green-700 border-green-300'
      case 'on_hold': return 'bg-red-100 text-red-700 border-red-300'
    }
  }

  const getStatusLabel = (status: Project['status']) => {
    switch (status) {
      case 'planning': return '計画中'
      case 'active': return '進行中'
      case 'review': return 'レビュー'
      case 'completed': return '完了'
      case 'on_hold': return '保留'
    }
  }

  const getPriorityIcon = (priority: Project['priority']) => {
    switch (priority) {
      case 'low': return '▽'
      case 'medium': return '◇'
      case 'high': return '△'
    }
  }

  const getRiskColor = (severity: 'low' | 'medium' | 'high') => {
    switch (severity) {
      case 'low': return 'text-yellow-600'
      case 'medium': return 'text-orange-600'
      case 'high': return 'text-red-600'
    }
  }

  const getDaysRemaining = (endDate: string) => {
    const now = new Date()
    const end = new Date(endDate)
    const diffTime = end.getTime() - now.getTime()
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    return diffDays
  }

  const handleProjectSelect = (project: Project) => {
    setSelectedProject(project)
    onProjectSelect?.(project)
  }

  return (
    <div className={cn('space-y-6', className)}>
      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="p-6 bg-gradient-to-br from-goldenrod-50 to-white border-goldenrod-200">
            <div className="flex items-center justify-between mb-2">
              <Briefcase className="w-8 h-8 text-goldenrod-600" />
              <TrendingUp className="w-5 h-5 text-green-500" />
            </div>
            <h3 className="text-2xl font-bold text-gray-900">{projects.length}</h3>
            <p className="text-sm text-gray-600">総プロジェクト</p>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="p-6 bg-gradient-to-br from-blue-50 to-white border-blue-200">
            <div className="flex items-center justify-between mb-2">
              <Activity className="w-8 h-8 text-blue-600" />
              <Badge variant="secondary" className="text-xs bg-blue-100 text-blue-700">
                {projects.filter(p => p.status === 'active').length}
              </Badge>
            </div>
            <h3 className="text-2xl font-bold text-gray-900">
              {Math.round(projects.reduce((acc, p) => acc + p.progress, 0) / projects.length)}%
            </h3>
            <p className="text-sm text-gray-600">平均進捗率</p>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card className="p-6 bg-gradient-to-br from-green-50 to-white border-green-200">
            <div className="flex items-center justify-between mb-2">
              <CheckCircle className="w-8 h-8 text-green-600" />
              <span className="text-sm font-medium text-green-600">
                +{projects.filter(p => p.status === 'completed').length}
              </span>
            </div>
            <h3 className="text-2xl font-bold text-gray-900">
              {projects.reduce((acc, p) => acc + p.tasks.completed, 0)}
            </h3>
            <p className="text-sm text-gray-600">完了タスク</p>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <Card className="p-6 bg-gradient-to-br from-red-50 to-white border-red-200">
            <div className="flex items-center justify-between mb-2">
              <AlertTriangle className="w-8 h-8 text-red-600" />
              <Badge variant="secondary" className="text-xs bg-red-100 text-red-700">
                要対応
              </Badge>
            </div>
            <h3 className="text-2xl font-bold text-gray-900">
              {projects.reduce((acc, p) => acc + p.risks.filter(r => r.status === 'open').length, 0)}
            </h3>
            <p className="text-sm text-gray-600">アクティブリスク</p>
          </Card>
        </motion.div>
      </div>

      {/* Projects Grid/List */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Projects List */}
        <div className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">プロジェクト一覧</h2>
            <div className="flex items-center space-x-2">
              <Button
                variant={viewMode === 'grid' ? 'secondary' : 'ghost'}
                size="sm"
                onClick={() => setViewMode('grid')}
              >
                グリッド
              </Button>
              <Button
                variant={viewMode === 'list' ? 'secondary' : 'ghost'}
                size="sm"
                onClick={() => setViewMode('list')}
              >
                リスト
              </Button>
            </div>
          </div>

          <div className={cn(
            viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 gap-4' : 'space-y-4'
          )}>
            {projects.map((project) => {
              const daysRemaining = getDaysRemaining(project.endDate)
              const isOverdue = daysRemaining < 0 && project.status !== 'completed'

              return (
                <motion.div
                  key={project.id}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <Card
                    className={cn(
                      'p-4 cursor-pointer transition-all duration-200',
                      'hover:shadow-lg hover:border-goldenrod-300',
                      selectedProject?.id === project.id && 'ring-2 ring-goldenrod-500 border-goldenrod-500'
                    )}
                    onClick={() => handleProjectSelect(project)}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center space-x-2">
                        <span className="text-lg">{getPriorityIcon(project.priority)}</span>
                        <h3 className="font-semibold text-gray-900">{project.name}</h3>
                      </div>
                      <Badge className={cn('text-xs border', getStatusColor(project.status))}>
                        {getStatusLabel(project.status)}
                      </Badge>
                    </div>

                    <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                      {project.description}
                    </p>

                    {/* Progress */}
                    <div className="mb-3">
                      <div className="flex justify-between text-xs text-gray-500 mb-1">
                        <span>進捗</span>
                        <span>{project.progress}%</span>
                      </div>
                      <Progress value={project.progress} className="h-2" />
                    </div>

                    {/* Tasks Summary */}
                    <div className="flex items-center justify-between mb-3 text-sm">
                      <div className="flex items-center space-x-4">
                        <span className="text-gray-500">
                          タスク: {project.tasks.completed}/{project.tasks.total}
                        </span>
                        <span className={cn(
                          'font-medium',
                          isOverdue ? 'text-red-600' : 'text-gray-600'
                        )}>
                          {isOverdue ? `${Math.abs(daysRemaining)}日遅延` :
                           daysRemaining === 0 ? '今日締切' :
                           `残り${daysRemaining}日`}
                        </span>
                      </div>
                    </div>

                    {/* Team Avatars */}
                    <div className="flex items-center justify-between">
                      <div className="flex -space-x-2">
                        {project.team.slice(0, 3).map((member) => (
                          <Avatar
                            key={member.id}
                            src={member.avatar}
                            alt={member.name}
                            size="sm"
                            className="ring-2 ring-white"
                            fallback={member.name.slice(0, 2)}
                          />
                        ))}
                        {project.team.length > 3 && (
                          <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-xs font-medium text-gray-600 ring-2 ring-white">
                            +{project.team.length - 3}
                          </div>
                        )}
                      </div>
                      {project.risks.filter(r => r.status === 'open').length > 0 && (
                        <div className="flex items-center space-x-1">
                          <AlertTriangle className={cn(
                            'w-4 h-4',
                            getRiskColor(project.risks.filter(r => r.status === 'open')[0].severity)
                          )} />
                          <span className="text-xs text-gray-500">
                            {project.risks.filter(r => r.status === 'open').length} リスク
                          </span>
                        </div>
                      )}
                    </div>
                  </Card>
                </motion.div>
              )
            })}
          </div>
        </div>

        {/* Selected Project Details */}
        <div className="lg:col-span-1">
          {selectedProject ? (
            <motion.div
              key={selectedProject.id}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="sticky top-6"
            >
              <Card className="p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4">
                  {selectedProject.name}
                </h2>

                {/* Milestones */}
                <div className="mb-6">
                  <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
                    <Target className="w-4 h-4 mr-2 text-goldenrod-600" />
                    マイルストーン
                  </h3>
                  <div className="space-y-2">
                    {selectedProject.milestones.map((milestone) => (
                      <div
                        key={milestone.id}
                        className="flex items-center justify-between p-2 bg-gray-50 rounded"
                      >
                        <div className="flex items-center space-x-2">
                          <div className={cn(
                            'w-2 h-2 rounded-full',
                            milestone.completed ? 'bg-green-500' : 'bg-gray-300'
                          )} />
                          <span className={cn(
                            'text-sm',
                            milestone.completed && 'line-through text-gray-500'
                          )}>
                            {milestone.name}
                          </span>
                        </div>
                        <span className="text-xs text-gray-500">
                          {new Date(milestone.date).toLocaleDateString('ja-JP')}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Budget */}
                <div className="mb-6">
                  <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
                    <Clock className="w-4 h-4 mr-2 text-goldenrod-600" />
                    予算状況
                  </h3>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">配分予算</span>
                      <span className="font-medium">
                        {selectedProject.budget.currency}{selectedProject.budget.allocated.toLocaleString()}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">使用済み</span>
                      <span className="font-medium text-orange-600">
                        {selectedProject.budget.currency}{selectedProject.budget.spent.toLocaleString()}
                      </span>
                    </div>
                    <Progress
                      value={(selectedProject.budget.spent / selectedProject.budget.allocated) * 100}
                      className="h-2"
                    />
                    <div className="text-xs text-gray-500 text-right">
                      {Math.round((selectedProject.budget.spent / selectedProject.budget.allocated) * 100)}% 使用
                    </div>
                  </div>
                </div>

                {/* Team */}
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
                    <Users className="w-4 h-4 mr-2 text-goldenrod-600" />
                    チームメンバー
                  </h3>
                  <div className="space-y-2">
                    {selectedProject.team.map((member) => (
                      <div
                        key={member.id}
                        className="flex items-center space-x-3 p-2 hover:bg-gray-50 rounded"
                      >
                        <Avatar
                          src={member.avatar}
                          alt={member.name}
                          size="sm"
                          fallback={member.name.slice(0, 2)}
                        />
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-900">{member.name}</p>
                          <p className="text-xs text-gray-500">{member.role}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </Card>
            </motion.div>
          ) : (
            <div className="h-full flex items-center justify-center text-gray-400">
              <div className="text-center">
                <Briefcase className="w-12 h-12 mx-auto mb-2" />
                <p>プロジェクトを選択してください</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
