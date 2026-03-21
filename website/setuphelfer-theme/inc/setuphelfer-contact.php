<?php
/**
 * Kontaktformular (Kurzcode [setuphelfer_contact_form]) — Versand per wp_mail an piinstaller@setuphelfer.de.
 */

function setuphelfer_contact_recipient_email() {
	return apply_filters( 'setuphelfer_contact_recipient', 'piinstaller@setuphelfer.de' );
}

/**
 * @return void
 */
function setuphelfer_handle_contact_post() {
	if ( ! isset( $_SERVER['REQUEST_METHOD'] ) || strtoupper( (string) $_SERVER['REQUEST_METHOD'] ) !== 'POST' ) {
		return;
	}
	if ( ! isset( $_POST['setuphelfer_contact_action'] ) || (string) $_POST['setuphelfer_contact_action'] !== '1' ) {
		return;
	}
	if ( ! isset( $_POST['setuphelfer_contact_nonce'] ) || ! wp_verify_nonce( sanitize_text_field( wp_unslash( (string) $_POST['setuphelfer_contact_nonce'] ) ), 'setuphelfer_contact' ) ) {
		wp_safe_redirect( add_query_arg( 'kontakt', 'nonce', setuphelfer_page_url( 'kontakt' ) ) );
		exit;
	}

	$name    = isset( $_POST['contact_name'] ) ? sanitize_text_field( wp_unslash( $_POST['contact_name'] ) ) : '';
	$email   = isset( $_POST['contact_email'] ) ? sanitize_email( wp_unslash( $_POST['contact_email'] ) ) : '';
	$subject = isset( $_POST['contact_subject'] ) ? sanitize_text_field( wp_unslash( $_POST['contact_subject'] ) ) : '';
	$detail  = isset( $_POST['contact_sonstiges_detail'] ) ? sanitize_textarea_field( wp_unslash( $_POST['contact_sonstiges_detail'] ) ) : '';
	$message = isset( $_POST['contact_message'] ) ? sanitize_textarea_field( wp_unslash( $_POST['contact_message'] ) ) : '';

	if ( $name === '' || ! is_email( $email ) || $message === '' || $subject === '' ) {
		wp_safe_redirect( add_query_arg( 'kontakt', 'fehlt', setuphelfer_page_url( 'kontakt' ) ) );
		exit;
	}
	if ( $subject === 'sonstiges' && $detail === '' ) {
		wp_safe_redirect( add_query_arg( 'kontakt', 'fehlt', setuphelfer_page_url( 'kontakt' ) ) );
		exit;
	}

	$labels = [
		'technik'      => 'SETUPHELFER – Technisches Problem',
		'fehler'       => 'SETUPHELFER – Fehler melden',
		'verbesserung' => 'SETUPHELFER – Verbesserungsvorschlag',
		'projekt'      => 'SETUPHELFER – Projektfrage',
		'sonstiges'    => 'SETUPHELFER – Sonstiges',
	];
	$sub_label = $labels[ $subject ] ?? $subject;

	$body  = "Kontaktanfrage über setuphelfer.de\n\n";
	$body .= "Name: {$name}\n";
	$body .= "E-Mail: {$email}\n";
	$body .= "Betreff: {$sub_label}\n";
	if ( $subject === 'sonstiges' && $detail !== '' ) {
		$body .= "Ergänzung (Sonstiges): {$detail}\n";
	}
	$body .= "\nNachricht:\n{$message}\n";

	$headers = [ 'Content-Type: text/plain; charset=UTF-8', 'Reply-To: ' . $name . ' <' . $email . '>' ];

	$sent = wp_mail(
		setuphelfer_contact_recipient_email(),
		'[SetupHelfer] ' . $sub_label,
		$body,
		$headers
	);

	wp_safe_redirect( add_query_arg( 'kontakt', $sent ? 'gesendet' : 'mailfehler', setuphelfer_page_url( 'kontakt' ) ) );
	exit;
}
add_action( 'template_redirect', 'setuphelfer_handle_contact_post', 5 );

/**
 * @return string
 */
function setuphelfer_contact_form_shortcode() {
	$url = esc_url( setuphelfer_page_url( 'kontakt' ) );

	$notice = '';
	if ( isset( $_GET['kontakt'] ) ) {
		$st = sanitize_text_field( wp_unslash( (string) $_GET['kontakt'] ) );
		if ( $st === 'gesendet' ) {
			$notice = '<p class="contact-form__notice contact-form__notice--ok" role="status">Nachricht wurde übermittelt. Bei E-Mail-Problemen des Servers bitte direkt an <a href="mailto:' . esc_attr( setuphelfer_contact_recipient_email() ) . '">' . esc_html( setuphelfer_contact_recipient_email() ) . '</a> schreiben.</p>';
		} elseif ( $st === 'fehlt' ) {
			$notice = '<p class="contact-form__notice contact-form__notice--err" role="alert">Bitte alle Pflichtfelder ausfüllen (bei „Sonstiges“ auch das Zusatzfeld).</p>';
		} elseif ( $st === 'nonce' ) {
			$notice = '<p class="contact-form__notice contact-form__notice--err" role="alert">Sitzung abgelaufen. Bitte Seite neu laden und erneut senden.</p>';
		} elseif ( $st === 'mailfehler' ) {
			$notice = '<p class="contact-form__notice contact-form__notice--err" role="alert">E-Mail konnte nicht gesendet werden. Bitte später erneut versuchen oder direkt an <a href="mailto:' . esc_attr( setuphelfer_contact_recipient_email() ) . '">' . esc_html( setuphelfer_contact_recipient_email() ) . '</a> schreiben.</p>';
		}
	}

	ob_start();
	?>
	<form class="contact-form card" method="post" action="<?php echo $url; ?>">
		<input type="hidden" name="setuphelfer_contact_nonce" value="<?php echo esc_attr( wp_create_nonce( 'setuphelfer_contact' ) ); ?>" />
		<input type="hidden" name="setuphelfer_contact_action" value="1" />
		<?php echo $notice; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
		<p>
			<label for="contact_name">Name <span class="required">*</span></label><br />
			<input id="contact_name" name="contact_name" type="text" required autocomplete="name" class="contact-form__input" value="<?php echo isset( $_POST['contact_name'] ) ? esc_attr( wp_unslash( (string) $_POST['contact_name'] ) ) : ''; ?>" />
		</p>
		<p>
			<label for="contact_email">E-Mail <span class="required">*</span></label><br />
			<input id="contact_email" name="contact_email" type="email" required autocomplete="email" class="contact-form__input" value="<?php echo isset( $_POST['contact_email'] ) ? esc_attr( wp_unslash( (string) $_POST['contact_email'] ) ) : ''; ?>" />
		</p>
		<p>
			<label for="contact_subject">Betreff <span class="required">*</span></label><br />
			<select id="contact_subject" name="contact_subject" required class="contact-form__input">
				<option value="">— bitte wählen —</option>
				<option value="technik" <?php selected( isset( $_POST['contact_subject'] ) ? (string) $_POST['contact_subject'] : '', 'technik' ); ?>>SETUPHELFER – Technisches Problem</option>
				<option value="fehler" <?php selected( isset( $_POST['contact_subject'] ) ? (string) $_POST['contact_subject'] : '', 'fehler' ); ?>>SETUPHELFER – Fehler melden</option>
				<option value="verbesserung" <?php selected( isset( $_POST['contact_subject'] ) ? (string) $_POST['contact_subject'] : '', 'verbesserung' ); ?>>SETUPHELFER – Verbesserungsvorschlag</option>
				<option value="projekt" <?php selected( isset( $_POST['contact_subject'] ) ? (string) $_POST['contact_subject'] : '', 'projekt' ); ?>>SETUPHELFER – Projektfrage</option>
				<option value="sonstiges" <?php selected( isset( $_POST['contact_subject'] ) ? (string) $_POST['contact_subject'] : '', 'sonstiges' ); ?>>SETUPHELFER – Sonstiges</option>
			</select>
		</p>
		<p id="contact-sonstiges-wrap" class="contact-form__sonstiges" hidden>
			<label for="contact_sonstiges_detail">Ergänzung (bei „Sonstiges“) <span class="required">*</span></label><br />
			<input id="contact_sonstiges_detail" name="contact_sonstiges_detail" type="text" class="contact-form__input" autocomplete="off" value="<?php echo isset( $_POST['contact_sonstiges_detail'] ) ? esc_attr( wp_unslash( (string) $_POST['contact_sonstiges_detail'] ) ) : ''; ?>" />
		</p>
		<p>
			<label for="contact_message">Nachricht <span class="required">*</span></label><br />
			<textarea id="contact_message" name="contact_message" rows="7" required class="contact-form__textarea"><?php echo isset( $_POST['contact_message'] ) ? esc_textarea( wp_unslash( (string) $_POST['contact_message'] ) ) : ''; ?></textarea>
		</p>
		<p>
			<button type="submit" class="btn btn-primary">Nachricht senden</button>
		</p>
		<p class="small">Empfänger: <?php echo esc_html( setuphelfer_contact_recipient_email() ); ?> — Es werden keine Daten an Drittanbieter außerhalb des Webhostings übermittelt (siehe Datenschutz).</p>
	</form>
	<script>
	(function(){
		var sel = document.getElementById('contact_subject');
		var wrap = document.getElementById('contact-sonstiges-wrap');
		var extra = document.getElementById('contact_sonstiges_detail');
		function toggle(){ var on = sel && sel.value === 'sonstiges'; if(wrap){ wrap.hidden = !on; } if(extra){ extra.required = !!on; if(!on) extra.value=''; } }
		if(sel){ sel.addEventListener('change', toggle); toggle(); }
	})();
	</script>
	<?php
	return (string) ob_get_clean();
}
add_shortcode( 'setuphelfer_contact_form', 'setuphelfer_contact_form_shortcode' );
