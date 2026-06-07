import chromadb
import httpx
import os

HF_TOKEN = os.getenv("HF_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2"

client = chromadb.Client()
try:
    client.delete_collection("github_issues")
except:
    pass
collection = client.create_collection("github_issues")

def get_embeddings(texts: list):
    headers = {}
    if HF_TOKEN:
        headers["Authorization"] = f"Bearer {HF_TOKEN}"
    try:
        response = httpx.post(API_URL, headers=headers, json={"inputs": texts}, timeout=30)
        result = response.json()
        # Check if HF returned an error
        if isinstance(result, dict) and "error" in result:
            print(f"HF API error: {result}")
            return None
        return result
    except Exception as e:
        print(f"HF API exception: {e}")
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
        results = collection.query(query_embeddings=[query_embedding], n_results=n_results)
        matches = []
        for doc, meta, distance in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
            if meta.get("owner") == owner and meta.get("repo") == repo:
                matches.append({"number": meta["number"], "title": doc, "state": meta["state"], "similarity": round(1 - distance, 3)})
        return matches
    except Exception as e:
        return []