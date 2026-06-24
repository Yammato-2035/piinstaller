import React, { useEffect, useRef, useState } from 'react';

export type SystemMenuAction = 'shell' | 'logs' | 'exportDiagnostic' | 'reboot';

export const RescueSystemMenu: React.FC<{
  labels: Record<SystemMenuAction | 'menu' | 'confirmReboot' | 'confirmShutdown' | 'cancel' | 'hotkey' | 'exportOk' | 'exportFail', string>;
  onOpenLogs: () => void;
  onOpenShell: () => void;
  onExportDiagnostic: () => void;
  onReboot: () => void;
}> = ({ labels, onOpenLogs, onOpenShell, onExportDiagnostic, onReboot }) => {
  const [open, setOpen] = useState(false);
  const [confirm, setConfirm] = useState<'reboot' | null>(null);
  const [message, setMessage] = useState('');
  const rootRef = useRef<HTMLDivElement>(null);
  const itemRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const [focusIdx, setFocusIdx] = useState(0);

  const items: SystemMenuAction[] = ['reboot', 'shell', 'logs', 'exportDiagnostic'];

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'F10') {
        e.preventDefault();
        setOpen((v) => !v);
        setConfirm(null);
      }
      if (e.key === 'Escape' && open) {
        e.preventDefault();
        setOpen(false);
        setConfirm(null);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onClick = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) {
        setOpen(false);
        setConfirm(null);
      }
    };
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, [open]);

  useEffect(() => {
    if (open && !confirm) {
      itemRefs.current[focusIdx]?.focus();
    }
  }, [open, confirm, focusIdx]);

  const runAction = async (action: SystemMenuAction) => {
    setMessage('');
    switch (action) {
      case 'shell':
        onOpenShell();
        setOpen(false);
        break;
      case 'logs':
        onOpenLogs();
        setOpen(false);
        break;
      case 'exportDiagnostic':
        onExportDiagnostic();
        setMessage(labels.exportOk);
        setOpen(false);
        break;
      case 'reboot':
        setConfirm('reboot');
        break;
      default:
        break;
    }
  };

  const confirmAction = () => {
    if (confirm === 'reboot') {
      onReboot();
      setConfirm(null);
      setOpen(false);
    }
  };

  const onMenuKeyDown = (e: React.KeyboardEvent) => {
    if (confirm) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setFocusIdx((i) => (i + 1) % items.length);
    }
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      setFocusIdx((i) => (i - 1 + items.length) % items.length);
    }
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      runAction(items[focusIdx]);
    }
  };

  return (
    <div ref={rootRef} style={{ position: 'relative' }} data-rescue-system-menu="true">
      <button
        type="button"
        className="rescue-focus-ring rescue-top-icon-btn"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={labels.menu}
        title={`${labels.menu} (${labels.hotkey})`}
        onClick={() => setOpen((v) => !v)}
      >
        <span aria-hidden>⚙</span>
      </button>
      {open ? (
        <div role="menu" className="rescue-system-menu-dropdown" onKeyDown={onMenuKeyDown}>
          {confirm ? (
            <div style={{ padding: 8 }}>
              <p style={{ margin: '0 0 12px', fontSize: 18 }}>
                {labels.confirmReboot}
              </p>
              <div style={{ display: 'flex', gap: 8 }}>
                <button type="button" className="rescue-focus-ring rescue-system-menu-item" onClick={confirmAction}>
                  OK
                </button>
                <button
                  type="button"
                  className="rescue-focus-ring rescue-system-menu-item"
                  onClick={() => setConfirm(null)}
                >
                  {labels.cancel}
                </button>
              </div>
            </div>
          ) : (
            items.map((id, idx) => (
              <button
                key={id}
                ref={(el) => {
                  itemRefs.current[idx] = el;
                }}
                type="button"
                role="menuitem"
                className="rescue-focus-ring rescue-system-menu-item"
                onFocus={() => setFocusIdx(idx)}
                onClick={() => runAction(id)}
                style={focusIdx === idx ? { borderColor: '#93c5fd' } : undefined}
              >
                {labels[id]}
              </button>
            ))
          )}
        </div>
      ) : null}
      {message ? (
        <p style={{ position: 'absolute', right: 0, top: 'calc(100% + 4px)', fontSize: 16, margin: 0, whiteSpace: 'nowrap' }}>
          {message}
        </p>
      ) : null}
    </div>
  );
};
