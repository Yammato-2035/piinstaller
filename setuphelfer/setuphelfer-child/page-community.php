<?php
/**
 * Template Name: Community (Child Override)
 * Description: Community-Seite mit Intro-Snippet und bbPress-Forum.
 */

get_header();

// Parent-Snippet mit voller Platzhalter-Aufloesung (Lucide, Links, Screenshots).
setuphelfer_render_snippet( 'community' );
?>

<section class="section community-page-forum">
    <div class="card">
                <?php
                if ( function_exists( 'setuphelfer_forum_welcome_markup' ) ) {
                    setuphelfer_forum_welcome_markup();
                }
                // Page-Inhalt aus dem Editor ausgeben.
                if ( have_posts() ) :
                    while ( have_posts() ) :
                        the_post();
                        the_content();
                    endwhile;
                endif;

                // BuddyPress Activity-Stream einbetten (ohne Shortcode-Plugins).
                // So bleibt die Darstellung "buddytypisch" (Avatar, Meta, Einträge).
                if ( function_exists( 'bp_has_activities' ) && function_exists( 'bp_the_activity' ) && function_exists( 'bp_activities' ) ) {
                    echo '<div class="section">';
                    echo '<h2>Aktivität</h2>';

                    // BuddyPress setzt auf normalen WP-Seiten nicht automatisch den passenden Scope/Context.
                    // Daher erzwingen wir "sitewide" Aktivität (globale Aktivitäten aller Nutzer).
                    $bp_params = function_exists( 'bp_ajax_querystring' ) ? (array) bp_ajax_querystring( 'activity' ) : [];
                    $bp_params['per_page'] = 10;
                    $bp_params['user_id'] = 0; // sitewide
                    $bp_params['scope'] = 0;   // global

                    if ( bp_has_activities( $bp_params ) ) {
                        while ( bp_activities() ) :
                            bp_the_activity();
                            // Rendert den einzelnen Activity-Eintrag über die BuddyPress Template-Hierarchie.
                            if ( function_exists( 'bp_get_template_part' ) ) {
                                bp_get_template_part( 'activity', 'entry' );
                            } else {
                                locate_template( ['activity/entry.php'], true, false );
                            }
                        endwhile;

                        if ( function_exists( 'bp_activity_pagination_links' ) ) {
                            bp_activity_pagination_links();
                        }
                    } else {
                        echo '<p>Aktuell gibt es keine Aktivitäten.</p>';
                    }

                    echo '</div>';
                }

                // BuddyPress: Neueste Mitglieder einbetten, damit "social"-Optik auch ohne Aktivitäten sichtbar ist.
                if ( function_exists( 'bp_has_members' ) && function_exists( 'bp_the_member' ) && function_exists( 'bp_members' ) ) {
                    echo '<div class="section">';
                    echo '<h2>Neueste Mitglieder</h2>';

                    if ( bp_has_members( ['type' => 'newest', 'per_page' => 6] ) ) {
                        // BuddyPress/styles sollen das Layout übernehmen.
                        echo '<ul class="item-list">';
                        while ( bp_members() ) :
                            bp_the_member();
                            // BuddyPress Template Part rendert Avatar + Name + Link je nach Theme-Style.
                            if ( function_exists( 'bp_get_template_part' ) ) {
                                bp_get_template_part( 'members', 'entry' );
                            } else {
                                locate_template( ['members/entry.php'], true, false );
                            }
                        endwhile;
                        echo '</ul>';
                    } else {
                        echo '<p>Keine Mitglieder gefunden.</p>';
                    }

                    echo '</div>';
                }

                // Forum-Kategorien sichtbar machen, damit die Community nicht "leer" wirkt.
                $forum_slugs = [
                    'erste-schritte' => 'Erste Schritte',
                    'projekte' => 'Projekte',
                    'linux' => 'Linux',
                    'fehler' => 'Fehler',
                    'ideen' => 'Ideen',
                ];
                echo '<div class="section" id="forum-kategorien">';
                echo '<h2>Forum-Kategorien</h2>';
                echo '<div class="grid-3">';
                foreach ( $forum_slugs as $slug => $label ) {
                    $forum = get_page_by_path( $slug, OBJECT, 'forum' );
                    $url = $forum ? get_permalink( $forum ) : '#';
                    echo '<article class="card"><h3>' . esc_html( $label ) . '</h3>';
                    echo '<p><a href="' . esc_url( $url ) . '">Kategorie oeffnen</a></p></article>';
                }
                echo '</div>';
                echo '</div>';

                // bbPress-Forum über Shortcode einbinden.
                echo '<div class="section">';
                echo do_shortcode( '[bbp-forum-index]' );
                echo '</div>';
                ?>
    </div>
</section>

<?php
get_footer();

