import React, { createContext, useContext, useMemo } from 'react'

export interface PlatformInfo {
  isRaspberryPi: boolean
  deviceType: 'desktop' | 'laptop' | null
  /** "Raspberry-Pi-System" oder "Linux-System (Desktop)" / "Linux-System (Laptop)" / "Linux-System" */
  systemLabel: string
  /** Für Possessiv: "Raspberry-Pi-Systems" oder "Linux-Systems (Desktop)" etc. */
  systemLabelPossessive: string
  /** Für Seiten-Untertitel: auf Pi "Raspberry-Pi-System", sonst "Ihr Linuxsystem" */
  pageSubtitleLabel: string
}

const defaultPlatform: PlatformInfo = {
  isRaspberryPi: false,
  deviceType: null,
  systemLabel: 'Linux-System',
  systemLabelPossessive: 'Linux-Systems',
  pageSubtitleLabel: 'Ihr Linuxsystem',
}

const PlatformContext = createContext<PlatformInfo>(defaultPlatform)

export function usePlatform(): PlatformInfo {
  return useContext(PlatformContext)
}

export function platformFromSystemInfo(systemInfo: any): PlatformInfo {
  if (!systemInfo) return defaultPlatform
  const isRaspberryPi = systemInfo.is_raspberry_pi === true
  const deviceType = systemInfo.device_type ?? null
  const hostname = systemInfo.network?.hostname
  const systemLabel = isRaspberryPi
    ? 'Raspberry-Pi-System'
    : (hostname && hostname !== 'unknown' ? hostname : deviceType === 'laptop' ? 'Linux-System (Laptop)' : deviceType === 'desktop' ? 'Linux-System (Desktop)' : 'Linux-System')
  const systemLabelPossessive = isRaspberryPi
    ? 'Raspberry-Pi-Systems'
    : (hostname && hostname !== 'unknown' ? hostname : deviceType === 'laptop' ? 'Linux-Systems (Laptop)' : deviceType === 'desktop' ? 'Linux-Systems (Desktop)' : 'Linux-Systems')
  const pageSubtitleLabel = isRaspberryPi ? 'Raspberry-Pi-System' : 'Ihr Linuxsystem'
  return { isRaspberryPi, deviceType, systemLabel, systemLabelPossessive, pageSubtitleLabel }
}

export const PlatformProvider = PlatformContext.Provider
export default PlatformContext
