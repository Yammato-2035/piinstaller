import QtQuick
import QtQuick.Controls

/**
 * Analoges VU-Meter: Skala OBEN. Kreissegment 120° (kein Vollkreis).
 * Bogen wie ein umgekehrtes U – Mitte oben. Zeiger läuft im Segment (-40 … 0 dB).
 * Weißer Hintergrund, rechts roter Bereich (-3 … 0 dB).
 */
Item {
    id: root
    width: 140
    height: 200

    property real dbValue: -80
    property string label: "L"
    property real dbMin: -40
    property real dbMax: 0
    property real dbRedStart: -3

    readonly property real segmentDeg: 120
    readonly property real startRad: 5 * Math.PI / 6
    readonly property real endRad: Math.PI / 6

    function dbToT(db) {
        var t = (db - root.dbMin) / (root.dbMax - root.dbMin)
        return Math.max(0, Math.min(1, t))
    }
    function dbToCanvasRad(db) {
        var t = dbToT(db)
        t = Math.pow(t, 0.7)
        return root.startRad + t * (root.endRad - root.startRad)
    }

    onDbValueChanged: canvas.requestPaint()

    Canvas {
        id: canvas
        anchors.fill: parent
        antialiasing: true

        onPaint: {
            var ctx = getContext("2d")
            var w = width
            var h = height
            var margin = 14
            var r = Math.min((w - 2 * margin) * 0.55, (h - 2 * margin) * 0.5)
            var cx = w / 2
            var cy = margin - r
            var tickInward = 10
            var tickR = r + 8
            var needleLen = r - 2
            var scalePx = Math.min(w, h) / 80

            ctx.reset()

            ctx.fillStyle = "#ffffff"
            ctx.fillRect(0, 0, w, h)

            var radRedStart = dbToCanvasRad(root.dbRedStart)

            ctx.strokeStyle = "#1e293b"
            ctx.lineWidth = Math.max(2.5, scalePx * 0.5)
            ctx.beginPath()
            ctx.arc(cx, cy, r, root.startRad, radRedStart, true)
            ctx.stroke()

            ctx.strokeStyle = "#dc2626"
            ctx.lineWidth = Math.max(2.5, scalePx * 0.5)
            ctx.beginPath()
            ctx.arc(cx, cy, r, radRedStart, root.endRad, true)
            ctx.stroke()

            ctx.strokeStyle = "#94a3b8"
            ctx.lineWidth = Math.max(1, scalePx * 0.25)
            ctx.beginPath()
            ctx.arc(cx, cy, r + 6, root.startRad, root.endRad, true)
            ctx.stroke()

            var tickDbWhite = [-40, -30, -20, -10, -7, -5]
            ctx.strokeStyle = "#1e293b"
            ctx.fillStyle = "#1e293b"
            ctx.font = "bold " + Math.round(11 + scalePx * 0.6) + "px sans-serif"
            ctx.textAlign = "center"
            ctx.textBaseline = "middle"
            for (var i = 0; i < tickDbWhite.length; i++) {
                var rad = dbToCanvasRad(tickDbWhite[i])
                var x1 = cx + r * Math.cos(rad)
                var y1 = cy + r * Math.sin(rad)
                var x2 = cx + (r - tickInward) * Math.cos(rad)
                var y2 = cy + (r - tickInward) * Math.sin(rad)
                ctx.beginPath()
                ctx.moveTo(x1, y1)
                ctx.lineTo(x2, y2)
                ctx.stroke()
                var tx = cx + (r - tickInward - 14) * Math.cos(rad)
                var ty = cy + (r - tickInward - 14) * Math.sin(rad)
                ctx.fillText(tickDbWhite[i].toString(), tx, ty)
            }

            var tickDbRed = [-3, -1, 0]
            ctx.strokeStyle = "#dc2626"
            ctx.fillStyle = "#dc2626"
            for (var j = 0; j < tickDbRed.length; j++) {
                var rrad = dbToCanvasRad(tickDbRed[j])
                var x1 = cx + r * Math.cos(rrad)
                var y1 = cy + r * Math.sin(rrad)
                var x2 = cx + (r - tickInward) * Math.cos(rrad)
                var y2 = cy + (r - tickInward) * Math.sin(rrad)
                ctx.beginPath()
                ctx.moveTo(x1, y1)
                ctx.lineTo(x2, y2)
                ctx.stroke()
                var tx = cx + (r - tickInward - 14) * Math.cos(rrad)
                var ty = cy + (r - tickInward - 14) * Math.sin(rrad)
                ctx.fillText(tickDbRed[j].toString(), tx, ty)
            }

            var pivotY = margin + 18
            ctx.fillStyle = "#64748b"
            ctx.font = Math.round(10 + scalePx * 0.4) + "px sans-serif"
            ctx.fillText("dB", cx, pivotY + 28)

            var needleRad = dbToCanvasRad(dbValue)
            var nx = cx + needleLen * Math.cos(needleRad)
            var ny = cy + needleLen * Math.sin(needleRad)
            ctx.strokeStyle = "#1e293b"
            ctx.lineWidth = Math.max(3.5, scalePx * 0.9)
            ctx.beginPath()
            ctx.moveTo(cx, pivotY)
            ctx.lineTo(nx, ny)
            ctx.stroke()

            var pivotR = Math.max(6, scalePx * 1.2)
            ctx.fillStyle = "#334155"
            ctx.beginPath()
            ctx.arc(cx, pivotY, pivotR, 0, 2 * Math.PI)
            ctx.fill()
            ctx.strokeStyle = "#64748b"
            ctx.lineWidth = Math.max(1.5, scalePx * 0.35)
            ctx.stroke()
        }
    }
}
