
<?php
function setuphelfer_asset($path = '') {
    return trailingslashit(get_template_directory_uri()) . 'assets/' . ltrim($path, '/');
}

/**
 * GitHub-Repository-URL (für Download-Links, filterbar via `setuphelfer_github_repo_url`).
 */
function setuphelfer_github_repo_url() {
    return apply_filters('setuphelfer_github_repo_url', 'https://github.com/VolkerGlienke/piinstaller');
}

/**
 * Direktlink zur neuesten GitHub-Release-Seite (Artefakte dort auswählen).
 */
function setuphelfer_github_releases_latest_url() {
    return esc_url(untrailingslashit(setuphelfer_github_repo_url()) . '/releases/latest');
}

function setuphelfer_ensure_post($type, $slug, $title, $excerpt = '') {
    $existing = get_page_by_path($slug, OBJECT, $type);
    if ($existing) {
        $needs_update = ((string) $existing->post_title !== (string) $title) || ((string) $existing->post_excerpt !== (string) $excerpt);
        if ($needs_update) {
            wp_update_post([
                'ID' => $existing->ID,
                'post_title' => $title,
                'post_excerpt' => $excerpt,
            ]);
        }
        return $existing->ID;
    }
    return wp_insert_post([
        'post_type' => $type,
        'post_status' => 'publish',
        'post_title' => $title,
        'post_name' => $slug,
        'post_excerpt' => $excerpt,
        'post_content' => '',
    ]);
}

function setuphelfer_page_url($slug) {
    if ($slug === 'home') {
        return home_url('/');
    }
    if (in_array($slug, ['projekte','tutorials','fehlerhilfe','dokumentation'], true)) {
        if ($slug === 'projekte') return get_post_type_archive_link('projekt');
        if ($slug === 'tutorials') return get_post_type_archive_link('tutorial');
        if ($slug === 'fehlerhilfe') return get_post_type_archive_link('fehlerhilfe');
        if ($slug === 'dokumentation') return get_post_type_archive_link('doc_entry');
    }
    $page = get_page_by_path($slug);
    return $page ? get_permalink($page) : home_url('/' . $slug . '/');
}

function setuphelfer_snippet_mappings() {
    $map = [
        'index.html' => setuphelfer_page_url('home'),
        'guided-start.html' => setuphelfer_page_url('einstieg'),
        'projects.html' => get_post_type_archive_link('projekt'),
        'tutorials.html' => get_post_type_archive_link('tutorial'),
        'troubleshooting.html' => setuphelfer_page_url('fehlerhilfe'),
        'community.html' => setuphelfer_page_url('community'),
        'download.html' => setuphelfer_page_url('download'),
        'sicherheit.html' => setuphelfer_page_url('sicherheit'),
        'changelog.html' => setuphelfer_page_url('changelog'),
        'kontakt.html' => setuphelfer_page_url('kontakt'),
        'cookie-policy.html' => setuphelfer_page_url('cookie-richtlinie'),
        'datenschutz.html' => setuphelfer_page_url('datenschutz'),
        'impressum.html' => setuphelfer_page_url('impressum'),
        'documentation.html' => get_post_type_archive_link('doc_entry'),
        'about.html' => setuphelfer_page_url('ueber-setuphelfer'),
    ];
    foreach (setuphelfer_projects() as $slug => $item) {
        $post = get_page_by_path($slug, OBJECT, 'projekt');
        $map[$item['snippet'] . '.html'] = $post ? get_permalink($post) : home_url('/projekte/' . $slug . '/');
    }
    foreach (setuphelfer_tutorials() as $slug => $item) {
        $post = get_page_by_path($slug, OBJECT, 'tutorial');
        $map[$item['snippet'] . '.html'] = $post ? get_permalink($post) : home_url('/tutorials/' . $slug . '/');
    }
    foreach (setuphelfer_fehlerhilfen() as $slug => $item) {
        $post = get_page_by_path($slug, OBJECT, 'fehlerhilfe');
        $map[$item['snippet'] . '.html'] = $post ? get_permalink($post) : home_url('/fehlerhilfe/' . $slug . '/');
    }
    foreach (setuphelfer_docs() as $slug => $item) {
        $post = get_page_by_path($slug, OBJECT, 'doc_entry');
        $map[$item['snippet'] . '.html'] = $post ? get_permalink($post) : home_url('/dokumentation/' . $slug . '/');
    }
    return $map;
}

function setuphelfer_render_snippet($name) {
    $locale = function_exists('setuphelfer_locale') ? setuphelfer_locale() : 'de';
    $base = get_template_directory() . '/snippets/';
    $file = $base . $name . '.html';
    if ($locale === 'en') {
        $en = $base . 'en/' . $name . '.html';
        if (file_exists($en)) {
            $file = $en;
        }
    }
    if (!file_exists($file)) {
        return;
    }
    $html = file_get_contents($file);
    $html = setuphelfer_expand_lucide_placeholders($html);
    $html = setuphelfer_expand_tauri_shot_placeholders($html);
    $html = preg_replace_callback('#(src|href|data)="assets/([^"]+)"#', function($m) {
        return $m[1] . '="' . esc_url(setuphelfer_asset($m[2])) . '"';
    }, $html);
    // Legacy: Screenshots lagen unter /docs/screenshots/ (Webroot) — jetzt im Theme unter assets/screenshots/.
    $html = preg_replace_callback('#(src|href)="/docs/screenshots/([^"]+)"#', function($m) {
        return $m[1] . '="' . esc_url(setuphelfer_asset('screenshots/' . $m[2])) . '"';
    }, $html);
    // Platzhalter für filterbare Download-URLs (siehe download.html).
    $html = str_replace('{{RELEASES_LATEST}}', setuphelfer_github_releases_latest_url(), $html);
    // Lazy-Loading für alle Snippet-Bilder (Browser übernimmt Priorisierung).
    $html = preg_replace('/<img(?![^>]*\bloading=)/i', '<img loading="lazy"', $html);
    $html = preg_replace('/<img loading="lazy"([^>]*screenshot-dashboard\.png[^>]*)>/i', '<img loading="eager"$1>', $html);
    foreach (setuphelfer_snippet_mappings() as $from => $to) {
        $html = str_replace('href="' . $from . '"', 'href="' . esc_url($to) . '"', $html);
    }
    $html = do_shortcode( $html );
    echo $html; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
}

function setuphelfer_fallback_menu() {
    $items = [
        ['label' => setuphelfer_t('nav.home'), 'url' => setuphelfer_page_url('home')],
        ['label' => setuphelfer_t('footer.guided'), 'url' => setuphelfer_page_url('einstieg')],
        ['label' => setuphelfer_t('footer.projects'), 'url' => get_post_type_archive_link('projekt')],
        ['label' => setuphelfer_t('footer.tutorials'), 'url' => get_post_type_archive_link('tutorial')],
        ['label' => setuphelfer_t('footer.help'), 'url' => get_post_type_archive_link('fehlerhilfe')],
        ['label' => setuphelfer_t('footer.community'), 'url' => setuphelfer_page_url('community')],
        ['label' => setuphelfer_t('footer.download'), 'url' => setuphelfer_page_url('download')],
    ];
    echo '<nav id="site-nav" class="nav">';
    foreach ($items as $item) {
        $active = untrailingslashit($item['url']) === untrailingslashit((is_front_page() ? home_url('/') : home_url(add_query_arg([], $GLOBALS['wp']->request)))) ? ' class="active"' : '';
        echo '<a' . $active . ' href="' . esc_url($item['url']) . '">' . esc_html($item['label']) . '</a>';
    }
    echo '</nav>';
}

function setuphelfer_get_item($type, $slug) {
    if ($type === 'projekt') {
        $all = setuphelfer_projects();
    } elseif ($type === 'tutorial') {
        $all = setuphelfer_tutorials();
    } elseif ($type === 'fehlerhilfe') {
        $all = setuphelfer_fehlerhilfen();
    } else {
        $all = setuphelfer_docs();
    }
    return $all[$slug] ?? null;
}

/**
 * Menschlich formulierten Willkommenstext für den Forum-Bereich auf der Community-Seite ausgeben.
 */
function setuphelfer_forum_welcome_markup() {
    ?>
    <div class="forum-welcome">
        <h2 class="forum-welcome__title">Willkommen im Forum</h2>
        <p>Schön, dass du hier bist. Hinter den Beiträgen stecken echte Menschen, die Raspberry Pi und Linux nicht nur aus Tutorials kennen, sondern zu Hause wirklich einsetzen – mit denselben kleinen und großen Hürden wie du.</p>
        <p>Wenn etwas nicht klappt, du ein Projekt zeigen willst oder eine Idee einbringen möchtest: such dir einfach die passende Kategorie aus. Du musst hier kein Profi sein; ein paar konkrete Infos (was du vorhast, welches System, was genau passiert) reichen oft schon, damit andere gezielt helfen können.</p>
        <p class="forum-welcome__footnote">Vielen Dank, dass du mitliest und mitmachst – der Austausch lebt von genau solchen Fragen und Erfahrungen.</p>
    </div>
    <?php
}
