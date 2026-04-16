from PySide6.QtWidgets import QWidget, QPushButton
from PySide6.QtCore import Signal, Qt, QPointF
from PySide6.QtGui import (
    QPainter, QPen, QFont, QColor, QBrush, QLinearGradient,
)
from dovay.theme import (
    ACCENT, DANGER, TEXT_HIGH, TEXT_LOW,
    SURFACE_RAISED, BORDER_LIGHT,
    FONT_DISPLAY, FONT_MONO, HEADER_H,
)


class _WinBtn(QPushButton):
    """Frameless window control button (minimize / close)."""

    def __init__(self, kind: str, parent: QWidget | None = None):
        super().__init__(parent)
        self._kind = kind
        self._hovered = False
        self.setFixedSize(28, 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, _event):
        with QPainter(self) as p:
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            if self._hovered:
                p.setBrush(QBrush(SURFACE_RAISED))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawRoundedRect(self.rect(), 6, 6)

            color = ACCENT if self._kind == "min" else DANGER
            if not self._hovered:
                color = TEXT_LOW
            pen = QPen(color, 1.5)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)

            cx, cy = self.width() // 2, self.height() // 2
            if self._kind == "min":
                p.drawLine(cx - 5, cy, cx + 5, cy)
            else:
                p.drawLine(cx - 4, cy - 4, cx + 4, cy + 4)
                p.drawLine(cx + 4, cy - 4, cx - 4, cy + 4)

    def enterEvent(self, _event):
        self._hovered = True
        self.update()

    def leaveEvent(self, _event):
        self._hovered = False
        self.update()


class Header(QWidget):
    """Custom draggable title bar."""

    close_clicked = Signal()
    minimize_clicked = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedHeight(HEADER_H)
        self._drag_pos: QPointF | None = None

        self._min_btn = _WinBtn("min", self)
        self._close_btn = _WinBtn("close", self)
        self._min_btn.clicked.connect(self.minimize_clicked)
        self._close_btn.clicked.connect(self.close_clicked)

    def resizeEvent(self, _event):
        bw = 28
        y = (self.height() - bw) // 2
        self._close_btn.move(self.width() - 14 - bw, y)
        self._min_btn.move(self.width() - 14 - bw * 2 - 2, y)

    def paintEvent(self, _event):
        with QPainter(self) as p:
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            mid_y = self.height() / 2

            # Diamond icon
            p.save()
            p.translate(20, mid_y)
            p.rotate(45)
            p.setBrush(QBrush(ACCENT))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(-4, -4, 8, 8, 1, 1)
            p.restore()

            # "DOVAY"
            font = QFont(FONT_DISPLAY, 10)
            font.setWeight(QFont.Weight.Bold)
            font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 135)
            p.setFont(font)
            p.setPen(TEXT_HIGH)
            p.drawText(34, int(mid_y + 4), "DOVAY")

            # Version badge
            bx, by, bw, bh = 96, int(mid_y - 6), 28, 13
            p.setPen(QPen(BORDER_LIGHT, 1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(bx, by, bw, bh, 3, 3)

            fm = QFont(FONT_MONO, 6)
            fm.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 112)
            p.setFont(fm)
            p.setPen(TEXT_LOW)
            p.drawText(bx + 4, by + 10, "v0.1")

            # Bottom gradient line
            grad = QLinearGradient(20, 0, self.width() - 20, 0)
            grad.setColorAt(0, QColor(0, 0, 0, 0))
            grad.setColorAt(0.3, BORDER_LIGHT)
            grad.setColorAt(0.7, BORDER_LIGHT)
            grad.setColorAt(1, QColor(0, 0, 0, 0))
            p.setPen(QPen(QBrush(grad), 1))
            p.drawLine(20, self.height() - 1, self.width() - 20, self.height() - 1)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.window().pos()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and (event.buttons() & Qt.MouseButton.LeftButton):
            self.window().move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, _event):
        self._drag_pos = None
