'use client'

import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { BookOpen, GitBranch, Clock, Search, Filter, ChevronRight, FileText, Folder, Tag, History } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'

interface KnowledgeItem {
  id: string
  title: string
  content: string
  category: string
  tags: string[]
  lastModified: string
  version: string
  author: string
  type: 'document' | 'note' | 'guide' | 'reference'
  connections: string[]
}

interface KnowledgeBaseViewerProps {
  items: KnowledgeItem[]
  className?: string
}

export function KnowledgeBaseViewer({ items, className }: KnowledgeBaseViewerProps) {
  const [selectedItem, setSelectedItem] = useState<KnowledgeItem | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<'grid' | 'list' | 'graph'>('grid')

  const categories = Array.from(new Set(items.map(item => item.category)))
  
  const filteredItems = items.filter(item => {
    const matchesSearch = searchQuery === '' || 
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
    
    const matchesCategory = !selectedCategory || item.category === selectedCategory
    
    return matchesSearch && matchesCategory
  })

  const getTypeIcon = (type: KnowledgeItem['type']) => {
    switch (type) {
      case 'document': return <FileText className="w-4 h-4" />
      case 'note': return <BookOpen className="w-4 h-4" />
      case 'guide': return <GitBranch className="w-4 h-4" />
      case 'reference': return <Folder className="w-4 h-4" />
    }
  }

  const getTypeColor = (type: KnowledgeItem['type']) => {
    switch (type) {
      case 'document': return 'bg-purple-100 text-purple-800'
      case 'note': return 'bg-indigo-100 text-indigo-800'
      case 'guide': return 'bg-violet-100 text-violet-800'
      case 'reference': return 'bg-purple-100 text-purple-800'
    }
  }

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header Controls */}
      <div className="flex flex-col lg:flex-row gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="知識ベースを検索..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
        </div>
        
        <div className="flex gap-2">
          <select
            value={selectedCategory || ''}
            onChange={(e) => setSelectedCategory(e.target.value || null)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
          >
            <option value="">すべてのカテゴリ</option>
            {categories.map(category => (
              <option key={category} value={category}>{category}</option>
            ))}
          </select>
          
          <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
            {(['grid', 'list', 'graph'] as const).map(mode => (
              <button
                key={mode}
                onClick={() => setViewMode(mode)}
                className={cn(
                  'px-3 py-1 rounded text-sm font-medium transition-colors',
                  viewMode === mode
                    ? 'bg-purple-500 text-white'
                    : 'text-gray-600 hover:text-gray-900'
                )}
              >
                {mode === 'grid' ? 'グリッド' : mode === 'list' ? 'リスト' : 'グラフ'}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Items List */}
        <div className="lg:col-span-2">
          <AnimatePresence mode="wait">
            {viewMode === 'grid' && (
              <motion.div
                key="grid"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="grid grid-cols-1 md:grid-cols-2 gap-4"
              >
                {filteredItems.map((item) => (
                  <motion.div
                    key={item.id}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <Card
                      className={cn(
                        'p-4 cursor-pointer transition-all duration-200',
                        'hover:shadow-lg hover:border-purple-300',
                        selectedItem?.id === item.id && 'ring-2 ring-purple-500 border-purple-500'
                      )}
                      onClick={() => setSelectedItem(item)}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className={cn('p-2 rounded-lg', getTypeColor(item.type))}>
                          {getTypeIcon(item.type)}
                        </div>
                        <Badge variant="secondary" className="text-xs">
                          v{item.version}
                        </Badge>
                      </div>
                      
                      <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">
                        {item.title}
                      </h3>
                      
                      <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                        {item.content}
                      </p>
                      
                      <div className="flex flex-wrap gap-1 mb-3">
                        {item.tags.slice(0, 3).map((tag) => (
                          <span
                            key={tag}
                            className="px-2 py-1 bg-purple-50 text-purple-700 text-xs rounded"
                          >
                            #{tag}
                          </span>
                        ))}
                        {item.tags.length > 3 && (
                          <span className="text-xs text-gray-500">
                            +{item.tags.length - 3}
                          </span>
                        )}
                      </div>
                      
                      <div className="flex items-center justify-between text-xs text-gray-500">
                        <span>{item.author}</span>
                        <span>{new Date(item.lastModified).toLocaleDateString('ja-JP')}</span>
                      </div>
                    </Card>
                  </motion.div>
                ))}
              </motion.div>
            )}

            {viewMode === 'list' && (
              <motion.div
                key="list"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="space-y-2"
              >
                {filteredItems.map((item) => (
                  <motion.div
                    key={item.id}
                    whileHover={{ x: 4 }}
                    className={cn(
                      'p-4 bg-white border rounded-lg cursor-pointer transition-all duration-200',
                      'hover:shadow-md hover:border-purple-300',
                      selectedItem?.id === item.id && 'ring-2 ring-purple-500 border-purple-500'
                    )}
                    onClick={() => setSelectedItem(item)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className={cn('p-2 rounded-lg', getTypeColor(item.type))}>
                          {getTypeIcon(item.type)}
                        </div>
                        <div>
                          <h3 className="font-semibold text-gray-900">
                            {item.title}
                          </h3>
                          <div className="flex items-center space-x-4 text-sm text-gray-500">
                            <span>{item.category}</span>
                            <span>•</span>
                            <span>{item.author}</span>
                            <span>•</span>
                            <span>{new Date(item.lastModified).toLocaleDateString('ja-JP')}</span>
                          </div>
                        </div>
                      </div>
                      <ChevronRight className="w-5 h-5 text-gray-400" />
                    </div>
                  </motion.div>
                ))}
              </motion.div>
            )}

            {viewMode === 'graph' && (
              <motion.div
                key="graph"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="h-96 bg-gray-50 rounded-lg flex items-center justify-center"
              >
                <div className="text-center text-gray-500">
                  <GitBranch className="w-12 h-12 mx-auto mb-2" />
                  <p>知識グラフビュー</p>
                  <p className="text-sm">（実装予定）</p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Detail Panel */}
        <div className="lg:col-span-1">
          <AnimatePresence mode="wait">
            {selectedItem ? (
              <motion.div
                key={selectedItem.id}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="sticky top-6"
              >
                <Card className="p-6">
                  <div className="mb-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className={cn('p-2 rounded-lg', getTypeColor(selectedItem.type))}>
                        {getTypeIcon(selectedItem.type)}
                      </div>
                      <Badge variant="secondary">v{selectedItem.version}</Badge>
                    </div>
                    <h2 className="text-xl font-bold text-gray-900 mb-2">
                      {selectedItem.title}
                    </h2>
                    <div className="flex items-center space-x-4 text-sm text-gray-500 mb-4">
                      <span>{selectedItem.category}</span>
                      <span>•</span>
                      <span>{selectedItem.author}</span>
                    </div>
                  </div>

                  <div className="prose prose-sm max-w-none mb-6">
                    <p className="text-gray-700">{selectedItem.content}</p>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <h3 className="text-sm font-semibold text-gray-700 mb-2 flex items-center">
                        <Tag className="w-4 h-4 mr-1" />
                        タグ
                      </h3>
                      <div className="flex flex-wrap gap-1">
                        {selectedItem.tags.map((tag) => (
                          <span
                            key={tag}
                            className="px-2 py-1 bg-purple-50 text-purple-700 text-xs rounded"
                          >
                            #{tag}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h3 className="text-sm font-semibold text-gray-700 mb-2 flex items-center">
                        <GitBranch className="w-4 h-4 mr-1" />
                        関連ドキュメント
                      </h3>
                      <div className="space-y-1">
                        {selectedItem.connections.map((connection) => (
                          <div
                            key={connection}
                            className="text-sm text-purple-600 hover:text-purple-800 cursor-pointer"
                          >
                            → {connection}
                          </div>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h3 className="text-sm font-semibold text-gray-700 mb-2 flex items-center">
                        <History className="w-4 h-4 mr-1" />
                        更新履歴
                      </h3>
                      <div className="text-sm text-gray-500">
                        <div>最終更新: {new Date(selectedItem.lastModified).toLocaleString('ja-JP')}</div>
                        <Button variant="link" className="p-0 h-auto text-purple-600">
                          履歴を表示
                        </Button>
                      </div>
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
                  <BookOpen className="w-12 h-12 mx-auto mb-2" />
                  <p>アイテムを選択してください</p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}