import type { ConversationSession } from '../types/chat';

const STORAGE_KEY = 'contract_ai_conversations_v1';
const ACTIVE_SESSION_KEY = 'contract_ai_active_session_id';

export function getStoredConversations(): ConversationSession[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw);
  } catch (err) {
    console.error('Failed to load conversations from localStorage:', err);
    return [];
  }
}

export function saveStoredConversations(conversations: ConversationSession[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
  } catch (err) {
    console.error('Failed to save conversations to localStorage:', err);
  }
}

export function getActiveSessionId(): string | null {
  try {
    return localStorage.getItem(ACTIVE_SESSION_KEY);
  } catch {
    return null;
  }
}

export function setActiveSessionId(id: string | null): void {
  try {
    if (id) {
      localStorage.setItem(ACTIVE_SESSION_KEY, id);
    } else {
      localStorage.removeItem(ACTIVE_SESSION_KEY);
    }
  } catch (err) {
    console.error('Failed to set active session ID:', err);
  }
}

export function createNewSession(initialTitle = 'New Chat'): ConversationSession {
  const newSession: ConversationSession = {
    id: `conv_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
    title: initialTitle,
    createdAt: Date.now(),
    updatedAt: Date.now(),
    messages: [],
  };

  const existing = getStoredConversations();
  const updated = [newSession, ...existing];
  saveStoredConversations(updated);
  setActiveSessionId(newSession.id);
  return newSession;
}

export function updateSession(session: ConversationSession): void {
  const existing = getStoredConversations();
  const index = existing.findIndex((c) => c.id === session.id);
  if (index >= 0) {
    existing[index] = { ...session, updatedAt: Date.now() };
    saveStoredConversations(existing);
  } else {
    saveStoredConversations([session, ...existing]);
  }
}

export function deleteSession(id: string): ConversationSession[] {
  const existing = getStoredConversations();
  const filtered = existing.filter((c) => c.id !== id);
  saveStoredConversations(filtered);
  return filtered;
}

export function renameSession(id: string, newTitle: string): ConversationSession[] {
  const existing = getStoredConversations();
  const updated = existing.map((c) => (c.id === id ? { ...c, title: newTitle.trim() || 'Untitled Chat', updatedAt: Date.now() } : c));
  saveStoredConversations(updated);
  return updated;
}

export interface GroupedConversations {
  group: string;
  sessions: ConversationSession[];
}

export function groupConversationsByDate(conversations: ConversationSession[]): GroupedConversations[] {
  const now = new Date();
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const startOfYesterday = startOfToday - 24 * 60 * 60 * 1000;
  const startOf7Days = startOfToday - 7 * 24 * 60 * 60 * 1000;

  const todayList: ConversationSession[] = [];
  const yesterdayList: ConversationSession[] = [];
  const past7DaysList: ConversationSession[] = [];
  const olderList: ConversationSession[] = [];

  const sorted = [...conversations].sort((a, b) => b.updatedAt - a.updatedAt);

  for (const session of sorted) {
    const time = session.updatedAt || session.createdAt;
    if (time >= startOfToday) {
      todayList.push(session);
    } else if (time >= startOfYesterday) {
      yesterdayList.push(session);
    } else if (time >= startOf7Days) {
      past7DaysList.push(session);
    } else {
      olderList.push(session);
    }
  }

  const groups: GroupedConversations[] = [];
  if (todayList.length > 0) groups.push({ group: 'Today', sessions: todayList });
  if (yesterdayList.length > 0) groups.push({ group: 'Yesterday', sessions: yesterdayList });
  if (past7DaysList.length > 0) groups.push({ group: 'Previous 7 Days', sessions: past7DaysList });
  if (olderList.length > 0) groups.push({ group: 'Older', sessions: olderList });

  return groups;
}

/**
 * Generate a concise title for a session from the user's first prompt
 */
export function generateChatTitle(prompt: string, fileName?: string): string {
  if (fileName && (!prompt || prompt.length < 5)) {
    return fileName.replace(/\.[^/.]+$/, '').replace(/[-_]/g, ' ');
  }
  const clean = prompt.trim().replace(/^["']|["']$/g, '');
  if (clean.length <= 36) return clean;
  return clean.substring(0, 36) + '...';
}
