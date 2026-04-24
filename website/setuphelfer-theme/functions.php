
<?php
require get_template_directory() . '/inc/setuphelfer-i18n.php';
require get_template_directory() . '/inc/setuphelfer-data.php';
require get_template_directory() . '/inc/setuphelfer-lucide.php';
require get_template_directory() . '/inc/setuphelfer-screenshots.php';
require get_template_directory() . '/inc/setuphelfer-helpers.php';
require get_template_directory() . '/inc/setuphelfer-contact.php';
require get_template_directory() . '/inc/setuphelfer-legal-pages.php';

function setuphelfer_setup() {
    add_theme_support('title-tag');
    add_theme_support('post-thumbnails');
    add_theme_support('html5', ['search-form','comment-form','comment-list','gallery','caption','style','script']);
    register_nav_menus(['primary' => 'Hauptnavigation']);
}
add_action('after_setup_theme', 'setuphelfer_setup');

function setuphelfer_assets() {
    // Wichtig für Child-Themes: get_stylesheet_uri() würde im Child-Kontext die Child-Styles laden.
    // Wir wollen aber die Parent-Styles als Basis.
    wp_enqueue_style('setuphelfer-style', get_template_directory_uri() . '/style.css', [], '1.5.0.0');
    wp_enqueue_script('setuphelfer-nav', get_template_directory_uri().'/assets/js/nav.js', [], '1.5.0.0', true);
    wp_enqueue_script('setuphelfer-consent', get_template_directory_uri().'/assets/js/consent.js', [], '1.5.0.0', true);
    wp_enqueue_script('setuphelfer-live-status', get_template_directory_uri().'/assets/js/live-status.js', [], '1.0.1', true);
    $matomo_url = defined('SETUPHELFER_MATOMO_URL') ? constant('SETUPHELFER_MATOMO_URL') : '';
    $matomo_site_id = defined('SETUPHELFER_MATOMO_SITE_ID') ? constant('SETUPHELFER_MATOMO_SITE_ID') : '';
    if (!empty($matomo_url) && !empty($matomo_site_id)) {
        $config = [
            'url' => trailingslashit($matomo_url),
            'siteId' => (string) $matomo_site_id,
        ];
        wp_add_inline_script('setuphelfer-consent', 'window.setuphelferMatomo = ' . wp_json_encode($config) . ';', 'before');
    }
}
add_action('wp_enqueue_scripts', 'setuphelfer_assets');

function setuphelfer_dequeue_front_page_scripts() {
    if (is_front_page()) {
        wp_dequeue_script('setuphelfer-live-status');
    }
}
add_action('wp_enqueue_scripts', 'setuphelfer_dequeue_front_page_scripts', 99);

function setuphelfer_output_consent_banner() {
    ?>
    <div id="setuphelfer-consent" class="setuphelfer-consent" hidden>
      <div class="setuphelfer-consent__inner">
        <p><strong><?php echo esc_html(setuphelfer_t('consent.title')); ?></strong> <?php echo esc_html(setuphelfer_t('consent.text')); ?></p>
        <div class="setuphelfer-consent__actions">
          <button type="button" data-consent="accept" class="btn btn-primary"><?php echo esc_html(setuphelfer_t('consent.accept')); ?></button>
          <button type="button" data-consent="decline" class="btn btn-secondary"><?php echo esc_html(setuphelfer_t('consent.decline')); ?></button>
          <a href="<?php echo esc_url(home_url('/cookie-richtlinie/')); ?>"><?php echo esc_html(setuphelfer_t('consent.cookie')); ?></a>
        </div>
      </div>
    </div>
    <?php
}
add_action('wp_footer', 'setuphelfer_output_consent_banner', 30);

function setuphelfer_consent_styles() {
    $css = '.setuphelfer-consent{position:fixed;left:16px;right:16px;bottom:16px;z-index:99}.setuphelfer-consent__inner{background:#fff;border:1px solid #d6dfdc;border-radius:12px;box-shadow:0 10px 22px rgba(20,30,30,.08);padding:14px}.setuphelfer-consent__inner p{margin:0 0 10px 0}.setuphelfer-consent__actions{display:flex;flex-wrap:wrap;gap:10px;align-items:center}';
    wp_add_inline_style('setuphelfer-style', $css);
}
add_action('wp_enqueue_scripts', 'setuphelfer_consent_styles', 40);

function setuphelfer_register_types() {
    register_post_type('projekt', [
        'labels' => ['name' => 'Projekte', 'singular_name' => 'Projekt'],
        'public' => true,
        'has_archive' => 'projekte',
        'rewrite' => ['slug' => 'projekte'],
        'supports' => ['title','editor','excerpt','thumbnail'],
        'menu_icon' => 'dashicons-screenoptions',
        'show_in_rest' => true,
    ]);
    register_post_type('tutorial', [
        'labels' => ['name' => 'Tutorials', 'singular_name' => 'Tutorial'],
        'public' => true,
        'has_archive' => 'tutorials',
        'rewrite' => ['slug' => 'tutorials'],
        'supports' => ['title','editor','excerpt','thumbnail'],
        'menu_icon' => 'dashicons-welcome-learn-more',
        'show_in_rest' => true,
    ]);
    register_post_type('fehlerhilfe', [
        'labels' => ['name' => 'Fehlerhilfe', 'singular_name' => 'Fehlerhilfe'],
        'public' => true,
        'has_archive' => 'fehlerhilfe',
        'rewrite' => ['slug' => 'fehlerhilfe'],
        'supports' => ['title','editor','excerpt','thumbnail'],
        'menu_icon' => 'dashicons-warning',
        'show_in_rest' => true,
    ]);
    register_post_type('doc_entry', [
        'labels' => ['name' => 'Dokumentation', 'singular_name' => 'Dokueintrag'],
        'public' => true,
        'has_archive' => 'dokumentation',
        'rewrite' => ['slug' => 'dokumentation'],
        'supports' => ['title','editor','excerpt','thumbnail'],
        'menu_icon' => 'dashicons-media-document',
        'show_in_rest' => true,
    ]);

    $taxonomies = [
        'schwierigkeitsgrad' => 'Schwierigkeitsgrad',
        'plattform' => 'Plattform',
        'einsatzzweck' => 'Einsatzzweck',
        'themengebiet' => 'Themengebiet',
    ];
    foreach ($taxonomies as $slug => $label) {
        register_taxonomy($slug, ['projekt', 'tutorial', 'fehlerhilfe'], [
            'labels' => [
                'name' => $label,
                'singular_name' => $label,
            ],
            'public' => true,
            'hierarchical' => true,
            'show_in_rest' => true,
            'rewrite' => ['slug' => $slug],
        ]);
    }
}
add_action('init', 'setuphelfer_register_types');

function setuphelfer_seed_content() {
    $pages = [
        'home' => ['title' => 'Home', 'content' => ''],
        'einstieg' => ['title' => 'Gefuehrter Einstieg', 'content' => ''],
        'projekte' => ['title' => 'Projekte', 'content' => ''],
        'tutorials' => ['title' => 'Tutorials', 'content' => ''],
        'fehlerhilfe' => ['title' => 'Fehlerhilfe', 'content' => ''],
        'community' => ['title' => 'Community', 'content' => ''],
        'download' => ['title' => 'Download', 'content' => ''],
        'sicherheit' => ['title' => 'Sicherheit', 'content' => ''],
        'changelog' => ['title' => 'Changelog', 'content' => ''],
        'kontakt' => [
            'title' => 'Kontakt',
            'content' => '
                <h2>Kontakt</h2>
                <p>Für Rückfragen, Hinweise oder Korrekturen kannst du eine E-Mail schreiben an:<br>
                <a href="mailto:volker.glienke&#64;googlemail.com">volker.glienke&#64;googlemail.com</a></p>
                <p>Bitte beschreibe bei technischen Problemen möglichst genau:
                System, Version, Fehlermeldung, bisherige Schritte.</p>
            ',
        ],
        'cookie-richtlinie' => [
            'title' => 'Cookie-Richtlinie',
            'content' => '
                <h2>Cookie-Richtlinie</h2>
                <p>Diese Website verwendet technisch notwendige Speicherungen für die Grundfunktion.</p>
                <p>Optionale Statistik-/Analyse-Cookies werden nur nach Zustimmung gesetzt.</p>
                <p>Du kannst deine Auswahl jederzeit über den Hinweisbanner erneut treffen.</p>
            ',
        ],
        'dokumentation' => ['title' => 'Dokumentation', 'content' => ''],
        'ueber-setuphelfer' => ['title' => 'Über SetupHelfer', 'content' => ''],
        'impressum' => [
            'title' => 'Impressum',
            'content' => setuphelfer_get_impressum_html(),
        ],
        'datenschutz' => [
            'title' => 'Datenschutz',
            'content' => setuphelfer_get_datenschutz_html(),
        ],
    ];

    $page_ids = [];
    $created_any = false;
    $needs_update = false;
    $expected_impressum_version = 'Impressum-Textversion 2025-03';
    $expected_datenschutz_version = 'Datenschutz-Textversion 2025-03';

    // Wenn das Seeden bereits durchgeführt wurde, aber einzelne Seiten fehlen (z.B. nach Code-Update),
    // erzeugen wir nur die fehlenden Seiten nach.
    $seeded = (bool) get_option('setuphelfer_seeded_v2');
    $missing_any = false;
    foreach (array_keys($pages) as $slug) {
        if (!get_page_by_path($slug)) {
            $missing_any = true;
            break;
        }
    }
    // Wenn Seiten existieren, aber deren Inhalt nur "Platzhalter" ist (z.B. durch alte Seed-Version),
    // dann sollen wir den Inhalt aktualisieren.
    foreach (['impressum', 'datenschutz'] as $slug) {
        $existing = get_page_by_path($slug);
        if ($existing) {
            $content = (string) ($existing->post_content ?? '');
            if (trim($content) === '' || stripos($content, 'platzhalter') !== false) {
                $needs_update = true;
                break;
            }

            if ($slug === 'impressum') {
                if (stripos($content, $expected_impressum_version) === false) {
                    $needs_update = true;
                    break;
                }
            }

            if ($slug === 'datenschutz') {
                if (stripos($content, $expected_datenschutz_version) === false) {
                    $needs_update = true;
                    break;
                }
            }
        }
    }
    if ($seeded && !$missing_any && !$needs_update) {
        return;
    }

    foreach ($pages as $slug => $page) {
        $existing = get_page_by_path($slug);
        if ($existing) {
            $page_ids[$slug] = $existing->ID;
            if (in_array($slug, ['impressum', 'datenschutz'], true)) {
                $content = (string) ($existing->post_content ?? '');
                if (trim($content) === '' || stripos($content, 'platzhalter') !== false) {
                    wp_update_post([
                        'ID' => $existing->ID,
                        'post_content' => $page['content'],
                    ]);
                    $created_any = true;
                } elseif ($slug === 'impressum' && stripos($content, $expected_impressum_version) === false) {
                    wp_update_post([
                        'ID' => $existing->ID,
                        'post_content' => $page['content'],
                    ]);
                    $created_any = true;
                } elseif ($slug === 'datenschutz' && stripos($content, $expected_datenschutz_version) === false) {
                    wp_update_post([
                        'ID' => $existing->ID,
                        'post_content' => $page['content'],
                    ]);
                    $created_any = true;
                }
            }
            continue;
        }
        $page_ids[$slug] = wp_insert_post([
            'post_type' => 'page',
            'post_status' => 'publish',
            'post_title' => $page['title'],
            'post_name' => $slug,
            'post_content' => $page['content'],
        ]);
        $created_any = true;
    }

    if (!empty($page_ids['home'])) {
        if (get_option('show_on_front') !== 'page') {
            update_option('show_on_front', 'page');
        }
        $current_front = (int) get_option('page_on_front');
        if ($current_front !== (int) $page_ids['home']) {
            update_option('page_on_front', (int) $page_ids['home']);
        }
    }

    foreach (setuphelfer_projects() as $slug => $item) {
        $post_id = setuphelfer_ensure_post('projekt', $slug, $item['title'], $item['excerpt']);
        if (!empty($item['difficulty'])) {
            wp_set_object_terms($post_id, $item['difficulty'], 'schwierigkeitsgrad', false);
        }
        wp_set_object_terms($post_id, 'Raspberry Pi', 'plattform', false);
        wp_set_object_terms($post_id, 'Projekt', 'themengebiet', true);
    }
    foreach (setuphelfer_tutorials() as $slug => $item) {
        $post_id = setuphelfer_ensure_post('tutorial', $slug, $item['title'], $item['excerpt']);
        if (!empty($item['difficulty'])) {
            wp_set_object_terms($post_id, $item['difficulty'], 'schwierigkeitsgrad', false);
        }
        wp_set_object_terms($post_id, 'Raspberry Pi', 'plattform', false);
        wp_set_object_terms($post_id, 'Tutorial', 'themengebiet', true);
    }
    foreach (setuphelfer_docs() as $slug => $item) {
        setuphelfer_ensure_post('doc_entry', $slug, $item['title'], $item['excerpt']);
    }
    foreach (setuphelfer_fehlerhilfen() as $slug => $item) {
        $post_id = setuphelfer_ensure_post('fehlerhilfe', $slug, $item['title'], $item['excerpt']);
        wp_set_object_terms($post_id, 'Einsteigerhilfe', 'einsatzzweck', true);
        wp_set_object_terms($post_id, 'Fehlerhilfe', 'themengebiet', true);
    }

    if ($created_any) {
        flush_rewrite_rules();
    }
    update_option('setuphelfer_seeded_v2', 1);
}
add_action('after_switch_theme', 'setuphelfer_seed_content');
// Stellt sicher, dass fehlende Standard-Seiten nach Updates nachgezogen werden.
add_action('init', 'setuphelfer_seed_content');

function setuphelfer_seed_forums() {
    // Nur ausführen, wenn bbPress/Forum-Post-Type verfügbar ist.
    if (!post_type_exists('forum')) {
        return;
    }
    if (get_option('setuphelfer_forums_seeded_v1')) {
        return;
    }

    $forums = [
        'erste-schritte' => 'Erste Schritte',
        'projekte' => 'Projekte',
        'linux' => 'Linux',
        'fehler' => 'Fehler',
        'ideen' => 'Ideen',
    ];

    foreach ($forums as $slug => $title) {
        $existing = get_page_by_path($slug, OBJECT, 'forum');
        if ($existing) {
            continue;
        }
        wp_insert_post([
            'post_type' => 'forum',
            'post_status' => 'publish',
            'post_title' => $title,
            'post_name' => $slug,
            'post_content' => '',
        ]);
    }

    update_option('setuphelfer_forums_seeded_v1', 1);
}
add_action('init', 'setuphelfer_seed_forums', 30);

function setuphelfer_cleanup_legacy_forum() {
    // Nur ausführen, wenn bbPress/Forum verfügbar ist.
    if (!post_type_exists('forum')) {
        return;
    }
    // Einmalige Bereinigung.
    if (get_option('setuphelfer_forums_cleanup_v1')) {
        return;
    }

    $legacy_forum = get_page_by_path('allgemeines-forum', OBJECT, 'forum');
    if (!$legacy_forum) {
        update_option('setuphelfer_forums_cleanup_v1', 1);
        return;
    }

    $topic_type = function_exists('bbp_get_topic_post_type') ? bbp_get_topic_post_type() : 'topic';
    $has_topics = get_posts([
        'post_type' => $topic_type,
        'post_status' => ['publish', 'private', 'pending', 'draft'],
        'post_parent' => (int) $legacy_forum->ID,
        'fields' => 'ids',
        'posts_per_page' => 1,
        'no_found_rows' => true,
    ]);

    // Nur leeres Legacy-Forum entfernen, um keine Inhalte zu verlieren.
    if (empty($has_topics)) {
        wp_trash_post((int) $legacy_forum->ID);
    }

    update_option('setuphelfer_forums_cleanup_v1', 1);
}
add_action('init', 'setuphelfer_cleanup_legacy_forum', 31);

function setuphelfer_meta_title($title) {
    $en = function_exists('setuphelfer_locale') && setuphelfer_locale() === 'en';
    if ($en) {
        if (is_page('einstieg')) {
            return 'Guided start | SetupHelfer';
        }
        if (is_page('projekte') || is_post_type_archive('projekt')) {
            return 'Projects for Raspberry Pi | SetupHelfer';
        }
        if (is_page('tutorials') || is_post_type_archive('tutorial')) {
            return 'Tutorials | SetupHelfer';
        }
        if (is_page('fehlerhilfe')) {
            return 'Troubleshooting | SetupHelfer';
        }
        if (is_page('community')) {
            return 'Community & forum | SetupHelfer';
        }
        if (is_page('download')) {
            return 'Download SetupHelfer | SetupHelfer';
        }
        if (is_page('changelog')) {
            return 'Changelog | SetupHelfer';
        }
        if (is_page('kontakt')) {
            return 'Contact | SetupHelfer';
        }
        if (is_page('cookie-richtlinie')) {
            return 'Cookie policy | SetupHelfer';
        }
        if (is_page('datenschutz')) {
            return 'Privacy | SetupHelfer';
        }
        if (is_page('impressum')) {
            return 'Legal notice | SetupHelfer';
        }
        if (is_page('sicherheit')) {
            return 'Security | SetupHelfer';
        }
        if (is_page('ueber-setuphelfer') || is_page('ueber') || is_page('about')) {
            return 'About SetupHelfer | SetupHelfer';
        }
        if (is_post_type_archive('doc_entry')) {
            return 'Documentation | SetupHelfer';
        }
        if (is_singular('doc_entry')) {
            $slug = get_post_field('post_name', get_queried_object_id());
            $item = setuphelfer_get_item('doc_entry', $slug);
            if ($item && !empty($item['title_en'])) {
                return $item['title_en'] . ' | SetupHelfer';
            }
        }
        return $title;
    }
    if (is_page('einstieg')) {
        return 'Gefuehrter Einstieg | SetupHelfer';
    }
    if (is_page('projekte') || is_post_type_archive('projekt')) {
        return 'Projekte fuer Raspberry Pi | SetupHelfer';
    }
    if (is_page('tutorials') || is_post_type_archive('tutorial')) {
        return 'Tutorials fuer Einsteiger | SetupHelfer';
    }
    if (is_page('fehlerhilfe')) {
        return 'Fehlerhilfe | SetupHelfer';
    }
    if (is_page('community')) {
        return 'Community und Forum | SetupHelfer';
    }
    if (is_page('download')) {
        return 'Download SetupHelfer | SetupHelfer';
    }
    if (is_page('changelog')) {
        return 'Changelog | SetupHelfer';
    }
    if (is_page('kontakt')) {
        return 'Kontakt | SetupHelfer';
    }
    if (is_page('cookie-richtlinie')) {
        return 'Cookie-Richtlinie | SetupHelfer';
    }
    if (is_page('datenschutz')) {
        return 'Datenschutz | SetupHelfer';
    }
    if (is_page('impressum')) {
        return 'Impressum | SetupHelfer';
    }
    return $title;
}
add_filter('pre_get_document_title', 'setuphelfer_meta_title');

function setuphelfer_html_lang($output) {
    if (!function_exists('setuphelfer_locale')) {
        return $output;
    }
    $loc = setuphelfer_locale();
    if (preg_match('/lang="[^"]*"/', $output)) {
        return preg_replace('/lang="[^"]*"/', 'lang="' . esc_attr($loc) . '"', $output, 1);
    }
    return 'lang="' . esc_attr($loc) . '" ' . $output;
}
add_filter('language_attributes', 'setuphelfer_html_lang', 20);

function setuphelfer_meta_description() {
    $en = function_exists('setuphelfer_locale') && setuphelfer_locale() === 'en';
    if ($en) {
        $description = 'SetupHelfer helps you get started with Raspberry Pi and Linux: clear steps, projects, tutorials, troubleshooting and community.';
        if (is_page('einstieg')) {
            $description = 'Guided start in four steps: device, goal, experience level and a clear recommendation.';
        }
        if (is_page('projekte') || is_post_type_archive('projekt')) {
            $description = 'Project archive with difficulty, duration and clear paths for Raspberry Pi and Linux.';
        }
        if (is_page('tutorials') || is_post_type_archive('tutorial')) {
            $description = 'Beginner-friendly tutorials with prerequisites, duration, steps and common pitfalls.';
        }
        if (is_page('fehlerhilfe')) {
            $description = 'Troubleshooting with practical checks for boot, network, installation and hardware.';
        }
        if (is_page('community')) {
            $description = 'Community and forum categories for first steps, projects, Linux, errors and ideas.';
        }
        if (is_page('download')) {
            $description = 'Download SetupHelfer with version notes, system hints, changelog and security information.';
        }
        if (is_page('ueber-setuphelfer') || is_page('ueber') || is_page('about')) {
            $description = 'How SetupHelfer evolved from a small installer into a connected help stack: app, website, tutorials and community.';
        }
        if (is_post_type_archive('doc_entry')) {
            $description = 'Documentation index: installation, backup, Docker, mail server, diagnostics — structured entry for SetupHelfer.';
        }
        if (is_singular('tutorial')) {
            $description = wp_strip_all_tags(get_the_excerpt());
        }
        if (is_singular('projekt')) {
            $description = wp_strip_all_tags(get_the_excerpt());
        }
        if (is_singular('fehlerhilfe')) {
            $description = wp_strip_all_tags(get_the_excerpt());
        }
        if (is_singular('doc_entry')) {
            $slug = get_post_field('post_name', get_queried_object_id());
            $item = setuphelfer_get_item('doc_entry', $slug);
            if ($item && !empty($item['title_en'])) {
                $description = 'SetupHelfer documentation: ' . $item['title_en'] . '.';
            } else {
                $description = wp_strip_all_tags(get_the_excerpt());
            }
        }
    } else {
        $description = 'SetupHelfer begleitet Einsteiger bei Raspberry Pi und Linux mit klaren Schritten, Projekten, Tutorials, Fehlerhilfe und Community.';
        if (is_page('einstieg')) {
            $description = 'Gefuehrter Einstieg in 4 Schritten: Geraet, Ziel, Erfahrungslevel und klare Empfehlung fuer den Start.';
        }
        if (is_page('projekte') || is_post_type_archive('projekt')) {
            $description = 'Projektarchiv mit Schwierigkeit, Dauer und klaren Startpfaden fuer Raspberry Pi und Linux.';
        }
        if (is_page('tutorials') || is_post_type_archive('tutorial')) {
            $description = 'Verstaendliche Tutorials mit Voraussetzungen, Dauer, Schritten und typischen Fehlern.';
        }
        if (is_page('fehlerhilfe')) {
            $description = 'Fehlerhilfe mit konkreten Diagnosen fuer Boot, Netzwerk, Installation und Hardware.';
        }
        if (is_page('community')) {
            $description = 'Community mit Forum-Kategorien fuer Erste Schritte, Projekte, Linux, Fehler und Ideen.';
        }
        if (is_page('download')) {
            $description = 'Download von SetupHelfer mit Version, Systemhinweisen, Changelog und Sicherheitsinformationen.';
        }
        if (is_singular('tutorial')) {
            $description = wp_strip_all_tags(get_the_excerpt());
        }
        if (is_singular('projekt')) {
            $description = wp_strip_all_tags(get_the_excerpt());
        }
        if (is_singular('fehlerhilfe')) {
            $description = wp_strip_all_tags(get_the_excerpt());
        }
        if (is_singular('doc_entry')) {
            $description = wp_strip_all_tags(get_the_excerpt());
        }
    }
    $description = trim(preg_replace('/\s+/', ' ', $description));
    if (function_exists('mb_substr')) {
        $description = mb_substr($description, 0, 155);
    } else {
        $description = substr($description, 0, 155);
    }
    echo '<meta name="description" content="' . esc_attr($description) . '">' . "\n";
}
add_action('wp_head', 'setuphelfer_meta_description', 5);

function setuphelfer_schema_org() {
    $schema = null;
    if (is_singular('tutorial')) {
        $schema = [
            '@context' => 'https://schema.org',
            '@graph' => [
                [
                    '@type' => 'Article',
                    'headline' => get_the_title(),
                    'description' => wp_strip_all_tags(get_the_excerpt()),
                    'mainEntityOfPage' => get_permalink(),
                ],
                [
                    '@type' => 'HowTo',
                    'name' => get_the_title(),
                    'description' => wp_strip_all_tags(get_the_excerpt()),
                    'totalTime' => 'PT30M',
                    'step' => [
                        ['@type' => 'HowToStep', 'name' => 'Voraussetzungen prüfen'],
                        ['@type' => 'HowToStep', 'name' => 'Schritte nacheinander ausführen'],
                        ['@type' => 'HowToStep', 'name' => 'Ergebnis und Fehler prüfen'],
                    ],
                    'mainEntityOfPage' => get_permalink(),
                ],
            ],
        ];
    } elseif (is_singular('doc_entry')) {
        $slug = get_post_field('post_name', get_the_ID());
        if (in_array($slug, ['boot-probleme', 'netzwerk-probleme', 'installations-probleme', 'hardware-probleme'], true)) {
            $schema = [
                '@context' => 'https://schema.org',
                '@type' => 'FAQPage',
                'mainEntity' => [
                    [
                        '@type' => 'Question',
                        'name' => 'Was ist das sichtbare Problem?',
                        'acceptedAnswer' => ['@type' => 'Answer', 'text' => 'Bitte starte mit dem konkreten Symptom und arbeite die Diagnose Schritt für Schritt ab.'],
                    ],
                    [
                        '@type' => 'Question',
                        'name' => 'Wann sollte ich die Community fragen?',
                        'acceptedAnswer' => ['@type' => 'Answer', 'text' => 'Wenn die Ursache nach den Basischecks unklar bleibt oder Spezialhardware beteiligt ist.'],
                    ],
                ],
            ];
        } else {
            $schema = [
                '@context' => 'https://schema.org',
                '@type' => 'Article',
                'headline' => get_the_title(),
                'description' => wp_strip_all_tags(get_the_excerpt()),
                'mainEntityOfPage' => get_permalink(),
            ];
        }
    } elseif (is_page('download')) {
        $schema = [
            '@context' => 'https://schema.org',
            '@type' => 'SoftwareApplication',
            'name' => 'SetupHelfer',
            'alternateName' => 'SetupHelfer Desktop',
            'applicationCategory' => 'UtilitiesApplication',
            'operatingSystem' => 'Linux, Raspberry Pi OS',
            'softwareVersion' => '1.5.0.0',
            'url' => home_url('/download/'),
            'author' => ['@type' => 'Person', 'name' => 'Volker Glienke'],
        ];
    } elseif (is_page('fehlerhilfe')) {
        $schema = [
            '@context' => 'https://schema.org',
            '@type' => 'FAQPage',
            'mainEntity' => [
                [
                    '@type' => 'Question',
                    'name' => 'Mein System startet nicht. Was zuerst prüfen?',
                    'acceptedAnswer' => ['@type' => 'Answer', 'text' => 'Netzteil, SD-Karte und Boot-Image einzeln prüfen und erst danach weitere Komponenten testen.'],
                ],
                [
                    '@type' => 'Question',
                    'name' => 'Wann sollte ich in die Community wechseln?',
                    'acceptedAnswer' => ['@type' => 'Answer', 'text' => 'Wenn die Basisdiagnose keine klare Ursache liefert oder mehrere Fehlerbilder gleichzeitig auftreten.'],
                ],
            ],
        ];
    }
    if ($schema) {
        echo '<script type="application/ld+json">' . wp_json_encode($schema, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE) . '</script>' . "\n";
    }
}
add_action('wp_head', 'setuphelfer_schema_org', 20);

function setuphelfer_security_headers() {
    if (headers_sent()) {
        return;
    }
    header('X-Frame-Options: SAMEORIGIN');
    header('X-Content-Type-Options: nosniff');
    header('Referrer-Policy: strict-origin-when-cross-origin');
    header("Content-Security-Policy: default-src 'self' https: data: blob: 'unsafe-inline' 'unsafe-eval'; img-src 'self' https: data: blob:; object-src 'none'; frame-ancestors 'self';");
}
add_action('send_headers', 'setuphelfer_security_headers');

function setuphelfer_force_https() {
    if (is_admin() || wp_doing_ajax() || wp_doing_cron()) {
        return;
    }
    $forwarded = isset($_SERVER['HTTP_X_FORWARDED_PROTO']) ? strtolower((string) $_SERVER['HTTP_X_FORWARDED_PROTO']) : '';
    $is_https = is_ssl() || $forwarded === 'https';
    if (!$is_https && !empty($_SERVER['HTTP_HOST']) && !empty($_SERVER['REQUEST_URI'])) {
        wp_safe_redirect('https://' . $_SERVER['HTTP_HOST'] . $_SERVER['REQUEST_URI'], 301);
        exit;
    }
}
add_action('template_redirect', 'setuphelfer_force_https', 1);

function setuphelfer_harden_endpoints($endpoints) {
    if (!is_user_logged_in()) {
        unset($endpoints['/wp/v2/users']);
        unset($endpoints['/wp/v2/users/(?P<id>[\d]+)']);
    }
    return $endpoints;
}
add_filter('rest_endpoints', 'setuphelfer_harden_endpoints');
add_filter('xmlrpc_enabled', '__return_false');

function setuphelfer_cleanup_primary_menu_items($items, $args) {
    if (empty($args->theme_location) || $args->theme_location !== 'primary') {
        return $items;
    }

    $blocked_slugs = ['impressum', 'datenschutz'];
    $filtered = [];

    foreach ($items as $item) {
        $remove = false;

        if (!empty($item->object) && $item->object === 'page' && !empty($item->object_id)) {
            $post = get_post((int) $item->object_id);
            if ($post && in_array($post->post_name, $blocked_slugs, true)) {
                $remove = true;
            }
        }

        if (!$remove && !empty($item->url)) {
            $path = wp_parse_url($item->url, PHP_URL_PATH);
            $path = is_string($path) ? trim($path, '/') : '';
            if (in_array($path, $blocked_slugs, true)) {
                $remove = true;
            }
        }

        if (!$remove) {
            $filtered[] = $item;
        }
    }

    return $filtered;
}
add_filter('wp_nav_menu_objects', 'setuphelfer_cleanup_primary_menu_items', 10, 2);
