<?php
/**
 * Suchergebnisse (WordPress-Standardparameter s).
 */
get_header();
?>
<section class="section">
  <h1>Suchergebnisse<?php echo get_search_query() ? ' — ' . esc_html(get_search_query()) : ''; ?></h1>
  <?php if (have_posts()) : ?>
    <div class="grid-2">
      <?php
      while (have_posts()) :
        the_post();
        ?>
        <article class="card">
          <h2><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h2>
          <p class="small"><?php echo esc_html(wp_strip_all_tags(get_the_excerpt())); ?></p>
        </article>
        <?php
      endwhile;
      ?>
    </div>
    <div class="pagination" style="margin-top:24px">
      <?php
      the_posts_pagination([
        'mid_size'  => 2,
        'prev_text' => 'Zurueck',
        'next_text' => 'Weiter',
      ]);
      ?>
    </div>
  <?php else : ?>
    <p>Keine Treffer fuer diese Suche.</p>
  <?php endif; ?>
</section>
<?php
get_footer();
