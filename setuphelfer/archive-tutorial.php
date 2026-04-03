
<?php
get_header();
$type = get_post_type();
if ($type === 'projekt') {
    setuphelfer_render_snippet('projects');
} elseif ($type === 'tutorial') {
    setuphelfer_render_snippet('tutorials');
} else {
    setuphelfer_render_snippet('documentation');
}
get_footer();
