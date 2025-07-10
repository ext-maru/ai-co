'use client'

import { useState } from 'react'
import Link from 'next/link'
import { ArrowLeftIcon, ChartBarIcon, ChartPieIcon, SparklesIcon } from '@heroicons/react/24/outline'
import useSWR from 'swr'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer
} from 'recharts'

const fetcher = (url: string) => fetch(url).then(res => res.json())

const COLORS = ['#8B5CF6', '#EC4899', '#10B981', '#F59E0B', '#3B82F6', '#EF4444']

export default function StatsPage() {
  const { data: statsData, error, isLoading } = useSWR('/api/projects/stats', fetcher)

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="loading-spinner mx-auto mb-4"></div>
          <p className="text-gray-500">統計情報を読み込み中...</p>
        </div>
      </div>
    )
  }

  if (error || !statsData) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">統計情報の読み込みに失敗しました</p>
          <Link href="/" className="btn-primary">
            ホームに戻る
          </Link>
        </div>
      </div>
    )
  }

  // データ整形
  const typeData = Object.entries(statsData.projects_by_type || {}).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value
  }))

  const statusData = Object.entries(statsData.projects_by_status || {}).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value
  }))

  const techStackData = Object.entries(statsData.tech_stack_usage || {})
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([name, value]) => ({
      name,
      count: value
    }))

  return (
    <div className="min-h-screen bg-elder-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* ヘッダー */}
        <div className="mb-8">
          <Link href="/" className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-4">
            <ArrowLeftIcon className="h-5 w-5 mr-2" />
            ホームに戻る
          </Link>

          <h1 className="text-3xl font-bold text-gray-900 flex items-center">
            <ChartBarIcon className="h-8 w-8 mr-3 text-elder-600" />
            プロジェクト統計情報
          </h1>
        </div>

        {/* サマリーカード */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">総プロジェクト数</p>
                <p className="text-3xl font-bold text-gray-900">{statsData.total_projects}</p>
              </div>
              <SparklesIcon className="h-12 w-12 text-elder-400" />
            </div>
          </div>

          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">アクティブ</p>
                <p className="text-3xl font-bold text-green-600">{statsData.active_projects || 0}</p>
              </div>
              <div className="h-12 w-12 rounded-full bg-green-100 flex items-center justify-center">
                <div className="h-6 w-6 rounded-full bg-green-500"></div>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">完了済み</p>
                <p className="text-3xl font-bold text-blue-600">{statsData.completed_projects || 0}</p>
              </div>
              <div className="h-12 w-12 rounded-full bg-blue-100 flex items-center justify-center">
                <div className="h-6 w-6 rounded-full bg-blue-500"></div>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">計画中</p>
                <p className="text-3xl font-bold text-yellow-600">{statsData.planning_projects || 0}</p>
              </div>
              <div className="h-12 w-12 rounded-full bg-yellow-100 flex items-center justify-center">
                <div className="h-6 w-6 rounded-full bg-yellow-500"></div>
              </div>
            </div>
          </div>
        </div>

        {/* チャートセクション */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* プロジェクトタイプ分布 */}
          <div className="card">
            <h2 className="text-xl font-semibold mb-4">プロジェクトタイプ分布</h2>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={typeData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {typeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* ステータス別分布 */}
          <div className="card">
            <h2 className="text-xl font-semibold mb-4">ステータス別分布</h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={statusData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#8B5CF6" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* 技術スタック使用状況 */}
          <div className="card lg:col-span-2">
            <h2 className="text-xl font-semibold mb-4">技術スタック使用状況 (Top 10)</h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={techStackData} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#10B981" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* 最近のプロジェクト */}
        {statsData.recent_projects && statsData.recent_projects.length > 0 && (
          <div className="card mt-8">
            <h2 className="text-xl font-semibold mb-4">最近更新されたプロジェクト</h2>
            <div className="space-y-4">
              {statsData.recent_projects.map((project: any) => (
                <div key={project.project_id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <Link href={`/projects/${project.project_id}`} className="text-lg font-medium text-blue-600 hover:text-blue-800">
                      {project.name}
                    </Link>
                    <p className="text-gray-500 text-sm mt-1">
                      {project.project_type} • {project.status}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-500">
                      {new Date(project.updated_at).toLocaleDateString('ja-JP')}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
