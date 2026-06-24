import React, { useEffect, useState } from 'react';
import { fetchRescueBootStatus, loadOfflineBootStatus } from './rescueApi';
import { RescueBackupPanel } from './RescueBackupPanel';
import { RescueBootSplash } from './RescueBootSplash';
import { RescueStartCenter } from './RescueStartCenter';
import type { RescueMenuItemId } from './rescueMenuItems';

type View = 'menu' | RescueMenuItemId;

export const RescueApp: React.FC = () => {
  const [locale, setLocale] = useState<'de' | 'en'>('de');
  const [status, setStatus] = useState(loadOfflineBootStatus());
  const [view, setView] = useState<View>('menu');
  const [bootReady, setBootReady] = useState(false);
  const [apiReady, setApiReady] = useState(false);

  useEffect(() => {
    fetchRescueBootStatus()
      .then((s) => {
        setStatus(s);
        setApiReady(true);
      })
      .catch(() => {
        setStatus(loadOfflineBootStatus());
        setApiReady(true);
      });
  }, []);

  if (!bootReady) {
    return (
      <RescueBootSplash
        status={status}
        ready={apiReady}
        onReady={() => setBootReady(true)}
      />
    );
  }

  if (view === 'backup_create') {
    return <RescueBackupPanel onBack={() => setView('menu')} />;
  }

  return (
    <RescueStartCenter
      status={status}
      locale={locale}
      onLocaleChange={setLocale}
      onSelectItem={(id) => {
        if (id === 'backup_create' || id === 'backup_verify' || id === 'restore') {
          setView(id);
        }
      }}
    />
  );
};
