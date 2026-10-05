import React from 'react';
import { Sparkles } from 'lucide-react';

interface WelcomeHeroProps {
  onSelectPrompt?: (prompt: string) => void;
}

export const WelcomeHero: React.FC<WelcomeHeroProps> = () => {
  return (
    <div
      className="animate-fadeIn"
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
        padding: '3rem 1.5rem 2rem',
        maxWidth: '780px',
        margin: '0 auto',
        width: '100%',
      }}
    >
      {/* Gemini Sparkle Orb Icon */}
      <div
        style={{
          width: '56px',
          height: '56px',
          borderRadius: '16px',
          background: 'linear-gradient(135deg, rgba(56, 189, 248, 0.2) 0%, rgba(99, 102, 241, 0.25) 100%)',
          border: '1px solid rgba(56, 189, 248, 0.35)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#38bdf8',
          marginBottom: '1.25rem',
          boxShadow: '0 0 28px rgba(56, 189, 248, 0.2)',
        }}
      >
        <Sparkles size={28} />
      </div>

      <h2
        style={{
          fontSize: '1.85rem',
          fontWeight: 700,
          letterSpacing: '-0.025em',
          color: '#f8fafc',
          marginBottom: '0.5rem',
        }}
      >
        How can I help you today?
      </h2>

      <p
        style={{
          fontSize: '0.92rem',
          color: 'var(--text-secondary)',
          maxWidth: '520px',
          lineHeight: '1.55',
          marginBottom: '2rem',
        }}
      >
        Upload contracts or invoices for compliance audits, cross-examine clauses, or query company records in natural language.
      </p>
    </div>
  );
};
