import { useState, useEffect, useRef } from 'react';
import { Sidebar } from './components/Sidebar';
import { TopHeader } from './components/TopHeader';
import { ChatMessage } from './components/ChatMessage';
import { WelcomeHero } from './components/WelcomeHero';
import { ChatInput } from './components/ChatInput';
import { useChatMutation } from './api/client';
import type { ConversationSession, ChatMessageItem } from './types/chat';
import {
  getStoredConversations,
  getActiveSessionId,
  setActiveSessionId,
  createNewSession,
  updateSession,
  deleteSession,
  renameSession,
  generateChatTitle,
} from './services/conversationStorage';
import { Loader2 } from 'lucide-react';

export function App() {
  const [conversations, setConversations] = useState<ConversationSession[]>(() => {
    return getStoredConversations();
  });
  const [activeSessionId, setActiveId] = useState<string | null>(() => {
    const loaded = getStoredConversations();
    const savedActiveId = getActiveSessionId();
    if (savedActiveId && loaded.some((c) => c.id === savedActiveId)) {
      return savedActiveId;
    }
    return loaded.length > 0 ? loaded[0].id : null;
  });
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [attachedFile, setAttachedFile] = useState<File | null>(null);

  const chatMutation = useChatMutation();
  const chatBottomRef = useRef<HTMLDivElement>(null);

  const activeSession = conversations.find((c) => c.id === activeSessionId) || null;
  const messages = activeSession ? activeSession.messages : [];

  // Determine dynamic thinking status based on active user action
  const getThinkingStatusText = () => {
    const lastUserMessage = [...messages].reverse().find((m) => m.role === 'user');
    if (lastUserMessage?.attachment) {
      return 'Analyzing document and verifying compliance against rulebook...';
    }
    const text = (lastUserMessage?.content || '').toLowerCase().trim();
    if (text.includes('save') || text.includes('store') || text.includes('persist') || text.includes('record')) {
      return 'Saving details to database...';
    }
    if (
      text.startsWith('show') ||
      text.startsWith('list') ||
      text.startsWith('select') ||
      text.startsWith('find') ||
      text.startsWith('how many') ||
      text.startsWith('which') ||
      text.startsWith('what') ||
      text.startsWith('get') ||
      text.includes('crore') ||
      text.includes('lakh') ||
      text.includes('filter') ||
      text.includes('where')
    ) {
      return 'Querying database with SQL analytics...';
    }
    if (text.includes('rule') || text.includes('policy') || text.includes('clause') || text.includes('penalty') || text.includes('liability')) {
      return 'Searching company policies and rulebook...';
    }
    return 'ContractAI is thinking...';
  };

  // Scroll to bottom whenever messages change or when mutation is pending
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length, chatMutation.isPending]);

  const handleNewChat = () => {
    setAttachedFile(null);
    const newSess = createNewSession('New Chat');
    setConversations(getStoredConversations());
    setActiveId(newSess.id);
  };

  const handleSelectSession = (id: string) => {
    setActiveId(id);
    setActiveSessionId(id);
    setAttachedFile(null);
  };

  const handleDeleteSession = (id: string) => {
    const updated = deleteSession(id);
    setConversations(updated);
    if (activeSessionId === id) {
      if (updated.length > 0) {
        setActiveId(updated[0].id);
        setActiveSessionId(updated[0].id);
      } else {
        setActiveId(null);
        setActiveSessionId(null);
      }
    }
  };

  const handleRenameSession = (id: string, newTitle: string) => {
    const updated = renameSession(id, newTitle);
    setConversations(updated);
  };

  const handleSendMessage = async (promptText: string, file: File | null) => {
    const effectivePrompt = promptText.trim() || (file ? `Analyze this document: ${file.name}` : '');
    if (!effectivePrompt && !file) return;

    const now = new Date();
    const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    // Determine current or new session
    let targetSession = activeSession;
    if (!targetSession) {
      const generatedTitle = generateChatTitle(effectivePrompt, file?.name);
      targetSession = createNewSession(generatedTitle);
      setActiveId(targetSession.id);
    }

    const userMessage: ChatMessageItem = {
      id: `msg_${Date.now()}_user`,
      role: 'user',
      content: effectivePrompt,
      timestamp: timeStr,
      attachment: file
        ? {
            name: file.name,
            size: `${(file.size / (1024 * 1024)).toFixed(1)} MB`,
            type: file.type,
          }
        : undefined,
    };

    const updatedMessages = [...targetSession.messages, userMessage];

    // If it was the first message in this session and titled "New Chat", auto-rename
    let sessionTitle = targetSession.title;
    if (targetSession.title === 'New Chat') {
      sessionTitle = generateChatTitle(effectivePrompt, file?.name);
    }

    const updatedSession: ConversationSession = {
      ...targetSession,
      title: sessionTitle,
      messages: updatedMessages,
      updatedAt: Date.now(),
    };

    updateSession(updatedSession);
    setConversations(getStoredConversations());
    setAttachedFile(null);

    // Call backend
    try {
      const res = await chatMutation.mutateAsync({
        message: effectivePrompt,
        file,
        sessionId: targetSession.id,
      });
      let assistantContent = res.message || '';
      if (res.action === 'review_contract' && res.review?.summary) {
        assistantContent = res.review.summary;
      } else if (res.action === 'validate_invoice' && res.validation) {
        assistantContent = `Invoice validation completed for ${res.invoice?.contract_name || 'the submitted invoice'}. Result: ${res.validation.is_valid ? 'All values align with corporate contract rules.' : `Identified ${res.validation.issues?.length || 1} discrepancies.`}`;
      } else if (!assistantContent) {
        assistantContent = 'Here is the analysis based on your request:';
      }

      const assistantMessage: ChatMessageItem = {
        id: `msg_${Date.now()}_agent`,
        role: 'assistant',
        content: assistantContent,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        response: res,
        status: 'success',
      };

      const finalSession: ConversationSession = {
        ...updatedSession,
        messages: [...updatedMessages, assistantMessage],
        updatedAt: Date.now(),
      };

      updateSession(finalSession);
      setConversations(getStoredConversations());
    } catch (err: any) {
      const errorMessage: ChatMessageItem = {
        id: `msg_${Date.now()}_agent_err`,
        role: 'assistant',
        content: 'I encountered an error processing your request.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        status: 'error',
        errorMessage: err?.message || 'Failed to communicate with AI agent.',
      };

      const errorSession: ConversationSession = {
        ...updatedSession,
        messages: [...updatedMessages, errorMessage],
        updatedAt: Date.now(),
      };

      updateSession(errorSession);
      setConversations(getStoredConversations());
    }
  };

  const handleSaveContract = () => {
    handleSendMessage('Save this contract in the database', null);
  };

  const handleSaveInvoice = () => {
    handleSendMessage('Save this invoice details', null);
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: 'var(--bg-app)' }}>
      {/* 1. Left Sidebar with Conversation History */}
      <Sidebar
        conversations={conversations}
        activeSessionId={activeSessionId}
        onSelectSession={handleSelectSession}
        onNewChat={handleNewChat}
        onDeleteSession={handleDeleteSession}
        onRenameSession={handleRenameSession}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
      />

      {/* 2. Main Chat Workspace */}
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          minWidth: 0,
          height: '100vh',
          position: 'relative',
        }}
      >
        {/* Minimal ChatGPT/Gemini Top Header */}
        <TopHeader
          conversationTitle={activeSession?.title || ''}
          isSidebarCollapsed={isSidebarCollapsed}
          onToggleSidebar={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
          onNewChat={handleNewChat}
        />

        {/* Scrollable Conversation Stream */}
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            padding: '1.5rem 1.25rem 2rem',
          }}
        >
          <div
            style={{
              width: '100%',
              maxWidth: '840px',
              margin: '0 auto',
              display: 'flex',
              flexDirection: 'column',
              gap: '1.75rem',
              flex: 1,
            }}
          >
            {/* Empty State / Welcome Hero when no messages */}
            {messages.length === 0 && !chatMutation.isPending && (
              <WelcomeHero onSelectPrompt={(prompt) => handleSendMessage(prompt, null)} />
            )}

            {/* Conversation Messages Feed */}
            {messages.map((item) => (
              <ChatMessage
                key={item.id}
                message={item}
                onSaveContract={handleSaveContract}
                onSaveInvoice={handleSaveInvoice}
                isSaving={chatMutation.isPending}
              />
            ))}

            {/* Thinking / Analyzing Indicator during mutation */}
            {chatMutation.isPending && (
              <div
                className="animate-fadeIn"
                style={{
                  display: 'flex',
                  gap: '0.85rem',
                  alignItems: 'flex-start',
                  width: '100%',
                  maxWidth: '840px',
                  margin: '0 auto',
                }}
              >
                <div
                  style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: '10px',
                    background: 'linear-gradient(135deg, #0284c7 0%, #4f46e5 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#fff',
                    flexShrink: 0,
                  }}
                >
                  <Loader2 size={16} className="animate-spin" />
                </div>
                <div
                  style={{
                    backgroundColor: 'var(--bg-surface)',
                    border: '1px solid var(--border-app)',
                    borderRadius: 'var(--radius-md)',
                    padding: '0.85rem 1.2rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.65rem',
                    fontSize: '0.86rem',
                    color: 'var(--text-secondary)',
                  }}
                >
                  <span>{getThinkingStatusText()}</span>
                </div>
              </div>
            )}

            <div ref={chatBottomRef} style={{ height: '1px' }} />
          </div>
        </div>

        {/* 3. Floating Bottom Search / Prompt Bar with PDF & File Upload */}
        <ChatInput
          onSend={handleSendMessage}
          isLoading={chatMutation.isPending}
          attachedFile={attachedFile}
          onSelectFile={setAttachedFile}
        />
      </div>
    </div>
  );
}

export default App;
