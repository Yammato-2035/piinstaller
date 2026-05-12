<?php
get_header();
while (have_posts()) : the_post();
    $slug = $post->post_name;
    $type = get_post_type();
    $item = setuphelfer_get_item($type, $slug);
    if ($item && !empty($item['snippet'])) {
        setuphelfer_render_snippet($item['snippet']);
    } else {
        echo '<section class="section"><article class="card"><h1>' . esc_html(get_the_title()) . '</h1><div class="entry-content">';
        the_content();
        echo '</div></article></section>';
    }
endwhile;
get_footer();
