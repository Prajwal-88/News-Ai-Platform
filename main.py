import requests
import sqlite3
import os
from dotenv import load_dotenv
from datetime import datetime
 
#Load API key from .env file

load_dotenv()
API_KEY = os.getenv("NEWS_API_KEY")

def fetch_news(topic="technology", count=10):
    """Fetch news articles from NewsAPI"""
 
    url = "https://newsapi.org/v2/everything"
 
    params = {
        "q": topic,
        "pageSize": count,
        "sortBy": "publishedAt",
        "language": "en",
        "apiKey": API_KEY
    }
 
    print(f"\nFetching news about: {topic}...")
 
    response = requests.get(url, params=params)
 
    # Check if request was successful
    if response.status_code == 200:
        data = response.json()
        articles = data["articles"]
        print(f"Found {len(articles)} articles!\n")
        return articles
    else:
        print(f"Error: {response.status_code} - {response.json()}")
        return []
    
def setup_database():
    """Create the database and articles table if it doesn't exist"""
 
    # This creates a file called news.db in your data/ folder
    conn = sqlite3.connect("data/news.db")
    cursor = conn.cursor()
 
    # Create table to store articles
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            source TEXT,
            author TEXT,
            url TEXT UNIQUE,
            title TEXT UNIQUE,
            published_at TEXT,
            topic TEXT,
            saved_at TEXT
        )
    """)
 
    conn.commit()
    conn.close()
    print("✅ Database ready!")

def save_articles(articles, topic):
    """Save fetched articles into SQLite database"""
 
    conn = sqlite3.connect("data/news.db")
    cursor = conn.cursor()
 
    saved = 0
 
    for article in articles:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO articles 
                (title, description, source, author, url, published_at, topic, saved_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                article.get("title"),
                article.get("description"),
                article.get("source", {}).get("name"),
                article.get("author"),
                article.get("url"),
                article.get("publishedAt"),
                topic,
                datetime.now().isoformat()
            ))
            saved += 1
        except Exception as e:
            print(f"⚠️ Skipped an article: {e}")
 
    conn.commit()
    conn.close()
    print(f"💾 Saved {saved} new articles to database!")
 

def show_saved_articles(topic=None):
    """Display articles saved in the database"""
 
    conn = sqlite3.connect("data/news.db")
    cursor = conn.cursor()
 
    if topic:
        cursor.execute("SELECT title, source, published_at FROM articles WHERE topic=? ORDER BY published_at DESC", (topic,))
    else:
        cursor.execute("SELECT title, source, published_at FROM articles ORDER BY published_at DESC")
 
    articles = cursor.fetchall()
    conn.close()
 
    print(f"\n📰 Articles in Database ({len(articles)} total):")
    print("-" * 60)
 
    for i, (title, source, published_at) in enumerate(articles, 1):
        print(f"{i}. {title}")
        print(f"   📡 {source} | 🕒 {published_at[:10]}\n")
 

if __name__ == "__main__":
 
    # 1. Setup database
    setup_database()
 
    # 2. Choose your topic
    topic = "artificial intelligence"
 
    # 3. Fetch news from API
    articles = fetch_news(topic=topic, count=10)
 
    # 4. Save to database
    if articles:
        save_articles(articles, topic)
 
    # 5. Show what's saved
    show_saved_articles(topic=topic)
 