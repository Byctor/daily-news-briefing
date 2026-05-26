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

## Extending News Sources

### Built-in (no Agent tools required)

The skill includes HTTP-based scrapers that work without any Agent-side web capabilities:

| Source | Method | Language |
|--------|--------|----------|
| GitHub Trending | `requests` + BeautifulSoup | EN → CN (MyMemory) |
| TechCrunch | RSS feed via `xml.etree` | EN |
| The Verge | RSS feed via `xml.etree` | EN |
| Hacker News | Firebase REST API | EN |
| 36kr | Article page scraping (meta description) | CN |
| Xinhuanet | Article page scraping | CN |
| People's Daily | Article page scraping (GB2312) | CN |

These work out of the box after `pip install -r requirements.txt` — the Agent needs no web-search API key or CDP browser.

### Agent-side pre-fill (for blocked sources)

Some Chinese tech sites use WAF/CAPTCHA or JS rendering and cannot be scraped with plain HTTP. To include them:

1. Use your Agent's web-search / CDP browser capability to collect articles
2. Write results to `output/data/news_input.json` in this format:
```json
{
  "github_trending": [],
  "ai_news": [
    {"title": "...", "description": "...", "url": "..."}
  ],
  "domestic_news": [
    {"title": "...", "description": "...", "url": "..."}
  ]
}
```
3. Run `python scripts/generate.py` — it reads this file first and only supplements what's missing

Example prompt for your Agent:
```
Collect today's top 5 AI news from huxiu.com, then save to
output/data/news_input.json and run python scripts/generate.py
```

This two-path design keeps the skill self-contained for the common case, while allowing richer sources when the Agent has advanced networking tools.

## Translation Fallback

GitHub Trending descriptions are translated from English to Chinese via the free [MyMemory](https://mymemory.translated.net/) API. MyMemory has a daily quota (~500 requests/day), and when exhausted, translations will be empty.

When this happens, `generate.py` writes `output/data/translate_backlog.json`:

```json
[
  {"index": 0, "name": "owner/repo", "text": "English description...", "cn": ""}
]
```

**The Agent must handle this automatically:**

1. After running `generate.py`, check if `output/data/translate_backlog.json` exists
2. If it does, read the file, translate each `"text"` field to Simplified Chinese
3. Write the translation back into the `"cn"` field of each entry
4. Re-run `python scripts/generate.py` — it will automatically apply the translations and delete the backlog file

This fallback uses the Agent's own LLM capability, requiring no external API key. The backlog file is self-describing: any Agent can understand the format and complete the translation task.

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
