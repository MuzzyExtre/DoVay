import webview
import time
import threading
import json
import mss
import ctypes
import numpy as np
import cv2
import datetime
import os
import ctypes.wintypes

# Шаблон кнопки Accept (загружается один раз)
_TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates', 'accept_button.png')
ACCEPT_TEMPLATE = cv2.imread(_TEMPLATE_PATH)
if ACCEPT_TEMPLATE is None:
    print(f'[WARN] Шаблон не найден: {_TEMPLATE_PATH}')

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

def get_focused_title():
    """Возвращает заголовок активного окна"""
    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return ''
    length = user32.GetWindowTextLengthW(hwnd) + 1
    buf = ctypes.create_unicode_buffer(length)
    user32.GetWindowTextW(hwnd, buf, length)
    return buf.value


def is_dota_focused():
    """True если активное окно — Dota 2"""
    title = get_focused_title()
    return title == 'Dota 2' or 'dota' in title.lower()


def click_mouse(x, y):
    # Получаем разрешение для нормализации абсолютных координат (0–65535)
    sm_cx = ctypes.windll.user32.GetSystemMetrics(0)
    sm_cy = ctypes.windll.user32.GetSystemMetrics(1)
    abs_x = int(x * 65536 / sm_cx)
    abs_y = int(y * 65536 / sm_cy)
    extra = ctypes.c_ulong(0)

    MOVE_ABS = 0x0001 | 0x8000  # MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE
    DOWN = 0x0002               # MOUSEEVENTF_LEFTDOWN
    UP = 0x0004                 # MOUSEEVENTF_LEFTUP

    ii_move = Input_I(); ii_move.mi = MouseInput(abs_x, abs_y, 0, MOVE_ABS, 0, ctypes.pointer(extra))
    ii_down = Input_I(); ii_down.mi = MouseInput(abs_x, abs_y, 0, MOVE_ABS | DOWN, 0, ctypes.pointer(extra))
    ii_up   = Input_I(); ii_up.mi   = MouseInput(abs_x, abs_y, 0, MOVE_ABS | UP, 0, ctypes.pointer(extra))

    # Сначала перемещаем курсор через SendInput (работает в fullscreen)
    move_input = (Input * 1)(Input(0, ii_move))
    ctypes.windll.user32.SendInput(1, move_input, ctypes.sizeof(Input))
    time.sleep(0.05)

    # Потом клик
    click_inputs = (Input * 2)(Input(0, ii_down), Input(0, ii_up))
    ctypes.windll.user32.SendInput(2, click_inputs, ctypes.sizeof(Input))
    time.sleep(0.1)

    # Убираем курсор в угол
    ii_hide = Input_I(); ii_hide.mi = MouseInput(0, 0, 0, MOVE_ABS, 0, ctypes.pointer(extra))
    hide_input = (Input * 1)(Input(0, ii_hide))
    ctypes.windll.user32.SendInput(1, hide_input, ctypes.sizeof(Input))


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
        if ACCEPT_TEMPLATE is None:
            self.send_event('error', 'Шаблон accept_button.png не найден!')
            return

        # Шаблон вырезан с экрана 2559x1439 — масштабируем под текущее разрешение
        TEMPLATE_REF_W = 2559
        consecutive = 0
        threshold = 2
        match_threshold = 0.70   # уверенность совпадения [0..1]

        with mss.mss() as sct:
            monitor = sct.monitors[1]
            w, h = monitor["width"], monitor["height"]
            # Центральная область поиска
            sx = max(0, int(w * 0.3))
            sy = max(0, int(h * 0.25))
            sw = int(w * 0.4)
            sh = int(h * 0.30)
            bbox = {'top': monitor["top"] + sy, 'left': monitor["left"] + sx, 'width': sw, 'height': sh}

            # Подгоняем шаблон под разрешение пользователя
            scale = w / TEMPLATE_REF_W
            th, tw = ACCEPT_TEMPLATE.shape[:2]
            new_tw, new_th = max(1, int(tw * scale)), max(1, int(th * scale))
            template = cv2.resize(ACCEPT_TEMPLATE, (new_tw, new_th), interpolation=cv2.INTER_AREA)
            self.send_event('info', f'Экран {w}x{h}, шаблон {new_tw}x{new_th} (scale {scale:.2f})')

            last_debug = 0
            was_dota_focused = True
            while self.loop_active:
                t0 = time.time()

                # Сканируем только когда Dota 2 — активное окно
                if not is_dota_focused():
                    if was_dota_focused:
                        title = get_focused_title()
                        self.send_event('info', f'Не Dota: "{title[:40]}" — пауза')
                        was_dota_focused = False
                    consecutive = 0
                    time.sleep(0.5)
                    continue
                if not was_dota_focused:
                    self.send_event('info', 'Dota в фокусе — сканирую')
                    was_dota_focused = True

                try:
                    img = np.array(sct.grab(bbox))[:, :, :3]  # BGRA → BGR

                    # Debug снимок каждые 5 сек
                    if t0 - last_debug > 5:
                        cv2.imwrite(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'debug_scan.png'), img)
                        last_debug = t0

                    # Template matching на нескольких масштабах (на случай разного UI scale)
                    best_val = 0
                    best_loc = None
                    best_size = (new_tw, new_th)
                    for s in (0.85, 1.0, 1.15):
                        tw2, th2 = int(new_tw * s), int(new_th * s)
                        if tw2 < 30 or th2 < 10 or tw2 > sw or th2 > sh:
                            continue
                        tpl = cv2.resize(template, (tw2, th2), interpolation=cv2.INTER_AREA)
                        result = cv2.matchTemplate(img, tpl, cv2.TM_CCOEFF_NORMED)
                        _, max_val, _, max_loc = cv2.minMaxLoc(result)
                        if max_val > best_val:
                            best_val = max_val
                            best_loc = max_loc
                            best_size = (tw2, th2)

                    if best_val >= match_threshold and best_loc:
                        bw2, bh2 = best_size
                        cx = best_loc[0] + bw2 // 2 + sx + monitor["left"]
                        cy = best_loc[1] + bh2 // 2 + sy + monitor["top"]
                        consecutive += 1
                        self.send_event('info', f'Совпадение #{consecutive}: {best_val:.2f} @ [{cx},{cy}]')
                        if consecutive >= threshold:
                            self.update_status('match_found', 'Матч найден! Принимаю...')
                            self.send_event('success', f'Кнопка [{cx}, {cy}] match={best_val:.2f}')
                            time.sleep(0.3)
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
