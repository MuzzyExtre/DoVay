document.addEventListener('DOMContentLoaded', () => {
    const btnMin = document.getElementById('btn-min');
    const btnClose = document.getElementById('btn-close');
    const btnOverlay = document.getElementById('btn-overlay');
    const mainSwitch = document.getElementById('main-switch');
    const toggleLabel = document.getElementById('toggle-label');
    const statusLabel = document.getElementById('status-label');
    const statusMessage = document.getElementById('status-message');
    const logList = document.getElementById('log-list');
    const header = document.querySelector('header');

    let isActive = false;
    let events = [];
    let isDragging = false;

    // ═══════════════════════════════════════════
    //  ПЕРЕТАСКИВАНИЕ ОКНА (через screen coordinates)
    // ═══════════════════════════════════════════
    header.addEventListener('mousedown', (e) => {
        if (e.target.closest('.no-drag')) return;
        if (e.button !== 0) return;
        isDragging = true;
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.start_drag(e.screenX, e.screenY);
        }
    });

    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.do_drag(e.screenX, e.screenY);
        }
    });

    document.addEventListener('mouseup', () => {
        isDragging = false;
    });

    // ═══════════════════════════════════════════
    //  УПРАВЛЕНИЕ ОКНОМ
    // ═══════════════════════════════════════════
    btnMin.addEventListener('click', () => {
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.minimize();
        }
    });

    btnClose.addEventListener('click', () => {
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.close();
        }
    });

    // ═══════════════════════════════════════════
    //  ОВЕРЛЕЙ (поверх всех окон)
    // ═══════════════════════════════════════════
    btnOverlay.addEventListener('click', () => {
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.toggle_overlay().then((isOverlay) => {
                if (isOverlay) {
                    btnOverlay.classList.add('active');
                    btnOverlay.title = 'Оверлей: ВКЛ';
                } else {
                    btnOverlay.classList.remove('active');
                    btnOverlay.title = 'Оверлей: ВЫКЛ';
                }
            });
        }
    });

    // ═══════════════════════════════════════════
    //  ГЛАВНЫЙ ПЕРЕКЛЮЧАТЕЛЬ
    // ═══════════════════════════════════════════
    mainSwitch.addEventListener('click', () => {
        isActive = !isActive;
        
        if (isActive) {
            document.body.className = 'scanning';
            toggleLabel.textContent = 'АВТОПРИНЯТИЕ ВКЛЮЧЕНО';
            if (window.pywebview && window.pywebview.api) {
                window.pywebview.api.start();
            }
        } else {
            document.body.className = '';
            toggleLabel.textContent = 'АКТИВИРОВАТЬ СКАНИРОВАНИЕ';
            statusLabel.textContent = 'ОЖИДАНИЕ';
            statusMessage.textContent = 'Система выключена';
            if (window.pywebview && window.pywebview.api) {
                window.pywebview.api.stop();
            }
        }
    });

    // ═══════════════════════════════════════════
    //  API для Python
    // ═══════════════════════════════════════════
    window.updateStatusFromPython = (status, message) => {
        document.body.className = status;
        
        const labels = {
            'idle': 'ОЖИДАНИЕ',
            'scanning': 'ПОИСК СЕССИИ',
            'match_found': 'МАТЧ НАЙДЕН',
            'accepted': 'ПРИНЯТО'
        };
        
        statusLabel.textContent = labels[status] || status.toUpperCase();
        statusMessage.textContent = message;
    };

    window.addEventFromPython = (eventData) => {
        events.unshift(eventData);
        if (events.length > 20) events.pop();
        renderEvents();
    };

    function renderEvents() {
        if (events.length === 0) {
            logList.innerHTML = '<div class="empty-log">Журнал пуст</div>';
            return;
        }

        logList.innerHTML = '';
        const colors = {
            'info': 'var(--color-text-mid)',
            'success': 'var(--color-success)',
            'error': 'var(--color-scan)'
        };

        events.forEach((ev, i) => {
            const isNewest = i === 0;
            const c = colors[ev.type] || colors['info'];
            
            const item = document.createElement('div');
            item.className = `log-item ${isNewest ? 'newest' : ''}`;
            
            item.innerHTML = `
                <div class="log-dot" style="background: ${c}; box-shadow: ${isNewest ? `0 0 8px ${c}` : 'none'}"></div>
                <div class="log-time">${ev.timestamp}</div>
                <div class="log-msg" style="color: ${isNewest ? 'var(--color-text-high)' : ''}">${ev.message}</div>
            `;
            
            logList.appendChild(item);
        });
    }

    // Initial state
    document.body.className = '';
});
