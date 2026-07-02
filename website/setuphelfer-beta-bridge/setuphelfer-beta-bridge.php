<?php
/**
 * Plugin Name: Setuphelfer Beta Bridge
 * Description: WordPress bridge for beta.setuphelfer.de — landing, status, no Root-of-Trust.
 * Version: 0.1.0
 * Author: Setuphelfer Team
 * Text Domain: setuphelfer-beta-bridge
 */

if (!defined('ABSPATH')) {
    exit;
}

define('SETUPHELFER_BETA_BRIDGE_VERSION', '0.1.0');

require_once plugin_dir_path(__FILE__) . 'includes/class-setuphelfer-beta-bridge.php';
require_once plugin_dir_path(__FILE__) . 'includes/class-setuphelfer-beta-status-cache.php';

function setuphelfer_beta_bridge_init(): void {
    Setuphelfer_Beta_Bridge::instance();
}
add_action('plugins_loaded', 'setuphelfer_beta_bridge_init');
