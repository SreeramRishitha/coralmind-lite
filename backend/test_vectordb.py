import chromadb
from sentence_transformers import SentenceTransformer

# Load local model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Sample GitHub issues
issues = [
    {"id": "1", "text": "OAuth token validation failing for new users"},
    {"id": "2", "text": "MCP transport connection timeout"},
    {"id": "3", "text": "Search results returning irrelevant sources"},
    {"id": "4", "text": "Database connection pool exhausted"},
    {"id": "5", "text": "Fix catalog ranking algorithm"},
    {"id": "6", "text": "Add Google Fonts community source"},
    {"id": "7", "text": "Authentication error when using GitHub OAuth"},
]

print("Creating ChromaDB collection...")
client = chromadb.Client()
collection = client.create_collection("github_issues")

print("Getting embeddings...")
texts = [issue["text"] for issue in issues]
embeddings = model.encode(texts).tolist()

print("Storing in ChromaDB...")
collection.add(
    embeddings=embeddings,
    documents=texts,
    ids=[issue["id"] for issue in issues]
)

print(f"Stored {len(issues)} issues in vector DB\n")

# Search
query = "login authentication problems"
print(f"Searching for: '{query}'")
query_embedding = model.encode([query]).tolist()[0]

results = collection.query(
    query_embeddings=[query_embedding],
    n_results=3
)

print("\nTop 3 similar issues:")
for doc, distance in zip(results["documents"][0], results["distances"][0]):
    print(f"  {doc} (distance: {distance:.3f})")