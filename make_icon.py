"""Genera l'icona di Census ERP: C stilizzata + codice a barre su gradiente blu.

Output: icon.png (1024), icon_512.png, icon_256.png, icon.ico (multi-size), icon.icns (Mac).
"""
import math
from PIL import Image, ImageDraw, ImageFilter, ImageOps

S = 1024          # dimensione finale
F = 4             # supersampling per l'antialiasing
W = S * F

C_TOP = (104, 152, 255)    # blu acceso in alto
C_BOT = (24, 33, 96)       # indaco profondo in basso
WHITE = (255, 255, 255, 255)


def _radial_highlight(size, center, radius, color):
    """Crea un alone radiale morbido (per il riflesso 'vetro')."""
    layer = Image.new('L', (size, size), 0)
    d = ImageDraw.Draw(layer)
    cx, cy = center
    d.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=255)
    layer = layer.filter(ImageFilter.GaussianBlur(radius * 0.55))
    out = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    solid = Image.new('RGBA', (size, size), color)
    out.paste(solid, (0, 0), layer)
    return out


def build():
    radius = int(W * 0.235)

    # --- Sfondo: squircle con gradiente verticale ---
    grad = Image.linear_gradient('L').resize((W, W))
    bg_rgb = ImageOps.colorize(grad, black=C_TOP, white=C_BOT).convert('RGBA')

    mask = Image.new('L', (W, W), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, W - 1, W - 1), radius=radius, fill=255)

    img = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    img.paste(bg_rgb, (0, 0), mask)

    def clip(layer):
        """Ritaglia un layer alla forma dello squircle."""
        return Image.composite(layer, Image.new('RGBA', (W, W), (0, 0, 0, 0)), mask)

    # Riflesso 'vetro' diagonale in alto a sinistra
    img = Image.alpha_composite(img, clip(
        _radial_highlight(W, (W * 0.30, W * 0.20), W * 0.42, (255, 255, 255, 46))))
    # Vignettatura scura in basso a destra per dare profondità
    img = Image.alpha_composite(img, clip(
        _radial_highlight(W, (W * 0.86, W * 0.92), W * 0.50, (8, 12, 44, 70))))

    # Bordo interno luminoso (effetto bevel)
    ring = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    ImageDraw.Draw(ring).rounded_rectangle(
        (int(W * 0.012), int(W * 0.012), int(W - W * 0.012), int(W - W * 0.012)),
        radius=int(radius * 0.96), outline=(255, 255, 255, 60), width=int(W * 0.006))
    img = Image.alpha_composite(img, clip(ring))

    # --- Motivo: C aperta + codice a barre realistico ---
    cx, cy = W * 0.415, W * 0.50
    stroke = W * 0.122
    r_mid = W * 0.225
    a1, a2 = 38, 322  # apertura della C verso destra

    def draw_arc(color, off=(0, 0), width_scale=1.0):
        layer = Image.new('RGBA', (W, W), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        sw = stroke * width_scale
        r_out = r_mid + sw / 2
        ox, oy = off
        box = (cx - r_out + ox, cy - r_out + oy, cx + r_out + ox, cy + r_out + oy)
        d.arc(box, start=a1, end=a2, fill=color, width=int(sw))
        for a in (a1, a2):
            rad = math.radians(a)
            px, py = cx + r_mid * math.cos(rad) + ox, cy + r_mid * math.sin(rad) + oy
            d.ellipse((px - sw / 2, py - sw / 2, px + sw / 2, py + sw / 2), fill=color)
        return layer

    def draw_bars(color, off=(0, 0)):
        layer = Image.new('RGBA', (W, W), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        ox, oy = off
        x = W * 0.595
        # (larghezza, altezza relativa) — barre di altezze diverse come un vero barcode
        bars = [(0.022, 1.00), (0.050, 0.78), (0.020, 1.00),
                (0.030, 0.62), (0.020, 1.00), (0.044, 0.84)]
        base_h = W * 0.150
        for bw, hf in bars:
            bw_px = W * bw
            h = base_h * hf
            d.rounded_rectangle((x + ox, cy - h + oy, x + bw_px + ox, cy + h + oy),
                                radius=bw_px / 2, fill=color)
            x += bw_px + W * 0.022
        return layer

    # Ombra portata del motivo
    shadow = Image.alpha_composite(
        draw_arc((6, 10, 40, 120), off=(W * 0.006, W * 0.014)),
        draw_bars((6, 10, 40, 120), off=(W * 0.006, W * 0.014)))
    img = Image.alpha_composite(img, clip(shadow.filter(ImageFilter.GaussianBlur(W * 0.014))))

    # Motivo bianco con leggero gradiente (più luminoso in alto)
    motif = Image.alpha_composite(draw_arc(WHITE), draw_bars(WHITE))
    shade = Image.linear_gradient('L').resize((W, W)).point(lambda v: 255 - int(v * 0.16))
    motif_rgb = motif.copy()
    motif_rgb.putalpha(Image.composite(motif.getchannel('A'),
                                       Image.new('L', (W, W), 0), motif.getchannel('A')))
    tint = ImageOps.colorize(shade, black=(214, 226, 255), white=WHITE[:3]).convert('RGBA')
    tinted = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    tinted.paste(tint, (0, 0), motif.getchannel('A'))
    img = Image.alpha_composite(img, tinted)

    return img.resize((S, S), Image.LANCZOS)


if __name__ == '__main__':
    icon = build()
    icon.save('icon.png')
    icon.resize((512, 512), Image.LANCZOS).save('icon_512.png')
    icon.resize((256, 256), Image.LANCZOS).save('icon_256.png')
    icon.save('icon.ico', sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (24, 24), (16, 16)])
    try:
        icon.save('icon.icns')
        print('icon.icns OK')
    except Exception as e:
        print('icns non generato (verra creato da PyInstaller su Mac):', e)
    print('Icone generate: icon.png / icon_512.png / icon_256.png / icon.ico')
