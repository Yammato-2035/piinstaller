import React from 'react';
import ReactDOM from 'react-dom/client';
import { RescueApp } from './RescueApp';
import './rescue-shell.css';

function syncRescueViewport() {
  // Nur innerWidth — screen.width ist in Kiosk oft größer als das Chromium-Fenster (Rechts-Abschnitt).
  document.documentElement.style.setProperty('--rescue-vw', `${window.innerWidth}px`);
}

syncRescueViewport();
window.addEventListener('resize', syncRescueViewport);

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <RescueApp />
  </React.StrictMode>,
);
