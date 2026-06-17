import React, { useEffect, useState } from 'react';
import { fetchRescueBootStatus, loadOfflineBootStatus } from './rescueApi';
import { RescueBackupPanel } from './RescueBackupPanel';
import { RescueStartCenter } from './RescueStartCenter';
import type { RescueMenuItemId } from './rescueMenuItems';

type View = 'menu' | RescueMenuItemId;

export const RescueApp: React.FC = () => {
  const [locale, setLocale] = useState<'de' | 'en'>('de');
  const [status, setStatus] = useState(loadOfflineBootStatus());
  const [view, setView] = useState<View>('menu');

  useEffect(() => {
    fetchRescueBootStatus().then(setStatus).catch(() => setStatus(loadOfflineBootStatus()));
  }, []);

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
