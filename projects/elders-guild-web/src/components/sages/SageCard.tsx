'use client'

import { motion } from 'framer-motion'
import { Activity, AlertCircle, BookOpen, Search, TrendingUp } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Avatar, AvatarFallback } from '@/components/ui/Avatar'
import { Progress } from '@/components/ui/Progress'
import { Button } from '@/components/ui/Button'
import { cn } from '@/lib/utils'
import type { Sage, SageType } from '@/types/sages'

interface SageCardProps {
  sage: Sage
  onSelect?: () => void
  isSelected?: boolean
}

const sageIcons: Record<SageType, React.ReactNode> = {
  knowledge: <BookOpen className="h-5 w-5" />,
  task: <TrendingUp className="h-5 w-5" />,
  incident: <AlertCircle className="h-5 w-5" />,
  rag: <Search className="h-5 w-5" />,
}

const sageAvatarEmojis: Record<SageType, string> = {
  knowledge: '📚',
  task: '📋',
  incident: '🚨',
  rag: '🔍',
}

export function SageCard({ sage, onSelect, isSelected }: SageCardProps) {
  const statusColors = {
    active: 'text-green-600 dark:text-green-400',
    inactive: 'text-gray-500 dark:text-gray-400',
    busy: 'text-yellow-600 dark:text-yellow-400',
    meditation: 'text-purple-600 dark:text-purple-400',
  }

  const getProgressValue = (sage: Sage): number => {
    if (sage.type === 'knowledge') {
      return (sage.experience / 10000) * 100
    } else if (sage.type === 'task') {
      return ((sage.completedTasks || 0) / ((sage.completedTasks || 0) + (sage.activeTasks || 0))) * 100
    } else if (sage.type === 'incident') {
      return 100 - (sage.activeIncidents || 0) * 10
    } else if (sage.type === 'rag') {
      return sage.searchAccuracy || 0
    }
    return 0
  }

  return (
    <motion.div
      whileHover={{ y: -4 }}
      whileTap={{ scale: 0.98 }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card
        variant={sage.type}
        hover
        className={cn(
          'cursor-pointer transition-all duration-200',
          isSelected && 'ring-2 ring-offset-2',
          isSelected && `ring-${sage.type}-500`
        )}
        onClick={onSelect}
      >
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <Avatar sage={sage.type} size="lg">
                <AvatarFallback>
                  <span className="text-2xl">{sageAvatarEmojis[sage.type]}</span>
                </AvatarFallback>
              </Avatar>
              <div>
                <CardTitle className="flex items-center gap-2">
                  {sage.name}
                  <Badge variant={sage.type} size="sm">
                    Lv.{sage.level}
                  </Badge>
                </CardTitle>
                <CardDescription>{sage.title}</CardDescription>
              </div>
            </div>
            <div className="flex items-center gap-1">
              {sageIcons[sage.type]}
              <Activity className={cn('h-4 w-4', statusColors[sage.status])} />
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-sage-600 dark:text-sage-400">
                {sage.activity}
              </span>
              <Badge variant="secondary" size="sm" pulse={sage.status === 'active'}>
                {sage.status === 'active' ? '稼働中' :
                 sage.status === 'busy' ? '多忙' :
                 sage.status === 'meditation' ? '瞑想中' : '休止中'}
              </Badge>
            </div>
            <Progress
              value={getProgressValue(sage)}
              variant={sage.type}
              showValue
            />
          </div>

          <div className="grid grid-cols-2 gap-4 pt-2">
            <div className="space-y-1">
              <p className="text-xs text-sage-500 dark:text-sage-400">
                {sage.metrics.primary.label}
              </p>
              <p className="text-lg font-semibold">
                {sage.metrics.primary.value}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-xs text-sage-500 dark:text-sage-400">
                {sage.metrics.secondary.label}
              </p>
              <p className="text-lg font-semibold">
                {sage.metrics.secondary.value}
              </p>
            </div>
          </div>

          <div className="flex gap-2 pt-2">
            <Button
              size="sm"
              variant={sage.type}
              className="flex-1"
              onClick={(e) => {
                e.stopPropagation()
                // Handle primary action
              }}
            >
              詳細を見る
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={(e) => {
                e.stopPropagation()
                // Handle secondary action
              }}
            >
              設定
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}
