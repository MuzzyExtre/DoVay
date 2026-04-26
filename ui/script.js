document.addEventListener('DOMContentLoaded', () => {
    // ═══════════════════════════════════════════
    //  Элементы — overlay
    // ═══════════════════════════════════════════
    const mainSwitch = document.getElementById('main-switch');
    const compactLabel = document.getElementById('compact-label');
    const compactMsg = document.getElementById('compact-msg');
    const statWins = document.getElementById('stat-wins');
    const statLosses = document.getElementById('stat-losses');
    const statLossCell = document.getElementById('stat-loss-cell');
    const btnAddWin = document.getElementById('btn-add-win');
    const btnAddLoss = document.getElementById('btn-add-loss');
    const sessionTimer = document.getElementById('session-timer');
    const ovAlert = document.getElementById('ov-alert');
    const ovAlertText = document.getElementById('ov-alert-text');
    const ovAlertDismiss = document.getElementById('ov-alert-dismiss');
    const btnCompactLock = document.getElementById('btn-compact-lock');
    const btnCompactExpand = document.getElementById('btn-compact-expand');
    const btnCompactClose = document.getElementById('btn-compact-close');

    // ═══════════════════════════════════════════
    //  Элементы — settings (full view)
    // ═══════════════════════════════════════════
    const btnMin = document.getElementById('btn-min');
    const btnCollapse = document.getElementById('btn-collapse');
    const btnClose = document.getElementById('btn-close');
    const fullWins = document.getElementById('full-wins');
    const fullLosses = document.getElementById('full-losses');
    const fullStreak = document.getElementById('full-streak');
    const fullLossCard = document.getElementById('full-loss-card');
    const fullTimer = document.getElementById('full-timer');
    const panelDate = document.getElementById('panel-date');
    const btnMarkWin = document.getElementById('btn-mark-win');
    const btnMarkLoss = document.getElementById('btn-mark-loss');
    const btnResetSession = document.getElementById('btn-reset-session');
    const streakSlider = document.getElementById('streak-slider');
    const streakValue = document.getElementById('streak-value');
    const lateSlider = document.getElementById('late-slider');
    const lateValue = document.getElementById('late-value');
    const autoAcceptSwitch = document.getElementById('auto-accept-switch');
    const alphaSlider = document.getElementById('alpha-slider');
    const alphaValue = document.getElementById('alpha-value');
    const logList = document.getElementById('log-list');
    const logCount = document.getElementById('log-count');
    const resizeHandle = document.getElementById('resize-handle');

    // ═══════════════════════════════════════════
    //  Состояние
    // ═══════════════════════════════════════════
    let isActive = false;          // авто-акцепт сканер ON/OFF (визуально)
    let autoAcceptEnabled = true;  // global enable из настроек
    let isDragging = false;
    let isResizing = false;
    let isLocked = false;
    let events = [];

    let sessionStartTs = Date.now() / 1000;
    let serverNowTs = Date.now() / 1000;
    let serverSyncedAt = Date.now() / 1000;

    // ═══════════════════════════════════════════
    //  ПЕРЕТАСКИВАНИЕ ОКНА
    // ═══════════════════════════════════════════
    function attachDrag(el) {
        el.addEventListener('mousedown', (e) => {
            if (e.target.closest('.no-drag')) return;
            if (e.button !== 0) return;
            if (isLocked) return;
            isDragging = true;
            if (window.pywebview && window.pywebview.api) {
                window.pywebview.api.start_drag(e.screenX, e.screenY);
            }
        });
    }
    document.querySelectorAll('.drag-region').forEach(attachDrag);
    document.addEventListener('mousemove', (e) => {
        if (isResizing) {
            if (window.pywebview && window.pywebview.api) {
                window.pywebview.api.do_resize(e.screenX, e.screenY);
            }
            return;
        }
        if (!isDragging) return;
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.do_drag(e.screenX, e.screenY);
        }
    });
    document.addEventListener('mouseup', () => {
        isDragging = false;
        isResizing = false;
    });

    // ═══════════════════════════════════════════
    //  RESIZE
    // ═══════════════════════════════════════════
    if (resizeHandle) {
        resizeHandle.addEventListener('mousedown', (e) => {
            if (e.button !== 0) return;
            isResizing = true;
            if (window.pywebview && window.pywebview.api) {
                window.pywebview.api.start_resize(e.screenX, e.screenY);
            }
            e.preventDefault();
            e.stopPropagation();
        });
    }

    // ═══════════════════════════════════════════
    //  LOCK
    // ═══════════════════════════════════════════
    function applyLockUI(locked) {
        isLocked = locked;
        if (btnCompactLock) {
            btnCompactLock.classList.toggle('locked', locked);
            btnCompactLock.title = locked ? 'Открепить позицию' : 'Закрепить позицию';
        }
    }
    function toggleLock() {
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.toggle_lock().then(applyLockUI);
        } else {
            applyLockUI(!isLocked);
        }
    }
    btnCompactLock && btnCompactLock.addEventListener('click', toggleLock);

    // ═══════════════════════════════════════════
    //  УПРАВЛЕНИЕ ОКНОМ
    // ═══════════════════════════════════════════
    btnMin && btnMin.addEventListener('click', () => {
        if (window.pywebview && window.pywebview.api) window.pywebview.api.minimize();
    });
    // Close в overlay = выход из приложения
    btnCompactClose && btnCompactClose.addEventListener('click', () => {
        if (window.pywebview && window.pywebview.api) window.pywebview.api.close();
    });
    // Close в settings = выход из приложения
    btnClose && btnClose.addEventListener('click', () => {
        if (window.pywebview && window.pywebview.api) window.pywebview.api.close();
    });
    // «В оверлей» = свернуть обратно в compact
    btnCollapse && btnCollapse.addEventListener('click', () => {
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.toggle_compact().then(setCompactBody);
        }
    });
    // Expand из overlay = открыть settings
    btnCompactExpand && btnCompactExpand.addEventListener('click', () => {
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.toggle_compact().then((compact) => {
                setCompactBody(compact);
                refreshSettings();
                refreshStats();
            });
        }
    });

    function setCompactBody(compact) {
        if (compact) document.body.classList.add('compact');
        else document.body.classList.remove('compact');
    }

    // ═══════════════════════════════════════════
    //  ГЛАВНЫЙ ПЕРЕКЛЮЧАТЕЛЬ авто-акцепта (радар)
    // ═══════════════════════════════════════════
    function setBodyState(state) {
        const compact = document.body.classList.contains('compact');
        const alertStreak = document.body.classList.contains('alert-streak');
        const alertLate = document.body.classList.contains('alert-late');
        document.body.className = state +
            (compact ? ' compact' : '') +
            (alertStreak ? ' alert-streak' : '') +
            (alertLate ? ' alert-late' : '');
    }

    mainSwitch && mainSwitch.addEventListener('click', () => {
        if (!autoAcceptEnabled) {
            // Авто-акцепт выключен в настройках — мигнуть алертом
            setOvLabel('ВЫКЛ', 'Включи авто-акцепт в настройках');
            return;
        }
        isActive = !isActive;
        if (isActive) {
            setBodyState('scanning');
            setOvLabel('СКАН', 'Поиск матча');
            if (window.pywebview && window.pywebview.api) window.pywebview.api.start();
        } else {
            setBodyState('');
            setOvLabel('ОЖИДАНИЕ', 'Авто-акцепт выкл');
            if (window.pywebview && window.pywebview.api) window.pywebview.api.stop();
        }
    });

    // Hotkey: Space
    document.addEventListener('keydown', (e) => {
        if (e.code === 'Space' && !e.repeat &&
            !(e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA')) {
            e.preventDefault();
            mainSwitch && mainSwitch.click();
        }
    });

    function setOvLabel(label, msg) {
        if (compactLabel) compactLabel.textContent = label;
        if (compactMsg) compactMsg.textContent = msg || '';
    }

    // ═══════════════════════════════════════════
    //  W/L отметки
    // ═══════════════════════════════════════════
    function bumpStat(el) {
        if (!el) return;
        el.classList.remove('bumped');
        void el.offsetWidth;
        el.classList.add('bumped');
        setTimeout(() => el.classList.remove('bumped'), 600);
    }

    function applyStats(stats) {
        if (!stats) return;
        if (typeof stats.session_start_ts === 'number') {
            sessionStartTs = stats.session_start_ts;
        }
        if (typeof stats.now_ts === 'number') {
            serverNowTs = stats.now_ts;
            serverSyncedAt = Date.now() / 1000;
        }
        statWins.textContent = stats.wins;
        statLosses.textContent = stats.losses;
        if (fullWins) fullWins.textContent = stats.wins;
        if (fullLosses) fullLosses.textContent = stats.losses;
        if (fullStreak) {
            if (stats.loss_streak > 0) {
                fullStreak.hidden = false;
                fullStreak.querySelector('b').textContent = stats.loss_streak;
            } else {
                fullStreak.hidden = true;
            }
        }
        if (panelDate) panelDate.textContent = stats.date || '';
        applyAlerts(stats);
        updateTimer();
    }

    function applyAlerts(stats) {
        document.body.classList.toggle('alert-streak', !!stats.streak_alert);
        document.body.classList.toggle('alert-late', !stats.streak_alert && !!stats.late_alert);
        if (stats.streak_alert) {
            ovAlertText.textContent = `${stats.loss_streak} ПОРАЖЕНИЙ ПОДРЯД`;
        } else if (stats.late_alert) {
            ovAlertText.textContent = 'ПОЗДНО — ИДИ СПАТЬ';
        }
    }

    btnAddWin && btnAddWin.addEventListener('click', () => {
        if (!window.pywebview || !window.pywebview.api) return;
        window.pywebview.api.add_win().then((s) => {
            applyStats(s);
            bumpStat(document.querySelector('.ov-stat.win'));
        });
    });
    btnAddLoss && btnAddLoss.addEventListener('click', () => {
        if (!window.pywebview || !window.pywebview.api) return;
        window.pywebview.api.add_loss().then((s) => {
            applyStats(s);
            bumpStat(statLossCell);
        });
    });
    btnMarkWin && btnMarkWin.addEventListener('click', () => btnAddWin && btnAddWin.click());
    btnMarkLoss && btnMarkLoss.addEventListener('click', () => btnAddLoss && btnAddLoss.click());
    btnResetSession && btnResetSession.addEventListener('click', () => {
        if (!window.pywebview || !window.pywebview.api) return;
        window.pywebview.api.reset_session().then(applyStats);
    });

    ovAlertDismiss && ovAlertDismiss.addEventListener('click', () => {
        // Если активен late — диссмиссим его. Если streak — он уйдёт сам после +W
        if (document.body.classList.contains('alert-late') && window.pywebview && window.pywebview.api) {
            window.pywebview.api.dismiss_late_alert().then(applyStats);
        } else if (document.body.classList.contains('alert-streak')) {
            // Снимаем визуально (до следующего +L)
            document.body.classList.remove('alert-streak');
        }
    });

    // ═══════════════════════════════════════════
    //  Таймер сессии (локальный)
    // ═══════════════════════════════════════════
    function updateTimer() {
        const elapsedSinceSync = (Date.now() / 1000) - serverSyncedAt;
        const nowEffective = serverNowTs + elapsedSinceSync;
        const secs = Math.max(0, Math.floor(nowEffective - sessionStartTs));
        const h = Math.floor(secs / 3600);
        const m = Math.floor((secs % 3600) / 60);
        const s = secs % 60;
        const text = (h > 0)
            ? `${h}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`
            : `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
        if (sessionTimer) sessionTimer.textContent = text;
        if (fullTimer) fullTimer.textContent = text;
    }
    setInterval(updateTimer, 1000);

    // ═══════════════════════════════════════════
    //  Поллинг статов (для авто-обновления late-alert)
    // ═══════════════════════════════════════════
    function refreshStats() {
        if (!window.pywebview || !window.pywebview.api) return;
        window.pywebview.api.get_stats().then(applyStats).catch(() => {});
    }
    setInterval(refreshStats, 5000);

    // ═══════════════════════════════════════════
    //  Настройки — слайдеры и переключатели
    // ═══════════════════════════════════════════
    function fmtLate(h) {
        h = parseInt(h, 10);
        if (!h) return 'выкл';
        const realH = h % 24;
        return `${String(realH).padStart(2,'0')}:00${h >= 24 ? ' (+1)' : ''}`;
    }

    function refreshSettings() {
        if (!window.pywebview || !window.pywebview.api) return;
        window.pywebview.api.get_settings().then((s) => {
            if (!s) return;
            autoAcceptEnabled = !!s.auto_accept_enabled;
            if (autoAcceptSwitch) autoAcceptSwitch.setAttribute('aria-checked', autoAcceptEnabled ? 'true' : 'false');
            if (streakSlider) {
                streakSlider.value = s.loss_streak_limit;
                streakValue.textContent = s.loss_streak_limit > 0 ? s.loss_streak_limit : 'выкл';
            }
            if (lateSlider) {
                lateSlider.value = s.late_hour;
                lateValue.textContent = fmtLate(s.late_hour);
            }
            if (alphaSlider) {
                alphaSlider.value = s.overlay_alpha_pct;
                alphaValue.textContent = s.overlay_alpha_pct + '%';
            }
        }).catch(() => {});
    }

    streakSlider && streakSlider.addEventListener('input', () => {
        const n = parseInt(streakSlider.value, 10);
        streakValue.textContent = n > 0 ? n : 'выкл';
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.set_loss_streak_limit(n).then(refreshStats);
        }
    });

    lateSlider && lateSlider.addEventListener('input', () => {
        const h = parseInt(lateSlider.value, 10);
        lateValue.textContent = fmtLate(h);
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.set_late_hour(h).then(refreshStats);
        }
    });

    autoAcceptSwitch && autoAcceptSwitch.addEventListener('click', () => {
        const next = autoAcceptSwitch.getAttribute('aria-checked') !== 'true';
        autoAcceptSwitch.setAttribute('aria-checked', next ? 'true' : 'false');
        autoAcceptEnabled = next;
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.set_auto_accept_enabled(next).then((v) => {
                autoAcceptEnabled = !!v;
                autoAcceptSwitch.setAttribute('aria-checked', v ? 'true' : 'false');
                if (!v && isActive) {
                    isActive = false;
                    setBodyState('');
                    setOvLabel('ВЫКЛ', 'Авто-акцепт отключён');
                }
            });
        }
    });

    alphaSlider && alphaSlider.addEventListener('input', () => {
        const pct = parseInt(alphaSlider.value, 10);
        alphaValue.textContent = pct + '%';
        if (window.pywebview && window.pywebview.api && window.pywebview.api.set_overlay_alpha) {
            window.pywebview.api.set_overlay_alpha(pct);
        }
    });

    // ═══════════════════════════════════════════
    //  API для Python (push)
    // ═══════════════════════════════════════════
    const STATUS_LABELS = {
        'idle': 'ОЖИДАНИЕ',
        'scanning': 'СКАН',
        'match_found': 'МАТЧ',
        'accepted': 'ПРИНЯТ'
    };

    window.updateStatusFromPython = (status, message) => {
        setBodyState(status === 'idle' ? '' : status);
        setOvLabel(STATUS_LABELS[status] || status.toUpperCase(), message || '');
        if (status === 'scanning') isActive = true;
        if (status === 'idle') isActive = false;
    };

    window.addEventFromPython = (eventData) => {
        events.unshift(eventData);
        if (events.length > 30) events.pop();
        renderEvents();
    };

    function renderEvents() {
        if (!logList) return;
        if (events.length === 0) {
            logList.innerHTML = '<div class="empty-log"><span>журнал пуст</span></div>';
            if (logCount) logCount.textContent = '0';
            return;
        }
        if (logCount) logCount.textContent = String(events.length).padStart(2, '0');

        logList.innerHTML = '';
        events.forEach((ev, i) => {
            const isNewest = i === 0;
            const type = ev.type || 'info';
            const item = document.createElement('div');
            item.className = `log-item ${isNewest ? 'newest' : ''} ${type}`;
            item.innerHTML = `
                <div class="log-time">${ev.timestamp}</div>
                <div class="log-msg">${escapeHtml(ev.message)}</div>
            `;
            logList.appendChild(item);
        });
    }

    function escapeHtml(s) {
        const div = document.createElement('div');
        div.textContent = String(s);
        return div.innerHTML;
    }

    // ═══════════════════════════════════════════
    //  Старт
    // ═══════════════════════════════════════════
    setBodyState('');
    setOvLabel('ОЖИДАНИЕ', 'Готов');

    // Pywebview API готов с задержкой — дождёмся события
    function init() {
        refreshSettings();
        refreshStats();
    }
    if (window.pywebview && window.pywebview.api) {
        init();
    } else {
        window.addEventListener('pywebviewready', init);
        // fallback — если события нет, попробуем через 600мс
        setTimeout(() => {
            if (window.pywebview && window.pywebview.api) init();
        }, 600);
    }
});
