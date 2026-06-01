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

export const devControlUiEnabled: boolean =
  typeof __SETUPHELFER_DEV_CONTROL_UI_ENABLED__ !== 'undefined'
    ? Boolean(__SETUPHELFER_DEV_CONTROL_UI_ENABLED__)
    : frontendBuildProfile === 'developer' || frontendBuildProfile === 'local_lab'

export const buildProfileMeta = {
  frontend_build_profile: frontendBuildProfile,
  dev_control_ui_enabled: devControlUiEnabled,
  internal_lab_warning:
    frontendBuildProfile !== 'release'
      ? 'Interne Entwicklungsdaten. Nicht öffentlich teilen.'
      : undefined,
}
