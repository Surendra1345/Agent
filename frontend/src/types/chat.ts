import type { ChatResponse } from './index';

export interface ChatAttachment {
  name: string;
  size?: string;
  type?: string;
  url?: string;
}

export interface ChatMessageItem {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  attachment?: ChatAttachment;
  response?: ChatResponse;
  status?: 'sending' | 'success' | 'error';
  errorMessage?: string;
}

export interface ConversationSession {
  id: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  messages: ChatMessageItem[];
}
