import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"
import { SageType } from '@/types/sages'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// 4 Sages Theme Helper Functions
export const getSageThemeClasses = (sageType: SageType) => {
  const themes = {
    knowledge: {
      primary: 'bg-knowledge-500 text-white',
      secondary: 'bg-knowledge-100 text-knowledge-800 border-knowledge-200',
      accent: 'text-knowledge-600',
      hover: 'hover:bg-knowledge-600',
      border: 'border-knowledge-300',
      ring: 'ring-knowledge-500',
      shadow: 'shadow-knowledge',
      glow: 'animate-knowledge-pulse',
    },
    task: {
      primary: 'bg-task-500 text-white',
      secondary: 'bg-task-100 text-task-800 border-task-200',
      accent: 'text-task-600',
      hover: 'hover:bg-task-600',
      border: 'border-task-300',
      ring: 'ring-task-500',
      shadow: 'shadow-task',
      glow: 'animate-task-shimmer',
    },
    incident: {
      primary: 'bg-incident-500 text-white',
      secondary: 'bg-incident-100 text-incident-800 border-incident-200',
      accent: 'text-incident-600',
      hover: 'hover:bg-incident-600',
      border: 'border-incident-300',
      ring: 'ring-incident-500',
      shadow: 'shadow-incident',
      glow: 'animate-incident-alert',
    },
    rag: {
      primary: 'bg-rag-500 text-white',
      secondary: 'bg-rag-100 text-rag-800 border-rag-200',
      accent: 'text-rag-600',
      hover: 'hover:bg-rag-600',
      border: 'border-rag-300',
      ring: 'ring-rag-500',
      shadow: 'shadow-rag',
      glow: 'animate-rag-search',
    },
  }
  return themes[sageType]
}

export const getSageIcon = (sageType: SageType): string => {
  const icons = {
    knowledge: '📚',
    task: '📋',
    incident: '🚨',
    rag: '🔍'
  }
  return icons[sageType]
}

export const getSageTitle = (sageType: SageType): string => {
  const titles = {
    knowledge: '叡智の守護者',
    task: '修行導師',
    incident: '危機の守護者',
    rag: '探求の導師'
  }
  return titles[sageType]
}

export const getSageName = (sageType: SageType): string => {
  const names = {
    knowledge: 'ナレッジ賢者',
    task: 'タスク賢者',
    incident: 'インシデント賢者',
    rag: 'RAG賢者'
  }
  return names[sageType]
}

export const getHierarchyIcon = (level: string): string => {
  const icons: Record<string, string> = {
    grand_elder: '👑',
    elder: '🧙‍♂️',
    sage: '🧙‍♀️',
    servant: '🤖'
  }
  return icons[level] || '🤖'
}

export const formatJapaneseDateTime = (date: Date): string => {
  return date.toLocaleString('ja-JP', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'Asia/Tokyo'
  })
}

export const formatMetricValue = (value: string | number): string => {
  if (typeof value === 'number') {
    if (value >= 1000000) {
      return `${(value / 1000000).toFixed(1)}M`
    } else if (value >= 1000) {
      return `${(value / 1000).toFixed(1)}K`
    }
    return value.toString()
  }
  return value
}

export const getStatusColor = (status: string): string => {
  const colors: Record<string, string> = {
    active: 'text-green-500',
    inactive: 'text-gray-500',
    busy: 'text-yellow-500',
    meditation: 'text-purple-500',
    error: 'text-red-500'
  }
  return colors[status] || 'text-gray-500'
}

export const getPriorityColor = (priority: string): string => {
  const colors: Record<string, string> = {
    high: 'text-red-500 bg-red-50 border-red-200',
    medium: 'text-yellow-600 bg-yellow-50 border-yellow-200',
    low: 'text-green-600 bg-green-50 border-green-200',
    urgent: 'text-red-700 bg-red-100 border-red-300'
  }
  return colors[priority] || 'text-gray-600 bg-gray-50 border-gray-200'
}

export const getCulturalTerm = (englishTerm: string): string => {
  const terms: Record<string, string> = {
    'dashboard': '四賢者評議会',
    'task': '修行録',
    'tasks': '修行録',
    'worker': '従者',
    'workers': '従者たち',
    'queue': '叡智の流れ',
    'queues': '叡智の流れ',
    'admin': '賢者統制',
    'user': '賢者',
    'users': '評議員',
    'status': '状態',
    'active': '活動中',
    'inactive': '休息中',
    'busy': '修行中',
    'completed': '悟得',
    'pending': '待機中',
    'in_progress': '修行中',
    'high': '聖なる緊急',
    'medium': '賢者推奨',
    'low': '修行候補',
    'cpu': '神力',
    'memory': '記憶の器',
    'processing': '修行指導中',
    'login': '叡智の間への参入'
  }
  return terms[englishTerm] || englishTerm
}

export const generateSageMessage = (sageType: SageType, messageType: string): string => {
  const messages: Record<SageType, Record<string, string>> = {
    knowledge: {
      greeting: '叡智の守護者として、知識を皆様と共有いたします',
      working: '古の文献と最新の学問を統合しております',
      completed: '新たなる叡智を獲得いたしました',
      error: '知識の探求中に障害を発見いたしました'
    },
    task: {
      greeting: '修行導師として、皆様の修行を支援いたします',
      working: '最適な修行道を照らしております',
      completed: '修行録の指導が完了いたしました',
      error: '修行の道筋に障害が見つかりました'
    },
    incident: {
      greeting: '危機の守護者として、平穏を維持いたします',
      working: '潜在的な危機を監視しております',
      completed: '危機を無事に解決いたしました',
      error: '緊急事態が発生いたしました'
    },
    rag: {
      greeting: '探求の導師として、真理を探索いたします',
      working: '隠された答えを発見中です',
      completed: '求められた知識を発見いたしました',
      error: '探索中に予期せぬ障害が発生しました'
    }
  }

  return messages[sageType]?.[messageType] || '賢者からのメッセージ'
}
