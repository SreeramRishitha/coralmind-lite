import chromadb
import os
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.Client()

# Create collection
try:
    collection = client.get_collection("github_issues")
except:
    collection = client.create_collection("github_issues")

def index_issues(issues: list, owner: str, repo: str):
    if not issues:
        return
    
    texts = []
    ids = []
    metadatas = []
    
    for issue in issues:
        number = str(issue.get("number", ""))
        title = issue.get("title", "")
        state = issue.get("state", "")
        
        if not number or not title:
            continue
            
        texts.append(title)
        ids.append(f"{owner}_{repo}_{number}")
        metadatas.append({
            "number": number,
            "state": state,
            "owner": owner,
            "repo": repo
        })
    
    if not texts:
        return
    
    # Remove existing entries for this repo
    try:
        existing = collection.get(
            where={"owner": owner, "repo": repo}
        )
        if existing["ids"]:
            collection.delete(ids=existing["ids"])
    except:
        pass
    
    embeddings = model.encode(texts).tolist()
    
    collection.add(
        embeddings=embeddings,
        documents=texts,
        ids=ids,
        metadatas=metadatas
    )
    
    print(f"Indexed {len(texts)} issues for {owner}/{repo}")

def search_issues(query: str, owner: str, repo: str, n_results: int = 5):
    try:
        query_embedding = model.encode([query]).tolist()[0]
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        matches = []
        for doc, meta, distance in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ):
            # Filter by owner/repo manually
            if meta.get("owner") == owner and meta.get("repo") == repo:
                matches.append({
                    "number": meta["number"],
                    "title": doc,
                    "state": meta["state"],
                    "similarity": round(1 - distance, 3)
                })
        return matches
    except Exception as e:
        print(f"Search error: {e}")
        return []