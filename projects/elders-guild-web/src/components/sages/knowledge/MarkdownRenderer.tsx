'use client'

import React from 'react'
import { motion } from 'framer-motion'
import { CheckCircle, AlertCircle, Info, AlertTriangle, Copy, Check } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useState } from 'react'

interface MarkdownRendererProps {
  content: string
  className?: string
}

export function MarkdownRenderer({ content, className }: MarkdownRendererProps) {
  const [copiedStates, setCopiedStates] = useState<{ [key: string]: boolean }>({})

  const copyToClipboard = async (text: string, id: string) => {
    await navigator.clipboard.writeText(text)
    setCopiedStates(prev => ({ ...prev, [id]: true }))
    setTimeout(() => {
      setCopiedStates(prev => ({ ...prev, [id]: false }))
    }, 2000)
  }

  // Simple markdown parser
  const parseMarkdown = (text: string) => {
    const lines = text.split('\n')
    const elements: React.ReactNode[] = []
    let currentList: string[] = []
    let currentCodeBlock: string[] = []
    let inCodeBlock = false
    let codeLanguage = ''

    lines.forEach((line, index) => {
      // Code blocks
      if (line.startsWith('```')) {
        if (!inCodeBlock) {
          inCodeBlock = true
          codeLanguage = line.slice(3).trim()
          currentCodeBlock = []
        } else {
          inCodeBlock = false
          const codeContent = currentCodeBlock.join('\n')
          const codeId = `code-${index}`
          elements.push(
            <div key={index} className="relative group my-4">
              <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={() => copyToClipboard(codeContent, codeId)}
                  className="p-2 bg-gray-800 text-white rounded hover:bg-gray-700 transition-colors"
                >
                  {copiedStates[codeId] ? (
                    <Check className="w-4 h-4" />
                  ) : (
                    <Copy className="w-4 h-4" />
                  )}
                </button>
              </div>
              <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto">
                <code className={`language-${codeLanguage}`}>
                  {codeContent}
                </code>
              </pre>
            </div>
          )
          currentCodeBlock = []
        }
        return
      }

      if (inCodeBlock) {
        currentCodeBlock.push(line)
        return
      }

      // Headers
      if (line.startsWith('# ')) {
        elements.push(
          <motion.h1
            key={index}
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-3xl font-bold text-gray-900 mb-4 mt-6 border-b border-purple-200 pb-2"
          >
            {line.slice(2)}
          </motion.h1>
        )
      } else if (line.startsWith('## ')) {
        elements.push(
          <motion.h2
            key={index}
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-2xl font-semibold text-gray-800 mb-3 mt-5"
          >
            {line.slice(3)}
          </motion.h2>
        )
      } else if (line.startsWith('### ')) {
        elements.push(
          <motion.h3
            key={index}
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-xl font-semibold text-gray-800 mb-2 mt-4"
          >
            {line.slice(4)}
          </motion.h3>
        )
      }
      // Lists
      else if (line.startsWith('- ') || line.startsWith('* ')) {
        currentList.push(line.slice(2))
        if (index === lines.length - 1 || (!lines[index + 1].startsWith('- ') && !lines[index + 1].startsWith('* '))) {
          elements.push(
            <ul key={`list-${index}`} className="list-disc list-inside space-y-1 mb-4 text-gray-700">
              {currentList.map((item, i) => (
                <motion.li
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="ml-4"
                >
                  {item}
                </motion.li>
              ))}
            </ul>
          )
          currentList = []
        }
      }
      // Blockquotes
      else if (line.startsWith('> ')) {
        const content = line.slice(2)
        let icon = <Info className="w-5 h-5" />
        let bgColor = 'bg-blue-50 border-blue-200'
        let textColor = 'text-blue-800'

        if (content.startsWith('[!NOTE]')) {
          icon = <Info className="w-5 h-5" />
          bgColor = 'bg-blue-50 border-blue-200'
          textColor = 'text-blue-800'
        } else if (content.startsWith('[!WARNING]')) {
          icon = <AlertTriangle className="w-5 h-5" />
          bgColor = 'bg-yellow-50 border-yellow-200'
          textColor = 'text-yellow-800'
        } else if (content.startsWith('[!SUCCESS]')) {
          icon = <CheckCircle className="w-5 h-5" />
          bgColor = 'bg-green-50 border-green-200'
          textColor = 'text-green-800'
        } else if (content.startsWith('[!ERROR]')) {
          icon = <AlertCircle className="w-5 h-5" />
          bgColor = 'bg-red-50 border-red-200'
          textColor = 'text-red-800'
        }

        const displayContent = content.replace(/^\[!\w+\]\s*/, '')
        
        elements.push(
          <motion.blockquote
            key={index}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className={cn(
              'border-l-4 p-4 my-4 rounded-r-lg flex items-start space-x-3',
              bgColor, textColor
            )}
          >
            <div className="flex-shrink-0 mt-0.5">{icon}</div>
            <p className="flex-1">{displayContent}</p>
          </motion.blockquote>
        )
      }
      // Horizontal rule
      else if (line.startsWith('---') || line.startsWith('***')) {
        elements.push(
          <hr key={index} className="my-6 border-gray-200" />
        )
      }
      // Regular paragraphs
      else if (line.trim() !== '') {
        // Parse inline elements
        let parsedLine = line
        
        // Bold
        parsedLine = parsedLine.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')
        
        // Italic
        parsedLine = parsedLine.replace(/\*(.*?)\*/g, '<em class="italic">$1</em>')
        
        // Code
        parsedLine = parsedLine.replace(/`(.*?)`/g, '<code class="px-1.5 py-0.5 bg-purple-100 text-purple-800 rounded text-sm font-mono">$1</code>')
        
        // Links
        parsedLine = parsedLine.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-purple-600 hover:text-purple-800 underline" target="_blank" rel="noopener noreferrer">$1</a>')

        elements.push(
          <motion.p
            key={index}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mb-4 text-gray-700 leading-relaxed"
            dangerouslySetInnerHTML={{ __html: parsedLine }}
          />
        )
      }
    })

    return elements
  }

  return (
    <motion.div
      className={cn('prose prose-purple max-w-none', className)}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      {parseMarkdown(content)}
    </motion.div>
  )
}