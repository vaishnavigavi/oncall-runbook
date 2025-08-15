// API service for communicating with the backend
const API_BASE_URL = import.meta.env.VITE_API_BASE || 'https://oncall-runbook-d64jzxlow-vaishnavis-projects-6721f8c1.vercel.app/api';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  citations?: Citation[];
  confidence?: number;
  diagnostics?: any;
}

export interface Citation {
  filename: string;
  chunk_id: string;
  content?: string;
}

export interface Session {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
}

export interface StructuredAskResponse {
  answer: string;
  citations: Citation[];
  confidence: number;
  session_id: string;
  diagnostics: any;
  retrieval_stats: any;
  planning_stats: any;
}

export interface KBStatus {
  docs_count: number;
  docs: Array<{ filename: string; uploaded_at: string }>;
  index_ready: boolean;
  message: string;
}

// API functions
export const api = {
  // Health check
  async healthCheck(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.json();
  },

  // Self check
  async selfCheck(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/selfcheck`);
    return response.json();
  },

  // Ask a question
  async askQuestion(question: string, sessionId?: string): Promise<StructuredAskResponse> {
    const formData = new FormData();
    formData.append('question', question);
    if (sessionId) {
      formData.append('session_id', sessionId);
    }

    const response = await fetch(`${API_BASE_URL}/ask/structured`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status} ${response.statusText}`);
    }

    return response.json();
  },

  // Upload document
  async uploadDocument(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/kb/ingest`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.status} ${response.statusText}`);
    }

    return response.json();
  },

  // Get KB status
  async getKBStatus(): Promise<KBStatus> {
    const response = await fetch(`${API_BASE_URL}/kb/status`);
    if (!response.ok) {
      throw new Error(`Failed to get KB status: ${response.status}`);
    }
    return response.json();
  },

  // Refresh KB
  async refreshKB(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/kb/refresh`, {
      method: 'POST',
    });
    if (!response.ok) {
      throw new Error(`Failed to refresh KB: ${response.status}`);
    }
    return response.json();
  },

  // Session management
  async createSession(name: string): Promise<Session> {
    const formData = new FormData();
    formData.append('name', name);

    const response = await fetch(`${API_BASE_URL}/sessions`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Failed to create session: ${response.status}`);
    }

    return response.json();
  },

  async getSessions(): Promise<Session[]> {
    const response = await fetch(`${API_BASE_URL}/sessions`);
    if (!response.ok) {
      throw new Error(`Failed to get sessions: ${response.status}`);
    }
    const data = await response.json();
    return data.sessions || [];
  },

  async getSession(sessionId: string): Promise<Session> {
    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`);
    if (!response.ok) {
      throw new Error(`Failed to get session: ${response.status}`);
    }
    return response.json();
  },

  async updateSession(sessionId: string, name: string): Promise<Session> {
    const formData = new FormData();
    formData.append('name', name);

    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`, {
      method: 'PATCH',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Failed to update session: ${response.status}`);
    }

    return response.json();
  },

  async deleteSession(sessionId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error(`Failed to delete session: ${response.status}`);
    }
  },

  async getSessionMessages(sessionId: string): Promise<Message[]> {
    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/messages`);
    if (!response.ok) {
      throw new Error(`Failed to get messages: ${response.status}`);
    }
    const data = await response.json();
    return data.messages || [];
  },

  async exportSession(sessionId: string): Promise<{ markdown: string }> {
    const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/export`, {
      method: 'POST',
    });

    if (!response.ok) {
      throw new Error(`Failed to export session: ${response.status}`);
    }

    return response.json();
  },

  async getSessionStats(): Promise<{ total_sessions: number; total_messages: number }> {
    const response = await fetch(`${API_BASE_URL}/session-stats`);
    if (!response.ok) {
      throw new Error(`Failed to get session stats: ${response.status}`);
    }
    return response.json();
  },
};
