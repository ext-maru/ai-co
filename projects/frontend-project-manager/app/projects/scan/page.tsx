'use client'

import { useState } from 'react'
import Link from 'next/link'
import {
  ArrowLeftIcon,
  FolderIcon,
  MagnifyingGlassIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon
} from '@heroicons/react/24/outline'

export default function ScanPage() {
  const [scanPath, setScanPath] = useState('')
  const [isScanning, setIsScanning] = useState(false)
  const [scanResults, setScanResults] = useState<any>(null)
  const [error, setError] = useState('')

  const handleScan = async () => {
    if (!scanPath.trim()) {
      setError('スキャンパスを入力してください')
      return
    }

    setIsScanning(true)
    setError('')
    setScanResults(null)

    try {
      // 実際の実装では、ここでスキャンAPIを呼び出します
      // 現在はモックデータを返します
      await new Promise(resolve => setTimeout(resolve, 3000)) // 3秒のシミュレーション

      setScanResults({
        path: scanPath,
        foundProjects: [
          {
            name: 'Example Project 1',
            path: scanPath + '/project1',
            type: 'Next.js Application',
            hasPackageJson: true,
            hasReadme: true,
            estimatedSize: '15.2 MB'
          },
          {
            name: 'Example Project 2',
            path: scanPath + '/project2',
            type: 'React Library',
            hasPackageJson: true,
            hasReadme: false,
            estimatedSize: '8.7 MB'
          }
        ],
        totalScanned: 127,
        totalFound: 2,
        scanTime: '3.2s'
      })
    } catch (err) {
      setError('スキャン中にエラーが発生しました')
    } finally {
      setIsScanning(false)
    }
  }

  const handleAddProject = async (project: any) => {
    try {
      const response = await fetch('/api/projects', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: project.name,
          project_type: project.type.toLowerCase().includes('app') ? 'application' : 'library',
          status: 'discovered',
          description: `${project.path}で発見されたプロジェクト`,
          tech_stack: project.type.includes('Next.js') ? ['Next.js', 'React'] : ['React'],
          file_path: project.path
        })
      })

      if (response.ok) {
        alert('プロジェクトが追加されました！')
      } else {
        alert('プロジェクトの追加に失敗しました')
      }
    } catch (error) {
      alert('エラーが発生しました')
    }
  }

  return (
    <div className="min-h-screen bg-elder-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* ヘッダー */}
        <div className="mb-8">
          <Link href="/" className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-4">
            <ArrowLeftIcon className="h-5 w-5 mr-2" />
            ホームに戻る
          </Link>

          <h1 className="text-3xl font-bold text-gray-900 flex items-center">
            <MagnifyingGlassIcon className="h-8 w-8 mr-3 text-elder-600" />
            新規プロジェクトスキャン
          </h1>
          <p className="text-gray-600 mt-2">
            指定したディレクトリから新しいプロジェクトを検出します
          </p>
        </div>

        {/* スキャンフォーム */}
        <div className="card mb-8">
          <h2 className="text-xl font-semibold mb-4">スキャン設定</h2>

          <div className="space-y-4">
            <div>
              <label htmlFor="scanPath" className="block text-sm font-medium text-gray-700 mb-2">
                スキャンパス
              </label>
              <input
                type="text"
                id="scanPath"
                value={scanPath}
                onChange={(e) => setScanPath(e.target.value)}
                placeholder="/path/to/projects"
                className="input w-full"
                disabled={isScanning}
              />
              <p className="text-sm text-gray-500 mt-1">
                プロジェクトが含まれているディレクトリパスを入力してください
              </p>
            </div>

            {error && (
              <div className="flex items-center p-3 bg-red-50 border border-red-200 rounded-lg">
                <ExclamationTriangleIcon className="h-5 w-5 text-red-500 mr-2" />
                <span className="text-red-700">{error}</span>
              </div>
            )}

            <button
              onClick={handleScan}
              disabled={isScanning}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isScanning ? (
                <>
                  <ClockIcon className="h-5 w-5 mr-2 animate-spin" />
                  スキャン中...
                </>
              ) : (
                <>
                  <MagnifyingGlassIcon className="h-5 w-5 mr-2" />
                  スキャン開始
                </>
              )}
            </button>
          </div>
        </div>

        {/* スキャン結果 */}
        {scanResults && (
          <div className="card">
            <h2 className="text-xl font-semibold mb-4">スキャン結果</h2>

            {/* サマリー */}
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
              <div className="flex items-center mb-2">
                <CheckCircleIcon className="h-5 w-5 text-green-500 mr-2" />
                <span className="font-medium text-green-800">スキャン完了</span>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">スキャン対象</span>
                  <p className="font-medium">{scanResults.totalScanned} ファイル</p>
                </div>
                <div>
                  <span className="text-gray-500">発見プロジェクト</span>
                  <p className="font-medium">{scanResults.totalFound} 個</p>
                </div>
                <div>
                  <span className="text-gray-500">処理時間</span>
                  <p className="font-medium">{scanResults.scanTime}</p>
                </div>
                <div>
                  <span className="text-gray-500">スキャンパス</span>
                  <p className="font-medium text-gray-700">{scanResults.path}</p>
                </div>
              </div>
            </div>

            {/* 発見されたプロジェクト */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium">発見されたプロジェクト</h3>

              {scanResults.foundProjects.map((project: any, index: number) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center mb-2">
                        <FolderIcon className="h-5 w-5 text-gray-400 mr-2" />
                        <h4 className="font-medium text-gray-900">{project.name}</h4>
                        <span className="ml-2 px-2 py-1 bg-elder-100 text-elder-800 text-xs rounded">
                          {project.type}
                        </span>
                      </div>

                      <p className="text-sm text-gray-600 mb-2">{project.path}</p>

                      <div className="flex items-center space-x-4 text-sm">
                        <div className="flex items-center">
                          {project.hasPackageJson ? (
                            <CheckCircleIcon className="h-4 w-4 text-green-500 mr-1" />
                          ) : (
                            <ExclamationTriangleIcon className="h-4 w-4 text-yellow-500 mr-1" />
                          )}
                          <span>package.json</span>
                        </div>

                        <div className="flex items-center">
                          {project.hasReadme ? (
                            <CheckCircleIcon className="h-4 w-4 text-green-500 mr-1" />
                          ) : (
                            <ExclamationTriangleIcon className="h-4 w-4 text-yellow-500 mr-1" />
                          )}
                          <span>README</span>
                        </div>

                        <span className="text-gray-500">サイズ: {project.estimatedSize}</span>
                      </div>
                    </div>

                    <button
                      onClick={() => handleAddProject(project)}
                      className="btn-primary ml-4"
                    >
                      追加
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 使用方法 */}
        <div className="card mt-8">
          <h2 className="text-xl font-semibold mb-4">使用方法</h2>
          <div className="space-y-3 text-sm text-gray-600">
            <p>1. スキャンしたいディレクトリパスを入力してください</p>
            <p>2. 「スキャン開始」ボタンをクリックしてプロジェクトを検出します</p>
            <p>3. 発見されたプロジェクトの一覧が表示されます</p>
            <p>4. 追加したいプロジェクトの「追加」ボタンをクリックしてシステムに登録します</p>
          </div>
        </div>
      </div>
    </div>
  )
}
