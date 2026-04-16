# DoVay

Автоматический приём матчей в Dota 2. Сканирует экран, находит зелёную кнопку «Accept» и нажимает за вас.

## Как работает

1. Захват центральной области экрана через **mss** (~3 FPS)
2. Пиксельный анализ через **numpy** — ищет зелёный паттерн кнопки Accept
3. Двойное подтверждение (2 кадра подряд) для исключения ложных срабатываний
4. Аппаратный клик через **SendInput** (Win32 API) — работает даже в полноэкранном режиме

## Стек

| Слой | Технология |
|------|-----------|
| UI | HTML / CSS / JS (pywebview) |
| Backend | Python 3.10+ |
| Захват экрана | mss + numpy |
| Клик | ctypes / SendInput |
| Шрифты | Sora, IBM Plex Mono |

## Установка

```bash
# Клонировать
git clone https://github.com/MuzzyExtre/DoVay.git
cd DoVay

# Виртуальное окружение
python -m venv .venv
.venv\Scripts\activate

# Зависимости
pip install -r requirements.txt
```

## Запуск

```bash
python main.py
```

## Интерфейс

- **Переключатель** — запуск / остановка сканирования
- **Радар** — визуализация состояния (idle → scanning → match found → accepted)
- **Журнал событий** — лог всех действий
- **Оверлей** — окно поверх всех (кнопка 📌 в шапке)
- **Перетаскивание** — за шапку окна

## Структура

```
DoVay/
├── main.py              # Точка входа, backend, сканер
├── requirements.txt     # Python-зависимости
├── ui/
│   ├── index.html       # Разметка
│   ├── style.css        # Стили + анимации
│   └── script.js        # Логика UI, мост к Python API
└── dovay/               # Модули (theme, scanner, window и др.)
```

## Лицензия

MIT
