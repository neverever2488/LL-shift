"""Phase Shift API: serveris, kas saglabā spēles rezultātus datubāzē un nodod tos spēlei un lapām."""

from pathlib import Path
import sqlite3

# FastAPI: ietvars, ar kuru izveidots serveris; HTTPException izmanto kļūdu atgriešanai;
# Query ļauj iestatīt URL parametrus (piemēram, ?limit=10); FileResponse atdod HTML failu
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
# Pydantic: automātiski pārbauda, vai saņemtie dati ir pareizi
from pydantic import BaseModel, Field

# Adrese /docs ir datubāzes skats, tāpēc automātiskā Swagger dokumentācija pārcelta uz /swagger.
app = FastAPI(title="Phase Shift API", docs_url="/swagger", redoc_url=None)

# Visi ceļi tiek rēķināti no šī faila atrašanās vietas, tāpēc serveris vienmēr atrod datubāzi
# un lapas, neatkarīgi no tā, no kurienes tas palaists.
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "leaderboard.db"          # vienīgā datubāze
PAGE_PATH = BASE_DIR / "leaderboard.html"      # rezultātu tabulas lapa
DB_PAGE_PATH = BASE_DIR / "database.html"      # datubāzes skata lapa


# Rezultāta apraksts: tieši šādus datus nosūta spēle.
# Ja dati neatbilst noteikumiem (piemēram, segvārds par īsu), FastAPI pats atgriež kļūdu.
class Score(BaseModel):
    nickname: str = Field(min_length=3, max_length=16)   # segvārds: 3-16 rakstzīmes
    total_time: float = Field(gt=0)                      # laiks sekundēs (lielāks par 0)
    coins: int = Field(ge=0)                             # monētas (ne mazāk par 0)
    skin: str                                            # varoņa izskata ID
    played_on: str                                       # spēles datums


# Atver savienojumu ar datubāzi.
# row_factory = sqlite3.Row ļauj pārvērst rindas vārdnīcās (dict).
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# Pārbaude, vai serveris darbojas
@app.get("/")
def home():
    return {"message": "Phase Shift API is running"}


# Saglabā jaunu rezultātu datubāzē (to izsauc spēle, kad spēlētājs pabeidz visus līmeņus)
@app.post("/api/scores")
def add_score(score: Score):
    conn = get_connection()

    try:
        # Vērtības tiek nodotas caur ? (nevis ievietotas tekstā), lai nevarētu iesūtīt kaitīgu SQL kodu
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

        conn.commit()  # apstiprina izmaiņas, citādi ieraksts netiktu saglabāts
        return {"message": "Score saved successfully"}

    except sqlite3.Error:
        # Ja ar datubāzi kaut kas nogāja greizi, atgriež kļūdu 500
        raise HTTPException(
            status_code=500,
            detail="Database error"
        )

    finally:
        # Savienojums tiek aizvērts vienmēr, arī kļūdas gadījumā
        conn.close()


# Rezultātu tabulas lapa pārlūkprogrammā (adrese /leaderboard)
@app.get("/leaderboard", include_in_schema=False)
def leaderboard_page():
    if not PAGE_PATH.exists():
        raise HTTPException(status_code=404, detail="leaderboard.html not found next to api.py")
    return FileResponse(PAGE_PATH)


# Datubāzes skata lapa pārlūkprogrammā (adrese /docs)
@app.get("/docs", include_in_schema=False)
def database_page():
    if not DB_PAGE_PATH.exists():
        raise HTTPException(status_code=404, detail="database.html not found next to api.py")
    return FileResponse(DB_PAGE_PATH)


# Atdod visas tabulas rindas ar visām kolonnām (jaunākās pirmās); to izmanto lapa /docs
@app.get("/api/db")
def get_database():
    """Katra leaderboard tabulas rinda ar visām kolonnām (jaunākās pirmās), tikai lasīšanai."""
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


# Atdod labākos rezultātus; to izmanto gan spēle, gan lapa /leaderboard.
# Parametrs ?limit= nosaka, cik rezultātu atgriezt (no 1 līdz 1000, pēc noklusējuma 10).
@app.get("/api/leaderboard")
def get_leaderboard(limit: int = Query(10, ge=1, le=1000)):
    if not DB_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="Database not found"
        )

    conn = get_connection()

    try:
        # Kārtošana: vispirms mazāks laiks (ASC), tad vairāk monētu (DESC), tad agrāks ieraksts
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