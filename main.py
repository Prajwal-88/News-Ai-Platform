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
            published_at TEXT,
            topic TEXT,
            saved_at TEXT
        )
    """)
 
    conn.commit()
    conn.close()
    print("✅ Database ready!")