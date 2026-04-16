import webview
import time
import threading
import json
import mss
import ctypes
import numpy as np
import datetime
import os
import ctypes.wintypes

# ═══════════════════════════════════════════════
#  SendInput (аппаратный клик мыши для Dota 2)
# ═══════════════════════════════════════════════
PUL = ctypes.POINTER(ctypes.c_ulong)
class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong), ("dwExtraInfo", PUL)]
class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong), ("wParamL", ctypes.c_short), ("wParamH", ctypes.c_ushort)]
class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long), ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong), ("dwExtraInfo", PUL)]
class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput), ("mi", MouseInput), ("hi", HardwareInput)]
class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("ii", Input_I)]

def click_mouse(x, y):
    ctypes.windll.user32.SetCursorPos(x, y)
    time.sleep(0.06)
    extra = ctypes.c_ulong(0)
    ii_ = Input_I(); ii_.mi = MouseInput(0, 0, 0, 0x0002, 0, ctypes.pointer(extra))
    ii2_ = Input_I(); ii2_.mi = MouseInput(0, 0, 0, 0x0004, 0, ctypes.pointer(extra))
    cmd1 = Input(0, ii_); cmd2 = Input(0, ii2_)
    ctypes.windll.user32.SendInput(2, ctypes.pointer(cmd1), ctypes.sizeof(cmd1))
    time.sleep(0.1)
    ctypes.windll.user32.SetCursorPos(0, 0)


# ═══════════════════════════════════════════════
#  API (мост Python ↔ JavaScript)
# ═══════════════════════════════════════════════
class Api:
    def __init__(self):
        self._window = None
        self._hwnd = None
        self.loop_active = False
        self.overlay_active = True

    def set_window(self, window):
        self._window = window

    def start(self):
        if self.loop_active: return
        self.loop_active = True
        self.send_event('info', 'Сканирование запущено')
        threading.Thread(target=self._scanner_loop, daemon=True).start()

    def stop(self):
        self.loop_active = False
        self.send_event('info', 'Сканирование остановлено')

    def close(self):
        if self._window: self._window.destroy()

    def minimize(self):
        if self._window: self._window.minimize()

    def start_drag(self, screen_x, screen_y):
        """JS вызывает при mousedown на header — запоминаем смещение"""
        if self._window:
            self._drag_offset_x = screen_x - self._window.x
            self._drag_offset_y = screen_y - self._window.y

    def do_drag(self, screen_x, screen_y):
        """JS вызывает при mousemove — двигаем окно"""
        if self._window and hasattr(self, '_drag_offset_x'):
            self._window.move(
                screen_x - self._drag_offset_x,
                screen_y - self._drag_offset_y
            )

    def toggle_overlay(self):
        """Переключаем: окно поверх всех / обычное"""
        if not self._hwnd:
            return self.overlay_active
        
        user32 = ctypes.windll.user32
        HWND_TOPMOST = -1
        HWND_NOTOPMOST = -2
        SWP_NOMOVE = 0x0002
        SWP_NOSIZE = 0x0001
        
        self.overlay_active = not self.overlay_active
        
        if self.overlay_active:
            user32.SetWindowPos(self._hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
            self.send_event('info', '📌 Оверлей: ВКЛ')
        else:
            user32.SetWindowPos(self._hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
            self.send_event('info', '📌 Оверлей: ВЫКЛ')
        
        return self.overlay_active

    def debug(self):
        self.send_event('info', 'Debug screenshot saved')

    def send_event(self, type_str, message):
        if not self._window: return
        event = {
            'id': str(time.time()),
            'timestamp': datetime.datetime.now().strftime('%H:%M:%S'),
            'type': type_str,
            'message': message
        }
        self._window.evaluate_js(f"if(window.addEventFromPython) window.addEventFromPython({json.dumps(event)})")

    def update_status(self, status, message):
        if not self._window: return
        self._window.evaluate_js(f"if(window.updateStatusFromPython) window.updateStatusFromPython('{status}', '{message}')")

    def _scanner_loop(self):
        consecutive = 0
        threshold = 2
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            w, h = monitor["width"], monitor["height"]
            sx = max(0, w // 2 - 250)
            sy = max(0, int(h * 0.42))
            sw = min(500, w - sx)
            sh = min(160, h - sy)
            bbox = {'top': monitor["top"] + sy, 'left': monitor["left"] + sx, 'width': sw, 'height': sh}

            while self.loop_active:
                t0 = time.time()
                try:
                    img = np.array(sct.grab(bbox))
                    b, g, r = img[:, :, 0], img[:, :, 1], img[:, :, 2]
                    mask = (g >= 160) & (r >= 40) & (r <= 150) & (b >= 20) & (b <= 130) & ((g.astype(int) - r) >= 50) & ((g.astype(int) - b) >= 60)
                    y_coords, x_coords = np.where(mask)
                    count = len(x_coords)
                    
                    if count >= 200:
                        min_x, max_x = np.min(x_coords), np.max(x_coords)
                        min_y, max_y = np.min(y_coords), np.max(y_coords)
                        bw, bh = max_x - min_x, max(1, max_y - min_y)
                        if bw > bh * 2 and 80 <= bw <= 500 and 15 <= bh <= 120:
                            cx = int(np.mean(x_coords)) + sx + monitor["left"]
                            cy = int(np.mean(y_coords)) + sy + monitor["top"]
                            consecutive += 1
                            if consecutive >= threshold:
                                self.update_status('match_found', 'Матч найден! Принимаю...')
                                self.send_event('success', f'Кнопка [{cx}, {cy}]')
                                time.sleep(0.2)
                                if self.loop_active:
                                    click_mouse(cx, cy)
                                    self.update_status('accepted', 'Принято \u2713')
                                    self.send_event('success', 'Матч принят!')
                                    consecutive = 0
                                    time.sleep(5)
                                    if self.loop_active:
                                        self.update_status('scanning', 'Ожидание матча...')
                            time.sleep(0.15)
                            continue
                    consecutive = 0
                except Exception as e:
                    self.send_event('error', f'Ошибка: {str(e)}')
                    consecutive = 0
                elapsed = time.time() - t0
                time.sleep(max(0, 0.3 - elapsed))


# ═══════════════════════════════════════════════
#  Поиск HWND после старта (для overlay toggle)
# ═══════════════════════════════════════════════
def on_started(api):
    time.sleep(1.0)
    user32 = ctypes.windll.user32
    hwnd = user32.FindWindowW(None, 'DoVay')
    if hwnd:
        api._hwnd = hwnd
        print(f"[OK] HWND: {hwnd}")
    else:
        print("[WARN] HWND not found")


# ═══════════════════════════════════════════════
#  ЗАПУСК
# ═══════════════════════════════════════════════
if __name__ == '__main__':
    api = Api()
    
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ui', 'index.html')
    if not os.path.exists(html_path):
        print(f"File not found: {html_path}")
        exit(1)
        
    window = webview.create_window(
        'DoVay', 
        url=f'file:///{html_path}', 
        js_api=api,
        width=400, 
        height=600,
        frameless=True,            # Чистый виджет, без системного заголовка
        easy_drag=False,           # Мы сами управляем drag через CSS
        resizable=False,
        on_top=True,
        background_color='#060609' # Тёмный фон = нет белых углов
    )
    api.set_window(window)
    webview.start(func=on_started, args=(api,))
