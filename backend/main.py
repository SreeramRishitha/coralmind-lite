from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import time
import json
from groq import Groq
import os
from dotenv import load_dotenv
from incidents import init_db, get_all_incidents, get_incidents_by_status, get_incidents_for_issues
import sentry_sdk
from deployments import generate_deployments_from_prs
import redis as redis_client
load_dotenv()
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    traces_sample_rate=0.1,
    send_default_pii=False
)
init_db()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CORAL_PATH = os.getenv("CORAL_PATH", "/app/coral")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

REDIS_URL = os.getenv("REDIS_URL")
try:
    cache = redis_client.from_url(REDIS_URL) if REDIS_URL else None
except:
    cache = None
CACHE_TTL = 300

INCIDENT_KEYWORDS = ["bug", "fail", "failure", "error", "timeout", "crash", "broken", "fix", "regression", "flake"]

class QuestionRequest(BaseModel):
    question: str
    owner: str = "withcoral"
    repo: str = "coral"

class PRRequest(BaseModel):
    number: int
    owner: str = "withcoral"
    repo: str = "coral"

def run_coral(query: str):
    if cache:
        try:
            cached = cache.get(query)
            if cached:
                return cached.decode("utf-8")
        except:
            pass

    try:
        result = subprocess.run(
            [CORAL_PATH, "sql", query],
            capture_output=True,
            text=True,
            timeout=30
        )
        output = result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
    except subprocess.TimeoutExpired:
        output = "Error: Query timed out. Try again."

    if cache:
        try:
            cache.set(query, output, ex=CACHE_TTL)
        except:
            pass

    return output

def parse_coral_output(raw: str):
    rows = []
    lines = raw.strip().split("\n")
    data_lines = [l for l in lines if l.startswith("|") and "---" not in l]
    if len(data_lines) < 2:
        return rows
    headers = [h.strip() for h in data_lines[0].split("|")[1:-1]]
    for line in data_lines[1:]:
        values = [v.strip() for v in line.split("|")[1:-1]]
        if len(values) == len(headers):
            rows.append(dict(zip(headers, values)))
    return rows

def generate_dynamic_incidents(issues: list):
    incidents = []
    for idx, issue in enumerate(issues):
        title = issue.get("title", "").lower()
        if any(word in title for word in INCIDENT_KEYWORDS):
            if any(w in title for w in ["fail", "crash", "error", "timeout", "regression"]):
                severity = "high"
            elif any(w in title for w in ["bug", "broken", "flake"]):
                severity = "medium"
            else:
                severity = "low"
            try:
                service = title.split("(")[1].split(")")[0] if "(" in title else "general"
            except:
                service = "general"
            incidents.append({
                "id": f"DYN-{idx+1:03}",
                "issue_number": str(issue.get("number", "")),
                "service": service,
                "description": issue.get("title", "")[:80],
                "severity": severity,
                "reported_at": "live",
                "status": "investigating"
            })
    return incidents[:5]

def get_sentry_incidents():
    query = "SELECT id, title, status, level FROM sentry.issues LIMIT 7"
    raw = run_coral(query)
    rows = parse_coral_output(raw)
    incidents = []
    for row in rows:
        incidents.append({
            "id": row.get("id", ""),
            "issue_number": "",
            "service": "sentry",
            "description": row.get("title", ""),
            "severity": "high" if row.get("level") == "error" else "medium",
            "reported_at": "live",
            "status": row.get("status", "unresolved")
        })
    return incidents

def is_technical_question(question: str) -> bool:
    non_technical = [
        "hi", "hii", "hello", "hey", "howdy", "sup", "what's up", "whats up",
        "how are you", "who are you", "what are you", "what is coral",
        "good morning", "good evening", "good night", "thanks", "thank you",
        "ok", "okay", "cool", "nice", "bye", "goodbye"
    ]
    if question.lower().strip() in non_technical:
        return False
    try:
        client = Groq(api_key=GROQ_API_KEY)
        check = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": f'Is this question about software engineering, GitHub, code, repositories, commits, PRs, issues, incidents, or deployments? Answer only YES or NO.\nQuestion: "{question}"'}],
            max_tokens=5
        )
        return "YES" in check.choices[0].message.content.upper()
    except:
        return True

def answer_non_technical(question: str) -> str:
    try:
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": f'You are CoralMind, an AI engineering assistant that helps developers understand their GitHub repositories. Answer this conversationally and briefly: "{question}"'}],
            max_tokens=150
        )
        return response.choices[0].message.content
    except:
        return "Hi! I'm CoralMind, your AI engineering assistant. Ask me about your repository — try 'show incidents', 'who are the top contributors', or 'explain #990'."
def generate_sql_from_question(question: str, owner: str, repo: str):
    from semantic_router import get_route
    q = question.lower()

    # "prs by username" — must stay first
    if "prs by " in q or "pulls by " in q or "raised by " in q:
        for keyword in ["prs by ", "pulls by ", "raised by "]:
            if keyword in q:
                username = q.split(keyword)[-1].strip().strip("@").strip()
                break
        return [
            f"SELECT number, title, state, user__login, created_at, merged_at FROM github.pulls WHERE owner = '{owner}' AND repo = '{repo}' LIMIT 1000",
            f"SELECT number, title, state FROM github.issues WHERE owner = '{owner}' AND repo = '{repo}' AND state = 'open' LIMIT 5",
            username
        ]

    # Semantic routing
    route = get_route(question)

    if route == "contributors":
        return [
            f"SELECT login, contributions FROM github.repo_contributors WHERE owner = '{owner}' AND repo = '{repo}' LIMIT 10",
            f"SELECT login, contributions FROM github.repo_contributors WHERE owner = '{owner}' AND repo = '{repo}' LIMIT 5"
        ]
    elif route == "merged_prs":
        return [
            f"SELECT number, title, state, merged_at, user__login FROM github.pulls WHERE owner = '{owner}' AND repo = '{repo}' AND state = 'closed' LIMIT 10",
            f"SELECT number, title, merged_at FROM github.pulls WHERE owner = '{owner}' AND repo = '{repo}' AND state = 'closed' LIMIT 5"
        ]
    elif route == "open_issues":
        return [
            f"SELECT number, title, state FROM github.issues WHERE owner = '{owner}' AND repo = '{repo}' AND state = 'open' LIMIT 10",
            f"SELECT number, title, state FROM github.issues WHERE owner = '{owner}' AND repo = '{repo}' AND state = 'open' LIMIT 5"
        ]
    elif route == "incidents":
        return [
            f"SELECT number, title, state FROM github.issues WHERE owner = '{owner}' AND repo = '{repo}' LIMIT 10",
            f"SELECT id, title, status, level FROM sentry.issues LIMIT 5"
        ]
    elif route == "active_work":
        return [
            f"SELECT number, title, state, created_at FROM github.issues WHERE owner = '{owner}' AND repo = '{repo}' AND state = 'open' LIMIT 10",
            f"SELECT number, title, state FROM github.pulls WHERE owner = '{owner}' AND repo = '{repo}' AND state = 'open' LIMIT 5"
        ]

    # AI-generated SQL for everything else
    prompt = f"""You are a SQL expert for Coral, a SQL runtime that queries GitHub and other sources.

Generate exactly 2 SQL queries to answer this question: "{question}"

Available tables:
- github.issues: number, title, state, created_at, closed_at (filter: owner='{owner}', repo='{repo}')
- github.pulls: number, title, state, created_at, merged_at, user__login (filter: owner='{owner}', repo='{repo}')
- github.repo_contributors: login, contributions (filter: owner='{owner}', repo='{repo}')
- sentry.issues: id, title, status, level

Rules:
- Always include WHERE owner='{owner}' AND repo='{repo}' for github tables
- Use LIMIT 10 on first query, LIMIT 5 on second
- Never use SELECT * — always specify columns explicitly
- Only use these columns: number, title, state, created_at, merged_at, user__login, login, contributions, id, level, status
- Return ONLY a JSON object like: {{"query1": "SELECT ...", "query2": "SELECT ..."}}
- No explanation, no markdown, just the JSON"""

    try:
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )
        text = response.choices[0].message.content.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(text)
        return [parsed.get("query1", ""), parsed.get("query2", "")]
    except Exception as e:
        return [
            f"SELECT number, title, state, created_at FROM github.issues WHERE owner = '{owner}' AND repo = '{repo}' AND state = 'open' LIMIT 10",
            f"SELECT number, title, state FROM github.pulls WHERE owner = '{owner}' AND repo = '{repo}' AND state = 'open' LIMIT 5"
        ]
    
def generate_summary(question: str, github_data: list, supporting_data: list, incidents: list, similar_issues: list = []):
    github_str = str(github_data[:10])[:2000]
    supporting_str = str(supporting_data[:5])[:800]
    incidents_str = str(incidents[:5])[:800]
    similar_str = str(similar_issues[:3])[:500]

    context = f"""You are an engineering intelligence assistant analyzing GitHub activity and operational incidents.

Answer this question directly: {question}

Primary data: {github_str}
Supporting data: {supporting_str}
Incident data: {incidents_str}
Semantically similar issues: {similar_str}

Rules:
- Be concise and specific, 2-3 sentences max
- Mention actual names, issue numbers, PR titles, and incident IDs when present
- Use similar issues to provide better context
- Write like an internal engineering insights tool, not a chatbot"""
    try:
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": context}],
            max_tokens=250
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Summary unavailable: {str(e)}"

@app.get("/")
def home():
    return {"status": "CoralMind Lite is running"}

@app.get("/ping")
def ping():
    return {"status": "alive"}

@app.get("/debug-coral")
def debug_coral():
    coral_path = os.getenv("CORAL_PATH", "/app/coral")
    exists = os.path.exists(coral_path)
    config_paths = [
        "/root/.local/share/withcoral/coral/config/config.toml",
        "/root/.config/withcoral/coral/config/config.toml",
    ]
    config_found = {p: os.path.exists(p) for p in config_paths}
    raw = run_coral("SELECT login, contributions FROM github.repo_contributors WHERE owner = 'withcoral' AND repo = 'coral' LIMIT 5")
    return {
        "coral_path": coral_path,
        "coral_exists": exists,
        "config_found": config_found,
        "raw_output": raw,
        "github_token_set": bool(os.getenv("GITHUB_TOKEN")),
    }

@app.get("/debug-pulls")
def debug_pulls():
    raw = run_coral("SELECT * FROM github.pulls WHERE owner = 'sugarlabs' AND repo = 'musicblocks' LIMIT 1")
    return {"raw": raw}
@app.get("/debug-embeddings")
def debug_embeddings():
    try:
        from vector_store import get_embeddings
        result = get_embeddings(["test connection issue"])
        return {"status": "ok", "type": str(type(result)), "length": len(result) if result else 0, "sample": str(result)[:200] if result else None}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.post("/explain-pr")
async def explain_pr(data: PRRequest):
    query = f"SELECT number, title, body, state, user__login FROM github.pulls WHERE owner = '{data.owner}' AND repo = '{data.repo}' AND number = {data.number} LIMIT 1"
    raw = run_coral(query)
    title = ""
    state = ""
    author = ""
    body = ""
    for line in raw.split("\n"):
        line = line.strip()
        if line.startswith("|") and "---" not in line and "number" not in line.lower()[:20]:
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 4 and parts[0].isdigit():
                title = parts[1]
                body = parts[2]
                state = parts[3]
                author = parts[4] if len(parts) > 4 else ""
                break
    if not title:
        body_text = raw[:2000]
        title = f"PR #{data.number}"
    else:
        body_text = body[:2000]
    context = f"""Explain this GitHub pull request clearly for an engineer.

Title: {title}
Author: {author}
State: {state}
Body: {body_text}

Give a 3-4 sentence explanation: what problem it solves, what changed, and why it matters."""
    try:
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": context}],
            max_tokens=250
        )
        return {"explanation": response.choices[0].message.content, "pr": {"number": data.number, "title": title}}
    except Exception as e:
        return {"explanation": f"Unavailable: {str(e)}", "pr": None}

@app.post("/ask")
async def ask(data: QuestionRequest):
    q = data.question.lower()

    if not is_technical_question(data.question):
        return {
            "question": data.question,
            "owner": data.owner,
            "repo": data.repo,
            "summary": answer_non_technical(data.question),
            "sources_used": [],
            "sql_queries": [],
            "correlated_data": [],
            "open_issues": [],
            "incidents": [],
            "deployments": [],
        }

    queries = generate_sql_from_question(data.question, data.owner, data.repo)

    raw1 = run_coral(queries[0])
    raw2 = run_coral(queries[1])

    data1 = parse_coral_output(raw1)[:10]

    if len(queries) > 2 and queries[2]:
        username = queries[2]
        data1 = [r for r in data1 if r.get("user__login", "").lower() == username.lower()]

    data2 = parse_coral_output(raw2)[:5]
    # Search vector DB for semantically similar issues
    try:
        from vector_store import index_issues, search_issues
        index_issues(data1, data.owner, data.repo)
        similar_issues = search_issues(data.question, data.owner, data.repo, n_results=3)
        print(f"Similar issues found: {similar_issues}")
    except Exception as e:
        print(f"Vector store error: {e}")
        similar_issues = []         

    merged_prs = [r for r in data1 if r.get("merged_at")]
    deployments = generate_deployments_from_prs(merged_prs)

    if any(w in q for w in ["incident", "outage", "down", "service", "alert", "severity", "sentry", "production"]):
        static = get_all_incidents()
        sentry = get_sentry_incidents()
        dynamic = generate_dynamic_incidents(data1)
        incidents = (sentry + static + dynamic)[:7]
    else:
        issue_numbers = [int(r["number"]) for r in data1 if r.get("number") and str(r.get("number", "")).isdigit()]
        static = get_incidents_for_issues(issue_numbers)
        dynamic = generate_dynamic_incidents(data1)
        incidents = (static + dynamic)[:5]

    summary = generate_summary(data.question, data1, data2, incidents, similar_issues)

    active_sources = []
    if data1 or data2:
        active_sources = ["github.issues", "github.pulls"]
    if incidents:
        active_sources += ["sentry.issues", "operational.insights"]
    if deployments:
        active_sources.append("deployments")

    return {
        "question": data.question,
        "owner": data.owner,
        "repo": data.repo,
        "summary": summary,
        "sources_used": active_sources,
        "sql_queries": queries,
        "correlated_data": data1,
        "open_issues": data2,
        "incidents": incidents,
        "deployments": deployments,
        "similar_issues": similar_issues,
    }