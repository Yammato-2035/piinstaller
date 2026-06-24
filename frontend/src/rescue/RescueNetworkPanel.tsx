import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { fetchSystemSummary } from './rescueBackupApi';
import {
  connectWifiNetwork,
  fetchWifiConnectionStatus,
  fetchWifiHardware,
  scanWifiNetworks,
  type WifiNetwork,
} from './rescueNetworkApi';
import { getRescueDict, tPath, type RescueLocale } from './rescueLocale';

function chipsetLabel(hw: { wlan_chipset?: string | null; kernel_module?: string | null }) {
  if (hw.wlan_chipset) {
    const short = hw.wlan_chipset.replace(/^\S+\s+/, '').replace(/\[.*\]$/, '').trim();
    if (/9560|AC9560/i.test(short)) return 'Intel AC9560';
    return short.slice(0, 64);
  }
  if (hw.kernel_module === 'iwlwifi') return 'Intel Wireless (iwlwifi)';
  return '';
}

export const RescueNetworkPanel: React.FC<{ locale: RescueLocale }> = ({ locale }) => {
  const dict = useMemo(() => getRescueDict(locale), [locale]);
  const [hardware, setHardware] = useState('');
  const [networks, setNetworks] = useState<WifiNetwork[]>([]);
  const [scanning, setScanning] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const [password, setPassword] = useState('');
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState('');
  const [status, setStatus] = useState<Awaited<ReturnType<typeof fetchWifiConnectionStatus>> | null>(null);
  const [machine, setMachine] = useState<{ vendor?: string; model?: string } | null>(null);

  const refreshStatus = useCallback(async () => {
    const next = await fetchWifiConnectionStatus();
    setStatus(next);
    if (next.telemetry_ok || next.internet_ok) {
      try {
        const summary = await fetchSystemSummary();
        const id = summary.identity as { vendor?: string; model?: string } | undefined;
        if (id) setMachine(id);
      } catch {
        setMachine(null);
      }
    }
  }, []);

  const runScan = useCallback(async () => {
    setScanning(true);
    setError('');
    try {
      const hw = await fetchWifiHardware();
      const label = chipsetLabel(hw);
      setHardware(label || tPath(dict, 'network.hardwareUnknown'));
      const result = await scanWifiNetworks();
      if (!result.success) {
        const detail = result.error?.trim();
        setError(
          detail
            ? `${tPath(dict, 'network.scanFailed')} (${detail})`
            : tPath(dict, 'network.scanFailed'),
        );
        setNetworks([]);
      } else {
        setNetworks(result.networks);
      }
    } catch {
      setError(tPath(dict, 'network.scanFailed'));
    } finally {
      setScanning(false);
      await refreshStatus();
    }
  }, [dict, refreshStatus]);

  useEffect(() => {
    void runScan();
  }, [runScan]);

  const onConnect = async () => {
    if (!selected) return;
    setConnecting(true);
    setError('');
    try {
      const res = await connectWifiNetwork(selected, password);
      if (!res.success) {
        setError(tPath(dict, 'network.connectFailed'));
      } else {
        setPassword('');
        await refreshStatus();
      }
    } catch {
      setError(tPath(dict, 'network.connectFailed'));
    } finally {
      setConnecting(false);
    }
  };

  const toneClass =
    status?.tone === 'green'
      ? 'rescue-net-status-green'
      : status?.tone === 'yellow'
        ? 'rescue-net-status-yellow'
        : 'rescue-net-status-red';

  return (
    <section className="rescue-network-panel" data-rescue-network="true">
      <div className="rescue-network-hardware">
        <span className="rescue-network-label">{tPath(dict, 'network.hardware')}</span>
        <span className="rescue-network-value">{hardware || '…'}</span>
      </div>

      {status ? (
        <div className={`rescue-network-status ${toneClass}`} role="status" aria-live="polite">
          {status.ethernet?.available || status.wifi?.available ? (
            <div className="rescue-network-dual-summary">
              {status.ethernet?.connected ? (
                <p>
                  <strong>{tPath(dict, 'network.lanLabel')}:</strong>{' '}
                  {tPath(dict, 'network.connected')}
                  {status.ethernet.ip_address ? ` (${status.ethernet.ip_address})` : ''}
                </p>
              ) : status.ethernet?.available ? (
                <p>
                  <strong>{tPath(dict, 'network.lanLabel')}:</strong> {tPath(dict, 'network.disconnected')}
                </p>
              ) : null}
              {status.wifi?.available ? (
                <p>
                  <strong>{tPath(dict, 'network.wifiLabel')}:</strong>{' '}
                  {status.wifi.connected
                    ? `${tPath(dict, 'network.connected')}${status.wifi.ssid ? `: ${status.wifi.ssid}` : ''}`
                    : tPath(dict, 'network.disconnected')}
                  {' · '}
                  {status.wifi.scan_allowed
                    ? tPath(dict, 'network.scanAllowed')
                    : tPath(dict, 'network.scanBlocked')}
                </p>
              ) : null}
              {status.dual_link_note === 'lan_connected_wifi_connected' ? (
                <p className="rescue-settings-hint">{tPath(dict, 'network.dualConnected')}</p>
              ) : status.dual_link_note === 'lan_and_wifi_available' ? (
                <p className="rescue-settings-hint">{tPath(dict, 'network.dualLink')}</p>
              ) : null}
            </div>
          ) : null}
          <p className="rescue-network-status-title">
            {status.connection_type === 'ethernet'
              ? tPath(dict, 'network.ethernetConnected')
              : status.connection_type === 'dual'
                ? tPath(dict, 'network.dualConnected')
                : status.connected
                  ? tPath(dict, 'network.connected')
                  : tPath(dict, 'network.disconnected')}
            {status.ssid && status.connection_type !== 'ethernet' ? `: ${status.ssid}` : ''}
          </p>
          {status.ip_address ? (
            <p>
              {tPath(dict, 'network.ip')}: {status.ip_address}
            </p>
          ) : null}
          {status.gateway ? (
            <p>
              {tPath(dict, 'network.gateway')}: {status.gateway}
            </p>
          ) : null}
          <p>
            {tPath(dict, 'network.internet')}:{' '}
            {(status.connectivity?.internet_ok ?? status.internet_ok)
              ? tPath(dict, 'network.yes')
              : tPath(dict, 'network.no')}
          </p>
          <p>
            {tPath(dict, 'network.telemetry')}:{' '}
            {(status.connectivity?.local_backend_ok ?? status.telemetry_local_ok)
              ? tPath(dict, 'network.telemetryLocalOk')
              : (status.connectivity?.telemetry_ok ?? status.telemetry_ok)
                ? tPath(dict, 'network.yes')
                : tPath(dict, 'network.no')}
          </p>
          {!(status.connectivity?.local_backend_ok ?? status.telemetry_local_ok) &&
          status.connected &&
          status.link_up ? (
            <p className="rescue-settings-hint">{tPath(dict, 'network.telemetryLocalFail')}</p>
          ) : null}
        </div>
      ) : null}

      {(status?.telemetry_local_ok || status?.telemetry_ok) && status.connected ? (
        <div className="rescue-telemetry-peer-card" role="status">
          <h3 className="rescue-telemetry-peer-title">{tPath(dict, 'network.telemetryPeerTitle')}</h3>
          <p className="rescue-telemetry-peer-machine">
            {tPath(dict, 'network.machineLabel')}:{' '}
            {[machine?.vendor, machine?.model].filter(Boolean).join(' ') || status.ip_address || '—'}
          </p>
          <p className="rescue-telemetry-peer-hint">{tPath(dict, 'network.telemetryPeerHint')}</p>
        </div>
      ) : null}

      <div className="rescue-network-actions">
        <button
          type="button"
          className="rescue-focus-ring rescue-back-btn"
          onClick={() => void runScan()}
          disabled={scanning || connecting}
        >
          {scanning ? tPath(dict, 'network.scanning') : tPath(dict, 'network.rescan')}
        </button>
      </div>

      {scanning ? <div className="rescue-partitions-spinner" aria-hidden /> : null}

      <div className="rescue-network-list-wrap">
        <div className="rescue-network-list" role="listbox" aria-label={tPath(dict, 'network.available')}>
          {networks.map((net) => {
            const active = selected === net.ssid;
            return (
              <button
                key={net.ssid}
                type="button"
                role="option"
                aria-selected={active}
                className={`rescue-focus-ring rescue-network-item${active ? ' rescue-network-item-active' : ''}`}
                onClick={() => setSelected(net.ssid)}
              >
                <span className="rescue-network-ssid">{net.ssid}</span>
                <span className="rescue-network-meta">
                  {net.signal}% · {net.security}
                  {net.in_use ? ' · ✓' : ''}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {selected ? (
        <div className="rescue-network-connect">
          <label className="rescue-network-label" htmlFor="rescue-wifi-password">
            {tPath(dict, 'network.passwordFor')} {selected}
          </label>
          <input
            id="rescue-wifi-password"
            type="password"
            className="rescue-focus-ring rescue-network-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="off"
          />
          <button
            type="button"
            className="rescue-focus-ring rescue-back-btn"
            disabled={connecting || !password}
            onClick={() => void onConnect()}
          >
            {connecting ? tPath(dict, 'network.connecting') : tPath(dict, 'network.connect')}
          </button>
        </div>
      ) : null}

      {error ? (
        <p className="rescue-network-error" role="alert">
          {error}
        </p>
      ) : null}

      <p className="rescue-settings-hint">{tPath(dict, 'network.noAutoConnect')}</p>
    </section>
  );
};
