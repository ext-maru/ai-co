'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { 
  ArrowLeftIcon,
  FolderIcon,
  DocumentTextIcon,
  CodeBracketIcon,
  CalendarIcon,
  UserGroupIcon,
  ChartBarIcon,
  SparklesIcon,
  ClipboardDocumentIcon,
} from '@heroicons/react/24/outline'
import { motion } from 'framer-motion'
import useSWR from 'swr'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism'

// API クライアント
const fetcher = (url: string) => fetch(url).then(res => res.json())

// 型定義
interface ProjectDetail {
  project_id: string
  name: string
  path: string
  project_type: string
  status: string
  tech_stack: string[]
  description: string
  created_at: string
  updated_at: string
  code_structure?: {
    total_lines: number
    total_files: number
    classes: string[]
    functions: string[]
    complexity_score: number
    languages: Record<string, number>
  }
  git_metrics?: {
    total_commits: number
    contributors: string[]
    last_commit: string
    creation_date: string
    active_branches: number
    commit_frequency: number
  }
  dependencies: Array<{
    name: string
    version?: string
    type: string
  }>
  documentation?: {
    overview: string
    architecture: string
    setup_guide: string
    api_reference: string
    usage_examples: string
    diagrams: Record<string, string>
    quality_score: number
  }
}

interface SimilarProject {
  project_id: string
  name: string
  description: string
  similarity: number
  tech_stack: string[]
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

// Mermaidコンポーネント
const MermaidDiagram = ({ code }: { code: string }) => {
  const [diagramSvg, setDiagramSvg] = useState<string>('')
  
  useEffect(() => {
    const renderDiagram = async () => {
      try {
        const mermaid = (await import('mermaid')).default
        mermaid.initialize({ 
          startOnLoad: false,
          theme: 'default',
          themeVariables: {
            primaryColor: '#0ea5e9',
            primaryTextColor: '#1f2937',
            primaryBorderColor: '#0284c7',
            lineColor: '#6b7280',
            secondaryColor: '#f3f4f6',
            tertiaryColor: '#e5e7eb'
          }
        })
        
        const { svg } = await mermaid.render('mermaid-diagram', code)
        setDiagramSvg(svg)
      } catch (error) {
        console.error('Mermaid rendering error:', error)
        setDiagramSvg('<p class="text-red-600">図表の描画に失敗しました</p>')
      }
    }
    
    if (code) {
      renderDiagram()
    }
  }, [code])
  
  return (
    <div 
      className="mermaid-container"
      dangerouslySetInnerHTML={{ __html: diagramSvg }}
    />
  )
}

// Markdownコンポーネント
const MarkdownContent = ({ content }: { content: string }) => {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      className="prose prose-sm max-w-none"
      components={{
        code({ node, inline, className, children, ...props }) {
          const match = /language-(\w+)/.exec(className || '')
          return !inline && match ? (
            <SyntaxHighlighter
              style={tomorrow}
              language={match[1]}
              PreTag="div"
              {...props}
            >
              {String(children).replace(/\n$/, '')}
            </SyntaxHighlighter>
          ) : (
            <code className={className} {...props}>
              {children}
            </code>
          )
        }
      }}
    >
      {content}
    </ReactMarkdown>
  )
}

// タブコンポーネント
const Tabs = ({ tabs, activeTab, onTabChange }: {
  tabs: Array<{ id: string, label: string, icon?: React.ReactNode }>
  activeTab: string
  onTabChange: (tab: string) => void
}) => {
  return (
    <div className="border-b border-gray-200">
      <nav className="-mb-px flex space-x-8">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`group inline-flex items-center py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === tab.id
                ? 'border-elder-500 text-elder-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            {tab.icon && <span className="mr-2">{tab.icon}</span>}
            {tab.label}
          </button>
        ))}
      </nav>
    </div>
  )
}

// プロジェクト詳細ページ
export default function ProjectDetailPage() {
  const params = useParams()
  const projectId = params.id as string
  
  const [activeTab, setActiveTab] = useState('overview')
  const [generatingDocs, setGeneratingDocs] = useState(false)
  
  // データ取得
  const { data: project, error: projectError, mutate } = useSWR<ProjectDetail>(
    projectId ? `/api/projects/${projectId}` : null,
    fetcher
  )
  
  const { data: similarProjects } = useSWR<SimilarProject[]>(
    projectId ? `/api/projects/${projectId}/similar` : null,
    fetcher
  )
  
  // 資料生成
  const generateDocumentation = async () => {
    setGeneratingDocs(true)
    try {
      const response = await fetch(`/api/projects/${projectId}/documentation`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_id: projectId, include_similar: true })
      })
      
      if (response.ok) {
        // データ再取得
        mutate()
      }
    } catch (error) {
      console.error('Documentation generation error:', error)
    } finally {
      setGeneratingDocs(false)
    }
  }
  
  // ローディング状態
  if (!project && !projectError) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="loading-spinner mx-auto mb-4"></div>
          <p className="text-gray-500">プロジェクト情報を読み込み中...</p>
        </div>
      </div>
    )
  }
  
  // エラー状態
  if (projectError) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">プロジェクトが見つかりませんでした</p>
          <Link href="/" className="btn-primary">
            ホームに戻る
          </Link>
        </div>
      </div>
    )
  }
  
  if (!project) return null
  
  // タブ定義
  const tabs = [
    { id: 'overview', label: '概要', icon: <FolderIcon className="h-4 w-4" /> },
    { id: 'code', label: 'コード構造', icon: <CodeBracketIcon className="h-4 w-4" /> },
    { id: 'dependencies', label: '依存関係', icon: <ChartBarIcon className="h-4 w-4" /> },
    ...(project.documentation ? [
      { id: 'documentation', label: '自動生成資料', icon: <DocumentTextIcon className="h-4 w-4" /> }
    ] : [])
  ]
  
  return (
    <div className="min-h-screen bg-gray-50">
      {/* ヘッダー */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link 
                href="/" 
                className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
              >
                <ArrowLeftIcon className="h-5 w-5" />
              </Link>
              
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  {project.name}
                </h1>
                <div className="flex items-center space-x-3 mt-2">
                  <span className={`badge ${getStatusColor(project.status)}`}>
                    {project.status}
                  </span>
                  <span className="text-sm text-gray-500 capitalize">
                    {project.project_type}
                  </span>
                  <span className="text-sm text-gray-500">
                    {project.path}
                  </span>
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              {!project.documentation && (
                <button
                  onClick={generateDocumentation}
                  disabled={generatingDocs}
                  className="btn-primary"
                >
                  {generatingDocs ? (
                    <>
                      <div className="loading-spinner mr-2"></div>
                      生成中...
                    </>
                  ) : (
                    <>
                      <SparklesIcon className="h-4 w-4 mr-2" />
                      資料生成
                    </>
                  )}
                </button>
              )}
              
              <button className="btn-secondary">
                <ClipboardDocumentIcon className="h-4 w-4 mr-2" />
                エクスポート
              </button>
            </div>
          </div>
        </div>
      </header>
      
      {/* メインコンテンツ */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* メインコンテンツ */}
          <div className="lg:col-span-3">
            <div className="card">
              <Tabs tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} />
              
              <div className="mt-6">
                {/* 概要タブ */}
                {activeTab === 'overview' && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="space-y-6"
                  >
                    {/* 説明 */}
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-3">説明</h3>
                      <p className="text-gray-700 leading-relaxed">
                        {project.description || 'プロジェクトの説明がありません'}
                      </p>
                    </div>
                    
                    {/* 技術スタック */}
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-3">技術スタック</h3>
                      <div className="flex flex-wrap gap-2">
                        {project.tech_stack.map((tech, index) => (
                          <span key={index} className="badge badge-primary">
                            {tech}
                          </span>
                        ))}
                      </div>
                    </div>
                    
                    {/* Git情報 */}
                    {project.git_metrics && (
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-3">Git統計</h3>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          <div className="text-center">
                            <div className="text-2xl font-bold text-gray-900">
                              {project.git_metrics.total_commits}
                            </div>
                            <div className="text-sm text-gray-500">コミット</div>
                          </div>
                          <div className="text-center">
                            <div className="text-2xl font-bold text-gray-900">
                              {project.git_metrics.contributors.length}
                            </div>
                            <div className="text-sm text-gray-500">貢献者</div>
                          </div>
                          <div className="text-center">
                            <div className="text-2xl font-bold text-gray-900">
                              {project.git_metrics.active_branches}
                            </div>
                            <div className="text-sm text-gray-500">ブランチ</div>
                          </div>
                          <div className="text-center">
                            <div className="text-2xl font-bold text-gray-900">
                              {project.git_metrics.commit_frequency.toFixed(1)}
                            </div>
                            <div className="text-sm text-gray-500">週間頻度</div>
                          </div>
                        </div>
                      </div>
                    )}
                  </motion.div>
                )}
                
                {/* コード構造タブ */}
                {activeTab === 'code' && project.code_structure && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="space-y-6"
                  >
                    {/* コード統計 */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-gray-900">
                          {project.code_structure.total_lines.toLocaleString()}
                        </div>
                        <div className="text-sm text-gray-500">総行数</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-gray-900">
                          {project.code_structure.total_files}
                        </div>
                        <div className="text-sm text-gray-500">ファイル数</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-gray-900">
                          {project.code_structure.classes.length}
                        </div>
                        <div className="text-sm text-gray-500">クラス数</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-gray-900">
                          {project.code_structure.functions.length}
                        </div>
                        <div className="text-sm text-gray-500">関数数</div>
                      </div>
                    </div>
                    
                    {/* 主要クラス */}
                    {project.code_structure.classes.length > 0 && (
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-3">主要クラス</h3>
                        <div className="bg-gray-50 rounded-lg p-4">
                          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                            {project.code_structure.classes.slice(0, 12).map((cls, index) => (
                              <code key={index} className="text-sm text-gray-700 bg-white px-2 py-1 rounded">
                                {cls}
                              </code>
                            ))}
                          </div>
                          {project.code_structure.classes.length > 12 && (
                            <p className="text-sm text-gray-500 mt-2">
                              他 {project.code_structure.classes.length - 12} クラス
                            </p>
                          )}
                        </div>
                      </div>
                    )}
                  </motion.div>
                )}
                
                {/* 依存関係タブ */}
                {activeTab === 'dependencies' && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="space-y-6"
                  >
                    {project.dependencies.length > 0 ? (
                      <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                          <thead className="bg-gray-50">
                            <tr>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                パッケージ
                              </th>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                バージョン
                              </th>
                              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                タイプ
                              </th>
                            </tr>
                          </thead>
                          <tbody className="bg-white divide-y divide-gray-200">
                            {project.dependencies.map((dep, index) => (
                              <tr key={index}>
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                  {dep.name}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                  {dep.version || 'N/A'}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                  <span className={`badge ${dep.type === 'runtime' ? 'badge-primary' : 'badge-gray'}`}>
                                    {dep.type}
                                  </span>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <div className="text-center py-8">
                        <p className="text-gray-500">依存関係情報がありません</p>
                      </div>
                    )}
                  </motion.div>
                )}
                
                {/* 自動生成資料タブ */}
                {activeTab === 'documentation' && project.documentation && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="space-y-8"
                  >
                    {/* 品質スコア */}
                    <div className="bg-elder-50 rounded-lg p-4 border border-elder-200">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-elder-800">
                          資料品質スコア
                        </span>
                        <span className="text-lg font-bold text-elder-900">
                          {(project.documentation.quality_score * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                    
                    {/* 概要 */}
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">概要</h3>
                      <MarkdownContent content={project.documentation.overview} />
                    </div>
                    
                    {/* アーキテクチャ */}
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">アーキテクチャ</h3>
                      <MarkdownContent content={project.documentation.architecture} />
                    </div>
                    
                    {/* 図表 */}
                    {Object.keys(project.documentation.diagrams).length > 0 && (
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">図表</h3>
                        <div className="space-y-6">
                          {Object.entries(project.documentation.diagrams).map(([type, code]) => (
                            <div key={type}>
                              <h4 className="text-md font-medium text-gray-700 mb-2 capitalize">
                                {type}
                              </h4>
                              <MermaidDiagram code={code} />
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {/* セットアップガイド */}
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">セットアップガイド</h3>
                      <MarkdownContent content={project.documentation.setup_guide} />
                    </div>
                  </motion.div>
                )}
              </div>
            </div>
          </div>
          
          {/* サイドバー */}
          <div className="lg:col-span-1 space-y-6">
            {/* プロジェクト情報 */}
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">プロジェクト情報</h3>
              
              <div className="space-y-3">
                <div className="flex items-center text-sm">
                  <CalendarIcon className="h-4 w-4 text-gray-400 mr-2" />
                  <span className="text-gray-500">作成日:</span>
                  <span className="ml-2 text-gray-900">
                    {new Date(project.created_at).toLocaleDateString('ja-JP')}
                  </span>
                </div>
                
                <div className="flex items-center text-sm">
                  <CalendarIcon className="h-4 w-4 text-gray-400 mr-2" />
                  <span className="text-gray-500">更新日:</span>
                  <span className="ml-2 text-gray-900">
                    {new Date(project.updated_at).toLocaleDateString('ja-JP')}
                  </span>
                </div>
                
                {project.git_metrics && (
                  <div className="flex items-center text-sm">
                    <UserGroupIcon className="h-4 w-4 text-gray-400 mr-2" />
                    <span className="text-gray-500">貢献者:</span>
                    <span className="ml-2 text-gray-900">
                      {project.git_metrics.contributors.length}人
                    </span>
                  </div>
                )}
              </div>
            </div>
            
            {/* 類似プロジェクト */}
            {similarProjects && similarProjects.length > 0 && (
              <div className="card">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">類似プロジェクト</h3>
                
                <div className="space-y-3">
                  {similarProjects.slice(0, 5).map((similar) => (
                    <Link
                      key={similar.project_id}
                      href={`/projects/${similar.project_id}`}
                      className="block p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium text-gray-900 text-sm">
                          {similar.name}
                        </span>
                        <span className="text-xs text-gray-500">
                          {(similar.similarity * 100).toFixed(0)}%
                        </span>
                      </div>
                      <p className="text-xs text-gray-600 text-truncate-2">
                        {similar.description}
                      </p>
                    </Link>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}