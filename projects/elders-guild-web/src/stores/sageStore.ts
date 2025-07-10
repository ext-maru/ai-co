import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import {
  Sage,
  SageType,
  DashboardState,
  CouncilSession,
  SageMessage,
  KnowledgeSage,
  TaskSage,
  IncidentSage,
  RAGSage
} from '@/types/sages'

// Initial mock data for 4 sages
const createInitialSages = (): Sage[] => [
  {
    id: 'knowledge-sage',
    type: 'knowledge',
    name: '📚 ナレッジ賢者',
    title: '叡智の守護者',
    status: 'active',
    activity: '叡智を蓄積中',
    metrics: {
      primary: { label: '蓄積叡智', value: '∞' },
      secondary: { label: '学習効率', value: '95%' }
    },
    lastActive: new Date(),
    level: 10,
    experience: 9999,
    specialties: ['知識管理', '学習最適化', '情報統合'],
    knowledgeBase: {
      total: 15420,
      categories: {
        'プログラミング': 3840,
        'AI技術': 2950,
        'プロジェクト管理': 1860,
        'システム設計': 2290,
        'その他': 4480
      },
      recentUpdates: [
        {
          id: 'kb-001',
          title: 'Next.js 14 App Router最新機能',
          timestamp: new Date(),
          category: 'プログラミング'
        },
        {
          id: 'kb-002',
          title: 'Claude AI統合パターン',
          timestamp: new Date(Date.now() - 3600000),
          category: 'AI技術'
        }
      ]
    }
  } as KnowledgeSage,
  {
    id: 'task-sage',
    type: 'task',
    name: '📋 タスク賢者',
    title: '修行導師',
    status: 'active',
    activity: '修行を監督中',
    metrics: {
      primary: { label: '指導効率', value: '88%' },
      secondary: { label: '完了修行', value: 12 }
    },
    lastActive: new Date(),
    level: 9,
    experience: 8750,
    activeTasks: 5,
    completedTasks: 47,
    taskQueue: [
      {
        id: 'task-001',
        title: '4賢者システムUI実装',
        priority: 'high',
        status: 'in_progress',
        assignedTo: 'claude-elder',
        deadline: new Date(Date.now() + 86400000)
      },
      {
        id: 'task-002',
        title: 'API統合テスト',
        priority: 'medium',
        status: 'pending',
        assignedTo: 'dev-servant',
        deadline: new Date(Date.now() + 172800000)
      }
    ]
  } as TaskSage,
  {
    id: 'incident-sage',
    type: 'incident',
    name: '🚨 インシデント賢者',
    title: '危機の守護者',
    status: 'active',
    activity: '平穏を維持中',
    metrics: {
      primary: { label: '守護力', value: '92%' },
      secondary: { label: '解決事案', value: 7 }
    },
    lastActive: new Date(),
    level: 8,
    experience: 7200,
    activeIncidents: 0,
    resolvedIncidents: 23,
    alertLevel: 'low',
    recentIncidents: [
      {
        id: 'inc-001',
        title: 'API応答時間低下',
        severity: 'medium',
        status: 'resolved',
        timestamp: new Date(Date.now() - 7200000)
      },
      {
        id: 'inc-002',
        title: 'メモリ使用量増加',
        severity: 'low',
        status: 'resolved',
        timestamp: new Date(Date.now() - 14400000)
      }
    ]
  } as IncidentSage,
  {
    id: 'rag-sage',
    type: 'rag',
    name: '🔍 RAG賢者',
    title: '探求の導師',
    status: 'active',
    activity: '真理を探索中',
    metrics: {
      primary: { label: '探索精度', value: '97%' },
      secondary: { label: '発見率', value: '94%' }
    },
    lastActive: new Date(),
    level: 9,
    experience: 8400,
    searchAccuracy: 97,
    discoveryRate: 94,
    recentSearches: [
      {
        id: 'search-001',
        query: 'React Server Components',
        results: 234,
        timestamp: new Date(),
        relevance: 0.95
      },
      {
        id: 'search-002',
        query: 'TypeScript 5.x features',
        results: 167,
        timestamp: new Date(Date.now() - 1800000),
        relevance: 0.92
      }
    ],
    indexedDocuments: 12580
  } as RAGSage
]

interface SageStore extends DashboardState {
  // Actions
  updateSage: (sageId: string, updates: Partial<Sage>) => void
  setSageStatus: (sageId: string, status: Sage['status']) => void
  selectSage: (sageType: SageType | undefined) => void
  addMessage: (message: Omit<SageMessage, 'id' | 'timestamp'>) => void
  clearMessages: () => void
  toggleCulturalMode: () => void
  toggleTheme: () => void
  startCouncilSession: (session: Omit<CouncilSession, 'id' | 'timestamp' | 'status'>) => void
  endCouncilSession: () => void
  refreshSagesData: () => Promise<void>

  // Computed values
  getActiveSages: () => Sage[]
  getSageByType: (type: SageType) => Sage | undefined
  getRecentMessages: (limit?: number) => SageMessage[]
  getCouncilStatus: () => 'active' | 'inactive'
}

export const useSageStore = create<SageStore>()(
  devtools(
    persist(
      (set, get) => ({
      // Initial state
      sages: createInitialSages(),
      messages: [],
      hierarchy: {
        level: 'grand_elder',
        name: 'Grand Elder maru',
        title: '至高の導師',
        permissions: ['all'],
        subordinates: [
          {
            level: 'elder',
            name: 'Claude Elder',
            title: '開発実行責任者',
            permissions: ['manage_sages', 'approve_tasks', 'emergency_response'],
            subordinates: []
          }
        ]
      },
      culturalMode: true,
      theme: 'light' as const,
      selectedSage: undefined,
      activeSession: undefined as CouncilSession | undefined,

      // Actions
      updateSage: (sageId, updates) => {
        set((state) => ({
          sages: state.sages.map((sage) =>
            sage.id === sageId ? { ...sage, ...updates, lastActive: new Date() } as Sage : sage
          )
        }))
      },

      setSageStatus: (sageId, status) => {
        set((state) => ({
          sages: state.sages.map((sage) =>
            sage.id === sageId ? { ...sage, status, lastActive: new Date() } : sage
          )
        }))
      },

      selectSage: (sageType) => {
        set({ selectedSage: sageType })
      },

      addMessage: (message) => {
        const newMessage: SageMessage = {
          ...message,
          id: `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          timestamp: new Date()
        }
        set((state) => ({
          messages: [newMessage, ...state.messages].slice(0, 100) // Keep only last 100 messages
        }))
      },

      clearMessages: () => {
        set({ messages: [] })
      },

      toggleCulturalMode: () => {
        set((state) => ({ culturalMode: !state.culturalMode }))
      },

      toggleTheme: () => {
        set((state) => ({ theme: state.theme === 'light' ? 'dark' : 'light' }))
      },

      startCouncilSession: (session) => {
        const newSession: CouncilSession = {
          ...session,
          id: `council-${Date.now()}`,
          timestamp: new Date(),
          status: 'in_progress'
        }
        set({ activeSession: newSession })

        // Add system message
        get().addMessage({
          from: 'knowledge',
          to: 'all',
          content: `四賢者評議会が開始されました: ${session.type}`,
          type: 'info',
          priority: 'high'
        })
      },

      endCouncilSession: () => {
        set((state) => ({
          activeSession: state.activeSession
            ? { ...state.activeSession, status: 'completed' }
            : undefined
        }))

        get().addMessage({
          from: 'knowledge',
          to: 'all',
          content: '四賢者評議会が終了しました',
          type: 'success',
          priority: 'medium'
        })
      },

      refreshSagesData: async () => {
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1000))

        // Update last active times
        set((state) => ({
          sages: state.sages.map((sage) => ({
            ...sage,
            lastActive: new Date()
          }))
        }))
      },

      // Computed values
      getActiveSages: () => {
        return get().sages.filter(sage => sage.status === 'active')
      },

      getSageByType: (type) => {
        return get().sages.find(sage => sage.type === type)
      },

      getRecentMessages: (limit = 10) => {
        return get().messages.slice(0, limit)
      },

      getCouncilStatus: () => {
        return get().activeSession?.status === 'in_progress' ? 'active' : 'inactive'
      }
    }),
    {
      name: 'sage-store',
      partialize: (state) => ({
        sages: state.sages,
        culturalMode: state.culturalMode,
        theme: state.theme,
        hierarchy: state.hierarchy
      })
    }
  ),
  {
    name: 'sage-store'
  }
  )
)
