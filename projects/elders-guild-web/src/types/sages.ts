// 4 Sages System Type Definitions
export type SageType = 'knowledge' | 'task' | 'incident' | 'rag'

export interface SageStatus {
  id: string
  type: SageType
  name: string
  title: string
  status: 'active' | 'inactive' | 'busy' | 'meditation'
  activity: string
  metrics: {
    primary: { label: string; value: string | number }
    secondary: { label: string; value: string | number }
  }
  lastActive: Date
  level: number
  experience: number
}

export interface KnowledgeSage extends SageStatus {
  type: 'knowledge'
  name: '📚 ナレッジ賢者'
  title: '叡智の守護者'
  specialties: string[]
  knowledgeBase: {
    total: number
    categories: Record<string, number>
    recentUpdates: Array<{
      id: string
      title: string
      timestamp: Date
      category: string
    }>
  }
}

export interface TaskSage extends SageStatus {
  type: 'task'
  name: '📋 タスク賢者'
  title: '修行導師'
  activeTasks: number
  completedTasks: number
  taskQueue: Array<{
    id: string
    title: string
    priority: 'high' | 'medium' | 'low'
    status: 'pending' | 'in_progress' | 'completed'
    assignedTo?: string
    deadline?: Date
  }>
}

export interface IncidentSage extends SageStatus {
  type: 'incident'
  name: '🚨 インシデント賢者'
  title: '危機の守護者'
  activeIncidents: number
  resolvedIncidents: number
  alertLevel: 'low' | 'medium' | 'high' | 'critical'
  recentIncidents: Array<{
    id: string
    title: string
    severity: 'low' | 'medium' | 'high' | 'critical'
    status: 'open' | 'investigating' | 'resolved'
    timestamp: Date
  }>
}

export interface RAGSage extends SageStatus {
  type: 'rag'
  name: '🔍 RAG賢者'
  title: '探求の導師'
  searchAccuracy: number
  discoveryRate: number
  recentSearches: Array<{
    id: string
    query: string
    results: number
    timestamp: Date
    relevance: number
  }>
  indexedDocuments: number
}

export type Sage = KnowledgeSage | TaskSage | IncidentSage | RAGSage

// Elder Hierarchy Types
export type HierarchyLevel = 'grand_elder' | 'elder' | 'sage' | 'servant'

export interface ElderHierarchy {
  level: HierarchyLevel
  name: string
  title: string
  permissions: string[]
  subordinates: ElderHierarchy[]
}

// AI Company Cultural Types
export interface CulturalTheme {
  primary: string
  secondary: string
  accent: string
  background: string
  text: string
  hover: string
}

export interface SageTheme {
  knowledge: CulturalTheme
  task: CulturalTheme
  incident: CulturalTheme
  rag: CulturalTheme
}

// Council System Types
export interface CouncilSession {
  id: string
  type: 'regular' | 'emergency' | 'strategic'
  participants: Sage[]
  agenda: string[]
  decisions: Array<{
    topic: string
    decision: string
    votes: Record<SageType, 'approve' | 'reject' | 'abstain'>
  }>
  timestamp: Date
  status: 'scheduled' | 'in_progress' | 'completed' | 'cancelled'
}

// Communication Types
export interface SageMessage {
  id: string
  from: SageType
  to: SageType | 'all'
  content: string
  type: 'info' | 'warning' | 'error' | 'success'
  timestamp: Date
  priority: 'low' | 'medium' | 'high' | 'urgent'
}

// Dashboard State Types
export interface DashboardState {
  sages: Sage[]
  activeSession?: CouncilSession
  messages: SageMessage[]
  hierarchy: ElderHierarchy
  culturalMode: boolean
  theme: 'light' | 'dark'
  selectedSage?: SageType
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  timestamp: Date
}

export type SageApiResponse = ApiResponse<Sage[]>
export type CouncilApiResponse = ApiResponse<CouncilSession[]>
export type MessageApiResponse = ApiResponse<SageMessage[]>
