import React from 'react';
import { ShieldCheck, Sparkles, Database, FileText } from 'lucide-react';

interface NavbarProps {
  activeTab: 'chat' | 'explorer';
  setActiveTab: (tab: 'chat' | 'explorer') => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab }) => {
  return (
    <header style={{
      borderBottom: '1px solid var(--border-subtle)',
      background: 'rgba(7, 9, 14, 0.8)',
      backdropFilter: 'blur(12px)',
      position: 'sticky',
      top: 0,
      zIndex: 50,
      padding: '0.85rem 2rem',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
    }}>
      {/* Brand */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <div style={{
          background: 'var(--accent-gradient)',
          width: '38px',
          height: '38px',
          borderRadius: '10px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 0 15px rgba(99, 102, 241, 0.4)'
        }}>
          <ShieldCheck size={22} color="#fff" />
        </div>
        <div>
          <h1 style={{ fontSize: '1.15rem', fontWeight: 700, lineHeight: 1.2 }}>
            Contract<span style={{ color: '#818cf8' }}>AI</span> Review
          </h1>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <Sparkles size={11} color="#a855f7" /> RAG Policy Verification & DB Agent
          </span>
        </div>
      </div>

      {/* Nav Tabs */}
      <div style={{
        display: 'flex',
        background: 'rgba(255, 255, 255, 0.04)',
        padding: '0.25rem',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--border-subtle)',
        gap: '0.3rem'
      }}>
        <button
          onClick={() => setActiveTab('chat')}
          style={{
            background: activeTab === 'chat' ? 'var(--accent-primary)' : 'transparent',
            color: activeTab === 'chat' ? '#fff' : 'var(--text-muted)',
            border: 'none',
            padding: '0.45rem 1rem',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.85rem',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            transition: 'all 0.2s ease',
          }}
        >
          <FileText size={16} /> AI Review & Upload
        </button>
        <button
          onClick={() => setActiveTab('explorer')}
          style={{
            background: activeTab === 'explorer' ? 'var(--accent-primary)' : 'transparent',
            color: activeTab === 'explorer' ? '#fff' : 'var(--text-muted)',
            border: 'none',
            padding: '0.45rem 1rem',
            borderRadius: 'var(--radius-sm)',
            fontSize: '0.85rem',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            transition: 'all 0.2s ease',
          }}
        >
          <Database size={16} /> Database Explorer
        </button>
      </div>

      {/* System Status badge */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981', display: 'inline-block' }} />
        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 500 }}>PostgreSQL Connected</span>
      </div>
    </header>
  );
};
