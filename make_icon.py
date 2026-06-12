"""Genera l'icona di Census ERP: C stilizzata + codice a barre su gradiente blu.

Output: icon.png (1024), icon_512.png, icon_256.png, icon.ico (multi-size), icon.icns (Mac).
"""
import math
from PIL import Image, ImageDraw, ImageFilter, ImageOps

S = 1024          # dimensione finale
F = 4             # supersampling per l'antialiasing
W = S * F

C_TOP = (95, 140, 255)     # blu chiaro in alto
C_BOT = (30, 41, 110)      # indaco profondo in basso
WHITE = (255, 255, 255, 255)


def build():
    # --- Sfondo: rounded-rect con gradiente verticale ---
    grad = Image.linear_gradient('L').resize((W, W))
    bg_rgb = ImageOps.colorize(grad, black=C_TOP, white=C_BOT).convert('RGBA')

    mask = Image.new('L', (W, W), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, W - 1, W - 1), radius=int(W * 0.225), fill=255)

    img = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    img.paste(bg_rgb, (0, 0), mask)

    # Riflesso morbido in alto a sinistra
    glow = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((-W * 0.35, -W * 0.45, W * 0.85, W * 0.45), fill=(255, 255, 255, 36))
    glow = glow.filter(ImageFilter.GaussianBlur(W * 0.06))
    img = Image.alpha_composite(img, Image.composite(glow, Image.new('RGBA', (W, W), (0, 0, 0, 0)), mask))

    # --- Motivo: C + codice a barre ---
    def draw_motif(color):
        layer = Image.new('RGBA', (W, W), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)

        cx, cy = W * 0.44, W * 0.50
        stroke = W * 0.115
        r_mid = W * 0.215
        r_out = r_mid + stroke / 2
        a1, a2 = 35, 325  # apertura della C verso destra

        d.arc((cx - r_out, cy - r_out, cx + r_out, cy + r_out),
              start=a1, end=a2, fill=color, width=int(stroke))
        # estremità arrotondate
        for a in (a1, a2):
            rad = math.radians(a)
            px, py = cx + r_mid * math.cos(rad), cy + r_mid * math.sin(rad)
            d.ellipse((px - stroke / 2, py - stroke / 2, px + stroke / 2, py + stroke / 2), fill=color)

        # codice a barre che esce dall'apertura della C
        bar_h = W * 0.105
        x = W * 0.655
        for bw in (0.024, 0.046, 0.022, 0.036):
            bw_px = W * bw
            d.rounded_rectangle((x, cy - bar_h, x + bw_px, cy + bar_h),
                                radius=bw_px / 2, fill=color)
            x += bw_px + W * 0.026
        return layer

    # ombra del motivo
    shadow = draw_motif((10, 16, 50, 110)).filter(ImageFilter.GaussianBlur(W * 0.012))
    img = Image.alpha_composite(img, shadow.transform(
        shadow.size, Image.AFFINE, (1, 0, -W * 0.008, 0, 1, -W * 0.012)))
    img = Image.alpha_composite(img, draw_motif(WHITE))

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
