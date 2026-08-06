import React, { useEffect, useMemo, useState } from 'react';
import {
  fetchCarrierStatus,
  fetchHardwareCpu,
  fetchHardwareGpus,
  fetchHardwareInput,
  fetchHardwareMainboard,
  fetchHardwareUsb,
  fetchPeripheralPrinters,
  fetchPeripheralScanners,
  fetchProvisioningCatalog,
  fetchRaspberryPiOverview,
  postCarrierLayoutPreview,
  type RescueCarrierLayoutPlan,
  type RescueCarrierStatus,
  type RescueCpuReport,
  type RescueGpuReport,
  type RescueInputDeviceReport,
  type RescueMainboardReport,
  type RescueOsCatalogEntry,
  type RescuePiOverview,
  type RescuePrinterReport,
  type RescueScannerReport,
  type RescueUsbFunction,
} from './rescueHardwareApi';
import { getRescueDict, tPath, type RescueLocale } from './rescueLocale';
import { RescueHardwareBaselinePanel } from './RescueHardwareBaselinePanel';

/** Simplified 4-color mapping onto the spec's ampel model (Gruen/Gelb/Rot/Grau). */
function ampelClass(status: string | undefined | null): 'ok' | 'warn' | 'err' | 'neutral' {
  switch (status) {
    case 'ready':
    case 'identified':
    case 'confirmed':
    case 'board_identified_boot_plan_available':
      return 'ok';
    case 'blocked':
    case 'unsupported':
      return 'err';
    case 'unknown':
      return 'neutral';
    default:
      return 'warn';
  }
}

const AmpelBadge: React.FC<{ status: string | null | undefined; label?: string }> = ({ status, label }) => {
  const cls = ampelClass(status ?? 'unknown');
  const icon = cls === 'ok' ? '✓' : cls === 'err' ? '✕' : cls === 'warn' ? '◐' : '○';
  return (
    <span className={`rescue-hw-badge rescue-hw-badge-${cls}`}>
      {icon} {label ?? status ?? '—'}
    </span>
  );
};

function formatBytes(bytes: number | undefined | null): string {
  if (!bytes || bytes <= 0) return '—';
  const gb = bytes / 1024 ** 3;
  return `${gb.toFixed(1)} GB`;
}

export const RescueHardwarePanel: React.FC<{ locale: RescueLocale }> = ({ locale }) => {
  const dict = useMemo(() => getRescueDict(locale), [locale]);
  const [loading, setLoading] = useState(true);
  const [cpu, setCpu] = useState<RescueCpuReport | null>(null);
  const [gpus, setGpus] = useState<RescueGpuReport[]>([]);
  const [mainboard, setMainboard] = useState<RescueMainboardReport | null>(null);
  const [usbFunctions, setUsbFunctions] = useState<RescueUsbFunction[]>([]);
  const [inputDevices, setInputDevices] = useState<RescueInputDeviceReport[]>([]);
  const [printers, setPrinters] = useState<RescuePrinterReport[]>([]);
  const [scanners, setScanners] = useState<RescueScannerReport[]>([]);
  const [pi, setPi] = useState<RescuePiOverview | null>(null);
  const [carrierStatus, setCarrierStatus] = useState<RescueCarrierStatus | null>(null);
  const [carrierPlan, setCarrierPlan] = useState<RescueCarrierLayoutPlan | null>(null);
  const [carrierSizeInput, setCarrierSizeInput] = useState('63864502272');
  const [osCatalog, setOsCatalog] = useState<RescueOsCatalogEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      fetchHardwareCpu().catch(() => null),
      fetchHardwareGpus().catch(() => null),
      fetchHardwareMainboard().catch(() => null),
      fetchHardwareUsb().catch(() => null),
      fetchHardwareInput().catch(() => null),
      fetchPeripheralPrinters().catch(() => null),
      fetchPeripheralScanners().catch(() => null),
      fetchRaspberryPiOverview().catch(() => null),
      fetchCarrierStatus().catch(() => null),
      fetchProvisioningCatalog().catch(() => null),
    ])
      .then(([cpuR, gpuR, mbR, usbR, inputR, printerR, scannerR, piR, carrierR, catalogR]) => {
        if (cpuR) setCpu(cpuR);
        if (gpuR) setGpus(gpuR.gpus);
        if (mbR) setMainboard(mbR);
        if (usbR) setUsbFunctions(usbR.usb_functions);
        if (inputR) setInputDevices(inputR.input_devices);
        if (printerR) setPrinters(printerR.printers);
        if (scannerR) setScanners(scannerR.scanners);
        if (piR) setPi(piR);
        if (carrierR) setCarrierStatus(carrierR);
        if (catalogR) setOsCatalog(catalogR.entries);
        if (!cpuR && !gpuR && !mbR) setError(tPath(dict, 'section.hardware.loadError'));
      })
      .finally(() => setLoading(false));
  }, [dict]);

  const runCarrierPreview = () => {
    const bytes = Number.parseInt(carrierSizeInput, 10);
    if (!Number.isFinite(bytes) || bytes <= 0) return;
    postCarrierLayoutPreview(bytes)
      .then(setCarrierPlan)
      .catch(() => setCarrierPlan(null));
  };

  if (loading) {
    return <p>{tPath(dict, 'section.hardware.loading')}</p>;
  }

  const osSupportCounts = osCatalog.reduce<Record<string, number>>((acc, e) => {
    acc[e.support_status] = (acc[e.support_status] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="rescue-hardware-panel rescue-scroll-content" data-rescue-hardware="true">
      <p className="rescue-section-intro">{tPath(dict, 'section.hardware.intro')}</p>
      {error ? (
        <p className="rescue-notice-banner" role="status">
          {error}
        </p>
      ) : null}

      <RescueHardwareBaselinePanel locale={locale} />

      <section className="rescue-plan-card">
        <h3>{tPath(dict, 'section.hardware.cpuTitle')}</h3>
        {cpu ? (
          <ul className="rescue-migration-list">
            <li>{tPath(dict, 'section.hardware.architecture')}: {cpu.architecture}</li>
            <li>{tPath(dict, 'section.hardware.virtualization')}: {cpu.virtualization_available ? '✓' : '—'}</li>
            <li>{tPath(dict, 'section.hardware.microcode')}: {cpu.microcode_status}</li>
            <li>{tPath(dict, 'section.hardware.raspberryPiSoc')}: {cpu.is_raspberry_pi_soc ? '✓' : '—'}</li>
            <li>
              <AmpelBadge status={cpu.device.operational_status} />
            </li>
          </ul>
        ) : (
          <p className="rescue-hw-unavailable">{tPath(dict, 'section.hardware.unavailable')}</p>
        )}
      </section>

      <section className="rescue-plan-card">
        <h3>{tPath(dict, 'section.hardware.gpuTitle')}</h3>
        {gpus.length === 0 ? (
          <p className="rescue-hw-unavailable">{tPath(dict, 'section.hardware.unavailable')}</p>
        ) : (
          <ul className="rescue-migration-list">
            {gpus.map((g) => (
              <li key={g.device_id}>
                {g.vendor} — {g.gpu_type} — <AmpelBadge status={g.gpu_status} />{' '}
                {g.disabling_cmdline_params.length > 0
                  ? `(${tPath(dict, 'section.hardware.disabledByCmdline')}: ${g.disabling_cmdline_params.join(', ')})`
                  : null}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="rescue-plan-card">
        <h3>{tPath(dict, 'section.hardware.mainboardTitle')}</h3>
        {mainboard ? (
          <ul className="rescue-migration-list">
            <li>{tPath(dict, 'section.hardware.systemVendor')}: {mainboard.system_vendor || '—'}</li>
            <li>{tPath(dict, 'section.hardware.systemProduct')}: {mainboard.system_product || '—'}</li>
            <li>{tPath(dict, 'section.hardware.platformClass')}: {mainboard.platform_class}</li>
            <li>
              {tPath(dict, 'section.hardware.chipset')}: {mainboard.chipset_name || tPath(dict, 'section.hardware.reviewRequired')}{' '}
              <AmpelBadge status={mainboard.chipset_status} />
            </li>
          </ul>
        ) : (
          <p className="rescue-hw-unavailable">{tPath(dict, 'section.hardware.unavailable')}</p>
        )}
      </section>

      <section className="rescue-plan-card">
        <h3>{tPath(dict, 'section.hardware.usbTitle')}</h3>
        {usbFunctions.length === 0 ? (
          <p className="rescue-hw-unavailable">{tPath(dict, 'section.hardware.unavailable')}</p>
        ) : (
          <ul className="rescue-migration-list">
            {usbFunctions.map((u) => (
              <li key={u.sysfs_id}>
                {u.sysfs_id}: {u.functions.map((f) => f.function).join(', ')}
                {u.is_composite ? ` (${tPath(dict, 'section.hardware.composite')})` : ''}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="rescue-plan-card">
        <h3>{tPath(dict, 'section.hardware.inputTitle')}</h3>
        {inputDevices.length === 0 ? (
          <p className="rescue-hw-unavailable">{tPath(dict, 'section.hardware.unavailable')}</p>
        ) : (
          <ul className="rescue-migration-list">
            {inputDevices.map((d) => (
              <li key={d.device_id}>
                {d.product_name || d.device_id} — {d.function} — <AmpelBadge status={d.operational_status} />
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="rescue-plan-card">
        <h3>{tPath(dict, 'section.hardware.printerScannerTitle')}</h3>
        {printers.length === 0 && scanners.length === 0 ? (
          <p className="rescue-hw-unavailable">{tPath(dict, 'section.hardware.unavailable')}</p>
        ) : (
          <ul className="rescue-migration-list">
            {printers.map((p) => (
              <li key={p.device_id}>
                🖨️ {p.device_kind} — {tPath(dict, 'section.hardware.technology')}: {p.technology} — {tPath(dict, 'section.hardware.color')}: {p.color_capability}{' '}
                <AmpelBadge status={p.classification_status} />
              </li>
            ))}
            {scanners.map((s) => (
              <li key={s.device_id}>
                🖼️ {tPath(dict, 'section.hardware.scanner')} ({s.source}) — <AmpelBadge status={s.operational_status} />
              </li>
            ))}
          </ul>
        )}
        <p className="rescue-hw-hint">{tPath(dict, 'section.hardware.printerScannerHint')}</p>
      </section>

      <section className="rescue-plan-card">
        <h3>{tPath(dict, 'section.hardware.raspberryPiTitle')}</h3>
        {pi?.detection.is_raspberry_pi ? (
          <ul className="rescue-migration-list">
            <li>{tPath(dict, 'section.hardware.model')}: {pi.detection.model_name || pi.detection.model_id || '—'}</li>
            <li>{tPath(dict, 'section.hardware.soc')}: {pi.detection.soc || '—'}</li>
            <li>{tPath(dict, 'section.hardware.compatibility')}: <AmpelBadge status={pi.compatibility_summary.compatibility_status} /></li>
          </ul>
        ) : (
          <p className="rescue-hw-unavailable">{tPath(dict, 'section.hardware.notARaspberryPi')}</p>
        )}
      </section>

      <section className="rescue-plan-card">
        <h3>{tPath(dict, 'section.hardware.carrierTitle')}</h3>
        {carrierStatus ? (
          <p>
            {tPath(dict, 'section.hardware.recommendedStrategy')}: <strong>{carrierStatus.strategy_decision.recommended_strategy}</strong>
          </p>
        ) : null}
        <div className="rescue-hw-inline-form">
          <label htmlFor="rescue-hw-carrier-bytes">{tPath(dict, 'section.hardware.carrierBytesLabel')}</label>
          <input
            id="rescue-hw-carrier-bytes"
            type="number"
            value={carrierSizeInput}
            onChange={(e) => setCarrierSizeInput(e.target.value)}
          />
          <button type="button" className="rescue-hw-btn" onClick={runCarrierPreview}>
            {tPath(dict, 'section.hardware.carrierPreviewButton')}
          </button>
        </div>
        {carrierPlan ? (
          <ul className="rescue-migration-list">
            <li>{tPath(dict, 'section.hardware.layoutStatus')}: <AmpelBadge status={carrierPlan.layout_status === 'ok' ? 'ready' : carrierPlan.layout_status} /></li>
            <li>{tPath(dict, 'section.hardware.usableCapacity')}: {formatBytes(carrierPlan.usable_bytes)}</li>
            <li>{tPath(dict, 'section.hardware.reservedCapacity')}: {formatBytes(carrierPlan.reserved_bytes)}</li>
            <li>{tPath(dict, 'section.hardware.maxCachedImages')}: {carrierPlan.max_cached_images}</li>
          </ul>
        ) : null}
      </section>

      <section className="rescue-plan-card">
        <h3>{tPath(dict, 'section.hardware.osTitle')}</h3>
        <ul className="rescue-migration-list">
          <li>{tPath(dict, 'section.hardware.osExperimental')}: {osSupportCounts.experimental || 0}</li>
          <li>{tPath(dict, 'section.hardware.osFuture')}: {osSupportCounts.future || 0}</li>
          <li>{tPath(dict, 'section.hardware.osVerified')}: {osSupportCounts.verified || 0}</li>
        </ul>
        <p className="rescue-hw-hint" data-rescue-hardware-write-disclaimer="true">
          {tPath(dict, 'section.hardware.noWriteDisclaimer')}
        </p>
      </section>
    </div>
  );
};
