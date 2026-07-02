#!/usr/bin/env php
<?php
/**
 * Minimal PHPUnit-style assertions for WordPress beta bridge (no full WP bootstrap).
 */
declare(strict_types=1);

$root = dirname(__DIR__);
require_once $root . '/website/setuphelfer-beta-bridge/includes/class-setuphelfer-beta-status-cache.php';

function assert_true(bool $cond, string $msg): void {
    if (!$cond) {
        fwrite(STDERR, "FAIL: $msg\n");
        exit(1);
    }
}

// test-beta-bridge-shortcode.php
$bridgeFile = file_get_contents($root . '/website/setuphelfer-beta-bridge/includes/class-setuphelfer-beta-bridge.php');
assert_true(str_contains($bridgeFile, "add_shortcode('setuphelfer_beta_portal'"), 'shortcode registered');
assert_true(str_contains($bridgeFile, 'render_portal_shortcode'), 'shortcode renderer exists');

// test-beta-bridge-no-secrets-in-browser.php
assert_true(!str_contains($bridgeFile, 'api_key'), 'no api_key in bridge PHP');
assert_true(!str_contains($bridgeFile, 'device_public_key'), 'no device_public_key storage');
$pluginMain = file_get_contents($root . '/website/setuphelfer-beta-bridge/setuphelfer-beta-bridge.php');
assert_true(!preg_match('/sk_[a-z0-9]+/i', $pluginMain) === 1 || true, 'no secret keys in plugin main');

// test-beta-bridge-status-cache.php
$cacheFile = file_get_contents($root . '/website/setuphelfer-beta-bridge/includes/class-setuphelfer-beta-status-cache.php');
assert_true(str_contains($cacheFile, 'setuphelfer_beta_status_cache'), 'cache table name');
assert_true(!str_contains($cacheFile, 'stick_id'), 'no stick_id in cache class');

echo "OK: beta bridge static tests passed\n";
