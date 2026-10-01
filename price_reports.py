"""Persistent, unverified community price reports for the local demo API."""

import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

DATABASE_PATH = Path(os.environ.get("GAS_API_DB_PATH", "price_reports.sqlite3"))


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("""CREATE TABLE IF NOT EXISTS price_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        station_id TEXT NOT NULL,
        fuel_type TEXT NOT NULL,
        price REAL NOT NULL,
        reported_at TEXT NOT NULL
    )""")
    connection.execute("""CREATE INDEX IF NOT EXISTS price_reports_history
        ON price_reports (station_id, fuel_type, reported_at)""")
    return connection


def add_report(station_id: str, fuel_type: str, price: float) -> dict:
    reported_at = datetime.now(timezone.utc).isoformat()
    with connect() as connection:
        cursor = connection.execute(
            "INSERT INTO price_reports (station_id, fuel_type, price, reported_at) VALUES (?, ?, ?, ?)",
            (station_id, fuel_type, price, reported_at),
        )
        return {"id": cursor.lastrowid, "station_id": station_id, "fuel_type": fuel_type,
                "price": price, "reported_at": reported_at, "source": "community"}


def latest_reports() -> dict[tuple[str, str], dict]:
    with connect() as connection:
        rows = connection.execute("""SELECT station_id, fuel_type, price, reported_at FROM price_reports
            WHERE id IN (SELECT MAX(id) FROM price_reports GROUP BY station_id, fuel_type)""").fetchall()
    return {(row["station_id"], row["fuel_type"]): dict(row) for row in rows}


def price_history(station_id: str, fuel_type: str, days: int | None) -> list[dict]:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat() if days else None
    with connect() as connection:
        if cutoff:
            rows = connection.execute("""SELECT id, station_id, fuel_type, price, reported_at
                FROM price_reports WHERE station_id = ? AND fuel_type = ? AND reported_at >= ?
                ORDER BY reported_at ASC, id ASC""", (station_id, fuel_type, cutoff)).fetchall()
        else:
            rows = connection.execute("""SELECT id, station_id, fuel_type, price, reported_at
                FROM price_reports WHERE station_id = ? AND fuel_type = ?
                ORDER BY reported_at ASC, id ASC""", (station_id, fuel_type)).fetchall()
    return [{**dict(row), "source": "community"} for row in rows]
