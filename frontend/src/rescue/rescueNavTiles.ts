import type { RescueMenuItemId } from './rescueMenuItems';

/** RS-P2N dashboard grid — UI layout only (8 large tiles). */
export type RescueNavTileId =
  | 'backup_create'
  | 'data_rescue'
  | 'linux_migration'
  | 'system_analyze'
  | 'network'
  | 'partitions'
  | 'linux_install'
  | 'settings'
  | 'system';

export interface RescueNavTileDef {
  id: RescueNavTileId;
  menuId?: RescueMenuItemId;
  icon: 'backup' | 'rescue' | 'migration' | 'analyze' | 'network' | 'partition' | 'install' | 'settings' | 'system';
  titleKey: string;
  subtitleKey: string;
  uiOnly: boolean;
}

export const RESCUE_NAV_TILES: RescueNavTileDef[] = [
  {
    id: 'backup_create',
    menuId: 'backup_create',
    icon: 'backup',
    titleKey: 'nav.backup.title',
    subtitleKey: 'nav.backup.subtitle',
    uiOnly: false,
  },
  {
    id: 'data_rescue',
    icon: 'rescue',
    titleKey: 'nav.dataRescue.title',
    subtitleKey: 'nav.dataRescue.subtitle',
    uiOnly: true,
  },
  {
    id: 'linux_migration',
    icon: 'migration',
    titleKey: 'nav.linuxMigration.title',
    subtitleKey: 'nav.linuxMigration.subtitle',
    uiOnly: true,
  },
  {
    id: 'system_analyze',
    menuId: 'system_analyze',
    icon: 'analyze',
    titleKey: 'nav.analyze.title',
    subtitleKey: 'nav.analyze.subtitle',
    uiOnly: true,
  },
  {
    id: 'network',
    icon: 'network',
    titleKey: 'nav.network.title',
    subtitleKey: 'nav.network.subtitle',
    uiOnly: true,
  },
  {
    id: 'partitions',
    icon: 'partition',
    titleKey: 'nav.partitions.title',
    subtitleKey: 'nav.partitions.subtitle',
    uiOnly: true,
  },
  {
    id: 'linux_install',
    icon: 'install',
    titleKey: 'nav.linuxInstall.title',
    subtitleKey: 'nav.linuxInstall.subtitle',
    uiOnly: true,
  },
  {
    id: 'settings',
    menuId: 'settings',
    icon: 'settings',
    titleKey: 'nav.settings.title',
    subtitleKey: 'nav.settings.subtitle',
    uiOnly: true,
  },
  {
    id: 'system',
    menuId: 'backup_verify',
    icon: 'system',
    titleKey: 'nav.system.title',
    subtitleKey: 'nav.system.subtitle',
    uiOnly: true,
  },
];
