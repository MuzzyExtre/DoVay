import threading
import numpy as np
from PySide6.QtCore import QThread, Signal


class AutoAcceptScanner(QThread):
    """Background thread that scans the screen center for the Dota 2
    accept button (bright-green pixels) and clicks it automatically."""

    status_changed = Signal(str, str)  # (status, message)
    event_occurred = Signal(str, str)  # (type, message)

    def __init__(self):
        super().__init__()
        self._stop = threading.Event()

    def run(self):
        import mss
        import pyautogui

        self._stop.clear()
        self.status_changed.emit("scanning", "\u041e\u0436\u0438\u0434\u0430\u043d\u0438\u0435 \u043c\u0430\u0442\u0447\u0430...")
        self.event_occurred.emit("info", "\u0421\u043a\u0430\u043d\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u0435 \u0437\u0430\u043f\u0443\u0449\u0435\u043d\u043e")

        try:
            with mss.mss() as sct:
                mon = sct.monitors[1]
                sw, sh = mon["width"], mon["height"]
                region = {
                    "left": (sw - 600) // 2,
                    "top": (sh - 240) // 2,
                    "width": 600,
                    "height": 240,
                }

                while not self._stop.is_set():
                    img = sct.grab(region)
                    px = np.array(img, dtype=np.int16)

                    # mss returns BGRA on Windows
                    b, g, r = px[:, :, 0], px[:, :, 1], px[:, :, 2]
                    mask = (
                        (g > 85) & (r < 130) & (b < 110)
                        & (g > r * 1.4) & (g > b * 1.4)
                    )
                    count = int(np.sum(mask))

                    if count >= 80:
                        self.status_changed.emit("match_found", "\u041c\u0430\u0442\u0447 \u043d\u0430\u0439\u0434\u0435\u043d!")
                        self.event_occurred.emit(
                            "success", f"\u041e\u0431\u043d\u0430\u0440\u0443\u0436\u0435\u043d \u043c\u0430\u0442\u0447 ({count} px)",
                        )

                        ys, xs = np.where(mask)
                        cx = int(np.mean(xs)) + region["left"]
                        cy = int(np.mean(ys)) + region["top"]

                        if self._stop.wait(0.3):
                            break

                        pyautogui.click(cx, cy)
                        self.status_changed.emit("accepted", "\u041c\u0430\u0442\u0447 \u043f\u0440\u0438\u043d\u044f\u0442!")
                        self.event_occurred.emit("success", f"\u041a\u043b\u0438\u043a: ({cx}, {cy})")

                        if self._stop.wait(3.0):
                            break

                        self.status_changed.emit("scanning", "\u041e\u0436\u0438\u0434\u0430\u043d\u0438\u0435 \u043c\u0430\u0442\u0447\u0430...")

                    if self._stop.wait(0.5):
                        break

        except Exception as e:
            self.event_occurred.emit("error", str(e))

    def stop(self):
        self._stop.set()
