import React from 'react';
import { FileText } from 'lucide-react';

interface UserQueryCardProps {
  userName?: string;
  timestamp?: string;
  fileName?: string;
  fileSize?: string;
  prompt: string;
}

export const UserQueryCard: React.FC<UserQueryCardProps> = ({
  userName = 'Marcus Vance',
  timestamp = '11:42 AM',
  fileName,
  fileSize,
  prompt,
}) => {
  return (
    <div
      className="animate-fadeIn"
      style={{
        backgroundColor: 'var(--bg-surface)',
        border: '1px solid var(--border-app)',
        borderRadius: 'var(--radius-lg)',
        padding: '1.25rem 1.4rem',
        marginBottom: '1.5rem',
      }}
    >
      {/* Header: User meta */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.85rem' }}>
        <div
          style={{
            width: '24px',
            height: '24px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #1e293b, #334155)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '0.68rem',
            color: '#38bdf8',
            fontWeight: 600,
          }}
        >
          MV
        </div>
        <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>
          {userName}
        </span>
        <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>•</span>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
          {timestamp}
        </span>
      </div>

      {/* Document attachment pills */}
      {fileName && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.9rem' }}>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.45rem',
              backgroundColor: 'rgba(255, 255, 255, 0.04)',
              border: '1px solid var(--border-app)',
              padding: '0.35rem 0.75rem',
              borderRadius: 'var(--radius-md)',
              fontSize: '0.75rem',
              fontFamily: 'var(--font-mono)',
              color: 'var(--text-primary)',
            }}
          >
            <FileText size={14} color="#38bdf8" />
            <span style={{ fontWeight: 500 }}>{fileName}</span>
            {fileSize && (
              <span style={{ color: 'var(--text-dim)', fontSize: '0.7rem' }}>
                {fileSize}
              </span>
            )}
          </div>
        </div>
      )}

      {/* User prompt text */}
      <div
        style={{
          fontSize: '0.88rem',
          lineHeight: '1.6',
          color: 'var(--text-primary)',
          fontWeight: 400,
        }}
      >
        {prompt}
      </div>
    </div>
  );
};
