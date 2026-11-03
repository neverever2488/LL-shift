
from pathlib import Path
import sqlite3

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# /docs is the database viewer; the automatic Swagger UI lives at /swagger instead.
app = FastAPI(title="Phase Shift API", docs_url="/swagger", redoc_url=None)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "leaderboard.db"
PAGE_PATH = BASE_DIR / "leaderboard.html"
DB_PAGE_PATH = BASE_DIR / "database.html"


class Score(BaseModel):
    nickname: str = Field(min_length=3, max_length=16)
    total_time: float = Field(gt=0)
    coins: int = Field(ge=0)
    skin: str
    played_on: str


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/")
def home():
    return {"message": "Phase Shift API is running"}


@app.post("/api/scores")
def add_score(score: Score):
    conn = get_connection()

    try:
        conn.execute("""
            INSERT INTO leaderboard
            (nickname, total_time, coins, skin, played_on)
            VALUES (?, ?, ?, ?, ?)
        """, (
            score.nickname,
            score.total_time,
            score.coins,
            score.skin,
            score.played_on
        ))

        conn.commit()
        return {"message": "Score saved successfully"}

    except sqlite3.Error:
        raise HTTPException(
            status_code=500,
            detail="Database error"
        )

    finally:
        conn.close()


@app.get("/leaderboard", include_in_schema=False)
def leaderboard_page():
    if not PAGE_PATH.exists():
        raise HTTPException(status_code=404, detail="leaderboard.html not found next to api.py")
    return FileResponse(PAGE_PATH)


@app.get("/docs", include_in_schema=False)
def database_page():
    if not DB_PAGE_PATH.exists():
        raise HTTPException(status_code=404, detail="database.html not found next to api.py")
    return FileResponse(DB_PAGE_PATH)


@app.get("/api/db")
def get_database():
    """Every row of the leaderboard table with all columns (newest first), read-only."""
    if not DB_PATH.exists():
        raise HTTPException(status_code=404, detail="Database not found")

    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT id, nickname, total_time, coins, skin, played_on, created_at
            FROM leaderboard
            ORDER BY id DESC
        """).fetchall()
        return {"table": "leaderboard", "count": len(rows), "rows": [dict(r) for r in rows]}
    finally:
        conn.close()


@app.get("/api/leaderboard")
def get_leaderboard(limit: int = Query(10, ge=1, le=1000)):
    if not DB_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="Database not found"
        )

    conn = get_connection()

    try:
        rows = conn.execute("""
            SELECT nickname, total_time, coins, skin, played_on
            FROM leaderboard
            ORDER BY total_time ASC, coins DESC, id ASC
            LIMIT ?
        """, (limit,)).fetchall()

        return {
            "count": len(rows),
            "results": [dict(row) for row in rows]
        }

    finally:
        conn.close()
