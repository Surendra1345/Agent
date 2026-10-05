import React, { useState } from 'react';
import {
  Sparkles,
  FileText,
  Copy,
  Check,
  Database,
  AlertCircle,
  ThumbsUp,
  ThumbsDown,
} from 'lucide-react';
import type { ChatMessageItem } from '../types/chat';
import { ContractReviewCard } from './ContractReviewCard';
import { InvoiceValidationCard } from './InvoiceValidationCard';
import { ErrorBoundary } from './ErrorBoundary';

interface ChatMessageProps {
  message: ChatMessageItem;
  onSaveContract?: () => void;
  onSaveInvoice?: () => void;
  isSaving?: boolean;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({
  message,
  onSaveContract,
  onSaveInvoice,
  isSaving = false,
}) => {
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState<'up' | 'down' | null>(null);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Helper to format basic markdown-style text (bold, bullet points, code ticks)
  const renderFormattedText = (text: string) => {
    if (!text) return null;
    const lines = text.split('\n');

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', lineHeight: '1.65' }}>
        {lines.map((line, lIdx) => {
          const trimmed = line.trim();
          if (!trimmed) {
            return <div key={lIdx} style={{ height: '0.25rem' }} />;
          }

          // Bullet points
          if (trimmed.startsWith('•') || trimmed.startsWith('-') || trimmed.startsWith('*')) {
            const cleanContent = trimmed.replace(/^[-*•]\s*/, '');
            return (
              <div key={lIdx} style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem', paddingLeft: '0.25rem' }}>
                <span style={{ color: '#38bdf8', fontSize: '0.85rem' }}>•</span>
                <span>{renderInlineFormatting(cleanContent)}</span>
              </div>
            );
          }

          // Numbered lists e.g. "1. "
          const numMatch = trimmed.match(/^(\d+)\.\s+(.*)/);
          if (numMatch) {
            return (
              <div key={lIdx} style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem', paddingLeft: '0.25rem' }}>
                <span style={{ color: '#38bdf8', fontWeight: 600, fontSize: '0.82rem' }}>{numMatch[1]}.</span>
                <span>{renderInlineFormatting(numMatch[2])}</span>
              </div>
            );
          }

          return <div key={lIdx}>{renderInlineFormatting(line)}</div>;
        })}
      </div>
    );
  };

  const renderInlineFormatting = (str: string) => {
    // Basic regex parser for **bold** and `code`
    const parts: React.ReactNode[] = [];
    let remaining = str;
    let keyIdx = 0;

    while (remaining.length > 0) {
      const boldMatch = remaining.match(/\*\*(.*?)\*\*/);
      const codeMatch = remaining.match(/`([^`]+)`/);

      let firstMatch: { type: 'bold' | 'code'; index: number; full: string; inner: string } | null = null;

      if (boldMatch && boldMatch.index !== undefined) {
        firstMatch = { type: 'bold', index: boldMatch.index, full: boldMatch[0], inner: boldMatch[1] };
      }

      if (codeMatch && codeMatch.index !== undefined) {
        if (!firstMatch || codeMatch.index < firstMatch.index) {
          firstMatch = { type: 'code', index: codeMatch.index, full: codeMatch[0], inner: codeMatch[1] };
        }
      }

      if (!firstMatch) {
        parts.push(<span key={keyIdx++}>{remaining}</span>);
        break;
      }

      if (firstMatch.index > 0) {
        parts.push(<span key={keyIdx++}>{remaining.substring(0, firstMatch.index)}</span>);
      }

      if (firstMatch.type === 'bold') {
        parts.push(
          <strong key={keyIdx++} style={{ fontWeight: 600, color: '#f8fafc' }}>
            {firstMatch.inner}
          </strong>,
        );
      } else {
        parts.push(
          <code
            key={keyIdx++}
            style={{
              backgroundColor: 'rgba(255, 255, 255, 0.07)',
              padding: '1px 5px',
              borderRadius: '4px',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.82em',
              color: '#38bdf8',
            }}
          >
            {firstMatch.inner}
          </code>,
        );
      }

      remaining = remaining.substring(firstMatch.index + firstMatch.full.length);
    }

    return parts;
  };

  const response = message.response;
  const hasContractCard =
    response &&
    (response.action === 'review_contract' || response.action === 'save_contract') &&
    Boolean(response.contract);
  const hasInvoiceCard =
    response &&
    (response.action === 'validate_invoice' || response.action === 'save_invoice') &&
    Boolean(response.invoice);
  const hasSqlResults = response && response.action === 'text_to_sql' && Boolean(response.results);

  return (
    <div
      className="animate-fadeIn"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '0.75rem',
        width: '100%',
        maxWidth: '840px',
        margin: '0 auto',
      }}
    >
      {isUser ? (
        /* User Message Turn (Right aligned / sleek user bubble) */
        <div style={{ display: 'flex', justifyContent: 'flex-end', width: '100%' }}>
          <div
            style={{
              maxWidth: '85%',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'flex-end',
              gap: '0.45rem',
            }}
          >
            {/* Attachment preview chip if a file was uploaded */}
            {message.attachment && (
              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.45rem',
                  backgroundColor: 'rgba(56, 189, 248, 0.08)',
                  border: '1px solid rgba(56, 189, 248, 0.25)',
                  padding: '0.35rem 0.75rem',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '0.75rem',
                  fontFamily: 'var(--font-mono)',
                  color: 'var(--text-primary)',
                }}
              >
                <FileText size={15} color="#38bdf8" />
                <span style={{ fontWeight: 500 }}>{message.attachment.name}</span>
                {message.attachment.size && (
                  <span style={{ color: 'var(--text-dim)', fontSize: '0.7rem' }}>
                    {message.attachment.size}
                  </span>
                )}
              </div>
            )}

            {/* Bubble */}
            <div
              style={{
                backgroundColor: 'var(--bg-surface-elevated)',
                border: '1px solid var(--border-app)',
                borderRadius: '18px 18px 4px 18px',
                padding: '0.85rem 1.15rem',
                color: '#f8fafc',
                fontSize: '0.9rem',
                lineHeight: '1.55',
                wordBreak: 'break-word',
                whiteSpace: 'pre-wrap',
                boxShadow: '0 2px 8px rgba(0, 0, 0, 0.2)',
              }}
            >
              {message.content}
            </div>

            <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', paddingRight: '0.3rem' }}>
              {message.timestamp}
            </div>
          </div>
        </div>
      ) : (
        /* Assistant Message Turn (Left aligned / Gemini style) */
        <div style={{ display: 'flex', gap: '0.85rem', width: '100%', alignItems: 'flex-start' }}>
          {/* Avatar */}
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
              boxShadow: '0 0 14px rgba(56, 189, 248, 0.25)',
              marginTop: '2px',
            }}
          >
            <Sparkles size={16} />
          </div>

          {/* Assistant Content Stream */}
          <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            {/* Header: Name and timestamp */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                ContractAI
              </span>
              <span style={{ fontSize: '0.68rem', color: 'var(--text-dim)' }}>
                {message.timestamp}
              </span>
            </div>

            {/* Error banner if any */}
            {message.errorMessage && (
              <div
                style={{
                  backgroundColor: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  borderRadius: 'var(--radius-md)',
                  padding: '0.75rem 0.9rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.6rem',
                  color: '#f87171',
                  fontSize: '0.82rem',
                }}
              >
                <AlertCircle size={16} />
                <span>{message.errorMessage}</span>
              </div>
            )}

            {/* Conversational Text Message */}
            {message.content && (
              <div
                style={{
                  fontSize: '0.88rem',
                  color: 'var(--text-primary)',
                  lineHeight: '1.65',
                }}
              >
                {renderFormattedText(message.content)}
              </div>
            )}

            {/* Contract Review Card */}
            {hasContractCard && response && (
              <div style={{ marginTop: '0.35rem' }}>
                <ErrorBoundary fallbackTitle="Contract Analysis Card Error" fallbackMessage="Could not display this contract card.">
                  <ContractReviewCard
                    data={response}
                    onSave={onSaveContract || (() => { })}
                    isSaving={isSaving}
                  />
                </ErrorBoundary>
              </div>
            )}

            {/* Invoice Validation Card */}
            {hasInvoiceCard && response && (
              <div style={{ marginTop: '0.35rem' }}>
                <ErrorBoundary fallbackTitle="Invoice Validation Card Error" fallbackMessage="Could not display this invoice card.">
                  <InvoiceValidationCard
                    data={response}
                    onSave={onSaveInvoice || (() => { })}
                    isSaving={isSaving}
                  />
                </ErrorBoundary>
              </div>
            )}

            {/* SQL Query Results Table */}
            {hasSqlResults && response && response.results && (
              <ErrorBoundary fallbackTitle="Database Records Error" fallbackMessage="Could not display query records.">
                <div
                  className="animate-fadeIn"
                  style={{
                    backgroundColor: 'var(--bg-surface)',
                    border: '1px solid var(--border-app)',
                    borderRadius: 'var(--radius-lg)',
                    padding: '1.25rem 1.4rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.85rem',
                    marginTop: '0.35rem',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#38bdf8', fontWeight: 600, fontSize: '0.86rem' }}>
                      <Database size={16} />
                      <span>Contract Database Records ({Array.isArray(response.results) ? response.results.length : 0} found)</span>
                    </div>
                  </div>

                  {Array.isArray(response.results) && response.results.length > 0 && typeof response.results[0] === 'object' && response.results[0] !== null ? (
                    <div style={{ overflowX: 'auto', borderRadius: '8px', border: '1px solid var(--border-app)' }}>
                      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem', textAlign: 'left' }}>
                        <thead>
                          <tr style={{ backgroundColor: 'rgba(255, 255, 255, 0.04)', color: 'var(--text-dim)', borderBottom: '1px solid var(--border-app)' }}>
                            {Object.keys(response.results[0] || {})
                              .filter((key) => key !== 'file_url')
                              .map((key) => {
                                const headerName =
                                  key === 'contract_id'
                                    ? 'Contract ID'
                                    : key === 'contract_name'
                                      ? 'Contract Title'
                                      : key === 'contract_amount'
                                        ? 'Contract Value'
                                        : key === 'tax_rate'
                                          ? 'Tax Rate'
                                          : key === 'start_date'
                                            ? 'Effective Date'
                                            : key === 'end_date'
                                              ? 'Completion Date'
                                              : key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
                                return (
                                  <th key={key} style={{ padding: '0.65rem 0.85rem', fontWeight: 600, whiteSpace: 'nowrap' }}>
                                    {headerName}
                                  </th>
                                );
                              })}
                          </tr>
                        </thead>
                        <tbody>
                          {response.results.map((row: any, idx: number) => (
                            <tr
                              key={idx}
                              style={{
                                borderBottom: '1px solid var(--border-subtle)',
                                backgroundColor: idx % 2 === 0 ? 'transparent' : 'rgba(255, 255, 255, 0.01)',
                              }}
                            >
                              {row && typeof row === 'object'
                                ? Object.entries(row)
                                  .filter(([key]) => key !== 'file_url')
                                  .map(([key, val]: [string, any], vIdx) => {
                                    let formatted: React.ReactNode = val !== null && val !== undefined ? String(val) : '—';
                                    if (key.includes('amount') && val !== null && val !== undefined) {
                                      const num = Number(val);
                                      if (!isNaN(num)) {
                                        formatted = (
                                          <span style={{ color: '#38bdf8', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
                                            {new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(num)}
                                          </span>
                                        );
                                      }
                                    } else if (key === 'tax_rate' && val !== null && val !== undefined) {
                                      formatted = <span style={{ fontWeight: 500 }}>{val}%</span>;
                                    } else if (key === 'contract_id' && val) {
                                      formatted = (
                                        <span
                                          style={{
                                            fontFamily: 'var(--font-mono)',
                                            fontSize: '0.72rem',
                                            backgroundColor: 'rgba(255, 255, 255, 0.05)',
                                            padding: '2px 6px',
                                            borderRadius: '4px',
                                            color: 'var(--text-secondary)',
                                          }}
                                        >
                                          {String(val)}
                                        </span>
                                      );
                                    } else if (key === 'contract_name' && val) {
                                      formatted = <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{String(val)}</span>;
                                    }

                                    return (
                                      <td key={vIdx} style={{ padding: '0.65rem 0.85rem', color: 'var(--text-primary)', whiteSpace: key === 'contract_name' ? 'normal' : 'nowrap' }}>
                                        {formatted}
                                      </td>
                                    );
                                  })
                                : null}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', fontStyle: 'italic', padding: '0.5rem 0' }}>
                      No matching records found in database.
                    </div>
                  )}

                  {/* Optional collapsed technical detail (hidden by default) */}
                  {response.generated_sql && (
                    <details style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: '0.25rem' }}>
                      <summary style={{ cursor: 'pointer', userSelect: 'none', color: 'var(--text-dim)' }}>
                        Technical details (SQL)
                      </summary>
                      <div
                        style={{
                          marginTop: '0.35rem',
                          padding: '0.5rem 0.75rem',
                          backgroundColor: 'rgba(0, 0, 0, 0.35)',
                          borderRadius: '4px',
                          fontFamily: 'var(--font-mono)',
                          fontSize: '0.74rem',
                          color: 'var(--text-muted)',
                        }}
                      >
                        <code>{response.generated_sql}</code>
                      </div>
                    </details>
                  )}
                </div>
              </ErrorBoundary>
            )}

            {/* Assistant Action Bar (Copy text, Feedback) */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.2rem' }}>
              <button
                type="button"
                onClick={() => handleCopy(message.content)}
                title="Copy response"
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-dim)',
                  cursor: 'pointer',
                  padding: '4px 6px',
                  borderRadius: '4px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.3rem',
                  fontSize: '0.72rem',
                }}
                onMouseOver={(e) => (e.currentTarget.style.color = 'var(--text-primary)')}
                onMouseOut={(e) => (e.currentTarget.style.color = 'var(--text-dim)')}
              >
                {copied ? <Check size={13} color="#10b981" /> : <Copy size={13} />}
                <span>{copied ? 'Copied' : 'Copy'}</span>
              </button>

              <button
                type="button"
                onClick={() => setFeedback(feedback === 'up' ? null : 'up')}
                title="Good response"
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: feedback === 'up' ? '#10b981' : 'var(--text-dim)',
                  cursor: 'pointer',
                  padding: '4px 6px',
                  borderRadius: '4px',
                }}
              >
                <ThumbsUp size={13} />
              </button>

              <button
                type="button"
                onClick={() => setFeedback(feedback === 'down' ? null : 'down')}
                title="Bad response"
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: feedback === 'down' ? '#ef4444' : 'var(--text-dim)',
                  cursor: 'pointer',
                  padding: '4px 6px',
                  borderRadius: '4px',
                }}
              >
                <ThumbsDown size={13} />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
