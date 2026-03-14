import hashlib
import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = Path("/data/catalog.db")
_conn: sqlite3.Connection | None = None


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL")
    return _conn


def init_db() -> None:
    """Create catalog table if it doesn't exist."""
    conn = _get_conn()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS catalog (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            prompt TEXT NOT NULL,
            category TEXT NOT NULL,
            style TEXT NOT NULL,
            model_used TEXT NOT NULL,
            result_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_catalog_name ON catalog(name)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_catalog_category ON catalog(category)")
    conn.commit()
    logger.info("Catalog DB initialized at %s", DB_PATH)


def generate_id(prompt: str, category: str, style: str, model: str) -> str:
    """Deterministic SHA256 hash for dedup."""
    key = f"{prompt}|{category}|{style}|{model}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def add_to_catalog(
    prompt: str,
    category: str,
    style: str,
    model_used: str,
    result: dict,
) -> str:
    """Insert a generation result into the catalog. Returns the item ID."""
    item_id = generate_id(prompt, category, style, model_used)
    name = result.get("name", prompt[:50])
    conn = _get_conn()
    conn.execute(
        """
        INSERT OR IGNORE INTO catalog (id, name, prompt, category, style, model_used, result_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            item_id,
            name,
            prompt,
            category,
            style,
            model_used,
            json.dumps(result),
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    return item_id


def get_catalog_list(
    search: str | None = None,
    category: str | None = None,
    limit: int = 200,
) -> list[dict]:
    """Lightweight listing (no result_json)."""
    conn = _get_conn()
    query = "SELECT id, name, prompt, category, style, model_used, created_at FROM catalog"
    conditions = []
    params: list = []

    if search:
        conditions.append("name LIKE ?")
        params.append(f"%{search}%")
    if category:
        conditions.append("category = ?")
        params.append(category)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def get_catalog_item(item_id: str) -> dict | None:
    """Full model data by ID."""
    conn = _get_conn()
    row = conn.execute("SELECT * FROM catalog WHERE id = ?", (item_id,)).fetchone()
    if row is None:
        return None
    item = dict(row)
    item["result"] = json.loads(item.pop("result_json"))
    return item
