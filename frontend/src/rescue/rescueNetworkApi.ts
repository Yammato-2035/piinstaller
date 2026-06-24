export type WifiNetwork = {
  ssid: string;
  signal: number;
  security: string;
  in_use?: boolean;
};

export type WifiHardware = {
  wlan_chipset?: string | null;
  kernel_module?: string | null;
  firmware_ok?: boolean;
  interface_name?: string | null;
  nm_wifi_enabled?: boolean;
  nm_wifi_hw_enabled?: boolean;
};

export type WifiConnectionStatus = {
  connected: boolean;
  status: string;
  tone: 'green' | 'yellow' | 'red';
  connection_type?: 'wifi' | 'ethernet' | 'dual' | null;
  link_up?: boolean;
  ssid?: string | null;
  interface?: string | null;
  ip_address?: string | null;
  gateway?: string | null;
  internet_ok?: boolean;
  telemetry_local_ok?: boolean;
  telemetry_local_url?: string | null;
  telemetry_ok?: boolean;
  hardware?: WifiHardware;
  ethernet?: {
    available?: boolean;
    connected?: boolean;
    interface?: string | null;
    ip_address?: string | null;
  };
  wifi?: {
    available?: boolean;
    radio_enabled?: boolean;
    scan_allowed?: boolean;
    connected?: boolean;
    interface?: string | null;
    ssid?: string | null;
    ip_address?: string | null;
  };
  connectivity?: {
    local_backend_ok?: boolean;
    internet_ok?: boolean;
    telemetry_ok?: boolean;
  };
  dual_link_note?: string | null;
};

export async function fetchWifiHardware(): Promise<WifiHardware> {
  const res = await fetch('/api/rescue/network/hardware', { cache: 'no-store' });
  if (!res.ok) return {};
  return (await res.json()) as WifiHardware;
}

export async function scanWifiNetworks(): Promise<{
  success: boolean;
  networks: WifiNetwork[];
  error?: string;
}> {
  try {
    const res = await fetch('/api/rescue/network/wifi/scan', { cache: 'no-store' });
    if (!res.ok) {
      const detail = await res.text();
      return { success: false, networks: [], error: detail.slice(0, 240) };
    }
    const data = (await res.json()) as { success?: boolean; networks?: WifiNetwork[]; error?: string };
    return {
      success: Boolean(data.success),
      networks: data.networks ?? [],
      error: data.error,
    };
  } catch (e) {
    return { success: false, networks: [], error: String(e) };
  }
}

export async function connectWifiNetwork(
  ssid: string,
  password: string,
): Promise<{ success: boolean; status: string }> {
  const res = await fetch('/api/rescue/network/connect', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ssid, password }),
  });
  const data = (await res.json()) as { success?: boolean; status?: string };
  return { success: Boolean(data.success), status: data.status ?? 'failed' };
}

export async function setTelemetryOptIn(enabled: boolean): Promise<{ success: boolean; opt_in?: boolean }> {
  if (!enabled) {
    return { success: false };
  }
  const res = await fetch('/api/rescue/network/telemetry/opt-in', { method: 'POST' });
  if (!res.ok) return { success: false };
  const data = (await res.json()) as { success?: boolean; opt_in?: boolean };
  return { success: Boolean(data.success), opt_in: data.opt_in };
}

export async function fetchTelemetryOptIn(): Promise<boolean> {
  const res = await fetch('/api/rescue/network/telemetry/opt-in', { cache: 'no-store' });
  if (!res.ok) return false;
  const data = (await res.json()) as { opt_in?: boolean };
  return Boolean(data.opt_in);
}

export async function fetchWifiConnectionStatus(): Promise<WifiConnectionStatus> {
  const res = await fetch('/api/rescue/network/status', { cache: 'no-store' });
  if (!res.ok) {
    return { connected: false, status: 'disconnected', tone: 'red' };
  }
  return (await res.json()) as WifiConnectionStatus;
}
