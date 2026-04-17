"""Генерация icon.ico для DoVay в стиле in-app логотипа.
Скруглённый тайл с диагональным градиентом cyan→violet→deep + буква D + cyan-точка."""
from PIL import Image, ImageDraw, ImageChops
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.ico')
SIZES = [16, 24, 32, 48, 64, 128, 256]


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


def make_icon(size):
    s = size
    pad = max(1, int(s * 0.04))
    radius = int(s * 0.26)

    # 1) Диагональный градиентный квадрат во всю площадь
    grad_top = (34, 227, 255)     # cyan
    grad_mid = (139, 92, 246)     # violet
    grad_bot = (60, 20, 130)      # deep purple

    grad = Image.new('RGB', (s, s), grad_mid)
    gpx = grad.load()
    for y in range(s):
        for x in range(s):
            t = (x + (s - 1 - y)) / (2 * (s - 1)) if s > 1 else 0
            if t < 0.55:
                col = lerp(grad_top, grad_mid, t / 0.55)
            else:
                col = lerp(grad_mid, grad_bot, (t - 0.55) / 0.45)
            gpx[x, y] = col

    # 2) Маска со скруглёнными углами
    tile_mask = Image.new('L', (s, s), 0)
    ImageDraw.Draw(tile_mask).rounded_rectangle(
        (pad, pad, s - 1 - pad, s - 1 - pad), radius=radius, fill=255)

    tile = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    tile.paste(grad, (0, 0))
    tile.putalpha(tile_mask)

    # 3) Глянцевый верхний блик (полупрозрачный белый, обрезанный маской тайла)
    shine = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shine)
    shine_h = int(s * 0.50)
    for y in range(shine_h):
        a = int(85 * (1 - y / shine_h))
        sdraw.line([(0, y), (s, y)], fill=(255, 255, 255, a))
    # Применяем маску тайла к блику
    shine_alpha = ImageChops.multiply(shine.split()[3], tile_mask)
    shine.putalpha(shine_alpha)
    tile = Image.alpha_composite(tile, shine)

    # 4) Буква D — белая, через композит двух слоёв (заливка минус вырез)
    d_layer = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    ddraw = ImageDraw.Draw(d_layer)

    # Размеры буквы
    margin_x = s * 0.30
    margin_y = s * 0.24
    L = margin_x
    R = s - margin_x * 0.85
    T = margin_y
    B = s - margin_y
    H = B - T
    bar_w = max(2, s * 0.085)

    # Внешний контур: прямоугольник + полукруг справа (белая заливка с alpha)
    outer_alpha = Image.new('L', (s, s), 0)
    odraw = ImageDraw.Draw(outer_alpha)
    flat_w = (R - L) - H / 2
    odraw.rectangle([L, T, L + flat_w, B], fill=255)
    odraw.pieslice([L + flat_w - H / 2, T, L + flat_w + H / 2, B],
                   start=-90, end=90, fill=255)

    # Внутренний вырез (вычитаем из outer)
    inner_alpha = Image.new('L', (s, s), 0)
    idraw = ImageDraw.Draw(inner_alpha)
    iL = L + bar_w
    iT = T + bar_w
    iB = B - bar_w
    iH = iB - iT
    i_flat_w = flat_w - bar_w
    if i_flat_w > 0 and iH > 0:
        idraw.rectangle([iL, iT, iL + i_flat_w, iB], fill=255)
        idraw.pieslice([iL + i_flat_w - iH / 2, iT, iL + i_flat_w + iH / 2, iB],
                       start=-90, end=90, fill=255)

    letter_alpha = ImageChops.subtract(outer_alpha, inner_alpha)
    d_layer = Image.new('RGBA', (s, s), (255, 255, 255, 0))
    d_layer.putalpha(letter_alpha)

    tile = Image.alpha_composite(tile, d_layer)

    # 5) Маленький cyan-акцент справа сверху
    if s >= 24:
        dot = Image.new('RGBA', (s, s), (0, 0, 0, 0))
        dot_draw = ImageDraw.Draw(dot)
        r = max(2, int(s * 0.08))
        cx = s - pad - r * 1.4
        cy = pad + r * 1.4
        dot_draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                         fill=(78, 225, 208, 255))
        tile = Image.alpha_composite(tile, dot)

    return tile


if __name__ == '__main__':
    frames = [make_icon(s) for s in SIZES]
    frames[-1].save(OUT, format='ICO',
                    sizes=[(s, s) for s in SIZES],
                    append_images=frames[:-1])
    # Превью самого большого
    frames[-1].save(os.path.join(os.path.dirname(OUT), '_icon_preview.png'))
    print(f'Saved {OUT}, sizes: {SIZES}')
