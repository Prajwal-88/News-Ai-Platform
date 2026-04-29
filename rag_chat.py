import sqlite3
import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
import chromadb
from sentence_transformers import SentenceTransformer

# ✅ Load API key
load_dotenv()
HF_API_KEY = os.getenv("HF_API_KEY")

# ✅ AI client for answering questions
client = InferenceClient(
    provider="featherless-ai",
    api_key=HF_API_KEY,
)

# ✅ Embedding model — converts text to vectors
# This runs LOCALLY on your computer, no API needed!
print("⏳ Loading embedding model (first time takes ~30 seconds)...")
embedder = SentenceTransformer("all-MiniLM-L6-v2")
print("✅ Embedding model ready!\n")

# ✅ ChromaDB — local vector database
# Stores vectors in the rag/ folder
chroma_client = chromadb.PersistentClient(path="rag/")
collection = chroma_client.get_or_create_collection(name="news_articles")


# -----------------------------------------------
# STEP 1: GET ARTICLES FROM SQLITE DATABASE
# -----------------------------------------------
def get_articles_from_db(limit=50):
    """Fetch articles from SQLite"""

    conn = sqlite3.connect("data/news.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, description, source, sentiment
        FROM articles
        ORDER BY published_at DESC
        LIMIT ?
    """, (limit,))
    articles = cursor.fetchall()
    conn.close()
    return articles


# -----------------------------------------------
# STEP 2: STORE ARTICLES AS VECTORS IN CHROMADB
# -----------------------------------------------
def store_articles_in_vectordb():
    """Convert articles to vectors and store in ChromaDB"""

    print("📰 Loading articles from database...")
    articles = get_articles_from_db(limit=50)

    if not articles:
        print("❌ No articles found. Run main.py first!")
        return

    print(f"✅ Found {len(articles)} articles")
    print("🔢 Converting articles to vectors...")

    # Prepare data for ChromaDB
    ids        = []
    texts      = []
    metadatas  = []

    for article_id, title, description, source, sentiment in articles:

        # Combine title + description into one text
        text = f"{title}."
        if description:
            text += f" {description}"

        # Skip if already in ChromaDB
        existing = collection.get(ids=[str(article_id)])
        if existing["ids"]:
            continue

        ids.append(str(article_id))
        texts.append(text)
        metadatas.append({
            "title"    : title or "",
            "source"   : source or "",
            "sentiment": sentiment or "Neutral",
        })

    if not ids:
        print("✅ All articles already in vector database!")
        return

    # Convert texts to vectors using the embedding model
    # This is where the magic happens — text becomes numbers!
    embeddings = embedder.encode(texts).tolist()

    # Store in ChromaDB
    collection.add(
        ids        = ids,
        embeddings = embeddings,
        documents  = texts,
        metadatas  = metadatas,
    )

    print(f"✅ Stored {len(ids)} articles as vectors in ChromaDB!\n")


# -----------------------------------------------
# STEP 3: SEARCH FOR RELEVANT ARTICLES
# -----------------------------------------------
def search_relevant_articles(question, top_k=3):
    """
    Convert question to vector and find most similar articles.
    This is the CORE of RAG — semantic search!
    """

    # Convert question to a vector
    question_vector = embedder.encode([question]).tolist()

    # Search ChromaDB for most similar article vectors
    results = collection.query(
        query_embeddings = question_vector,
        n_results        = top_k,
    )

    # Extract the matched articles
    articles = []
    for i in range(len(results["ids"][0])):
        articles.append({
            "text"     : results["documents"][0][i],
            "title"    : results["metadatas"][0][i]["title"],
            "source"   : results["metadatas"][0][i]["source"],
            "sentiment": results["metadatas"][0][i]["sentiment"],
            "score"    : results["distances"][0][i],
        })

    return articles


# -----------------------------------------------
# STEP 4: ANSWER QUESTION USING RELEVANT ARTICLES
# -----------------------------------------------
def rag_chat(question):
    """
    Full RAG pipeline:
    1. Search for relevant articles
    2. Build context from those articles
    3. Send to AI for answer
    """

    print(f"\n🔍 Searching for relevant articles...")

    # Step 1 — Find relevant articles
    relevant_articles = search_relevant_articles(question, top_k=3)

    if not relevant_articles:
        return "❌ No relevant articles found.", []

    # Step 2 — Show which articles were found
    print(f"✅ Found {len(relevant_articles)} relevant articles:")
    for i, article in enumerate(relevant_articles):
        print(f"   {i+1}. {article['title'][:60]}...")
        print(f"      Source: {article['source']} | Sentiment: {article['sentiment']}")

    # Step 3 — Build context from ONLY relevant articles
    context = ""
    for i, article in enumerate(relevant_articles):
        context += f"Article {i+1}: {article['text']}\n\n"

    # Step 4 — Send to AI with focused context
    print(f"\n🤔 Asking AI based on relevant articles...")

    try:
        result = client.chat.completions.create(
            model="meta-llama/Llama-3.1-8B-Instruct",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a helpful news assistant.
                    Answer the question based ONLY on these relevant news articles:
                    {context}
                    Be specific and mention the sources."""
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            max_tokens=300,
        )

        answer = result.choices[0].message.content.strip()
        return answer, relevant_articles

    except Exception as e:
        return f"❌ Error: {str(e)[:120]}", []


# -----------------------------------------------
# STEP 5: INTERACTIVE RAG CHAT
# -----------------------------------------------
def rag_chat_mode():
    """Interactive RAG chat session"""

    print("\n🤖 RAG News Chat — Smarter AI with Vector Search")
    print("   Unlike before, AI now reads ONLY the most relevant articles!")
    print("   Type 'quit' to exit\n")
    print("=" * 60)

    while True:
        question = input("\n💬 You: ").strip()

        if question.lower() == "quit":
            print("👋 Goodbye!")
            break

        if not question:
            continue

        answer, sources = rag_chat(question)

        print(f"\n🤖 AI: {answer}")
        print("-" * 60)


# -----------------------------------------------
# MAIN
# -----------------------------------------------
def main():
    print("\n🚀 RAG News Intelligence System")
    print("=" * 60)
    print("1. Store articles in vector database")
    print("2. Chat using RAG (smarter answers)")
    print("3. Exit")

    choice = input("\nChoose an option (1/2/3): ").strip()

    if choice == "1":
        store_articles_in_vectordb()
        main()
    elif choice == "2":
        # Make sure articles are stored first
        total = collection.count()
        if total == 0:
            print("⚠️  Vector database is empty. Storing articles first...")
            store_articles_in_vectordb()
        else:
            print(f"✅ Vector database has {total} articles ready!")
        rag_chat_mode()
    elif choice == "3":
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")
        main()


if __name__ == "__main__":
    main()