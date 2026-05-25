#!/usr/bin/env python3
"""
Daily News Briefing — Minimal configuration template.
Copy this file to config/settings.py and customize as needed.
"""

from pathlib import Path

# Skill root (auto-detected, no need to change)
SKILL_DIR = Path(__file__).parent.parent if __file__ else Path.cwd()

# Weather
WEATHER = {
    "forecast_days": 3,
    "api_url": "https://api.open-meteo.com/v1/forecast",
    "request_timeout": 15,
    "cities": [
        {"name": "北京", "latitude": 39.9042, "longitude": 116.4074, "timezone": "Asia/Shanghai"},
        {"name": "深圳", "latitude": 22.5431, "longitude": 114.0579, "timezone": "Asia/Shanghai"},
    ],
}

WEATHER_CODE_MAP = {
    0: "晴天", 1: "少云", 2: "多云", 3: "阴天",
    45: "雾", 48: "霜雾",
    51: "小毛毛雨", 53: "毛毛雨", 55: "大毛毛雨",
    61: "小雨", 63: "中雨", 65: "大雨",
    71: "小雪", 73: "中雪", 75: "大雪",
    80: "阵雨", 81: "中等阵雨", 82: "强阵雨",
    85: "小阵雪", 86: "大阵雪",
    95: "雷阵雨", 96: "雷阵雨伴冰雹", 99: "强雷阵雨伴冰雹",
}

# GitHub Trending
GITHUB_TRENDING = {
    "display_count": 10,
    "scrape_url": "https://github.com/trending",
    "description_max_chars": 120,
    "request_timeout": 15,
    "user_agent": "Mozilla/5.0",
}

# AI News
AI_NEWS = {
    "display_count": 10,
    "sources": [
        {"name": "36氪", "url": "https://36kr.com"},
        {"name": "Hacker News", "url": "https://news.ycombinator.com"},
        {"name": "TechCrunch", "url": "https://techcrunch.com"},
        {"name": "The Verge", "url": "https://theverge.com"},
    ],
}

# Domestic News
DOMESTIC_NEWS = {
    "display_count": 10,
    "sources": [
        {"name": "新华社", "url": "https://xinhuanet.com"},
        {"name": "人民日报", "url": "https://people.cn"},
    ],
}

# Card dimensions
CARD = {"width": 1200, "margin": 22, "padding": 55}

# Color palette (warm tones)
COLORS = {
    "bg": "#F5EDE3", "card_bg": "#FFFCF7", "card_shadow": "#E8DDD2",
    "card_border": "#E8D5C4", "accent": "#E07B3C", "accent_light": "#FEF5EC",
    "accent_bg": "#FDF2E9", "title": "#3D2218", "body": "#5D4037",
    "link": "#C56A2E", "muted": "#A08070", "divider": "#F0E6DA",
    "footer": "#C0A890", "accent_bar_segments": ["#E07B3C", "#E89050", "#F0A870"],
}

# Fonts (macOS system fonts + bundled fallbacks)
FONTS = {
    "bold": "/System/Library/Fonts/STHeiti Medium.ttc",
    "light": "/System/Library/Fonts/STHeiti Light.ttc",
    "fallback_bold": str(SKILL_DIR / "assets" / "fonts" / "NotoSansSC-Bold.otf"),
    "fallback_regular": str(SKILL_DIR / "assets" / "fonts" / "NotoSansSC-Regular.otf"),
    "sizes": {
        "title": 56, "subtitle": 22, "section": 32, "item_title": 26,
        "item_desc": 20, "item_cn": 19, "item_link": 16, "weather": 21,
        "weather_label": 21, "quote": 23, "quote_auth": 18, "footer": 16,
    },
}

# Quote API
QUOTE_API = {
    "url": "https://zenquotes.io/api/today",
    "request_timeout": 10,
    "enabled": True,
}

# Static fallback quotes
QUOTES = [
    ("Stay hungry, stay foolish.", "Steve Jobs"),
    ("The only way to do great work is to love what you do.", "Steve Jobs"),
    ("Simplicity is the ultimate sophistication.", "Leonardo da Vinci"),
    ("First, solve the problem. Then, write the code.", "John Johnson"),
]

# Skill paths (auto-detected)
PROJECT_DIR = SKILL_DIR
SRC_DIR = SKILL_DIR / "scripts"
CONFIG_DIR = SKILL_DIR / "config"
OUTPUT_DIR = SKILL_DIR / "output"
DATA_DIR = OUTPUT_DIR / "data"
DAILY_DIR = OUTPUT_DIR / "daily"
IMAGES_DIR = OUTPUT_DIR / "images"
SUMMARY_FILE = OUTPUT_DIR / "briefing-summary.md"
NEWS_INPUT_FILE = DATA_DIR / "news_input.json"

# Other settings
BEIJING_TZ = "Asia/Shanghai"
URL_DISPLAY_MAX_LEN = 90
LINK_ICON_SIZE = 16
WEATHER_ICON_SIZE = 26
