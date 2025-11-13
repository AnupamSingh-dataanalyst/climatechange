import feedparser
import os
import requests
import json
import logging
from datetime import datetime
from pathlib import Path

# === Configuration ===
webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
if not webhook_url:
    raise RuntimeError("Discord webhook URL not set in environment")
RSS_FEED_URL = "https://www.thehindu.com/sci-tech/energy-and-environment/feeder/default.rss"
SEEN_ARTICLES_FILE = "seen_articles.json"
LOG_DIR = "logs"
LOG_FILE = f"{LOG_DIR}/climate_bot_{datetime.now().strftime('%Y-%m-%d')}.log"


# === Setup Logging ===
Path(LOG_DIR).mkdir(exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# Also print logs to console (so GitHub shows them)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
console.setFormatter(formatter)
logging.getLogger("").addHandler(console)


# === Helper Functions ===
def load_seen_articles():
    try:
        with open(SEEN_ARTICLES_FILE, 'r') as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()


def save_seen_articles(seen_articles):
    with open(SEEN_ARTICLES_FILE, 'w') as f:
        json.dump(list(seen_articles), f)


def check_climate_keywords(title, summary):
    keywords = [
        'climate change', 'global warming', 'greenhouse gas', 
        'carbon emission', 'climate crisis', 'net zero',
        'renewable energy', 'fossil fuel', 'climate action'
    ]
    text = (title + " " + summary).lower()
    return any(keyword in text for keyword in keywords)


def send_discord_notification(article):
    embed = {
        "title": article['title'],
        "description": article['summary'][:500] + "..." if len(article['summary']) > 500 else article['summary'],
        "url": article['link'],
        "color": 3066993,
        "fields": [
            {"name": "Published", "value": article['published'], "inline": True},
            {"name": "Source", "value": "The Hindu", "inline": True}
        ],
        "footer": {"text": "Climate Change Alert"},
        "timestamp": datetime.utcnow().isoformat()
    }

    data = {"username": "Climate Change Monitor", "embeds": [embed]}
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=data, headers=headers, timeout=10)
        if 200 <= response.status_code < 300:
            logging.info(f"✅ Notification sent: {article['title']}")
        else:
            logging.warning(f"⚠️ Failed to send notification ({response.status_code}): {article['title']}")
    except Exception as e:
        logging.error(f"❌ Error sending to Discord: {e}")


def check_feed():
    logging.info(f"🌍 Checking feed at {datetime.now()}")

    seen_articles = load_seen_articles()
    feed = feedparser.parse(RSS_FEED_URL)

    if not feed.entries:
        logging.warning("No entries found in feed")
        return

    new_articles = []

    for entry in feed.entries:
        article_id = entry.get('id', entry.get('link'))
        if article_id in seen_articles:
            continue

        title = entry.get('title', '')
        summary = entry.get('summary', '')

        if check_climate_keywords(title, summary):
            article = {
                'title': title,
                'summary': summary,
                'link': entry.get('link', ''),
                'published': entry.get('published', 'Unknown date')
            }
            send_discord_notification(article)
            new_articles.append(article_id)

    if new_articles:
        seen_articles.update(new_articles)
        save_seen_articles(seen_articles)
        logging.info(f"📢 Found {len(new_articles)} new climate change article(s)")
    else:
        logging.info("No new climate change articles found")


def main():
    logging.info("🚀 Climate Change Monitor started")
    try:
        check_feed()
        logging.info("✅ Finished run — exiting.")
    except Exception as e:
        logging.exception(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
