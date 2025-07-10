'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { 
  MagnifyingGlassIcon, 
  FolderIcon, 
  DocumentTextIcon,
  ChartBarIcon,
  ClockIcon,
  CodeBracketIcon,
  CpuChipIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline'
import { motion } from 'framer-motion'
import useSWR from 'swr'

// API クライアント - デバッグログ付き
const fetcher = async (url: string) => {
  console.log('🔄 Fetching:', url)
  try {
    const res = await fetch(url)
    console.log('📡 Response status:', res.status, res.statusText)
    
    if (!res.ok) {
      console.error('❌ Response not OK:', res.status, res.statusText)
      throw new Error(`HTTP ${res.status}: ${res.statusText}`)
    }
    
    const data = await res.json()
    console.log('✅ Data received:', data)
    return data
  } catch (error) {
    console.error('💥 Fetch error:', error)
    throw error
  }
}

// 型定義
interface ProjectSummary {
  project_id: string
  name: string
  project_type: string
  status: string
  tech_stack: string[]
  description: string
  updated_at: string
}

interface Stats {
  total_projects: number
  by_type: Record<string, number>
  by_status: Record<string, number>
  by_tech_stack: Record<string, number>
  most_used_tech?: [string, number]
}

// プロジェクトタイプアイコン
const getProjectTypeIcon = (type: string) => {
  const iconClass = "h-6 w-6"
  switch (type) {
    case 'library': return <FolderIcon className={iconClass} />
    case 'application': return <CpuChipIcon className={iconClass} />
    case 'script': return <CodeBracketIcon className={iconClass} />
    case 'api': return <DocumentTextIcon className={iconClass} />
    default: return <FolderIcon className={iconClass} />
  }
}

// プロジェクトステータス色
const getStatusColor = (status: string) => {
  switch (status) {
    case 'active': return 'badge-success'
    case 'completed': return 'badge-primary'
    case 'deprecated': return 'badge-danger'
    case 'experimental': return 'badge-warning'
    default: return 'badge-gray'
  }
}

// プロジェクトカードコンポーネント
const ProjectCard = ({ project }: { project: ProjectSummary }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="project-card"
    >
      <Link href={`/projects/${project.project_id}`}>
        <div className="flex items-start space-x-4">
          <div className="flex-shrink-0">
            <div className="p-2 bg-elder-100 rounded-lg">
              {getProjectTypeIcon(project.project_type)}
            </div>
          </div>
          
          <div className="flex-1 min-w-0">
            <h3 className="project-title text-lg font-semibold text-gray-900 truncate transition-colors duration-200">
              {project.name}
            </h3>
            
            <div className="mt-2 flex items-center space-x-2">
              <span className={`badge ${getStatusColor(project.status)}`}>
                {project.status}
              </span>
              <span className="text-sm text-gray-500 capitalize">
                {project.project_type}
              </span>
            </div>
            
            <p className="mt-2 text-sm text-gray-600 text-truncate-2">
              {project.description}
            </p>
            
            <div className="mt-3 flex items-center justify-between">
              <div className="flex flex-wrap gap-1">
                {project.tech_stack.slice(0, 3).map((tech, index) => (
                  <span key={index} className="badge badge-gray text-xs">
                    {tech}
                  </span>
                ))}
                {project.tech_stack.length > 3 && (
                  <span className="text-xs text-gray-500">
                    +{project.tech_stack.length - 3}
                  </span>
                )}
              </div>
              
              <div className="flex items-center text-xs text-gray-500">
                <ClockIcon className="h-3 w-3 mr-1" />
                {new Date(project.updated_at).toLocaleDateString('ja-JP')}
              </div>
            </div>
          </div>
        </div>
      </Link>
    </motion.div>
  )
}

// 統計カードコンポーネント
const StatsCard = ({ title, value, icon }: { title: string, value: number, icon: React.ReactNode }) => {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      className="stats-card"
    >
      <div className="flex items-center justify-center w-12 h-12 bg-elder-100 rounded-lg mx-auto">
        {icon}
      </div>
      <div className="stats-number">
        {value.toLocaleString()}
      </div>
      <div className="stats-label">
        {title}
      </div>
    </motion.div>
  )
}

// メインページコンポーネント
export default function HomePage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [filteredProjects, setFilteredProjects] = useState<ProjectSummary[]>([])
  
  // データ取得 - デバッグログ付き
  const { data: projects, error: projectsError, isLoading: projectsLoading } = useSWR<ProjectSummary[]>('/api/projects', fetcher)
  const { data: stats, error: statsError, isLoading: statsLoading } = useSWR<Stats>('/api/projects/stats', fetcher)
  
  // デバッグログ
  console.log('🏠 HomePage render:', {
    projects: projects ? `${projects.length} projects` : 'no projects',
    stats: stats ? 'stats loaded' : 'no stats',
    projectsError,
    statsError,
    projectsLoading,
    statsLoading
  })
  
  // 検索フィルタリング
  useEffect(() => {
    if (!projects) return
    
    if (!searchQuery.trim()) {
      setFilteredProjects(projects)
      return
    }
    
    const query = searchQuery.toLowerCase()
    const filtered = projects.filter(project => 
      project.name.toLowerCase().includes(query) ||
      project.description.toLowerCase().includes(query) ||
      project.tech_stack.some(tech => tech.toLowerCase().includes(query))
    )
    
    setFilteredProjects(filtered)
  }, [projects, searchQuery])
  
  // ローディング状態
  if (projectsLoading || statsLoading || !projects || !stats) {
    console.log('🔄 Loading state:', { projectsLoading, statsLoading, projects: !!projects, stats: !!stats })
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="loading-spinner mx-auto mb-4"></div>
          <p className="text-gray-500">
            プロジェクト情報を読み込み中...
            {projectsLoading && ' (projects)'}
            {statsLoading && ' (stats)'}
          </p>
          {(projectsError || statsError) && (
            <div className="mt-4 text-red-600">
              <p>エラー詳細:</p>
              {projectsError && <p>Projects: {projectsError.message}</p>}
              {statsError && <p>Stats: {statsError.message}</p>}
            </div>
          )}
        </div>
      </div>
    )
  }
  
  // エラー状態
  if (projectsError || statsError) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">データの読み込みに失敗しました</p>
          <button 
            onClick={() => window.location.reload()} 
            className="btn-primary"
          >
            再読み込み
          </button>
        </div>
      </div>
    )
  }
  
  return (
    <div className="min-h-screen bg-gray-50">
      {/* ヘッダー */}
      <header className="hero-section text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center"
          >
            <h1 className="text-4xl font-bold sm:text-5xl lg:text-6xl">
              <SparklesIcon className="inline-block h-12 w-12 mr-4 mb-2" />
              Elders Guild
            </h1>
            <p className="text-xl mt-4 text-elder-100">
              Project Portal
            </p>
            <p className="text-lg mt-2 text-elder-200 max-w-2xl mx-auto">
              RAGエルダー推奨による高度なプロジェクト管理・自動資料生成システム
            </p>
          </motion.div>
        </div>
      </header>
      
      {/* メインコンテンツ */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 統計情報 */}
        <section className="mb-12">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <StatsCard
              title="総プロジェクト数"
              value={stats.total_projects}
              icon={<FolderIcon className="h-6 w-6 text-elder-600" />}
            />
            <StatsCard
              title="アクティブ"
              value={stats.by_status.active || 0}
              icon={<ChartBarIcon className="h-6 w-6 text-sage-600" />}
            />
            <StatsCard
              title="ライブラリ"
              value={stats.by_type.library || 0}
              icon={<CodeBracketIcon className="h-6 w-6 text-guild-600" />}
            />
            <StatsCard
              title="最新更新"
              value={projects.length > 0 ? 1 : 0}
              icon={<ClockIcon className="h-6 w-6 text-gray-600" />}
            />
          </div>
        </section>
        
        {/* 検索・フィルタ */}
        <section className="mb-8">
          <div className="card">
            <div className="flex items-center space-x-4">
              <div className="flex-1">
                <div className="relative">
                  <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="text"
                    placeholder="プロジェクト名、説明、技術スタックで検索..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="input-field pl-10"
                  />
                </div>
              </div>
              
              <Link href="/projects/scan" className="btn-primary">
                プロジェクトスキャン
              </Link>
            </div>
            
            {searchQuery && (
              <div className="mt-4 text-sm text-gray-600">
                {filteredProjects.length}件のプロジェクトが見つかりました
              </div>
            )}
          </div>
        </section>
        
        {/* プロジェクト一覧 */}
        <section>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">
              プロジェクト一覧
            </h2>
            
            <Link href="/projects" className="text-elder-600 hover:text-elder-700 font-medium">
              すべて表示 →
            </Link>
          </div>
          
          {filteredProjects.length > 0 ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {filteredProjects.slice(0, 6).map((project) => (
                <ProjectCard key={project.project_id} project={project} />
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <FolderIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">
                {searchQuery ? '検索に一致するプロジェクトが見つかりませんでした' : 'プロジェクトがありません'}
              </p>
            </div>
          )}
        </section>
        
        {/* クイックアクション */}
        <section className="mt-12">
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              クイックアクション
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Link href="/projects/scan" className="btn-secondary justify-center">
                <FolderIcon className="h-5 w-5 mr-2" />
                新規スキャン
              </Link>
              
              <Link href="/stats" className="btn-secondary justify-center">
                <ChartBarIcon className="h-5 w-5 mr-2" />
                統計情報
              </Link>
              
              <Link href="/docs" className="btn-secondary justify-center">
                <DocumentTextIcon className="h-5 w-5 mr-2" />
                ドキュメント
              </Link>
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}