'use client'

import { useMemo } from 'react'
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer
} from 'recharts'
import { motion } from 'framer-motion'

interface DashboardProps {
  projects: any[]
  stats: any
}

// カラーパレット
const COLORS = {
  completed: '#10b981',
  development: '#3b82f6',
  planning: '#f59e0b',
  deleted: '#ef4444',
  high: '#ef4444',
  medium: '#f59e0b',
  low: '#10b981'
}

export default function Dashboard({ projects, stats }: DashboardProps) {
  // プロジェクトのタイムライン分析
  const timelineData = useMemo(() => {
    const monthlyData: Record<string, { month: string; created: number; completed: number }> = {}
    
    projects.forEach(project => {
      const date = new Date(project.updated_at)
      const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
      
      if (!monthlyData[monthKey]) {
        monthlyData[monthKey] = { month: monthKey, created: 0, completed: 0 }
      }
      
      monthlyData[monthKey].created++
      if (project.status === 'completed') {
        monthlyData[monthKey].completed++
      }
    })
    
    return Object.values(monthlyData).sort((a, b) => a.month.localeCompare(b.month))
  }, [projects])
  
  // ステータス別データ（円グラフ用）
  const statusData = useMemo(() => {
    return Object.entries(stats.by_status || {}).map(([status, count]) => ({
      name: status,
      value: count as number
    }))
  }, [stats])
  
  // 技術スタックランキング（上位10件）
  const techStackData = useMemo(() => {
    return Object.entries(stats.by_tech_stack || {})
      .sort(([, a], [, b]) => (b as number) - (a as number))
      .slice(0, 10)
      .map(([tech, count]) => ({
        tech,
        count: count as number
      }))
  }, [stats])
  
  // 優先度別データ
  const priorityData = useMemo(() => {
    return ['high', 'medium', 'low'].map(priority => ({
      priority,
      count: stats.by_status?.[priority] || 0
    }))
  }, [stats])
  
  return (
    <div className="space-y-8">
      {/* メトリクスカード */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card"
        >
          <div className="text-sm font-medium text-gray-500 mb-2">総プロジェクト</div>
          <div className="text-3xl font-bold text-gray-900">{stats.total_projects || 0}</div>
          <div className="text-xs text-gray-500 mt-2">アクティブ率 {Math.round(((stats.by_status?.development || 0) / stats.total_projects) * 100)}%</div>
        </motion.div>
        
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card"
        >
          <div className="text-sm font-medium text-gray-500 mb-2">完了プロジェクト</div>
          <div className="text-3xl font-bold text-green-600">{stats.by_status?.completed || 0}</div>
          <div className="text-xs text-gray-500 mt-2">完了率 {Math.round(((stats.by_status?.completed || 0) / stats.total_projects) * 100)}%</div>
        </motion.div>
        
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="card"
        >
          <div className="text-sm font-medium text-gray-500 mb-2">開発中</div>
          <div className="text-3xl font-bold text-blue-600">{stats.by_status?.development || 0}</div>
          <div className="text-xs text-gray-500 mt-2">アクティブプロジェクト</div>
        </motion.div>
        
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="card"
        >
          <div className="text-sm font-medium text-gray-500 mb-2">使用技術数</div>
          <div className="text-3xl font-bold text-purple-600">{Object.keys(stats.by_tech_stack || {}).length}</div>
          <div className="text-xs text-gray-500 mt-2">最多: {stats.most_used_tech?.[0] || 'N/A'}</div>
        </motion.div>
      </div>
      
      {/* チャートセクション */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* プロジェクトタイムライン */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.4 }}
          className="card"
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4">プロジェクトタイムライン</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={timelineData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Area type="monotone" dataKey="created" stackId="1" stroke="#3b82f6" fill="#3b82f6" name="作成" />
              <Area type="monotone" dataKey="completed" stackId="1" stroke="#10b981" fill="#10b981" name="完了" />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>
        
        {/* ステータス分布 */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.5 }}
          className="card"
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4">ステータス分布</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={statusData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {statusData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[entry.name as keyof typeof COLORS] || '#8884d8'} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </motion.div>
        
        {/* 技術スタックランキング */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.6 }}
          className="card"
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4">人気の技術スタック TOP10</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={techStackData} layout="horizontal" margin={{ left: 80 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="tech" type="category" width={80} />
              <Tooltip />
              <Bar dataKey="count" fill="#6366f1" />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>
        
        {/* プロジェクト進捗分布 */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.7 }}
          className="card"
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4">プロジェクト進捗分布</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart
              data={projects.map((p, i) => ({
                name: p.name.slice(0, 15) + (p.name.length > 15 ? '...' : ''),
                progress: Math.round(p.progress * 100)
              })).slice(0, 10)}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
              <YAxis domain={[0, 100]} />
              <Tooltip formatter={(value) => `${value}%`} />
              <Line type="monotone" dataKey="progress" stroke="#10b981" strokeWidth={2} dot={{ fill: '#10b981' }} />
            </LineChart>
          </ResponsiveContainer>
        </motion.div>
      </div>
      
      {/* アクティビティフィード */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8 }}
        className="card"
      >
        <h3 className="text-lg font-semibold text-gray-900 mb-4">最近のアクティビティ</h3>
        <div className="space-y-3">
          {projects
            .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
            .slice(0, 5)
            .map((project, index) => (
              <div key={project.project_id} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                <div className="flex items-center space-x-3">
                  <div className={`w-2 h-2 rounded-full ${COLORS[project.status as keyof typeof COLORS] ? `bg-[${COLORS[project.status as keyof typeof COLORS]}]` : 'bg-gray-400'}`} />
                  <div>
                    <div className="font-medium text-gray-900">{project.name}</div>
                    <div className="text-sm text-gray-500">
                      {new Date(project.updated_at).toLocaleDateString('ja-JP')} - {project.status}
                    </div>
                  </div>
                </div>
                <div className="text-sm text-gray-500">
                  {Math.round(project.progress * 100)}% 完了
                </div>
              </div>
            ))}
        </div>
      </motion.div>
    </div>
  )
}