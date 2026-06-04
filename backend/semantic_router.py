import os
import httpx
import numpy as np

HF_TOKEN = os.getenv("HF_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2"

ROUTES = {
    "contributors": [
        "who are the top contributors",
        "who built this",
        "most active developers",
        "who works on this repo",
    ],
    "merged_prs": [
        "show merged pull requests",
        "what was recently shipped",
        "completed work",
        "what got merged",
    ],
    "open_issues": [
        "any bugs open",
        "show open issues",
        "what problems exist",
        "errors and bugs",
    ],
    "incidents": [
        "show incidents",
        "production outages",
        "sentry errors",
        "what is failing",
        "what broke in production",
    ],
    "active_work": [
        "what is being worked on",
        "current active work",
        "in progress items",
        "what is open right now",
    ],
}

def get_embeddings(texts: list):
    headers = {}
    if HF_TOKEN:
        headers["Authorization"] = f"Bearer {HF_TOKEN}"
    try:
        response = httpx.post(
            API_URL,
            headers=headers,
            json={"inputs": texts},
            timeout=30
        )
        return np.array(response.json())
    except Exception as e:
        return None

# Pre-compute route embeddings at startup
route_names = list(ROUTES.keys())
route_embeddings = []

for examples in ROUTES.values():
    embs = get_embeddings(examples)
    if embs is not None:
        route_embeddings.append(np.mean(embs, axis=0))
    else:
        route_embeddings.append(np.zeros(384))

route_embeddings = np.array(route_embeddings)

def get_route(question: str) -> str:
    emb = get_embeddings([question])
    if emb is None:
        return "active_work"  # fallback
    similarities = np.dot(emb[0], route_embeddings.T)
    return route_names[np.argmax(similarities)]