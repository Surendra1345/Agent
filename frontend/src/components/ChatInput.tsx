import React, { useState, useRef, useEffect } from 'react';
import { Paperclip, ArrowUp, X, FileText, Loader2 } from 'lucide-react';

interface ChatInputProps {
  onSend: (message: string, file: File | null) => void;
  isLoading: boolean;
  attachedFile: File | null;
  onSelectFile: (file: File | null) => void;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSend,
  isLoading,
  attachedFile,
  onSelectFile,
}) => {
  const [message, setMessage] =  useState('');
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea based on content
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  }, [message]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if ((!message.trim() && !attachedFile) || isLoading) return;

    onSend(message.trim(), attachedFile);
    setMessage('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleFileChange = (file: File | null) => {
    if (file) {
      onSelectFile(file);
    }
  };

  const canSubmit = Boolean(message.trim() || attachedFile) && !isLoading;

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div
      style={{
        position: 'sticky',
        bottom: 0,
        width: '100%',
        maxWidth: '840px',
        margin: '0 auto',
        padding: '0.75rem 1.25rem 1.25rem',
        background: 'linear-gradient(to top, var(--bg-app) 80%, transparent)',
        zIndex: 20,
      }}
    >
      {/* Outer Input Box with drag & drop */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          if (e.dataTransfer.files?.[0]) handleFileChange(e.dataTransfer.files[0]);
        }}
        style={{
          backgroundColor: 'var(--bg-surface-elevated)',
          border: isDragging ? '1.5px dashed #38bdf8' : '1px solid var(--border-app)',
          borderRadius: '24px',
          padding: '0.65rem 0.85rem 0.65rem 1rem',
          boxShadow: isDragging
            ? '0 0 20px rgba(56, 189, 248, 0.25)'
            : '0 8px 32px rgba(0, 0, 0, 0.45)',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.45rem',
          transition: 'all 0.2s ease',
        }}
      >
        {/* Attached File Preview Chip */}
        {attachedFile && (
          <div
            className="animate-fadeIn"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              backgroundColor: 'rgba(56, 189, 248, 0.1)',
              border: '1px solid rgba(56, 189, 248, 0.3)',
              padding: '0.3rem 0.75rem',
              borderRadius: 'var(--radius-md)',
              fontSize: '0.76rem',
              color: 'var(--text-primary)',
              fontFamily: 'var(--font-mono)',
              alignSelf: 'flex-start',
            }}
          >
            <FileText size={15} color="#38bdf8" />
            <span style={{ fontWeight: 600 }}>{attachedFile.name}</span>
            <span style={{ color: 'var(--text-dim)', fontSize: '0.7rem' }}>
              ({formatFileSize(attachedFile.size)})
            </span>
            <button
              type="button"
              onClick={() => onSelectFile(null)}
              title="Remove file"
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                padding: '2px',
                borderRadius: '50%',
                marginLeft: '4px',
              }}
              onMouseOver={(e) => (e.currentTarget.style.color = '#ef4444')}
              onMouseOut={(e) => (e.currentTarget.style.color = 'var(--text-muted)')}
            >
              <X size={14} />
            </button>
          </div>
        )}

        {/* Input Controls Row */}
        <form
          onSubmit={handleSubmit}
          style={{
            display: 'flex',
            alignItems: 'flex-end',
            gap: '0.65rem',
            width: '100%',
          }}
        >
          {/* File attach input & button */}
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.doc,.docx,.txt"
            style={{ display: 'none' }}
            onChange={(e) => handleFileChange(e.target.files?.[0] || null)}
          />

          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            title="Upload file or PDF"
            style={{
              background: attachedFile ? 'rgba(56, 189, 248, 0.15)' : 'rgba(255, 255, 255, 0.05)',
              border: '1px solid var(--border-subtle)',
              color: attachedFile ? '#38bdf8' : 'var(--text-secondary)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '34px',
              height: '34px',
              borderRadius: '50%',
              flexShrink: 0,
              marginBottom: '2px',
              transition: 'all 0.15s ease',
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
              e.currentTarget.style.color = '#38bdf8';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.backgroundColor = attachedFile ? 'rgba(56, 189, 248, 0.15)' : 'rgba(255, 255, 255, 0.05)';
              e.currentTarget.style.color = attachedFile ? '#38bdf8' : 'var(--text-secondary)';
            }}
          >
            <Paperclip size={17} />
          </button>

          {/* Auto-expanding Multiline Textarea */}
          <textarea
            ref={textareaRef}
            rows={1}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              attachedFile
                ? `Ask anything about ${attachedFile.name}...`
                : 'Ask ContractAI or upload a PDF to review...'
            }
            disabled={isLoading}
            style={{
              flex: 1,
              background: 'transparent',
              border: 'none',
              outline: 'none',
              color: 'var(--text-primary)',
              fontSize: '0.92rem',
              fontFamily: 'inherit',
              resize: 'none',
              lineHeight: '1.5',
              maxHeight: '180px',
              padding: '6px 0',
            }}
          />

          {/* Circular Up Arrow Send Button (ChatGPT/Gemini Style) */}
          <button
            type="submit"
            disabled={!canSubmit}
            title="Send message"
            style={{
              width: '34px',
              height: '34px',
              borderRadius: '50%',
              backgroundColor: canSubmit ? '#ffffff' : 'rgba(255, 255, 255, 0.08)',
              color: canSubmit ? '#0a0c10' : 'rgba(255, 255, 255, 0.25)',
              border: 'none',
              cursor: canSubmit ? 'pointer' : 'not-allowed',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.18s ease',
              flexShrink: 0,
              marginBottom: '2px',
              boxShadow: canSubmit ? '0 0 12px rgba(255, 255, 255, 0.3)' : 'none',
            }}
          >
            {isLoading ? (
              <Loader2 size={16} className="animate-spin" color="#38bdf8" />
            ) : (
              <ArrowUp size={18} strokeWidth={2.6} />
            )}
          </button>
        </form>
      </div>

      {/* Subtle Gemini-style Disclaimer */}
      <div
        style={{
          textAlign: 'center',
          fontSize: '0.72rem',
          color: 'var(--text-dim)',
          marginTop: '0.45rem',
        }}
      >
        ContractAI evaluates contracts against corporate standards & database records. Verify critical legal redlines.
      </div>
    </div>
  );
};
