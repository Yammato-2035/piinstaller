/**
 * PI-RS-HW-COMPAT-PROVISION-001 Phase 15 — read-only/preview-only fetch helpers
 * for the rescue hardware overview UI.
 *
 * Every call here targets a GET/POST-preview route from Phase 14
 * (/api/rescue/hardware|peripherals|platform|carrier|provision/*). None of
 * these routes install, write, flash, format or partition anything.
 */

export interface RescueHardwareDevice {
  device_id: string;
  device_class: string;
  vendor_name: string | null;
  product_name: string | null;
  model_name: string | null;
  operational_status: string;
  firmware_status: string;
  detection_confidence: number;
  kernel_driver_in_use: string | null;
}

export interface RescueCpuReport {
  device: RescueHardwareDevice;
  architecture: string;
  virtualization_available: boolean;
  microcode_status: string;
  is_raspberry_pi_soc: boolean;
  missing_tools: string[];
}

export interface RescueGpuReport {
  device_id: string;
  vendor: string;
  gpu_type: string;
  product_name: string | null;
  driver_in_use: string | null;
  gpu_status: string;
  gui_boot_recommendation: string;
  physical_test_required: boolean;
  disabling_cmdline_params: string[];
}

export interface RescueMainboardReport {
  system_vendor: string | null;
  system_product: string | null;
  baseboard_vendor: string | null;
  baseboard_product: string | null;
  bios_version: string | null;
  platform_class: string;
  chipset_name: string | null;
  chipset_status: string;
}

export interface RescueUsbFunction {
  sysfs_id: string;
  is_composite: boolean;
  functions: { function: string; operational_status: string; detection_confidence: number }[];
}

export interface RescueInputDeviceReport {
  device_id: string;
  product_name: string | null;
  bus_type: string;
  function: string;
  operational_status: string;
}

export interface RescuePrinterReport {
  device_id: string;
  device_kind: string;
  technology: string;
  color_capability: string;
  classification_status: string;
  requires_physical_print_test: boolean;
  driver_plan_preview?: { recommended_driver: string | null; warnings: string[] };
}

export interface RescueScannerReport {
  device_id: string;
  source: string;
  operational_status: string;
  requires_physical_scan_test: boolean;
}

export interface RescuePiDetection {
  is_raspberry_pi: boolean;
  model_id: string | null;
  model_name: string | null;
  soc: string | null;
  detection_confidence: number;
}

export interface RescuePiOverview {
  detection: RescuePiDetection;
  boot_plan: { boot_media: { medium: string; status: string; physical_validation_required: boolean }[] };
  compatibility_summary: { compatibility_status: string; known_limitations: string[]; physical_validation_required: boolean };
}

export interface RescueCarrierStatus {
  strategy_decision: { recommended_strategy: string; decision_status: string; rationale: string };
}

export interface RescueCarrierLayoutPlan {
  layout_status: 'ok' | 'review_required' | 'blocked';
  carrier_size_bytes: number;
  reserved_bytes: number;
  usable_bytes: number;
  required_bytes: number;
  runtime_bytes: number;
  driver_cache_bytes: number;
  image_cache_bytes: number;
  evidence_bytes: number;
  max_cached_images: number;
  recommended_strategy: string;
  warnings: string[];
}

export interface RescueOsCatalogEntry {
  image_id: string;
  display_name: string;
  architecture: string;
  support_status: 'verified' | 'experimental' | 'future' | 'blocked';
  download_enabled: boolean;
}

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) throw new Error(`request_failed:${res.status}`);
  return (await res.json()) as T;
}

async function postJson<T>(url: string, body: Record<string, unknown>): Promise<T> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`request_failed:${res.status}`);
  return (await res.json()) as T;
}

export async function fetchHardwareDevices(): Promise<{ devices: RescueHardwareDevice[] }> {
  return getJson('/api/rescue/hardware/devices');
}

export async function fetchHardwareCpu(): Promise<RescueCpuReport> {
  return getJson('/api/rescue/hardware/cpu');
}

export async function fetchHardwareGpus(): Promise<{ gpus: RescueGpuReport[] }> {
  return getJson('/api/rescue/hardware/gpus');
}

export async function fetchHardwareMainboard(): Promise<RescueMainboardReport> {
  return getJson('/api/rescue/hardware/mainboard');
}

export async function fetchHardwareUsb(): Promise<{ lsusb_devices: RescueHardwareDevice[]; usb_functions: RescueUsbFunction[] }> {
  return getJson('/api/rescue/hardware/usb');
}

export async function fetchHardwareInput(): Promise<{ input_devices: RescueInputDeviceReport[] }> {
  return getJson('/api/rescue/hardware/input');
}

export async function fetchDriverPlan(deviceId: string): Promise<{ recommended_driver: string | null; driver_type: string; warnings: string[]; errors: string[]; live_activation_possible: boolean }> {
  return getJson(`/api/rescue/hardware/devices/${encodeURIComponent(deviceId)}/driver-plan`);
}

export async function fetchPeripheralPrinters(): Promise<{ printers: RescuePrinterReport[] }> {
  return getJson('/api/rescue/peripherals/printers');
}

export async function fetchPeripheralScanners(): Promise<{ scanners: RescueScannerReport[] }> {
  return getJson('/api/rescue/peripherals/scanners');
}

export async function fetchRaspberryPiOverview(): Promise<RescuePiOverview> {
  return getJson('/api/rescue/platform/raspberry-pi');
}

export async function fetchCarrierStatus(): Promise<RescueCarrierStatus> {
  return getJson('/api/rescue/carrier/status');
}

export async function postCarrierLayoutPreview(carrierSizeBytes: number): Promise<RescueCarrierLayoutPlan> {
  return postJson('/api/rescue/carrier/layout-preview', { carrier_size_bytes: carrierSizeBytes });
}

export async function fetchProvisioningCatalog(): Promise<{ entries: RescueOsCatalogEntry[] }> {
  return getJson('/api/rescue/provision/catalog');
}
