<?php
if (!defined('ABSPATH')) {
    exit;
}

/**
 * Bridge cache only — no stick keys, no MFA secrets, no telemetry payloads.
 */
class Setuphelfer_Beta_Status_Cache {
    private string $table;

    public function __construct() {
        global $wpdb;
        $this->table = $wpdb->prefix . 'setuphelfer_beta_status_cache';
    }

    public function get(string $cache_key): ?array {
        global $wpdb;
        $row = $wpdb->get_row(
            $wpdb->prepare(
                "SELECT cache_value_json, expires_at FROM {$this->table} WHERE cache_key = %s LIMIT 1",
                $cache_key
            ),
            ARRAY_A
        );
        if (!$row) {
            return null;
        }
        if (strtotime((string) $row['expires_at']) < time()) {
            return null;
        }
        $decoded = json_decode((string) $row['cache_value_json'], true);
        return is_array($decoded) ? $decoded : null;
    }

    public function set(string $cache_key, array $value, int $ttl_seconds): void {
        global $wpdb;
        $expires = gmdate('Y-m-d H:i:s', time() + $ttl_seconds);
        $wpdb->replace(
            $this->table,
            [
                'cache_key' => $cache_key,
                'cache_value_json' => wp_json_encode($value),
                'fetched_at' => gmdate('Y-m-d H:i:s'),
                'expires_at' => $expires,
            ],
            ['%s', '%s', '%s', '%s']
        );
    }
}
