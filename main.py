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
import sys
import ctypes.wintypes


def _resource_path(rel):
    """Путь к ресурсу: рядом с .py при разработке, внутри _MEIPASS — при PyInstaller --onefile"""
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


def _user_data_dir():
    """Каталог для пользовательских данных:
    - bundled EXE: %APPDATA%/DoVay/ (чтобы не сорить рядом с EXE)
    - dev: рядом с main.py"""
    if getattr(sys, 'frozen', False):
        base = os.environ.get('APPDATA') or os.path.expanduser('~')
        path = os.path.join(base, 'DoVay')
        os.makedirs(path, exist_ok=True)
        return path
    return os.path.dirname(os.path.abspath(__file__))


# Файл с пользовательскими настройками — всегда рядом с EXE / main.py
_SETTINGS_PATH = os.path.join(_user_data_dir(), 'settings.json')

def _load_settings():
    try:
        with open(_SETTINGS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def _save_settings(data):
    try:
        with open(_SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARN] save settings: {e}")

# Шаблон кнопки Accept (загружается один раз)
_TEMPLATE_PATH = _resource_path(os.path.join('templates', 'accept_button.png'))
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
def _today_str():
    return datetime.date.today().isoformat()


class Api:
    def __init__(self):
        self._window = None
        self._hwnd = None
        self.loop_active = False
        # Стартуем сразу в компактном (overlay) режиме
        self.compact_mode = True
        self.position_locked = False
        self._resize_start = None

        self._settings = _load_settings()
        self.overlay_alpha_pct = int(self._settings.get('overlay_alpha_pct', 92))

        # Лимиты / поведение
        self.loss_streak_limit = int(self._settings.get('loss_streak_limit', 3))
        # late_hour: 0 = выключено, иначе 18..26 (>24 — за полночь)
        self.late_hour = int(self._settings.get('late_hour', 23))
        self.auto_accept_enabled = bool(self._settings.get('auto_accept_enabled', True))

        # Статистика дня (W/L), автосброс на новый день
        today = _today_str()
        if self._settings.get('stats_date') != today:
            self._settings['stats_date'] = today
            self._settings['wins'] = 0
            self._settings['losses'] = 0
            self._settings['loss_streak'] = 0
            self._settings['late_alert_dismissed_date'] = ''
            _save_settings(self._settings)
        self.wins = int(self._settings.get('wins', 0))
        self.losses = int(self._settings.get('losses', 0))
        self.loss_streak = int(self._settings.get('loss_streak', 0))
        self.late_alert_dismissed_date = str(self._settings.get('late_alert_dismissed_date', ''))

        # Сессия = с момента запуска приложения
        self.session_start_ts = time.time()

    def set_window(self, window):
        self._window = window

    # ─── Авто-акцепт сканер ───────────────────────────
    def start(self):
        if self.loop_active: return
        if not self.auto_accept_enabled:
            self.send_event('info', 'Авто-акцепт выключен в настройках')
            return
        self.loop_active = True
        self.send_event('info', 'Сканирование запущено')
        threading.Thread(target=self._scanner_loop, daemon=True).start()

    def stop(self):
        self.loop_active = False
        self.send_event('info', 'Сканирование остановлено')

    def set_auto_accept_enabled(self, enabled):
        self.auto_accept_enabled = bool(enabled)
        self._settings['auto_accept_enabled'] = self.auto_accept_enabled
        _save_settings(self._settings)
        if not self.auto_accept_enabled and self.loop_active:
            self.stop()
        return self.auto_accept_enabled

    def close(self):
        if self._window: self._window.destroy()

    # ─── Статистика W/L ───────────────────────────────
    def _persist_stats(self):
        self._settings['stats_date'] = _today_str()
        self._settings['wins'] = self.wins
        self._settings['losses'] = self.losses
        self._settings['loss_streak'] = self.loss_streak
        self._settings['late_alert_dismissed_date'] = self.late_alert_dismissed_date
        _save_settings(self._settings)

    def _ensure_today(self):
        """Если сменился день — обнуляем счётчики (но НЕ сессионный таймер,
        он живёт пока приложение запущено)."""
        if self._settings.get('stats_date') != _today_str():
            self.wins = 0
            self.losses = 0
            self.loss_streak = 0
            self.late_alert_dismissed_date = ''
            self._persist_stats()

    def add_win(self):
        self._ensure_today()
        self.wins += 1
        self.loss_streak = 0
        self._persist_stats()
        self.send_event('success', f'+W ({self.wins}W {self.losses}L)')
        return self.get_stats()

    def add_loss(self):
        self._ensure_today()
        self.losses += 1
        self.loss_streak += 1
        self._persist_stats()
        self.send_event('error', f'+L ({self.wins}W {self.losses}L · стрик {self.loss_streak})')
        if self.loss_streak >= self.loss_streak_limit and self.loss_streak_limit > 0:
            self.send_event('error', f'⚠ {self.loss_streak} поражений подряд — пора сделать паузу')
        return self.get_stats()

    def undo_last(self):
        """Откат последней отметки нельзя сделать точно (не храним историю),
        но можно уменьшить wins/losses вручную через кнопки (убрали из UI)."""
        return self.get_stats()

    def reset_session(self):
        """Сброс счётчиков и таймера сессии."""
        self.wins = 0
        self.losses = 0
        self.loss_streak = 0
        self.late_alert_dismissed_date = ''
        self.session_start_ts = time.time()
        self._persist_stats()
        self.send_event('info', 'Сессия сброшена')
        return self.get_stats()

    def _streak_alert(self):
        return self.loss_streak_limit > 0 and self.loss_streak >= self.loss_streak_limit

    def _late_alert(self):
        if not self.late_hour or self.late_hour <= 0:
            return False
        if self.late_alert_dismissed_date == _today_str():
            return False
        # Поздний час: late_hour 18..26 — поддержка «за полночь» (25 = 01:00)
        h = datetime.datetime.now().hour
        lh = self.late_hour % 24
        if self.late_hour >= 24:
            # Например late_hour=25 → алерт с 01:00 до утра (4–6)
            return 0 <= h < (self.late_hour - 24 + 4)
        # Стандарт: после late_hour и до 6 утра
        return h >= lh or h < 6

    def get_stats(self):
        self._ensure_today()
        return {
            'wins': self.wins,
            'losses': self.losses,
            'loss_streak': self.loss_streak,
            'session_start_ts': self.session_start_ts,
            'now_ts': time.time(),
            'streak_alert': self._streak_alert(),
            'late_alert': self._late_alert(),
            'date': _today_str(),
        }

    def dismiss_late_alert(self):
        self.late_alert_dismissed_date = _today_str()
        self._persist_stats()
        return self.get_stats()

    # ─── Настройки ────────────────────────────────────
    def get_settings(self):
        return {
            'overlay_alpha_pct': self.overlay_alpha_pct,
            'loss_streak_limit': self.loss_streak_limit,
            'late_hour': self.late_hour,
            'auto_accept_enabled': self.auto_accept_enabled,
        }

    def set_loss_streak_limit(self, n):
        try:
            n = max(0, min(20, int(n)))
        except (TypeError, ValueError):
            return self.loss_streak_limit
        self.loss_streak_limit = n
        self._settings['loss_streak_limit'] = n
        _save_settings(self._settings)
        return n

    def set_late_hour(self, h):
        try:
            h = max(0, min(26, int(h)))
        except (TypeError, ValueError):
            return self.late_hour
        self.late_hour = h
        self._settings['late_hour'] = h
        _save_settings(self._settings)
        return h

    def minimize(self):
        if self._window: self._window.minimize()

    def start_drag(self, screen_x, screen_y):
        if self.position_locked or not self._window:
            return
        self._drag_offset_x = screen_x - self._window.x
        self._drag_offset_y = screen_y - self._window.y

    def do_drag(self, screen_x, screen_y):
        if self.position_locked or not self._window:
            return
        if hasattr(self, '_drag_offset_x'):
            self._window.move(
                screen_x - self._drag_offset_x,
                screen_y - self._drag_offset_y
            )

    def toggle_lock(self):
        self.position_locked = not self.position_locked
        self.send_event('info', '🔒 Позиция закреплена' if self.position_locked else '🔓 Позиция свободна')
        return self.position_locked

    def start_resize(self, screen_x, screen_y):
        if not self._window:
            return
        try:
            self._resize_start = (screen_x, screen_y, self._window.width, self._window.height)
        except Exception:
            self._resize_start = (screen_x, screen_y, 420, 720)

    def do_resize(self, screen_x, screen_y):
        if not self._window or not self._resize_start:
            return
        sx, sy, w0, h0 = self._resize_start
        new_w = max(320, w0 + (screen_x - sx))
        new_h = max(240, h0 + (screen_y - sy))
        self._window.resize(int(new_w), int(new_h))

    def toggle_compact(self):
        """Переключаем compact-overlay ↔ панель настроек.
        Запоминаем позиции и размеры обоих режимов отдельно."""
        if not self._window:
            return self.compact_mode
        try:
            cur_size = (self._window.width, self._window.height)
            cur_pos = (self._window.x, self._window.y)
        except Exception:
            cur_size = (540, 72) if self.compact_mode else (420, 660)
            cur_pos = None

        if self.compact_mode:
            # compact → full (панель настроек)
            self._compact_size = cur_size
            self._compact_pos = cur_pos
            self.compact_mode = False
            if self._hwnd:
                _apply_layered_transparency(self._hwnd, False)
            full_size = getattr(self, '_full_size', (420, 660))
            self._window.resize(*full_size)
            full_pos = getattr(self, '_full_pos', None)
            if full_pos:
                self._window.move(*full_pos)
        else:
            # full → compact (overlay)
            self._full_size = cur_size
            self._full_pos = cur_pos
            self.compact_mode = True
            compact_size = getattr(self, '_compact_size', (540, 72))
            self._window.resize(*compact_size)
            compact_pos = getattr(self, '_compact_pos', None)
            if compact_pos:
                self._window.move(*compact_pos)
            if self._hwnd:
                _apply_layered_transparency(self._hwnd, True, self._alpha_byte())
        return self.compact_mode

    def _alpha_byte(self):
        """Процент 40–100 → байт 102–255"""
        pct = max(40, min(100, int(self.overlay_alpha_pct)))
        return int(round(pct * 255 / 100))

    def get_overlay_alpha(self):
        """Текущая прозрачность оверлея в процентах"""
        return int(self.overlay_alpha_pct)

    def set_overlay_alpha(self, pct):
        """Изменить прозрачность оверлея (40–100%) и применить мгновенно если активен compact"""
        try:
            pct = max(40, min(100, int(pct)))
        except (TypeError, ValueError):
            return self.overlay_alpha_pct
        self.overlay_alpha_pct = pct
        self._settings['overlay_alpha_pct'] = pct
        _save_settings(self._settings)
        if self.compact_mode and self._hwnd:
            _apply_layered_transparency(self._hwnd, True, self._alpha_byte())
        return pct

    def set_position_preset(self, preset):
        """Перемещает окно в один из угловых пресетов экрана"""
        if not self._hwnd or not self._window:
            return
        user32 = ctypes.windll.user32
        sw = user32.GetSystemMetrics(0)
        sh = user32.GetSystemMetrics(1)
        rect = ctypes.wintypes.RECT()
        user32.GetWindowRect(self._hwnd, ctypes.byref(rect))
        ww = rect.right - rect.left
        wh = rect.bottom - rect.top
        m = 14
        taskbar = 56
        positions = {
            'tl': (m, m),
            'tc': ((sw - ww) // 2, m),
            'tr': (sw - ww - m, m),
            'bl': (m, sh - wh - m - taskbar),
            'bc': ((sw - ww) // 2, sh - wh - m - taskbar),
            'br': (sw - ww - m, sh - wh - m - taskbar),
            'cc': ((sw - ww) // 2, (sh - wh) // 2),
        }
        if preset in positions:
            x, y = positions[preset]
            self._window.move(x, y)
            self.send_event('info', f'Позиция: {preset.upper()}')

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

                    # Debug снимок только в режиме разработки
                    if not getattr(sys, 'frozen', False) and t0 - last_debug > 5:
                        cv2.imwrite(os.path.join(_user_data_dir(), 'debug_scan.png'), img)
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
def _set_window_corners(hwnd, rounded):
    """Win11 DWM corner preference.
    rounded=True: скруглённые углы + системная тень (полный режим)
    rounded=False: квадратные углы без тени (compact-overlay)"""
    try:
        DWMWA_WINDOW_CORNER_PREFERENCE = 33
        DWMWCP_ROUND = 2
        DWMWCP_DONOTROUND = 1
        pref = ctypes.c_int(DWMWCP_ROUND if rounded else DWMWCP_DONOTROUND)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_WINDOW_CORNER_PREFERENCE,
            ctypes.byref(pref), ctypes.sizeof(pref))
    except Exception as e:
        print(f"[WARN] DWM corner pref: {e}")


def _round_window_corners(hwnd):
    """Backwards-compat: скруглить (на старте)"""
    _set_window_corners(hwnd, True)


# ═══════════════════════════════════════════════
#  Прозрачность через WS_EX_LAYERED + color-key
#  (Edge/WebView2 не поддерживает per-pixel alpha,
#   color-key делает заданный цвет фона полностью
#   прозрачным — desktop виден насквозь)
# ═══════════════════════════════════════════════
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
LWA_COLORKEY = 0x00000001
LWA_ALPHA = 0x00000002
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOZORDER = 0x0004
SWP_FRAMECHANGED = 0x0020
# CSS-цвет #FE00FF → COLORREF 0x00BBGGRR = 0x00FF00FE
KEY_COLOR_REF = 0x00FF00FE

def _apply_layered_transparency(hwnd, compact, alpha=235):
    """compact=True: окно становится 'плавающим' — magenta-фон CSS = прозрачный.
    compact=False: убираем layered, окно полностью непрозрачное.
    alpha: 0–255, прозрачность всей панели поверх desktop."""
    user32 = ctypes.windll.user32
    style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    if compact:
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED)
        user32.SetLayeredWindowAttributes(hwnd, KEY_COLOR_REF, int(alpha),
                                          LWA_COLORKEY | LWA_ALPHA)
    else:
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style & ~WS_EX_LAYERED)
    user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0,
                        SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED)


def on_started(api):
    time.sleep(1.0)
    user32 = ctypes.windll.user32
    hwnd = user32.FindWindowW(None, 'DoVay')
    if hwnd:
        api._hwnd = hwnd
        _round_window_corners(hwnd)
        # Стартуем сразу в overlay-режиме — применяем layered transparency
        if api.compact_mode:
            _apply_layered_transparency(hwnd, True, api._alpha_byte())
            # Сообщаем JS, что мы в compact (на всякий случай — body class уже есть)
            try:
                api._window.evaluate_js("document.body.classList.add('compact')")
            except Exception:
                pass
            # Если включён авто-акцепт — сразу запускаем сканер
            if api.auto_accept_enabled:
                api.start()
        print(f"[OK] HWND: {hwnd}")
    else:
        print("[WARN] HWND not found")


# ═══════════════════════════════════════════════
#  ЗАПУСК
# ═══════════════════════════════════════════════
if __name__ == '__main__':
    api = Api()
    
    html_path = _resource_path(os.path.join('ui', 'index.html'))
    if not os.path.exists(html_path):
        print(f"File not found: {html_path}")
        exit(1)
        
    # Стартуем в compact-overlay режиме (540×72)
    window = webview.create_window(
        'DoVay',
        url=f'file:///{html_path}',
        js_api=api,
        width=540,
        height=72,
        min_size=(320, 60),
        frameless=True,
        easy_drag=False,
        resizable=True,
        on_top=True,
        transparent=False,
        background_color='#060609'
    )
    api.set_window(window)
    webview.start(func=on_started, args=(api,))
