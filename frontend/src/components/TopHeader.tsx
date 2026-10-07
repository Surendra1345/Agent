import React from 'react';
import { PanelLeft, Plus, Sparkles, ShieldCheck } from 'lucide-react';

interface TopHeaderProps {
  conversationTitle: string;
  isSidebarCollapsed: boolean;
  onToggleSidebar: () => void;
  onNewChat: () => void;
}

export const TopHeader: React.FC<TopHeaderProps> = ({
  conversationTitle,
  isSidebarCollapsed,
  onToggleSidebar,
  onNewChat,
}) => {
  return (
    <header
      style={{
        height: '54px',
        borderBottom: '1px solid var(--border-subtle)',
        backgroundColor: 'rgba(10, 12, 16, 0.85)',
        backdropFilter: 'blur(16px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 1.25rem',
        position: 'sticky',
        top: 0,
        zIndex: 30,
        flexShrink: 0,
      }}
    >
      {/* Left: Sidebar toggle (if collapsed) and Title / Model badge */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', minWidth: 0 }}>
        {isSidebarCollapsed && (
          <button
            type="button"
            onClick={onToggleSidebar}
            title="Open sidebar"
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
            <PanelLeft size={18} />
          </button>
        )}

        {/* Model Indicator Pill (Gemini/ChatGPT style) */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.45rem',
            backgroundColor: 'rgba(255, 255, 255, 0.04)',
            border: '1px solid var(--border-app)',
            padding: '0.28rem 0.65rem',
            borderRadius: '9999px',
            fontSize: '0.78rem',
            fontWeight: 600,
            color: 'var(--text-primary)',
          }}
        >
          <Sparkles size={13} color="#38bdf8" />
          <span>ContractAI</span>
          <span style={{ color: 'var(--text-dim)', fontSize: '0.7rem' }}>• Gemini Engine</span>
        </div>

        {/* Active Conversation Title */}
        {conversationTitle && (
          <div
            style={{
              fontSize: '0.82rem',
              color: 'var(--text-secondary)',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              maxWidth: '300px',
            }}
          >
            {conversationTitle}
          </div>
        )}
      </div>

      {/* Right: Quick actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.35rem',
            fontSize: '0.72rem',
            color: 'var(--text-dim)',
            padding: '0.25rem 0.5rem',
            borderRadius: '6px',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <ShieldCheck size={13} color="#10b981" />
          <span>Rulebook v4.2 Active</span>
        </div>

        <button
          type="button"
          onClick={onNewChat}
          title="New Chat"
          style={{
            background: 'rgba(255, 255, 255, 0.06)',
            border: '1px solid var(--border-app)',
            color: 'var(--text-primary)',
            cursor: 'pointer',
            padding: '0.35rem 0.75rem',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.78rem',
            fontWeight: 500,
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            transition: 'all 0.15s ease',
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
            e.currentTarget.style.borderColor = 'rgba(56, 189, 248, 0.4)';
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.06)';
            e.currentTarget.style.borderColor = 'var(--border-app)';
          }}
        >
          <Plus size={14} color="#38bdf8" />
          <span>New Chat</span>
        </button>
      </div>
    </header>
  );
};
