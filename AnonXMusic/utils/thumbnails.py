import os
import re
import math

import aiofiles
import aiohttp
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from unidecode import unidecode
from ytSearch import VideosSearch

from AnonXMusic import app
from config import YOUTUBE_IMG_URL


# ── helpers ───────────────────────────────────────────────────────────────────

def changeImageSize(maxWidth, maxHeight, image):
    widthRatio  = maxWidth  / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth    = int(widthRatio  * image.size[0])
    newHeight   = int(heightRatio * image.size[1])
    return image.resize((newWidth, newHeight), Image.LANCZOS)


def circle(img):
    img = img.convert("RGBA")
    h, w = img.size
    mask = Image.new("L", (h, w), 0)
    ImageDraw.Draw(mask).ellipse([(0, 0), (h, w)], fill=255)
    result = Image.new("RGBA", (h, w), (0, 0, 0, 0))
    result.paste(img, mask=mask)
    return result


def clear(text, limit=45):
    words, title = text.split(" "), ""
    for w in words:
        if len(title) + len(w) < limit:
            title += " " + w
    return title.strip()


def get_dominant_color(img: Image.Image, n=4):
    """Return most vibrant dominant colour via mini k-means."""
    small = img.convert("RGB").resize((120, 120))
    arr   = np.array(small).reshape(-1, 3).astype(float)
    np.random.seed(42)
    centers = arr[np.random.choice(len(arr), n, replace=False)]
    for _ in range(12):
        dists  = np.linalg.norm(arr[:, None] - centers[None], axis=2)
        labels = np.argmin(dists, axis=1)
        for k in range(n):
            pts = arr[labels == k]
            if len(pts):
                centers[k] = pts.mean(axis=0)
    best, best_sat = centers[0], 0
    for c in centers:
        r, g, b = c / 255.0
        mx, mn  = max(r, g, b), min(r, g, b)
        sat     = (mx - mn) / (mx + 1e-9)
        lum     = (mx + mn) / 2
        # prefer vibrant colours (high sat, mid luminance)
        score   = sat * (1 - abs(lum - 0.5))
        if score > best_sat:
            best_sat, best = score, c
    return tuple(int(x) for x in best)


def build_palette(base):
    """
    Always return ALL 10 neon colours in a visually pleasing rainbow cycle,
    rotated so the colour closest to the song's dominant hue comes first.
    This guarantees a true multi-colour rainbow ring every time regardless
    of the song cover — not just warm or cool tones.

    The 10 neon colours (as specified):
      Blue #1e90ff  Purple #a855f7  Rose #f43f5e  Amber #f59e0b
      Teal #14b8a6  Green #22c55e   Orange #f97316 Pink #ec4899
      Cyan #06b6d4  White #e2e8f0
    """
    # Fixed rainbow cycle order (visually flows blue→purple→rose→amber→teal etc.)
    RAINBOW = [
        (0x1e, 0x90, 0xff),   # Blue
        (0x06, 0xb6, 0xd4),   # Cyan
        (0x14, 0xb8, 0xa6),   # Teal
        (0x22, 0xc5, 0x5e),   # Green
        (0xf5, 0x9e, 0x0b),   # Amber
        (0xf9, 0x73, 0x16),   # Orange
        (0xf4, 0x3f, 0x5e),   # Rose
        (0xec, 0x48, 0x99),   # Pink
        (0xa8, 0x55, 0xf7),   # Purple
        (0xe2, 0xe8, 0xf0),   # White
    ]
    br, bg, bb = base

    def dist(c):
        return math.sqrt((c[0]-br)**2 * 0.299 + (c[1]-bg)**2 * 0.587 + (c[2]-bb)**2 * 0.114)

    # Find the index of the closest colour in the rainbow
    best_idx = min(range(len(RAINBOW)), key=lambda i: dist(RAINBOW[i]))

    # Rotate the rainbow so the closest colour leads
    rotated = RAINBOW[best_idx:] + RAINBOW[:best_idx]
    return rotated  # all 10 colours, rainbow-ordered, dominant-first


def make_neon_glow_border(size, bbox, dominant, radius=30, stroke=6, glow_layers=10):
    """
    Clean single-stroke neon border with soft glowing blur halo.
    - One thin bright stroke at the bbox edge
    - Multiple expanding faint layers behind it for the glow spread
    - Colour comes from the song dominant, mapped to the closest neon hue
    - Same function used for both outer card and centre rectangle ring
    """
    NEON = [
        (0x1e, 0x90, 0xff),   # Blue
        (0x06, 0xb6, 0xd4),   # Cyan
        (0x14, 0xb8, 0xa6),   # Teal
        (0x22, 0xc5, 0x5e),   # Green
        (0xf5, 0x9e, 0x0b),   # Amber
        (0xf9, 0x73, 0x16),   # Orange
        (0xf4, 0x3f, 0x5e),   # Rose
        (0xec, 0x48, 0x99),   # Pink
        (0xa8, 0x55, 0xf7),   # Purple
        (0xe2, 0xe8, 0xf0),   # White
    ]
    br, bg, bb = dominant

    def dist(c):
        return math.sqrt((c[0]-br)**2*0.299 + (c[1]-bg)**2*0.587 + (c[2]-bb)**2*0.114)

    # Pick the single closest neon hue — this IS the border colour
    best = min(NEON, key=dist)
    nr, ng, nb = best

    # Secondary accent (second closest, for subtle glow variation)
    sorted_neon = sorted(NEON, key=dist)
    nr2, ng2, nb2 = sorted_neon[1]

    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    x0, y0, x1, y1 = bbox
    ld = ImageDraw.Draw(layer)

    # ── Outer soft glow halo (wide, faint, expanding) ────────────────────────
    for i in range(glow_layers, 0, -1):
        t      = i / glow_layers
        expand = int(t ** 0.5 * glow_layers * 4)   # spreads outward
        alpha  = int(4 + (1 - t) ** 1.2 * 140)     # faint outside, brighter inside
        w      = stroke + int(t * glow_layers * 2)
        lx0    = max(0,       x0 - expand)
        ly0    = max(0,       y0 - expand)
        lx1    = min(size[0], x1 + expand)
        ly1    = min(size[1], y1 + expand)
        # alternate primary/secondary colour for subtle shimmer
        cr, cg, cb = (nr, ng, nb) if i % 2 == 0 else (nr2, ng2, nb2)
        ld.rounded_rectangle(
            (lx0, ly0, lx1, ly1),
            radius=max(6, radius - expand // 6),
            outline=(cr, cg, cb, alpha),
            width=w
        )

    # ── Bright inner glow (tight, vivid) ─────────────────────────────────────
    for s in range(4, 0, -1):
        alpha = 60 + s * 35
        ld.rounded_rectangle(
            (x0 - s, y0 - s, x1 + s, y1 + s),
            radius=radius,
            outline=(min(255, nr + 60), min(255, ng + 60), min(255, nb + 60), alpha),
            width=stroke + s
        )

    # ── Crisp primary stroke ──────────────────────────────────────────────────
    ld.rounded_rectangle(
        bbox, radius=radius,
        outline=(min(255, nr + 90), min(255, ng + 90), min(255, nb + 90), 255),
        width=stroke
    )

    # ── White-hot centre line ─────────────────────────────────────────────────
    ld.rounded_rectangle(
        bbox, radius=radius,
        outline=(255, 255, 255, 90),
        width=max(1, stroke // 3)
    )

    return layer


def draw_glowing_progress_bar(draw, canvas, x0, y0, x1, bar_h, thumb_frac, palette):
    """
    Draw a neon-glowing progress bar whose colour matches the border palette.
    Includes soft glow behind the filled portion + bright thumb dot with glow.
    """
    # ── track background ──────────────────────────────────────────────────────
    draw.rounded_rectangle(
        [(x0, y0), (x1, y0 + bar_h)],
        radius=bar_h // 2,
        fill=(50, 50, 80, 160)
    )

    thumb_x = int(x0 + (x1 - x0) * thumb_frac)
    base_col = palette[0]
    accent   = palette[3]   # magenta-pink for contrast pop

    # ── glow behind filled bar (soft, wide) ──────────────────────────────────
    for glow in range(6, 0, -1):
        gr, gg, gb = base_col
        ga         = int(15 + (6 - glow) * 18)
        gpad       = glow * 2
        draw.rounded_rectangle(
            [(x0, y0 - gpad // 2), (thumb_x, y0 + bar_h + gpad // 2)],
            radius=bar_h // 2 + gpad // 2,
            fill=(min(255, gr + 60), min(255, gg + 60), min(255, gb + 60), ga)
        )

    # ── filled (played) bar – gradient-like using two overlaid rects ─────────
    r1, g1, b1 = base_col
    r2, g2, b2 = accent
    draw.rounded_rectangle(
        [(x0, y0), (thumb_x, y0 + bar_h)],
        radius=bar_h // 2,
        fill=(min(255, r1 + 80), min(255, g1 + 80), min(255, b1 + 80), 240)
    )
    # thin bright top highlight stripe
    draw.rounded_rectangle(
        [(x0, y0), (thumb_x, y0 + bar_h // 3)],
        radius=bar_h // 2,
        fill=(min(255, r2 + 100), min(255, g2 + 100), min(255, b2 + 100), 120)
    )

    # ── thumb dot glow ────────────────────────────────────────────────────────
    TR = 10
    cy = y0 + bar_h // 2
    for glow in range(5, 0, -1):
        gr, gg, gb = accent
        ga         = int(20 + (5 - glow) * 25)
        gr_r       = TR + glow * 3
        draw.ellipse(
            [(thumb_x - gr_r, cy - gr_r), (thumb_x + gr_r, cy + gr_r)],
            fill=(min(255, gr + 80), min(255, gg + 80), min(255, gb + 80), ga)
        )
    # solid bright dot
    draw.ellipse(
        [(thumb_x - TR, cy - TR), (thumb_x + TR, cy + TR)],
        fill=(255, 255, 255, 250)
    )
    # inner coloured core
    draw.ellipse(
        [(thumb_x - TR + 3, cy - TR + 3), (thumb_x + TR - 3, cy + TR - 3)],
        fill=(min(255, r2 + 100), min(255, g2 + 100), min(255, b2 + 100), 200)
    )

    return thumb_x


# ── main function ─────────────────────────────────────────────────────────────

async def get_thumb(videoid, user_id, title=None, duration=None, thumbnail=None,
                    views=None, channel=None):
    """
    Generate a styled now-playing thumbnail.

    Called as:
      get_thumb(videoid, user_id)                            – auto-fetches details
      get_thumb(videoid, user_id, title=, duration=, ...)   – uses provided details
    """
    if os.path.isfile(f"cache/{videoid}_{user_id}.png"):
        return f"cache/{videoid}_{user_id}.png"

    try:
        # ── fetch song details if not already provided ────────────────────
        if not title or not thumbnail:
            url     = f"https://www.youtube.com/watch?v={videoid}"
            results = VideosSearch(url, limit=1)
            for result in (await results.next())["result"]:
                try:
                    title = result["title"]
                    title = re.sub(r"\W+", " ", title).title()
                except:
                    title = "Unsupported Title"
                try:
                    duration = result["duration"]
                except:
                    duration = "Unknown"
                thumbnail = result["thumbnails"][0]["url"].split("?")[0]
                try:
                    views = result["viewCount"]["short"]
                except:
                    views = "Unknown Views"
                try:
                    channel = result["channel"]["name"]
                except:
                    channel = "Unknown Channel"
        else:
            title    = re.sub(r"\W+", " ", str(title)).title()
            duration = duration or "Unknown"
            views    = views    or "Unknown Views"
            channel  = channel  or "Unknown Channel"

        # ── download thumbnail ────────────────────────────────────────────
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status == 200:
                    f = await aiofiles.open(f"cache/thumb{videoid}.png", mode="wb")
                    await f.write(await resp.read())
                    await f.close()

        # ═════════════════════════════════════════════════════════════════
        # WORK AT 2× RESOLUTION → downsample at end for anti-aliasing
        # This gives much crisper text, borders and thumbnail quality.
        # ═════════════════════════════════════════════════════════════════
        SCALE    = 2
        W, H     = 1280 * SCALE, 720 * SCALE

        # Layout (in full-res coords)
        BOTTOM_H = 185 * SCALE    # taller bar (was 150)
        CZ_H     = H - BOTTOM_H  # cover zone height

        canvas = Image.new("RGBA", (W, H), (10, 6, 22, 255))

        # ── blurred cover background ──────────────────────────────────────
        cover_raw = Image.open(f"cache/thumb{videoid}.png").convert("RGBA")
        # Enhance the source image sharpness/colour before using it
        cover_raw = ImageEnhance.Sharpness(cover_raw).enhance(1.4)
        cover_raw = ImageEnhance.Color(cover_raw).enhance(1.3)

        dominant  = get_dominant_color(cover_raw)
        palette   = build_palette(dominant)
        r_d, g_d, b_d = dominant

        cover_bg = cover_raw.resize((W, CZ_H), Image.LANCZOS).convert("RGBA")
        cover_bg = cover_bg.filter(ImageFilter.GaussianBlur(28 * SCALE // 2))
        cover_bg = Image.alpha_composite(
            cover_bg, Image.new("RGBA", (W, CZ_H), (0, 0, 0, 140))
        )
        canvas.paste(cover_bg, (0, 0))

        # gradient fade at bottom of cover zone
        fade = Image.new("RGBA", (W, 130 * SCALE), (0, 0, 0, 0))
        for row in range(130 * SCALE):
            a = int((row / (130 * SCALE)) ** 1.5 * 240)
            ImageDraw.Draw(fade).line([(0, row), (W, row)], fill=(10, 6, 22, a))
        canvas.alpha_composite(fade, (0, CZ_H - 65 * SCALE))

        # ── bottom bar ────────────────────────────────────────────────────
        bar_r = max(0, r_d - 160)
        bar_g = max(0, g_d - 160)
        bar_b = max(0, b_d - 150)
        bar   = Image.new("RGBA", (W, BOTTOM_H + 20 * SCALE), (bar_r, bar_g, bar_b, 240))
        bar   = Image.alpha_composite(
            bar, Image.new("RGBA", (W, BOTTOM_H + 20 * SCALE), (0, 0, 0, 80))
        )
        canvas.alpha_composite(bar, (0, CZ_H - 16 * SCALE))

        # ── centre cover art – bigger, nudged down into centre of cover zone ──
        CV_W    = 390 * SCALE   # wider (was 340)
        CV_H    = 320 * SCALE   # taller (was 280)
        CV_LEFT = (W - CV_W) // 2
        # +30*SCALE moves it down from the zone midpoint toward the bar
        CV_TOP  = (CZ_H - CV_H) // 2 + 30 * SCALE

        cover_sq = cover_raw.resize((CV_W, CV_H), Image.LANCZOS).convert("RGBA")
        # Extra sharpness on the displayed cover
        cover_sq = ImageEnhance.Sharpness(cover_sq).enhance(1.5)
        cover_sq = ImageEnhance.Contrast(cover_sq).enhance(1.1)
        rc_mask  = Image.new("L", (CV_W, CV_H), 0)
        ImageDraw.Draw(rc_mask).rounded_rectangle(
            [(0, 0), (CV_W, CV_H)], radius=22 * SCALE, fill=255
        )
        cover_sq.putalpha(rc_mask)

        # drop shadow
        sh_w, sh_h = CV_W + 80 * SCALE, CV_H + 80 * SCALE
        shadow     = Image.new("RGBA", (sh_w, sh_h), (0, 0, 0, 0))
        ImageDraw.Draw(shadow).rounded_rectangle(
            [(24 * SCALE, 24 * SCALE), (sh_w - 24 * SCALE, sh_h - 24 * SCALE)],
            radius=30 * SCALE, fill=(r_d // 2, g_d // 2, b_d // 2, 180)
        )
        shadow = shadow.filter(ImageFilter.GaussianBlur(22 * SCALE // 2))
        canvas.alpha_composite(shadow, (CV_LEFT - 40 * SCALE, CV_TOP - 40 * SCALE))
        canvas.alpha_composite(cover_sq, (CV_LEFT, CV_TOP))

        # neon ring around cover art — same colour as outer border
        ring_pad   = 10 * SCALE
        ring_layer = make_neon_glow_border(
            (W, H),
            (CV_LEFT - ring_pad, CV_TOP - ring_pad,
             CV_LEFT + CV_W + ring_pad, CV_TOP + CV_H + ring_pad),
            dominant, radius=28 * SCALE, stroke=5 * SCALE, glow_layers=10
        )
        canvas.alpha_composite(ring_layer)

        # ── outer card border – thin glowing neon, colour from song ──────────
        border_layer = make_neon_glow_border(
            (W, H), (6 * SCALE, 6 * SCALE, W - 6 * SCALE, H - 6 * SCALE),
            dominant, radius=30 * SCALE, stroke=5 * SCALE, glow_layers=12
        )
        canvas.alpha_composite(border_layer)

        # ── "NOW PLAYING" badge (top-left) ───────────────────────────────
        BW, BH = 210 * SCALE, 42 * SCALE
        badge  = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
        p0     = palette[0]
        ImageDraw.Draw(badge).rounded_rectangle(
            [(0, 0), (BW, BH)],
            radius=BH // 2,
            fill=(max(0, p0[0] - 80), max(0, p0[1] - 80), max(0, p0[2] - 80), 210),
            outline=(min(255, p0[0] + 100), min(255, p0[1] + 100), min(255, p0[2] + 100), 220),
            width=3 * SCALE // 2
        )
        canvas.alpha_composite(badge, (28 * SCALE, 26 * SCALE))

        # ── Bot name badge (top-right, same style & height) ───────────────
        bot_name  = unidecode(app.name)[:18]   # truncate if very long
        # measure text width to size the badge dynamically
        try:
            font_badge_tmp = ImageFont.truetype("AnonXMusic/assets/font2.ttf", 18 * SCALE)
            txt_w = font_badge_tmp.getlength(bot_name)
        except:
            txt_w = len(bot_name) * 11 * SCALE
        RBW = int(txt_w) + 36 * SCALE   # padding on each side
        RBH = BH
        rbadge = Image.new("RGBA", (RBW, RBH), (0, 0, 0, 0))
        ImageDraw.Draw(rbadge).rounded_rectangle(
            [(0, 0), (RBW, RBH)],
            radius=RBH // 2,
            fill=(max(0, p0[0] - 80), max(0, p0[1] - 80), max(0, p0[2] - 80), 210),
            outline=(min(255, p0[0] + 100), min(255, p0[1] + 100), min(255, p0[2] + 100), 220),
            width=3 * SCALE // 2
        )
        # Place at same Y as NOW PLAYING badge, flush to right edge
        RB_X = W - RBW - 28 * SCALE
        RB_Y = 26 * SCALE
        canvas.alpha_composite(rbadge, (RB_X, RB_Y))

        # ── fonts (scaled) ────────────────────────────────────────────────
        try:
            font_bold  = ImageFont.truetype("AnonXMusic/assets/font2.ttf", 32 * SCALE)
            font_badge = ImageFont.truetype("AnonXMusic/assets/font2.ttf", 18 * SCALE)
            font_small = ImageFont.truetype("AnonXMusic/assets/font.ttf",  24 * SCALE)
            font_dur   = ImageFont.truetype("AnonXMusic/assets/font.ttf",  22 * SCALE)
        except:
            font_bold = font_badge = font_small = font_dur = ImageFont.load_default()

        draw = ImageDraw.Draw(canvas)

        # badge texts
        draw.text(
            (48 * SCALE, 34 * SCALE),
            "NOW PLAYING",
            fill=(230, 235, 255, 245),
            font=font_badge
        )
        # bot name badge text — centred inside the right badge
        draw.text(
            (RB_X + 18 * SCALE, RB_Y + (RBH - font_badge.size) // 2),
            bot_name,
            fill=(230, 235, 255, 245),
            font=font_badge
        )

        # ═══════════════════════════════════════════════════════════════════
        # BOTTOM BAR (taller = more breathing room)
        #
        #  [icon]  Song Title (bold, large)
        #          Played by: BotName  ·  Channel
        #          ════════════════●═══════════════
        #          00:00                      4:29
        # ═══════════════════════════════════════════════════════════════════
        BAR_Y     = CZ_H - 16 * SCALE
        IS        = 118 * SCALE   # icon size
        ICON_X    = 52 * SCALE    # shifted right (was 24) for better alignment
        ICON_Y    = BAR_Y + (BOTTOM_H - IS) // 2

        # icon
        icon_img = cover_raw.resize((IS, IS), Image.LANCZOS).convert("RGBA")
        icon_img = ImageEnhance.Sharpness(icon_img).enhance(1.3)
        ic_mask  = Image.new("L", (IS, IS), 0)
        ImageDraw.Draw(ic_mask).rounded_rectangle(
            [(0, 0), (IS, IS)], radius=16 * SCALE, fill=255
        )
        icon_img.putalpha(ic_mask)
        canvas.alpha_composite(icon_img, (ICON_X, ICON_Y))

        # text columns
        TEXT_X  = ICON_X + IS + 22 * SCALE
        LINE1_Y = BAR_Y + 16 * SCALE                          # title
        LINE2_Y = BAR_Y + 16 * SCALE + 38 * SCALE            # subtitle

        draw.text((TEXT_X, LINE1_Y), clear(title, 40),
                  fill=(255, 255, 255, 250), font=font_bold)
        draw.text(
            (TEXT_X, LINE2_Y),
            f"Played by: {unidecode(app.name)}  ·  {channel[:32]}",
            fill=(175, 180, 215, 195),
            font=font_small
        )

        # ── progress bar (colour-matched to border palette) ───────────────
        PROG_X0  = TEXT_X
        PROG_X1  = W - 32 * SCALE
        BAR_H_PX = 8 * SCALE
        PROG_Y   = BAR_Y + BOTTOM_H - 52 * SCALE   # neat gap from bar bottom
        TIME_Y   = PROG_Y + BAR_H_PX + 8 * SCALE

        draw_glowing_progress_bar(
            draw, canvas,
            PROG_X0, PROG_Y, PROG_X1, BAR_H_PX,
            thumb_frac=0.65,
            palette=palette
        )

        # time labels – same Y, anchored to bar edges
        draw.text((PROG_X0,          TIME_Y), "00:00",       fill=(195, 200, 230, 210), font=font_dur)
        draw.text((PROG_X1 - 74 * SCALE, TIME_Y), duration[:7], fill=(195, 200, 230, 210), font=font_dur)

        # ── downsample to final 1280×720 for crisp anti-aliased output ────
        final = canvas.convert("RGB").resize((1280, 720), Image.LANCZOS)

        try:
            os.remove(f"cache/thumb{videoid}.png")
        except:
            pass

        final.save(f"cache/{videoid}_{user_id}.png", quality=97, optimize=False)
        return f"cache/{videoid}_{user_id}.png"

    except Exception:
        return YOUTUBE_IMG_URL
