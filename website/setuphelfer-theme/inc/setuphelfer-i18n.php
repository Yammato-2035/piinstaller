<?php
/**
 * Zweisprachige Oberfläche (DE/EN): Locale aus Query, Cookie oder Browser.
 */

const SETUPHELFER_LANG_COOKIE = 'setuphelfer_lang';
const SETUPHELFER_LANG_QUERY = 'lang';

/**
 * @return 'de'|'en'
 */
function setuphelfer_locale() {
    static $cached = null;
    if ($cached !== null) {
        return $cached;
    }
    if (isset($_GET[SETUPHELFER_LANG_QUERY])) {
        $q = strtolower(sanitize_text_field(wp_unslash((string) $_GET[SETUPHELFER_LANG_QUERY])));
        if ($q === 'en' || $q === 'de') {
            $cached = $q;
            setuphelfer_locale_set_cookie($cached);
            return $cached;
        }
    }
    if (!empty($_COOKIE[SETUPHELFER_LANG_COOKIE])) {
        $c = strtolower(sanitize_text_field(wp_unslash((string) $_COOKIE[SETUPHELFER_LANG_COOKIE])));
        if ($c === 'en' || $c === 'de') {
            $cached = $c;
            return $cached;
        }
    }
    $accept = isset($_SERVER['HTTP_ACCEPT_LANGUAGE']) ? (string) $_SERVER['HTTP_ACCEPT_LANGUAGE'] : '';
    if ($accept !== '' && preg_match('/\ben(-[a-z]+)?\b/i', $accept)) {
        $cached = 'en';
        return $cached;
    }
    $cached = 'de';
    return $cached;
}

function setuphelfer_locale_set_cookie($locale) {
    if ($locale !== 'de' && $locale !== 'en') {
        return;
    }
    if (headers_sent()) {
        return;
    }
    $path = (defined('COOKIEPATH') && COOKIEPATH) ? COOKIEPATH : '/';
    $domain = defined('COOKIE_DOMAIN') ? COOKIE_DOMAIN : '';
    setcookie(
        SETUPHELFER_LANG_COOKIE,
        $locale,
        time() + 365 * DAY_IN_SECONDS,
        $path,
        $domain,
        is_ssl(),
        false
    );
    $_COOKIE[SETUPHELFER_LANG_COOKIE] = $locale;
}

/**
 * URL mit Sprachparameter (für Switcher).
 *
 * @param string $url Absolute oder relative URL.
 * @param string $locale 'de'|'en'
 */
function setuphelfer_locale_url($url, $locale) {
    return add_query_arg(SETUPHELFER_LANG_QUERY, $locale, $url);
}

/**
 * Übersetzte Theme-Zeichenketten (Chrome: Header, Footer, Consent).
 *
 * @param string $key z. B. 'brand.tagline'
 * @return string
 */
function setuphelfer_t($key) {
    $locale = setuphelfer_locale();
    $map = [
        'de' => [
            'nav.home' => 'Start',
            'brand.tagline' => 'SetupHelfer, Projekte, Tutorials und Community',
            'menu.open' => 'Menü',
            'search.label' => 'Website durchsuchen',
            'search.placeholder' => 'Suche…',
            'search.submit' => 'Los',
            'footer.tagline' => 'Die Plattform für den Einstieg in Raspberry Pi und Linux mit klaren Projekten, nachvollziehbaren Tutorials und einer Community ohne unnötige Hürden.',
            'footer.quick' => 'Schnellzugriff',
            'footer.more' => 'Weiterführend',
            'footer.guided' => 'Geführter Einstieg',
            'footer.projects' => 'Projekte',
            'footer.tutorials' => 'Tutorials',
            'footer.help' => 'Fehlerhilfe',
            'footer.download' => 'Download',
            'footer.community' => 'Community',
            'footer.docs' => 'Dokumentation',
            'footer.security' => 'Sicherheit',
            'footer.changelog' => 'Changelog',
            'footer.contact' => 'Kontakt',
            'footer.privacy' => 'Datenschutz',
            'footer.imprint' => 'Impressum',
            'consent.title' => 'Datenschutz-Hinweis:',
            'consent.text' => 'Optionale Analyse wird erst nach Zustimmung aktiviert.',
            'consent.accept' => 'Akzeptieren',
            'consent.decline' => 'Ablehnen',
            'consent.cookie' => 'Cookie-Richtlinie',
            'lang.de' => 'DE',
            'lang.en' => 'EN',
            'lang.switch' => 'Sprache',
        ],
        'en' => [
            'nav.home' => 'Home',
            'brand.tagline' => 'SetupHelfer — projects, tutorials and community',
            'menu.open' => 'Menu',
            'search.label' => 'Search this site',
            'search.placeholder' => 'Search…',
            'search.submit' => 'Go',
            'footer.tagline' => 'Your entry point to Raspberry Pi and Linux: clear projects, step‑by‑step tutorials, and a welcoming community.',
            'footer.quick' => 'Quick links',
            'footer.more' => 'More',
            'footer.guided' => 'Guided start',
            'footer.projects' => 'Projects',
            'footer.tutorials' => 'Tutorials',
            'footer.help' => 'Troubleshooting',
            'footer.download' => 'Download',
            'footer.community' => 'Community',
            'footer.docs' => 'Documentation',
            'footer.security' => 'Security',
            'footer.changelog' => 'Changelog',
            'footer.contact' => 'Contact',
            'footer.privacy' => 'Privacy',
            'footer.imprint' => 'Legal notice',
            'consent.title' => 'Privacy notice:',
            'consent.text' => 'Optional analytics only load after you consent.',
            'consent.accept' => 'Accept',
            'consent.decline' => 'Decline',
            'consent.cookie' => 'Cookie policy',
            'lang.de' => 'DE',
            'lang.en' => 'EN',
            'lang.switch' => 'Language',
        ],
    ];
    return isset($map[$locale][$key]) ? $map[$locale][$key] : ($map['de'][$key] ?? $key);
}

/**
 * Langer Markenhinweis im Footer (Produktnamen).
 */
function setuphelfer_footer_brand_notice_text() {
    $locale = setuphelfer_locale();
    if ($locale === 'en') {
        return 'Raspberry Pi, Linux and other product and brand names are trademarks of their respective owners. '
            . 'They are used only to describe compatibility, use cases and tutorials. '
            . 'Mentions of software (e.g. Docker, Samba, Jellyfin, OpenSSH, apt) are factual; there is no implied partnership with those vendors.';
    }
    return 'Raspberry Pi, Linux und weitere genannte Produkt- und Markennamen sind Eigentum der jeweiligen Rechteinhaber. '
        . 'Die Nennung dient ausschließlich der Beschreibung von Kompatibilität, Einsatzmöglichkeiten und Tutorials. '
        . 'Nennung von Software (z. B. Docker, Samba, Jellyfin, OpenSSH, apt) erfolgt sachlich zur Einordnung; es besteht keine behauptete Partnerschaft mit den jeweiligen Anbietern.';
}

/**
 * Deutsche Navigations-Bezeichnungen (WP-Menü) → Englisch bei Locale en.
 * Zusätzlich Abgleich über URL-Pfad, falls Titel im Backend angepasst wurden.
 *
 * @param string               $title Menütext.
 * @param WP_Post|object|null  $item  Menüeintrag.
 */
function setuphelfer_nav_menu_item_title_i18n($title, $item = null, $args = null, $depth = null) {
    if (!function_exists('setuphelfer_locale') || setuphelfer_locale() !== 'en') {
        return $title;
    }
    $t = trim(wp_strip_all_tags((string) $title));
    $by_title = [
        'Start' => 'Home',
        'Home' => 'Home',
        'Einstieg' => 'Guided start',
        'Geführter Einstieg' => 'Guided start',
        'Gefuehrter Einstieg' => 'Guided start',
        'Projekte' => 'Projects',
        'Tutorials' => 'Tutorials',
        'Fehlerhilfe' => 'Troubleshooting',
        'Community' => 'Community',
        'Download' => 'Download',
        'Dokumentation' => 'Documentation',
        'Über SetupHelfer' => 'About SetupHelfer',
        'Ueber SetupHelfer' => 'About SetupHelfer',
        'Über uns' => 'About',
        'Kontakt' => 'Contact',
        'Changelog' => 'Changelog',
        'Sicherheit' => 'Security',
        'Cookie-Richtlinie' => 'Cookie policy',
        'Datenschutz' => 'Privacy',
        'Impressum' => 'Legal notice',
    ];
    if (isset($by_title[$t])) {
        return $by_title[$t];
    }
    if ($item && !empty($item->url)) {
        if (untrailingslashit((string) $item->url) === untrailingslashit(home_url('/'))) {
            return 'Home';
        }
        $path = (string) wp_parse_url($item->url, PHP_URL_PATH);
        $path = trim($path, '/');
        $seg = $path;
        if (strpos($path, '/') !== false) {
            $parts = explode('/', $path);
            $seg = end($parts);
        }
        $by_slug = [
            '' => 'Home',
            'einstieg' => 'Guided start',
            'projekte' => 'Projects',
            'tutorials' => 'Tutorials',
            'fehlerhilfe' => 'Troubleshooting',
            'community' => 'Community',
            'download' => 'Download',
            'dokumentation' => 'Documentation',
            'ueber-setuphelfer' => 'About SetupHelfer',
            'ueber' => 'About SetupHelfer',
            'about' => 'About SetupHelfer',
            'kontakt' => 'Contact',
            'changelog' => 'Changelog',
            'sicherheit' => 'Security',
            'cookie-richtlinie' => 'Cookie policy',
            'datenschutz' => 'Privacy',
            'impressum' => 'Legal notice',
        ];
        if ($seg !== '' && isset($by_slug[$seg])) {
            return $by_slug[$seg];
        }
    }
    return $title;
}
add_filter('nav_menu_item_title', 'setuphelfer_nav_menu_item_title_i18n', 10, 4);

/**
 * CPT-Titel in der Oberfläche (z. B. Breadcrumb, Admin-Vorschau): Dokueinträge bei Locale en.
 */
function setuphelfer_translate_doc_entry_title($title, $post_id = null) {
    if (!function_exists('setuphelfer_locale') || setuphelfer_locale() !== 'en') {
        return $title;
    }
    if (is_admin() && !wp_doing_ajax()) {
        return $title;
    }
    if ($post_id === null || $post_id === '' || (int) $post_id === 0) {
        return $title;
    }
    $post = get_post((int) $post_id);
    if (!$post || $post->post_type !== 'doc_entry') {
        return $title;
    }
    if (!function_exists('setuphelfer_get_item')) {
        return $title;
    }
    $item = setuphelfer_get_item('doc_entry', $post->post_name);
    return ($item && !empty($item['title_en'])) ? $item['title_en'] : $title;
}
add_filter('the_title', 'setuphelfer_translate_doc_entry_title', 10, 2);

/**
 * Archiv-Titel (falls Theme/Core ihn ausgibt): Dokumentation → Documentation.
 */
function setuphelfer_translate_archive_title($title) {
    if (!function_exists('setuphelfer_locale') || setuphelfer_locale() !== 'en') {
        return $title;
    }
    if (is_post_type_archive('doc_entry')) {
        return 'Documentation';
    }
    return $title;
}
add_filter('get_the_archive_title', 'setuphelfer_translate_archive_title', 10, 1);
