#!/usr/bin/env python3
"""
Daily News Briefing — 全局配置文件
修改此文件即可调整各板块行为，无需改业务代码。
"""

from pathlib import Path

# Skill root — dynamic, no hardcoded path (used by FONTS fallback and path definitions)
SKILL_DIR = Path(__file__).parent.parent

# ═══════════════════════════════════════════════════════════
# 天气（支持多城市，依次展示）
# ═══════════════════════════════════════════════════════════

WEATHER = {
    "forecast_days": 3,          # 今天 + 未来 N-1 天
    "api_url": "https://api.open-meteo.com/v1/forecast",
    "request_timeout": 15,       # 秒
    "cities": [
        {"name": "北京", "latitude": 39.9042, "longitude": 116.4074, "timezone": "Asia/Shanghai"},
        # 添加更多城市示例（取消注释即可启用）：
        # {"name": "上海", "latitude": 31.2304, "longitude": 121.4737, "timezone": "Asia/Shanghai"},
        {"name": "深圳", "latitude": 22.5431, "longitude": 114.0579, "timezone": "Asia/Shanghai"},
        # {"name": "杭州", "latitude": 30.2741, "longitude": 120.1551, "timezone": "Asia/Shanghai"},
    ],
}

# WMO 天气代码 → 中文描述
WEATHER_CODE_MAP = {
    0:  "晴天",
    1:  "少云",
    2:  "多云",
    3:  "阴天",
    45: "雾",
    48: "霜雾",
    51: "小毛毛雨",
    53: "毛毛雨",
    55: "大毛毛雨",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    80: "阵雨",
    81: "中等阵雨",
    82: "强阵雨",
    85: "小阵雪",
    86: "大阵雪",
    95: "雷阵雨",
    96: "雷阵雨伴冰雹",
    99: "强雷阵雨伴冰雹",
}

# ═══════════════════════════════════════════════════════════
# GitHub Trending
# ═══════════════════════════════════════════════════════════

GITHUB_TRENDING = {
    "display_count": 10,
    "scrape_url": "https://github.com/trending",
    "description_max_chars": 120,
    "request_timeout": 15,
    "user_agent": "Mozilla/5.0",
}

# ═══════════════════════════════════════════════════════════
# AI 科技动态
# ═══════════════════════════════════════════════════════════

AI_NEWS = {
    "display_count": 10,
    "sources": [
        {"name": "36氪",    "url": "https://36kr.com"},
        {"name": "虎嗅",    "url": "https://huxiu.com"},
        {"name": "机器之心", "url": "https://jiqizhixin.com"},
        {"name": "量子位",   "url": "https://liangziwei.com"},
        {"name": "Hacker News",  "url": "https://news.ycombinator.com"},
        {"name": "TechCrunch",   "url": "https://techcrunch.com"},
        {"name": "The Verge",    "url": "https://theverge.com"},
    ],
}

# ═══════════════════════════════════════════════════════════
# 国内热点
# ═══════════════════════════════════════════════════════════

DOMESTIC_NEWS = {
    "display_count": 10,
    "sources": [
        {"name": "新华社",   "url": "https://xinhuanet.com"},
        {"name": "人民日报", "url": "https://people.cn"},
        {"name": "央视新闻", "url": "https://news.cctv.com"},
    ],
}

# ═══════════════════════════════════════════════════════════
# 卡片视觉
# ═══════════════════════════════════════════════════════════

CARD = {
    "width": 1200,
    "margin": 22,
    "padding": 55,
}

COLORS = {
    "bg":           "#F5EDE3",
    "card_bg":      "#FFFCF7",
    "card_shadow":  "#E8DDD2",
    "card_border":  "#E8D5C4",
    "accent":       "#E07B3C",
    "accent_light": "#FEF5EC",
    "accent_bg":    "#FDF2E9",
    "title":        "#3D2218",
    "body":         "#5D4037",
    "link":         "#C56A2E",
    "muted":        "#A08070",
    "divider":      "#F0E6DA",
    "footer":       "#C0A890",
    "accent_bar_segments": ["#E07B3C", "#E89050", "#F0A870"],
}

FONTS = {
    "bold":  "/System/Library/Fonts/STHeiti Medium.ttc",
    "light": "/System/Library/Fonts/STHeiti Light.ttc",
    # Cross-platform fallbacks (bundled open-source fonts)
    "fallback_bold": str(SKILL_DIR / "assets" / "fonts" / "NotoSansSC-Bold.otf"),
    "fallback_regular": str(SKILL_DIR / "assets" / "fonts" / "NotoSansSC-Regular.otf"),
    "sizes": {
        "title":       56,
        "subtitle":    22,
        "section":     32,
        "item_title":  26,
        "item_desc":   20,
        "item_cn":     19,
        "item_link":   16,
        "weather":     21,
        "weather_label": 21,
        "quote":       23,
        "quote_auth":  18,
        "footer":      16,
    },
}

# ═══════════════════════════════════════════════════════════
# 名言（优先从 API 动态获取，失败时回退到静态库）
# ═══════════════════════════════════════════════════════════

QUOTE_API = {
    "url": "https://zenquotes.io/api/today",  # 每日自动更换，免费无需 Key
    "request_timeout": 10,
    "enabled": True,            # False = 仅使用静态库
}

# 静态名言库（API 不可用时的 fallback）
QUOTES = [
    ("Stay hungry, stay foolish.", "Steve Jobs"),
    ("The only way to do great work is to love what you do.", "Steve Jobs"),
    ("Innovation distinguishes between a leader and a follower.", "Steve Jobs"),
    ("Design is not just what it looks like and feels like. Design is how it works.", "Steve Jobs"),
    ("The best way to predict the future is to invent it.", "Alan Kay"),
    ("Simplicity is the ultimate sophistication.", "Leonardo da Vinci"),
    ("First, solve the problem. Then, write the code.", "John Johnson"),
    ("Code is like humor. When you have to explain it, it's bad.", "Cory House"),
    ("Make it work, make it right, make it fast.", "Kent Beck"),
    ("Any fool can write code that a computer can understand. Good programmers write code that humans can understand.", "Martin Fowler"),
    ("The computer was born to solve problems that did not exist before.", "Bill Gates"),
    ("Technology is best when it brings people together.", "Matt Mullenweg"),
    ("It's not a bug — it's an undocumented feature.", "Anonymous"),
    ("Measuring programming progress by lines of code is like measuring aircraft building progress by weight.", "Bill Gates"),
    ("Talk is cheap. Show me the code.", "Linus Torvalds"),
    ("The advance of technology is based on making it fit in so that you don't really even notice it.", "Bill Gates"),
    ("Programs must be written for people to read, and only incidentally for machines to execute.", "Harold Abelson"),
    ("The most disastrous thing that you can ever learn is your first programming language.", "Alan Kay"),
    ("A language that doesn't affect the way you think about programming is not worth knowing.", "Alan Perlis"),
    ("There are two ways of constructing a software design: One way is to make it so simple that there are obviously no deficiencies.", "C.A.R. Hoare"),
]

# ═══════════════════════════════════════════════════════════
# 文件路径（一般不修改）
# ═══════════════════════════════════════════════════════════

PROJECT_DIR = SKILL_DIR
SRC_DIR = SKILL_DIR / "scripts"
CONFIG_DIR = SKILL_DIR / "config"
OUTPUT_DIR = SKILL_DIR / "output"
DATA_DIR = OUTPUT_DIR / "data"
DAILY_DIR = OUTPUT_DIR / "daily"
IMAGES_DIR = OUTPUT_DIR / "images"
SUMMARY_FILE = OUTPUT_DIR / "briefing-summary.md"
NEWS_INPUT_FILE = DATA_DIR / "news_input.json"

# ═══════════════════════════════════════════════════════════
# 其它
# ═══════════════════════════════════════════════════════════

# 北京时间
BEIJING_TZ = "Asia/Shanghai"

# URL 显示截断长度
URL_DISPLAY_MAX_LEN = 90

# 链接 emoji 图标尺寸（px）
LINK_ICON_SIZE = 16

# 天气 emoji 图标尺寸（px）
WEATHER_ICON_SIZE = 26
