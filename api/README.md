# API placeholder

This folder is reserved for a future server-side leaderboard service.

The current game stores scores locally in SQLite so the game works without a backend. If you later want a shared leaderboard across multiple machines, this folder can host an API endpoint that accepts a nickname, completion time, coin count, selected skin, and date, then returns the leaderboard sorted by time and coins.
