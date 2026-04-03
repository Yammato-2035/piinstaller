
<?php ?><!doctype html>
<html <?php language_attributes(); ?>>
<head>
<meta charset="<?php bloginfo('charset'); ?>">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" type="image/svg+xml" href="<?php echo esc_url(setuphelfer_asset('branding/setuphelfer-favicon.svg')); ?>">
<link rel="apple-touch-icon" href="<?php echo esc_url(setuphelfer_asset('branding/setuphelfer-app-icon.svg')); ?>">
<?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>
<header class="site-header">
  <div class="container topbar">
    <a class="brand" href="<?php echo esc_url(home_url('/')); ?>">
      <img src="<?php echo esc_url(setuphelfer_asset('branding/setuphelfer-logo-main.svg')); ?>" width="108" height="108" alt="SetupHelfer Logo" decoding="async">
      <div>SetupHelfer<small><?php echo esc_html(setuphelfer_t('brand.tagline')); ?></small></div>
    </a>
    <div class="setuphelfer-lang" role="navigation" aria-label="<?php echo esc_attr(setuphelfer_t('lang.switch')); ?>">
      <?php
      $loc = setuphelfer_locale();
      $qs_de = esc_url(add_query_arg('lang', 'de'));
      $qs_en = esc_url(add_query_arg('lang', 'en'));
      ?>
      <a class="setuphelfer-lang__link<?php echo $loc === 'de' ? ' is-active' : ''; ?>" href="<?php echo $qs_de; ?>" hreflang="de" lang="de"><?php echo esc_html(setuphelfer_t('lang.de')); ?></a>
      <span class="setuphelfer-lang__sep" aria-hidden="true">|</span>
      <a class="setuphelfer-lang__link<?php echo $loc === 'en' ? ' is-active' : ''; ?>" href="<?php echo $qs_en; ?>" hreflang="en" lang="en"><?php echo esc_html(setuphelfer_t('lang.en')); ?></a>
    </div>
    <button class="menu-toggle" type="button" aria-controls="site-nav" aria-expanded="false"><?php echo esc_html(setuphelfer_t('menu.open')); ?></button>
    <form class="site-search" role="search" method="get" action="<?php echo esc_url(home_url('/')); ?>">
      <label class="screen-reader-text" for="setuphelfer-site-search"><?php echo esc_html(setuphelfer_t('search.label')); ?></label>
      <input id="setuphelfer-site-search" class="site-search__input" type="search" name="s" value="<?php echo isset($_GET['s']) ? esc_attr(wp_unslash((string) $_GET['s'])) : ''; ?>" placeholder="<?php echo esc_attr(setuphelfer_t('search.placeholder')); ?>" autocomplete="off" />
      <button type="submit" class="site-search__submit"><?php echo esc_html(setuphelfer_t('search.submit')); ?></button>
    </form>
    <?php
    if (has_nav_menu('primary')) {
        wp_nav_menu([
            'theme_location' => 'primary',
            'container' => 'nav',
            'container_class' => 'nav',
            'container_id' => 'site-nav',
            'menu_class' => '',
            'fallback_cb' => false,
            'depth' => 1,
        ]);
    } else {
        setuphelfer_fallback_menu();
    }
    ?>
  </div>
</header>
<main class="container">
