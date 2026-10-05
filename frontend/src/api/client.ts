import { useMutation } from '@tanstack/react-query';
import type { ChatResponse } from '../types';

export const API_BASE = '';

/**
 * The single unified API request: sends the prompt message, optional attached file, and session ID to POST /api/chat.
 */
export async function sendChatMessage(
  message: string,
  file?: File | null,
  sessionId?: string,
): Promise<ChatResponse> {
  const formData = new FormData();
  formData.append('message', message);
  if (file) {
    formData.append('file', file);
  }
  if (sessionId) {
    formData.append('session_id', sessionId);
  }

  const response = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Failed to process request' }));
    throw new Error(err.detail || `Server error: ${response.status}`);
  }

  return response.json();
}

/**
 * TanStack Mutation hook for POST /api/chat
 */
export function useChatMutation() {
  return useMutation({
    mutationFn: ({ message, file, sessionId }: { message: string; file?: File | null; sessionId?: string }) =>
      sendChatMessage(message, file, sessionId),
  });
}
