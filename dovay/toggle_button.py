from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal, Qt, QTimer, QPointF, QRectF
from PySide6.QtGui import QPainter, QPen, QFont, QColor, QBrush
from dovay.theme import ACCENT, DANGER, SURFACE, BORDER, FONT_DISPLAY


class ToggleButton(QWidget):
    """Start / Stop toggle with hover and blink effects."""

    clicked = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedHeight(46)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._active = False
        self._hovered = False
        self._blink_on = True

        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._toggle_blink)

    def set_active(self, active: bool):
        self._active = active
        if active:
            self._blink_timer.start(400)
        else:
            self._blink_timer.stop()
            self._blink_on = True
        self.update()

    def _toggle_blink(self):
        self._blink_on = not self._blink_on
        self.update()

    # ── painting ────────────────────────────────────────────────────────
    def paintEvent(self, _event):
        with QPainter(self) as p:
            p.setRenderHint(QPainter.RenderHint.Antialiasing)

            color = DANGER if self._active else ACCENT
            rect = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)

            bg = QColor(color.red(), color.green(), color.blue(), 6) if self._active else SURFACE
            p.setBrush(QBrush(bg))

            if self._hovered:
                bc = color
            elif self._active:
                bc = QColor(color.red(), color.green(), color.blue(), 88)
            else:
                bc = BORDER
            p.setPen(QPen(bc, 1))
            p.drawRoundedRect(rect, 8, 8)

            # Active blink dot
            if self._active and self._blink_on:
                p.setBrush(QBrush(color))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(QPointF(16, self.height() / 2), 2, 2)

            # Label
            font = QFont(FONT_DISPLAY, 9)
            font.setWeight(QFont.Weight.Bold)
            font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 125)
            p.setFont(font)
            p.setPen(color)
            icon = "\u25a0" if self._active else "\u25b6"
            label = "\u0421\u0422\u041e\u041f" if self._active else "\u0417\u0410\u041f\u0423\u0421\u041a"
            p.drawText(rect.toRect(), Qt.AlignmentFlag.AlignCenter, f"{icon}  {label}")

    # ── interaction ─────────────────────────────────────────────────────
    def enterEvent(self, _event):
        self._hovered = True
        self.update()

    def leaveEvent(self, _event):
        self._hovered = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
