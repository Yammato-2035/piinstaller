import React from 'react';

export const RescueNetworkPanel: React.FC<{ locale: 'de' | 'en' }> = ({ locale }) => (
  <section style={{ color: '#cbd5e1', fontSize: 14, lineHeight: 1.5 }}>
    <p>
      {locale === 'de'
        ? 'Netzwerk ist optional. WLAN-Suche startet erst nach deiner Auswahl.'
        : 'Network is optional. Wi-Fi scan starts only after you choose it.'}
    </p>
    <p style={{ color: '#94a3b8', marginTop: 8 }}>
      {locale === 'de'
        ? 'Keine Verbindung wird ohne weitere Bestätigung aufgebaut.'
        : 'No connection is established without further confirmation.'}
    </p>
  </section>
);
