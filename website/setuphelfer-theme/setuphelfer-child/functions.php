<?php
/**
 * Child-Theme Funktionen
 *
 * Aktuell sind die meisten Styles/Logik im Parent-Theme.
 * Diese Datei sorgt nur dafür, dass bei späteren Anpassungen im Child
 * die Child-Styles korrekt nachgeladen werden.
 */

add_action('wp_enqueue_scripts', function () {
    wp_enqueue_style(
        'setuphelfer-child-style',
        get_stylesheet_uri(),
        ['setuphelfer-style'],
        '1.3.8.4'
    );
}, 20);

// BuddyPress 12+ lädt Assets standardmäßig nur auf BuddyPress-Seiten.
// Da wir BuddyPress-Komponenten (Activity-Stream) auf einer normalen WP-Page rendern,
// müssen wir hier die BuddyPress-Assets für genau diese Community-Seite erlauben.
add_filter('bp_enqueue_assets_in_bp_pages_only', function ($bp_pages_only) {
    if ( (function_exists('is_page_template') && is_page_template('page-community.php')) || (function_exists('is_page') && is_page('community')) ) {
        return false;
    }
    return $bp_pages_only;
}, 20);

