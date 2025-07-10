// AI Company Configuration Constants

export const AI_COMPANY = {
  name: 'AI Company',
  version: '1.0.0',
  description: 'AI-powered company management system with 4 Sages architecture',
} as const

export const SAGE_CONFIG = {
  knowledge: {
    maxKnowledgeItems: 100000,
    updateInterval: 5000, // 5 seconds
    searchDepth: 10,
  },
  task: {
    maxActiveTasks: 50,
    priorityLevels: ['low', 'medium', 'high', 'urgent'] as const,
    taskTimeout: 86400000, // 24 hours
  },
  incident: {
    severityLevels: ['low', 'medium', 'high', 'critical'] as const,
    alertThreshold: 3,
    autoResolveTimeout: 3600000, // 1 hour
  },
  rag: {
    maxSearchResults: 100,
    minRelevanceScore: 0.7,
    indexUpdateInterval: 60000, // 1 minute
  },
} as const

export const HIERARCHY_LEVELS = {
  grand_elder: {
    name: 'Grand Elder',
    permissions: ['all'],
    color: 'elder',
  },
  elder: {
    name: 'Elder',
    permissions: ['manage_sages', 'approve_tasks', 'emergency_response'],
    color: 'elder',
  },
  sage: {
    name: 'Sage',
    permissions: ['execute_tasks', 'report_incidents', 'access_knowledge'],
    color: 'sage',
  },
  servant: {
    name: 'Servant',
    permissions: ['view_only', 'basic_tasks'],
    color: 'servant',
  },
} as const

export const COUNCIL_TYPES = {
  regular: {
    name: 'Regular Council',
    requiredSages: 3,
    duration: 30, // minutes
  },
  emergency: {
    name: 'Emergency Council',
    requiredSages: 2,
    duration: 15, // minutes
  },
  strategic: {
    name: 'Strategic Council',
    requiredSages: 4,
    duration: 60, // minutes
  },
} as const

export const API_ENDPOINTS = {
  base: process.env['NEXT_PUBLIC_API_BASE_URL'] || 'http://localhost:3000/api',
  sages: '/sages',
  council: '/council',
  messages: '/messages',
  tasks: '/tasks',
  incidents: '/incidents',
  knowledge: '/knowledge',
} as const

export const STORAGE_KEYS = {
  theme: 'ai-company-theme',
  culturalMode: 'ai-company-cultural-mode',
  sageStore: 'sage-store',
} as const
