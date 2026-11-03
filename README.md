# Phase Shift

Retro stila platformeru spēle ar pikseļu grafiku, izvēlni, varoņu izskatiem (skiniem) un globālu rezultātu tabulu. Spēle (`pygame`) nosūta rezultātus uz nelielu API (`FastAPI`), kas tos glabā vienā SQLite datubāzē. Rezultātus var apskatīt gan pašā spēlē, gan pārlūkprogrammā.

## Satura rādītājs

- [Iespējas](#iespējas)
- [Projekta struktūra](#projekta-struktūra)
- [Uzstādīšana](#uzstādīšana)
- [Palaišana](#palaišana)
- [Vadība](#vadība)
- [API un lapas](#api-un-lapas)
- [Datubāze](#datubāze)
- [Biežāk sastopamās problēmas](#biežāk-sastopamās-problēmas)

## Iespējas

- 4 līmeņi, katram ir 90 sekunžu laika ierobežojums.
- Monētu vākšana, atsperu platformas un pagaidu platformas, ko spēlētājs var uzbūvēt pats.
- 3 varoņu izskati: Sun Runner, Violet Dash un Mint Shift.
- Segvārda ievade pirms spēles (3–16 rakstzīmes).
- Rezultātu tabula spēlē (labākie 10) un pilna tabula pārlūkprogrammā.
- Datubāzes skats pārlūkprogrammā adresē `/docs`.

## Projekta struktūra

Zemāk redzams piemērs. Mapju nosaukumi var atšķirties, svarīgi ir tas, ka `api.py`, abas HTML lapas un `leaderboard.db` atrodas vienā mapē.

```text
phase-shift/
├── api/
│   ├── api.py              # FastAPI serveris
│   ├── requirements.txt
│   ├── leaderboard.html    # rezultātu tabulas lapa  (/leaderboard)
│   ├── database.html       # datubāzes skats         (/docs)
│   └── leaderboard.db      # vienīgā datubāze
├── client/
│   └── main.py             # spēles palaišanas punkts (palaiž game/phase_shift.py)
└── game/
    ├── phase_shift.py      # spēle
    ├── requirements.txt
    ├── asset_builder.py
    ├── logic.py
    ├── assets/             # attēli (trūkstošos izveido asset_builder)
    └── settings.json       # segvārds un izvēlētais skins (izveidojas pats)
```

> **Svarīgi:** spēle pati vairs neveido un neatver nekādu datubāzi. Visi dati iet caur API, tāpēc datubāze ir tikai viena, un tā atrodas mapē `api`. Ja mapē ar spēli ir fails `leaderboard.db`, to var droši izdzēst.

## Uzstādīšana

Nepieciešams Python 3.9 vai jaunāks.

Spēlei un API ir atsevišķi atkarību faili:

```bash
pip install -r api/requirements.txt    # API: fastapi, uvicorn
pip install -r game/requirements.txt   # spēle: pygame, requests
```

Ieteicams izmantot virtuālo vidi (`python -m venv .venv`).

## Palaišana

Vispirms jāpalaiž API, pēc tam spēle.

**1. API serveris** (no mapes `api`):

```bash
cd api
uvicorn api:app --port 8000
```

Izstrādes laikā var izmantot `--reload`, lai serveris pārlādētos pēc izmaiņām kodā.

**2. Spēle** (otrā terminālī, no projekta saknes):

```bash
python client/main.py
```

Fails `client/main.py` ir tikai palaišanas punkts: tas pievieno projekta sakni pie `sys.path` un palaiž spēli no faila `game/phase_shift.py`. Spēli var palaist arī tieši: `python game/phase_shift.py`. Tam nav vajadzīgas papildu atkarības, pietiek ar `game/requirements.txt`.

Spēle sazinās ar serveri adresē `http://127.0.0.1:8000`. Ja serveris darbojas citā adresē vai portā, nomaini `SERVER_URL` spēles faila sākumā (`game/phase_shift.py`).

## Vadība

| Darbība | Taustiņi |
| --- | --- |
| Kustība | Bultiņas vai `A` / `D` |
| Lēciens | Turēt `Space` (jo ilgāk tur, jo augstāks lēciens) |
| Uzbūvēt pagaidu platformu | `E` (vienlaikus ne vairāk kā 2) |
| Izvēlne | Pele vai `↑` / `↓` + `Enter` |
| Atcelt / atpakaļ | `Esc` |

## API un lapas

Pēc servera palaišanas ir pieejams:

| Adrese | Metode | Apraksts |
| --- | --- | --- |
| `/` | GET | Pārbaude, vai API darbojas |
| `/api/scores` | POST | Saglabā jaunu rezultātu (to izmanto spēle) |
| `/api/leaderboard` | GET | Labākie rezultāti. Parametrs `?limit=` (1–1000, pēc noklusējuma 10) |
| `/api/db` | GET | Visas tabulas rindas ar visām kolonnām, jaunākās pirmās (tikai lasīšana) |
| `/leaderboard` | GET | Rezultātu tabulas lapa (angļu valodā, ar meklēšanu pēc segvārda) |
| `/docs` | GET | Datubāzes skats pārlūkprogrammā |
| `/swagger` | GET | Automātiskā FastAPI dokumentācija (Swagger UI) |

Adresēs `/leaderboard` un `/docs` dati atjaunojas paši ik pēc 15 sekundēm.

### Rezultāta formāts (`POST /api/scores`)

```json
{
  "nickname": "player1",
  "total_time": 45.5,
  "coins": 10,
  "skin": "sun",
  "played_on": "2026-11-03"
}
```

Ierobežojumi: `nickname` ir 3–16 rakstzīmes, `total_time` ir lielāks par 0, `coins` nav negatīvs.

### Kārtošana

Rezultāti tiek kārtoti pēc laika augošā secībā (mazāks laiks ir labāks). Ja laiks ir vienāds, augstāk ir tas, kam vairāk monētu, bet, ja arī tās sakrīt, tas, kurš rezultātu sasniedza agrāk.

## Datubāze

SQLite fails `leaderboard.db`, tabula `leaderboard`:

| Kolonna | Tips | Apraksts |
| --- | --- | --- |
| `id` | INTEGER, PRIMARY KEY | Automātiski palielināms numurs |
| `nickname` | TEXT | Spēlētāja segvārds |
| `total_time` | REAL | Kopējais laiks sekundēs |
| `coins` | INTEGER | Savāktās monētas |
| `skin` | TEXT | Izmantotā varoņa izskata ID (`sun`, `violet`, `mint`) |
| `played_on` | TEXT | Spēles datums (`GGGG-MM-DD`) |
| `created_at` | TEXT | Ieraksta izveides laiks (aizpildās automātiski) |

Pirms jebkādām darbībām ar datubāzi ieteicams izveidot faila `leaderboard.db` rezerves kopiju.

## Biežāk sastopamās problēmas

**Spēlē rezultātu tabula ir tukša.**
Pārbaudi, vai API darbojas, un atver `http://127.0.0.1:8000/api/leaderboard`. Jābūt redzamam JSON ar rezultātiem. Ja tas nav tā, spēle izdrukās kļūdas ziņojumu terminālī.

**Rezultāti netiek saglabāti.**
Terminālī meklē ziņojumu `Failed to save result`. Biežākie iemesli: serveris nav palaists, nepareizs `SERVER_URL` vai segvārds, kas īsāks par 3 rakstzīmēm.

**Lapa `/leaderboard` vai `/docs` rāda `Not Found`.**
Serveris darbojas ar vecu `api.py`. Aptur to (`Ctrl+C`) un palaid vēlreiz. Pārliecinies arī, ka `leaderboard.html` un `database.html` atrodas vienā mapē ar `api.py`.

**HTML lapa neielādē datus.**
Lapas nedrīkst atvērt ar dubultklikšķi (`file://...`). Tās jāatver caur serveri: `http://127.0.0.1:8000/leaderboard` un `http://127.0.0.1:8000/docs`.

**Serveris saka `Database not found`.**
Fails `leaderboard.db` nav atrodams mapē ar `api.py`. Ievieto tur savu īsto datubāzi.

## Drošība

Adrese `/docs` un `/api/db` rāda visus datubāzes ierakstus bez paroles. Kamēr API darbojas tikai uz tava datora, tā nav problēma, taču, ja serveri publicē internetā, šīs lapas jāaizsargā ar paroli vai jāizņem.
