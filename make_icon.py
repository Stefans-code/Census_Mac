"""Genera l'icona di Census ERP: scatola di magazzino isometrica su gradiente blu.

Output: icon.png (1024), icon_512.png, icon_256.png, icon.ico (multi-size), icon.icns (Mac).
"""
from PIL import Image, ImageDraw, ImageFilter, ImageOps

S = 1024          # dimensione finale
F = 4             # supersampling per l'antialiasing
W = S * F

C_TOP = (104, 152, 255)    # blu acceso in alto
C_BOT = (24, 33, 96)       # indaco profondo in basso

# Facce della scatola (top più chiara, lati progressivamente più scuri)
FACE_TOP   = (255, 255, 255, 255)
FACE_LEFT  = (214, 228, 250, 255)
FACE_RIGHT = (176, 200, 240, 255)
FLAP_TOP   = (236, 244, 255, 255)
FLAP_INNER = (198, 214, 242, 255)


def _squircle_mask():
    m = Image.new('L', (W, W), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, W - 1, W - 1), radius=int(W * 0.235), fill=255)
    return m


def _radial(center, radius, color):
    layer = Image.new('L', (W, W), 0)
    cx, cy = center
    ImageDraw.Draw(layer).ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=255)
    layer = layer.filter(ImageFilter.GaussianBlur(radius * 0.55))
    out = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    out.paste(Image.new('RGBA', (W, W), color), (0, 0), layer)
    return out


def build():
    mask = _squircle_mask()

    # --- Sfondo squircle con gradiente verticale ---
    grad = Image.linear_gradient('L').resize((W, W))
    bg = ImageOps.colorize(grad, black=C_TOP, white=C_BOT).convert('RGBA')
    img = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    img.paste(bg, (0, 0), mask)

    def clip(layer):
        return Image.composite(layer, Image.new('RGBA', (W, W), (0, 0, 0, 0)), mask)

    # Riflesso vetro + vignettatura per profondità
    img = Image.alpha_composite(img, clip(_radial((W * 0.30, W * 0.20), W * 0.42, (255, 255, 255, 46))))
    img = Image.alpha_composite(img, clip(_radial((W * 0.86, W * 0.92), W * 0.50, (8, 12, 44, 70))))

    # Bordo interno luminoso (bevel)
    ring = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    ImageDraw.Draw(ring).rounded_rectangle(
        (int(W * 0.012), int(W * 0.012), int(W - W * 0.012), int(W - W * 0.012)),
        radius=int(W * 0.235 * 0.96), outline=(255, 255, 255, 60), width=int(W * 0.006))
    img = Image.alpha_composite(img, clip(ring))

    # --- Scatola isometrica chiusa (design pulito approvato) ---
    cx, cy = W * 0.50, W * 0.52
    s = W * 0.23       # mezza larghezza/altezza del cubo

    def draw_box(layer):
        d = ImageDraw.Draw(layer)
        # Faccia superiore (rombo)
        d.polygon([(cx, cy - s), (cx + s, cy - s / 2), (cx, cy), (cx - s, cy - s / 2)], fill=FACE_TOP)
        # Faccia sinistra
        d.polygon([(cx - s, cy - s / 2), (cx, cy), (cx, cy + s), (cx - s, cy + s / 2)], fill=FACE_LEFT)
        # Faccia destra
        d.polygon([(cx, cy), (cx + s, cy - s / 2), (cx + s, cy + s / 2), (cx, cy + s)], fill=FACE_RIGHT)
        # Nastro adesivo sul lembo superiore
        d.line([(cx, cy - s), (cx, cy)], fill=(120, 150, 220, 255), width=int(W * 0.013))

    # Ombra portata
    shadow_layer = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    draw_box(shadow_layer)
    alpha = shadow_layer.getchannel('A')
    shadow = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    shadow.paste(Image.new('RGBA', (W, W), (8, 14, 44, 120)), (int(W * 0.006), int(W * 0.018)), alpha)
    shadow = shadow.filter(ImageFilter.GaussianBlur(W * 0.016))
    img = Image.alpha_composite(img, clip(shadow))

    # Scatola
    box_layer = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    draw_box(box_layer)
    img = Image.alpha_composite(img, box_layer)

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
