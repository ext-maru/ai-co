'use client'

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { MessageSquare, Send, Share2, AlertCircle, CheckCircle, Clock, ArrowRight } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Avatar } from '@/components/ui/Avatar'

interface SageMessage {
  id: string
  from: string
  to: string[]
  type: 'request' | 'response' | 'notification' | 'collaboration' | 'escalation'
  priority: 'low' | 'medium' | 'high' | 'urgent'
  subject: string
  content: string
  data?: any
  timestamp: string
  status: 'sent' | 'delivered' | 'read' | 'processed' | 'failed'
  relatedContext?: {
    type: 'task' | 'incident' | 'knowledge' | 'search'
    id: string
    title: string
  }
}

interface CommunicationChannel {
  id: string
  name: string
  participants: string[]
  isActive: boolean
  messageCount: number
  lastActivity: string
  purpose: string
}

interface SageCommunicationProps {
  messages: SageMessage[]
  channels: CommunicationChannel[]
  activeSages: string[]
  onSendMessage?: (message: Omit<SageMessage, 'id' | 'timestamp' | 'status'>) => void
  onJoinChannel?: (channelId: string) => void
  className?: string
}

export function SageCommunication({
  messages,
  channels,
  activeSages,
  onSendMessage,
  onJoinChannel,
  className
}: SageCommunicationProps) {
  const [selectedChannel, setSelectedChannel] = useState<CommunicationChannel | null>(channels[0] || null)
  const [messageFilter, setMessageFilter] = useState<'all' | 'unread' | 'high-priority'>('all')
  const [newMessage, setNewMessage] = useState('')
  const [isComposing, setIsComposing] = useState(false)

  const getSageInfo = (sageName: string) => {
    const sageMap: { [key: string]: { icon: string; color: string; theme: string } } = {
      'Knowledge Sage': { icon: '📚', color: '#9333ea', theme: 'purple' },
      'Task Oracle': { icon: '📋', color: '#eab308', theme: 'yellow' },
      'Crisis Sage': { icon: '🚨', color: '#dc2626', theme: 'red' },
      'Search Mystic': { icon: '🔍', color: '#16a34a', theme: 'green' }
    }
    return sageMap[sageName] || { icon: '🧙‍♂️', color: '#6b7280', theme: 'gray' }
  }

  const getMessageTypeIcon = (type: SageMessage['type']) => {
    switch (type) {
      case 'request': return <MessageSquare className="w-4 h-4" />
      case 'response': return <ArrowRight className="w-4 h-4" />
      case 'notification': return <AlertCircle className="w-4 h-4" />
      case 'collaboration': return <Share2 className="w-4 h-4" />
      case 'escalation': return <AlertCircle className="w-4 h-4" />
    }
  }

  const getMessageTypeColor = (type: SageMessage['type']) => {
    switch (type) {
      case 'request': return 'bg-blue-100 text-blue-800'
      case 'response': return 'bg-green-100 text-green-800'
      case 'notification': return 'bg-gray-100 text-gray-800'
      case 'collaboration': return 'bg-purple-100 text-purple-800'
      case 'escalation': return 'bg-red-100 text-red-800'
    }
  }

  const getPriorityColor = (priority: SageMessage['priority']) => {
    switch (priority) {
      case 'urgent': return 'bg-red-500 text-white'
      case 'high': return 'bg-orange-500 text-white'
      case 'medium': return 'bg-yellow-500 text-white'
      case 'low': return 'bg-gray-500 text-white'
    }
  }

  const getStatusIcon = (status: SageMessage['status']) => {
    switch (status) {
      case 'sent': return <Send className="w-3 h-3" />
      case 'delivered': return <CheckCircle className="w-3 h-3" />
      case 'read': return <CheckCircle className="w-3 h-3 text-blue-500" />
      case 'processed': return <CheckCircle className="w-3 h-3 text-green-500" />
      case 'failed': return <AlertCircle className="w-3 h-3 text-red-500" />
    }
  }

  const filteredMessages = messages
    .filter(msg => !selectedChannel || selectedChannel.participants.includes(msg.from) || selectedChannel.participants.includes(msg.to[0]))
    .filter(msg => {
      switch (messageFilter) {
        case 'unread': return msg.status === 'delivered'
        case 'high-priority': return msg.priority === 'high' || msg.priority === 'urgent'
        default: return true
      }
    })
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())

  const handleSendMessage = () => {
    if (!newMessage.trim() || !selectedChannel) return

    const message: Omit<SageMessage, 'id' | 'timestamp' | 'status'> = {
      from: 'System Admin', // In practice, this would be the current user/sage
      to: selectedChannel.participants,
      type: 'notification',
      priority: 'medium',
      subject: 'Manual Message',
      content: newMessage
    }

    onSendMessage?.(message)
    setNewMessage('')
    setIsComposing(false)
  }

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)

    if (diffMins < 1) return '今'
    if (diffMins < 60) return `${diffMins}分前`
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}時間前`
    return date.toLocaleDateString('ja-JP')
  }

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900 flex items-center">
          <MessageSquare className="w-5 h-5 mr-2 text-blue-600" />
          賢者間コミュニケーション
        </h2>
        <div className="flex items-center space-x-2">
          <Badge variant="secondary" className="bg-green-100 text-green-800">
            {activeSages.length} オンライン
          </Badge>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsComposing(!isComposing)}
          >
            <Send className="w-4 h-4 mr-2" />
            新規メッセージ
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Channels Sidebar */}
        <div className="lg:col-span-1">
          <Card className="p-4">
            <h3 className="text-sm font-semibold text-gray-900 mb-3">コミュニケーションチャンネル</h3>

            <div className="space-y-2">
              {channels.map((channel) => (
                <button
                  key={channel.id}
                  onClick={() => setSelectedChannel(channel)}
                  className={cn(
                    'w-full text-left p-3 rounded-lg transition-all duration-200',
                    selectedChannel?.id === channel.id
                      ? 'bg-blue-100 border border-blue-300'
                      : 'hover:bg-gray-50 border border-transparent'
                  )}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-sm text-gray-900">{channel.name}</span>
                    {channel.isActive && (
                      <div className="w-2 h-2 bg-green-500 rounded-full" />
                    )}
                  </div>
                  <p className="text-xs text-gray-600 mb-2">{channel.purpose}</p>
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>{channel.messageCount} メッセージ</span>
                    <span>{formatTimestamp(channel.lastActivity)}</span>
                  </div>
                </button>
              ))}
            </div>
          </Card>
        </div>

        {/* Message Area */}
        <div className="lg:col-span-3">
          <Card className="p-6">
            {/* Message Filters */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
                {[
                  { id: 'all', label: 'すべて' },
                  { id: 'unread', label: '未読' },
                  { id: 'high-priority', label: '高優先度' }
                ].map(({ id, label }) => (
                  <button
                    key={id}
                    onClick={() => setMessageFilter(id as any)}
                    className={cn(
                      'px-3 py-1 rounded text-sm font-medium transition-all duration-200',
                      messageFilter === id
                        ? 'bg-white text-blue-600 shadow-sm'
                        : 'text-gray-600 hover:text-gray-900'
                    )}
                  >
                    {label}
                  </button>
                ))}
              </div>

              {selectedChannel && (
                <div className="text-sm text-gray-600">
                  {selectedChannel.name} • {filteredMessages.length} メッセージ
                </div>
              )}
            </div>

            {/* Compose Message */}
            <AnimatePresence>
              {isComposing && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="mb-4 overflow-hidden"
                >
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <textarea
                      value={newMessage}
                      onChange={(e) => setNewMessage(e.target.value)}
                      placeholder="メッセージを入力..."
                      className="w-full p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      rows={3}
                    />
                    <div className="flex justify-end space-x-2 mt-3">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setIsComposing(false)}
                      >
                        キャンセル
                      </Button>
                      <Button
                        size="sm"
                        onClick={handleSendMessage}
                        disabled={!newMessage.trim()}
                        className="bg-blue-600 hover:bg-blue-700"
                      >
                        送信
                      </Button>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Messages */}
            <div className="space-y-4 max-h-96 overflow-y-auto">
              <AnimatePresence>
                {filteredMessages.map((message) => {
                  const fromSage = getSageInfo(message.from)
                  const isFromCurrentUser = message.from === 'System Admin'

                  return (
                    <motion.div
                      key={message.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -20 }}
                      className={cn(
                        'flex',
                        isFromCurrentUser ? 'justify-end' : 'justify-start'
                      )}
                    >
                      <div className={cn(
                        'max-w-2xl',
                        isFromCurrentUser ? 'order-2' : 'order-1'
                      )}>
                        <div className={cn(
                          'p-4 rounded-lg',
                          isFromCurrentUser
                            ? 'bg-blue-600 text-white'
                            : 'bg-white border border-gray-200'
                        )}>
                          {/* Message Header */}
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center space-x-2">
                              {!isFromCurrentUser && (
                                <span className="text-lg">{fromSage.icon}</span>
                              )}
                              <span className={cn(
                                'text-sm font-medium',
                                isFromCurrentUser ? 'text-blue-100' : 'text-gray-900'
                              )}>
                                {message.from}
                              </span>
                              <Badge className={cn('text-xs', getMessageTypeColor(message.type))}>
                                {getMessageTypeIcon(message.type)}
                                <span className="ml-1">{message.type}</span>
                              </Badge>
                            </div>
                            <div className="flex items-center space-x-2">
                              <Badge className={cn('text-xs', getPriorityColor(message.priority))}>
                                {message.priority}
                              </Badge>
                              {getStatusIcon(message.status)}
                            </div>
                          </div>

                          {/* Message Content */}
                          <div className="mb-2">
                            <h4 className={cn(
                              'font-medium mb-1',
                              isFromCurrentUser ? 'text-white' : 'text-gray-900'
                            )}>
                              {message.subject}
                            </h4>
                            <p className={cn(
                              'text-sm',
                              isFromCurrentUser ? 'text-blue-100' : 'text-gray-700'
                            )}>
                              {message.content}
                            </p>
                          </div>

                          {/* Related Context */}
                          {message.relatedContext && (
                            <div className={cn(
                              'p-2 rounded border-l-4 mt-3',
                              isFromCurrentUser
                                ? 'bg-blue-500 border-blue-300'
                                : 'bg-gray-50 border-gray-300'
                            )}>
                              <div className={cn(
                                'text-xs font-medium',
                                isFromCurrentUser ? 'text-blue-100' : 'text-gray-700'
                              )}>
                                関連: {message.relatedContext.title}
                              </div>
                            </div>
                          )}

                          {/* Timestamp */}
                          <div className={cn(
                            'text-xs mt-2',
                            isFromCurrentUser ? 'text-blue-200' : 'text-gray-500'
                          )}>
                            {formatTimestamp(message.timestamp)}
                          </div>
                        </div>
                      </div>

                      {/* Avatar */}
                      <div className={cn(
                        'flex-shrink-0 mx-3',
                        isFromCurrentUser ? 'order-1' : 'order-2'
                      )}>
                        <div
                          className="w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium"
                          style={{ backgroundColor: fromSage.color }}
                        >
                          {isFromCurrentUser ? 'A' : fromSage.icon}
                        </div>
                      </div>
                    </motion.div>
                  )
                })}
              </AnimatePresence>
            </div>
          </Card>
        </div>
      </div>

      {/* Active Sages Status */}
      <Card className="p-4">
        <h3 className="text-sm font-semibold text-gray-900 mb-3">アクティブ賢者ステータス</h3>
        <div className="flex items-center space-x-4">
          {activeSages.map((sageName) => {
            const sageInfo = getSageInfo(sageName)
            return (
              <div key={sageName} className="flex items-center space-x-2">
                <div className="relative">
                  <div
                    className="w-8 h-8 rounded-full flex items-center justify-center text-white text-sm"
                    style={{ backgroundColor: sageInfo.color }}
                  >
                    {sageInfo.icon}
                  </div>
                  <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-green-500 border-2 border-white rounded-full" />
                </div>
                <span className="text-sm font-medium text-gray-700">{sageName}</span>
              </div>
            )
          })}
        </div>
      </Card>
    </div>
  )
}
