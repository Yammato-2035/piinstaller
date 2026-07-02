<?php
if (!defined('ABSPATH')) {
    exit;
}

final class Setuphelfer_Beta_Bridge {
    private static ?self $instance = null;

    public static function instance(): self {
        if (self::$instance === null) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    private function __construct() {
        add_shortcode('setuphelfer_beta_portal', [$this, 'render_portal_shortcode']);
        add_action('admin_init', [$this, 'register_settings']);
    }

    public function register_settings(): void {
        register_setting('setuphelfer_beta_bridge', 'setuphelfer_beta_api_base', [
            'type' => 'string',
            'sanitize_callback' => 'esc_url_raw',
            'default' => 'https://beta.setuphelfer.de',
        ]);
        register_setting('setuphelfer_beta_bridge', 'setuphelfer_beta_portal_url', [
            'type' => 'string',
            'sanitize_callback' => 'esc_url_raw',
            'default' => 'https://beta.setuphelfer.de',
        ]);
    }

    public function fetch_public_status(): array {
        $cache = new Setuphelfer_Beta_Status_Cache();
        $cached = $cache->get('beta_status');
        if ($cached !== null) {
            return $cached;
        }
        $base = rtrim((string) get_option('setuphelfer_beta_api_base', ''), '/');
        if ($base === '') {
            return ['status' => 'unconfigured'];
        }
        $response = wp_remote_get($base . '/public/v1/beta/status', ['timeout' => 8]);
        if (is_wp_error($response)) {
            return ['status' => 'error', 'message' => 'unreachable'];
        }
        $body = json_decode((string) wp_remote_retrieve_body($response), true);
        if (!is_array($body)) {
            $body = ['status' => 'invalid_response'];
        }
        $cache->set('beta_status', $body, 300);
        return $body;
    }

    public function render_portal_shortcode(): string {
        $status = $this->fetch_public_status();
        $portal = esc_url((string) get_option('setuphelfer_beta_portal_url', 'https://beta.setuphelfer.de'));
        ob_start();
        ?>
        <div class="setuphelfer-beta-portal" data-testid="setuphelfer-beta-portal">
            <h2><?php esc_html_e('Setuphelfer Beta', 'setuphelfer-beta-bridge'); ?></h2>
            <p><?php esc_html_e('Registrierung und Stick-Verwaltung erfolgen über den Beta-Service — nicht über WordPress.', 'setuphelfer-beta-bridge'); ?></p>
            <ul>
                <li><a href="<?php echo esc_url($portal); ?>"><?php esc_html_e('Registrieren / Login', 'setuphelfer-beta-bridge'); ?></a></li>
                <li><?php esc_html_e('Rettungsstick aktivieren', 'setuphelfer-beta-bridge'); ?></li>
                <li><?php esc_html_e('Betatestvereinbarung erforderlich', 'setuphelfer-beta-bridge'); ?></li>
            </ul>
            <p class="setuphelfer-beta-status" data-server-status="<?php echo esc_attr((string) ($status['status'] ?? 'unknown')); ?>">
                <?php esc_html_e('Beta-Status:', 'setuphelfer-beta-bridge'); ?>
                <?php echo esc_html((string) ($status['status'] ?? 'unknown')); ?>
            </p>
        </div>
        <?php
        return (string) ob_get_clean();
    }
}
