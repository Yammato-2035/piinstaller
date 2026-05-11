<?php
/**
 * Template Name: Community
 * Description: Community-Seite mit Intro-Snippet und bbPress-Forum.
 */

get_header();

// Wichtig: wie page.php — Lucide/TAURI-Platzhalter und Link-Mappings expandieren.
setuphelfer_render_snippet( 'community' );
?>

<section class="section community-page-forum">
    <div class="card">
        <?php
        if ( function_exists( 'setuphelfer_forum_welcome_markup' ) ) {
            setuphelfer_forum_welcome_markup();
        }
        if ( have_posts() ) :
            while ( have_posts() ) :
                the_post();
                the_content();
            endwhile;
        endif;

        echo '<div class="community-forum-shortcode">';
        echo do_shortcode( '[bbp-forum-index]' );
        echo '</div>';
        ?>
    </div>
</section>

<?php
get_footer();

