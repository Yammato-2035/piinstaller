export const DANGEROUS_TEST_OPS = [
  'backup',
  'restore',
  'verify',
  'target_path_tests',
  'hardware_tests',
  'rescue_tests',
] as const

export const STANDALONE_SNAPSHOT_PATH = '/dev-dashboard.snapshot.json'

export const API_STATUS_PATH = '/api/dev-dashboard/status'
