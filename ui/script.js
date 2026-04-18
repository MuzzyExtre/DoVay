document.addEventListener('DOMContentLoaded', () => {
    const btnMin = document.getElementById('btn-min');
    const btnClose = document.getElementById('btn-close');
    const btnOverlay = document.getElementById('btn-overlay');
    const btnLock = document.getElementById('btn-lock');
    const btnCompactLock = document.getElementById('btn-compact-lock');
    const resizeHandle = document.getElementById('resize-handle');
    const mainSwitch = document.getElementById('main-switch');
    const toggleLabel = document.getElementById('toggle-label');
    const statusLabel = document.getElementById('status-label');
    const statusMessage = document.getElementById('status-message');
    const logList = document.getElementById('log-list');
    const logCount = document.getElementById('log-count');
    // Компактный режим
    const compactLabel = document.getElementById('compact-label');
    const compactMsg = document.getElementById('compact-msg');
    const btnCompactToggle = document.getElementById('btn-compact-toggle');
    const btnCompactExpand = document.getElementById('btn-compact-expand');
    const btnCompactClose = document.getElementById('btn-compact-close');
    const btnCompactSettings = document.getElementById('btn-compact-settings');
    // Настройки
    const btnSettings = document.getElementById('btn-settings');
    const btnSettingsClose = document.getElementById('btn-settings-close');
    const settingsModal = document.getElementById('settings-modal');
    const alphaSlider = document.getElementById('alpha-slider');
    const alphaValue = document.getElementById('alpha-value');

    let isActive = false;
    let isDragging = false;
    let isResizing = false;
    let isCompact = false;
    let isLocked = false;
    let events = [];
    let currentStatus = 'idle';

    // ═══════════════════════════════════════════
    //  ПЕРЕТАСКИВАНИЕ ОКНА (header + compact-bar)
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
    //  RESIZE — кастомный handle (frameless окно)
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
    //  LOCK — закрепить позицию
    // ═══════════════════════════════════════════
    function applyLockUI(locked) {
        isLocked = locked;
        if (locked) {
            btnLock && btnLock.classList.add('locked');
            btnCompactLock && btnCompactLock.classList.add('locked');
            btnLock && (btnLock.title = 'Открепить позицию');
            btnCompactLock && (btnCompactLock.title = 'Открепить позицию');
        } else {
            btnLock && btnLock.classList.remove('locked');
            btnCompactLock && btnCompactLock.classList.remove('locked');
            btnLock && (btnLock.title = 'Закрепить позицию');
            btnCompactLock && (btnCompactLock.title = 'Закрепить позицию');
        }
    }
    function toggleLock() {
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.toggle_lock().then(applyLockUI);
        } else {
            applyLockUI(!isLocked);
        }
    }
    btnLock && btnLock.addEventListener('click', toggleLock);
    btnCompactLock && btnCompactLock.addEventListener('click', toggleLock);

    // ═══════════════════════════════════════════
    //  УПРАВЛЕНИЕ ОКНОМ
    // ═══════════════════════════════════════════
    btnMin.addEventListener('click', () => {
        if (window.pywebview && window.pywebview.api) window.pywebview.api.minimize();
    });
    btnClose.addEventListener('click', () => {
        if (window.pywebview && window.pywebview.api) window.pywebview.api.close();
    });
    btnCompactClose.addEventListener('click', () => {
        if (window.pywebview && window.pywebview.api) window.pywebview.api.close();
    });

    // ═══════════════════════════════════════════
    //  КОМПАКТНЫЙ РЕЖИМ
    // ═══════════════════════════════════════════
    function setCompact(on) {
        isCompact = on;
        if (on) document.body.classList.add('compact');
        else document.body.classList.remove('compact');
    }
    btnOverlay.addEventListener('click', () => {
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.toggle_compact().then((compact) => setCompact(compact));
        } else {
            setCompact(!isCompact);
        }
    });
    btnCompactExpand.addEventListener('click', () => {
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.toggle_compact().then((compact) => setCompact(compact));
        }
    });

    // Старт/стоп из компактного режима
    btnCompactToggle.addEventListener('click', () => mainSwitch.click());

    // ═══════════════════════════════════════════
    //  ГЛАВНЫЙ ПЕРЕКЛЮЧАТЕЛЬ
    // ═══════════════════════════════════════════
    function setBodyState(state) {
        currentStatus = state;
        const compact = document.body.classList.contains('compact');
        document.body.className = state + (compact ? ' compact' : '');
    }

    mainSwitch.addEventListener('click', () => {
        // Ripple-эффект — снимаем класс и навешиваем заново для перезапуска анимации
        mainSwitch.classList.remove('clicked');
        // forced reflow, чтобы анимация всегда стартовала заново
        void mainSwitch.offsetWidth;
        mainSwitch.classList.add('clicked');

        isActive = !isActive;
        if (isActive) {
            setBodyState('scanning');
            toggleLabel.textContent = 'ОСТАНОВИТЬ';
            mainSwitch.setAttribute('aria-label', 'Остановить сканирование');
            compactLabel.textContent = 'СКАНИРОВАНИЕ';
            compactMsg.textContent = 'Поиск матча...';
            if (window.pywebview && window.pywebview.api) window.pywebview.api.start();
        } else {
            setBodyState('');
            toggleLabel.textContent = 'ВКЛЮЧИТЬ';
            mainSwitch.setAttribute('aria-label', 'Запустить сканирование');
            statusLabel.textContent = 'ОЖИДАНИЕ';
            statusMessage.textContent = 'Система выключена';
            compactLabel.textContent = 'ОЖИДАНИЕ';
            compactMsg.textContent = 'Выключено';
            if (window.pywebview && window.pywebview.api) window.pywebview.api.stop();
        }
    });

    // Hotkey: Space
    document.addEventListener('keydown', (e) => {
        if (e.code === 'Space' && !e.repeat) {
            e.preventDefault();
            mainSwitch.click();
        }
    });

    // ═══════════════════════════════════════════
    //  API для Python
    // ═══════════════════════════════════════════
    const chSysText = document.querySelector('#ch-system .ch-sys-text');

    window.updateStatusFromPython = (status, message) => {
        setBodyState(status);
        const labels = {
            'idle': 'ОЖИДАНИЕ',
            'scanning': 'ПОИСК СЕССИИ',
            'match_found': 'МАТЧ НАЙДЕН',
            'accepted': 'ПРИНЯТО'
        };
        const sysLabels = {
            'idle': 'STANDBY',
            'scanning': 'ACTIVE',
            'match_found': 'TARGET LOCK',
            'accepted': 'CONFIRMED'
        };
        const text = labels[status] || status.toUpperCase();
        statusLabel.textContent = text;
        statusMessage.textContent = message;
        compactLabel.textContent = text;
        compactMsg.textContent = message;
        if (chSysText) chSysText.textContent = sysLabels[status] || status.toUpperCase();
    };

    window.addEventFromPython = (eventData) => {
        events.unshift(eventData);
        if (events.length > 30) events.pop();
        renderEvents();
    };

    const ICONS = {
        info: '<svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><circle cx="6" cy="6" r="4.5"/><line x1="6" y1="5" x2="6" y2="8.5"/><circle cx="6" cy="3.4" r="0.5" fill="currentColor"/></svg>',
        success: '<svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M2.5 6L5 8.5L9.5 3.5"/></svg>',
        error: '<svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><line x1="3.5" y1="3.5" x2="8.5" y2="8.5"/><line x1="8.5" y1="3.5" x2="3.5" y2="8.5"/></svg>'
    };

    function renderEvents() {
        if (events.length === 0) {
            logList.innerHTML = `
                <div class="empty-log">
                    <div class="empty-icon"><span></span></div>
                    <span>Журнал пуст</span>
                </div>`;
            logCount.textContent = '0';
            return;
        }
        logCount.textContent = String(events.length).padStart(2, '0');

        logList.innerHTML = '';
        events.forEach((ev, i) => {
            const isNewest = i === 0;
            const type = ev.type || 'info';
            const icon = ICONS[type] || ICONS.info;

            const item = document.createElement('div');
            item.className = `log-item ${isNewest ? 'newest' : ''} ${type}`;
            item.innerHTML = `
                <div class="log-icon">${icon}</div>
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

    setBodyState('');

    // ═══════════════════════════════════════════
    //  НАСТРОЙКИ — модалка с прозрачностью оверлея
    // ═══════════════════════════════════════════
    function openSettings() {
        settingsModal.classList.add('open');
        if (window.pywebview && window.pywebview.api && window.pywebview.api.get_overlay_alpha) {
            window.pywebview.api.get_overlay_alpha().then((pct) => {
                if (typeof pct === 'number') {
                    alphaSlider.value = pct;
                    alphaValue.textContent = pct + '%';
                }
            });
        }
    }
    function closeSettings() { settingsModal.classList.remove('open'); }

    btnSettings && btnSettings.addEventListener('click', openSettings);
    btnCompactSettings && btnCompactSettings.addEventListener('click', () => {
        // Из compact-режима настройки открываются в полном виде
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.toggle_compact().then((compact) => {
                setCompact(compact);
                openSettings();
            });
        } else {
            openSettings();
        }
    });
    btnSettingsClose && btnSettingsClose.addEventListener('click', closeSettings);
    settingsModal && settingsModal.addEventListener('click', (e) => {
        if (e.target === settingsModal) closeSettings();
    });

    alphaSlider && alphaSlider.addEventListener('input', () => {
        const pct = parseInt(alphaSlider.value, 10);
        alphaValue.textContent = pct + '%';
        if (window.pywebview && window.pywebview.api && window.pywebview.api.set_overlay_alpha) {
            window.pywebview.api.set_overlay_alpha(pct);
        }
    });
});
