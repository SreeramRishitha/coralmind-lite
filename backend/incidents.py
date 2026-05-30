import sqlite3

def init_db():
    conn = sqlite3.connect("incidents.db")
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
    c.execute("DELETE FROM incidents")
    incidents = [
        ("INC-001", 907, "catalog", "Search results returning irrelevant sources", "high", "2026-05-27T20:00:00Z", "open"),
        ("INC-002", 871, "mcp", "MCP transport failing for some clients", "high", "2026-05-27T18:00:00Z", "open"),
        ("INC-003", 913, "catalog", "Catalog metadata snapshots not caching correctly", "medium", "2026-05-27T10:00:00Z", "investigating"),
        ("INC-004", 901, "mcp", "Catalog discovery output too verbose", "low", "2026-05-26T14:00:00Z", "resolved"),
        ("INC-005", 792, "search", "Universal search returning stale metadata", "high", "2026-05-25T09:00:00Z", "open"),
        ("INC-006", 914, "notion", "Notion authorization docs link broken", "medium", "2026-05-28T08:00:00Z", "open"),
        ("INC-007", 922, "engine", "LIKE translation causing query failures", "high", "2026-05-28T09:00:00Z", "investigating"),
    ]
    c.executemany("INSERT INTO incidents VALUES (?,?,?,?,?,?,?)", incidents)
    conn.commit()
    conn.close()

def get_all_incidents():
    conn = sqlite3.connect("incidents.db")
    c = conn.cursor()
    c.execute("SELECT * FROM incidents ORDER BY reported_at DESC")
    rows = c.fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]

def get_incidents_by_status(status: str):
    conn = sqlite3.connect("incidents.db")
    c = conn.cursor()
    c.execute("SELECT * FROM incidents WHERE status = ? ORDER BY reported_at DESC", (status,))
    rows = c.fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]

def get_incidents_for_issues(issue_numbers: list):
    if not issue_numbers:
        return []
    conn = sqlite3.connect("incidents.db")
    c = conn.cursor()
    placeholders = ",".join("?" * len(issue_numbers))
    c.execute(f"SELECT * FROM incidents WHERE issue_number IN ({placeholders})", issue_numbers)
    rows = c.fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]

def _row_to_dict(r):
    return {
        "id": r[0],
        "issue_number": r[1],
        "service": r[2],
        "description": r[3],
        "severity": r[4],
        "reported_at": r[5],
        "status": r[6]
    }