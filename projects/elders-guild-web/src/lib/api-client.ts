/**
 * API Client for AI Company Web - Four Sages System
 * FastAPI Backend Integration
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/api/ws';

export interface ApiResponse<T = any> {
  success: boolean;
  message: string;
  data?: T;
  total_count?: number;
  timestamp: string;
}

export interface ErrorResponse {
  success: false;
  error: string;
  details?: Record<string, any>;
  timestamp: string;
}

// Base API client class
class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;

    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || `HTTP ${response.status}: ${response.statusText}`);
      }

      return data;
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  async get<T>(endpoint: string, params?: Record<string, any>): Promise<ApiResponse<T>> {
    const searchParams = params ? new URLSearchParams(params).toString() : '';
    const url = searchParams ? `${endpoint}?${searchParams}` : endpoint;

    return this.request<T>(url);
  }

  async post<T>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T>(endpoint: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'DELETE',
    });
  }
}

// Create API client instances for each sage
export const knowledgeApi = {
  // Knowledge Sage API
  getArticles: (params?: {
    category?: string;
    status?: string;
    tags?: string[];
    limit?: number;
    offset?: number;
  }) => apiClient.get('/sages/knowledge/', params),

  createArticle: (article: {
    title: string;
    content: string;
    category: string;
    tags?: string[];
    author: string;
  }) => apiClient.post('/sages/knowledge/', article),

  getArticle: (id: string) => apiClient.get(`/sages/knowledge/${id}`),

  updateArticle: (id: string, update: {
    title?: string;
    content?: string;
    category?: string;
    tags?: string[];
    status?: string;
  }) => apiClient.put(`/sages/knowledge/${id}`, update),

  deleteArticle: (id: string) => apiClient.delete(`/sages/knowledge/${id}`),

  getCategories: () => apiClient.get('/sages/knowledge/categories/'),
  getTags: () => apiClient.get('/sages/knowledge/tags/'),
  getStats: () => apiClient.get('/sages/knowledge/stats/'),
};

export const taskApi = {
  // Task Sage API
  getTasks: (params?: {
    status?: string;
    priority?: string;
    assignee?: string;
    project?: string;
    labels?: string[];
    limit?: number;
    offset?: number;
  }) => apiClient.get('/sages/tasks/', params),

  createTask: (task: {
    title: string;
    description?: string;
    status?: string;
    priority?: string;
    assignee?: string;
    project?: string;
    labels?: string[];
    due_date?: string;
    estimated_hours?: number;
  }) => apiClient.post('/sages/tasks/', task),

  getTask: (id: string) => apiClient.get(`/sages/tasks/${id}`),

  updateTask: (id: string, update: {
    title?: string;
    description?: string;
    status?: string;
    priority?: string;
    assignee?: string;
    project?: string;
    labels?: string[];
    due_date?: string;
    estimated_hours?: number;
    actual_hours?: number;
  }) => apiClient.put(`/sages/tasks/${id}`, update),

  deleteTask: (id: string) => apiClient.delete(`/sages/tasks/${id}`),

  getProjects: () => apiClient.get('/sages/tasks/projects/'),
  getAssignees: () => apiClient.get('/sages/tasks/assignees/'),
  getStats: () => apiClient.get('/sages/tasks/stats/'),
};

export const incidentApi = {
  // Incident Sage API
  getIncidents: (params?: {
    severity?: string;
    status?: string;
    assignee?: string;
    affected_systems?: string[];
    limit?: number;
    offset?: number;
  }) => apiClient.get('/sages/incidents/', params),

  createIncident: (incident: {
    title: string;
    description: string;
    severity: string;
    assignee?: string;
    reporter: string;
    affected_systems?: string[];
  }) => apiClient.post('/sages/incidents/', incident),

  getIncident: (id: string) => apiClient.get(`/sages/incidents/${id}`),

  updateIncident: (id: string, update: {
    title?: string;
    description?: string;
    severity?: string;
    status?: string;
    assignee?: string;
    affected_systems?: string[];
    resolution?: string;
  }) => apiClient.put(`/sages/incidents/${id}`, update),

  deleteIncident: (id: string) => apiClient.delete(`/sages/incidents/${id}`),

  createAlert: (alert: {
    title: string;
    description: string;
    severity: string;
    affected_systems: string[];
    auto_response?: boolean;
  }) => apiClient.post('/sages/incidents/alert', alert),

  getSystems: () => apiClient.get('/sages/incidents/systems/'),
  getStats: () => apiClient.get('/sages/incidents/stats/'),
};

export const searchApi = {
  // Search Sage API
  search: (query: {
    query: string;
    search_type?: string;
    filters?: Record<string, any>;
    limit?: number;
    offset?: number;
  }) => apiClient.post('/sages/search/', query),

  getSuggestions: (params: {
    q: string;
    limit?: number;
  }) => apiClient.get('/sages/search/suggestions', params),

  findSimilar: (contentType: string, contentId: string, limit?: number) =>
    apiClient.get(`/sages/search/similar/${contentType}/${contentId}`, { limit }),

  getAnalytics: () => apiClient.get('/sages/search/analytics'),
  rebuildIndex: () => apiClient.post('/sages/search/index/rebuild'),
};

export const elderCouncilApi = {
  // Elder Council API
  getSessions: (params?: {
    status?: string;
    limit?: number;
    offset?: number;
  }) => apiClient.get('/elder-council/sessions', params),

  createSession: (session: {
    title: string;
    description?: string;
    participants?: string[];
  }) => apiClient.post('/elder-council/sessions', session),

  getSession: (sessionId: string) => apiClient.get(`/elder-council/sessions/${sessionId}`),

  updateSession: (sessionId: string, update: {
    status?: string;
    title?: string;
    description?: string;
  }) => apiClient.put(`/elder-council/sessions/${sessionId}`, update),

  sendMessage: (sessionId: string, message: {
    sender: string;
    message_type?: string;
    content: string;
    metadata?: Record<string, any>;
  }) => apiClient.post(`/elder-council/sessions/${sessionId}/messages`, message),

  getMessages: (sessionId: string, params?: {
    message_type?: string;
    limit?: number;
    offset?: number;
  }) => apiClient.get(`/elder-council/sessions/${sessionId}/messages`, params),

  invokeCouncil: (sessionId: string, params: {
    topic: string;
    priority?: string;
    auto_invite_sages?: boolean;
  }) => apiClient.post(`/elder-council/sessions/${sessionId}/invoke`, params),

  getStats: () => apiClient.get('/elder-council/stats'),
};

// WebSocket connection management
export class WebSocketManager {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 1000;
  private messageHandlers: Map<string, Function[]> = new Map();

  constructor(
    private sageType?: string,
    private userId?: string,
    private elderCouncilSession?: string
  ) {}

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const params = new URLSearchParams();
        if (this.sageType) params.append('sage_type', this.sageType);
        if (this.userId) params.append('user_id', this.userId);
        if (this.elderCouncilSession) params.append('elder_council_session', this.elderCouncilSession);

        const url = `${WS_BASE_URL}/connect?${params.toString()}`;
        this.ws = new WebSocket(url);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        this.ws.onclose = () => {
          console.log('WebSocket disconnected');
          this.attemptReconnect();
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(message: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, message not sent:', message);
    }
  }

  on(messageType: string, handler: Function) {
    if (!this.messageHandlers.has(messageType)) {
      this.messageHandlers.set(messageType, []);
    }
    this.messageHandlers.get(messageType)!.push(handler);
  }

  off(messageType: string, handler: Function) {
    const handlers = this.messageHandlers.get(messageType);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  private handleMessage(message: any) {
    const handlers = this.messageHandlers.get(message.type);
    if (handlers) {
      handlers.forEach(handler => handler(message));
    }

    // Handle heartbeat
    if (message.type === 'heartbeat') {
      this.send({
        type: 'heartbeat',
        timestamp: Date.now(),
      });
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);

      setTimeout(() => {
        this.connect().catch(error => {
          console.error('Reconnect failed:', error);
        });
      }, this.reconnectInterval * this.reconnectAttempts);
    } else {
      console.error('Max reconnect attempts reached');
    }
  }
}

// Create global API client instance
const apiClient = new ApiClient();

// Health check endpoint
export const healthApi = {
  check: () => apiClient.get('/health'),
};

export default apiClient;
