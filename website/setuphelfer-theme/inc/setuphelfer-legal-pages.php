<?php
/**
 * Mustertexte Impressum und Datenschutz (Deutschland / DSGVO).
 *
 * Hinweis: Kein Ersatz für individuelle Rechtsberatung — Anpassung an konkrete
 * Verhältnisse (Gewerbe, USt-ID, Hosting-Vertrag, Auftragsverarbeitung) durch
 * Fachanwalt oder Datenschutzbeauftragte empfohlen.
 */

/**
 * @return string HTML für die Seite „Impressum“ (post_content).
 */
function setuphelfer_get_impressum_html() {
    return <<<'HTML'
<p class="legal-meta screen-reader-text">Impressum-Textversion 2025-03</p>

<h2>Angaben gemäß § 5 TMG</h2>
<p>
Volker Glienke<br>
Erlenstraße 25<br>
47574 Goch<br>
Deutschland
</p>

<h2>Kontakt</h2>
<p>
E-Mail: <a href="mailto:volker.glienke&#64;googlemail.com">volker.glienke&#64;googlemail.com</a><br>
Projekt / Plattform SetupHelfer: <a href="mailto:piinstaller&#64;setuphelfer.de">piinstaller&#64;setuphelfer.de</a>
</p>
<p>Telefonische Erreichbarkeit wird nicht angeboten; Kontakt erfolgt bevorzugt per E-Mail.</p>

<h2>Umsatzsteuer</h2>
<p>Diese Website wird als nicht gewerbsmäßige, private Informationsplattform betrieben. Eine Umsatzsteuer-Identifikationsnummer wird nicht ausgewiesen, soweit keine steuerpflichtigen Leistungen erbracht werden.</p>

<h2>Verantwortlich für den Inhalt nach § 55 Abs. 2 RStV</h2>
<p>Volker Glienke, Anschrift wie oben.</p>

<h2>Haftung für Inhalte</h2>
<p>Als Diensteanbieter sind wir gemäß § 7 Abs. 1 TMG für eigene Inhalte auf diesen Seiten nach den allgemeinen Gesetzen verantwortlich. Nach §§ 8 bis 10 TMG sind wir als Diensteanbieter jedoch nicht verpflichtet, übermittelte oder gespeicherte fremde Informationen zu überwachen oder nach Umständen zu forschen, die auf eine rechtswidrige Tätigkeit hinweisen.</p>
<p>Verpflichtungen zur Entfernung oder Sperrung der Nutzung von Informationen nach den allgemeinen Gesetzen bleiben hiervon unberührt. Eine diesbezügliche Haftung ist erst ab dem Zeitpunkt der Kenntnis einer konkreten Rechtsverletzung möglich. Bei Bekanntwerden entsprechender Rechtsverletzungen werden wir diese Inhalte umgehend entfernen.</p>

<h2>Haftung für Links</h2>
<p>Unser Angebot enthält Links zu externen Websites Dritter, auf deren Inhalte wir keinen Einfluss haben. Deshalb können wir für diese fremden Inhalte auch keine Gewähr übernehmen. Für die Inhalte der verlinkten Seiten ist stets der jeweilige Anbieter oder Betreiber der Seiten verantwortlich. Die verlinkten Seiten wurden zum Zeitpunkt der Verlinkung auf mögliche Rechtsverstöße überprüft. Rechtswidrige Inhalte waren zum Zeitpunkt der Verlinkung nicht erkennbar.</p>
<p>Eine permanente inhaltliche Kontrolle der verlinkten Seiten ist jedoch ohne konkrete Anhaltspunkte einer Rechtsverletzung nicht zumutbar. Bei Bekanntwerden von Rechtsverletzungen werden wir derartige Links umgehend entfernen.</p>

<h2>Urheberrecht</h2>
<p>Die durch den Seitenbetreiber erstellten Inhalte und Werke auf diesen Seiten unterliegen dem deutschen Urheberrecht. Die Vervielfältigung, Bearbeitung, Verbreitung und jede Art der Verwertung außerhalb der Grenzen des Urheberrechts bedürfen der schriftlichen Zustimmung des jeweiligen Autors bzw. Erstellers. Downloads und Kopien dieser Seite sind nur für den privaten, nicht kommerziellen Gebrauch gestattet.</p>
<p>Soweit die Inhalte auf dieser Seite nicht vom Betreiber erstellt wurden, werden die Urheberrechte Dritter beachtet. Insbesondere werden Inhalte Dritter als solche gekennzeichnet. Sollten Sie trotzdem auf eine Urheberrechtsverletzung aufmerksam werden, bitten wir um einen entsprechenden Hinweis. Bei Bekanntwerden von Rechtsverletzungen werden wir derartige Inhalte umgehend entfernen.</p>

<h2>Streitbeilegung</h2>
<p>Die Europäische Kommission stellt eine Plattform zur Online-Streitbeilegung (OS) bereit: <a href="https://ec.europa.eu/consumers/odr/" target="_blank" rel="noopener noreferrer">https://ec.europa.eu/consumers/odr/</a>. Unsere E-Mail-Adresse finden Sie oben im Impressum.</p>
<p>Wir sind nicht bereit oder verpflichtet, an Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen, soweit dies für private, nicht gewerbliche Angebote zutrifft.</p>

<h2>Haftungshinweis zur Nutzung von Software und Anleitungen</h2>
<p>Die Nutzung der bereitgestellten Hilfen, Anleitungen und Software (einschließlich der Desktop-Anwendung „SetupHelfer“) erfolgt auf eigene Verantwortung. Für Schäden, die aus der Nutzung oder der Anwendung der Inhalte entstehen, wird keine Haftung übernommen, soweit gesetzlich zulässig.</p>
HTML;
}

/**
 * @return string HTML für die Seite „Datenschutz“ (post_content).
 */
function setuphelfer_get_datenschutz_html() {
    return <<<'HTML'
<p class="legal-meta screen-reader-text">Datenschutz-Textversion 2025-03</p>

<h2>Verantwortliche Stelle</h2>
<p>
Verantwortlich im Sinne der Datenschutz-Grundverordnung (DSGVO) und des Bundesdatenschutzgesetzes (BDSG) ist:<br><br>
Volker Glienke<br>
Erlenstraße 25<br>
47574 Goch<br>
Deutschland<br>
E-Mail: <a href="mailto:volker.glienke&#64;googlemail.com">volker.glienke&#64;googlemail.com</a>
</p>

<h2>Allgemeines zur Datenverarbeitung</h2>
<p>Der Schutz Ihrer personenbezogenen Daten ist uns wichtig. Personenbezogene Daten sind alle Daten, mit denen Sie persönlich identifiziert werden können. Die nachfolgenden Hinweise geben einen einfachen Überblick darüber, was mit Ihren Daten passiert, wenn Sie diese Website besuchen.</p>

<h2>Rechtsgrundlagen der Verarbeitung</h2>
<p>Sofern nicht im Einzelnen etwas anderes genannt ist, erfolgt die Verarbeitung personenbezogener Daten auf Grundlage von:</p>
<ul>
<li><strong>Art. 6 Abs. 1 lit. b DSGVO</strong>, soweit die Verarbeitung zur Erfüllung eines Vertrags oder vorvertraglicher Maßnahmen erforderlich ist (z.&nbsp;B. Beantwortung von Anfragen über ein Kontaktformular).</li>
<li><strong>Art. 6 Abs. 1 lit. f DSGVO</strong>, soweit die Verarbeitung zur Wahrung unserer berechtigten Interessen erforderlich ist (z.&nbsp;B. Betrieb, Sicherheit und Stabilität dieser Website, Server-Logfiles).</li>
<li><strong>Art. 6 Abs. 1 lit. a DSGVO</strong>, soweit Sie in die Verarbeitung eingewilligt haben (z.&nbsp;B. optionale Analyse nach Cookie-Einwilligung).</li>
</ul>

<h2>Hosting und Server-Logfiles</h2>
<p>Diese Website wird bei einem externen Hosting-Anbieter (Webhosting) betrieben. Dabei werden durch den Hosting-Dienst in der Regel sogenannte Server-Logfiles erhoben und kurzfristig gespeichert, insbesondere:</p>
<ul>
<li>IP-Adresse des anfragenden Rechners</li>
<li>Datum und Uhrzeit der Anfrage</li>
<li>angeforderte Datei / URL</li>
<li>übertragene Datenmenge</li>
<li>HTTP-Statuscode</li>
<li>Webbrowser und Betriebssystem (User-Agent, soweit übermittelt)</li>
<li>Referrer-URL (soweit übermittelt)</li>
</ul>
<p>Die Verarbeitung erfolgt zur Bereitstellung der Website, zur Gewährleistung der technischen Sicherheit (z.&nbsp;B. Abwehr von Angriffen) und zur Störungsbehebung. Rechtsgrundlage ist Art. 6 Abs. 1 lit. f DSGVO. Die Logfiles werden nach einer angemessenen Frist gelöscht oder anonymisiert, soweit der Hosting-Anbieter nicht gesetzlich zu einer längeren Aufbewahrung verpflichtet ist.</p>
<p><strong>Hinweis:</strong> Bitte ergänzen Sie den Namen und die Kontaktdaten Ihres konkreten Hosting-Anbieters sowie ggf. einen Auftragsverarbeitungsvertrag (AV-Vertrag) in Ihrer Dokumentation; bei Standard-Paketen (z.&nbsp;B. Plesk/Shared Hosting) gelten die Datenschutzhinweise des jeweiligen Anbieters.</p>

<h2>Zwecke der Verarbeitung und Speicherdauer</h2>
<p>Personenbezogene Daten werden nur so lange gespeichert, wie dies für den jeweiligen Zweck erforderlich ist oder gesetzliche Aufbewahrungsfristen bestehen. Kriterien für die Speicherdauer sind die jeweiligen gesetzlichen Verjährungs- und Aufbewahrungsfristen sowie unsere berechtigten Interessen an der IT-Sicherheit.</p>

<h2>Cookies und Einwilligung (Tracking)</h2>
<p>Diese Website kann technisch notwendige Cookies oder vergleichbare Speicherungen verwenden, die für den Betrieb der Seite erforderlich sind. Optionale Analyse- oder Statistikfunktionen (z.&nbsp;B. Matomo o.&nbsp;Ä.) werden nur geladen, wenn Sie dem zuvor im Cookie-Hinweis zugestimmt haben. Ohne Einwilligung findet kein derartiges Tracking statt. Rechtsgrundlage für einwilligungsbasierte Verarbeitung ist Art. 6 Abs. 1 lit. a DSGVO; Sie können eine erteilte Einwilligung mit Wirkung für die Zukunft widerrufen (siehe unten).</p>
<p>Näheres zu Cookies finden Sie in der <a href="/cookie-richtlinie/">Cookie-Richtlinie</a>.</p>

<h2>Kontaktformular</h2>
<p>Wenn Sie das Kontaktformular nutzen, werden die von Ihnen eingegebenen Daten (z.&nbsp;B. Name, E-Mail-Adresse, Nachrichtentext) zur Bearbeitung Ihrer Anfrage verarbeitet und per E-Mail an die im Formular angegebene Empfängeradresse übermittelt (typischerweise <a href="mailto:piinstaller&#64;setuphelfer.de">piinstaller&#64;setuphelfer.de</a>). Eine Weitergabe an Dritte zu Werbezwecken erfolgt nicht.</p>
<p>Rechtsgrundlage ist Art. 6 Abs. 1 lit. b DSGVO (Anfragen außerhalb eines Vertragsverhältnisses: berechtigtes Interesse an der Beantwortung Ihrer Anfrage gemäß Art. 6 Abs. 1 lit. f DSGVO i. V. m. Art. 6 Abs. 1 lit. b DSGVO analog).</p>
<p>Die Daten werden gelöscht, sobald die Speicherung für die Erledigung Ihrer Anfrage nicht mehr erforderlich ist, sofern keine gesetzlichen Aufbewahrungspflichten entgegenstehen.</p>

<h2>Kontakt per E-Mail</h2>
<p>Wenn Sie uns per E-Mail kontaktieren, werden die von Ihnen mitgeteilten Daten (mindestens die E-Mail-Adresse und der Inhalt der Nachricht) zur Bearbeitung der Anfrage verarbeitet und in der Regel in den Postfächern gespeichert. Rechtsgrundlage ist Art. 6 Abs. 1 lit. b bzw. lit. f DSGVO.</p>

<h2>bbPress / Community</h2>
<p>Wenn Forenfunktionen (z.&nbsp;B. bbPress in Verbindung mit BuddyPress) genutzt werden, verarbeiten wir die im jeweiligen Nutzungskonto und in Beiträgen angegebenen Daten zur Bereitstellung der Community-Funktion. Umfang und Zweck richten sich nach Ihren Einstellungen und den öffentlich sichtbaren Profilfeldern. Rechtsgrundlage ist Art. 6 Abs. 1 lit. b DSGVO (Nutzungsvertrag der Community) bzw. Art. 6 Abs. 1 lit. f DSGVO (Betrieb und Moderation).</p>
<p>Öffentlich sichtbare Inhalte können von Suchmaschinen indexiert werden; bitte beachten Sie dies bei der Veröffentlichung persönlicher Daten.</p>

<h2>WordPress und technische Kommentarfunktionen</h2>
<p>Diese Website basiert auf WordPress. Dabei können technische Daten (z.&nbsp;B. bei Anmeldung, Kommentaren oder Medien-Uploads) verarbeitet werden. Sofern Kommentarfunktionen aktiv sind, können der Kommentartext, Zeitstempel und ggf. Ihr gewählter Name gespeichert werden. Details ergeben sich aus den jeweiligen Einstellungen in WordPress.</p>

<h2>Externe Dienste und Verweise (z.&nbsp;B. GitHub)</h2>
<p>Auf dieser Website können Verweise auf externe Angebote (z.&nbsp;B. GitHub-Repository, Dokumentation) gesetzt sein. Beim Aufruf solcher Links gelten die Datenschutzhinweise des jeweiligen Drittanbieters. Wir haben keinen Einfluss auf die Datenverarbeitung dort.</p>

<h2>Verwendete Bilder und Medien</h2>
<p>Verwendete Bilder stammen aus eigenen Screenshots der Anwendung oder aus lizenzfrei nutzbaren Quellen (siehe Bildnachweise auf den jeweiligen Seiten, soweit erforderlich).</p>

<h2>Markennamen</h2>
<p>Die Nennung von Raspberry Pi, Linux und anderen Marken dient der Beschreibung von Kompatibilität und Nutzung; es wird keine Partnerschaft oder offizielle Zugehörigkeit behauptet.</p>

<h2>Ihre Rechte</h2>
<p>Sie haben — soweit die gesetzlichen Voraussetzungen erfüllt sind — insbesondere:</p>
<ul>
<li>Recht auf Auskunft (Art. 15 DSGVO)</li>
<li>Recht auf Berichtigung (Art. 16 DSGVO)</li>
<li>Recht auf Löschung (Art. 17 DSGVO)</li>
<li>Recht auf Einschränkung der Verarbeitung (Art. 18 DSGVO)</li>
<li>Recht auf Datenübertragbarkeit (Art. 20 DSGVO)</li>
<li>Widerspruchsrecht (Art. 21 DSGVO)</li>
<li>Recht auf Widerruf einer Einwilligung (Art. 7 Abs. 3 DSGVO) mit Wirkung für die Zukunft</li>
</ul>
<p>Zur Ausübung Ihrer Rechte können Sie sich an die oben genannte verantwortliche Stelle wenden.</p>

<h2>Beschwerderecht bei einer Aufsichtsbehörde</h2>
<p>Sie haben das Recht, sich bei einer Datenschutz-Aufsichtsbehörde über die Verarbeitung personenbezogener Daten durch uns zu beschweren. Zuständig ist insbesondere die Aufsichtsbehörde des Bundeslandes Ihres gewöhnlichen Aufenthaltsorts oder des Ortes des mutmaßlichen Verstoßes. Eine Liste der Behörden und Kontakte finden Sie unter <a href="https://www.bfdi.bund.de/DE/Infothek/Anschriften_Links/anschriften_links-node.html" target="_blank" rel="noopener noreferrer">bfdi.bund.de</a>.</p>

<h2>Datenübermittlung in Drittländer</h2>
<p>Eine Übermittlung in Drittländer (außerhalb der EU/des EWR) findet nur statt, soweit dies zur Vertragserfüllung erforderlich ist, Sie eingewilligt haben oder ein anderer gesetzlicher Erlaubnistatbestand greift, und die Vorgaben der DSGVO (insbesondere geeignete Garantien nach Art. 46 DSGVO) eingehalten werden.</p>

<h2>Änderung dieser Erklärung</h2>
<p>Wir behalten uns vor, diese Datenschutzerklärung anzupassen, damit sie stets den aktuellen rechtlichen Anforderungen entspricht oder Änderungen unserer Leistungen in der Erklärung abbildet. Für Ihren erneuten Besuch gilt die jeweils aktuelle Fassung.</p>

<h2>Disclaimer</h2>
<p>Die Nutzung der bereitgestellten Hilfen, Anleitungen und Software erfolgt auf eigene Verantwortung; siehe auch das <a href="/impressum/">Impressum</a>.</p>
HTML;
}
