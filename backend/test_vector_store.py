# test_vector_store.py
from vector_store import index_issues, search_issues

issues = [
    {"number": "871", "title": "MCP transport connection timeout", "state": "open"},
    {"number": "907", "title": "Search results returning irrelevant sources", "state": "open"},
    {"number": "913", "title": "Catalog metadata snapshots not caching", "state": "open"},
    {"number": "914", "title": "Notion authorization docs link broken", "state": "open"},
    {"number": "922", "title": "LIKE translation causing query failures", "state": "open"},
    {"number": "792", "title": "Universal search returning stale metadata", "state": "open"},
    {"number": "801", "title": "OAuth token validation failing", "state": "open"},
]

print("Indexing issues...")
index_issues(issues, "withcoral", "coral")

print("\nSearching for 'connection problems'...")
results = search_issues("connection problems", "withcoral", "coral")
for r in results:
    print(f"  #{r['number']} {r['title']} (similarity: {r['similarity']})")

print("\nSearching for 'search not working'...")
results = search_issues("search not working", "withcoral", "coral")
for r in results:
    print(f"  #{r['number']} {r['title']} (similarity: {r['similarity']})")