import React, { useState } from 'react';

export const RescuePowerButton: React.FC<{
  label: string;
  confirmLabel: string;
  cancelLabel: string;
  onShutdown: () => void;
}> = ({ label, confirmLabel, cancelLabel, onShutdown }) => {
  const [confirm, setConfirm] = useState(false);

  if (confirm) {
    return (
      <div className="rescue-toolbar-confirm" style={{ display: 'flex', gap: 8 }}>
        <button
          type="button"
          className="rescue-focus-ring rescue-top-icon-btn"
          style={{ width: 'auto', padding: '0 14px', fontSize: 16 }}
          onClick={() => {
            onShutdown();
            setConfirm(false);
          }}
        >
          OK
        </button>
        <button
          type="button"
          className="rescue-focus-ring rescue-top-icon-btn"
          style={{ width: 'auto', padding: '0 14px', fontSize: 16 }}
          onClick={() => setConfirm(false)}
        >
          {cancelLabel}
        </button>
      </div>
    );
  }

  return (
    <button
      type="button"
      className="rescue-focus-ring rescue-top-icon-btn"
      data-rescue-shutdown="true"
      aria-label={label}
      title={label}
      onClick={() => setConfirm(true)}
    >
      <span aria-hidden>⏻</span>
    </button>
  );
};
