# Daily News Briefing — Design Specification

> Version: 2.0 | Updated: 2026-05-25

## Overview

Generate a warm-toned card-style daily news briefing image. This is a standalone Agent Skill — scheduling and delivery are handled by the external agent that invokes it.

## Content Structure

### 1. Header — Super Large Title
Format: `X月X日热点速览精选`
- Font: Extra bold, largest on the card
- Color: Dark warm tone (#3D2218)

### 2. Weather Section
- Multi-city support with dynamic forecast days
- Data: Open-Meteo API (free, no key)
- Display: Weather icons, condition text, temperature range per day

### 3. GitHub Trending (Top N, configurable)
Section header: `—— GitHub Trending ——`
- Format: Numbered, project name, description, language tag, stars, link
- Source: github.com/trending (web scraping)

### 4. AI & Tech News (Top N, configurable)
Section header: `—— AI 科技动态 ——`
- Format: Numbered, headline, description, original article link
- Sources: 36Kr, Hacker News, TechCrunch, The Verge (RSS + API + scraping)

### 5. Domestic Hot News (Top N, configurable)
Section header: `—— 国内热点 ——`
- Format: Numbered, headline, description, original article link
- Sources: Xinhua News Agency, People's Daily (article page scraping)

### 6. Footer — Famous Quote
Format: `「Quote text」 —— Author`
- Priority: ZenQuotes API daily quote, fallback to static curated library

## Real-time Supplement Logic

When JSON input data is insufficient to meet the configured `display_count`, the skill automatically supplements from live sources:
- **GitHub**: Scrapes the trending page directly
- **AI News**: RSS feeds (TechCrunch, The Verge) for rich descriptions, Hacker News API for popularity signals, 36Kr for Chinese tech news
- **Domestic News**: Xinhuanet and People's Daily article pages with meta description extraction and first-paragraph fallback

## Visual Design

### Color Palette (Warm Tones)
| Element | Hex |
|---------|-----|
| Background | #F5EDE3 |
| Card background | #FFFCF7 |
| Card shadow | #E8DDD2 |
| Card border | #E8D5C4 |
| Primary accent | #E07B3C |
| Title text | #3D2218 |
| Body text | #5D4037 |
| Link text | #C56A2E |
| Section header bg | #FEF5EC |
| Divider | #F0E6DA |

### Card Style
- Rounded corners, subtle shadow
- Dynamic height (renders to oversized canvas, crops to actual content)
- PIL/Pillow rendering — no browser dependency
- Clear visual hierarchy with font sizes

## Output

### File Structure
```
output/
├── images/
│   └── YYYY-MM-DD.png      # Card image (primary output)
├── daily/
│   ├── YYYY-MM-DD.md       # Markdown version
│   └── YYYY-MM-DD.html     # HTML version
├── data/
│   └── news_input.json     # Optional pre-collected news input
└── briefing-summary.md     # Running summary with date index
```

### Summary Document Format
- New entries appended at top
- Format: `## YYYY-MM-DD` + content + `---` separator
- Index at top linking to each day's entry

## Data Sources

| Data | Source | Method |
|------|--------|--------|
| Weather | Open-Meteo API | requests |
| GitHub Trending | github.com/trending | BeautifulSoup scraping |
| AI News | Hacker News API, RSS feeds, 36Kr | requests + scraping |
| Domestic News | news.cn, people.cn | requests + article scraping |
| Quotes | ZenQuotes API + static fallback | requests |

## Changelog
- v2.0 (2026-05-25): Converted to Agent Skill SPEC. Removed scheduling/delivery concerns, updated file structure, documented supplement logic.
- v1.0 (2026-05-25): Initial design — warm card style, Open-Meteo weather, multi-section news
