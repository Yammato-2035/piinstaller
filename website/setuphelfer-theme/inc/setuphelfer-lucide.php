<?php
/**
 * Einheitliche Icons: Lucide Static (lokal unter assets/icons/lucide/, ISC).
 *
 * In Snippets: {{LUCIDE:icon-name}} oder {{LUCIDE:icon-name:72}} fuer Groesse (16–256 px, Standard 48).
 */
function setuphelfer_lucide_icon( $name, $size = 48 ) {
	$name = preg_replace( '/[^a-z0-9-]/', '', strtolower( (string) $name ) );
	$size = (int) $size;
	if ( $size < 16 || $size > 256 ) {
		$size = 48;
	}
	$path = get_template_directory() . '/assets/icons/lucide/' . $name . '.svg';
	if ( ! is_readable( $path ) ) {
		return '<!-- lucide missing: ' . esc_html( $name ) . ' -->';
	}
	$svg = file_get_contents( $path );
	$svg = preg_replace( '/<!--.*?-->\s*/s', '', $svg );
	$svg = trim( $svg );
	$class = 'lucide lucide-icon';
	$svg = preg_replace(
		'/<svg\b[\s\S]*?>/',
		sprintf(
			'<svg xmlns="http://www.w3.org/2000/svg" class="%s" width="%d" height="%d" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" focusable="false" aria-hidden="true">',
			esc_attr( $class ),
			$size,
			$size
		),
		$svg,
		1
	);
	return $svg;
}

/**
 * Ersetzt {{LUCIDE:name}} und {{LUCIDE:name:size}} in Snippet-HTML.
 *
 * @param string $html Rohes Snippet-HTML.
 * @return string
 */
function setuphelfer_expand_lucide_placeholders( $html ) {
	return preg_replace_callback(
		'/\{\{LUCIDE:([a-z0-9-]+)(?::(\d+))?\}\}/',
		function ( $m ) {
			$sz = isset( $m[2] ) ? (int) $m[2] : 48;
			return setuphelfer_lucide_icon( $m[1], $sz );
		},
		$html
	);
}
