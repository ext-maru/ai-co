'use client'

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, Filter, Clock, Star, TrendingUp, FileText, User, Tag } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Avatar } from '@/components/ui/Avatar'

interface SearchResult {
  id: string
  title: string
  content: string
  type: 'document' | 'task' | 'incident' | 'user' | 'code'
  source: string
  relevanceScore: number
  lastModified: string
  author?: {
    id: string
    name: string
    avatar: string
  }
  tags: string[]
  highlights: {
    field: string
    matches: string[]
  }[]
  url: string
}

interface SearchFilter {
  types: string[]
  sources: string[]
  dateRange: 'all' | '24h' | '7d' | '30d' | '90d'
  sortBy: 'relevance' | 'date' | 'popularity'
}

interface GlobalSearchInterfaceProps {
  onSearch?: (query: string, filters: SearchFilter) => void
  initialResults?: SearchResult[]
  isLoading?: boolean
  className?: string
}

export function GlobalSearchInterface({
  onSearch,
  initialResults = [],
  isLoading = false,
  className
}: GlobalSearchInterfaceProps) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>(initialResults)
  const [filters, setFilters] = useState<SearchFilter>({
    types: [],
    sources: [],
    dateRange: 'all',
    sortBy: 'relevance'
  })
  const [showFilters, setShowFilters] = useState(false)
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [recentSearches, setRecentSearches] = useState<string[]>([])

  useEffect(() => {
    // Load recent searches from localStorage
    const saved = localStorage.getItem('recentSearches')
    if (saved) {
      setRecentSearches(JSON.parse(saved))
    }
  }, [])

  useEffect(() => {
    if (query.length > 2) {
      // Simulate search suggestions
      const mockSuggestions = [
        'APIドキュメント',
        'データベース設計',
        'セキュリティガイド',
        'デプロイメント手順',
        'パフォーマンス最適化'
      ].filter(s => s.toLowerCase().includes(query.toLowerCase()))
      setSuggestions(mockSuggestions)
    } else {
      setSuggestions([])
    }
  }, [query])

  const getTypeIcon = (type: SearchResult['type']) => {
    switch (type) {
      case 'document': return '📄'
      case 'task': return '✅'
      case 'incident': return '🚨'
      case 'user': return '👤'
      case 'code': return '💻'
    }
  }

  const getTypeColor = (type: SearchResult['type']) => {
    switch (type) {
      case 'document': return 'bg-blue-100 text-blue-800'
      case 'task': return 'bg-green-100 text-green-800'
      case 'incident': return 'bg-red-100 text-red-800'
      case 'user': return 'bg-purple-100 text-purple-800'
      case 'code': return 'bg-gray-100 text-gray-800'
    }
  }

  const handleSearch = () => {
    if (query.trim()) {
      // Add to recent searches
      const updated = [query, ...recentSearches.filter(s => s !== query)].slice(0, 5)
      setRecentSearches(updated)
      localStorage.setItem('recentSearches', JSON.stringify(updated))

      onSearch?.(query, filters)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  const clearFilters = () => {
    setFilters({
      types: [],
      sources: [],
      dateRange: 'all',
      sortBy: 'relevance'
    })
  }

  const toggleFilter = (category: keyof SearchFilter, value: string) => {
    setFilters(prev => {
      const current = prev[category] as string[]
      const updated = current.includes(value)
        ? current.filter(v => v !== value)
        : [...current, value]
      return { ...prev, [category]: updated }
    })
  }

  const highlightText = (text: string, highlights: string[]) => {
    if (!highlights.length) return text

    let highlightedText = text
    highlights.forEach(highlight => {
      const regex = new RegExp(`(${highlight})`, 'gi')
      highlightedText = highlightedText.replace(regex, '<mark class="bg-lime-200 text-lime-900">$1</mark>')
    })

    return <span dangerouslySetInnerHTML={{ __html: highlightedText }} />
  }

  return (
    <div className={cn('space-y-6', className)}>
      {/* Search Input */}
      <Card className="p-6">
        <div className="relative">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-6 h-6 text-gray-400" />
            <input
              type="text"
              placeholder="すべてを検索..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              className="w-full pl-12 pr-4 py-4 text-lg border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-lime-500 focus:border-lime-500 transition-all duration-200"
            />
            {query && (
              <Button
                onClick={handleSearch}
                className="absolute right-2 top-1/2 transform -translate-y-1/2 bg-lime-600 hover:bg-lime-700"
                disabled={isLoading}
              >
                {isLoading ? '検索中...' : '検索'}
              </Button>
            )}
          </div>

          {/* Search Suggestions */}
          <AnimatePresence>
            {(suggestions.length > 0 || recentSearches.length > 0) && query && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="absolute top-full left-0 right-0 mt-2 bg-white border border-gray-200 rounded-lg shadow-lg z-50"
              >
                {suggestions.length > 0 && (
                  <div className="p-2">
                    <div className="text-xs font-medium text-gray-500 px-2 py-1">候補</div>
                    {suggestions.map((suggestion) => (
                      <button
                        key={suggestion}
                        onClick={() => {
                          setQuery(suggestion)
                          setSuggestions([])
                        }}
                        className="w-full text-left px-3 py-2 hover:bg-gray-50 rounded flex items-center space-x-2"
                      >
                        <Search className="w-4 h-4 text-gray-400" />
                        <span>{suggestion}</span>
                      </button>
                    ))}
                  </div>
                )}

                {recentSearches.length > 0 && !suggestions.length && (
                  <div className="p-2">
                    <div className="text-xs font-medium text-gray-500 px-2 py-1">最近の検索</div>
                    {recentSearches.map((recent) => (
                      <button
                        key={recent}
                        onClick={() => {
                          setQuery(recent)
                          setSuggestions([])
                        }}
                        className="w-full text-left px-3 py-2 hover:bg-gray-50 rounded flex items-center space-x-2"
                      >
                        <Clock className="w-4 h-4 text-gray-400" />
                        <span>{recent}</span>
                      </button>
                    ))}
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Quick Filters */}
        <div className="flex items-center justify-between mt-4">
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center space-x-2"
            >
              <Filter className="w-4 h-4" />
              <span>フィルター</span>
              {(filters.types.length + filters.sources.length > 0 || filters.dateRange !== 'all') && (
                <Badge variant="secondary" className="ml-1">
                  {filters.types.length + filters.sources.length + (filters.dateRange !== 'all' ? 1 : 0)}
                </Badge>
              )}
            </Button>

            {Object.values(filters).some(f => Array.isArray(f) ? f.length > 0 : f !== 'all' && f !== 'relevance') && (
              <Button variant="ghost" size="sm" onClick={clearFilters}>
                クリア
              </Button>
            )}
          </div>

          <div className="flex items-center space-x-2 text-sm text-gray-500">
            <span>並び順:</span>
            <select
              value={filters.sortBy}
              onChange={(e) => setFilters(prev => ({ ...prev, sortBy: e.target.value as any }))}
              className="border border-gray-300 rounded px-2 py-1 text-sm"
            >
              <option value="relevance">関連度</option>
              <option value="date">更新日</option>
              <option value="popularity">人気</option>
            </select>
          </div>
        </div>

        {/* Advanced Filters */}
        <AnimatePresence>
          {showFilters && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="mt-4 overflow-hidden"
            >
              <div className="border-t pt-4 space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">コンテンツタイプ</label>
                    <div className="space-y-1">
                      {['document', 'task', 'incident', 'user', 'code'].map((type) => (
                        <label key={type} className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            checked={filters.types.includes(type)}
                            onChange={() => toggleFilter('types', type)}
                            className="rounded border-gray-300"
                          />
                          <span className="text-sm capitalize">{type}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">ソース</label>
                    <div className="space-y-1">
                      {['Knowledge Base', 'Task System', 'Incident Reports', 'Code Repository'].map((source) => (
                        <label key={source} className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            checked={filters.sources.includes(source)}
                            onChange={() => toggleFilter('sources', source)}
                            className="rounded border-gray-300"
                          />
                          <span className="text-sm">{source}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">更新日</label>
                    <select
                      value={filters.dateRange}
                      onChange={(e) => setFilters(prev => ({ ...prev, dateRange: e.target.value as any }))}
                      className="w-full border border-gray-300 rounded px-3 py-2"
                    >
                      <option value="all">すべて</option>
                      <option value="24h">24時間以内</option>
                      <option value="7d">7日以内</option>
                      <option value="30d">30日以内</option>
                      <option value="90d">90日以内</option>
                    </select>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </Card>

      {/* Search Results */}
      {results.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              検索結果 ({results.length.toLocaleString()}件)
            </h2>
            <div className="flex items-center space-x-2 text-sm text-gray-500">
              <TrendingUp className="w-4 h-4" />
              <span>検索時間: 0.234秒</span>
            </div>
          </div>

          <div className="space-y-4">
            {results.map((result, index) => (
              <motion.div
                key={result.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <Card className="p-6 hover:shadow-lg transition-all duration-200 cursor-pointer">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      <span className="text-2xl">{getTypeIcon(result.type)}</span>
                      <div>
                        <h3 className="font-semibold text-gray-900 text-lg">
                          {highlightText(result.title, result.highlights.find(h => h.field === 'title')?.matches || [])}
                        </h3>
                        <div className="flex items-center space-x-2 mt-1">
                          <Badge className={cn('text-xs', getTypeColor(result.type))}>
                            {result.type}
                          </Badge>
                          <span className="text-sm text-gray-500">{result.source}</span>
                          <span className="text-sm text-gray-400">•</span>
                          <span className="text-sm text-gray-500">
                            {new Date(result.lastModified).toLocaleDateString('ja-JP')}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-2">
                      <Badge variant="outline" className="text-xs">
                        {Math.round(result.relevanceScore * 100)}% 関連
                      </Badge>
                      <Button variant="ghost" size="sm">
                        <Star className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>

                  <p className="text-gray-600 mb-4">
                    {highlightText(
                      result.content.slice(0, 200) + (result.content.length > 200 ? '...' : ''),
                      result.highlights.find(h => h.field === 'content')?.matches || []
                    )}
                  </p>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      {result.author && (
                        <div className="flex items-center space-x-2">
                          <Avatar
                            src={result.author.avatar}
                            alt={result.author.name}
                            size="sm"
                            fallback={result.author.name.slice(0, 2)}
                          />
                          <span className="text-sm text-gray-600">{result.author.name}</span>
                        </div>
                      )}

                      {result.tags.length > 0 && (
                        <div className="flex items-center space-x-1">
                          <Tag className="w-4 h-4 text-gray-400" />
                          <div className="flex space-x-1">
                            {result.tags.slice(0, 3).map((tag) => (
                              <span
                                key={tag}
                                className="px-2 py-1 bg-lime-50 text-lime-700 text-xs rounded"
                              >
                                #{tag}
                              </span>
                            ))}
                            {result.tags.length > 3 && (
                              <span className="text-xs text-gray-500">
                                +{result.tags.length - 3}
                              </span>
                            )}
                          </div>
                        </div>
                      )}
                    </div>

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => window.open(result.url, '_blank')}
                    >
                      <FileText className="w-4 h-4 mr-1" />
                      開く
                    </Button>
                  </div>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* No Results */}
      {query && results.length === 0 && !isLoading && (
        <Card className="p-12 text-center">
          <Search className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">検索結果が見つかりません</h3>
          <p className="text-gray-500 mb-4">
            「{query}」に一致する結果がありませんでした。
          </p>
          <div className="space-y-2 text-sm text-gray-600">
            <p>検索のヒント:</p>
            <ul className="list-disc list-inside space-y-1">
              <li>キーワードを短くしてみてください</li>
              <li>別の表現を試してみてください</li>
              <li>フィルターを調整してみてください</li>
            </ul>
          </div>
        </Card>
      )}
    </div>
  )
}
