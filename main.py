#!/usr/bin/env python3
"""LEVICUP — catalogue photo of an impossible gadget.

Generates /output/entry.png (1024x1024, <= 1 MiB): a studio catalogue
photo of a white ceramic mug hovering 3 cm above a table.
Stdlib + Pillow only, no network, deterministic.
Drawn at 2048x2048 and downscaled to 1024x1024 (supersampled AA).
"""

import math
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = 2  # supersample factor
W, H = 1024 * S, 1024 * S
OUT = "/output/entry.png"

BG_TOP = (232, 232, 230)
BG_BOT = (217, 217, 214)
TABLE_TOP = (212, 212, 209)
TABLE_BOT = (198, 198, 195)
HORIZON_Y = int(H * 0.65)

MUG_WHITE = (250, 250, 248)
MUG_SHADE = (216, 216, 213)
MUG_DARK = (188, 188, 185)
COFFEE = (74, 52, 36)
TEXT_DARK = (74, 74, 72)
TEXT_MID = (110, 110, 108)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def rounded_body(draw, box, radius, fill):
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def main():
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)

    # --- studio background: vertical gradient ---
    for y in range(H):
        t = y / (H - 1)
        if y < HORIZON_Y:
            c = lerp(BG_TOP, BG_BOT, y / HORIZON_Y)
        else:
            c = lerp(TABLE_TOP, TABLE_BOT, (y - HORIZON_Y) / (H - HORIZON_Y))
        d.line([(0, y), (W, y)], fill=c)

    # --- soft horizon line ---
    hl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hl)
    hd.line([(0, HORIZON_Y), (W, HORIZON_Y)], fill=(150, 150, 148, 90), width=3)
    img.paste(Image.alpha_composite(img.convert("RGBA"), hl.filter(ImageFilter.GaussianBlur(4))), (0, 0))
    d = ImageDraw.Draw(img)

    cx = W // 2

    # --- mug geometry (floating) ---
    mug_top = int(H * 0.30)        # 614
    mug_bot = int(H * 0.545)       # 1116
    mug_w = int(W * 0.27)          # 553
    mug_l, mug_r = cx - mug_w // 2, cx + mug_w // 2
    rim_h = int(H * 0.035)         # rim ellipse height

    # --- soft shadow on the table (below the floating mug) ---
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sh_cy = int(H * 0.685)
    sd.ellipse([cx - mug_w * 0.62, sh_cy - 34, cx + mug_w * 0.62, sh_cy + 34],
               fill=(90, 90, 88, 110))
    sh = sh.filter(ImageFilter.GaussianBlur(28))
    img.paste(Image.alpha_composite(img.convert("RGBA"), sh), (0, 0))
    d = ImageDraw.Draw(img)

    # --- faint reflection streak on the table ---
    rf = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rf)
    rd.ellipse([cx - mug_w * 0.42, sh_cy + 30, cx + mug_w * 0.42, sh_cy + 78],
               fill=(255, 255, 255, 55))
    rf = rf.filter(ImageFilter.GaussianBlur(18))
    img.paste(Image.alpha_composite(img.convert("RGBA"), rf), (0, 0))
    d = ImageDraw.Draw(img)

    # --- handle (right side), drawn first so body overlaps its base ---
    hw = int(W * 0.045)
    d.arc([mug_r - 30, mug_top + 90, mug_r + mug_w * 0.42, mug_bot - 60],
          start=-90, end=90, fill=MUG_WHITE, width=hw)
    d.arc([mug_r - 30, mug_top + 90, mug_r + mug_w * 0.42, mug_bot - 60],
          start=-90, end=90, fill=MUG_SHADE, width=4)

    # --- mug body: slightly tapered cylinder ---
    body = [mug_l, mug_top, mug_r, mug_bot]
    rounded_body(d, body, radius=46, fill=MUG_WHITE)
    # right-side shading
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shade)
    sdraw.rounded_rectangle([mug_r - 150, mug_top, mug_r, mug_bot], radius=46,
                            fill=(150, 150, 148, 70))
    shade = shade.filter(ImageFilter.GaussianBlur(30))
    img.paste(Image.alpha_composite(img.convert("RGBA"), shade), (0, 0))
    d = ImageDraw.Draw(img)
    # left highlight band
    hl2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    h2 = ImageDraw.Draw(hl2)
    h2.rounded_rectangle([mug_l + 34, mug_top + 30, mug_l + 110, mug_bot - 30],
                         radius=38, fill=(255, 255, 255, 120))
    hl2 = hl2.filter(ImageFilter.GaussianBlur(22))
    img.paste(Image.alpha_composite(img.convert("RGBA"), hl2), (0, 0))
    d = ImageDraw.Draw(img)
    # bottom edge / base shadow line under the mug
    d.rounded_rectangle([mug_l + 60, mug_bot - 26, mug_r - 60, mug_bot + 6],
                        radius=12, fill=(205, 205, 202))

    # --- rim + coffee inside ---
    d.ellipse([mug_l + 6, mug_top - rim_h // 2, mug_r - 6, mug_top + rim_h // 2],
              fill=(238, 238, 236), outline=(200, 200, 198), width=4)
    d.ellipse([mug_l + 34, mug_top - rim_h // 2 + 12, mug_r - 34, mug_top + rim_h // 2 - 4],
              fill=COFFEE)

    # --- steam: 3 thin curving wisps ---
    st = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    std = ImageDraw.Draw(st)
    for k, (xoff, amp, phase) in enumerate([(0, 46, 0.0), (-95, 38, 1.4), (95, 42, 2.6)]):
        pts = []
        y0 = mug_top - 30
        for i in range(41):
            t = i / 40
            x = cx + xoff + amp * math.sin(phase + t * 3.6) * (0.4 + t)
            y = y0 - t * 260
            pts.append((x, y))
        std.line(pts, fill=(255, 255, 255, 150 - k * 20), width=10 - k * 2, joint="curve")
    st = st.filter(ImageFilter.GaussianBlur(6))
    img.paste(Image.alpha_composite(img.convert("RGBA"), st), (0, 0))
    d = ImageDraw.Draw(img)

    # --- downscale to 1024 ---
    img = img.resize((1024, 1024), Image.LANCZOS)
    d = ImageDraw.Draw(img)

    # --- catalogue text (drawn at final size for crispness) ---
    def font(size, bold=False):
        for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
                  else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                  "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
        return ImageFont.load_default(size=size)

    f1 = font(34, bold=True)
    f2 = font(22)
    t1 = "LEVICUP\u2122 \u2014 HOVER MUG"
    t2 = "hovers 3 cm. forever. no batteries. no magnets. no explanation."
    for txt, fnt, y, col in ((t1, f1, 872, TEXT_DARK), (t2, f2, 922, TEXT_MID)):
        bb = d.textbbox((0, 0), txt, font=fnt)
        d.text(((1024 - (bb[2] - bb[0])) // 2, y), txt, font=fnt, fill=col)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    print("wrote", OUT, os.path.getsize(OUT), "bytes")


if __name__ == "__main__":
    main()
