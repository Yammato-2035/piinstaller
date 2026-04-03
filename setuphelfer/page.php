<?php
get_header();
while (have_posts()) : the_post();
    $slug = $post->post_name;
    $snippet_map = [
        'einstieg' => 'guided-start',
        'projekte' => 'projects',
        'tutorials' => 'tutorials',
        'fehlerhilfe' => 'troubleshooting',
        'community' => 'community',
        'download' => 'download',
        'sicherheit' => 'sicherheit',
        'changelog' => 'changelog',
        'kontakt' => 'kontakt',
        'cookie-richtlinie' => 'cookie-policy',
        'dokumentation' => 'documentation',
        'ueber-setuphelfer' => 'about',
        /* Legacy/manuelle Slugs: sonst leerer Seiteninhalt (nur WP-Titel) */
        'ueber' => 'about',
        'about' => 'about',
    ];
    if (isset($snippet_map[$slug])) {
        setuphelfer_render_snippet($snippet_map[$slug]);
    } else {
        echo '<section class="section"><article class="card"><h1>' . esc_html(get_the_title()) . '</h1><div class="entry-content">';
        the_content();
        echo '</div></article></section>';
    }
endwhile;
get_footer();
