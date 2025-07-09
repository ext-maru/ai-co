/**
 * WebSocket Hook for AI Company Web - Four Sages System
 * Real-time communication with FastAPI backend
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { WebSocketManager } from '@/lib/api-client';

export interface WebSocketOptions {
  sageType?: 'knowledge' | 'task' | 'incident' | 'search';
  userId?: string;
  elderCouncilSession?: string;
  autoConnect?: boolean;
}

export interface WebSocketState {
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  lastMessage: any;
}

export const useWebSocket = (options: WebSocketOptions = {}) => {
  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    isConnecting: false,
    error: null,
    lastMessage: null,
  });

  const wsManager = useRef<WebSocketManager | null>(null);
  const messageHandlers = useRef<Map<string, Function[]>>(new Map());

  // Initialize WebSocket manager
  useEffect(() => {
    wsManager.current = new WebSocketManager(
      options.sageType,
      options.userId,
      options.elderCouncilSession
    );

    return () => {
      if (wsManager.current) {
        wsManager.current.disconnect();
      }
    };
  }, [options.sageType, options.userId, options.elderCouncilSession]);

  // Auto-connect if enabled
  useEffect(() => {
    if (options.autoConnect !== false && wsManager.current) {
      connect();
    }
  }, [options.autoConnect]);

  const connect = useCallback(async () => {
    if (!wsManager.current || state.isConnecting || state.isConnected) {
      return;
    }

    setState(prev => ({ ...prev, isConnecting: true, error: null }));

    try {
      await wsManager.current.connect();
      setState(prev => ({
        ...prev,
        isConnected: true,
        isConnecting: false,
        error: null,
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        isConnected: false,
        isConnecting: false,
        error: error instanceof Error ? error.message : 'Connection failed',
      }));
    }
  }, [state.isConnecting, state.isConnected]);

  const disconnect = useCallback(() => {
    if (wsManager.current) {
      wsManager.current.disconnect();
      setState(prev => ({
        ...prev,
        isConnected: false,
        isConnecting: false,
      }));
    }
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (wsManager.current && state.isConnected) {
      wsManager.current.send(message);
    } else {
      console.warn('Cannot send message: WebSocket not connected');
    }
  }, [state.isConnected]);

  const addMessageHandler = useCallback((messageType: string, handler: Function) => {
    if (wsManager.current) {
      wsManager.current.on(messageType, handler);
      
      // Store handler for cleanup
      if (!messageHandlers.current.has(messageType)) {
        messageHandlers.current.set(messageType, []);
      }
      messageHandlers.current.get(messageType)!.push(handler);
    }
  }, []);

  const removeMessageHandler = useCallback((messageType: string, handler: Function) => {
    if (wsManager.current) {
      wsManager.current.off(messageType, handler);
      
      // Remove from stored handlers
      const handlers = messageHandlers.current.get(messageType);
      if (handlers) {
        const index = handlers.indexOf(handler);
        if (index > -1) {
          handlers.splice(index, 1);
        }
      }
    }
  }, []);

  // Cleanup handlers on unmount
  useEffect(() => {
    return () => {
      if (wsManager.current) {
        // Remove all handlers
        messageHandlers.current.forEach((handlers, messageType) => {
          handlers.forEach(handler => {
            wsManager.current?.off(messageType, handler);
          });
        });
        messageHandlers.current.clear();
      }
    };
  }, []);

  return {
    ...state,
    connect,
    disconnect,
    sendMessage,
    addMessageHandler,
    removeMessageHandler,
  };
};

// Specialized hooks for each sage type
export const useKnowledgeSageWebSocket = (userId?: string) => {
  return useWebSocket({ sageType: 'knowledge', userId });
};

export const useTaskSageWebSocket = (userId?: string) => {
  return useWebSocket({ sageType: 'task', userId });
};

export const useIncidentSageWebSocket = (userId?: string) => {
  return useWebSocket({ sageType: 'incident', userId });
};

export const useSearchSageWebSocket = (userId?: string) => {
  return useWebSocket({ sageType: 'search', userId });
};

export const useElderCouncilWebSocket = (sessionId: string, userId?: string) => {
  return useWebSocket({ elderCouncilSession: sessionId, userId });
};

// Hook for sage-to-sage communication
export const useSageCommunication = (sageType: 'knowledge' | 'task' | 'incident' | 'search', userId?: string) => {
  const webSocket = useWebSocket({ sageType, userId });
  const [messages, setMessages] = useState<any[]>([]);

  const sendSageMessage = useCallback((targetSage: string, content: any) => {
    webSocket.sendMessage({
      type: 'sage_message',
      target_sage: targetSage,
      content,
    });
  }, [webSocket]);

  const broadcastStatus = useCallback((content: any) => {
    webSocket.sendMessage({
      type: 'status_update',
      content,
    });
  }, [webSocket]);

  // Listen for sage messages
  useEffect(() => {
    const handleSageMessage = (message: any) => {
      if (message.sage_type && message.sage_type !== sageType) {
        setMessages(prev => [...prev, message]);
      }
    };

    webSocket.addMessageHandler('sage_message', handleSageMessage);
    webSocket.addMessageHandler('status_update', handleSageMessage);
    webSocket.addMessageHandler('broadcast', handleSageMessage);

    return () => {
      webSocket.removeMessageHandler('sage_message', handleSageMessage);
      webSocket.removeMessageHandler('status_update', handleSageMessage);
      webSocket.removeMessageHandler('broadcast', handleSageMessage);
    };
  }, [webSocket, sageType]);

  return {
    ...webSocket,
    messages,
    sendSageMessage,
    broadcastStatus,
    clearMessages: () => setMessages([]),
  };
};

// Hook for Elder Council communication
export const useElderCouncilCommunication = (sessionId: string, userId?: string) => {
  const webSocket = useWebSocket({ elderCouncilSession: sessionId, userId });
  const [messages, setMessages] = useState<any[]>([]);

  const sendCouncilMessage = useCallback((content: string, messageType: string = 'chat') => {
    webSocket.sendMessage({
      type: 'council_message',
      content,
      message_type: messageType,
      sender: userId || 'Anonymous',
    });
  }, [webSocket, userId]);

  const joinSession = useCallback((newSessionId: string) => {
    webSocket.sendMessage({
      type: 'join_session',
      session_id: newSessionId,
    });
  }, [webSocket]);

  const leaveSession = useCallback((sessionIdToLeave: string) => {
    webSocket.sendMessage({
      type: 'leave_session',
      session_id: sessionIdToLeave,
    });
  }, [webSocket]);

  // Listen for council messages
  useEffect(() => {
    const handleCouncilMessage = (message: any) => {
      if (message.type === 'council_message' || message.type === 'council_invoked') {
        setMessages(prev => [...prev, message]);
      }
    };

    webSocket.addMessageHandler('council_message', handleCouncilMessage);
    webSocket.addMessageHandler('council_invoked', handleCouncilMessage);
    webSocket.addMessageHandler('council_decision', handleCouncilMessage);

    return () => {
      webSocket.removeMessageHandler('council_message', handleCouncilMessage);
      webSocket.removeMessageHandler('council_invoked', handleCouncilMessage);
      webSocket.removeMessageHandler('council_decision', handleCouncilMessage);
    };
  }, [webSocket]);

  return {
    ...webSocket,
    messages,
    sendCouncilMessage,
    joinSession,
    leaveSession,
    clearMessages: () => setMessages([]),
  };
};