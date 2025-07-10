'use client'

import { motion } from 'framer-motion'
import { useSageStore } from '@/stores/sageStore'
import { SageCard } from '@/components/sages/SageCard'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Progress } from '@/components/ui/Progress'
import { Users, Activity, MessageSquare, Zap } from 'lucide-react'

export function Dashboard() {
  const {
    sages,
    selectedSage,
    selectSage,
    culturalMode,
    getActiveSages,
    getCouncilStatus,
    startCouncilSession,
    messages
  } = useSageStore()

  const activeSages = getActiveSages()
  const councilStatus = getCouncilStatus()

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  }

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        type: "spring" as const,
        stiffness: 100
      }
    }
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Status Overview */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="mb-8 grid gap-4 md:grid-cols-4"
      >
        <motion.div variants={itemVariants}>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {culturalMode ? '稼働状況' : 'System Status'}
              </CardTitle>
              <Activity className="h-4 w-4 text-sage-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{activeSages.length}/4</div>
              <Progress value={(activeSages.length / 4) * 100} className="mt-2" />
              <p className="text-xs text-sage-500 mt-2">
                {culturalMode ? '賢者稼働中' : 'Sages Active'}
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={itemVariants}>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {culturalMode ? '評議会' : 'Council'}
              </CardTitle>
              <Users className="h-4 w-4 text-elder-600" />
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <Badge
                  variant={councilStatus === 'active' ? 'elder' : 'secondary'}
                  pulse={councilStatus === 'active'}
                >
                  {councilStatus === 'active'
                    ? (culturalMode ? '開催中' : 'In Session')
                    : (culturalMode ? '待機中' : 'Standby')
                  }
                </Badge>
              </div>
              <Button
                size="sm"
                variant="outline"
                className="mt-3 w-full"
                onClick={() => startCouncilSession({
                  type: 'regular',
                  participants: activeSages,
                  agenda: ['System Review', 'Task Allocation'],
                  decisions: []
                })}
                disabled={councilStatus === 'active'}
              >
                {culturalMode ? '評議会を開始' : 'Start Council'}
              </Button>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={itemVariants}>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {culturalMode ? 'メッセージ' : 'Messages'}
              </CardTitle>
              <MessageSquare className="h-4 w-4 text-knowledge-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{messages.length}</div>
              <p className="text-xs text-sage-500 mt-2">
                {culturalMode ? '未読メッセージ' : 'Unread Messages'}
              </p>
              <div className="mt-3 flex gap-1">
                {['knowledge', 'task', 'incident', 'rag'].map((type) => {
                  const count = messages.filter(m => m.from === type).length
                  return count > 0 ? (
                    <Badge key={type} variant={type as 'knowledge' | 'task' | 'incident' | 'rag'} size="sm">
                      {count}
                    </Badge>
                  ) : null
                })}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={itemVariants}>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {culturalMode ? 'システム効率' : 'System Efficiency'}
              </CardTitle>
              <Zap className="h-4 w-4 text-yellow-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">92%</div>
              <Progress value={92} variant="task" className="mt-2" />
              <p className="text-xs text-sage-500 mt-2">
                {culturalMode ? '最適化済み' : 'Optimized'}
              </p>
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>

      {/* Sages Grid */}
      <motion.div variants={containerVariants} initial="hidden" animate="visible">
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-2xl font-bold text-sage-900 dark:text-sage-50">
            {culturalMode ? '四賢者' : 'Four Sages'}
          </h2>
          <Badge variant="outline" size="lg">
            {culturalMode ? '自動同期中' : 'Auto-sync Active'}
          </Badge>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {sages.map((sage) => (
            <motion.div key={sage.id} variants={itemVariants}>
              <SageCard
                sage={sage}
                isSelected={selectedSage === sage.type}
                onSelect={() => selectSage(sage.type)}
              />
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Recent Activity */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="mt-8"
      >
        <Card>
          <CardHeader>
            <CardTitle>{culturalMode ? '最新の活動' : 'Recent Activity'}</CardTitle>
            <CardDescription>
              {culturalMode ? '賢者たちの最新の動向' : 'Latest updates from the sages'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {messages.slice(0, 5).map((message) => (
                <div key={message.id} className="flex items-start gap-3">
                  <Badge variant={message.from as 'knowledge' | 'task' | 'incident' | 'rag'} size="sm">
                    {message.from}
                  </Badge>
                  <div className="flex-1">
                    <p className="text-sm">{message.content}</p>
                    <p className="text-xs text-sage-500 mt-1">
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </p>
                  </div>
                  <Badge
                    variant={
                      message.priority === 'urgent' ? 'destructive' :
                      message.priority === 'high' ? 'incident' :
                      message.priority === 'medium' ? 'task' :
                      'secondary'
                    }
                    size="sm"
                  >
                    {message.priority}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}
