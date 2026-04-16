"""Находит кнопку Accept по белому тексту 'ПРИНЯТЬ' внутри teal области."""
import cv2
import numpy as np

src = cv2.imread('photo_2026-04-14_23-32-12.jpg')
h, w = src.shape[:2]
print(f'Source: {w}x{h}')

# Шаг 1: маска белого текста (понижен порог из-за JPG)
gray = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
white = (gray > 180).astype(np.uint8) * 255

# Шаг 2: ограничиваем поиск центральной областью
mask = np.zeros_like(white)
mask[h//3:2*h//3, w//3:2*w//3] = 255
white_center = cv2.bitwise_and(white, mask)

# Шаг 3: находим связные компоненты текста
num, labels, stats, _ = cv2.connectedComponentsWithStats(white_center, 8)

# Шаг 4: фильтруем — буквы текста ПРИНЯТЬ небольшие, но их много в одной горизонтальной полосе
candidates = []
for i in range(1, num):
    x, y, cw, ch, area = stats[i]
    if 5 < cw < 80 and 15 < ch < 80 and area > 30:
        candidates.append((x, y, cw, ch))

print(f'Letter candidates: {len(candidates)}')
if not candidates:
    raise SystemExit('Текст не найден')

# Группируем буквы по строкам (близкие y)
candidates.sort(key=lambda c: c[1])
groups = []
cur_group = [candidates[0]]
for c in candidates[1:]:
    if abs(c[1] - cur_group[-1][1]) < 30:
        cur_group.append(c)
    else:
        groups.append(cur_group)
        cur_group = [c]
groups.append(cur_group)

# Самая нижняя группа из >=4 букв — кнопка ПРИНЯТЬ всегда внизу диалога
big_groups = [g for g in groups if len(g) >= 4]
print(f'Groups: {[(len(g), g[0][1]) for g in big_groups]}')
best = max(big_groups, key=lambda g: g[0][1])
print(f'Best (lowest) group has {len(best)} letters at y={best[0][1]}')

xs = [c[0] for c in best] + [c[0] + c[2] for c in best]
ys = [c[1] for c in best] + [c[1] + c[3] for c in best]
tx1, tx2 = min(xs), max(xs)
ty1, ty2 = min(ys), max(ys)
print(f'Text bbox: ({tx1},{ty1}) — ({tx2},{ty2})')

# Расширяем чтобы захватить ВСЮ кнопку (фон, рамка), а не только текст
pad_x = (tx2 - tx1) // 4
pad_y = (ty2 - ty1) // 1
x1 = max(0, tx1 - pad_x)
x2 = min(w, tx2 + pad_x)
y1 = max(0, ty1 - pad_y)
y2 = min(h, ty2 + pad_y)
print(f'Button bbox: ({x1},{y1}) — ({x2},{y2}) size {x2-x1}x{y2-y1}')

button = src[y1:y2, x1:x2]
cv2.imwrite('templates/accept_button.png', button)

preview = src.copy()
cv2.rectangle(preview, (x1, y1), (x2, y2), (0, 0, 255), 3)
cv2.rectangle(preview, (tx1, ty1), (tx2, ty2), (0, 255, 0), 2)
cv2.imwrite('templates/_preview_crop.png', preview)
print('OK')
