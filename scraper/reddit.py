import argparse, html, json, time
from typing import Optional
import requests

# Acknowledge Reddit API
USER_AGENT = "(+https://github.com/fatihiey/Reddit_scraper)"


def extract_image_url(post: dict) -> Optional[str]:
    """Extract an image URL from a Reddit post if one exists, else return None."""
    d = post.get("data", {})

    # 1) Only read image's link
    dest = d.get("url_overridden_by_dest") or d.get("url")
    if dest and dest.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
        return dest

    # 2) Keep an URL for images wiht post
    preview = d.get("preview")
    if preview and preview.get("images"):
        src = preview["images"][0].get("source")
        if src and src.get("url"):
            return html.unescape(src["url"])   # decode HTML entities 

    # 3) If the post has multiple images, pick the first image only
    if d.get("is_gallery") and "media_metadata" in d:
        for item in d["media_metadata"].values():
            s = item.get("s", {})     # "s" to keep source info
            u = s.get("u")            # "u" keep image's url
            if u:
                return html.unescape(u)

    # 4) Return if no image found
    return None


def fetch_listing(subreddit: str, sort: str, limit: int, after: Optional[str]) -> dict:
    """Fetch one page of posts from a subreddit."""
    url = f"https://www.reddit.com/r/{subreddit}/{sort}.json"
    params = {"limit": limit}    # put limit to the number of posts per request
    if after:
        params["after"] = after  # pagination cursor (reddit params to move to the next page)

    headers = {"User-Agent": USER_AGENT}

    # Retry loop in case of rate limit (429) or temporary network issues
    for attempt in range(5):
        resp = requests.get(url, headers=headers, params=params, timeout=20)

        if resp.status_code == 429:       # Too Many Requests
            time.sleep(2 ** attempt)     # waiting time before retry (1s, 2s, 4s, 8s…)
            continue

        resp.raise_for_status()          # throw error if bad status 
        return resp.json()               # return JSON if success

    # If all retries failed, raise error on last attempt
    resp.raise_for_status()
    return resp.json()


def main():
    # Add command-line arguments
    p = argparse.ArgumentParser(description="Reddit image scraper -> JSON")
    p.add_argument("--subreddit", required=True, help="e.g. malaysia")
    p.add_argument("--pages", type=int, default=10, help="number of pages to scrape (default 10)")
    p.add_argument("--sort", default="hot", choices=["hot", "new", "top", "rising"], help="listing type")
    p.add_argument("--limit", type=int, default=25, help="items per page (max 100)")
    p.add_argument("--out", default="data/reddit_images.json", help="output JSON path")
    p.add_argument("--sleep", type=float, default=1.0, help="seconds to sleep between pages")
    args = p.parse_args()

    all_items = []     #  posts (with title & image)
    after = None      

    # Loop over number of pages requested
    for page in range(args.pages):
        j = fetch_listing(args.subreddit, args.sort, args.limit, after)

        # Extract posts from API response
        children = j.get("data", {}).get("children", [])
        after = j.get("data", {}).get("after")   # get "after" token for next page

        # Go through each post
        for c in children:
            img = extract_image_url(c)   # extract image
            if img:
                title = c["data"].get("title", "").strip()
                all_items.append({"post_title": title, "image_url": img})

        # Sleep between pages to avoid hitting Reddit too fast
        if page < args.pages - 1:
            time.sleep(args.sleep)

        # If no more pages (after == None), stop early
        if not after:
            break

    # ---- Remove duplicate images before save to Json file ----
    seen = set()
    uniq = []
    for item in all_items:
        if item["image_url"] in seen:
            continue    # skip duplicates
        seen.add(item["image_url"])
        uniq.append(item)

    # ---- Save results to JSON file ----
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(uniq, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(uniq)} items to {args.out}")



if __name__ == "__main__":
    main()
