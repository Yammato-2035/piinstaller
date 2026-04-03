
</main>
<footer class="site-footer">
  <div class="container footer-grid">
    <div>
      <div class="footer-brand">
        <img src="<?php echo esc_url(setuphelfer_asset('branding/setuphelfer-logo-main.svg')); ?>" width="96" height="96" alt="" loading="lazy" decoding="async" />
        <div>
          <span class="label">SetupHelfer</span>
          <p><?php echo esc_html(setuphelfer_t('footer.tagline')); ?></p>
        </div>
      </div>
      <p class="footer-copyright small">© 2026 Volker Glienke · SetupHelfer</p>
      <p class="site-brand-notice" role="note"><?php echo esc_html(setuphelfer_footer_brand_notice_text()); ?></p>
    </div>
    <div><span class="label"><?php echo esc_html(setuphelfer_t('footer.quick')); ?></span><p><a href="<?php echo esc_url(setuphelfer_page_url('einstieg')); ?>"><?php echo esc_html(setuphelfer_t('footer.guided')); ?></a><br><a href="<?php echo esc_url(get_post_type_archive_link('projekt')); ?>"><?php echo esc_html(setuphelfer_t('footer.projects')); ?></a><br><a href="<?php echo esc_url(get_post_type_archive_link('tutorial')); ?>"><?php echo esc_html(setuphelfer_t('footer.tutorials')); ?></a><br><a href="<?php echo esc_url(setuphelfer_page_url('fehlerhilfe')); ?>"><?php echo esc_html(setuphelfer_t('footer.help')); ?></a></p></div>
    <div><span class="label"><?php echo esc_html(setuphelfer_t('footer.more')); ?></span><p><a href="<?php echo esc_url(setuphelfer_page_url('download')); ?>"><?php echo esc_html(setuphelfer_t('footer.download')); ?></a><br><a href="<?php echo esc_url(setuphelfer_page_url('community')); ?>"><?php echo esc_html(setuphelfer_t('footer.community')); ?></a><br><a href="<?php echo esc_url(get_post_type_archive_link('doc_entry')); ?>"><?php echo esc_html(setuphelfer_t('footer.docs')); ?></a><br><a href="<?php echo esc_url(setuphelfer_page_url('sicherheit')); ?>"><?php echo esc_html(setuphelfer_t('footer.security')); ?></a><br><a href="<?php echo esc_url(setuphelfer_page_url('changelog')); ?>"><?php echo esc_html(setuphelfer_t('footer.changelog')); ?></a><br><a href="<?php echo esc_url(setuphelfer_page_url('kontakt')); ?>"><?php echo esc_html(setuphelfer_t('footer.contact')); ?></a><br><a href="<?php echo esc_url(setuphelfer_page_url('datenschutz')); ?>"><?php echo esc_html(setuphelfer_t('footer.privacy')); ?></a><br><a href="<?php echo esc_url(setuphelfer_page_url('impressum')); ?>"><?php echo esc_html(setuphelfer_t('footer.imprint')); ?></a></p></div>
  </div>
</footer>
<?php wp_footer(); ?>
</body></html>
