import React, { createContext, useContext, useMemo } from 'react'
import { useTranslation } from 'react-i18next'

export interface PlatformInfo {
  isRaspberryPi: boolean
  deviceType: 'desktop' | 'laptop' | null
  /** Raspberry-Pi-System oder Hostname / Linux-System (Desktop) etc. */
  systemLabel: string
  /** Possessiv */
  systemLabelPossessive: string
  /** Seiten-Untertitel */
  pageSubtitleLabel: string
  /** Wizard-Willkommen */
  wizardWelcomeHeadline: string
  /** Fenster-/App-Titel */
  appTitle: string
}

export interface PlatformRaw {
  isRaspberryPi: boolean
  deviceType: 'desktop' | 'laptop' | null
  hostname?: string
}

const defaultPlatform: PlatformInfo = {
  isRaspberryPi: false,
  deviceType: null,
  systemLabel: '',
  systemLabelPossessive: '',
  pageSubtitleLabel: '',
  wizardWelcomeHeadline: '',
  appTitle: '',
}

const PlatformContext = createContext<PlatformInfo>(defaultPlatform)

export function usePlatform(): PlatformInfo {
  return useContext(PlatformContext)
}

export function platformRawFromSystemInfo(systemInfo: any): PlatformRaw {
  if (!systemInfo) {
    return { isRaspberryPi: false, deviceType: null }
  }
  const isRaspberryPi = systemInfo.is_raspberry_pi === true
  const deviceType = systemInfo.device_type ?? null
  const hostname = systemInfo.network?.hostname
  return { isRaspberryPi, deviceType, hostname }
}

/** Übersetzte Plattform-Strings aus Rohdaten (ohne Hook, für Tests). */
export function buildPlatformInfo(raw: PlatformRaw, t: (k: string, o?: Record<string, string>) => string): PlatformInfo {
  const { isRaspberryPi, deviceType, hostname } = raw
  const systemLabel = isRaspberryPi
    ? t('platform.system.raspberryPi')
    : hostname && hostname !== 'unknown'
      ? hostname
      : deviceType === 'laptop'
        ? t('platform.system.linuxLaptop')
        : deviceType === 'desktop'
          ? t('platform.system.linuxDesktop')
          : t('platform.system.linuxGeneric')
  const systemLabelPossessive = isRaspberryPi
    ? t('platform.system.raspberryPiPossessive')
    : hostname && hostname !== 'unknown'
      ? hostname
      : deviceType === 'laptop'
        ? t('platform.system.linuxLaptopPossessive')
        : deviceType === 'desktop'
          ? t('platform.system.linuxDesktopPossessive')
          : t('platform.system.linuxGenericPossessive')
  const pageSubtitleLabel = isRaspberryPi ? t('platform.pageSubtitle.raspberry') : t('platform.pageSubtitle.linux')
  const wizardWelcomeHeadline = isRaspberryPi
    ? t('platform.welcome.raspberry')
    : hostname && hostname !== 'unknown'
      ? t('platform.welcome.withHostname', { host: hostname })
      : t('platform.welcome.linuxGeneric')
  const appTitle = isRaspberryPi
    ? t('platform.appTitle.setuphelfer')
    : hostname && hostname !== 'unknown'
      ? hostname
      : t('platform.appTitle.configureSystem')
  return {
    isRaspberryPi,
    deviceType: deviceType ?? null,
    systemLabel,
    systemLabelPossessive,
    pageSubtitleLabel,
    wizardWelcomeHeadline,
    appTitle,
  }
}

function PlatformInfoBridge({ raw, children }: { raw: PlatformRaw; children: React.ReactNode }) {
  const { t } = useTranslation()
  const value = useMemo(() => buildPlatformInfo(raw, t), [raw, t])
  return <PlatformContext.Provider value={value}>{children}</PlatformContext.Provider>
}

export function PlatformProvider({
  systemInfo,
  children,
}: {
  systemInfo: any
  children: React.ReactNode
}) {
  const raw = useMemo(() => platformRawFromSystemInfo(systemInfo), [systemInfo])
  return <PlatformInfoBridge raw={raw}>{children}</PlatformInfoBridge>
}

export default PlatformContext
