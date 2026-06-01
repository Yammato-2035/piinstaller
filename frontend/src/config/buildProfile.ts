/**
 * Frontend build profile marker (injected at build time via Vite define).
 * Release builds must not expose Dev-Control / Lab UI surfaces.
 */

export type FrontendBuildProfile =
  | 'release'
  | 'developer'
  | 'local_lab'
  | 'rescue_lab'
  | 'production'

declare const __SETUPHELFER_FRONTEND_BUILD_PROFILE__: string | undefined
declare const __SETUPHELFER_DEV_CONTROL_UI_ENABLED__: boolean | undefined
declare const __SETUPHELFER_DEV_DIAGNOSTICS_UI_ENABLED__: boolean | undefined
declare const __SETUPHELFER_FLEET_SESSIONS_UI_ENABLED__: boolean | undefined
declare const __SETUPHELFER_RESCUE_REMOTE_UI_ENABLED__: boolean | undefined
declare const __SETUPHELFER_BUILD_ID__: string | undefined

const rawProfile =
  (typeof __SETUPHELFER_FRONTEND_BUILD_PROFILE__ !== 'undefined' &&
    __SETUPHELFER_FRONTEND_BUILD_PROFILE__) ||
  (import.meta.env.VITE_SETUPHELFER_FRONTEND_BUILD_PROFILE as string | undefined) ||
  'release'

export const frontendBuildProfile: FrontendBuildProfile =
  rawProfile === 'developer' ||
  rawProfile === 'local_lab' ||
  rawProfile === 'rescue_lab' ||
  rawProfile === 'production'
    ? rawProfile
    : 'release'

const labLike =
  frontendBuildProfile === 'developer' || frontendBuildProfile === 'local_lab'

export const devControlUiEnabled: boolean =
  typeof __SETUPHELFER_DEV_CONTROL_UI_ENABLED__ !== 'undefined'
    ? Boolean(__SETUPHELFER_DEV_CONTROL_UI_ENABLED__)
    : labLike

export const devDiagnosticsUiEnabled: boolean =
  typeof __SETUPHELFER_DEV_DIAGNOSTICS_UI_ENABLED__ !== 'undefined'
    ? Boolean(__SETUPHELFER_DEV_DIAGNOSTICS_UI_ENABLED__)
    : labLike || frontendBuildProfile === 'rescue_lab'

export const fleetSessionsUiEnabled: boolean =
  typeof __SETUPHELFER_FLEET_SESSIONS_UI_ENABLED__ !== 'undefined'
    ? Boolean(__SETUPHELFER_FLEET_SESSIONS_UI_ENABLED__)
    : labLike || frontendBuildProfile === 'rescue_lab'

export const rescueRemoteUiEnabled: boolean =
  typeof __SETUPHELFER_RESCUE_REMOTE_UI_ENABLED__ !== 'undefined'
    ? Boolean(__SETUPHELFER_RESCUE_REMOTE_UI_ENABLED__)
    : frontendBuildProfile === 'local_lab' || frontendBuildProfile === 'rescue_lab'

export const publicExposureAllowed = false

export const internalLabWarning =
  frontendBuildProfile !== 'release'
    ? 'Interne Entwicklungsdaten. Nicht öffentlich teilen.'
    : undefined

export const buildId =
  (typeof __SETUPHELFER_BUILD_ID__ !== 'undefined' && __SETUPHELFER_BUILD_ID__) ||
  (import.meta.env.VITE_SETUPHELFER_BUILD_ID as string | undefined) ||
  ''

export const buildProfileMeta = {
  frontend_build_profile: frontendBuildProfile,
  dev_control_ui_enabled: devControlUiEnabled,
  dev_diagnostics_ui_enabled: devDiagnosticsUiEnabled,
  fleet_sessions_ui_enabled: fleetSessionsUiEnabled,
  rescue_remote_ui_enabled: rescueRemoteUiEnabled,
  public_exposure_allowed: publicExposureAllowed,
  build_id: buildId,
  project_version:
    typeof __APP_VERSION__ !== 'undefined' ? String(__APP_VERSION__) : undefined,
  internal_lab_warning: internalLabWarning,
}
