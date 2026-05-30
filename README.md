# ◈ CoralMind Lite

<p align="center">
  <img src="./assets/logo.png" alt="CoralMind Lite Logo" width="220"/>
</p>

> AI-powered engineering intelligence assistant.
> Ask natural language questions about any GitHub repository — powered by Coral SQL.

---

## What It Does

CoralMind Lite uses Coral's SQL runtime to query GitHub issues, pull requests,
and contributor data across multiple tables, joins them, and correlates results
with live production incidents from Sentry — then generates AI summaries using
real cross-source data.

**This is only possible because of Coral.**
Without Coral, this requires separate API calls, manual data merging, and custom
glue code. With Coral, it's a SQL JOIN.

---

## Live Demo Questions

| Question                        | Coral Sources Used                    |
| ------------------------------- | ------------------------------------- |
| "What is being worked on?"      | `github.issues` JOIN `github.pulls`   |
| "Show merged PRs"               | `github.pulls WHERE state = 'closed'` |
| "Who are the top contributors?" | `github.repo_contributors`            |
| "Show incidents"                | `sentry.issues` + `incidents.db`      |
| "Any bugs open?"                | `github.issues WHERE state = 'open'`  |

---

## Core SQL Examples

### Cross-source join — Issues × Pull Requests

```sql
SELECT i.number, i.title, i.state, p.created_at, p.merged_at
FROM github.issues i
JOIN github.pulls p ON i.number = p.number
WHERE i.owner = 'withcoral' AND i.repo = 'coral'
AND p.owner = 'withcoral' AND p.repo = 'coral'
LIMIT 10
```

### Contributor analytics

```sql
SELECT login, contributions
FROM github.repo_contributors
WHERE owner = 'withcoral' AND repo = 'coral'
LIMIT 10
```

### Merged PR history

```sql
SELECT number, title, merged_at
FROM github.pulls
WHERE owner = 'withcoral' AND repo = 'coral'
AND state = 'closed'
LIMIT 10
```

### Live Sentry incidents

```sql
SELECT id, title, status, level
FROM sentry.issues
LIMIT 7
```

---

## Cross-Source Intelligence

CoralMind correlates GitHub development activity with live production incidents
from Sentry — all queried through Coral's unified SQL interface.

| Source                           | What it answers              |
| -------------------------------- | ---------------------------- |
| `github.issues` + `github.pulls` | What developers changed      |
| `sentry.issues`                  | What broke in production     |
| `github.repo_contributors`       | Who is working on what       |
| `incidents.db`                   | Operational incident history |

### Example Correlations

* Issue `#922 feat: Safer LIKE translation` → Sentry error `TimeoutError: SQL query execution timeout`
* Issue `#871 feat(mcp): native Streamable HTTP` → Sentry error `MCP transport connection timeout`

---

## Architecture

```text
User Question
      ↓
Question Router (keyword-aware)
      ↓
Coral SQL Runtime
├── github.issues
├── github.pulls
├── github.repo_contributors
└── sentry.issues (live production errors)
      ↓
SQLite — incidents.db (operational history)
      ↓
Groq AI (llama-3.3-70b-versatile)
      ↓
React Frontend
├── Landing Page with typing animation
├── AI Summary
├── Incident Cards
├── GitHub Data Cards
└── SQL Query Panel
```

---

## Tech Stack

| Layer            | Tech                                                  |
| ---------------- | ----------------------------------------------------- |
| Frontend         | React + Vite                                          |
| Backend          | FastAPI (Python)                                      |
| Data Layer       | Coral SQL                                             |
| Local Data       | SQLite (incidents)                                    |
| Error Monitoring | Sentry                                                |
| AI               | Groq — llama-3.3-70b-versatile                        |
| GitHub Sources   | github.issues, github.pulls, github.repo_contributors |

---

## Setup

### Prerequisites

* Coral installed and configured
* Python 3.10+
* Node.js 18+

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Coral Sources

```bash
coral source add --interactive github
coral source add --interactive sentry
```

### Environment Variables

```env
GROQ_API_KEY=your_groq_key_here
SENTRY_DSN=your_sentry_dsn_here
```

---

## Note on Deployment

Coral is a local-first runtime — credentials and data never leave your machine.

The frontend is deployed on Vercel.
The backend runs locally with Coral querying live GitHub and Sentry data during demos.

---

## Future Scope

Future versions could support:

* Deployment log correlation
* Release analytics dashboard
* Slack integrations
* Discord integrations
* Contributor activity timelines
* Engineering productivity metrics
* Semantic incident search
* Deployment intelligence

---

## Team

| Name             | Role                                                    |
| ---------------- | ------------------------------------------------------- |
| Manvitha Kopela  | Coral SQL, GitHub data, Sentry integration, AI, backend |
| Sreeram Rishitha | Frontend, React UI, landing page, API integration       |

Built for the **Pirates of the Coral-bean Hackathon** by WeMakeDevs × Coral.

---

## License

MIT
