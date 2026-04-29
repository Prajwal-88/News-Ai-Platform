import sqlite3
from textblob import TextBlob

# -----------------------------------------------
# STEP 1: ADD SENTIMENT COLUMN TO DATABASE
# -----------------------------------------------
def update_database():
    """Add sentiment columns to existing articles table"""
    conn = sqlite3.connect("data/news.db")
    cursor = conn.cursor()

    # Add new columns (will skip if they already exist)
    try:
        cursor.execute("ALTER TABLE articles ADD COLUMN sentiment TEXT")
        cursor.execute("ALTER TABLE articles ADD COLUMN sentiment_score REAL")
        conn.commit()
        print(" Database updated with sentiment columns!")
    except Exception:
        print(" Sentiment columns already exist, skipping...")

    conn.close()


# -----------------------------------------------
# STEP 2: ANALYSE SENTIMENT OF A TEXT
# -----------------------------------------------
def analyse_sentiment(text):
    """
    Analyse sentiment of a given text using TextBlob.
    Returns a label (Positive/Negative/Neutral) and a score (-1 to 1)
    """
    if not text:
        return "Neutral", 0.0

    blob = TextBlob(text)
    score = blob.sentiment.polarity  # score between -1.0 and 1.0

    if score > 0.1:
        label = "Positive"
    elif score < -0.1:
        label = "Negative"
    else:
        label = "Neutral"

    return label, round(score, 3)


# -----------------------------------------------
# STEP 3: ANALYSE ALL ARTICLES IN DATABASE
# -----------------------------------------------
def analyse_all_articles():
    """Read all articles, analyse sentiment, save back to DB"""

    conn = sqlite3.connect("data/news.db")
    cursor = conn.cursor()

    # Get all articles
    cursor.execute("SELECT id, title, description FROM articles")
    articles = cursor.fetchall()

    print(f"\n🔍 Analysing {len(articles)} articles...\n")
    print("-" * 60)

    positive = 0
    negative = 0
    neutral  = 0

    for article_id, title, description in articles:

        # Use title + description for better accuracy
        text = f"{title}. {description}" if description else title

        # Get sentiment
        label, score = analyse_sentiment(text)

        # Save back to database
        cursor.execute("""
            UPDATE articles
            SET sentiment = ?, sentiment_score = ?
            WHERE id = ?
        """, (label, score, article_id))

        # Print result with emoji
        if label == "Positive":
            emoji = "😊"
            positive += 1
        elif label == "Negative":
            emoji = "😟"
            negative += 1
        else:
            emoji = "😐"
            neutral += 1

        print(f"{emoji} {title[:70]}...")
        print(f"   Sentiment: {label} (score: {score})\n")

    conn.commit()
    conn.close()

    # -----------------------------------------------
    # STEP 4: PRINT SUMMARY
    # -----------------------------------------------
    print("-" * 60)
    print("📊 Sentiment Summary:")
    print(f"   😊 Positive : {positive} articles")
    print(f"   😐 Neutral  : {neutral} articles")
    print(f"   😟 Negative : {negative} articles")
    print("-" * 60)


# -----------------------------------------------
# STEP 5: SHOW TOP POSITIVE & NEGATIVE ARTICLES
# -----------------------------------------------
def show_top_articles():
    """Show the most positive and most negative articles"""

    conn = sqlite3.connect("data/news.db")
    cursor = conn.cursor()

    # Most positive
    cursor.execute("""
        SELECT title, sentiment_score FROM articles
        WHERE sentiment = 'Positive'
        ORDER BY sentiment_score DESC
        LIMIT 3
    """)
    positive_articles = cursor.fetchall()

    # Most negative
    cursor.execute("""
        SELECT title, sentiment_score FROM articles
        WHERE sentiment = 'Negative'
        ORDER BY sentiment_score ASC
        LIMIT 3
    """)
    negative_articles = cursor.fetchall()

    conn.close()

    print("\n🏆 Most Positive Articles:")
    for title, score in positive_articles:
        print(f"   😊 ({score}) {title[:70]}")

    print("\n⚠️  Most Negative Articles:")
    for title, score in negative_articles:
        print(f"   😟 ({score}) {title[:70]}")


# -----------------------------------------------
# MAIN
# -----------------------------------------------
if __name__ == "__main__":

    # 1. Update database to support sentiment
    update_database()

    # 2. Analyse all articles
    analyse_all_articles()

    # 3. Show top positive and negative
    show_top_articles()