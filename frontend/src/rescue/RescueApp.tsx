import React, { useEffect, useState } from 'react';
import { fetchRescueBootStatus, loadOfflineBootStatus } from './rescueApi';
import { RescueStartCenter } from './RescueStartCenter';

export const RescueApp: React.FC = () => {
  const [locale, setLocale] = useState<'de' | 'en'>('de');
  const [status, setStatus] = useState(loadOfflineBootStatus());

  useEffect(() => {
    fetchRescueBootStatus().then(setStatus).catch(() => setStatus(loadOfflineBootStatus()));
  }, []);

  return <RescueStartCenter status={status} locale={locale} onLocaleChange={setLocale} />;
};
