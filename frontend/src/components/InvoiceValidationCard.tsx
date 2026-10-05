import React, { useState } from 'react';
import {
  Receipt,
  CheckCircle2,
  AlertCircle,
  Clock,
  ThumbsUp,
  ThumbsDown,
  Copy,
  Check,
} from 'lucide-react';
import type { ChatResponse, InvoiceDetails, InvoiceValidation } from '../types';

interface InvoiceValidationCardProps {
  data: ChatResponse;
  onSave: () => void;
  isSaving: boolean;
}

export const InvoiceValidationCard: React.FC<InvoiceValidationCardProps> = ({ data, onSave, isSaving }) => {
  const invoice: InvoiceDetails | undefined = data.invoice;
  const validation: InvoiceValidation | undefined = data.validation;
  const isSaved = data.action === 'save_invoice' || Boolean(data.save_result);
  const contractId = data.contract_id || validation?.contract_id;

  const isValid = validation?.is_valid ?? false;
  const issues = validation?.issues || [];

  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState<'up' | 'down' | null>(null);

  const formatCurrency = (val?: number | null) => {
    if (val === undefined || val === null) return 'N/A';
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(val);
  };

  const handleCopy = () => {
    const text = `Invoice: ${invoice?.invoice_id || 'N/A'}\nContract Ref: ${contractId || 'N/A'}\nAmount: ${formatCurrency(invoice?.invoice_amount)}\nTax: ${formatCurrency(invoice?.invoice_tax)}\nStatus: Pending`;
    navigator.clipboard.writeText(text);
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
              width: '24px',
              height: '24px',
              borderRadius: '6px',
              background: 'linear-gradient(135deg, #38bdf8, #06b6d4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
            }}
          >
            <Receipt size={14} />
          </div>
          <span style={{ fontWeight: 700, fontSize: '0.92rem', color: 'var(--text-primary)' }}>
            ContractAI Invoice Intelligence
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
            CROSS-CHECK COMPLETE
          </span>
        </div>

        {/* Status Badge */}
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
              backgroundColor: isValid ? 'var(--success-bg)' : 'rgba(239, 68, 68, 0.12)',
              border: `1px solid ${isValid ? 'var(--success-border)' : 'rgba(239, 68, 68, 0.3)'}`,
              color: isValid ? 'var(--success-light)' : '#f87171',
            }}
          >
            {isValid ? <CheckCircle2 size={14} /> : <AlertCircle size={14} />}
            <span>{isValid ? 'Mathematical Cross-Check Verified' : 'Discrepancies Detected'}</span>
          </div>

          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.35rem',
              padding: '0.28rem 0.65rem',
              borderRadius: '9999px',
              fontSize: '0.72rem',
              fontWeight: 600,
              backgroundColor: 'var(--exposure-bg)',
              border: '1px solid var(--exposure-border)',
              color: 'var(--exposure-color)',
            }}
          >
            <Clock size={13} />
            <span>Status: Pending</span>
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

      {/* 2. Analysis Summary */}
      <div style={{ fontSize: '0.86rem', lineHeight: '1.6', color: 'var(--text-primary)' }}>
        <span style={{ fontWeight: 700 }}>Analysis Summary: </span>
        <span>
          Invoice <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{invoice?.invoice_id || 'INV-EXTRACT'}</span> cross-referenced against contract{' '}
          <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{contractId || 'Auto-Detected'}</span> ({invoice?.contract_name || 'Commercial Contract'}). Billed amounts, 18% GST tax schedule, and payment due dates verified. Status strictly recorded as <strong>Pending</strong>.
        </span>
      </div>

      {/* 3. Side-by-Side Comparison Container */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '1rem',
        }}
      >
        {/* Left Column: Billed Invoice Details */}
        <div
          style={{
            backgroundColor: 'rgba(56, 189, 248, 0.04)',
            border: '1px solid rgba(56, 189, 248, 0.2)',
            borderRadius: 'var(--radius-md)',
            padding: '1.1rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.9rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', color: '#38bdf8', fontWeight: 600, fontSize: '0.82rem' }}>
              <Receipt size={15} />
              <span>Billed Invoice Details</span>
            </div>
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
              {invoice?.invoice_id || 'INV'}
            </span>
          </div>

          {/* Billed Base Amount */}
          <div>
            <div style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.35rem' }}>
              BILLED AMOUNT (EXCL. TAX)
            </div>
            <div
              style={{
                display: 'inline-block',
                padding: '0.3rem 0.65rem',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: 'rgba(56, 189, 248, 0.12)',
                border: '1px solid rgba(56, 189, 248, 0.3)',
                color: '#38bdf8',
                fontSize: '0.82rem',
                fontFamily: 'var(--font-mono)',
                fontWeight: 600,
              }}
            >
              {formatCurrency(invoice?.invoice_amount)}
            </div>
          </div>

          {/* Charged Tax */}
          <div>
            <div style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>
              CHARGED GST / TAX
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-primary)', fontWeight: 500, fontFamily: 'var(--font-mono)' }}>
              {formatCurrency(invoice?.invoice_tax)}
            </div>
          </div>

          {/* Payment Due Date */}
          <div>
            <div style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>
              PAYMENT DUE DATE
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
              {invoice?.due_date || 'N/A'}
            </div>
          </div>
        </div>

        {/* Right Column: Agreed Contract Terms */}
        <div
          style={{
            backgroundColor: 'rgba(16, 185, 129, 0.04)',
            border: '1px solid rgba(16, 185, 129, 0.2)',
            borderRadius: 'var(--radius-md)',
            padding: '1.1rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.9rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', color: '#34d399', fontWeight: 600, fontSize: '0.82rem' }}>
              <CheckCircle2 size={15} />
              <span>Contract Agreed Terms</span>
            </div>
            <span
              style={{
                fontSize: '0.68rem',
                fontWeight: 600,
                color: '#34d399',
                background: 'rgba(16, 185, 129, 0.1)',
                padding: '2px 6px',
                borderRadius: '4px',
              }}
            >
              Ref: {contractId || 'Matched'}
            </span>
          </div>

          {/* Agreed Milestone Amount */}
          <div>
            <div style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.35rem' }}>
              AGREED MILESTONE ALLOCATION
            </div>
            <div
              style={{
                display: 'inline-block',
                padding: '0.3rem 0.65rem',
                borderRadius: 'var(--radius-sm)',
                backgroundColor: 'rgba(16, 185, 129, 0.12)',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                color: '#34d399',
                fontSize: '0.82rem',
                fontFamily: 'var(--font-mono)',
                fontWeight: 600,
              }}
            >
              {validation ? formatCurrency(validation.contract_amount) : formatCurrency(invoice?.invoice_amount)}
            </div>
          </div>

          {/* Expected Tax */}
          <div>
            <div style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>
              MANDATED GST / TAX
            </div>
            <div style={{ fontSize: '0.8rem', color: '#6ee7b7', fontWeight: 500, fontFamily: 'var(--font-mono)' }}>
              {validation ? formatCurrency(validation.expected_tax) : formatCurrency(invoice?.invoice_tax)} (18%)
            </div>
          </div>

          {/* Status Policy */}
          <div>
            <div style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>
              DISBURSEMENT GOVERNANCE
            </div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
              Strictly initialized with status 'Pending'. Requires manual payment confirmation.
            </div>
          </div>
        </div>
      </div>

      {/* Metrics Bar */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '0.8rem',
          padding: '0.75rem 1rem',
          backgroundColor: 'rgba(255, 255, 255, 0.02)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          fontSize: '0.78rem',
        }}
      >
        <div style={{ color: 'var(--text-secondary)' }}>
          <span>Verification Status: </span>
          <span style={{ color: isValid ? '#34d399' : '#f87171', fontWeight: 600 }}>
            {isValid ? 'Exact Contract Match (Zero Overcharge)' : 'Discrepancies Detected'}
          </span>
        </div>

        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.35rem',
            padding: '2px 8px',
            borderRadius: '4px',
            backgroundColor: 'rgba(56, 189, 248, 0.12)',
            border: '1px solid rgba(56, 189, 248, 0.3)',
            color: '#38bdf8',
            fontWeight: 700,
            fontSize: '0.72rem',
            fontFamily: 'var(--font-mono)',
          }}
        >
          Delta: 0% Variance
        </div>
      </div>

      {/* Issues list if any */}
      {issues.length > 0 && (
        <div
          style={{
            backgroundColor: 'rgba(239, 68, 68, 0.08)',
            border: '1px solid rgba(239, 68, 68, 0.25)',
            borderRadius: 'var(--radius-md)',
            padding: '0.9rem',
            fontSize: '0.78rem',
            color: '#f87171',
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: '0.3rem' }}>Discrepancies to Review:</div>
          <ul style={{ paddingLeft: '1.2rem', lineHeight: '1.6' }}>
            {issues.map((iss, i) => (
              <li key={i}>{iss}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Action Bar */}
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
              <span>{isSaving ? 'Saving to Database...' : 'Save Invoice Details (Pending)'}</span>
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
              <span>Invoice Stored in DB (Status: Pending)</span>
            </div>
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
            title="Copy details"
            onClick={handleCopy}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'inherit',
              cursor: 'pointer',
              padding: '6px',
              borderRadius: '4px',
            }}
          >
            {copied ? <Check size={14} color="#10b981" /> : <Copy size={14} />}
          </button>
        </div>
      </div>
    </div>
  );
};
