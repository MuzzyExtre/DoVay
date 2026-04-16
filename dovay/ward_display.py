import math

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF
from PySide6.QtGui import (
    QPainter, QPen, QFont, QColor, QBrush,
    QPainterPath, QRadialGradient, QConicalGradient, QLinearGradient,
)
from dovay.theme import (
    INK, VOID, BORDER, TEXT_LOW, TEXT_MID,
    STATE_COLORS, STATE_LABELS,
    FONT_DISPLAY, FONT_MONO,
)

_WARDS = [
    {"r": 70, "sw": 0.8, "d_on": 140, "d_off": 256, "off": 0,
     "i_op": 0.07, "a_op": 0.22, "spd": 0.214},
    {"r": 54, "sw": 1.2, "d_on": 100, "d_off": 205, "off": 80,
     "i_op": 0.09, "a_op": 0.4, "spd": -0.375},
    {"r": 37, "sw": 1.8, "d_on": 80, "d_off": 129, "off": 50,
     "i_op": 0.11, "a_op": 0.55, "spd": 0.6},
]

_PANEL_H = 218
_VIS_SZ = 160
_TOTAL_H = 240


class WardDisplay(QWidget):
    """Animated diamond-ward status visualization."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedHeight(_TOTAL_H)

        self._status = "idle"
        self._message = "\u0413\u043e\u0442\u043e\u0432 \u043a \u0437\u0430\u043f\u0443\u0441\u043a\u0443"
        self._scan_count = 0

        self._tick_n = 0
        self._angles = [0.0, 0.0, 0.0]
        self._sweep = 0.0
        self._pulse = 0.0
        self._cpulse = 0.0

        # Pre-build diamond paths centred at origin
        self._paths: list[QPainterPath] = []
        for w in _WARDS:
            r = w["r"]
            pa = QPainterPath()
            pa.moveTo(0, -r)
            pa.lineTo(r, 0)
            pa.lineTo(0, r)
            pa.lineTo(-r, 0)
            pa.closeSubpath()
            self._paths.append(pa)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

    # ── public ──────────────────────────────────────────────────────────
    def set_status(self, status: str, message: str):
        self._status = status
        self._message = message
        self.update()

    def set_scan_count(self, n: int):
        self._scan_count = n
        self.update()

    # ── animation ───────────────────────────────────────────────────────
    def _tick(self):
        self._tick_n += 1
        sc = self._status == "scanning"
        fo = self._status == "match_found"

        if sc or fo:
            f = 0.67 if fo else 1.0
            for i, w in enumerate(_WARDS):
                self._angles[i] = (self._angles[i] + w["spd"] * f) % 360
            self._sweep = (self._sweep + 0.0053) % 1.0

        if fo:
            self._pulse = (self._pulse + 0.0123) % 1.0

        if sc:
            self._cpulse = 0.5 + 0.5 * math.sin(self._tick_n * 0.04)
        elif fo:
            self._cpulse = 0.5 + 0.5 * math.sin(self._tick_n * 0.2)
        else:
            self._cpulse = 0.0

        if self._status != "idle":
            self.update()

    # ── painting ────────────────────────────────────────────────────────
    def paintEvent(self, _event):  # noqa: C901 — complex but self-contained
        w = self.width()
        col = STATE_COLORS.get(self._status, STATE_COLORS["idle"])
        cr, cg, cb = col.red(), col.green(), col.blue()
        active = self._status != "idle"
        scanning = self._status == "scanning"
        found = self._status == "match_found"
        accepted = self._status == "accepted"

        vcx = w / 2
        vcy = 12 + _VIS_SZ / 2

        with QPainter(self) as p:
            p.setRenderHint(QPainter.RenderHint.Antialiasing)

            # ── Panel ───────────────────────────────────────────────────
            panel = QRectF(0, 0, w, _PANEL_H)
            bc = QColor(cr, cg, cb, 24) if active else BORDER
            p.setPen(QPen(bc, 1))
            p.setBrush(QBrush(INK))
            p.drawRoundedRect(panel, 12, 12)

            # Scan sweep
            if scanning:
                p.save()
                clip = QPainterPath()
                clip.addRoundedRect(panel, 12, 12)
                p.setClipPath(clip)
                sy = self._sweep * _PANEL_H
                sg = QLinearGradient(0, sy, w, sy)
                sg.setColorAt(0, QColor(0, 0, 0, 0))
                sg.setColorAt(0.05, QColor(0, 0, 0, 0))
                sg.setColorAt(0.5, QColor(cr, cg, cb, 48))
                sg.setColorAt(0.95, QColor(0, 0, 0, 0))
                sg.setColorAt(1, QColor(0, 0, 0, 0))
                p.setPen(QPen(QBrush(sg), 1))
                p.drawLine(QPointF(0, sy), QPointF(w, sy))
                p.restore()

            # ── Visualization ───────────────────────────────────────────

            # Ambient glow
            gl = QRadialGradient(vcx, vcy, 30)
            gl.setColorAt(0, QColor(cr, cg, cb, 18 if active else 6))
            gl.setColorAt(1, QColor(0, 0, 0, 0))
            p.setBrush(QBrush(gl))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(vcx, vcy), 30, 30)

            # Outer reference circle
            p.setPen(QPen(QColor(cr, cg, cb, 20 if active else 10), 0.3))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPointF(vcx, vcy), 74, 74)

            # Inner reference ring
            p.setPen(QPen(QColor(cr, cg, cb, 15), 0.3))
            p.drawEllipse(QPointF(vcx, vcy), 26, 26)

            # Compass ticks
            for deg in range(0, 360, 45):
                rad = math.radians(deg)
                major = deg % 90 == 0
                r1, r2 = 74, (78 if major else 76)
                a = (76 if major else 38) if active else 15
                p.setPen(QPen(QColor(cr, cg, cb, a), 0.8 if major else 0.4))
                p.drawLine(
                    QPointF(vcx + r1 * math.sin(rad), vcy - r1 * math.cos(rad)),
                    QPointF(vcx + r2 * math.sin(rad), vcy - r2 * math.cos(rad)),
                )

            # Diamond wards
            for i, (wd, pa) in enumerate(zip(_WARDS, self._paths)):
                sw = wd["sw"] if active else wd["sw"] * 0.4
                pen = QPen(col, sw)
                pen.setDashPattern([wd["d_on"] / sw, wd["d_off"] / sw])
                pen.setDashOffset(wd["off"] / sw)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)

                p.save()
                p.translate(vcx, vcy)
                if scanning or found:
                    p.rotate(self._angles[i])
                p.setOpacity(wd["a_op"] if active else wd["i_op"])
                p.setPen(pen)
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawPath(pa)
                p.setOpacity(1.0)
                p.restore()

            # Conic sweep trail
            if scanning:
                sa = self._angles[2] * 3
                cn = QConicalGradient(vcx, vcy, -sa)
                cn.setColorAt(0, QColor(cr, cg, cb, 0))
                cn.setColorAt(0.055, QColor(cr, cg, cb, 10))
                cn.setColorAt(0.14, QColor(cr, cg, cb, 0))
                cn.setColorAt(0.5, QColor(0, 0, 0, 0))
                cn.setColorAt(1, QColor(cr, cg, cb, 0))
                p.setBrush(QBrush(cn))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(QPointF(vcx, vcy), 40, 40)

            # Expanding diamond pulses (match_found)
            if found:
                for off in (0.0, 0.27, 0.54):
                    ph = (self._pulse + off) % 1.0
                    sc2 = 1.0 + ph * 3.0
                    al = int(128 * (1.0 - ph))
                    r = 12 * sc2
                    pp = QPainterPath()
                    pp.moveTo(vcx, vcy - r)
                    pp.lineTo(vcx + r, vcy)
                    pp.lineTo(vcx, vcy + r)
                    pp.lineTo(vcx - r, vcy)
                    pp.closeSubpath()
                    p.setPen(QPen(QColor(cr, cg, cb, al), 1.5))
                    p.setBrush(Qt.BrushStyle.NoBrush)
                    p.drawPath(pp)

            # Centre element
            if not accepted:
                sz = 4.0
                if scanning:
                    sz = 5.0 + self._cpulse * 2.0
                elif found:
                    sz = 5.0 + self._cpulse * 3.0
                elif active:
                    sz = 7.0

                p.save()
                p.translate(vcx, vcy)
                p.rotate(45)
                if active:
                    p.setBrush(QBrush(QColor(cr, cg, cb, 21)))
                else:
                    p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(col, 2))
                p.drawRoundedRect(QRectF(-sz, -sz, sz * 2, sz * 2), 2, 2)
                p.restore()

                if active:
                    for gr, ga in [(8, 60), (16, 25), (28, 8)]:
                        rg = QRadialGradient(vcx, vcy, gr)
                        rg.setColorAt(0, QColor(cr, cg, cb, ga))
                        rg.setColorAt(1, QColor(0, 0, 0, 0))
                        p.setBrush(QBrush(rg))
                        p.setPen(Qt.PenStyle.NoPen)
                        p.drawEllipse(QPointF(vcx, vcy), gr, gr)
            else:
                # Accepted circle + checkmark
                p.setBrush(QBrush(col))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(QPointF(vcx, vcy), 16, 16)
                for gr, ga in [(20, 80), (32, 40), (44, 15)]:
                    rg = QRadialGradient(vcx, vcy, gr)
                    rg.setColorAt(0, QColor(cr, cg, cb, ga))
                    rg.setColorAt(1, QColor(0, 0, 0, 0))
                    p.setBrush(QBrush(rg))
                    p.drawEllipse(QPointF(vcx, vcy), gr, gr)
                ck = QPainterPath()
                ck.moveTo(vcx - 6, vcy)
                ck.lineTo(vcx - 2, vcy + 4)
                ck.lineTo(vcx + 6, vcy - 4)
                cp = QPen(VOID, 2.5)
                cp.setCapStyle(Qt.PenCapStyle.RoundCap)
                cp.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
                p.setPen(cp)
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawPath(ck)

            # ── Data readout ────────────────────────────────────────────
            if active:
                dy = 12 + _VIS_SZ + 4
                sig = 1 + (self._scan_count % 5) if scanning else 5
                sig_s = "\u25cf" * sig + "\u25cb" * (5 - sig)
                id_v = (self._scan_count * 7 + 0x3F2A) & 0xFFFF

                fm = QFont(FONT_MONO, 6)
                fm.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 110)
                p.setFont(fm)
                p.setOpacity(0.5)
                p.setPen(TEXT_LOW)
                p.drawText(12, dy + 8, f"SIG:{sig_s}")
                id_t = f"ID:0x{id_v:04X}"
                iw = p.fontMetrics().horizontalAdvance(id_t)
                p.drawText(int(w - 12 - iw), dy + 8, id_t)
                p.setOpacity(1.0)

            # ── Label row ───────────────────────────────────────────────
            ly = _PANEL_H - 22
            label = STATE_LABELS.get(self._status, "")

            lg = QLinearGradient(12, ly + 7, w / 2 - 40, ly + 7)
            lg.setColorAt(0, QColor(0, 0, 0, 0))
            lg.setColorAt(1, QColor(cr, cg, cb, 32))
            p.setPen(QPen(QBrush(lg), 1))
            p.drawLine(QPointF(12, ly + 7), QPointF(w / 2 - 40, ly + 7))

            rg2 = QLinearGradient(w / 2 + 40, ly + 7, w - 12, ly + 7)
            rg2.setColorAt(0, QColor(cr, cg, cb, 32))
            rg2.setColorAt(1, QColor(0, 0, 0, 0))
            p.setPen(QPen(QBrush(rg2), 1))
            p.drawLine(QPointF(w / 2 + 40, ly + 7), QPointF(w - 12, ly + 7))

            if active:
                da = int(128 + 127 * math.sin(self._tick_n * 0.1))
                p.setBrush(QBrush(QColor(cr, cg, cb, da)))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(QPointF(w / 2 - 35, ly + 7), 2.5, 2.5)

            lf = QFont(FONT_DISPLAY, 8)
            lf.setWeight(QFont.Weight.Bold)
            lf.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 125)
            p.setFont(lf)
            p.setPen(col)
            lw2 = p.fontMetrics().horizontalAdvance(label)
            p.drawText(int((w - lw2) / 2), ly + 11, label)

            if scanning:
                ct = f"#{self._scan_count:04d}"
                cf = QFont(FONT_MONO, 7)
                cf.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 108)
                p.setFont(cf)
                p.setPen(TEXT_LOW)
                p.drawText(int((w + lw2) / 2 + 8), ly + 10, ct)

            # ── Message ─────────────────────────────────────────────────
            my = _PANEL_H + 8
            mf = QFont(FONT_DISPLAY, 8)
            mf.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 112)
            p.setFont(mf)
            mc = col if active else TEXT_MID
            p.setPen(mc)
            mw = p.fontMetrics().horizontalAdvance(self._message)
            p.drawText(int((w - mw) / 2), my + 12, self._message)
