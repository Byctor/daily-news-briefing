---
name: daily-news-briefing
description: Generate a warm-toned daily news briefing card image with multi-city weather, GitHub Trending, AI/tech news, domestic China news, and inspirational quotes. Use when the user wants to create a daily news digest, morning briefing, or news summary card in PNG format.
license: MIT
compatibility: Requires Python 3.9+, Pillow, requests, beautifulsoup4. Internet access required for API calls and news scraping.
metadata:
  author: byctor
  version: "2.0"
---

# Daily News Briefing

Generates a warm-toned card-style PNG image containing:

- Multi-city weather forecast (Open-Meteo API, no key required)
- GitHub Trending repositories (web scraping)
- AI/Tech news (RSS feeds, Hacker News API, Chinese tech sites)
- Domestic China news (xinhuanet, people.cn)
- Daily inspirational quote (ZenQuotes API with static fallback)

## Quick Start

Install dependencies and run:

```bash
pip install -r requirements.txt
python scripts/generate.py
```

Output files are written to `output/`:
- `output/images/YYYY-MM-DD.png` — Card image (primary output)
- `output/daily/YYYY-MM-DD.md` — Markdown version
- `output/daily/YYYY-MM-DD.html` — HTML version
- `output/briefing-summary.md` — Running summary with date index

## Configuration

Edit `config/settings.py` to customize behavior. Key sections:

| Section | What you can change |
|---------|-------------------|
| `WEATHER` | Cities (lat/lon/timezone), forecast days |
| `GITHUB_TRENDING` | Display count, scrape URL |
| `AI_NEWS` | Display count, news sources |
| `DOMESTIC_NEWS` | Display count, news sources |
| `CARD` | Card width, margins, padding |
| `COLORS` | Full color palette |
| `FONTS` | Font paths, sizes for every text element |
| `QUOTE_API` | API toggle, timeout |
| `QUOTES` | Static fallback quotes |

For a minimal starting config, see `assets/config.template.py`.

## Architecture

```
scripts/
├── generate.py       # Orchestrator: fetch data, supplement, render, save
├── render_card.py    # PIL-based card image renderer (dynamic height, no browser)
└── emoji_icons.py    # PIL-drawn weather/emoji icons (no external images)
```

The generation pipeline:
1. Fetch weather for all configured cities (Open-Meteo)
2. Load news from `output/data/news_input.json` if available
3. Supplement insufficient items from live sources:
   - GitHub: scrape trending page
   - AI: RSS feeds + Hacker News API + Chinese tech sites
   - Domestic: xinhuanet + people.cn article scraping
4. Fetch daily quote (ZenQuotes API → static fallback)
5. Generate Markdown, HTML, and PIL-rendered PNG card
6. Update running summary file

## Font Cross-Platform Support

This skill bundles Noto Sans SC (SIL Open Font License) in `assets/fonts/` for cross-platform Chinese text rendering. On macOS, system STHeiti fonts are tried first. On other platforms, the bundled Noto Sans SC fonts are used automatically.

## References

- [Design Specification](references/DESIGN_SPEC.md) — Visual design, content structure, data sources
- [Configuration Template](assets/config.template.py) — Minimal starting config
