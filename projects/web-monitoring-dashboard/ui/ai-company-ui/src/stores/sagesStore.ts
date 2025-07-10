// 4賢者統合システム状態管理ストア

import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import type { 
  Sage, 
  CollaborationSession, 
  ConsensusData, 
  CrossLearningEvent 
} from '../types/sages';

interface SagesState {
  // 4賢者の状態
  sages: Record<string, Sage>;
  
  // 協調セッション
  collaborationSessions: CollaborationSession[];
  activeSessions: CollaborationSession[];
  
  // コンセンサス形成
  consensusData: ConsensusData[];
  
  // クロス学習イベント
  crossLearningEvents: CrossLearningEvent[];
  
  // システム状態
  systemHealth: {
    overall: number;
    connectivity: boolean;
    lastSyncTime: string;
  };
  
  // WebSocket接続状態
  connectionStatus: 'connected' | 'connecting' | 'disconnected' | 'error';
}

interface SagesActions {
  // 賢者状態更新
  updateSageStatus: (sageId: string, sage: Sage) => void;
  setSagesData: (sages: Record<string, Sage>) => void;
  
  // 協調セッション管理
  startCollaborationSession: (session: CollaborationSession) => void;
  updateSessionStatus: (sessionId: string, status: CollaborationSession['status']) => void;
  endCollaborationSession: (sessionId: string) => void;
  
  // コンセンサス管理
  submitConsensus: (consensus: ConsensusData) => void;
  updateConsensusVote: (sessionId: string, sageType: Sage['type'], vote: boolean) => void;
  
  // クロス学習
  addCrossLearningEvent: (event: CrossLearningEvent) => void;
  markLearningSuccess: (eventId: string, success: boolean) => void;
  
  // システム制御
  updateSystemHealth: (health: Partial<SagesState['systemHealth']>) => void;
  setConnectionStatus: (status: SagesState['connectionStatus']) => void;
  
  // API通信
  fetchSagesData: () => Promise<void>;
  initializeWebSocket: () => void;
  disconnectWebSocket: () => void;
}

const useSagesStore = create<SagesState & SagesActions>()(
  subscribeWithSelector((set, get) => ({
    // 初期状態
    sages: {},
    collaborationSessions: [],
    activeSessions: [],
    consensusData: [],
    crossLearningEvents: [],
    systemHealth: {
      overall: 0,
      connectivity: false,
      lastSyncTime: new Date().toISOString(),
    },
    connectionStatus: 'disconnected',
    
    // アクション実装
    updateSageStatus: (sageId, sage) => {
      set((state) => ({
        sages: {
          ...state.sages,
          [sageId]: sage,
        },
        systemHealth: {
          ...state.systemHealth,
          lastSyncTime: new Date().toISOString(),
        },
      }));
    },
    
    setSagesData: (sages) => {
      set(() => ({
        sages,
        systemHealth: {
          overall: calculateOverallHealth(sages),
          connectivity: true,
          lastSyncTime: new Date().toISOString(),
        },
      }));
    },
    
    startCollaborationSession: (session) => {
      set((state) => ({
        collaborationSessions: [...state.collaborationSessions, session],
        activeSessions: [...state.activeSessions, session],
      }));
    },
    
    updateSessionStatus: (sessionId, status) => {
      set((state) => ({
        collaborationSessions: state.collaborationSessions.map((session) =>
          session.id === sessionId ? { ...session, status } : session
        ),
        activeSessions: 
          status === 'completed' 
            ? state.activeSessions.filter((session) => session.id !== sessionId)
            : state.activeSessions.map((session) =>
                session.id === sessionId ? { ...session, status } : session
              ),
      }));
    },
    
    endCollaborationSession: (sessionId) => {
      set((state) => ({
        activeSessions: state.activeSessions.filter((session) => session.id !== sessionId),
      }));
    },
    
    submitConsensus: (consensus) => {
      set((state) => ({
        consensusData: [...state.consensusData, consensus],
      }));
    },
    
    updateConsensusVote: (sessionId, sageType, vote) => {
      set((state) => ({
        consensusData: state.consensusData.map((consensus) =>
          consensus.sessionId === sessionId
            ? {
                ...consensus,
                votes: { ...consensus.votes, [sageType]: vote },
              }
            : consensus
        ),
      }));
    },
    
    addCrossLearningEvent: (event) => {
      set((state) => ({
        crossLearningEvents: [...state.crossLearningEvents, event].slice(-100), // 最新100件のみ保持
      }));
    },
    
    markLearningSuccess: (eventId, success) => {
      set((state) => ({
        crossLearningEvents: state.crossLearningEvents.map((event) =>
          event.id === eventId ? { ...event, success } : event
        ),
      }));
    },
    
    updateSystemHealth: (health) => {
      set((state) => ({
        systemHealth: { ...state.systemHealth, ...health },
      }));
    },
    
    setConnectionStatus: (connectionStatus) => {
      set(() => ({ connectionStatus }));
    },
    
    // API通信の実装
    fetchSagesData: async () => {
      try {
        const response = await fetch('/api/sages/status');
        const data = await response.json();
        get().setSagesData(data.sages);
      } catch (error) {
        console.error('Failed to fetch sages data:', error);
        get().setConnectionStatus('error');
      }
    },
    
    initializeWebSocket: () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/sages`;
      
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        get().setConnectionStatus('connected');
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        switch (data.type) {
          case 'sage_update':
            get().updateSageStatus(data.sageId, data.sage);
            break;
          case 'collaboration_start':
            get().startCollaborationSession(data.session);
            break;
          case 'consensus_update':
            get().submitConsensus(data.consensus);
            break;
          case 'cross_learning':
            get().addCrossLearningEvent(data.event);
            break;
        }
      };
      
      ws.onclose = () => {
        get().setConnectionStatus('disconnected');
        // 自動再接続（10秒後）
        setTimeout(() => {
          get().initializeWebSocket();
        }, 10000);
      };
      
      ws.onerror = () => {
        get().setConnectionStatus('error');
      };
    },
    
    disconnectWebSocket: () => {
      get().setConnectionStatus('disconnected');
    },
  }))
);

// ヘルパー関数
function calculateOverallHealth(sages: Record<string, Sage>): number {
  const sagesToArray = Object.values(sages);
  if (sagesToArray.length === 0) return 0;
  
  const totalHealth = sagesToArray.reduce((sum, sage) => sum + sage.health, 0);
  return Math.round(totalHealth / sagesToArray.length);
}

export default useSagesStore;