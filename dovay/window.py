from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QPixmap,
    QPainterPath, QRadialGradient, QLinearGradient,
)
from dovay.theme import VOID, BORDER, ACCENT, ACCENT_DIM, WIN_W, WIN_H
from dovay.scanner import AutoAcceptScanner
from dovay.header import Header
from dovay.ward_display import WardDisplay
from dovay.toggle_button import ToggleButton
from dovay.event_log import EventLog


class _Sep(QWidget):
    """1-px gradient separator."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedHeight(1)

    def paintEvent(self, _event):
        with QPainter(self) as p:
            g = QLinearGradient(0, 0, self.width(), 0)
            g.setColorAt(0, QColor(0, 0, 0, 0))
            g.setColorAt(0.05, QColor(0, 0, 0, 0))
            g.setColorAt(0.5, BORDER)
            g.setColorAt(0.95, QColor(0, 0, 0, 0))
            g.setColorAt(1, QColor(0, 0, 0, 0))
            p.setPen(QPen(QBrush(g), 1))
            p.drawLine(0, 0, self.width(), 0)


class DovayWindow(QWidget):
    """Main application window — frameless, always-on-top, 400x600."""

    def __init__(self):
        super().__init__()
        self.setFixedSize(WIN_W, WIN_H)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle("Dovay")

        # ── Scanner ─────────────────────────────────────────────────────
        self._scanner = AutoAcceptScanner()
        self._scanner.status_changed.connect(self._on_status)
        self._scanner.event_occurred.connect(self._on_event)

        self._active = False
        self._scan_count = 0
        self._scan_timer = QTimer(self)
        self._scan_timer.timeout.connect(self._on_scan_tick)

        # ── Widgets ─────────────────────────────────────────────────────
        self._header = Header()
        self._header.close_clicked.connect(self.close)
        self._header.minimize_clicked.connect(self.showMinimized)

        self._ward = WardDisplay()
        self._toggle = ToggleButton()
        self._toggle.clicked.connect(self._on_toggle)
        self._sep = _Sep()
        self._log = EventLog()
        self._log.debug_clicked.connect(self._on_debug)

        # ── Layout ──────────────────────────────────────────────────────
        root = QVBoxLayout(self)
        root.setContentsMargins(2, 2, 2, 2)
        root.setSpacing(0)

        frame = QWidget()
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(0, 0, 0, 0)
        fl.setSpacing(0)
        fl.addWidget(self._header)

        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(20, 0, 20, 16)
        bl.setSpacing(12)
        bl.addWidget(self._ward)
        bl.addWidget(self._toggle)
        bl.addWidget(self._sep)
        bl.addWidget(self._log, 1)

        fl.addWidget(body, 1)
        root.addWidget(frame)

        # ── Background tile ─────────────────────────────────────────────
        self._dot = QPixmap(20, 20)
        self._dot.fill(Qt.GlobalColor.transparent)
        with QPainter(self._dot) as tp:
            tp.setPen(QPen(QColor(ACCENT.red(), ACCENT.green(), ACCENT.blue(), 5), 1))
            tp.drawPoint(10, 10)

    # ── painting ────────────────────────────────────────────────────────
    def paintEvent(self, _event):
        with QPainter(self) as p:
            p.setRenderHint(QPainter.RenderHint.Antialiasing)

            rect = QRectF(2, 2, self.width() - 4, self.height() - 4)

            # Background
            p.setBrush(QBrush(VOID))
            p.setPen(QPen(BORDER, 1))
            p.drawRoundedRect(rect, 12, 12)

            # Clip for effects
            clip = QPainterPath()
            clip.addRoundedRect(rect, 12, 12)
            p.setClipPath(clip)

            # Dot grid
            p.drawTiledPixmap(rect.toRect(), self._dot)

            # Warm orb
            orb = QRadialGradient(self.width() / 2, -20, 160)
            orb.setColorAt(0, QColor(ACCENT.red(), ACCENT.green(), ACCENT.blue(), 10))
            orb.setColorAt(1, QColor(0, 0, 0, 0))
            p.setBrush(QBrush(orb))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(self.width() / 2, -20), 160, 160)

            # Vignette
            vig = QRadialGradient(
                self.width() / 2, self.height() / 2,
                max(self.width(), self.height()) * 0.6,
            )
            vig.setColorAt(0, QColor(0, 0, 0, 0))
            vig.setColorAt(0.3, QColor(0, 0, 0, 0))
            vig.setColorAt(1, QColor(4, 4, 8, 166))
            p.setBrush(QBrush(vig))
            p.drawRect(rect.toRect())

            # Top accent line
            p.setClipping(False)
            al = QLinearGradient(40, 2.5, self.width() - 40, 2.5)
            al.setColorAt(0, QColor(0, 0, 0, 0))
            al.setColorAt(0.25, QColor(ACCENT_DIM.red(), ACCENT_DIM.green(), ACCENT_DIM.blue(), 64))
            al.setColorAt(0.5, QColor(ACCENT.red(), ACCENT.green(), ACCENT.blue(), 64))
            al.setColorAt(0.75, QColor(ACCENT_DIM.red(), ACCENT_DIM.green(), ACCENT_DIM.blue(), 64))
            al.setColorAt(1, QColor(0, 0, 0, 0))
            p.setPen(QPen(QBrush(al), 1))
            p.drawLine(QPointF(40, 2.5), QPointF(self.width() - 40, 2.5))

    # ── slots ──────────────────────────────────────────────────────────
    def _on_toggle(self):
        if self._active:
            self._scanner.stop()
            self._active = False
            self._scan_timer.stop()
            self._scan_count = 0
            self._ward.set_status("idle", "\u0413\u043e\u0442\u043e\u0432 \u043a \u0437\u0430\u043f\u0443\u0441\u043a\u0443")
            self._ward.set_scan_count(0)
            self._toggle.set_active(False)
        else:
            if self._scanner.isRunning():
                self._scanner.stop()
                self._scanner.wait(1000)
            self._active = True
            self._scan_count = 0
            self._scan_timer.start(500)
            self._ward.set_status("scanning", "\u041e\u0436\u0438\u0434\u0430\u043d\u0438\u0435 \u043c\u0430\u0442\u0447\u0430...")
            self._toggle.set_active(True)
            self._scanner.start()

    def _on_status(self, status: str, message: str):
        self._ward.set_status(status, message)

    def _on_event(self, etype: str, message: str):
        self._log.add_event(etype, message)

    def _on_scan_tick(self):
        self._scan_count += 1
        self._ward.set_scan_count(self._scan_count)

    def _on_debug(self):
        self._log.add_event("info", "\u0414\u0435\u0431\u0430\u0433: \u0432\u0441\u0451 \u0440\u0430\u0431\u043e\u0442\u0430\u0435\u0442")

    def closeEvent(self, event):
        if self._active:
            self._scanner.stop()
            self._scanner.wait(2000)
        event.accept()
