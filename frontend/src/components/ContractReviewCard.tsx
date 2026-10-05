import React, { useState } from 'react';
import {
  Sparkles,
  AlertTriangle,
  ShieldCheck,
  CheckCircle2,
  FileText,
  Copy,
  Check,
  ThumbsUp,
  ThumbsDown,
  Edit3,
  AlertCircle,
} from 'lucide-react';
import type { ChatResponse, ContractDetails, ReviewResponse, ReviewFlag } from '../types';

interface ContractReviewCardProps {
  data: ChatResponse;
  onSave: () => void;
  isSaving: boolean;
}

export const ContractReviewCard: React.FC<ContractReviewCardProps> = ({ data, onSave, isSaving }) => {
  const contract: ContractDetails | undefined = data.contract;
  const review: ReviewResponse | undefined = data.review;
  const isSaved = data.action === 'save_contract' || Boolean(data.save_result);
  const contractId = data.contract_id || contract?.contract_id || (data.save_result as any)?.contract_id;

  const isCompliant = review?.status?.toLowerCase() === 'compliant';
  const flags: ReviewFlag[] = review?.flags || [];

  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState<'up' | 'down' | null>(null);

  const formatCurrency = (val?: number | null) => {
    if (val === undefined || val === null) return 'N/A';
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(val);
  };

  const getSeverityBadge = (severity?: string) => {
    const sev = (severity || 'medium').toLowerCase();
    if (sev === 'high' || sev === 'critical') {
      return {
        bg: 'rgba(239, 68, 68, 0.15)',
        border: 'rgba(239, 68, 68, 0.35)',
        color: '#f87171',
      };
    }
    if (sev === 'medium') {
      return {
        bg: 'rgba(245, 158, 11, 0.15)',
        border: 'rgba(245, 158, 11, 0.35)',
        color: '#fbbf24',
      };
    }
    return {
      bg: 'rgba(56, 189, 248, 0.15)',
      border: 'rgba(56, 189, 248, 0.35)',
      color: '#38bdf8',
    };
  };

  const handleCopyAuditReport = () => {
    const lines = [
      `CONTRACT AUDIT REPORT: ${contract?.contract_name || 'Commercial Agreement'}`,
      `Status: ${review?.status || (isCompliant ? 'Compliant' : 'Review Complete')}`,
      `Contract Amount: ${formatCurrency(contract?.contract_amount)}`,
      `Tax Rate: ${contract?.tax_rate ? `${contract.tax_rate}%` : 'N/A'}`,
      `Effective: ${contract?.effective_date || 'N/A'} | Completion: ${contract?.completion_date || 'N/A'}`,
      '',
      `ANALYSIS SUMMARY:`,
      review?.summary || 'No summary provided.',
      '',
      `COMPLIANCE FLAGS (${flags.length}):`,
      ...flags.map(
        (f: any, i) =>
          `${i + 1}. [Rule ${f.rule_id || 'AUDIT'}] (${(f.severity || 'FLAG').toUpperCase()}) - ${f.issue || f.description || 'Compliance Flag'}\n   Current: ${f.contract_value || 'N/A'}\n   Required: ${f.required_value || 'N/A'}\n   Explanation: ${f.explanation || f.description || 'N/A'}`,
      ),
    ];

    navigator.clipboard.writeText(lines.join('\n'));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className="animate-fadeIn"
      style={{
        backgroundColor: 'var(--bg-surface)',
        border: '1px solid var(--border-app)',
        borderRadius: 'var(--radius-lg)',
        padding: '1.4rem 1.6rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '1.25rem',
      }}
    >
      {/* 1. Header Bar */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '0.8rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <div
            style={{
              width: '26px',
              height: '26px',
              borderRadius: '7px',
              background: 'linear-gradient(135deg, #38bdf8, #6366f1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
            }}
          >
            <Sparkles size={15} />
          </div>
          <span style={{ fontWeight: 700, fontSize: '0.94rem', color: 'var(--text-primary)' }}>
            Contract Legal Audit
          </span>
          <span
            style={{
              fontSize: '0.65rem',
              fontWeight: 700,
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
              padding: '2px 8px',
              borderRadius: '4px',
              backgroundColor: 'rgba(255, 255, 255, 0.06)',
              color: 'var(--text-muted)',
              border: '1px solid var(--border-subtle)',
            }}
          >
            {review?.status?.toUpperCase() || 'AUDIT COMPLETE'}
          </span>
          {contractId && (
            <span
              style={{
                fontSize: '0.68rem',
                fontFamily: 'var(--font-mono)',
                color: 'var(--text-dim)',
                background: 'rgba(255, 255, 255, 0.04)',
                padding: '2px 6px',
                borderRadius: '4px',
              }}
            >
              {contractId}
            </span>
          )}
        </div>

        {/* Exposure / Compliance Badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.4rem',
              padding: '0.28rem 0.75rem',
              borderRadius: '9999px',
              fontSize: '0.75rem',
              fontWeight: 600,
              backgroundColor: isCompliant ? 'var(--success-bg)' : 'var(--exposure-bg)',
              border: `1px solid ${isCompliant ? 'var(--success-border)' : 'var(--exposure-border)'}`,
              color: isCompliant ? 'var(--success-light)' : 'var(--exposure-color)',
            }}
          >
            {isCompliant ? <ShieldCheck size={14} /> : <AlertTriangle size={14} />}
            <span>{isCompliant ? 'Fully Compliant' : `${flags.length} Deviation Flag${flags.length === 1 ? '' : 's'}`}</span>
          </div>

          {isSaved && (
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.35rem',
                padding: '0.28rem 0.65rem',
                borderRadius: '9999px',
                fontSize: '0.72rem',
                fontWeight: 600,
                backgroundColor: 'rgba(56, 189, 248, 0.15)',
                border: '1px solid rgba(56, 189, 248, 0.3)',
                color: '#38bdf8',
              }}
            >
              <CheckCircle2 size={13} />
              <span>Saved in DB</span>
            </div>
          )}
        </div>
      </div>

      {/* 2. Contract Metadata Overview */}
      {contract && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))',
            gap: '0.75rem',
            padding: '0.85rem 1rem',
            backgroundColor: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            fontSize: '0.78rem',
          }}
        >
          <div>
            <div style={{ color: 'var(--text-dim)', fontSize: '0.68rem', fontWeight: 600, textTransform: 'uppercase' }}>
              Contract Name
            </div>
            <div style={{ color: 'var(--text-primary)', fontWeight: 600, marginTop: '2px' }}>
              {contract.contract_name || 'Standard Agreement'}
            </div>
          </div>

          <div>
            <div style={{ color: 'var(--text-dim)', fontSize: '0.68rem', fontWeight: 600, textTransform: 'uppercase' }}>
              Contract Value
            </div>
            <div style={{ color: '#38bdf8', fontWeight: 600, fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
              {formatCurrency(contract.contract_amount)}
            </div>
          </div>

          <div>
            <div style={{ color: 'var(--text-dim)', fontSize: '0.68rem', fontWeight: 600, textTransform: 'uppercase' }}>
              Tax Rate
            </div>
            <div style={{ color: 'var(--text-primary)', fontWeight: 600, marginTop: '2px' }}>
              {contract.tax_rate !== null && contract.tax_rate !== undefined ? `${contract.tax_rate}%` : 'N/A'}
            </div>
          </div>

          <div>
            <div style={{ color: 'var(--text-dim)', fontSize: '0.68rem', fontWeight: 600, textTransform: 'uppercase' }}>
              Effective & Completion
            </div>
            <div style={{ color: 'var(--text-secondary)', marginTop: '2px' }}>
              {contract.effective_date || '—'} → {contract.completion_date || '—'}
            </div>
          </div>
        </div>
      )}

      {/* 3. Analysis Summary */}
      <div style={{ fontSize: '0.86rem', lineHeight: '1.6', color: 'var(--text-primary)' }}>
        <span style={{ fontWeight: 700 }}>Analysis Summary: </span>
        <span>
          {review?.summary ||
            `Contract review completed for ${contract?.contract_name || 'commercial agreement'}. Terms evaluated against Corporate Rulebook standards.`}
        </span>
      </div>

      {/* 4. Real Flags List from Backend */}
      {flags.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-dim)' }}>
            Compliance Flags & Rulebook Deviations ({flags.length})
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {flags.map((flag: any, idx) => {
              const sev = getSeverityBadge(flag.severity);
              const issueTitle = flag.issue || flag.description || `Compliance Notice #${idx + 1}`;
              const ruleId = flag.rule_id || (flag.flag_id ? `F-${flag.flag_id}` : 'AUDIT');
              const severityText = (flag.severity || 'FLAG').toUpperCase();

              return (
                <div
                  key={idx}
                  style={{
                    backgroundColor: 'rgba(255, 255, 255, 0.02)',
                    border: '1px solid var(--border-app)',
                    borderRadius: 'var(--radius-md)',
                    padding: '1rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.65rem',
                  }}
                >
                  {/* Flag Header */}
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <AlertCircle size={16} color={sev.color} />
                      <span style={{ fontWeight: 600, fontSize: '0.84rem', color: 'var(--text-primary)' }}>
                        {issueTitle}
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      <span
                        style={{
                          fontSize: '0.68rem',
                          fontFamily: 'var(--font-mono)',
                          fontWeight: 600,
                          padding: '2px 7px',
                          borderRadius: '4px',
                          backgroundColor: 'rgba(255, 255, 255, 0.06)',
                          color: 'var(--text-secondary)',
                        }}
                      >
                        Rule {ruleId}
                      </span>
                      <span
                        style={{
                          fontSize: '0.68rem',
                          fontWeight: 700,
                          textTransform: 'uppercase',
                          padding: '2px 8px',
                          borderRadius: '4px',
                          backgroundColor: sev.bg,
                          border: `1px solid ${sev.border}`,
                          color: sev.color,
                        }}
                      >
                        {severityText}
                      </span>
                    </div>
                  </div>

                  {/* Values Comparison Grid */}
                  {(flag.contract_value || flag.required_value) && (
                    <div
                      style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                        gap: '0.65rem',
                        marginTop: '0.2rem',
                      }}
                    >
                      {flag.contract_value && (
                        <div
                          style={{
                            padding: '0.6rem 0.8rem',
                            backgroundColor: 'rgba(239, 68, 68, 0.08)',
                            border: '1px solid rgba(239, 68, 68, 0.25)',
                            borderRadius: 'var(--radius-sm)',
                          }}
                        >
                          <div style={{ fontSize: '0.65rem', fontWeight: 700, color: '#f87171', textTransform: 'uppercase', marginBottom: '2px' }}>
                            Draft Contract Value
                          </div>
                          <div style={{ fontSize: '0.8rem', color: '#fca5a5', fontFamily: 'var(--font-mono)' }}>
                            {flag.contract_value}
                          </div>
                        </div>
                      )}

                      {flag.required_value && (
                        <div
                          style={{
                            padding: '0.6rem 0.8rem',
                            backgroundColor: 'rgba(16, 185, 129, 0.08)',
                            border: '1px solid rgba(16, 185, 129, 0.25)',
                            borderRadius: 'var(--radius-sm)',
                          }}
                        >
                          <div style={{ fontSize: '0.65rem', fontWeight: 700, color: '#34d399', textTransform: 'uppercase', marginBottom: '2px' }}>
                            Required Rulebook Standard
                          </div>
                          <div style={{ fontSize: '0.8rem', color: '#6ee7b7', fontFamily: 'var(--font-mono)' }}>
                            {flag.required_value}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Explanation */}
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
                    {flag.explanation || flag.description || ''}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 5. Recommended Redline Revision Box (Dynamically generated from real flags) */}
      {flags.length > 0 && (
        <div
          style={{
            backgroundColor: 'rgba(10, 12, 16, 0.6)',
            border: '1px solid var(--border-app)',
            borderRadius: 'var(--radius-md)',
            padding: '1rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.75rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              <Edit3 size={14} color="#38bdf8" />
              <span>Recommended Redline Actions</span>
            </div>

            <button
              onClick={handleCopyAuditReport}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-muted)',
                fontSize: '0.75rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.3rem',
              }}
            >
              {copied ? <Check size={13} color="#10b981" /> : <Copy size={13} />}
              <span>{copied ? 'Copied Report' : 'Copy All'}</span>
            </button>
          </div>

          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '0.5rem',
              backgroundColor: 'rgba(0, 0, 0, 0.3)',
              padding: '0.85rem',
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.78rem',
              lineHeight: '1.6',
            }}
          >
            {flags.map((f: any, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}>
                <span style={{ color: '#38bdf8', fontWeight: 600 }}>
                  [Rule {f.rule_id || (f.flag_id ? `F-${f.flag_id}` : 'AUDIT')}]
                </span>
                <div>
                  {f.contract_value && (
                    <span className="diff-deletion" style={{ marginRight: '6px' }}>
                      {f.contract_value}
                    </span>
                  )}
                  {f.required_value && (
                    <span className="diff-addition" style={{ marginRight: '6px' }}>
                      {f.required_value}
                    </span>
                  )}
                  <span style={{ color: 'var(--text-secondary)' }}>
                    — {f.explanation || f.description || f.issue || 'Compliance rule review'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 6. Action Bar */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '0.8rem',
          paddingTop: '0.4rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          {!isSaved ? (
            <button
              onClick={onSave}
              disabled={isSaving}
              className="btn-action-primary"
            >
              <CheckCircle2 size={16} />
              <span>{isSaving ? 'Saving to Database...' : 'Accept Audit & Save to DB'}</span>
            </button>
          ) : (
            <div
              style={{
                fontSize: '0.82rem',
                color: '#10b981',
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                fontWeight: 600,
              }}
            >
              <CheckCircle2 size={16} />
              <span>Contract Stored in Database</span>
            </div>
          )}

          {contract?.file_url && (
            <a
              href={contract.file_url}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-action-secondary"
              style={{ textDecoration: 'none' }}
            >
              <FileText size={15} color="var(--text-muted)" />
              <span>Inspect Source PDF</span>
            </a>
          )}
        </div>

        {/* Feedback actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-dim)' }}>
          <button
            onClick={() => setFeedback('up')}
            title="Helpful"
            style={{
              background: feedback === 'up' ? 'rgba(16, 185, 129, 0.15)' : 'transparent',
              border: 'none',
              color: feedback === 'up' ? '#10b981' : 'inherit',
              cursor: 'pointer',
              padding: '6px',
              borderRadius: '4px',
            }}
          >
            <ThumbsUp size={14} />
          </button>
          <button
            onClick={() => setFeedback('down')}
            title="Unhelpful"
            style={{
              background: feedback === 'down' ? 'rgba(239, 68, 68, 0.15)' : 'transparent',
              border: 'none',
              color: feedback === 'down' ? '#ef4444' : 'inherit',
              cursor: 'pointer',
              padding: '6px',
              borderRadius: '4px',
            }}
          >
            <ThumbsDown size={14} />
          </button>
          <button
            title="Copy audit report"
            onClick={handleCopyAuditReport}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'inherit',
              cursor: 'pointer',
              padding: '6px',
              borderRadius: '4px',
            }}
          >
            <Copy size={14} />
          </button>
        </div>
      </div>
    </div>
  );
};
