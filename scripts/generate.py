#!/usr/bin/env python3
"""
Daily News Briefing Generator
Fetches weather, GitHub Trending, generates styled HTML and PNG image.
Part of the daily-news-briefing Agent Skill.

Image rendering: PIL (no browser dependency).
"""

import json
import os
import random
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
import zoneinfo

# Skill root directory — respects CLAUDE_SKILL_DIR env var, falls back to relative
SKILL_DIR = Path(os.environ.get("CLAUDE_SKILL_DIR", str(Path(__file__).parent.parent)))
sys.path.insert(0, str(SKILL_DIR))

# Import PIL renderer
from scripts.render_card import render_card as pil_render_card

# Import config
from config import (
    PROJECT_DIR, DATA_DIR, DAILY_DIR, IMAGES_DIR, SUMMARY_FILE, NEWS_INPUT_FILE,
    WEATHER, WEATHER_CODE_MAP, GITHUB_TRENDING, AI_NEWS, DOMESTIC_NEWS,
    COLORS, QUOTES, QUOTE_API, BEIJING_TZ,
)

try:
    _tz = zoneinfo.ZoneInfo(BEIJING_TZ)
except Exception:
    _tz = timezone(timedelta(hours=8))


# ── Weather ─────────────────────────────────────────────
def fetch_weather_for_city(city: dict) -> dict:
    """Fetch weather for a single city from Open-Meteo."""
    days = WEATHER["forecast_days"]
    url = (
        f"{WEATHER['api_url']}"
        f"?latitude={city['latitude']}&longitude={city['longitude']}"
        f"&daily=temperature_2m_max,temperature_2m_min,weathercode"
        f"&timezone={city['timezone']}&forecast_days={days}"
    )
    resp = requests.get(url, timeout=WEATHER["request_timeout"])
    resp.raise_for_status()
    data = resp.json()

    daily = data["daily"]
    day_list = []

    for i in range(days):
        code = daily["weathercode"][i]
        t_max = daily["temperature_2m_max"][i]
        t_min = daily["temperature_2m_min"][i]
        date_str = daily["time"][i]
        try:
            parts = date_str.split("-")
            date_display = f"{int(parts[1])}月{int(parts[2])}日"
        except Exception:
            date_display = date_str
        desc = WEATHER_CODE_MAP.get(code, f"天气代码{code}")
        day_list.append({
            "label": date_display,
            "date": date_str,
            "date_display": date_display,
            "weather": desc,
            "weather_code": code,
            "temp_max": t_max,
            "temp_min": t_min,
        })

    return {"name": city["name"], "days": day_list}


def fetch_weather() -> dict:
    """Fetch weather for all configured cities."""
    cities_data = []
    for city in WEATHER["cities"]:
        try:
            data = fetch_weather_for_city(city)
            cities_data.append(data)
            first = data["days"][0]
            print(f"   ✅ {city['name']}: {first['weather']} {first['temp_min']}~{first['temp_max']}°C")
        except Exception as e:
            print(f"   ⚠️  {city['name']} weather failed: {e}")
            # Fallback for this city
            fd = WEATHER["forecast_days"]
            cities_data.append({
                "name": city["name"],
                "days": [{"label": "--月--日", "date": "N/A", "date_display": "--月--日",
                          "weather": "获取失败", "weather_code": 0,
                          "temp_max": "--", "temp_min": "--"}
                         for _ in range(fd)]
            })
    return {"cities": cities_data}


# ── Quote ──────────────────────────────────────────────
def fetch_quote() -> tuple:
    """Fetch daily quote from API, fallback to static library."""
    if not QUOTE_API.get("enabled", True):
        return random.choice(QUOTES)

    try:
        resp = requests.get(QUOTE_API["url"], timeout=QUOTE_API["request_timeout"])
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list) and len(data) > 0:
            q = data[0].get("q", "").strip()
            a = data[0].get("a", "").strip()
            if q and a:
                return (q, a)
    except Exception as e:
        print(f"   ⚠️  Quote API failed: {e}, using static fallback")

    return random.choice(QUOTES)


# ── GitHub Trending ─────────────────────────────────────
def _translate_to_cn(text: str) -> str:
    """Translate English text to Chinese via MyMemory free API."""
    if not text or len(text) < 10:
        return ""
    try:
        url = "https://api.mymemory.translated.net/get"
        resp = requests.get(url, params={"q": text[:500], "langpair": "en|zh-CN"}, timeout=8)
        data = resp.json()
        translated = data.get("responseData", {}).get("translatedText", "")
        if translated and translated != text:
            return translated
    except Exception:
        pass
    return ""


def fetch_github_trending() -> list:
    """Scrape GitHub Trending page."""
    url = GITHUB_TRENDING["scrape_url"]
    headers = {"User-Agent": GITHUB_TRENDING["user_agent"], "Accept": "text/html"}
    resp = requests.get(url, headers=headers, timeout=GITHUB_TRENDING["request_timeout"])

    repos = []
    if resp.status_code != 200:
        return repos

    from bs4 import BeautifulSoup
    max_items = GITHUB_TRENDING["display_count"]
    soup = BeautifulSoup(resp.text, "html.parser")
    articles = soup.find_all("article", class_="Box-row")[:max_items]

    for article in articles:
        h2 = article.find("h2", class_="h3")
        if not h2:
            continue
        name = h2.get_text(strip=True).replace("\n", "").replace(" ", "")
        name = " ".join(name.split())

        desc_p = article.find("p", class_="col-9")
        desc = desc_p.get_text(strip=True) if desc_p else ""

        lang_el = article.find("span", itemprop="programmingLanguage")
        lang = lang_el.get_text(strip=True) if lang_el else ""

        stars_el = article.find("span", class_="d-inline-block float-sm-right")
        stars = stars_el.get_text(strip=True) if stars_el else ""

        repo_url = f"https://github.com/{name}"

        max_desc = GITHUB_TRENDING["description_max_chars"]
        desc_text = desc[:max_desc] if desc else ""
        repos.append({
            "name": name,
            "url": repo_url,
            "description": desc_text,
            "description_cn": _translate_to_cn(desc_text) if desc_text else "",
            "language": lang,
            "stars_today": stars,
        })

    return repos[:max_items]


# ── AI News Live Scraping ─────────────────────────────────

def _scrape_hacker_news(count: int) -> list:
    """Fetch top stories from Hacker News Firebase API."""
    items = []
    try:
        resp = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10
        )
        resp.raise_for_status()
        ids = resp.json()[: min(count * 3, 30)]
        for item_id in ids:
            if len(items) >= count:
                break
            try:
                detail = requests.get(
                    f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json",
                    timeout=5,
                ).json()
                title = detail.get("title", "")
                url = detail.get("url", "")
                if not url or url.startswith("item?"):
                    url = f"https://news.ycombinator.com/item?id={item_id}"
                score = detail.get("score", 0)
                descendants = detail.get("descendants", 0)
                desc_parts = []
                if score:
                    desc_parts.append(f"Score: {score}")
                if descendants:
                    desc_parts.append(f"Comments: {descendants}")
                if title:
                    items.append({
                        "title": title,
                        "description": " | ".join(desc_parts) if desc_parts else "",
                        "url": url,
                    })
            except Exception:
                continue
    except Exception as e:
        print(f"      HN API: {e}")
    return items


def _scrape_rss_feeds(count: int) -> list:
    """Try RSS feeds from TechCrunch and The Verge."""
    import xml.etree.ElementTree as ET

    items = []
    feeds = [
        "https://techcrunch.com/feed/",
        "https://www.theverge.com/rss/index.xml",
    ]
    headers = {"User-Agent": "Mozilla/5.0"}

    for feed_url in feeds:
        if len(items) >= count:
            break
        try:
            resp = requests.get(feed_url, headers=headers, timeout=10)
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
            for item in root.iter("item"):
                title_el = item.find("title")
                link_el = item.find("link")
                desc_el = item.find("description")
                if title_el is not None and title_el.text:
                    desc_text = ""
                    if desc_el is not None and desc_el.text:
                        from bs4 import BeautifulSoup
                        desc_text = BeautifulSoup(desc_el.text, "html.parser").get_text()[:200]
                    items.append({
                        "title": title_el.text.strip(),
                        "description": desc_text,
                        "url": link_el.text.strip() if link_el is not None and link_el.text else "",
                    })
                    if len(items) >= count:
                        break
        except Exception as e:
            print(f"      RSS {feed_url}: {e}")
            continue
    return items


def _scrape_cn_tech(count: int) -> list:
    """Scrape Chinese tech news sites with descriptions.

    Only sources that work with plain HTTP requests are included.
    Sites requiring JS rendering or blocked by WAF are excluded —
    use news_input.json pre-fill or Agent-side tools for those.
    """
    items = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml",
    }

    # 36kr newsflashes — collect titles then fetch articles for descriptions
    from bs4 import BeautifulSoup
    import html as html_mod
    import re
    try:
        resp = requests.get("https://36kr.com/newsflashes", headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        raw_36kr = []
        seen = set()
        for a in soup.select("a[href*='/newsflashes/'], a[href*='/p/']"):
            title = a.get_text(strip=True)
            href = a.get("href", "")
            if title and len(title) > 6 and title not in seen:
                seen.add(title)
                url = "https://36kr.com" + href if href.startswith("/") else href
                raw_36kr.append({"title": title, "url": url})

        # Fetch article pages for descriptions (first N only)
        for item in raw_36kr:
            if len(items) >= count:
                break
            desc = ""
            try:
                ar = requests.get(item["url"], headers=headers, timeout=8)
                match = re.search(
                    r'<meta[^>]*name="description"[^>]*content="([^"]+)"',
                    ar.text[:50000],
                )
                if match:
                    raw_desc = html_mod.unescape(match.group(1).strip())
                    raw_desc = re.sub(r'\s*[-|–—]\s*$', '', raw_desc)
                    raw_desc = raw_desc.strip()
                    if raw_desc and len(raw_desc) > len(item["title"]):
                        desc = raw_desc
            except Exception:
                pass
            items.append({
                "title": item["title"],
                "description": desc[:200],
                "url": item["url"],
            })
        print(f"      36kr: {len(items)} items")
    except Exception as e:
        print(f"      36kr: {e}")

    return items


def fetch_ai_news_live(count: int) -> list:
    """Live-fetch AI/tech news from multiple sources to supplement JSON data.
    Distributes across sources for diverse, high-quality items with descriptions."""
    all_items = []
    per_source = max(3, count // 3)  # Take ~1/3 from each source type

    # Source 1: RSS feeds first (best descriptions)
    rss = _scrape_rss_feeds(per_source)
    all_items.extend(rss)
    print(f"      RSS feeds: {len(rss)} items")

    # Source 2: Hacker News (popularity signals)
    if len(all_items) < count:
        hn = _scrape_hacker_news(per_source)
        all_items.extend(hn)
        print(f"      Hacker News: {len(hn)} items")

    # Source 3: Chinese tech sites
    if len(all_items) < count:
        cn = _scrape_cn_tech(count - len(all_items))
        all_items.extend(cn)
        print(f"      Chinese tech: {len(cn)} items")

    return all_items[:count]


# ── Domestic News Live Scraping ────────────────────────────

def _scrape_xinhuanet(count: int) -> list:
    """Scrape xinhuanet.com headlines with descriptions from article pages."""
    import re
    items = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "text/html",
    }
    from bs4 import BeautifulSoup

    # Step 1: Collect titles from listing pages
    raw_items = []
    seen = set()
    for url in ["https://www.news.cn/politics/", "https://www.news.cn/"]:
        if len(raw_items) >= count * 2:
            break
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.select("a[href*='/']"):
                title = a.get_text(strip=True)
                href = a.get("href", "")
                if title and len(title) > 10 and title not in seen and "/2026" in href:
                    seen.add(title)
                    url_full = href if href.startswith("http") else "https://www.news.cn" + href
                    raw_items.append({"title": title, "url": url_full})
        except Exception:
            continue

    # Step 2: Fetch article pages for descriptions (limited to avoid too many requests)
    import html as html_mod
    for item in raw_items[:count]:
        desc = ""
        try:
            resp = requests.get(item["url"], headers=headers, timeout=8)
            text = resp.text[:20000]

            # Try meta description
            match = re.search(
                r'<meta[^>]*name="description"[^>]*content="([^"]+)"',
                text,
            )
            if match:
                raw_desc = html_mod.unescape(match.group(1).strip())
                raw_desc = re.sub(r'\s*[-|–—]\s*$', '', raw_desc)
                raw_desc = raw_desc.strip()
                # Accept if it has more content than just the title
                if raw_desc and raw_desc != item["title"] and len(raw_desc) > len(item["title"]):
                    desc = raw_desc

            # Fallback: first meaningful paragraph
            if not desc:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(text, "html.parser")
                for p in soup.find_all("p"):
                    ptext = p.get_text(strip=True)
                    if len(ptext) > 30 and ptext != item["title"]:
                        desc = ptext
                        break
        except Exception:
            pass
        items.append({
            "title": item["title"],
            "description": desc[:200],
            "url": item["url"],
        })
        if len(items) >= count:
            break

    return items


def _scrape_people_cn(count: int) -> list:
    """Scrape people.com.cn headlines with descriptions from article pages."""
    import re
    items = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "text/html",
    }
    from bs4 import BeautifulSoup

    # Step 1: Collect titles from listing page
    raw_items = []
    seen = set()
    try:
        resp = requests.get("https://www.people.com.cn/", headers=headers, timeout=10)
        resp.raise_for_status()
        resp.encoding = "gb2312"
        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.find_all("a"):
            title = a.get_text(strip=True)
            href = a.get("href", "")
            if title and len(title) > 10 and title not in seen:
                seen.add(title)
                url_full = href if href.startswith("http") else "https://www.people.com.cn" + href
                raw_items.append({"title": title, "url": url_full})
                if len(raw_items) >= count * 2:
                    break
    except Exception as e:
        print(f"      人民网 listing: {e}")

    # Step 2: Fetch article pages for descriptions
    import html as html_mod
    for item in raw_items[:count]:
        desc = ""
        try:
            resp = requests.get(item["url"], headers=headers, timeout=8)
            text = resp.text[:20000]

            # Try meta description
            match = re.search(
                r'<meta[^>]*name="description"[^>]*content="([^"]+)"',
                text,
            )
            if match:
                raw_desc = html_mod.unescape(match.group(1).strip())
                raw_desc = re.sub(r'\s*[-|–—]\s*$', '', raw_desc)
                raw_desc = raw_desc.strip()
                if raw_desc and raw_desc != item["title"] and len(raw_desc) > len(item["title"]):
                    desc = raw_desc

            # Fallback: first meaningful paragraph
            if not desc:
                soup = BeautifulSoup(text, "html.parser")
                for p in soup.find_all("p"):
                    ptext = p.get_text(strip=True)
                    if len(ptext) > 30 and ptext != item["title"]:
                        desc = ptext
                        break
        except Exception:
            pass
        items.append({
            "title": item["title"],
            "description": desc[:200],
            "url": item["url"],
        })
        if len(items) >= count:
            break

    return items


def fetch_domestic_news_live(count: int) -> list:
    """Live-fetch domestic news to supplement insufficient JSON data."""
    all_items = []

    xh = _scrape_xinhuanet(count)
    all_items.extend(xh)
    print(f"      新华社: {len(xh)} items")

    if len(all_items) < count:
        rm = _scrape_people_cn(count - len(all_items))
        all_items.extend(rm)
        print(f"      人民网: {len(rm)} items")

    return all_items[:count]


# ── Markdown Generation ─────────────────────────────────
def generate_markdown(weather: dict, trending: list, ai_news: list, domestic_news: list, quote: tuple) -> str:
    """Generate the daily briefing Markdown file."""
    today = datetime.now(_tz)
    filename_date = today.strftime("%Y-%m-%d")
    month_day = f"{today.month}月{today.day}日"

    md = f"# {month_day}热点速览精选\n\n"
    city_names = " · ".join(c["name"] for c in weather["cities"])
    md += f"> {today.strftime('%Y年%m月%d日')} · {city_names}\n\n"

    # ── Weather ──
    md += "---\n\n"
    for city_data in weather["cities"]:
        md += f"## 🌤 {city_data['name']}天气\n\n"
        for d in city_data["days"]:
            t_range = f"{int(round(d['temp_min']))}°C ~ {int(round(d['temp_max']))}°C"
            md += f"- **{d['label']}**（{d['date']}）：{d['weather']}，{t_range}\n"
        md += "\n"

    # ── GitHub Trending ──
    md += "---\n\n"
    md += "## —— GitHub Trending ——\n\n"
    for i, repo in enumerate(trending, 1):
        num = f"{i:02d}"
        md += f"### {num}. {repo['name']}\n\n"
        desc = repo['description'] or "(暂无描述)"
        lang_tag = f" `{repo['language']}`" if repo['language'] else ""
        stars_tag = f" | {repo['stars_today']}" if repo['stars_today'] else ""
        md += f"{desc}{lang_tag}{stars_tag}\n\n"
        md += f"[查看项目]({repo['url']})\n\n"
    md += "\n"

    # ── AI News ──
    md += "---\n\n"
    md += "## —— AI 科技动态 ——\n\n"
    for i, item in enumerate(ai_news, 1):
        num = f"{i:02d}"
        md += f"### {num}. {item['title']}\n\n"
        md += f"{item.get('description', '')}\n\n"
        if item.get('url'):
            md += f"[阅读原文]({item['url']})\n\n"
    md += "\n"

    # ── Domestic News ──
    md += "---\n\n"
    md += "## —— 国内热点 ——\n\n"
    for i, item in enumerate(domestic_news, 1):
        num = f"{i:02d}"
        md += f"### {num}. {item['title']}\n\n"
        md += f"{item.get('description', '')}\n\n"
        if item.get('url'):
            md += f"[阅读原文]({item['url']})\n\n"
    md += "\n"

    # ── Quote ──
    md += "---\n\n"
    md += f"> *「{quote[0]}」*\n>\n> —— **{quote[1]}**\n"

    return md, filename_date, month_day


# ── HTML Generation (Warm Card Style) ───────────────────
def generate_html(md_content: str, month_day: str, weather: dict, trending: list,
                  ai_news: list, domestic_news: list, quote: tuple) -> str:
    """Convert the briefing to a warm-toned HTML card."""

    # Build weather line (multi-city)
    weather_blocks = []
    for city_data in weather["cities"]:
        city_lines = []
        for d in city_data["days"]:
            t_range = f"{int(round(d['temp_min']))}°C ~ {int(round(d['temp_max']))}°C"
            city_lines.append(
                f'<span class="weather-item"><strong>{d["label"]}</strong> {d["weather"]} {t_range}</span>'
            )
        weather_blocks.append(
            f'<div class="city-label">🌤 {city_data["name"]}天气</div>'
            f'<div>{" · ".join(city_lines)}</div>'
        )
    weather_html = "\n        ".join(weather_blocks)

    # Build trending items
    trending_html = ""
    for i, repo in enumerate(trending, 1):
        num = f"{i:02d}"
        desc = repo['description'] or "(暂无描述)"
        lang_tag = f' <span class="lang-tag">{repo["language"]}</span>' if repo["language"] else ""
        stars_tag = f' <span class="stars-tag">{repo["stars_today"]}</span>' if repo["stars_today"] else ""
        trending_html += f"""
        <div class="item">
            <div class="item-title">{num}. {repo['name']}{lang_tag}{stars_tag}</div>
            <div class="item-desc">{desc}</div>
            <a class="item-link" href="{repo['url']}">{repo['url']}</a>
        </div>"""

    # Build AI news items
    ai_html = ""
    for i, item in enumerate(ai_news, 1):
        num = f"{i:02d}"
        desc = item.get('description', '')
        url = item.get('url', '')
        ai_html += f"""
        <div class="item">
            <div class="item-title">{num}. {item['title']}</div>
            <div class="item-desc">{desc}</div>
            {f'<a class="item-link" href="{url}">阅读原文 →</a>' if url else ''}
        </div>"""

    # Build domestic news items
    dom_html = ""
    for i, item in enumerate(domestic_news, 1):
        num = f"{i:02d}"
        desc = item.get('description', '')
        url = item.get('url', '')
        dom_html += f"""
        <div class="item">
            <div class="item-title">{num}. {item['title']}</div>
            <div class="item-desc">{desc}</div>
            {f'<a class="item-link" href="{url}">阅读原文 →</a>' if url else ''}
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=500">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    background: {COLORS['bg']};
    font-family: -apple-system, "PingFang SC", "Microsoft YaHei", "Noto Sans SC", sans-serif;
    color: {COLORS['body']};
    display: flex;
    justify-content: center;
    padding: 30px 20px;
}}
.card {{
    background: {COLORS['card_bg']};
    border: 1px solid {COLORS['card_border']};
    border-radius: 16px;
    padding: 32px 28px;
    max-width: 480px;
    width: 100%;
    box-shadow: 0 4px 24px rgba(224, 123, 60, 0.08);
}}
/* ── Title ── */
.main-title {{
    font-size: 32px;
    font-weight: 900;
    color: {COLORS['title']};
    text-align: center;
    letter-spacing: 2px;
    margin-bottom: 8px;
}}
.subtitle {{
    text-align: center;
    color: #A08070;
    font-size: 14px;
    margin-bottom: 30px;
}}
/* ── Accent Bar ── */
.accent-bar {{
    height: 3px;
    background: linear-gradient(90deg, {COLORS['accent']}, #F0A050, {COLORS['accent']});
    border-radius: 2px;
    margin-bottom: 28px;
    opacity: 0.7;
}}
/* ── Sections ── */
.section {{
    margin-bottom: 28px;
}}
.section-header {{
    font-size: 22px;
    font-weight: 800;
    color: {COLORS['title']};
    text-align: center;
    padding: 12px 0;
    background: {COLORS['accent_light']};
    border-radius: 8px;
    margin-bottom: 16px;
    letter-spacing: 1px;
}}
/* ── Weather ── */
.weather-section {{
    background: {COLORS['accent_light']};
    border-radius: 10px;
    padding: 18px 24px;
    margin-bottom: 24px;
    text-align: center;
    font-size: 16px;
    line-height: 1.8;
}}
.weather-section .city-label {{
    font-size: 18px;
    font-weight: 700;
    color: {COLORS['accent']};
    margin-bottom: 6px;
}}
.weather-item {{
    display: inline-block;
    margin: 0 8px;
}}
/* ── Items ── */
.item {{
    padding: 14px 0;
    border-bottom: 1px solid #F0E6DA;
}}
.item:last-child {{
    border-bottom: none;
}}
.item-title {{
    font-size: 17px;
    font-weight: 700;
    color: {COLORS['title']};
    margin-bottom: 4px;
    line-height: 1.4;
}}
.item-desc {{
    font-size: 14px;
    color: {COLORS['body']};
    line-height: 1.6;
    margin-bottom: 4px;
}}
.item-link {{
    font-size: 13px;
    color: {COLORS['link']};
    text-decoration: none;
    word-break: break-all;
}}
.item-link:hover {{ text-decoration: underline; }}
.lang-tag {{
    font-size: 13px;
    font-weight: 400;
    background: #F5EBE0;
    color: #8B6B4A;
    padding: 1px 8px;
    border-radius: 10px;
    margin-left: 6px;
}}
.stars-tag {{
    font-size: 13px;
    color: #A08070;
    margin-left: 6px;
}}
/* ── Quote ── */
.quote-section {{
    margin-top: 30px;
    padding: 24px 30px;
    background: linear-gradient(135deg, #FDF2E9, #FFF0E0);
    border-radius: 12px;
    text-align: center;
    border-left: 4px solid {COLORS['accent']};
}}
.quote-text {{
    font-size: 17px;
    font-style: italic;
    color: {COLORS['title']};
    line-height: 1.8;
    margin-bottom: 8px;
}}
.quote-author {{
    font-size: 14px;
    color: #A08070;
    font-weight: 600;
}}
/* ── Footer ── */
.footer {{
    text-align: center;
    margin-top: 24px;
    font-size: 12px;
    color: #C0A890;
}}
</style>
</head>
<body>
<div class="card">
    <div class="main-title">{month_day}热点速览精选</div>
    <div class="subtitle">{datetime.now(_tz).strftime('%Y年%m月%d日')} · 每日新闻简报</div>
    <div class="accent-bar"></div>

    <!-- Weather -->
    <div class="weather-section">
        {weather_html}
    </div>

    <!-- GitHub Trending -->
    <div class="section">
        <div class="section-header">—— GitHub Trending ——</div>
        {trending_html}
    </div>

    <!-- AI News -->
    <div class="section">
        <div class="section-header">—— AI 科技动态 ——</div>
        {ai_html}
    </div>

    <!-- Domestic News -->
    <div class="section">
        <div class="section-header">—— 国内热点 ——</div>
        {dom_html}
    </div>

    <!-- Quote -->
    <div class="quote-section">
        <div class="quote-text">「{quote[0]}」</div>
        <div class="quote-author">—— {quote[1]}</div>
    </div>

    <div class="footer">Daily News Briefing · Auto-generated</div>
</div>
</body>
</html>"""

    return html


# ── Summary File Update ─────────────────────────────────
def update_summary(md_content: str, filename_date: str):
    """Prepend today's briefing to the summary file, update index."""
    import re
    today_header = f"## {filename_date}\n\n"
    new_entry = today_header + md_content + "\n---\n\n"

    # Read existing summary and remove any previous entry for this date
    existing = ""
    if SUMMARY_FILE.exists():
        existing = SUMMARY_FILE.read_text(encoding="utf-8")

    # Remove old entry for the same date (in case of re-run)
    pattern = rf"## {re.escape(filename_date)}\n\n.*?\n---\n\n"
    existing = re.sub(pattern, "", existing, flags=re.DOTALL)

    # Remove old index section
    parts = existing.split("\n---\n", 1)
    old_body = parts[1].lstrip("\n") if len(parts) > 1 else existing.lstrip("\n")

    # Collect all dates from new entry + old body
    all_content = new_entry + old_body
    dates = list(dict.fromkeys(
        re.findall(r"^## (\d{4}-\d{2}-\d{2})$", all_content, re.MULTILINE)
    ))

    # Rebuild index
    index_lines = ["# 每日新闻简报 · 汇总\n", "\n## 目录\n"]
    for d in dates:
        anchor = d.replace("-", "")
        index_lines.append(f"- [{d}](#{anchor})\n")

    index = "".join(index_lines)
    full = index + "\n---\n\n" + new_entry
    if old_body.strip():
        full += old_body

    SUMMARY_FILE.write_text(full, encoding="utf-8")


# ── Main ────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  Daily News Briefing Generator")
    print("=" * 60)

    # Ensure directories
    DAILY_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Weather
    print("\n🌤  Fetching weather...")
    weather = fetch_weather()

    # 2. Load news from JSON input file (pre-collected by external agent)
    print("\n📰  Loading news data...")
    ai_news = []
    domestic_news = []
    trending = []

    if NEWS_INPUT_FILE.exists():
        try:
            news_data = json.loads(NEWS_INPUT_FILE.read_text(encoding="utf-8"))
            ai_news = news_data.get("ai_news", [])
            domestic_news = news_data.get("domestic_news", [])
            trending = news_data.get("github_trending", [])
        except Exception as e:
            print(f"   ⚠️  Failed to parse news input: {e}")

    # 3. Ensure data meets config display_count — supplement if needed
    need_gh = GITHUB_TRENDING["display_count"]
    need_ai = AI_NEWS["display_count"]
    need_dm = DOMESTIC_NEWS["display_count"]

    # GitHub: scrape live if JSON is insufficient
    if len(trending) < need_gh:
        short = need_gh - len(trending)
        print(f"   ⚠️  GitHub Trending only {len(trending)} items (need {need_gh}), scraping {short} more...")
        try:
            scraped = fetch_github_trending()
            # Merge: keep existing CN-translated items, add scraped ones (dedup by name)
            existing_names = {r["name"] for r in trending}
            for r in scraped:
                if r["name"] not in existing_names:
                    trending.append(r)
                    existing_names.add(r["name"])
                if len(trending) >= need_gh:
                    break
            print(f"   ✅ GitHub Trending now: {len(trending)} repos")
        except Exception as e:
            print(f"   ⚠️  Scraping failed: {e}")

    # AI: supplement via live search if insufficient
    if len(ai_news) < need_ai:
        short = need_ai - len(ai_news)
        print(f"   ⚠️  AI news only {len(ai_news)} items (need {need_ai}), searching {short} more...")
        try:
            supplement = fetch_ai_news_live(short)
            existing_titles = {r["title"] for r in ai_news}
            for r in supplement:
                if r["title"] not in existing_titles:
                    ai_news.append(r)
                    existing_titles.add(r["title"])
                if len(ai_news) >= need_ai:
                    break
            print(f"   ✅ AI news now: {len(ai_news)} items")
        except Exception as e:
            print(f"   ⚠️  AI supplement failed: {e}")

    # Domestic: supplement via live search if insufficient
    if len(domestic_news) < need_dm:
        short = need_dm - len(domestic_news)
        print(f"   ⚠️  Domestic news only {len(domestic_news)} items (need {need_dm}), searching {short} more...")
        try:
            supplement = fetch_domestic_news_live(short)
            existing_titles = {r["title"] for r in domestic_news}
            for r in supplement:
                if r["title"] not in existing_titles:
                    domestic_news.append(r)
                    existing_titles.add(r["title"])
                if len(domestic_news) >= need_dm:
                    break
            print(f"   ✅ Domestic news now: {len(domestic_news)} items")
        except Exception as e:
            print(f"   ⚠️  Domestic supplement failed: {e}")

    # Apply display_count limits
    trending = trending[:need_gh]
    ai_news = ai_news[:need_ai]
    domestic_news = domestic_news[:need_dm]

    print(f"   ✅ AI: {len(ai_news)} items, Domestic: {len(domestic_news)} items, GitHub: {len(trending)} repos")

    # If no news, use placeholders for testing
    if not ai_news:
        ai_news = [{"title": "（待采集）", "description": "每日 AI 新闻将通过外部 Agent 自动采集"}]
    if not domestic_news:
        domestic_news = [{"title": "（待采集）", "description": "每日国内热点将通过外部 Agent 自动采集"}]

    # Save collected news data for reference (dated file for traceability)
    if trending or ai_news or domestic_news:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        today_str = datetime.now(_tz).strftime("%Y-%m-%d")
        dated_news_file = DATA_DIR / f"news_input_{today_str}.json"
        dated_news_file.write_text(
            json.dumps({
                "github_trending": trending,
                "ai_news": ai_news,
                "domestic_news": domestic_news,
            }, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"   📥 News data saved: {dated_news_file}")

    # 4. Fetch daily quote
    print("\n💬  Fetching quote...")
    quote = fetch_quote()
    print(f"   ✅ {quote[1]}: 「{quote[0][:50]}...」")

    # 5. Generate Markdown
    print("\n📝  Generating Markdown...")
    md_content, filename_date, month_day = generate_markdown(
        weather, trending, ai_news, domestic_news, quote
    )

    md_path = DAILY_DIR / f"{filename_date}.md"
    md_path.write_text(md_content, encoding="utf-8")
    print(f"   ✅ Saved: {md_path}")

    # 6. Generate HTML
    print("\n🎨  Generating warm-toned HTML card...")
    html_content = generate_html(md_content, month_day, weather, trending, ai_news, domestic_news, quote)

    html_path = DAILY_DIR / f"{filename_date}.html"
    html_path.write_text(html_content, encoding="utf-8")
    print(f"   ✅ Saved: {html_path}")

    # 7. Generate Image via PIL
    img_path = IMAGES_DIR / f"{filename_date}.png"
    img_ok = False

    print("\n🎨  Rendering card image...")
    try:
        pil_render_card(weather, trending, ai_news, domestic_news, quote, img_path)
        img_ok = img_path.exists()
        if img_ok:
            print(f"   ✅ Image saved: {img_path}")
        else:
            print(f"   ⚠️  Image file not found after render")
    except Exception as e:
        print(f"   ❌ Render error: {e}")

    # 8. Update Summary
    print("\n📋  Updating summary...")
    update_summary(md_content, filename_date)
    print(f"   ✅ Summary updated: {SUMMARY_FILE}")

    # 9. Report
    print("\n" + "=" * 60)
    print("  Generation Complete!")
    print(f"  Markdown: {md_path}")
    print(f"  HTML:     {html_path}")
    print(f"  Image:    {img_path}")
    print(f"  Summary:  {SUMMARY_FILE}")
    print("=" * 60)

    return {
        "md_path": str(md_path),
        "html_path": str(html_path),
        "img_path": str(img_path) if img_ok else None,
        "filename_date": filename_date,
        "month_day": month_day,
    }


if __name__ == "__main__":
    main()
