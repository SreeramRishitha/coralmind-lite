import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS incidents (
        id TEXT,
        issue_number INTEGER,
        service TEXT,
        description TEXT,
        severity TEXT,
        reported_at TEXT,
        status TEXT
    )''')
    c.execute("SELECT COUNT(*) FROM incidents")
    count = c.fetchone()["count"]
    if count == 0:
        incidents = [
            ("INC-001", 907, "catalog", "Search results returning irrelevant sources", "high", "2026-05-27T20:00:00Z", "open"),
            ("INC-002", 871, "mcp", "MCP transport failing for some clients", "high", "2026-05-27T18:00:00Z", "open"),
            ("INC-003", 913, "catalog", "Catalog metadata snapshots not caching correctly", "medium", "2026-05-27T10:00:00Z", "investigating"),
            ("INC-004", 901, "mcp", "Catalog discovery output too verbose", "low", "2026-05-26T14:00:00Z", "resolved"),
            ("INC-005", 792, "search", "Universal search returning stale metadata", "high", "2026-05-25T09:00:00Z", "open"),
            ("INC-006", 914, "notion", "Notion authorization docs link broken", "medium", "2026-05-28T08:00:00Z", "open"),
            ("INC-007", 922, "engine", "LIKE translation causing query failures", "high", "2026-05-28T09:00:00Z", "investigating"),
        ]
        c.executemany("INSERT INTO incidents VALUES (%s,%s,%s,%s,%s,%s,%s)", incidents)
    conn.commit()
    conn.close()

def get_all_incidents():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM incidents ORDER BY reported_at DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_incidents_for_issues(issue_numbers):
    if not issue_numbers:
        return []
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM incidents WHERE issue_number = ANY(%s)", (issue_numbers,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_incidents_by_status(status):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM incidents WHERE status = %s", (status,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]