<p align="center">
  <img src="https://res.cloudinary.com/dnrnhtkyq/image/upload/v1780174379/WhatsApp_Image_2026-05-31_at_2.15.45_AM_van54k.jpg" alt="CoralMind Lite Logo" width="120" />
</p>

<h1 align="center">◈ CoralMind Lite</h1>

<p align="center">
  AI-powered engineering intelligence assistant for GitHub repositories and operational systems. Ask natural language questions about any GitHub repository — powered by Coral SQL.
</p>

<p align="center">
  <a href="https://coralmind-lite.vercel.app">🌐 Live Demo</a> •
  <a href="https://github.com/SreeramRishitha/coralmind-lite">📦 GitHub</a>
</p>

---

## What It Does

CoralMind Lite uses Coral's SQL runtime to query GitHub issues, pull requests, and contributor data across multiple tables, joins them, and correlates results with live production incidents from Sentry — then generates AI summaries using real cross-source data.

This is only possible because of Coral. Without Coral, this requires separate API calls, manual data merging, and custom glue code. With Coral, it's a SQL JOIN.

---

## Features

- 🔍 **Natural language querying** — ask anything about your repo in plain English
- 🤖 **AI-generated SQL** — Groq LLM dynamically generates Coral SQL for every question
- 📊 **Cross-source joins** — GitHub issues × pull requests × contributors × Sentry incidents
- 💬 **PR explanation on click** — click any PR number to get an AI explanation in the summary panel
- 🧠 **AI summaries** — powered by Groq llama-3.3-70b-versatile
- 🚨 **Live incident correlation** — Sentry errors correlated with GitHub activity
- 🚀 **Deployment tracking** — auto-generated deployment logs from merged PRs
- 🌐 **Works on any repo** — change owner/repo in the header to query any GitHub repository
- 💡 **Non-technical question handling** — greetings and off-topic questions get friendly AI responses

---

## Live Demo Questions

| Question | Coral Sources Used |
|---|---|
| "What is being worked on?" | `github.issues JOIN github.pulls` |
| "Show merged PRs" | `github.pulls WHERE state = 'closed'` |
| "Who are the top contributors?" | `github.repo_contributors` |
| "Show incidents" | `sentry.issues + incidents.db` |
| "Any bugs open?" | `github.issues WHERE state = 'open'` |
| "explain #990" | `github.pulls WHERE number = 990` |

---

## Core SQL Examples

**Cross-source join — Issues × Pull Requests**
```sql
SELECT i.number, i.title, i.state, p.created_at, p.merged_at
FROM github.issues i
JOIN github.pulls p ON i.number = p.number
WHERE i.owner = 'withcoral' AND i.repo = 'coral'
AND p.owner = 'withcoral' AND p.repo = 'coral'
LIMIT 10
```

**Contributor analytics**
```sql
SELECT login, contributions
FROM github.repo_contributors
WHERE owner = 'withcoral' AND repo = 'coral'
LIMIT 10
```

**Merged PR history**
```sql
SELECT number, title, merged_at
FROM github.pulls
WHERE owner = 'withcoral' AND repo = 'coral'
AND state = 'closed'
LIMIT 10
```

**Live Sentry incidents**
```sql
SELECT id, title, status, level
FROM sentry.issues
LIMIT 7
```

---

## Cross-Source Intelligence

CoralMind correlates GitHub development activity with live production incidents from Sentry — all queried through Coral's unified SQL interface.

| Source | What it answers |
|---|---|
| `github.issues` + `github.pulls` | What developers changed |
| `sentry.issues` | What broke in production |
| `github.repo_contributors` | Who is working on what |
| `incidents.db` | Operational incident history |

**Example Correlations**
- Issue #922 `feat: Safer LIKE translation` → Sentry error `TimeoutError: SQL query execution timeout`
- Issue #871 `feat(mcp): native Streamable HTTP` → Sentry error `MCP transport connection timeout`

---

## Architecture

```
User Question
      ↓
Non-technical classifier (Groq)
      ↓
AI SQL Generator (Groq → Coral SQL)
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
├── Stats Dashboard (github results, incidents, open issues)
├── AI Summary / PR Explanation Panel
├── Incident Cards with severity badges
├── Contributor Leaderboard (click name → see their PRs)
├── GitHub Data Cards (click PR → AI explanation)
├── Deployment Tracking
└── SQL Query Panel (expandable)
```

---

## Tech Stack

| Layer | Tech |
|---|---|
| Frontend | React + Vite |
| Backend | FastAPI (Python) |
| Data Layer | Coral SQL |
| Local Data | SQLite (incidents) |
| Error Monitoring | Sentry |
| AI | Groq — llama-3.3-70b-versatile |
| GitHub Sources | `github.issues`, `github.pulls`, `github.repo_contributors` |
| Deployment | Vercel (frontend) + Render (backend) |

---

## Setup

### Prerequisites
- Coral installed and configured
- Python 3.10+
- Node.js 18+

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
```
GROQ_API_KEY=your_groq_key_here
SENTRY_DSN=your_sentry_dsn_here
GITHUB_TOKEN=your_github_token_here
CORAL_PATH=/path/to/coral
```

---

## Deployment

- **Frontend**: Vercel — https://coralmind-lite.vercel.app
- **Backend**: Render — https://coralmind-lite-backend.onrender.com
- **Uptime**: UptimeRobot pings `/ping` every 5 minutes to prevent Render cold starts

---

## Future Scope

- Slack / Discord integrations
- Contributor activity timelines
- Engineering productivity metrics
- Semantic incident search
- Deployment intelligence dashboard
- Release analytics with trend graphs

---

CoralMind Lite demonstrates how Coral can unify engineering systems into a single SQL-powered intelligence layer.

## Team

| Name | Role |
|---|---|
| Manvitha Kopela | Coral SQL, GitHub data, Sentry integration, AI, backend |
| Sreeram Rishitha | Frontend, React UI, landing page, API integration |

---

<p align="center">Built for the <strong>Pirates of the Coral-bean Hackathon</strong> by WeMakeDevs × Coral</p>

<p align="center">
  <img src="https://res.cloudinary.com/dnrnhtkyq/image/upload/v1780174379/WhatsApp_Image_2026-05-31_at_2.15.45_AM_van54k.jpg" alt="CoralMind" width="60" />
</p>
