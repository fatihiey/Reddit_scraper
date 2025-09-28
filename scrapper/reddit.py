#!/usr/bin/env python3
import argparse, html, json, time
from typing import Optional
import requests

USER_AGENT = "fatihah-reddit-scraper/1.0 (+github.com/your-username)"


def extract_image_url(post: dict) -> Optional[str]:
    """Return an image URL if present, else None."""
    d = post.get("data", {})

    # 1) Direct image link (e.g., i.redd.it / imgur direct)
    dest = d.get("url_overridden_by_dest") or d.get("url")
    if dest and dest.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
        return dest

    # 2) Preview image
    preview = d.get("preview")
    if preview and preview.get("images"):
        src = preview["images"][0].get("source")
        if src and src.get("url"):
            return html.unescape(src["url"])

    # 3) Gallery (pick first)
    if d.get("is_gallery") and "media_metadata" in d:
        for item in d["media_metadata"].values():
            s = item.get("s", {})
            u = s.get("u")
            if u:
                return html.unescape(u)

    return None


def fetch_listing(subreddit: str, sort: str, limit: int, after: Optional[str]) -> dict:
    url = f"https://www.reddit.com/r/{subreddit}/{sort}.json"
    params = {"limit": limit}
    if after:
        params["after"] = after

    headers = {"User-Agent": USER_AGENT}
    # Simple retry/backoff for rate limits (429) or transient issues
    for attempt in range(5):
        resp = requests.get(url, headers=headers, params=params, timeout=20)
        if resp.status_code == 429:
            time.sleep(2 ** attempt)
            continue
        resp.raise_for_status()
        return resp.json()
    # last try
    resp.raise_for_status()
    return resp.json()


def main():
    p = argparse.ArgumentParser(description="Reddit image scraper -> JSON")
    p.add_argument("--subreddit", required=True, help="e.g. malaysia")
    p.add_argument("--pages", type=int, default=10, help="number of pages to scrape (default 10)")
    p.add_argument("--sort", default="hot", choices=["hot", "new", "top", "rising"], help="listing type")
    p.add_argument("--limit", type=int, default=25, help="items per page (max 100)")
    p.add_argument("--out", default="data/reddit_images.json", help="output JSON path")
    p.add_argument("--sleep", type=float, default=1.0, help="seconds to sleep between pages")
    args = p.parse_args()

    all_items = []
    after = None

    for page in range(args.pages):
        j = fetch_listing(args.subreddit, args.sort, args.limit, after)
        children = j.get("data", {}).get("children", [])
        after = j.get("data", {}).get("after")

        for c in children:
            img = extract_image_url(c)
            if img:
                title = c["data"].get("title", "").strip()
                all_items.append({"post_title": title, "image_url": img})

        # Be polite to Reddit
        if page < args.pages - 1:
            time.sleep(args.sleep)

        # If no more pages, stop early
        if not after:
            break

    # De-duplicate by image_url (optional)
    seen = set()
    uniq = []
    for item in all_items:
        if item["image_url"] in seen:
            continue
        seen.add(item["image_url"])
        uniq.append(item)

    # Save
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(uniq, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(uniq)} items to {args.out}")


if __name__ == "__main__":
    main()
