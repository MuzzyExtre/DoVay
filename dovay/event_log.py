import time

from PySide6.QtWidgets import QWidget, QPushButton
from PySide6.QtCore import Signal, Qt, QTimer, QRectF
from PySide6.QtGui import QPainter, QPen, QFont, QColor, QBrush
from dovay.theme import (
    ACCENT, SURFACE_RAISED, BORDER, TEXT_LOW, TEXT_MID,
    EVENT_COLORS, FONT_MONO,
)


class _DebugBtn(QPushButton):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedSize(40, 14)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._hovered = False

    def paintEvent(self, _event):
        with QPainter(self) as p:
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            if self._hovered:
                p.setBrush(QBrush(SURFACE_RAISED))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawRoundedRect(self.rect(), 3, 3)
            f = QFont(FONT_MONO, 6)
            f.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 120)
            p.setFont(f)
            p.setPen(ACCENT if self._hovered else TEXT_LOW)
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "DEBUG")

    def enterEvent(self, _e):
        self._hovered = True
        self.update()

    def leaveEvent(self, _e):
        self._hovered = False
        self.update()


class EventLog(QWidget):
    """Scrollable event log with coloured type indicators."""

    debug_clicked = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._events: list[dict] = []
        self._blink_on = True

        self._debug_btn = _DebugBtn(self)
        self._debug_btn.clicked.connect(self.debug_clicked)

        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._toggle_blink)
        self._blink_timer.start(500)

    def add_event(self, event_type: str, message: str):
        self._events.insert(0, {
            "type": event_type,
            "ts": time.strftime("%H:%M:%S"),
            "msg": message,
        })
        self._events = self._events[:5]
        self.update()

    def _toggle_blink(self):
        self._blink_on = not self._blink_on
        if not self._events:
            self.update()

    def resizeEvent(self, _event):
        self._debug_btn.move(self.width() - self._debug_btn.width(), 1)

    # ── painting ────────────────────────────────────────────────────────
    def paintEvent(self, _event):
        w = self.width()
        with QPainter(self) as p:
            p.setRenderHint(QPainter.RenderHint.Antialiasing)

            hdr_h = 16

            # Diamond marker
            p.save()
            p.translate(3, hdr_h / 2)
            p.rotate(45)
            p.setOpacity(0.3)
            p.setBrush(QBrush(ACCENT))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRect(QRectF(-2.5, -2.5, 5, 5))
            p.restore()
            p.setOpacity(1.0)

            # Title
            f = QFont(FONT_MONO, 7)
            f.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 130)
            p.setFont(f)
            p.setPen(TEXT_LOW)
            p.drawText(12, hdr_h - 3, "\u0421\u041e\u0411\u042b\u0422\u0418\u042f")

            # Separator line
            p.setPen(QPen(BORDER, 1))
            p.drawLine(72, hdr_h // 2, w - 44, hdr_h // 2)

            # ── Events ──────────────────────────────────────────────────
            y0 = hdr_h + 6

            if not self._events:
                ef = QFont(FONT_MONO, 8)
                p.setFont(ef)
                p.setPen(QColor(ACCENT.red(), ACCENT.green(), ACCENT.blue(), 102))
                p.drawText(0, y0 + 12, "> ")
                p.setOpacity(0.4)
                p.setPen(TEXT_LOW)
                txt = "\u043e\u0436\u0438\u0434\u0430\u043d\u0438\u0435" + ("\u2588" if self._blink_on else "")
                p.drawText(14, y0 + 12, txt)
                p.setOpacity(1.0)
                return

            for i, ev in enumerate(self._events):
                c = EVENT_COLORS.get(ev["type"], TEXT_MID)
                alpha = max(60, 255 - i * 38)
                ry = y0 + i * 18

                # Index
                p.setFont(QFont(FONT_MONO, 6))
                p.setPen(QColor(TEXT_LOW.red(), TEXT_LOW.green(), TEXT_LOW.blue(), int(alpha * 0.3)))
                p.drawText(
                    QRectF(0, ry, 14, 14),
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                    f"{i + 1:02d}",
                )

                # Colour bar
                p.setBrush(QBrush(QColor(c.red(), c.green(), c.blue(), alpha)))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawRoundedRect(QRectF(18, ry + 2, 2, 10), 1, 1)

                # Timestamp
                p.setFont(QFont(FONT_MONO, 7))
                p.setPen(QColor(TEXT_LOW.red(), TEXT_LOW.green(), TEXT_LOW.blue(), alpha))
                p.drawText(26, ry + 10, ev["ts"])

                # Message (elided)
                mf = QFont(FONT_MONO, 8)
                p.setFont(mf)
                p.setPen(QColor(c.red(), c.green(), c.blue(), alpha))
                avail = w - 90
                msg = p.fontMetrics().elidedText(ev["msg"], Qt.TextElideMode.ElideRight, avail)
                p.drawText(82, ry + 10, msg)
