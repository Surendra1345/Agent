import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
  fallbackMessage?: string;
  onReset?: () => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('[ErrorBoundary caught error]:', error, errorInfo);
  }

  private handleRetry = () => {
    this.setState({ hasError: false, error: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div
          className="animate-fadeIn"
          style={{
            backgroundColor: 'rgba(239, 68, 68, 0.08)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: 'var(--radius-md)',
            padding: '1.25rem 1.5rem',
            margin: '0.5rem 0',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.75rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', color: '#f87171' }}>
            <AlertTriangle size={20} />
            <span style={{ fontWeight: 600, fontSize: '0.92rem' }}>
              {this.props.fallbackTitle || 'Component Rendering Error'}
            </span>
          </div>

          <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>
            {this.props.fallbackMessage ||
              'A rendering issue occurred in this section. The rest of the workspace is unaffected.'}
          </p>

          {this.state.error && (
            <div
              style={{
                fontSize: '0.74rem',
                fontFamily: 'var(--font-mono)',
                backgroundColor: 'rgba(0, 0, 0, 0.35)',
                color: '#fca5a5',
                padding: '0.5rem 0.75rem',
                borderRadius: '4px',
                overflowX: 'auto',
              }}
            >
              {this.state.error.message || String(this.state.error)}
            </div>
          )}

          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.25rem' }}>
            <button
              type="button"
              onClick={this.handleRetry}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.4rem',
                backgroundColor: 'rgba(239, 68, 68, 0.2)',
                border: '1px solid rgba(239, 68, 68, 0.4)',
                borderRadius: 'var(--radius-sm)',
                padding: '0.35rem 0.75rem',
                color: '#fca5a5',
                fontSize: '0.78rem',
                fontWeight: 500,
                cursor: 'pointer',
              }}
            >
              <RefreshCw size={13} />
              <span>Retry Component</span>
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
