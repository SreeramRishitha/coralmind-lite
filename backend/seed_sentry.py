# seed_sentry.py - replace with this
import sentry_sdk
import time
import os
from dotenv import load_dotenv
load_dotenv()

sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))

errors = [
    ("MCP transport connection timeout", ValueError),
    ("Catalog search returning irrelevant results", RuntimeError),
    ("GitHub OAuth token validation failed", PermissionError),
    ("SQL query execution timeout in engine", TimeoutError),
    ("Source connector authentication error", ConnectionError),
    ("Database connection pool exhausted", MemoryError),
    ("API rate limit exceeded for github source", Exception),
]

for msg, exc_type in errors:
    try:
        raise exc_type(msg)
    except Exception as e:
        sentry_sdk.capture_exception(e)
        print(f"Sent: {msg}")
    time.sleep(3)

print("Done.")