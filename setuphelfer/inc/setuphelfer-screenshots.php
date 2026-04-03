<?php
/**
 * Einheitliche Screenshot-Darstellung: echte PNGs aus assets/screenshots/ oder klarer Tauri-Platzhalter.
 */

/**
 * @param string $basename Dateiname unter assets/screenshots/ (nur Basisname).
 * @return string Absoluter Pfad.
 */
function setuphelfer_screenshot_path( $basename ) {
	$basename = basename( (string) $basename );
	return get_template_directory() . '/assets/screenshots/' . $basename;
}

/**
 * @param string $basename Dateiname.
 * @return bool Datei vorhanden und nicht leer/trivial klein.
 */
function setuphelfer_screenshot_is_present( $basename ) {
	$path = setuphelfer_screenshot_path( $basename );
	if ( ! is_file( $path ) || ! is_readable( $path ) ) {
		return false;
	}
	$size = @filesize( $path );
	return is_int( $size ) && $size > 64;
}

/**
 * Markup innerhalb der Platzhalter-Box (fehlendes Bild).
 *
 * @param string $basename Anzuzeigender Dateiname.
 * @return string
 */
function setuphelfer_tauri_screenshot_placeholder_inner( $basename ) {
	$basename = basename( (string) $basename );
	$en       = function_exists( 'setuphelfer_locale' ) && setuphelfer_locale() === 'en';
	if ( $en ) {
		$label = 'Screenshot will be generated from the Tauri app: ' . $basename;
		return sprintf(
			'<div class="tauri-screenshot-placeholder" role="img" aria-label="%1$s">'
			. '<p class="tauri-screenshot-placeholder__title">Screenshot generated from the Tauri app</p>'
			. '<code class="tauri-screenshot-placeholder__file">%2$s</code>'
			. '</div>',
			esc_attr( $label ),
			esc_html( $basename )
		);
	}
	$label = 'Screenshot wird automatisch aus Tauri erzeugt: ' . $basename;
	return sprintf(
		'<div class="tauri-screenshot-placeholder" role="img" aria-label="%1$s">'
		. '<p class="tauri-screenshot-placeholder__title">Screenshot wird automatisch aus Tauri erzeugt</p>'
		. '<code class="tauri-screenshot-placeholder__file">%2$s</code>'
		. '</div>',
		esc_attr( $label ),
		esc_html( $basename )
	);
}

/**
 * @param string $basename z. B. screenshot-dashboard.png.
 * @param string $alt      Alt-Text.
 * @param string $context  hero | product | inner.
 * @return string HTML (src zunaechst relativ assets/... fuer nachfolgendes Rewriting).
 */
function setuphelfer_render_tauri_shot( $basename, $alt, $context ) {
	$basename = basename( (string) $basename );
	if ( ! preg_match( '/\.(png|jpe?g|webp)$/i', $basename ) ) {
		return '<!-- setuphelfer: ungueltiger Screenshot-Name -->';
	}
	$alt      = trim( (string) $alt );
	$context  = strtolower( trim( (string) $context ) );
	$present  = setuphelfer_screenshot_is_present( $basename );
	$rel_src  = 'assets/screenshots/' . $basename;
	$alt_attr = esc_attr( $alt );

	if ( $present ) {
		$loading = ( 'hero' === $context ) ? 'eager' : 'lazy';
		$class   = 'screenshot-img';
		if ( 'hero' === $context ) {
			$class = 'hero-laptop__shot';
		} elseif ( 'product' === $context ) {
			$class = 'product-shot-img';
		}
		return sprintf(
			'<img src="%s" alt="%s" class="%s" width="1280" height="800" loading="%s" decoding="async" />',
			esc_attr( $rel_src ),
			$alt_attr,
			esc_attr( $class ),
			esc_attr( $loading )
		);
	}

	$inner = setuphelfer_tauri_screenshot_placeholder_inner( $basename );
	if ( 'hero' === $context ) {
		return '<div class="hero-laptop__shot hero-laptop__shot--placeholder">' . $inner . '</div>';
	}
	if ( 'product' === $context ) {
		return '<div class="product-shot-img product-shot-img--placeholder">' . $inner . '</div>';
	}
	return '<div class="screenshot-img screenshot-img--placeholder">' . $inner . '</div>';
}

/**
 * Hinweistext: keine Mockups, echte App.
 *
 * @return string
 */
function setuphelfer_tauri_screenshot_policy_note_html() {
	if ( function_exists( 'setuphelfer_locale' ) && setuphelfer_locale() === 'en' ) {
		return '<p class="small screenshot-source-policy"><strong>Note:</strong> Screenshots are captured from the running app (not mockups). Missing images show a placeholder with the expected filename until exported from Tauri.</p>';
	}
	return '<p class="small screenshot-source-policy"><strong>Hinweis:</strong> Screenshots werden aus der laufenden App generiert (kein Mockup). Fehlende Bilder erscheinen als Platzhalter mit dem erwarteten Dateinamen bis zum Export aus Tauri.</p>';
}

/**
 * Ersetzt {{TAURI_SHOT:datei.png|Alt-Text|hero|product|inner}} und {{TAURI_SHOT_POLICY}}.
 *
 * @param string $html Snippet-HTML.
 * @return string
 */
function setuphelfer_expand_tauri_shot_placeholders( $html ) {
	$html = str_replace( '{{TAURI_SHOT_POLICY}}', setuphelfer_tauri_screenshot_policy_note_html(), $html );
	return preg_replace_callback(
		'/\{\{TAURI_SHOT:([^|]+)\|([^|]+)\|(hero|product|inner)\}\}/',
		function ( $m ) {
			return setuphelfer_render_tauri_shot( trim( $m[1] ), trim( $m[2] ), trim( $m[3] ) );
		},
		$html
	);
}
