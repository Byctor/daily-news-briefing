#!/usr/bin/env python3
"""
Emoji icon renderer for PIL — draws colorful weather & utility icons.
No external font or download required. All icons are vector-like PIL primitives.
"""

from PIL import Image, ImageDraw


def create_sun(size=28):
    """☀ Yellow sun with rays."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    r = size // 2
    c = size // 2
    # Rays (thin lines)
    for angle in range(0, 360, 45):
        import math
        rad = math.radians(angle)
        outer_x = c + int((r - 2) * math.cos(rad))
        outer_y = c - int((r - 2) * math.sin(rad))
        inner_x = c + int((r - 8) * math.cos(rad))
        inner_y = c - int((r - 8) * math.sin(rad))
        draw.line([(inner_x, inner_y), (outer_x, outer_y)], fill="#F5A623", width=3)
    # Main circle
    draw.ellipse([4, 4, size - 4, size - 4], fill="#F5A623")
    draw.ellipse([5, 5, size - 5, size - 5], fill="#FFD54F")
    return img


def create_cloud(size=28):
    """☁ Gray-blue cloud."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    s = size
    # Cloud body (overlapping circles)
    draw.ellipse([2, s // 3, s // 2 + 4, s - 4], fill="#B0BEC5")
    draw.ellipse([s // 3 - 2, 4, s - 4, s // 2 + 6], fill="#90A4AE")
    draw.ellipse([s // 4, s // 4, s * 3 // 4 + 2, s - 4], fill="#90A4AE")
    # Highlight
    draw.ellipse([s // 4 + 4, 8, s // 2 + 6, s // 3 + 4], fill="#CFD8DC")
    return img


def create_umbrella(size=28):
    """☔ Umbrella with rain drops."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    s = size
    # Canopy
    draw.pieslice([2, 2, s - 2, s - 3], start=180, end=360, fill="#5C6BC0")
    draw.pieslice([4, 4, s - 4, s - 5], start=180, end=360, fill="#7986CB")
    # Handle
    draw.arc([s // 3 - 2, s // 3, s - s // 3 + 2, s + 6], start=0, end=180, fill="#5C6BC0", width=2)
    # Rain drops
    for dx, dy in [(s // 4 + 2, s - 6), (s // 2 - 2, s - 3), (s * 3 // 4 - 4, s - 5)]:
        draw.ellipse([dx, dy, dx + 3, dy + 5], fill="#42A5F5")
    return img


def create_snowflake(size=28):
    """❄ Light blue snowflake."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    c = size // 2
    # 6 arms
    import math
    for i in range(6):
        rad = math.radians(i * 60)
        end_x = c + int((c - 2) * math.cos(rad))
        end_y = c - int((c - 2) * math.sin(rad))
        draw.line([(c, c), (end_x, end_y)], fill="#81D4FA", width=3)
        # Small branches
        for frac in [0.5, 0.75]:
            bx = c + int((c - 2) * frac * math.cos(rad))
            by = c - int((c - 2) * frac * math.sin(rad))
            for side in [-1, 1]:
                s_rad = rad + side * 0.5
                sx = bx + int(4 * math.cos(s_rad))
                sy = by - int(4 * math.sin(s_rad))
                draw.line([(bx, by), (sx, sy)], fill="#B3E5FC", width=1)
    # Center dot
    draw.ellipse([c - 3, c - 3, c + 3, c + 3], fill="#4FC3F7")
    return img


def create_lightning(size=28):
    """⚡ Yellow lightning bolt."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    s = size
    # Lightning bolt shape
    points = [
        (s * 2 // 3, 2),       # top-right
        (s // 4, s // 2 - 2),   # mid-left
        (s // 2, s // 2 - 2),   # mid-center
        (s // 3, s - 2),        # bottom-left
        (s * 3 // 4, s // 2 + 2),  # mid-right
        (s // 2, s // 2 + 2),   # mid-center
    ]
    draw.polygon(points, fill="#FFD54F")
    draw.polygon(points, outline="#F5A623")
    return img


def create_link(size=28):
    """🔗 Interlocking chain links for URLs."""
    from PIL import ImageDraw as ID
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ID.Draw(img)
    s = size
    t = max(2, s // 12)
    c = s // 2
    lw = s * 2 // 5
    lh = s * 3 // 5

    # Right link (behind)
    draw.rounded_rectangle(
        [c, c - lh, c + lw, c + lh], radius=t * 2, outline="#C56A2E", width=t
    )
    # Left link (front)
    draw.rounded_rectangle(
        [s - c - lw, c - lh, s - c, c + lh], radius=t * 2, outline="#C56A2E", width=t
    )
    return img


def create_sun_cloud(size=28):
    """⛅ Sun behind cloud."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    s = size
    # Sun (partial, behind cloud)
    draw.ellipse([4, 2, s * 2 // 3 + 2, s * 2 // 3], fill="#FFD54F")
    draw.ellipse([6, 4, s * 2 // 3, s * 2 // 3 - 2], fill="#FFEB3B")
    # Cloud (front)
    draw.ellipse([s // 5, s // 3 + 2, s * 4 // 5, s - 4], fill="#B0BEC5")
    draw.ellipse([s // 4 - 2, 6, s - 2, s // 2 + 6], fill="#90A4AE")
    draw.ellipse([s // 4 + 4, s // 4, s * 3 // 4, s - 4], fill="#90A4AE")
    draw.ellipse([s // 4 + 6, 10, s // 2 + 6, s // 3 + 4], fill="#CFD8DC")
    return img


# ── Emoji mapping: Unicode codepoint → icon generator ──
EMOJI_ICONS = {
    "\u2600": create_sun,       # ☀
    "\u2601": create_cloud,     # ☁
    "\u26c5": create_sun_cloud,  # ⛅
    "\u2614": create_umbrella,  # ☔
    "\u2744": create_snowflake, # ❄
    "\u26a1": create_lightning, # ⚡
    "\U0001F517": create_link,  # 🔗
}

# Weather code → best emoji icon
WEATHER_ICON = {
    0:  create_sun,
    1:  create_sun_cloud,
    2:  create_cloud,
    3:  create_cloud,
    45: create_cloud,
    48: create_cloud,
    51: create_umbrella,
    53: create_umbrella,
    55: create_umbrella,
    61: create_umbrella,
    63: create_umbrella,
    65: create_umbrella,
    71: create_snowflake,
    73: create_snowflake,
    75: create_snowflake,
    80: create_umbrella,
    81: create_umbrella,
    82: create_umbrella,
    85: create_snowflake,
    86: create_snowflake,
    95: create_lightning,
    96: create_lightning,
    99: create_lightning,
}


def get_weather_icon(weather_code: int, size=28):
    """Return a PIL Image for the given Open-Meteo weather code."""
    gen = WEATHER_ICON.get(weather_code, create_sun)
    return gen(size)


def get_emoji_image(char: str, size=28):
    """Return a PIL Image for the given emoji character."""
    gen = EMOJI_ICONS.get(char)
    if gen:
        return gen(size)
    return None


# Emoji character detection
import re
_EMOJI_PATTERN = re.compile(
    "[\u2600-\u26FF\u2700-\u27BF]"    # Misc Symbols + Dingbats
    "|\U0001F300-\U0001F9FF"           # Emoticons, etc
    "|\ufe0f"                           # VS16
)


def has_emoji(text: str) -> bool:
    return bool(_EMOJI_PATTERN.search(text))


def split_emoji(text: str) -> list:
    """Split text into list of (type, content) where type is 'text' or 'emoji'."""
    result = []
    pos = 0
    for m in _EMOJI_PATTERN.finditer(text):
        if m.start() > pos:
            result.append(("text", text[pos:m.start()]))
        char = m.group()
        if char != "\ufe0f":  # skip VS16
            result.append(("emoji", char))
        pos = m.end()
    if pos < len(text):
        result.append(("text", text[pos:]))
    return result
