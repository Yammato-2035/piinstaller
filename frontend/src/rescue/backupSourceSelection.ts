import type { RescueStorageDevice, RescueStorageDiscovery } from './rescueBackupApi';

function isRescueStick(item: RescueStorageDevice): boolean {
  const role = String(item.role || '').toLowerCase();
  const label = String(item.label || '').toUpperCase();
  const tran = String(item.tran || '').toLowerCase();
  if (role.includes('rescue') || label.includes('SETUPHELFER') || label.includes('SETUP_LOGS')) {
    return true;
  }
  return tran === 'usb' && (role.includes('rescue') || label.includes('SETUP'));
}

export function pickAutoBackupSource(discovery: RescueStorageDiscovery): RescueStorageDevice | undefined {
  const systems = discovery.system_source_candidates || [];
  if (systems.length === 1) return systems[0];
  if (systems.length > 1) {
    return [...systems].sort(
      (a, b) => (Number(b.auto_select_score ?? 0) - Number(a.auto_select_score ?? 0))
        || String(a.path).localeCompare(String(b.path)),
    )[0];
  }
  const sources = discovery.source_candidates || [];
  const winDisk = sources.find(
    (d) => d.role === 'windows_system_disk' && (d.type === 'system_group' || d.type === 'disk'),
  );
  if (winDisk) return winDisk;
  const winAny = sources.find((d) => d.role === 'windows_system_disk' && !isRescueStick(d));
  if (winAny) return winAny;
  return sources.find((d) => !isRescueStick(d));
}

export function sortBackupSources(items: RescueStorageDevice[]): RescueStorageDevice[] {
  return [...items].sort((a, b) => {
    const ga = a.type === 'system_group' ? 0 : 1;
    const gb = b.type === 'system_group' ? 0 : 1;
    if (ga !== gb) return ga - gb;
    const sa = Number(a.auto_select_score ?? (a.role === 'windows_system_disk' ? 50 : 0));
    const sb = Number(b.auto_select_score ?? (b.role === 'windows_system_disk' ? 50 : 0));
    if (sa !== sb) return sb - sa;
    const ta = String(a.type || '');
    const tb = String(b.type || '');
    if (ta === 'disk' && tb !== 'disk') return -1;
    if (tb === 'disk' && ta !== 'disk') return 1;
    return Number(b.size_bytes ?? b.size ?? 0) - Number(a.size_bytes ?? a.size ?? 0);
  });
}

export function backupSourceLabel(s: RescueStorageDevice): string {
  if (s.type === 'system_group' || s.group_kind === 'windows_system') {
    const tags = (s.tags || []).join('+') || 'Windows';
    return `Windows-System · ${s.path} · ${tags}`;
  }
  const kind = s.type === 'part' ? 'Partition' : 'Platte';
  return `${s.path} · ${kind} · ${s.fstype || 'disk'} · ${s.role || 'unknown'}`;
}
