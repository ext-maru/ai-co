'use client'

import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { GitBranch, Clock, User, FileText, ChevronDown, ChevronUp, ArrowRight, GitCommit } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'

interface Version {
  id: string
  version: string
  timestamp: string
  author: string
  message: string
  changes: {
    additions: number
    deletions: number
    files: string[]
  }
  type: 'major' | 'minor' | 'patch'
}

interface VersionHistoryProps {
  documentId: string
  versions: Version[]
  currentVersion: string
  onVersionSelect?: (version: Version) => void
  onCompare?: (versionA: Version, versionB: Version) => void
  className?: string
}

export function VersionHistory({
  documentId,
  versions,
  currentVersion,
  onVersionSelect,
  onCompare,
  className
}: VersionHistoryProps) {
  const [expandedVersions, setExpandedVersions] = useState<Set<string>>(new Set())
  const [compareMode, setCompareMode] = useState(false)
  const [selectedVersions, setSelectedVersions] = useState<Set<string>>(new Set())

  const toggleExpanded = (versionId: string) => {
    setExpandedVersions(prev => {
      const next = new Set(prev)
      if (next.has(versionId)) {
        next.delete(versionId)
      } else {
        next.add(versionId)
      }
      return next
    })
  }

  const toggleVersionSelection = (versionId: string) => {
    if (!compareMode) return

    setSelectedVersions(prev => {
      const next = new Set(prev)
      if (next.has(versionId)) {
        next.delete(versionId)
      } else {
        if (next.size >= 2) {
          // Only allow 2 versions to be selected
          const first = Array.from(next)[0]
          next.delete(first)
        }
        next.add(versionId)
      }
      return next
    })
  }

  const handleCompare = () => {
    if (selectedVersions.size === 2 && onCompare) {
      const [v1, v2] = Array.from(selectedVersions).map(id => 
        versions.find(v => v.id === id)!
      )
      onCompare(v1, v2)
    }
  }

  const getVersionColor = (type: Version['type']) => {
    switch (type) {
      case 'major': return 'bg-red-100 text-red-800 border-red-200'
      case 'minor': return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'patch': return 'bg-green-100 text-green-800 border-green-200'
    }
  }

  const getVersionIcon = (type: Version['type']) => {
    switch (type) {
      case 'major': return '🚀'
      case 'minor': return '✨'
      case 'patch': return '🔧'
    }
  }

  return (
    <div className={cn('space-y-4', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
          <GitBranch className="w-5 h-5 mr-2 text-purple-600" />
          バージョン履歴
        </h3>
        <div className="flex items-center space-x-2">
          {compareMode && selectedVersions.size === 2 && (
            <Button
              variant="primary"
              size="sm"
              onClick={handleCompare}
              className="bg-purple-600 hover:bg-purple-700"
            >
              比較する
            </Button>
          )}
          <Button
            variant={compareMode ? 'secondary' : 'outline'}
            size="sm"
            onClick={() => {
              setCompareMode(!compareMode)
              setSelectedVersions(new Set())
            }}
          >
            {compareMode ? 'キャンセル' : '比較モード'}
          </Button>
        </div>
      </div>

      {/* Version Timeline */}
      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-purple-200" />

        <AnimatePresence>
          {versions.map((version, index) => (
            <motion.div
              key={version.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              className="relative"
            >
              {/* Timeline node */}
              <div className={cn(
                'absolute left-6 w-4 h-4 rounded-full border-4 border-white transform -translate-x-1/2',
                version.version === currentVersion
                  ? 'bg-purple-600 ring-4 ring-purple-200'
                  : 'bg-purple-400'
              )} />

              {/* Version card */}
              <Card
                className={cn(
                  'ml-12 mb-4 p-4 cursor-pointer transition-all duration-200',
                  'hover:shadow-md',
                  compareMode && selectedVersions.has(version.id) && 'ring-2 ring-purple-500',
                  version.version === currentVersion && 'border-purple-300 bg-purple-50'
                )}
                onClick={() => compareMode ? toggleVersionSelection(version.id) : onVersionSelect?.(version)}
              >
                {/* Version header */}
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl">{getVersionIcon(version.type)}</span>
                    <div>
                      <div className="flex items-center space-x-2">
                        <h4 className="font-semibold text-gray-900">
                          v{version.version}
                        </h4>
                        <Badge className={cn('text-xs', getVersionColor(version.type))}>
                          {version.type}
                        </Badge>
                        {version.version === currentVersion && (
                          <Badge variant="secondary" className="text-xs">
                            現在
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 mt-1">{version.message}</p>
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      toggleExpanded(version.id)
                    }}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    {expandedVersions.has(version.id) ? (
                      <ChevronUp className="w-5 h-5" />
                    ) : (
                      <ChevronDown className="w-5 h-5" />
                    )}
                  </button>
                </div>

                {/* Version metadata */}
                <div className="flex items-center space-x-4 text-sm text-gray-500">
                  <div className="flex items-center">
                    <User className="w-4 h-4 mr-1" />
                    {version.author}
                  </div>
                  <div className="flex items-center">
                    <Clock className="w-4 h-4 mr-1" />
                    {new Date(version.timestamp).toLocaleString('ja-JP')}
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-green-600">+{version.changes.additions}</span>
                    <span className="text-red-600">-{version.changes.deletions}</span>
                  </div>
                </div>

                {/* Expanded details */}
                <AnimatePresence>
                  {expandedVersions.has(version.id) && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="overflow-hidden"
                    >
                      <div className="mt-4 pt-4 border-t border-gray-200">
                        <h5 className="text-sm font-medium text-gray-700 mb-2">
                          変更されたファイル ({version.changes.files.length})
                        </h5>
                        <div className="space-y-1">
                          {version.changes.files.map((file, fileIndex) => (
                            <div
                              key={fileIndex}
                              className="flex items-center space-x-2 text-sm text-gray-600"
                            >
                              <FileText className="w-4 h-4" />
                              <span className="font-mono">{file}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Compare mode indicator */}
                {compareMode && (
                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <div className="flex items-center justify-center text-sm">
                      {selectedVersions.has(version.id) ? (
                        <span className="text-purple-600 font-medium">
                          比較対象として選択済み
                        </span>
                      ) : (
                        <span className="text-gray-400">
                          クリックして比較対象に追加
                        </span>
                      )}
                    </div>
                  </div>
                )}
              </Card>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Comparison preview */}
      {compareMode && selectedVersions.size === 2 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-6 p-4 bg-purple-50 rounded-lg border border-purple-200"
        >
          <div className="flex items-center justify-center space-x-4">
            {Array.from(selectedVersions).map((id, index) => {
              const version = versions.find(v => v.id === id)!
              return (
                <React.Fragment key={id}>
                  {index > 0 && <ArrowRight className="w-5 h-5 text-purple-600" />}
                  <div className="text-center">
                    <div className="font-semibold text-purple-900">v{version.version}</div>
                    <div className="text-sm text-purple-600">{version.author}</div>
                  </div>
                </React.Fragment>
              )
            })}
          </div>
        </motion.div>
      )}
    </div>
  )
}