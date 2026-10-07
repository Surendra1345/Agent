import React, { useState } from 'react';
import {
  Plus,
  MessageSquare,
  PanelLeftClose,
  PanelLeftOpen,
  Sparkles,
  Trash2,
  Edit2,
  Check,
  X,
} from 'lucide-react';
import type { ConversationSession } from '../types/chat';
import { groupConversationsByDate } from '../services/conversationStorage';

interface SidebarProps {
  conversations: ConversationSession[];
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
  onDeleteSession: (id: string) => void;
  onRenameSession: (id: string, newTitle: string) => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  conversations,
  activeSessionId,
  onSelectSession,
  onNewChat,
  onDeleteSession,
  onRenameSession,
  isCollapsed,
  onToggleCollapse,
}) => {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');

  const grouped = groupConversationsByDate(conversations);

  const startEditing = (id: string, currentTitle: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingId(id);
    setEditTitle(currentTitle);
  };

  const handleSaveRename = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (editTitle.trim()) {
      onRenameSession(id, editTitle.trim());
    }
    setEditingId(null);
  };

  const handleCancelRename = (e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingId(null);
  };

  return (
    <aside
      style={{
        width: isCollapsed ? '64px' : '260px',
        backgroundColor: 'var(--bg-sidebar)',
        borderRight: '1px solid var(--border-app)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        flexShrink: 0,
        transition: 'width 0.2s ease',
        overflow: 'hidden',
        height: '100vh',
        position: 'sticky',
        top: 0,
        zIndex: 40,
      }}
    >
      {/* Upper Area: Brand, New Chat, & History */}
      <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 65px)', overflow: 'hidden' }}>
        {/* Brand & Toggle Header */}
        <div
          style={{
            padding: '1rem 0.85rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid var(--border-subtle)',
            flexShrink: 0,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', overflow: 'hidden' }}>
            <div
              style={{
                width: '30px',
                height: '30px',
                borderRadius: '8px',
                background: 'linear-gradient(135deg, #38bdf8 0%, #6366f1 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#fff',
                boxShadow: '0 0 12px rgba(56, 189, 248, 0.35)',
                flexShrink: 0,
              }}
            >
              <Sparkles size={17} />
            </div>
            {!isCollapsed && (
              <span style={{ fontWeight: 700, fontSize: '1.02rem', letterSpacing: '-0.02em', color: '#fff', whiteSpace: 'nowrap' }}>
                Contract<span style={{ color: '#38bdf8' }}>AI</span>
              </span>
            )}
          </div>

          <button
            type="button"
            onClick={onToggleCollapse}
            title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '6px',
              borderRadius: '6px',
            }}
            onMouseOver={(e) => (e.currentTarget.style.color = 'var(--text-primary)')}
            onMouseOut={(e) => (e.currentTarget.style.color = 'var(--text-muted)')}
          >
            {isCollapsed ? <PanelLeftOpen size={18} /> : <PanelLeftClose size={18} />}
          </button>
        </div>

        {/* New Chat Button */}
        <div style={{ padding: '0.75rem 0.75rem 0.4rem', flexShrink: 0 }}>
          <button
            type="button"
            onClick={onNewChat}
            title="Start a new conversation"
            style={{
              width: '100%',
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid var(--border-app)',
              borderRadius: 'var(--radius-md)',
              padding: isCollapsed ? '0.65rem 0' : '0.6rem 0.85rem',
              color: '#f8fafc',
              fontSize: '0.84rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: isCollapsed ? 'center' : 'flex-start',
              gap: '0.6rem',
              transition: 'all 0.15s ease',
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.08)';
              e.currentTarget.style.borderColor = 'rgba(56, 189, 248, 0.4)';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
              e.currentTarget.style.borderColor = 'var(--border-app)';
            }}
          >
            <Plus size={17} color="#38bdf8" />
            {!isCollapsed && <span>New chat</span>}
          </button>
        </div>

        {/* Conversation History List */}
        {!isCollapsed ? (
          <div
            style={{
              flex: 1,
              overflowY: 'auto',
              padding: '0.5rem 0.65rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem',
            }}
          >
            {grouped.length === 0 ? (
              <div
                style={{
                  textAlign: 'center',
                  padding: '2.5rem 1rem',
                  color: 'var(--text-dim)',
                  fontSize: '0.78rem',
                }}
              >
                No previous conversations yet. Start a new chat below.
              </div>
            ) : (
              grouped.map((group) => (
                <div key={group.group} style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                  {/* Category Header */}
                  <div
                    style={{
                      fontSize: '0.68rem',
                      fontWeight: 700,
                      letterSpacing: '0.05em',
                      color: 'var(--text-dim)',
                      textTransform: 'uppercase',
                      padding: '0.4rem 0.5rem 0.25rem',
                    }}
                  >
                    {group.group}
                  </div>

                  {/* Sessions in group */}
                  {group.sessions.map((session) => {
                    const isActive = activeSessionId === session.id;
                    const isEditing = editingId === session.id;

                    return (
                      <div
                        key={session.id}
                        onClick={() => !isEditing && onSelectSession(session.id)}
                        className="group"
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          gap: '0.5rem',
                          padding: '0.45rem 0.6rem',
                          borderRadius: 'var(--radius-sm)',
                          fontSize: '0.8rem',
                          fontWeight: isActive ? 600 : 400,
                          color: isActive ? '#fff' : 'var(--text-secondary)',
                          backgroundColor: isActive ? 'rgba(56, 189, 248, 0.12)' : 'transparent',
                          border: isActive ? '1px solid rgba(56, 189, 248, 0.25)' : '1px solid transparent',
                          cursor: 'pointer',
                          transition: 'all 0.15s ease',
                          position: 'relative',
                        }}
                        onMouseOver={(e) => {
                          if (!isActive) e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.04)';
                        }}
                        onMouseOut={(e) => {
                          if (!isActive) e.currentTarget.style.backgroundColor = 'transparent';
                        }}
                      >
                        {isEditing ? (
                          <div
                            style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', width: '100%' }}
                            onClick={(e) => e.stopPropagation()}
                          >
                            <input
                              type="text"
                              value={editTitle}
                              onChange={(e) => setEditTitle(e.target.value)}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') handleSaveRename(session.id, e as any);
                                if (e.key === 'Escape') setEditingId(null);
                              }}
                              autoFocus
                              style={{
                                flex: 1,
                                background: 'rgba(0, 0, 0, 0.5)',
                                border: '1px solid #38bdf8',
                                borderRadius: '4px',
                                color: '#fff',
                                padding: '2px 6px',
                                fontSize: '0.78rem',
                                outline: 'none',
                              }}
                            />
                            <button
                              type="button"
                              onClick={(e) => handleSaveRename(session.id, e)}
                              style={{ background: 'transparent', border: 'none', color: '#10b981', cursor: 'pointer', padding: '2px' }}
                            >
                              <Check size={13} />
                            </button>
                            <button
                              type="button"
                              onClick={handleCancelRename}
                              style={{ background: 'transparent', border: 'none', color: 'var(--text-dim)', cursor: 'pointer', padding: '2px' }}
                            >
                              <X size={13} />
                            </button>
                          </div>
                        ) : (
                          <>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', overflow: 'hidden', flex: 1 }}>
                              <MessageSquare
                                size={14}
                                color={isActive ? '#38bdf8' : 'var(--text-dim)'}
                                style={{ flexShrink: 0 }}
                              />
                              <span
                                style={{
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis',
                                  whiteSpace: 'nowrap',
                                }}
                              >
                                {session.title}
                              </span>
                            </div>

                            {/* Actions on hover or active */}
                            <div
                              style={{
                                display: isActive ? 'flex' : 'none',
                                alignItems: 'center',
                                gap: '2px',
                                flexShrink: 0,
                              }}
                            >
                              <button
                                type="button"
                                onClick={(e) => startEditing(session.id, session.title, e)}
                                title="Rename chat"
                                style={{
                                  background: 'transparent',
                                  border: 'none',
                                  color: 'var(--text-dim)',
                                  cursor: 'pointer',
                                  padding: '2px',
                                  borderRadius: '3px',
                                }}
                                onMouseOver={(e) => (e.currentTarget.style.color = 'var(--text-primary)')}
                                onMouseOut={(e) => (e.currentTarget.style.color = 'var(--text-dim)')}
                              >
                                <Edit2 size={12} />
                              </button>

                              <button
                                type="button"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  onDeleteSession(session.id);
                                }}
                                title="Delete chat"
                                style={{
                                  background: 'transparent',
                                  border: 'none',
                                  color: 'var(--text-dim)',
                                  cursor: 'pointer',
                                  padding: '2px',
                                  borderRadius: '3px',
                                }}
                                onMouseOver={(e) => (e.currentTarget.style.color = '#ef4444')}
                                onMouseOut={(e) => (e.currentTarget.style.color = 'var(--text-dim)')}
                              >
                                <Trash2 size={12} />
                              </button>
                            </div>
                          </>
                        )}
                      </div>
                    );
                  })}
                </div>
              ))
            )}
          </div>
        ) : (
          /* Collapsed Mini History Icons */
          <div
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              padding: '0.5rem 0',
              gap: '0.5rem',
            }}
          >
            {conversations.slice(0, 8).map((session) => (
              <button
                key={session.id}
                type="button"
                onClick={() => onSelectSession(session.id)}
                title={session.title}
                style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '8px',
                  background: activeSessionId === session.id ? 'rgba(56, 189, 248, 0.15)' : 'transparent',
                  border: activeSessionId === session.id ? '1px solid rgba(56, 189, 248, 0.35)' : 'none',
                  color: activeSessionId === session.id ? '#38bdf8' : 'var(--text-dim)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <MessageSquare size={16} />
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Footer Area: System status / DB connection */}
      <div
        style={{
          padding: isCollapsed ? '0.8rem 0' : '0.8rem 0.9rem',
          borderTop: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: isCollapsed ? 'center' : 'space-between',
          fontSize: '0.72rem',
          color: 'var(--text-dim)',
          flexShrink: 0,
        }}
      >
        {!isCollapsed ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span
              style={{
                width: '7px',
                height: '7px',
                borderRadius: '50%',
                backgroundColor: '#10b981',
                boxShadow: '0 0 8px #10b981',
              }}
            />
            <span>Agent Engine Online</span>
          </div>
        ) : (
          <span
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: '#10b981',
              boxShadow: '0 0 8px #10b981',
            }}
          />
        )}
      </div>
    </aside>
  );
};
