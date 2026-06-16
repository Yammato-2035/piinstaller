export type RescueMenuItemId =
  | 'system_analyze'
  | 'backup_create'
  | 'backup_verify'
  | 'restore'
  | 'malware_scan'
  | 'cloudserver_manage'
  | 'settings';

export interface RescueMenuItemDef {
  id: RescueMenuItemId;
  icon: string;
  titleKey: string;
  subtitleKey: string;
  actionTarget: string;
  safetyLevel: 'read_only' | 'preview' | 'confirmation_required' | 'blocked';
  writeRisk: 'none' | 'low' | 'high';
  enabled: boolean;
  requiresConfirmation: boolean;
}

export const RESCUE_START_MENU_ITEMS: RescueMenuItemDef[] = [
  {
    id: 'system_analyze',
    icon: 'monitor',
    titleKey: 'menu.system_analyze.title',
    subtitleKey: 'menu.system_analyze.subtitle',
    actionTarget: '/rescue/analyze',
    safetyLevel: 'read_only',
    writeRisk: 'none',
    enabled: true,
    requiresConfirmation: false,
  },
  {
    id: 'backup_create',
    icon: 'backup',
    titleKey: 'menu.backup_create.title',
    subtitleKey: 'menu.backup_create.subtitle',
    actionTarget: '/rescue/backup/create',
    safetyLevel: 'confirmation_required',
    writeRisk: 'high',
    enabled: false,
    requiresConfirmation: true,
  },
  {
    id: 'backup_verify',
    icon: 'shield',
    titleKey: 'menu.backup_verify.title',
    subtitleKey: 'menu.backup_verify.subtitle',
    actionTarget: '/rescue/backup/verify',
    safetyLevel: 'read_only',
    writeRisk: 'none',
    enabled: true,
    requiresConfirmation: false,
  },
  {
    id: 'restore',
    icon: 'restore',
    titleKey: 'menu.restore.title',
    subtitleKey: 'menu.restore.subtitle',
    actionTarget: '/rescue/restore',
    safetyLevel: 'blocked',
    writeRisk: 'high',
    enabled: false,
    requiresConfirmation: true,
  },
  {
    id: 'malware_scan',
    icon: 'bug',
    titleKey: 'menu.malware_scan.title',
    subtitleKey: 'menu.malware_scan.subtitle',
    actionTarget: '/rescue/malware',
    safetyLevel: 'read_only',
    writeRisk: 'none',
    enabled: true,
    requiresConfirmation: false,
  },
  {
    id: 'cloudserver_manage',
    icon: 'cloud',
    titleKey: 'menu.cloudserver_manage.title',
    subtitleKey: 'menu.cloudserver_manage.subtitle',
    actionTarget: '/rescue/cloud',
    safetyLevel: 'preview',
    writeRisk: 'low',
    enabled: false,
    requiresConfirmation: true,
  },
  {
    id: 'settings',
    icon: 'gear',
    titleKey: 'menu.settings.title',
    subtitleKey: 'menu.settings.subtitle',
    actionTarget: '/rescue/settings',
    safetyLevel: 'read_only',
    writeRisk: 'none',
    enabled: true,
    requiresConfirmation: false,
  },
];
