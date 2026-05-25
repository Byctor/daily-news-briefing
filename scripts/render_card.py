#!/usr/bin/env python3
"""
PIL-based card renderer for daily news briefing.
Pure Python, no browser dependency. Generates warm-toned card PNG.

v2.0 - Part of daily-news-briefing Agent Skill.
"""

import os
import sys
from pathlib import Path

SKILL_DIR = Path(os.environ.get("CLAUDE_SKILL_DIR", str(Path(__file__).parent.parent)))
sys.path.insert(0, str(SKILL_DIR))

from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timezone, timedelta
from scripts.emoji_icons import (
    get_weather_icon, get_emoji_image, split_emoji,
    EMOJI_ICONS, WEATHER_ICON
)
from config import (
    CARD, COLORS, FONTS, LINK_ICON_SIZE,
    WEATHER_ICON_SIZE, URL_DISPLAY_MAX_LEN, BEIJING_TZ,
)

# Timezone
import zoneinfo
try:
    _tz = zoneinfo.ZoneInfo(BEIJING_TZ)
except Exception:
    _tz = timezone(timedelta(hours=8))


def load_font(size, bold=False):
    path = FONTS["bold"] if bold else FONTS["light"]
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        fallback = FONTS["fallback_bold"] if bold else FONTS["fallback_regular"]
        try:
            return ImageFont.truetype(fallback, size)
        except Exception:
            return ImageFont.load_default()


def draw_emoji_inline(draw, img, char, x, y, emoji_size):
    """Paste a single emoji icon inline at (x, y) and return its width."""
    icon = get_emoji_image(char, emoji_size)
    if icon:
        # Center vertically relative to text baseline
        # PillowImageDraw text y is top of text, emoji should align with text
        paste_y = y - 2  # slight adjustment for visual alignment
        img.paste(icon, (x, paste_y), icon)  # use alpha mask
        return emoji_size
    return 0


def draw_text_with_emoji(draw, img, text, x, y, font, color, emoji_size):
    """Draw text with inline emoji icons. Returns x position after drawing.

    Text containing emoji characters (☀☁☔❄⚡) will have those replaced
    with colorful PIL-drawn icons pasted inline.
    """
    segments = split_emoji(text)
    cur_x = x
    for typ, content in segments:
        if typ == "text":
            draw.text((cur_x, y), content, fill=color, font=font)
            bbox = draw.textbbox((0, 0), content, font=font)
            cur_x += bbox[2] - bbox[0]
        elif typ == "emoji":
            w = draw_emoji_inline(draw, img, content, cur_x, y, emoji_size)
            cur_x += w + 2  # small gap after emoji
    return cur_x


def wrap_text(draw, text, max_width, font):
    if not text:
        return []
    lines = []
    current = ""
    for char in text:
        test = current + char
        w = draw.textbbox((0, 0), test, font=font)[2]
        if w > max_width:
            if current:
                lines.append(current)
            current = char
        else:
            current = test
    if current:
        lines.append(current)
    return lines


def draw_wrapped(draw, text, x, y, max_width, font, color, line_h):
    for line in wrap_text(draw, text, max_width, font):
        draw.text((x, y), line, fill=color, font=font)
        y += line_h
    return y


def draw_shadow_card(draw, x, y, w, h):
    """Rounded card with shadow and border."""
    draw.rounded_rectangle([x + 3, y + 3, x + w + 3, y + h + 3], radius=20, fill=COLORS["card_shadow"])
    draw.rounded_rectangle([x, y, x + w, y + h], radius=20, fill=COLORS["card_bg"])
    draw.rounded_rectangle([x, y, x + w, y + h], radius=20, outline=COLORS["card_border"], width=1)


def render_card(weather, trending, ai_news, domestic_news, quote, output_path: Path):
    today = datetime.now(_tz)
    month_day = f"{today.month}月{today.day}日"
    date_str = today.strftime("%Y年%m月%d日")

    # ── Layout ──
    IMG_W = CARD["width"]
    MARGIN = CARD["margin"]
    PAD = CARD["padding"]
    CARD_X = MARGIN
    CARD_Y = MARGIN
    CARD_W = IMG_W - 2 * MARGIN
    CONTENT_W = CARD_W - 2 * PAD

    # ── Fonts ──
    fs = FONTS["sizes"]
    f_title = load_font(fs["title"], bold=True)
    f_sub = load_font(fs["subtitle"], bold=False)
    f_section = load_font(fs["section"], bold=True)
    f_item_title = load_font(fs["item_title"], bold=True)
    f_item_desc = load_font(fs["item_desc"], bold=False)
    f_item_cn = load_font(fs["item_cn"], bold=False)
    f_item_link = load_font(fs["item_link"], bold=False)
    f_wx = load_font(fs["weather"], bold=False)
    f_wx_label = load_font(fs["weather_label"], bold=True)
    f_quote = load_font(fs["quote"], bold=False)
    f_quote_auth = load_font(fs["quote_auth"], bold=True)
    f_footer = load_font(fs["footer"], bold=False)

    # ── Render to oversized canvas, crop to actual height at end ──
    MAX_H = 12000
    img = Image.new("RGB", (IMG_W, MAX_H), COLORS["bg"])
    draw = ImageDraw.Draw(img)

    # Draw card background with generous height (will be cropped later)
    draw_shadow_card(draw, CARD_X, CARD_Y, CARD_W, MAX_H - 2 * MARGIN)

    y = CARD_Y + PAD

    # ── Title ──
    title_text = f"{month_day}热点速览精选"
    tw = draw.textbbox((0, 0), title_text, font=f_title)[2]
    draw.text(((IMG_W - tw) // 2, y), title_text, fill=COLORS["title"], font=f_title)
    y += 70

    # ── Subtitle ──
    sub = f"{date_str} · 每日新闻简报"
    sw = draw.textbbox((0, 0), sub, font=f_sub)[2]
    draw.text(((IMG_W - sw) // 2, y), sub, fill=COLORS["muted"], font=f_sub)
    y += 28

    # ── Accent bar ──
    bar_w = 220
    bar_x = (IMG_W - bar_w) // 2
    bar_y = y + 8
    segments = COLORS["accent_bar_segments"]
    for i, c in enumerate(segments):
        draw.rectangle([bar_x + i * 3, bar_y, bar_x + i * 3 + 3, bar_y + 6], fill=c)
    draw.rectangle([bar_x + 9, bar_y, bar_x + bar_w - 9, bar_y + 6], fill=COLORS["accent"])
    y += 34

    # ── Helpers ──
    def section_header(text, y_pos):
        hdr_h = 56
        draw.rounded_rectangle(
            [CARD_X + PAD - 4, y_pos, CARD_X + CARD_W - PAD + 4, y_pos + hdr_h],
            radius=12, fill=COLORS["accent_light"]
        )
        tw = draw.textbbox((0, 0), text, font=f_section)[2]
        draw.text(((IMG_W - tw) // 2, y_pos + 10), text, fill=COLORS["title"], font=f_section)
        return y_pos + hdr_h + 18

    def draw_items(items, y_pos, show_trans=False):
        item_pad = CARD_X + PAD
        for i, item in enumerate(items, 1):
            num = f"{i:02d}."
            nw = draw.textbbox((0, 0), num, font=f_item_title)[2]
            draw.text((item_pad, y_pos), num, fill=COLORS["accent"], font=f_item_title)

            title = item.get("title", item.get("name", ""))
            max_tw = CONTENT_W - nw - 4
            line = f" {title}"
            while draw.textbbox((0, 0), line, font=f_item_title)[2] > max_tw and len(title) > 3:
                title = title[:-1]
                line = f" {title}..."
            draw.text((item_pad + nw + 2, y_pos), line, fill=COLORS["title"], font=f_item_title)
            y_pos += 34

            # Language/stars tag (for GitHub)
            if show_trans:
                tags = []
                if item.get("language"):
                    tags.append(item["language"])
                if item.get("stars_today"):
                    tags.append(item["stars_today"])
                if tags:
                    draw.text((item_pad + nw + 2, y_pos), " · ".join(tags), fill="#8B6B4A", font=f_item_link)
                    y_pos += 22

            # English description (original)
            desc = item.get("description", "")
            if desc:
                y_pos = draw_wrapped(draw, desc, item_pad + nw + 2, y_pos, CONTENT_W - nw - 2, f_item_desc, COLORS["body"], 26)
                y_pos += 2

            # Chinese translation line
            desc_cn = item.get("description_cn", "")
            if desc_cn:
                cn_text = desc_cn
                y_pos = draw_wrapped(draw, cn_text, item_pad + nw + 2, y_pos, CONTENT_W - nw - 2, f_item_cn, COLORS["muted"], 26)
                y_pos += 2

            # URL
            url = item.get("url", "")
            if url:
                url_text = url if len(url) < URL_DISPLAY_MAX_LEN else url[:URL_DISPLAY_MAX_LEN - 3] + "..."
                link_icon = get_emoji_image("\U0001F517", LINK_ICON_SIZE)
                if link_icon:
                    img.paste(link_icon, (item_pad + nw + 2, y_pos + 3), link_icon)
                    draw.text((item_pad + nw + 2 + LINK_ICON_SIZE + 4, y_pos), url_text, fill=COLORS["link"], font=f_item_link)
                else:
                    draw.text((item_pad + nw + 2, y_pos), url_text, fill=COLORS["link"], font=f_item_link)
                y_pos += 22

            # Divider
            y_pos += 4
            draw.line([(item_pad + 30, y_pos), (CARD_X + CARD_W - PAD - 30, y_pos)], fill=COLORS["divider"], width=1)
            y_pos += 16

        return y_pos

    # ── Weather ──
    wx_pad = CARD_X + PAD
    wx_content_w = CONTENT_W - 24  # available width inside weather block
    emoji_s = WEATHER_ICON_SIZE
    cities = weather.get("cities", [weather])

    # Pre-calc day entry width for wrapping
    def day_entry_width(day_text):
        w = emoji_s + 4  # icon + gap
        w += draw.textbbox((0, 0), day_text, font=f_wx)[2]
        w += draw.textbbox((0, 0), "  ·  ", font=f_wx)[2]  # separator
        return w

    # Render each city with line-wrapping
    for ci, city_data in enumerate(cities):
        city_name = city_data.get("name", city_data.get("city", ""))
        days = city_data["days"]

        # Build day segments for layout
        day_segs = []
        for di, d in enumerate(days):
            date_label = d.get("date_display", d.get("date", d["label"]))
            t = f"{int(round(d['temp_min']))}~{int(round(d['temp_max']))}°C"
            day_segs.append((d["weather_code"], f"{date_label} {t}"))

        # Layout days into lines
        lines = []
        cur_line = []
        cur_w = 0
        for wi, (wcode, wtext) in enumerate(day_segs):
            seg_w = emoji_s + 4 + draw.textbbox((0, 0), wtext, font=f_wx)[2]
            if wi < len(day_segs) - 1:
                seg_w += draw.textbbox((0, 0), "  ·  ", font=f_wx)[2]
            if cur_line and cur_w + seg_w > wx_content_w:
                lines.append(cur_line)
                cur_line = [(wcode, wtext, wi)]
                cur_w = seg_w
            else:
                cur_line.append((wcode, wtext, wi))
                cur_w += seg_w

        if cur_line:
            lines.append(cur_line)

        num_lines = len(lines)
        wx_h = 32 + num_lines * 28 + 16  # label + day lines + padding

        draw.rounded_rectangle(
            [wx_pad - 4, y, CARD_X + CARD_W - PAD + 4, y + wx_h],
            radius=10, fill=COLORS["accent_bg"]
        )
        draw.text((wx_pad + 12, y + 8), f"{city_name}天气", fill=COLORS["accent"], font=f_wx_label)

        for li, line in enumerate(lines):
            lx = wx_pad + 12
            ly = y + 38 + li * 28
            for wi, (wcode, wtext, day_idx) in enumerate(line):
                icon = get_weather_icon(wcode, emoji_s)
                if icon:
                    img.paste(icon, (lx, ly - 2), icon)
                    lx += emoji_s + 4
                draw.text((lx, ly), wtext, fill=COLORS["body"], font=f_wx)
                lx += draw.textbbox((0, 0), wtext, font=f_wx)[2]
                if wi < len(line) - 1:
                    sep = "  ·  "
                    draw.text((lx, ly), sep, fill=COLORS["muted"], font=f_wx)
                    lx += draw.textbbox((0, 0), sep, font=f_wx)[2]

        y += wx_h + 8

    y += 14  # gap after weather block

    # ── Sections ──
    y = section_header("—— GitHub Trending ——", y)
    y = draw_items(trending, y, show_trans=True)

    y = section_header("—— AI 科技动态 ——", y)
    y = draw_items(ai_news, y)

    y = section_header("—— 国内热点 ——", y)
    y = draw_items(domestic_news, y)

    # ── Quote ──
    y += 18
    q_pad = CARD_X + PAD
    q_text_w = CONTENT_W - 80  # available for quote text (wider margin)
    q_lines = wrap_text(draw, f"「{quote[0]}」", q_text_w, f_quote)
    q_text_h = len(q_lines) * 32  # 32px line height for 23px font
    q_h = q_text_h + 72  # text + author line + generous padding
    draw.rounded_rectangle([q_pad - 4, y, CARD_X + CARD_W - PAD + 4, y + q_h], radius=14, fill=COLORS["accent_bg"])
    draw.rectangle([q_pad - 4, y, q_pad + 4, y + q_h], fill=COLORS["accent"])
    for li, line in enumerate(q_lines):
        draw.text((q_pad + 18, y + 20 + li * 32), line, fill=COLORS["title"], font=f_quote)
    auth = f"—— {quote[1]}"
    aw = draw.textbbox((0, 0), auth, font=f_quote_auth)[2]
    draw.text((CARD_X + CARD_W - PAD - aw - 16, y + q_h - 32), auth, fill=COLORS["muted"], font=f_quote_auth)
    y += q_h + 24

    # ── Footer ──
    ft = "Daily News Briefing · Auto-generated"
    fw = draw.textbbox((0, 0), ft, font=f_footer)[2]
    draw.text(((IMG_W - fw) // 2, y), ft, fill=COLORS["footer"], font=f_footer)
    y += 40  # footer height + spacing

    # ── Crop to actual content height ──
    total_h = y + PAD + MARGIN
    img = img.crop((0, 0, IMG_W, total_h))

    # Save
    img.save(output_path, "PNG", optimize=True)
    return True
