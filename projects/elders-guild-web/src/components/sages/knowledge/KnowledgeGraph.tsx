'use client'

import React, { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'
import { ZoomIn, ZoomOut, Maximize2, Filter } from 'lucide-react'
import { Button } from '@/components/ui/Button'

interface Node {
  id: string
  label: string
  type: 'document' | 'category' | 'tag' | 'author'
  size: number
  color: string
  x?: number
  y?: number
  vx?: number
  vy?: number
}

interface Link {
  source: string
  target: string
  strength: number
}

interface KnowledgeGraphProps {
  nodes: Node[]
  links: Link[]
  className?: string
  onNodeClick?: (node: Node) => void
}

export function KnowledgeGraph({ nodes, links, className, onNodeClick }: KnowledgeGraphProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const animationRef = useRef<number>()
  const [zoom, setZoom] = useState(1)
  const [offset, setOffset] = useState({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })
  const [hoveredNode, setHoveredNode] = useState<Node | null>(null)
  const [selectedTypes, setSelectedTypes] = useState<Set<string>>(
    new Set(['document', 'category', 'tag', 'author'])
  )

  // Initialize node positions
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const width = canvas.width
    const height = canvas.height

    nodes.forEach((node) => {
      node.x = Math.random() * width
      node.y = Math.random() * height
      node.vx = 0
      node.vy = 0
    })
  }, [nodes])

  // Force simulation
  useEffect(() => {
    const canvas = canvasRef.current
    const ctx = canvas?.getContext('2d')
    if (!canvas || !ctx) return

    const width = canvas.width
    const height = canvas.height
    const centerX = width / 2
    const centerY = height / 2

    const simulate = () => {
      // Apply forces
      nodes.forEach((node) => {
        if (!selectedTypes.has(node.type)) return

        // Centering force
        const dx = centerX - (node.x || 0)
        const dy = centerY - (node.y || 0)
        node.vx = (node.vx || 0) + dx * 0.001
        node.vy = (node.vy || 0) + dy * 0.001

        // Repulsion between nodes
        nodes.forEach((other) => {
          if (node.id === other.id || !selectedTypes.has(other.type)) return

          const dx = (node.x || 0) - (other.x || 0)
          const dy = (node.y || 0) - (other.y || 0)
          const distance = Math.sqrt(dx * dx + dy * dy)

          if (distance < 100) {
            const force = (100 - distance) / distance * 0.5
            node.vx = (node.vx || 0) + dx * force
            node.vy = (node.vy || 0) + dy * force
          }
        })
      })

      // Apply link forces
      links.forEach((link) => {
        const source = nodes.find(n => n.id === link.source)
        const target = nodes.find(n => n.id === link.target)

        if (!source || !target || !selectedTypes.has(source.type) || !selectedTypes.has(target.type)) return

        const dx = (target.x || 0) - (source.x || 0)
        const dy = (target.y || 0) - (source.y || 0)
        const distance = Math.sqrt(dx * dx + dy * dy)

        const force = (distance - 150) * link.strength * 0.001
        const fx = dx / distance * force
        const fy = dy / distance * force

        source.vx = (source.vx || 0) + fx
        source.vy = (source.vy || 0) + fy
        target.vx = (target.vx || 0) - fx
        target.vy = (target.vy || 0) - fy
      })

      // Update positions
      nodes.forEach((node) => {
        if (!selectedTypes.has(node.type)) return

        // Apply velocity
        node.x = (node.x || 0) + (node.vx || 0)
        node.y = (node.y || 0) + (node.vy || 0)

        // Apply friction
        node.vx = (node.vx || 0) * 0.9
        node.vy = (node.vy || 0) * 0.9

        // Keep nodes within bounds
        node.x = Math.max(20, Math.min(width - 20, node.x || 0))
        node.y = Math.max(20, Math.min(height - 20, node.y || 0))
      })

      // Clear and redraw
      ctx.clearRect(0, 0, width, height)

      // Apply transformations
      ctx.save()
      ctx.translate(offset.x, offset.y)
      ctx.scale(zoom, zoom)

      // Draw links
      ctx.strokeStyle = '#e5e7eb'
      ctx.lineWidth = 1
      links.forEach((link) => {
        const source = nodes.find(n => n.id === link.source)
        const target = nodes.find(n => n.id === link.target)

        if (!source || !target || !selectedTypes.has(source.type) || !selectedTypes.has(target.type)) return

        ctx.beginPath()
        ctx.moveTo(source.x || 0, source.y || 0)
        ctx.lineTo(target.x || 0, target.y || 0)
        ctx.globalAlpha = link.strength
        ctx.stroke()
        ctx.globalAlpha = 1
      })

      // Draw nodes
      nodes.forEach((node) => {
        if (!selectedTypes.has(node.type)) return

        const x = node.x || 0
        const y = node.y || 0

        // Node circle
        ctx.beginPath()
        ctx.arc(x, y, node.size, 0, Math.PI * 2)
        ctx.fillStyle = node.color
        ctx.fill()

        if (hoveredNode?.id === node.id) {
          ctx.strokeStyle = '#7c3aed'
          ctx.lineWidth = 3
          ctx.stroke()
        }

        // Node label
        ctx.fillStyle = '#1f2937'
        ctx.font = '12px sans-serif'
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        ctx.fillText(node.label, x, y + node.size + 15)
      })

      ctx.restore()

      animationRef.current = requestAnimationFrame(simulate)
    }

    simulate()

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [nodes, links, zoom, offset, hoveredNode, selectedTypes])

  // Handle mouse events
  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current
    if (!canvas) return

    const rect = canvas.getBoundingClientRect()
    const x = (e.clientX - rect.left - offset.x) / zoom
    const y = (e.clientY - rect.top - offset.y) / zoom

    if (isDragging) {
      setOffset({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      })
    } else {
      // Check for node hover
      const hovered = nodes.find((node) => {
        if (!selectedTypes.has(node.type)) return false
        const dx = x - (node.x || 0)
        const dy = y - (node.y || 0)
        return Math.sqrt(dx * dx + dy * dy) < node.size
      })
      setHoveredNode(hovered || null)
    }
  }

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current
    if (!canvas) return

    const rect = canvas.getBoundingClientRect()
    const x = (e.clientX - rect.left - offset.x) / zoom
    const y = (e.clientY - rect.top - offset.y) / zoom

    // Check if clicking on a node
    const clicked = nodes.find((node) => {
      if (!selectedTypes.has(node.type)) return false
      const dx = x - (node.x || 0)
      const dy = y - (node.y || 0)
      return Math.sqrt(dx * dx + dy * dy) < node.size
    })

    if (clicked && onNodeClick) {
      onNodeClick(clicked)
    } else {
      setIsDragging(true)
      setDragStart({
        x: e.clientX - offset.x,
        y: e.clientY - offset.y
      })
    }
  }

  const handleMouseUp = () => {
    setIsDragging(false)
  }

  const handleWheel = (e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault()
    const delta = e.deltaY > 0 ? 0.9 : 1.1
    setZoom(prev => Math.max(0.5, Math.min(3, prev * delta)))
  }

  const toggleType = (type: string) => {
    setSelectedTypes(prev => {
      const next = new Set(prev)
      if (next.has(type)) {
        next.delete(type)
      } else {
        next.add(type)
      }
      return next
    })
  }

  const resetView = () => {
    setZoom(1)
    setOffset({ x: 0, y: 0 })
  }

  return (
    <div ref={containerRef} className={cn('relative bg-gray-50 rounded-lg overflow-hidden', className)}>
      {/* Controls */}
      <div className="absolute top-4 left-4 z-10 space-y-2">
        <div className="bg-white rounded-lg shadow-lg p-2 space-y-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setZoom(prev => Math.min(3, prev * 1.2))}
            className="w-full justify-start"
          >
            <ZoomIn className="w-4 h-4 mr-2" />
            拡大
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setZoom(prev => Math.max(0.5, prev * 0.8))}
            className="w-full justify-start"
          >
            <ZoomOut className="w-4 h-4 mr-2" />
            縮小
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={resetView}
            className="w-full justify-start"
          >
            <Maximize2 className="w-4 h-4 mr-2" />
            リセット
          </Button>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-2">
          <div className="flex items-center mb-2 text-sm font-medium text-gray-700">
            <Filter className="w-4 h-4 mr-2" />
            フィルター
          </div>
          {[
            { type: 'document', label: 'ドキュメント', color: '#9333ea' },
            { type: 'category', label: 'カテゴリ', color: '#3b82f6' },
            { type: 'tag', label: 'タグ', color: '#10b981' },
            { type: 'author', label: '作成者', color: '#f59e0b' }
          ].map(({ type, label, color }) => (
            <label key={type} className="flex items-center space-x-2 p-1 hover:bg-gray-50 rounded cursor-pointer">
              <input
                type="checkbox"
                checked={selectedTypes.has(type)}
                onChange={() => toggleType(type)}
                className="rounded text-purple-600 focus:ring-purple-500"
              />
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
              <span className="text-sm">{label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Canvas */}
      <canvas
        ref={canvasRef}
        width={800}
        height={600}
        className="w-full h-full cursor-move"
        onMouseMove={handleMouseMove}
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
        style={{ cursor: isDragging ? 'grabbing' : hoveredNode ? 'pointer' : 'grab' }}
      />

      {/* Hover tooltip */}
      {hoveredNode && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="absolute bottom-4 right-4 bg-white rounded-lg shadow-lg p-3 max-w-xs"
        >
          <div className="font-semibold text-gray-900">{hoveredNode.label}</div>
          <div className="text-sm text-gray-500 capitalize">{hoveredNode.type}</div>
        </motion.div>
      )}
    </div>
  )
}
