import chromadb
import os
from groq import Groq

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = chromadb.Client()
try:
    client.delete_collection("github_issues")
except:
    pass
collection = client.create_collection("github_issues")

def get_embeddings(texts: list):
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
        embeddings = []
        for text in texts:
            response = groq_client.embeddings.create(
                model="nomic-embed-text-v1_5",
                input=text
            )
            embeddings.append(response.data[0].embedding)
        return embeddings
    except Exception as e:
        print(f"Groq embedding error: {e}")
        return None

def index_issues(issues: list, owner: str, repo: str):
    if not issues:
        return
    texts = []
    ids = []
    metadatas = []
    for issue in issues:
        number = str(issue.get("number", ""))
        title = issue.get("title", "")
        if not number or not title:
            continue
        texts.append(title)
        ids.append(f"{owner}_{repo}_{number}")
        metadatas.append({"number": number, "state": issue.get("state", ""), "owner": owner, "repo": repo})
    if not texts:
        return
    try:
        existing = collection.get()
        if existing["ids"]:
            collection.delete(ids=existing["ids"])
    except:
        pass
    embeddings = get_embeddings(texts)
    if embeddings is None:
        return
    collection.add(embeddings=embeddings, documents=texts, ids=ids, metadatas=metadatas)

def search_issues(query: str, owner: str, repo: str, n_results: int = 5):
    try:
        query_embedding = get_embeddings([query])
        if query_embedding is None:
            return []
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        matches = []
        for doc, meta, distance in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
            if meta.get("owner") == owner and meta.get("repo") == repo:
                matches.append({"number": meta["number"], "title": doc, "state": meta["state"], "similarity": round(1 - distance, 3)})
        return matches
    except Exception as e:
        print(f"Search error: {e}")
        return []