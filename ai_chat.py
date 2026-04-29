import sqlite3
import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

#  Load API key from .env file
load_dotenv()
HF_API_KEY = os.getenv("HF_API_KEY")

#  Use featherless-ai provider — works reliably on free tier
client = InferenceClient(
    provider="featherless-ai",
    api_key=HF_API_KEY,
)


# -----------------------------------------------
# STEP 1: GET ARTICLES FROM DATABASE
# -----------------------------------------------
def get_articles(limit=10):
    """Fetch articles from SQLite database"""

    conn = sqlite3.connect("data/news.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT title, description, source, sentiment, sentiment_score
        FROM articles
        ORDER BY published_at DESC
        LIMIT ?
    """, (limit,))
    articles = cursor.fetchall()
    conn.close()
    return articles


# -----------------------------------------------
# STEP 2: BUILD CONTEXT FROM ARTICLES
# -----------------------------------------------
def build_context(articles):
    """Combine articles into one context string"""

    context = ""
    for i, (title, description, source, sentiment, score) in enumerate(articles):
        context += f"Article {i+1}: {title}."
        if description:
            context += f" {description}"
        context += "\n"
    return context.strip()


# -----------------------------------------------
# STEP 3: SUMMARISE AN ARTICLE
# -----------------------------------------------
def summarise_article(text):
    """Summarise a news article using LLM"""

    try:
        text = text[:800]

        result = client.chat.completions.create(
            model="meta-llama/Llama-3.1-8B-Instruct",
            messages=[
                {
                    "role": "system",
                    "content": "You are a news summariser. Summarise the given article in 2 sentences only."
                },
                {
                    "role": "user",
                    "content": f"Summarise this: {text}"
                }
            ],
            max_tokens=100,
        )

        return result.choices[0].message.content.strip()

    except Exception as e:
        return f" Error: {str(e)[:120]}"


# -----------------------------------------------
# STEP 4: CHAT WITH NEWS
# -----------------------------------------------
def chat_with_news(question, context):
    """Answer questions about the news using LLM"""

    try:
        result = client.chat.completions.create(
            model="meta-llama/Llama-3.1-8B-Instruct",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a helpful news assistant. Answer questions based only on these news articles:\n\n{context[:1500]}"
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            max_tokens=300,
        )

        return result.choices[0].message.content.strip()

    except Exception as e:
        error = str(e)
        if "loading" in error.lower() or "503" in error:
            return "⏳ Model is loading — wait 30 seconds and try again"
        elif "401" in error or "403" in error:
            return " API key issue — check HF_API_KEY in .env"
        else:
            return f" Error: {error[:120]}"


# -----------------------------------------------
# STEP 5: SUMMARISE LATEST NEWS
# -----------------------------------------------
def summarise_latest_news():
    """Summarise the latest news articles"""

    print("\n📰 Fetching latest articles...")
    articles = get_articles(limit=5)

    if not articles:
        print(" No articles found. Run main.py first!")
        return

    print(f" Found {len(articles)} articles\n")
    print("=" * 60)

    for title, description, source, sentiment, score in articles:
        print(f"\n {title[:80]}")
        print(f"   Source: {source} | Sentiment: {sentiment} ({score})")

        if description:
            text = f"{title}. {description}"
            print(f"   Summarising...")
            summary = summarise_article(text)
            print(f"  {summary}")

        print("-" * 60)


# -----------------------------------------------
# STEP 6: INTERACTIVE CHAT MODE
# -----------------------------------------------
def chat_mode():
    """Ask questions about your news articles"""

    print("\n🤖 AI News Chat Mode")
    print("   Ask anything about your news, for example:")
    print("   - 'What is the latest AI news?'")
    print("   - 'Summarise the top stories today'")
    print("   - 'What happened with Anthropic?'")
    print("   Type 'quit' to exit\n")

    articles = get_articles(limit=10)

    if not articles:
        print(" No articles found. Run main.py first!")
        return

    context = build_context(articles)
    print(f" Loaded {len(articles)} articles as context\n")
    print("=" * 60)

    while True:
        question = input("\n💬 You: ").strip()

        if question.lower() == "quit":
            print("👋 Goodbye!")
            break

        if not question:
            continue

        print("🤔 Thinking...")
        answer = chat_with_news(question, context)
        print(f"\n🤖 AI: {answer}")
        print("-" * 60)


# -----------------------------------------------
# MAIN MENU
# -----------------------------------------------
def main():
    print("\n AI News Intelligence Platform")
    print("=" * 60)
    print("1. Summarise latest news")
    print("2. Chat with your news")
    print("3. Exit")

    choice = input("\nChoose an option (1/2/3): ").strip()

    if choice == "1":
        summarise_latest_news()
    elif choice == "2":
        chat_mode()
    elif choice == "3":
        print("Goodbye!")
    else:
        print("Invalid choice, please enter 1, 2, or 3")
        main()


if __name__ == "__main__":
    main()