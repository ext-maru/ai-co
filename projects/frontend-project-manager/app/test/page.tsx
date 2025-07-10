'use client'

import { useState, useEffect } from 'react'

export default function TestPage() {
  const [projectsData, setProjectsData] = useState(null)
  const [statsData, setStatsData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const testAPIs = async () => {
      console.log('🧪 Test page: Starting API tests')
      
      try {
        // Projects API test
        console.log('📡 Testing /api/projects...')
        const projectsResponse = await fetch('/api/projects')
        console.log('Projects response:', projectsResponse.status, projectsResponse.statusText)
        
        if (projectsResponse.ok) {
          const projects = await projectsResponse.json()
          console.log('✅ Projects data:', projects)
          setProjectsData(projects)
        } else {
          throw new Error(`Projects API failed: ${projectsResponse.status}`)
        }

        // Stats API test
        console.log('📊 Testing /api/projects/stats...')
        const statsResponse = await fetch('/api/projects/stats')
        console.log('Stats response:', statsResponse.status, statsResponse.statusText)
        
        if (statsResponse.ok) {
          const stats = await statsResponse.json()
          console.log('✅ Stats data:', stats)
          setStatsData(stats)
        } else {
          throw new Error(`Stats API failed: ${statsResponse.status}`)
        }

        setLoading(false)
        console.log('🎉 All API tests completed successfully')
        
      } catch (err) {
        console.error('💥 API test error:', err)
        setError(err.message)
        setLoading(false)
      }
    }

    testAPIs()
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p>API テスト中...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center text-red-600">
          <h2 className="text-xl font-bold mb-4">API テストエラー</h2>
          <p>{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <h1 className="text-3xl font-bold mb-8 text-center">🧪 API テスト結果</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4 text-green-600">✅ Projects API</h2>
            <p className="text-sm text-gray-600 mb-2">データ数: {projectsData?.length || 0}</p>
            <pre className="bg-gray-100 p-3 rounded text-xs overflow-auto max-h-64">
              {JSON.stringify(projectsData, null, 2)}
            </pre>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4 text-blue-600">📊 Stats API</h2>
            <p className="text-sm text-gray-600 mb-2">総プロジェクト: {statsData?.total_projects || 0}</p>
            <pre className="bg-gray-100 p-3 rounded text-xs overflow-auto max-h-64">
              {JSON.stringify(statsData, null, 2)}
            </pre>
          </div>
        </div>
        
        <div className="text-center mt-8">
          <a 
            href="/" 
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            ← メインページに戻る
          </a>
        </div>
      </div>
    </div>
  )
}