'use client'

import React, { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import { BarChart3, PieChart, Network, TrendingUp, Filter, Download } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'

interface SearchAnalytics {
  totalResults: number
  searchTime: number
  categories: {
    name: string
    count: number
    percentage: number
    color: string
  }[]
  relevanceDistribution: {
    range: string
    count: number
    percentage: number
  }[]
  temporalData: {
    period: string
    searchCount: number
    avgRelevance: number
  }[]
  topQueries: {
    query: string
    count: number
    avgRelevance: number
  }[]
  sourceDistribution: {
    source: string
    count: number
    avgResponseTime: number
  }[]
}

interface NetworkNode {
  id: string
  label: string
  type: 'query' | 'result' | 'concept'
  size: number
  color: string
  x?: number
  y?: number
}

interface NetworkLink {
  source: string
  target: string
  strength: number
  type: 'semantic' | 'categorical' | 'temporal'
}

interface SearchVisualizationProps {
  analytics: SearchAnalytics
  networkData?: {
    nodes: NetworkNode[]
    links: NetworkLink[]
  }
  className?: string
}

export function SearchVisualization({
  analytics,
  networkData,
  className
}: SearchVisualizationProps) {
  const [activeChart, setActiveChart] = useState<'overview' | 'trends' | 'network' | 'heatmap'>('overview')
  const canvasRef = useRef<HTMLCanvasElement>(null)

  // Network visualization
  useEffect(() => {
    if (activeChart === 'network' && networkData && canvasRef.current) {
      const canvas = canvasRef.current
      const ctx = canvas.getContext('2d')
      if (!ctx) return

      const width = canvas.width
      const height = canvas.height
      
      // Clear canvas
      ctx.clearRect(0, 0, width, height)
      
      // Draw links
      networkData.links.forEach(link => {
        const sourceNode = networkData.nodes.find(n => n.id === link.source)
        const targetNode = networkData.nodes.find(n => n.id === link.target)
        
        if (sourceNode && targetNode) {
          ctx.beginPath()
          ctx.moveTo(sourceNode.x || 0, sourceNode.y || 0)
          ctx.lineTo(targetNode.x || 0, targetNode.y || 0)
          ctx.strokeStyle = `rgba(156, 163, 175, ${link.strength})`
          ctx.lineWidth = link.strength * 3
          ctx.stroke()
        }
      })
      
      // Draw nodes
      networkData.nodes.forEach(node => {
        ctx.beginPath()
        ctx.arc(node.x || 0, node.y || 0, node.size, 0, Math.PI * 2)
        ctx.fillStyle = node.color
        ctx.fill()
        ctx.strokeStyle = '#fff'
        ctx.lineWidth = 2
        ctx.stroke()
        
        // Label
        ctx.fillStyle = '#1f2937'
        ctx.font = '12px sans-serif'
        ctx.textAlign = 'center'
        ctx.fillText(node.label, node.x || 0, (node.y || 0) + node.size + 15)
      })
    }
  }, [activeChart, networkData])

  const renderBarChart = (data: { name: string; count: number; color: string }[]) => {
    const maxCount = Math.max(...data.map(d => d.count))
    
    return (
      <div className="space-y-3">
        {data.map((item, index) => (
          <motion.div
            key={item.name}
            initial={{ width: 0 }}
            animate={{ width: '100%' }}
            transition={{ delay: index * 0.1, duration: 0.5 }}
            className="relative"
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm font-medium text-gray-700">{item.name}</span>
              <span className="text-sm text-gray-500">{item.count}</span>
            </div>
            <div className="relative h-4 bg-gray-200 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${(item.count / maxCount) * 100}%` }}
                transition={{ delay: index * 0.1 + 0.2, duration: 0.5 }}
                className="h-full rounded-full"
                style={{ backgroundColor: item.color }}
              />
            </div>
          </motion.div>
        ))}
      </div>
    )
  }

  const renderPieChart = (data: { name: string; percentage: number; color: string }[]) => {
    let currentAngle = 0
    const radius = 80
    const centerX = 100
    const centerY = 100

    return (
      <div className="flex items-center space-x-6">
        <svg width="200" height="200" className="flex-shrink-0">
          {data.map((slice, index) => {
            const sliceAngle = (slice.percentage / 100) * 360
            const startAngle = currentAngle
            const endAngle = currentAngle + sliceAngle
            
            const x1 = centerX + radius * Math.cos((startAngle * Math.PI) / 180)
            const y1 = centerY + radius * Math.sin((startAngle * Math.PI) / 180)
            const x2 = centerX + radius * Math.cos((endAngle * Math.PI) / 180)
            const y2 = centerY + radius * Math.sin((endAngle * Math.PI) / 180)
            
            const largeArcFlag = sliceAngle > 180 ? 1 : 0
            
            const pathData = [
              `M ${centerX} ${centerY}`,
              `L ${x1} ${y1}`,
              `A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2}`,
              'Z'
            ].join(' ')
            
            currentAngle += sliceAngle
            
            return (
              <motion.path
                key={index}
                d={pathData}
                fill={slice.color}
                stroke="white"
                strokeWidth="2"
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.1, duration: 0.5 }}
              />
            )
          })}
        </svg>
        
        <div className="space-y-2">
          {data.map((item, index) => (
            <motion.div
              key={item.name}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="flex items-center space-x-2"
            >
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: item.color }}
              />
              <span className="text-sm text-gray-700">{item.name}</span>
              <span className="text-sm font-medium text-gray-900">
                {item.percentage.toFixed(1)}%
              </span>
            </motion.div>
          ))}
        </div>
      </div>
    )
  }

  const renderLineChart = (data: { period: string; searchCount: number; avgRelevance: number }[]) => {
    const maxCount = Math.max(...data.map(d => d.searchCount))
    const maxRelevance = Math.max(...data.map(d => d.avgRelevance))
    
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">検索回数推移</h4>
            <div className="h-32 relative">
              <svg width="100%" height="100%" viewBox="0 0 300 120">
                <polyline
                  points={data.map((d, i) => 
                    `${(i / (data.length - 1)) * 280 + 10},${120 - ((d.searchCount / maxCount) * 100 + 10)}`
                  ).join(' ')}
                  fill="none"
                  stroke="#10b981"
                  strokeWidth="2"
                />
                {data.map((d, i) => (
                  <circle
                    key={i}
                    cx={(i / (data.length - 1)) * 280 + 10}
                    cy={120 - ((d.searchCount / maxCount) * 100 + 10)}
                    r="3"
                    fill="#10b981"
                  />
                ))}
              </svg>
            </div>
          </div>
          
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">平均関連度推移</h4>
            <div className="h-32 relative">
              <svg width="100%" height="100%" viewBox="0 0 300 120">
                <polyline
                  points={data.map((d, i) => 
                    `${(i / (data.length - 1)) * 280 + 10},${120 - ((d.avgRelevance / maxRelevance) * 100 + 10)}`
                  ).join(' ')}
                  fill="none"
                  stroke="#3b82f6"
                  strokeWidth="2"
                />
                {data.map((d, i) => (
                  <circle
                    key={i}
                    cx={(i / (data.length - 1)) * 280 + 10}
                    cy={120 - ((d.avgRelevance / maxRelevance) * 100 + 10)}
                    r="3"
                    fill="#3b82f6"
                  />
                ))}
              </svg>
            </div>
          </div>
        </div>
        
        <div className="flex justify-between text-xs text-gray-500">
          {data.map(d => d.period)}
        </div>
      </div>
    )
  }

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">検索分析ダッシュボード</h2>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            エクスポート
          </Button>
          <Button variant="outline" size="sm">
            <Filter className="w-4 h-4 mr-2" />
            フィルター
          </Button>
        </div>
      </div>

      {/* Chart Type Selector */}
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg w-fit">
        {[
          { id: 'overview', label: '概要', icon: BarChart3 },
          { id: 'trends', label: 'トレンド', icon: TrendingUp },
          { id: 'network', label: 'ネットワーク', icon: Network },
          { id: 'heatmap', label: '分布', icon: PieChart }
        ].map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveChart(id as any)}
            className={cn(
              'px-4 py-2 rounded-md flex items-center space-x-2 transition-all duration-200',
              activeChart === id
                ? 'bg-white text-lime-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            )}
          >
            <Icon className="w-4 h-4" />
            <span className="text-sm font-medium">{label}</span>
          </button>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {activeChart === 'overview' && (
          <>
            {/* Summary Stats */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">検索統計</h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">総結果数</span>
                  <span className="text-2xl font-bold text-gray-900">
                    {analytics.totalResults.toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">検索時間</span>
                  <span className="text-lg font-semibold text-lime-600">
                    {analytics.searchTime.toFixed(3)}s
                  </span>
                </div>
                <div className="pt-2 border-t">
                  <div className="text-sm text-gray-600 mb-2">カテゴリ別結果数</div>
                  {renderBarChart(analytics.categories)}
                </div>
              </div>
            </Card>

            {/* Category Distribution */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">カテゴリ分布</h3>
              {renderPieChart(analytics.categories)}
            </Card>

            {/* Relevance Distribution */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">関連度分布</h3>
              <div className="space-y-3">
                {analytics.relevanceDistribution.map((range, index) => (
                  <div key={range.range}>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm text-gray-600">{range.range}</span>
                      <span className="text-sm font-medium">{range.count}</span>
                    </div>
                    <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${range.percentage}%` }}
                        transition={{ delay: index * 0.1, duration: 0.5 }}
                        className="h-full bg-gradient-to-r from-lime-400 to-lime-600 rounded-full"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </>
        )}

        {activeChart === 'trends' && (
          <>
            <div className="lg:col-span-2">
              <Card className="p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">検索トレンド</h3>
                {renderLineChart(analytics.temporalData)}
              </Card>
            </div>

            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">人気検索クエリ</h3>
              <div className="space-y-3">
                {analytics.topQueries.map((query, index) => (
                  <motion.div
                    key={query.query}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="p-3 bg-gray-50 rounded-lg"
                  >
                    <div className="flex justify-between items-start mb-1">
                      <span className="font-medium text-gray-900 text-sm">
                        {query.query}
                      </span>
                      <Badge variant="secondary" className="text-xs">
                        {query.count}回
                      </Badge>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs text-gray-500">平均関連度:</span>
                      <div className="flex-1 h-1 bg-gray-200 rounded-full">
                        <div
                          className="h-full bg-lime-500 rounded-full"
                          style={{ width: `${query.avgRelevance * 100}%` }}
                        />
                      </div>
                      <span className="text-xs font-medium text-gray-700">
                        {Math.round(query.avgRelevance * 100)}%
                      </span>
                    </div>
                  </motion.div>
                ))}
              </div>
            </Card>
          </>
        )}

        {activeChart === 'network' && networkData && (
          <div className="lg:col-span-3">
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">検索ネットワーク</h3>
              <div className="relative">
                <canvas
                  ref={canvasRef}
                  width={800}
                  height={400}
                  className="w-full border border-gray-200 rounded-lg"
                />
                <div className="absolute top-4 right-4 bg-white bg-opacity-90 rounded-lg p-3 text-xs">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 bg-lime-500 rounded-full" />
                      <span>クエリノード</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 bg-blue-500 rounded-full" />
                      <span>結果ノード</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 bg-purple-500 rounded-full" />
                      <span>概念ノード</span>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        )}

        {activeChart === 'heatmap' && (
          <div className="lg:col-span-3">
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">ソース別パフォーマンス</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {analytics.sourceDistribution.map((source, index) => (
                  <motion.div
                    key={source.source}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: index * 0.1 }}
                    className="p-4 border border-gray-200 rounded-lg text-center"
                  >
                    <h4 className="font-medium text-gray-900 mb-2">{source.source}</h4>
                    <div className="space-y-2">
                      <div>
                        <div className="text-2xl font-bold text-lime-600">{source.count}</div>
                        <div className="text-xs text-gray-500">結果数</div>
                      </div>
                      <div>
                        <div className="text-lg font-semibold text-blue-600">
                          {source.avgResponseTime}ms
                        </div>
                        <div className="text-xs text-gray-500">平均応答時間</div>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}