from PySide6.QtGui import QColor

# ── Backgrounds ──
VOID = QColor(6, 6, 10)
INK = QColor(12, 12, 18)
SURFACE = QColor(20, 20, 28)
SURFACE_RAISED = QColor(28, 28, 38)
SURFACE_HOVER = QColor(37, 37, 48)

# ── Accent ──
ACCENT = QColor(212, 166, 67)
ACCENT_BRIGHT = QColor(235, 195, 90)
ACCENT_DIM = QColor(154, 122, 48)

# ── Semantic ──
DANGER = QColor(212, 85, 85)
SUCCESS = QColor(69, 196, 144)
WARNING = QColor(224, 136, 64)

# ── Text ──
TEXT_HIGH = QColor(234, 232, 228)
TEXT_MID = QColor(138, 136, 144)
TEXT_LOW = QColor(80, 80, 88)

# ── Borders ──
BORDER = QColor(28, 28, 38)
BORDER_LIGHT = QColor(38, 38, 58)

# ── State colors ──
STATE_COLORS: dict[str, QColor] = {
    "idle": QColor(138, 122, 80),
    "scanning": QColor(212, 166, 67),
    "match_found": QColor(232, 112, 64),
    "accepted": QColor(69, 196, 144),
}

STATE_LABELS: dict[str, str] = {
    "idle": "\u041e\u0416\u0418\u0414\u0410\u041d\u0418\u0415",
    "scanning": "\u041f\u041e\u0418\u0421\u041a",
    "match_found": "\u041c\u0410\u0422\u0427",
    "accepted": "\u041f\u0420\u0418\u041d\u042f\u0422\u041e",
}

# ── Event type colors ──
EVENT_COLORS: dict[str, QColor] = {
    "info": QColor(138, 136, 144),
    "success": QColor(69, 196, 144),
    "error": QColor(212, 85, 85),
}

# ── Fonts ──
FONT_DISPLAY = "Segoe UI"
FONT_MONO = "Consolas"

# ── Dimensions ──
WIN_W = 400
WIN_H = 600
HEADER_H = 48
