from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import time
from groq import Groq
import os
from dotenv import load_dotenv
from incidents import init_db, get_all_incidents, get_incidents_by_status, get_incidents_for_issues
import sentry_sdk
from deployments import generate_deployments_from_prs
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

cache = {}
CACHE_TTL = 300

INCIDENT_KEYWORDS = ["bug", "fail", "failure", "error", "timeout", "crash", "broken", "fix", "regression", "flake"]

class QuestionRequest(BaseModel):
    question: str
    owner: str = "withcoral"
    repo: str = "coral"

def run_coral(query: str):
    now = time.time()
    if query in cache:
        result, timestamp = cache[query]
        if now - timestamp < CACHE_TTL:
            return result
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
    cache[query] = (output, now)
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
def get_queries(question: str, owner: str, repo: str):
    q = question.lower()

    # MUST be first — contains "pr" which matches later branch
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

    elif any(w in q for w in ["merged", "closed", "done", "completed", "shipped"]):
        return [
            f"SELECT number, title, merged_at FROM github.pulls WHERE owner = '{owner}' AND repo = '{repo}' AND state = 'closed' LIMIT 10",
            f"SELECT i.number, i.title, i.state, p.merged_at FROM github.issues i JOIN github.pulls p ON i.number = p.number WHERE i.owner = '{owner}' AND i.repo = '{repo}' AND p.owner = '{owner}' AND p.repo = '{repo}' LIMIT 5"
        ]

    elif any(w in q for w in ["deploy", "deployment", "release", "released"]):
        return [
            f"SELECT number, title, merged_at FROM github.pulls WHERE owner = '{owner}' AND repo = '{repo}' AND state = 'closed' LIMIT 10",
            f"SELECT i.number, i.title, i.state FROM github.issues i JOIN github.pulls p ON i.number = p.number WHERE i.owner = '{owner}' AND i.repo = '{repo}' AND p.owner = '{owner}' AND p.repo = '{repo}' LIMIT 5"
        ]

    elif any(w in q for w in ["contributor", "who", "author", "top", "most active", "active", "people", "team", "works"]):
        return [
            f"SELECT login, contributions FROM github.repo_contributors WHERE owner = '{owner}' AND repo = '{repo}' LIMIT 10",
            f"SELECT number, title, state FROM github.pulls WHERE owner = '{owner}' AND repo = '{repo}' AND state = 'open' LIMIT 5"
        ]

    elif any(w in q for w in ["incident", "outage", "down", "service", "production", "alert", "severity"]):
        return [
            f"SELECT number, title, state, created_at FROM github.issues WHERE owner = '{owner}' AND repo = '{repo}' AND state = 'open' LIMIT 10",
            f"SELECT i.number, i.title, p.merged_at FROM github.issues i JOIN github.pulls p ON i.number = p.number WHERE i.owner = '{owner}' AND i.repo = '{repo}' AND p.owner = '{owner}' AND p.repo = '{repo}' LIMIT 5"
        ]

    elif any(w in q for w in ["bug", "fix", "error", "broken", "fail", "crash", "problem"]):
        return [
            f"SELECT number, title, state, created_at FROM github.issues WHERE owner = '{owner}' AND repo = '{repo}' AND state = 'open' LIMIT 10",
            f"SELECT i.number, i.title, i.state, p.created_at FROM github.issues i JOIN github.pulls p ON i.number = p.number WHERE i.owner = '{owner}' AND i.repo = '{repo}' AND p.owner = '{owner}' AND p.repo = '{repo}' LIMIT 5"
        ]

    elif any(w in q for w in ["pr", "pull request", "pull", "review"]):
        return [
            f"SELECT number, title, state, created_at FROM github.pulls WHERE owner = '{owner}' AND repo = '{repo}' AND state = 'open' LIMIT 10",
            f"SELECT i.number, i.title, i.state, p.created_at FROM github.issues i JOIN github.pulls p ON i.number = p.number WHERE i.owner = '{owner}' AND i.repo = '{repo}' AND p.owner = '{owner}' AND p.repo = '{repo}' LIMIT 5"
        ]

    elif any(w in q for w in ["feature", "new", "add", "added", "built", "implement"]):
        return [
            f"SELECT number, title, state, created_at FROM github.issues WHERE owner = '{owner}' AND repo = '{repo}' AND state = 'open' LIMIT 10",
            f"SELECT number, title, merged_at FROM github.pulls WHERE owner = '{owner}' AND repo = '{repo}' AND state = 'closed' LIMIT 5"
        ]

    else:
        return [
            f"SELECT i.number, i.title, i.state, p.created_at, p.merged_at FROM github.issues i JOIN github.pulls p ON i.number = p.number WHERE i.owner = '{owner}' AND i.repo = '{repo}' AND p.owner = '{owner}' AND p.repo = '{repo}' LIMIT 10",
            f"SELECT number, title, state, created_at FROM github.issues WHERE owner = '{owner}' AND repo = '{repo}' AND state = 'open' LIMIT 5"
        ]
def generate_summary(question: str, github_data: list, supporting_data: list, incidents: list):
    context = f"""You are an engineering intelligence assistant analyzing GitHub activity and operational incidents.

Answer this question directly: {question}

Primary data: {github_data}
Supporting data: {supporting_data}
Incident data: {incidents}

Rules:
- Be concise and specific, 2-3 sentences max
- Mention actual names, issue numbers, PR titles, and incident IDs when present
- Never say "the data does not provide" — summarize the closest relevant findings instead
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
@app.get("/debug-coral")
def debug_coral():
    import os
    coral_path = os.getenv("CORAL_PATH", "/app/coral")
    # Check if file exists
    exists = os.path.exists(coral_path)
    # Check config location
    config_paths = [
        "/root/.local/share/withcoral/coral/config/config.toml",
        "/root/.config/withcoral/coral/config/config.toml",
    ]
    config_found = {p: os.path.exists(p) for p in config_paths}
    # Run coral
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
class PRRequest(BaseModel):
    number: int
    owner: str = "withcoral"
    repo: str = "coral"

@app.post("/explain-pr")
async def explain_pr(data: PRRequest):
    query = f"SELECT number, title, body, state, user__login FROM github.pulls WHERE owner = '{data.owner}' AND repo = '{data.repo}' AND number = {data.number} LIMIT 1"
    raw = run_coral(query)
    
    # Don't use parse_coral_output — body field breaks table parsing
    # Extract fields directly from raw output
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
        # fallback: just send raw to AI
        body_text = raw
        title = f"PR #{data.number}"
    else:
        body_text = body

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
    queries = get_queries(data.question, data.owner, data.repo)
    q = data.question.lower()

    raw1 = run_coral(queries[0])
    raw2 = run_coral(queries[1])

    data1 = parse_coral_output(raw1)
    # Filter by username in Python since Coral can't filter nested fields
    if len(queries) > 2 and queries[2]:
        username = queries[2]
        data1 = [r for r in data1 if r.get("user__login", "").lower() == username.lower()]
    data2 = parse_coral_output(raw2)
    # Generate deployments from merged PRs
    merged_prs = [r for r in data1 if r.get("merged_at")]
    deployments = generate_deployments_from_prs(merged_prs)

    # Generate dynamic incidents from repo activity
    dynamic = generate_dynamic_incidents(data1)

    if any(w in q for w in ["incident", "outage", "down", "service", "alert", "severity", "sentry", "production"]):
        static = get_all_incidents()
        sentry = get_sentry_incidents()
        dynamic = generate_dynamic_incidents(data1)
        incidents = (sentry + static + dynamic)[:7]
    else:
        issue_numbers = [int(r["number"]) for r in data1 if r.get("number") and str(r.get("number","")).isdigit()]
        static = get_incidents_for_issues(issue_numbers)
        dynamic = generate_dynamic_incidents(data1)
        incidents = (static + dynamic)[:5]

    summary = generate_summary(data.question, data1, data2, incidents)

    return {
        "question": data.question,
        "owner": data.owner,
        "repo": data.repo,
        "summary": summary,
        "sources_used": ["github.issues", "github.pulls", "sentry.issues", "operational.insights","deployments"],
        "sql_queries": queries,
        "correlated_data": data1,
        "open_issues": data2,
        "incidents": incidents,
        "deployments":deployments,
    }