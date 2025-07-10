// 4賢者システム TypeScript型定義

export interface SageStatus {
  id: string;
  name: string;
  status: 'active' | 'idle' | 'processing' | 'error';
  lastActive: string;
  currentTask?: string;
  health: number; // 0-100
}

export interface KnowledgeSage extends SageStatus {
  type: 'knowledge';
  knowledgeBase: {
    documents: number;
    lastUpdated: string;
    categories: string[];
  };
}

export interface TaskSage extends SageStatus {
  type: 'task';
  taskQueue: {
    pending: number;
    active: number;
    completed: number;
    failed: number;
  };
}

export interface IncidentSage extends SageStatus {
  type: 'incident';
  incidents: {
    critical: number;
    warning: number;
    resolved: number;
    total: number;
  };
}

export interface RAGSage extends SageStatus {
  type: 'rag';
  searchEngine: {
    indexSize: number;
    lastIndexed: string;
    queryLatency: number;
  };
}

export type Sage = KnowledgeSage | TaskSage | IncidentSage | RAGSage;

export interface CollaborationSession {
  id: string;
  participants: Sage['type'][];
  status: 'planning' | 'active' | 'consensus' | 'completed';
  objective: string;
  startTime: string;
  duration?: number;
}

export interface ConsensusData {
  sessionId: string;
  votes: Record<Sage['type'], boolean>;
  proposal: string;
  status: 'pending' | 'approved' | 'rejected';
}

export interface CrossLearningEvent {
  id: string;
  fromSage: Sage['type'];
  toSage: Sage['type'];
  learningType: 'pattern' | 'knowledge' | 'strategy';
  data: any;
  timestamp: string;
  success: boolean;
}
