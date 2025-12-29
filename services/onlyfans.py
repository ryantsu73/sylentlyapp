import re
from typing import Dict, Any, Optional

import requests
from bs4 import BeautifulSoup


def _parse_human_number(text: str) -> Optional[int]:
    """
    Convert strings like '4.5K', '10.2M', '12,345' to an integer.
    Returns None if it cannot be parsed.
    """
    if not text:
        return None
    t = text.strip().lower().replace(",", "")
    match = re.match(r"^([0-9]*\.?[0-9]+)\s*([km])?$", t)
    if not match:
        if t.isdigit():
            return int(t)
        return None

    num = float(match.group(1))
    suffix = match.group(2)

    if suffix == "k":
        num *= 1_000
    elif suffix == "m":
        num *= 1_000_000

    return int(num)


def fetch_onlyfans_profile(handle: str) -> Dict[str, Any]:
    """
    Scrape a public OnlyFans profile and estimate:
      - followers (fans)
      - avg_views (heuristic from followers)
      - engagement_rate (heuristic from likes and followers)
      - avg_cpm (simple assumption)

    Additionally tries to pull:
      - profile_name
      - profile_image_url
      - likes
      - posts_count
      - photos_count
      - videos_count

    Also returns simple ESTIMATES:
      - estimated_subscribers
      - estimated_monthly_visits

    Uses public metadata only and NEVER raises on parsing issues.
    On any failure, falls back to default values and records an 'error'
    string plus a 'raw_source' flag so the UI can still work.
    """
    username = handle.strip().lstrip("@").strip("/")
    if not username:
        followers = 5_000
        avg_views = int(followers * 0.3)
        engagement_rate = 3.5
        avg_cpm = 20.0
        estimated_subscribers = followers
        estimated_monthly_visits = followers * 15
        return {
            "platform": "OnlyFans",
            "handle": handle,
            "profile_name": handle or "Unknown",
            "profile_image_url": None,
            "followers": followers,
            "likes": None,
            "posts_count": None,
            "photos_count": None,
            "videos_count": None,
            "avg_views": avg_views,
            "engagement_rate": engagement_rate,
            "avg_cpm": avg_cpm,
            "estimated_subscribers": estimated_subscribers,
            "estimated_monthly_visits": estimated_monthly_visits,
            "raw_source": "onlyfans_invalid_handle_fallback",
            "error": "Handle was empty after cleaning.",
        }

    url = f"https://onlyfans.com/{username}"

    # Default values used whenever we can't parse real data
    def make_fallback(raw_source: str, error: Optional[str] = None) -> Dict[str, Any]:
        followers = 5_000
        avg_views = int(followers * 0.3)
        engagement_rate = 3.5
        avg_cpm = 20.0
        estimated_subscribers = followers
        estimated_monthly_visits = followers * 15

        data = {
            "platform": "OnlyFans",
            "handle": username,
            "profile_name": username,
            "profile_image_url": None,
            "followers": followers,
            "likes": None,
            "posts_count": None,
            "photos_count": None,
            "videos_count": None,
            "avg_views": avg_views,
            "engagement_rate": engagement_rate,
            "avg_cpm": avg_cpm,
            "estimated_subscribers": estimated_subscribers,
            "estimated_monthly_visits": estimated_monthly_visits,
            "raw_source": raw_source,
        }
        if error:
            data["error"] = error
        return data

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        # Network / HTTP error: fallback so the app never crashes
        return make_fallback("onlyfans_http_error_fallback", error=str(e))

    html = resp.text
    soup = BeautifulSoup(html, "html.parser")

    # ---------- Basic identity / image ----------

    profile_name = None
    profile_image_url = None

    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        profile_name = og_title["content"].strip()

    og_image = soup.find("meta", property="og:image")
    if og_image and og_image.get("content"):
        profile_image_url = og_image["content"].strip()

    if not profile_name and soup.title and soup.title.string:
        profile_name = soup.title.string.strip()

    # ---------- Numeric stats ----------

    followers = None
    likes = None
    posts_count = None
    photos_count = None
    videos_count = None

    # 1) Try meta description (common older pattern)
    meta_desc_tag = soup.find("meta", attrs={"name": "description"})
    if meta_desc_tag and meta_desc_tag.get("content"):
        desc = meta_desc_tag["content"]

        likes_match = re.search(r"(\d[\d.,]*\s*[kKmM]?)\s+[Ll]ikes", desc)
        fans_match = re.search(r"(\d[\d.,]*\s*[kKmM]?)\s+(fans|Fans)", desc)
        posts_match = re.search(r"(\d[\d.,]*\s*[kKmM]?)\s+[Pp]osts?", desc)
        photos_match = re.search(r"(\d[\d.,]*\s*[kKmM]?)\s+[Pp]hotos?", desc)
        videos_match = re.search(r"(\d[\d.,]*\s*[kKmM]?)\s+[Vv]ideos?", desc)

        if likes_match:
            likes = _parse_human_number(likes_match.group(1))
        if fans_match:
            followers = _parse_human_number(fans_match.group(1))
        if posts_match:
            posts_count = _parse_human_number(posts_match.group(1))
        if photos_match:
            photos_count = _parse_human_number(photos_match.group(1))
        if videos_match:
            videos_count = _parse_human_number(videos_match.group(1))

    # 2) Search in full page text for any remaining stats
    text = soup.get_text(separator=" ", strip=True)

    if followers is None:
        fans_match = re.search(r"(\d[\d.,]*\s*[kKmM]?)\s+(fans|Followers?)", text)
        if fans_match:
            followers = _parse_human_number(fans_match.group(1))

    if likes is None:
        likes_match = re.search(r"(\d[\d.,]*\s*[kKmM]?)\s+[Ll]ikes", text)
        if likes_match:
            likes = _parse_human_number(likes_match.group(1))

    if posts_count is None:
        posts_match = re.search(r"(\d[\d.,]*\s*[kKmM]?)\s+[Pp]osts?", text)
        if posts_match:
            posts_count = _parse_human_number(posts_match.group(1))

    if photos_count is None:
        photos_match = re.search(r"(\d[\d.,]*\s*[kKmM]?)\s+[Pp]hotos?", text)
        if photos_match:
            photos_count = _parse_human_number(photos_match.group(1))

    if videos_count is None:
        videos_match = re.search(r"(\d[\d.,]*\s*[kKmM]?)\s+[Vv]ideos?", text)
        if videos_match:
            videos_count = _parse_human_number(videos_match.group(1))

    # 3) If absolutely nothing numeric was found, use fallback defaults
    if followers is None and likes is None and posts_count is None:
        fb = make_fallback("onlyfans_fallback_no_numbers_found")
        fb["profile_name"] = profile_name or username
        fb["profile_image_url"] = profile_image_url
        return fb

    # 4) Derive core metrics

    if followers is None and likes is not None:
        # Rough guess: ~10% of followers like something at least once
        followers = max(int(likes / 0.1), likes)

    if followers is None:
        followers = 5_000

    avg_views = int(followers * 0.3)

    if likes is not None and followers > 0:
        engagement_rate = round((likes / followers) * 100, 2)
    else:
        engagement_rate = 3.5

    avg_cpm = 20.0

    # Simple ESTIMATES based on public data
    estimated_subscribers = followers  # "fans" on OF ~= subscribers
    estimated_monthly_visits = followers * 15  # assumption-based

    return {
        "platform": "OnlyFans",
        "handle": username,
        "profile_name": profile_name or username,
        "profile_image_url": profile_image_url,
        "followers": followers,
        "likes": likes,
        "posts_count": posts_count,
        "photos_count": photos_count,
        "videos_count": videos_count,
        "avg_views": avg_views,
        "engagement_rate": engagement_rate,
        "avg_cpm": avg_cpm,
        "estimated_subscribers": estimated_subscribers,
        "estimated_monthly_visits": estimated_monthly_visits,
        "raw_source": "onlyfans_meta_or_text",
    }


def fetch_creator_profile_from_web(handle: str, platform: str) -> Dict[str, Any]:
    """
    Dispatcher for web lookups by platform.
    """
    platform_norm = platform.strip().lower()

    if not handle:
        raise ValueError("Handle cannot be empty.")

    if platform_norm == "onlyfans":
        return fetch_onlyfans_profile(handle)

    # Extend here for other platforms if needed.
    raise NotImplementedError(f"Web lookup not implemented for platform: {platform}")
