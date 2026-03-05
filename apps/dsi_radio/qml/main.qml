import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

Window {
    id: root
    width: 900
    height: 640
    minimumWidth: 640
    minimumHeight: 400
    // Kein maximumHeight: Fenster darf sich bei Platz auf dem Desktop vergrößern, damit alle Komponenten sichtbar sind
    visible: true
    title: "Sabrina Tuner (QML)"
    color: "#0f172a"

    Component.onCompleted: function() {
        root.requestActivate()
        root.raise()
    }

    // === Hintergrund (Metall) – Fläche, keine Layouts ===
    Rectangle {
        anchors.fill: parent
        anchors.margins: 8
        radius: 16
        border.width: 1
        border.color: "#475569"
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: "#1e293b" }
            GradientStop { position: 0.3; color: "#0f172a" }
            GradientStop { position: 0.7; color: "#1e293b" }
            GradientStop { position: 1.0; color: "#334155" }
        }
    }

    // === Inhalt: Elemente selbst positionieren – x, y, width, height unten anpassen ===
    Item {
        id: content
        anchors.fill: parent
        anchors.margins: 16

        // ---- Titelleiste: App-Icon + Titel + Untertitel links; Datum, Backend-LED, Fenster-Buttons rechts; per Drag verschiebbar ----
        Item {
            id: titelBar
            x: 0
            y: 0
            width: content.width
            height: 62
            // Fenster per Titelleiste verschieben (ganze Titelleiste als Drag-Bereich)
            property point dragLast: Qt.point(0, 0)
            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.LeftButton
                onPressed: function(mouse) {
                    if (typeof root.startSystemMove === "function") {
                        root.startSystemMove()
                    } else {
                        titelBar.dragLast = Qt.point(mouse.x, mouse.y)
                    }
                }
                onPositionChanged: function(mouse) {
                    if (pressed && typeof root.startSystemMove !== "function") {
                        root.x += mouse.x - titelBar.dragLast.x
                        root.y += mouse.y - titelBar.dragLast.y
                        titelBar.dragLast = Qt.point(mouse.x, mouse.y)
                    }
                }
            }
            // App-Icon (Sabrina Tuner), dann Titel und Untertitel
            Image {
                id: appIcon
                x: 0
                y: 2
                width: 58
                height: 58
                source: (typeof sabrinaTunerIconPath !== "undefined" && sabrinaTunerIconPath) ? sabrinaTunerIconPath : "sabrina-tuner-icon.png"
                fillMode: Image.PreserveAspectFit
                mipmap: true
                onStatusChanged: if (status === Image.Error && source !== "sabrina-tuner-icon.png") source = "sabrina-tuner-icon.png"
            }
            Text {
                x: appIcon.width + 10
                y: 6
                text: "Sabrina Tuner"
                font.pixelSize: 19
                font.bold: true
                color: "#e2e8f0"
            }
            Text {
                x: appIcon.width + 10
                y: 28
                text: "VU-Meter + Titel/Interpret"
                font.pixelSize: 12
                color: "#94a3b8"
            }
            // Rechte Seite: weiter nach rechts (Datum, Uhrzeit, LED, Fenster-Buttons)
            Item {
                id: titelBarRight
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                anchors.verticalCenterOffset: -6
                width: 260
                height: 40
                Text {
                    x: 20
                    y: (parent.height - height) / 2
                    text: Qt.formatDateTime(new Date(), "dd.MM.yyyy HH:mm")
                    font.pixelSize: 14
                    font.bold: true
                    color: "#94a3b8"
                }
                // Runde LED: Backend aktiv (grün) / inaktiv (rot), dünner silberner Rand
                Rectangle {
                    x: 138
                    y: (parent.height - 16) / 2
                    width: 16
                    height: 16
                    radius: 8
                    color: radio.backendActive ? "#22c55e" : "#ef4444"
                    border.width: 1
                    border.color: "#c0c0c0"
                }
                Button {
                    x: 162
                    y: (parent.height - height) / 2
                    width: 20
                    height: 20
                    text: "−"
                    font.pixelSize: 14
                    onClicked: root.visibility = Window.Minimized
                }
                Button {
                    x: 186
                    y: (parent.height - height) / 2
                    width: 20
                    height: 20
                    text: "□"
                    font.pixelSize: 12
                    onClicked: root.visibility = (root.visibility === Window.Maximized ? Window.Windowed : Window.Maximized)
                }
                Button {
                    x: 210
                    y: (parent.height - height) / 2
                    width: 20
                    height: 20
                    text: "⏻"
                    font.pixelSize: 12
                    onClicked: radio.quit()
                }
            }
        }

        // ---- Radiodisplay (weiß, Text gut lesbar) ----
        Rectangle {
            id: displayRect
            x: 0
            y: titelBar.y + titelBar.height + 8
            width: Math.min(480, content.width - 160)
            height: Math.min(250, content.height - titelBar.height - 120)
            color: "#ffffff"
            border.color: "#94a3b8"
            border.width: 1
            radius: 8

            // Größen-Anzeige oben rechts (zum Positionieren anpassbar)
            Text {
                x: displayRect.width - width - 12
                y: 4
                text: "Breite: " + displayRect.width + " px   Höhe: " + displayRect.height + " px"
                font.pixelSize: 11
                color: "#64748b"
            }

            // Senderinfos (weißer Hintergrund, dunkler Text)
            Item {
                x: 12
                y: 28
                width: displayRect.width - 24
                height: displayRect.height - 36
                Rectangle {
                    id: logoPlaceholder
                    x: 0
                    y: 0
                    width: 80
                    height: 80
                    color: "#f1f5f9"
                    radius: 4
                    Text {
                        anchors.centerIn: parent
                        text: "📻"
                        font.pixelSize: 34
                        visible: !displayLogo.visible || displayLogo.status !== Image.Ready
                    }
                }
                Image {
                    id: displayLogo
                    x: 0
                    y: 0
                    width: 80
                    height: 80
                    fillMode: Image.PreserveAspectFit
                    mipmap: true
                    source: radio.currentStationIndex >= 0 ? (radio.logoFailCount, radio.getStationLogoUrl(radio.currentStationIndex)) : ""
                    visible: source !== "" && status === Image.Ready
                    onStatusChanged: if (status === Image.Error && source) { radio.reportLogoFailed(source) }
                }
                Text {
                    x: logoPlaceholder.x + logoPlaceholder.width + 17
                    y: 8
                    width: parent.width - x - 8
                    text: radio.currentStationName || "—"
                    font.pixelSize: 20
                    font.bold: true
                    color: "#1e293b"
                    elide: Text.ElideRight
                }
                Text {
                    x: logoPlaceholder.x + logoPlaceholder.width + 17
                    y: 34
                    width: parent.width - x - 8
                    font.pixelSize: 13
                    color: "#334155"
                    elide: Text.ElideRight
                    wrapMode: Text.WordWrap
                    maximumLineCount: 2
                    text: {
                        var t = String(radio.currentMetadataTitle || "").trim()
                        var a = String(radio.currentMetadataArtist || "").trim()
                        if (t || a) {
                            if (t && a) return t + " – " + a
                            return t || a
                        }
                        return "Es läuft: " + (radio.currentStationName || "—") + " – Live"
                    }
                }
            }
        }

        // ---- Analoges VU-Meter (L/R) + Demo-Schalter + Signalstärke ----
        Item {
            id: vuBlock
            x: displayRect.x + displayRect.width + 28
            y: displayRect.y
            width: 320
            height: 240

            Row {
                id: vuRow
                spacing: 8
                AnalogVuMeter {
                    dbValue: typeof vuBridge !== "undefined" ? vuBridge.leftDb : -80
                    label: "L"
                }
                AnalogVuMeter {
                    dbValue: typeof vuBridge !== "undefined" ? vuBridge.rightDb : -80
                    label: "R"
                }
            }

            CheckBox {
                id: vuDemoCheck
                anchors.top: vuRow.bottom
                anchors.left: vuRow.left
                anchors.topMargin: 6
                text: "Demo VU"
                font.pixelSize: 14
                checked: typeof vuBridge !== "undefined" ? vuBridge.demoMode : false
                onToggled: if (typeof vuBridge !== "undefined") vuBridge.demoMode = checked
            }

            // Signalstärke: Icon (LAN/WLAN) + grüne LEDs
            Text {
                x: 296
                y: 0
                width: 24
                horizontalAlignment: Text.AlignHCenter
                text: radio.networkType === "wlan" ? "📶" : "🔌"
                font.pixelSize: 18
            }
            Column {
                x: 292
                y: 24
                spacing: 3
                Repeater {
                    model: 5
                    Rectangle {
                        width: 14
                        height: 14
                        radius: 3
                        color: radio.signalStrength >= (5 - index) / 5.0 ? "#22c55e" : "#1e293b"
                        border.width: 1
                        border.color: "#475569"
                    }
                }
            }
        }

        // ---- Lautstärke (rechts neben VU/Signal) ----
        Item {
            id: volumeColumn
            x: vuBlock.x + vuBlock.width + 8
            y: displayRect.y
            width: 56
            height: 220
            Text {
                x: (parent.width - width) / 2
                y: 0
                text: "▶"
                font.pixelSize: 16
                font.bold: true
                color: "#facc15"
            }
            Slider {
                x: (parent.width - width) / 2
                y: 24
                width: 24
                height: parent.height - 24
                orientation: Qt.Vertical
                from: 0
                to: 100
                value: radio.volume
                onMoved: function() { radio.setVolume(Math.round(value)) }
            }
        }

        // ---- Sender-Buttons: 20 pro Seite, je 100 px breit; Seitenwechsel immer sichtbar, am Rand deaktiviert ----
        Item {
            id: buttonArea
            property int btnW: 130
            property int blockWidth: 40 + (gridColumns * btnW + (gridColumns - 1) * 6) + 8 + 32
            x: (content.width - blockWidth) / 2
            y: displayRect.y + displayRect.height + 23
            width: blockWidth
            height: 170
            property int stationPage: 0
            property int perPage: 20
            property int gridColumns: 5
            property int gridRows: 4
            property int pageCount: Math.max(1, Math.ceil(radio.stationCount / perPage))
            property int countOnPage: Math.min(perPage, Math.max(0, radio.stationCount - stationPage * perPage))

            Button {
                id: pagePrevBtn
                x: 0
                y: (parent.height - height) / 2
                width: 32
                height: 36
                text: "◀"
                enabled: buttonArea.stationPage > 0
                onClicked: if (buttonArea.stationPage > 0) buttonArea.stationPage--
            }
            Grid {
                id: buttonGrid
                x: 40
                y: 0
                rows: buttonArea.gridRows
                columns: buttonArea.gridColumns
                flow: Grid.LeftToRight
                rowSpacing: 6
                columnSpacing: 6
                width: buttonArea.gridColumns * buttonArea.btnW + (buttonArea.gridColumns - 1) * 6
                height: buttonArea.gridRows * 36 + (buttonArea.gridRows - 1) * 6
                Repeater {
                    model: buttonArea.countOnPage
                    Button {
                        width: buttonArea.btnW
                        height: 36
                        property int actualIndex: buttonArea.stationPage * buttonArea.perPage + index
                        text: radio.stationName(actualIndex) || ("Sender " + (actualIndex + 1))
                        highlighted: radio.currentStationName === radio.stationName(actualIndex)
                        onClicked: radio.setStation(actualIndex)
                        ToolTip.visible: hovered
                        ToolTip.delay: 400
                        ToolTip.text: {
                            var name = radio.stationName(actualIndex) || ("Sender " + (actualIndex + 1))
                            var quality = radio.getStationQuality(actualIndex)
                            return quality ? (name + "\n" + quality) : name
                        }
                    }
                }
            }
            Button {
                id: pageNextBtn
                x: 40 + (buttonArea.gridColumns * buttonArea.btnW + (buttonArea.gridColumns - 1) * 6) + 8
                y: (parent.height - height) / 2
                width: 32
                height: 36
                text: "▶"
                enabled: (buttonArea.stationPage + 1) * buttonArea.perPage < radio.stationCount
                onClicked: if ((buttonArea.stationPage + 1) * buttonArea.perPage < radio.stationCount) buttonArea.stationPage++
            }
        }

        // ---- Senderliste-Button: 10 px vom unteren Rand, zentriert ----
        Button {
            id: senderlisteBtn
            x: buttonArea.x + 40 + (buttonArea.gridColumns * buttonArea.btnW + (buttonArea.gridColumns - 1) * 6) / 2 - width / 2
            y: content.height - height - 10
            width: 182
            height: 30
            font.pixelSize: 14
            text: "📻 Senderliste"
            onClicked: senderlistePopup.open()
        }
    }

    // === Senderliste-Popup: Filter Land/Musikrichtung, Favoriten-Checkbox, Logos (Radio-Browser) ===
    Popup {
        id: senderlistePopup
        anchors.centerIn: parent
        width: Math.min(520, root.width - 40)
        height: Math.min(560, root.height - 80)
        modal: true
        focus: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        padding: 8
        onOpened: {
            var countries = ["Germany", "Austria", "Switzerland", "Netherlands", "France", "Italy", "Spain", "Poland"]
            var ci = countries.indexOf(radio.searchCountry)
            filterCountry.currentIndex = ci >= 0 ? ci : 0
            filterTag.editText = radio.searchTag || ""
        }
        contentItem: Column {
            width: senderlistePopup.width - 16
            height: senderlistePopup.height - 16
            spacing: 6
            Row {
                width: parent.width - 16
                height: 32
                spacing: 8
                Label {
                    text: "Senderliste (Radio-Browser)"
                    font.bold: true
                    font.pixelSize: 14
                    width: parent.width - 16 - 80
                    height: 28
                    verticalAlignment: Text.AlignVCenter
                }
                Button {
                    text: "✕ Schließen"
                    width: 100
                    height: 28
                    onClicked: senderlistePopup.close()
                }
            }
            Row {
                width: parent.width - 16
                height: 36
                spacing: 8
                Label { text: "Land:"; width: 36; height: 32; verticalAlignment: Text.AlignVCenter }
                ComboBox {
                    id: filterCountry
                    width: 140
                    height: 32
                    model: ["Germany", "Austria", "Switzerland", "Netherlands", "France", "Italy", "Spain", "Poland"]
                    onActivated: radio.setSearchFilter(model[currentIndex], filterTag.editText || filterTag.currentText || "")
                }
                Label { text: "Musikrichtung:"; width: 90; height: 32; verticalAlignment: Text.AlignVCenter; font.pixelSize: 11 }
                ComboBox {
                    id: filterTag
                    width: 140
                    height: 32
                    editable: true
                    model: ["", "pop", "rock", "schlager", "news", "classical", "jazz", "electronic", "country"]
                    onActivated: radio.setSearchFilter(filterCountry.currentText, currentText || editText || "")
                    onAccepted: radio.setSearchFilter(filterCountry.currentText, editText || "")
                }
            }
            ListView {
                id: senderlisteView
                clip: true
                width: parent.width
                height: parent.height - 80
                model: radio.stationCount
                delegate: Item {
                    width: senderlisteView.width - 4
                    height: 48
                    Row {
                        anchors.fill: parent
                        anchors.margins: 4
                        spacing: 8
                        CheckBox {
                            checked: radio.isFavorite(index)
                            onToggled: radio.toggleFavorite(index)
                        }
                        MouseArea {
                            width: parent.width - 44
                            height: 44
                            onClicked: function() {
                                radio.setStation(index)
                                senderlistePopup.close()
                            }
                            Item {
                                width: 40
                                height: 40
                                anchors.verticalCenter: parent.verticalCenter
                                Rectangle {
                                    anchors.fill: parent
                                    color: "#334155"
                                    radius: 4
                                    visible: stationLogo.status !== Image.Ready
                                    Text {
                                        anchors.centerIn: parent
                                        text: "📻"
                                        font.pixelSize: 20
                                    }
                                }
                                Image {
                                    id: stationLogo
                                    width: 40
                                    height: 40
                                    fillMode: Image.PreserveAspectFit
                                    mipmap: true
                                    source: (radio.logoFailCount, radio.getStationLogoUrl(index))
                                    visible: status === Image.Ready
                                    onStatusChanged: if (status === Image.Error && source) { radio.reportLogoFailed(source) }
                                }
                            }
                            Column {
                                x: 48
                                width: parent.width - 48
                                spacing: 2
                                anchors.verticalCenter: parent.verticalCenter
                                Text {
                                    text: radio.stationName(index)
                                    font.pixelSize: 13
                                    font.bold: true
                                    color: "#e2e8f0"
                                    elide: Text.ElideRight
                                    width: parent.width - 8
                                }
                                Text {
                                    text: (radio.getStationCountry(index) ? radio.getStationCountry(index) + " · " : "") + (radio.getStationGenre(index) || "—")
                                    font.pixelSize: 10
                                    color: "#94a3b8"
                                    elide: Text.ElideRight
                                    width: parent.width - 8
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
