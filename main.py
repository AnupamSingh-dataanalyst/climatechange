import feedparser
import requests
import json
import time
from datetime import datetime

# Configuration
DISCORD_WEBHOOK_URL = "your_discord_webhook_url_here"
RSS_FEED_URL = "https://www.thehindu.com/sci-tech/energy-and-environment/feeder/default.rss"
CHECK_INTERVAL = 3600  # Check every hour (in seconds)
SEEN_ARTICLES_FILE = "seen_articles.json"

def load_seen_articles():
    """Load previously seen article IDs"""
    try:
        with open(SEEN_ARTICLES_FILE, 'r') as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()

def save_seen_articles(seen_articles):
    """Save seen article IDs to file"""
    with open(SEEN_ARTICLES_FILE, 'w') as f:
        json.dump(list(seen_articles), f)

def check_climate_keywords(title, summary):
    """Check if article is about climate change"""
    keywords = ['climate change', 'global warming', 'greenhouse gas', 
                'carbon emission', 'climate crisis', 'net zero',
                'renewable energy', 'fossil fuel', 'climate action']
    
    text = (title + " " + summary).lower()
    return any(keyword in text for keyword in keywords)

def send_discord_notification(article):
    """Send notification to Discord webhook"""
    embed = {
        "title": article['title'],
        "description": article['summary'][:500] + "..." if len(article['summary']) > 500 else article['summary'],
        "url": article['link'],
        "color": 3066993,  # Green color
        "fields": [
            {
                "name": "Published",
                "value": article['published'],
                "inline": True
            },
            {
                "name": "Source",
                "value": "The Hindu",
                "inline": True
            }
        ],
        "footer": {
            "text": "Climate Change Alert"
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    
    data = {
        "username": "Climate Change Monitor",
        "embeds": [embed]
    }
    
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(DISCORD_WEBHOOK_URL, json=data, headers=headers)
    
    if 200 <= response.status_code < 300:
        print(f"✓ Notification sent: {article['title']}")
        return True
    else:
        print(f"✗ Failed to send notification: {response.status_code}")
        return False

def check_feed():
    """Check RSS feed for new climate change articles"""
    print(f"Checking feed at {datetime.now()}")
    
    # Load seen articles
    seen_articles = load_seen_articles()
    
    # Parse RSS feed
    feed = feedparser.parse(RSS_FEED_URL)
    
    if not feed.entries:
        print("No entries found in feed")
        return
    
    new_articles = []
    
    for entry in feed.entries:
        article_id = entry.get('id', entry.get('link'))
        
        # Skip if already seen
        if article_id in seen_articles:
            continue
        
        # Check if climate-related
        title = entry.get('title', '')
        summary = entry.get('summary', '')
        
        if check_climate_keywords(title, summary):
            article = {
                'title': title,
                'summary': summary,
                'link': entry.get('link', ''),
                'published': entry.get('published', 'Unknown date')
            }
            
            # Send notification
            if send_discord_notification(article):
                new_articles.append(article_id)
    
    # Update seen articles
    if new_articles:
        seen_articles.update(new_articles)
        save_seen_articles(seen_articles)
        print(f"Found {len(new_articles)} new climate change article(s)")
    else:
        print("No new climate change articles found")

def main():
    """Main loop"""
    print("Climate Change Monitor Started")
    print(f"Monitoring: {RSS_FEED_URL}")
    print(f"Check interval: {CHECK_INTERVAL} seconds")
    
    while True:
        try:
            check_feed()
        except Exception as e:
            print(f"Error: {e}")
        
        # Wait before next check
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
