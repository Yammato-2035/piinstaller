<?php
function setuphelfer_projects() {
    return [
        'media-server' => [
            'title' => 'Raspberry Pi als Medienserver',
            'excerpt' => 'Baue deinen eigenen Medienserver fuer Filme, Serien und Musik. Verwendet u.a.: Docker, Samba, Plex oder Jellyfin, OpenSSH.',
            'difficulty' => 'Anfaenger',
            'hardware' => 'Raspberry Pi, Speicher (SD oder NVMe), Netzwerk',
            'time' => '90 Minuten',
            'snippet' => 'project-media-server',
        ],
        'musikbox' => [
            'title' => 'Musikbox',
            'excerpt' => 'Verwandle deinen Raspberry Pi in eine einfache Musikbox. Verwendet u.a.: MPD, Samba, OpenSSH.',
            'difficulty' => 'Anfaenger',
            'hardware' => 'Raspberry Pi',
            'time' => '60 Minuten',
            'snippet' => 'project-music-box',
        ],
        'heim-nas' => [
            'title' => 'Backup-System',
            'excerpt' => 'Automatische Datensicherung im Netzwerk. Verwendet u.a.: rsync, OpenSSH, Samba, optional Docker.',
            'difficulty' => 'Anfaenger',
            'hardware' => 'Raspberry Pi oder Linux-PC',
            'time' => '75 Minuten',
            'snippet' => 'project-backup-system',
        ],
        'smart-home' => [
            'title' => 'Smart Home Einstieg',
            'excerpt' => 'Erste Automatisierungen mit Raspberry Pi. Verwendet u.a.: Docker (z.B. Home Assistant), OpenSSH, optional Samba.',
            'difficulty' => 'Anfaenger',
            'hardware' => 'Raspberry Pi + Netzwerk',
            'time' => '90 Minuten',
            'snippet' => 'project-smart-home',
        ],
        'retro-gaming' => [
            'title' => 'Retro Gaming',
            'excerpt' => 'Klassische Konsolen auf dem Pi. Verwendet u.a.: RetroPie, OpenSSH, optional Samba.',
            'difficulty' => 'Anfaenger',
            'hardware' => 'Raspberry Pi + Controller',
            'time' => '90 Minuten',
            'snippet' => 'project-retro-gaming',
        ],
        'digitaler-bilderrahmen' => [
            'title' => 'Digitaler Bilderrahmen',
            'excerpt' => 'Fotos automatisch anzeigen. Verwendet u.a.: OpenSSH, rsync, Samba fuer Bildordner.',
            'difficulty' => 'Anfaenger',
            'hardware' => 'Raspberry Pi + Display',
            'time' => '45 Minuten',
            'snippet' => 'project-photo-frame',
        ],
    ];
}

function setuphelfer_tutorials() {
    return [
        'erste-raspberry-pi-einrichtung' => [
            'title' => 'Raspberry Pi OS installieren',
            'excerpt' => 'Image herunterladen, auf SD schreiben, starten. Raspberry Pi Imager, optional OpenSSH.',
            'difficulty' => 'Anfaenger',
            'time' => '25 Minuten',
            'snippet' => 'tutorial-pi-os-install',
        ],
        'netzwerk-grundlagen' => [
            'title' => 'WLAN einrichten',
            'excerpt' => 'WLAN auf dem Raspberry Pi sauber konfigurieren. NetworkManager oder wpa_supplicant.',
            'difficulty' => 'Anfaenger',
            'time' => '20 Minuten',
            'snippet' => 'tutorial-wlan-setup',
        ],
        'ssh-aktivieren' => [
            'title' => 'SSH aktivieren',
            'excerpt' => 'Sicheren Fernzugriff fuer Verwaltung und Wartung einrichten. OpenSSH (sshd).',
            'difficulty' => 'Anfaenger',
            'time' => '15 Minuten',
            'snippet' => 'tutorial-ssh-enable',
        ],
        'backup-grundlagen' => [
            'title' => 'Backup erstellen',
            'excerpt' => 'Datensicherung strukturiert aufsetzen und testen. rsync, OpenSSH, Samba-Ziele.',
            'difficulty' => 'Anfaenger',
            'time' => '20 Minuten',
            'snippet' => 'tutorial-backup-create',
        ],
        'linux-grundlagen' => [
            'title' => 'Updates durchfuehren',
            'excerpt' => 'Systemupdates kontrolliert und sicher durchfuehren. apt, systemd.',
            'difficulty' => 'Anfaenger',
            'time' => '15 Minuten',
            'snippet' => 'tutorial-updates-run',
        ],
        'docker-grundlagen' => [
            'title' => 'Docker Grundlagen',
            'excerpt' => 'Containerbasis fuer typische Heimserver-Setups. Docker Engine; Beispiele: Jellyfin, Plex, Samba-Container.',
            'difficulty' => 'Fortgeschritten',
            'time' => '30 Minuten',
            'snippet' => 'tutorial-docker-basics',
        ],
        'nvme-einrichten' => [
            'title' => 'NVMe einrichten',
            'excerpt' => 'NVMe-Speicher am Raspberry Pi korrekt einbinden. Linux-NVMe, fdisk, fstab.',
            'difficulty' => 'Fortgeschritten',
            'time' => '30 Minuten',
            'snippet' => 'tutorial-nvme-setup',
        ],
        'netzwerk-grundlagen-vertiefung' => [
            'title' => 'Netzwerk-Grundlagen',
            'excerpt' => 'Erreichbarkeit, Hostnamen und Diagnose bei Verbindungsproblemen. ping, ss, OpenSSH.',
            'difficulty' => 'Fortgeschritten',
            'time' => '25 Minuten',
            'snippet' => 'tutorial-network-basics',
        ],
        'backup-grundlagen-vertiefung' => [
            'title' => 'Backup-Grundlagen',
            'excerpt' => 'Was sichern, wohin sichern und Wiederherstellung mitdenken. rsync, OpenSSH, Samba.',
            'difficulty' => 'Anfaenger',
            'time' => '20 Minuten',
            'snippet' => 'tutorial-backup-basics',
        ],
        'linux-grundlagen-vertiefung' => [
            'title' => 'Linux-Grundlagen ohne Umwege',
            'excerpt' => 'Die wichtigsten Begriffe und Wege fuer den Alltag auf Raspberry Pi oder Linux-PC. Bash, apt, systemd, OpenSSH.',
            'difficulty' => 'Anfaenger',
            'time' => '25 Minuten',
            'snippet' => 'tutorial-linux-basics',
        ],
    ];
}

function setuphelfer_fehlerhilfen() {
    return [
        'pi-bootet-nicht' => [
            'title' => 'Pi bootet nicht',
            'excerpt' => 'Netzteil, SD-Karte und Image als typische Ursachen.',
            'snippet' => 'issue-pi-no-boot',
        ],
        'wlan-funktioniert-nicht' => [
            'title' => 'WLAN funktioniert nicht',
            'excerpt' => 'Keine Verbindung oder instabile Reichweite systematisch pruefen.',
            'snippet' => 'issue-wlan-not-working',
        ],
        'kein-hdmi-signal' => [
            'title' => 'Kein HDMI-Signal',
            'excerpt' => 'Anzeigeproblem bei Boot oder Aufloesung beheben.',
            'snippet' => 'issue-no-hdmi-signal',
        ],
        'nvme-wird-nicht-erkannt' => [
            'title' => 'NVMe wird nicht erkannt',
            'excerpt' => 'Adapter, Firmware und Boot-Konfiguration pruefen.',
            'snippet' => 'issue-nvme-not-detected',
        ],
        'system-langsam' => [
            'title' => 'System langsam',
            'excerpt' => 'Leistungsprobleme durch Speicher, Last oder Temperatur finden.',
            'snippet' => 'issue-system-slow',
        ],
        'ssh-funktioniert-nicht' => [
            'title' => 'SSH funktioniert nicht',
            'excerpt' => 'Dienst, Port und Netzwerkzugriff pruefen.',
            'snippet' => 'issue-ssh-not-working',
        ],
    ];
}

function setuphelfer_docs() {
    return [
        'installation' => [
            'title' => 'Installation',
            'title_en' => 'Installation',
            'excerpt' => 'Grundlagen fuer Start, lokale Erreichbarkeit und erste Pruefung.',
            'snippet' => 'doc-installation',
        ],
        'backup' => [
            'title' => 'Backup',
            'title_en' => 'Backup',
            'excerpt' => 'Sinnvolle Sicherungsstrategie statt blosser Hoffnung.',
            'snippet' => 'doc-backup',
        ],
        'docker' => [
            'title' => 'Docker',
            'title_en' => 'Docker',
            'excerpt' => 'Container nur dort einsetzen, wo Leistung und Nutzen zusammenpassen.',
            'snippet' => 'doc-docker',
        ],
        'mailserver' => [
            'title' => 'Mailserver',
            'title_en' => 'Mail server',
            'excerpt' => 'Produktiv nur mit klaren Voraussetzungen, Testbetrieb getrennt behandeln.',
            'snippet' => 'doc-mailserver',
        ],
        'diagnose' => [
            'title' => 'Diagnose',
            'title_en' => 'Diagnostics',
            'excerpt' => 'Wie man Fehler systematisch eingrenzt, statt blind neu zu starten.',
            'snippet' => 'doc-diagnostics',
        ],
    ];
}
