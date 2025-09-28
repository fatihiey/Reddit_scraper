# Reddit Image Scraper

This project scrapes posts from Reddit (using Reddit's public API) and extracts only posts with images.  
Results are saved into a JSON file (`reddit_img.json`) and can  be displayed in a simple web page.

## Features
- Scrape Reddit posts with images
- Save results to JSON
- Simple web interface to display data

## Tech Stack
- Python 3
- Requests, BeautifulSoup


## Installation
```bash
git clone https://github.com/<your-username>/Reddit_scraper.git
cd Reddit_scraper
python3 -m venv .venv
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt

```
## Usage (in venv)
python scraper/reddit.py --subreddit malaysia --pages 10 --out data/reddit_img.json
python -m http.server <port number>
http://localhost:port number/web/

##Notes
-Replace the port number with your own port number to access the UI, it can be 8000,8080,5000 or else.
