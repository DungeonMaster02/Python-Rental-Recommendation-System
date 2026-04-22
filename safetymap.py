from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
DEFAULT_OUTPUT = PROJECT_DIR / "output" / "grid_safety_from_db.csv"


def to_float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def to_int(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def fetch_grid_safety_from_db(year: int) -> list[dict[str, Any]]:
    try:
        import connection
    except Exception as exc:
        raise RuntimeError(
            f"Cannot import DB connection module: {exc}. "
            "Install dependency with: python3 -m pip install psycopg2-binary"
        ) from exc

    conn = None
    cur = None
    try:
        conn = connection.get_connect()
        cur = conn.cursor()

        # Prefer year-specific schema if it exists in your DB.
        try:
            cur.execute(
                (
                    "SELECT grid_id, safety_score, COALESCE(convenience_score, 0), year "
                    "FROM grid "
                    "WHERE year = %s AND safety_score IS NOT NULL "
                    "ORDER BY grid_id ASC"
                ),
                [year],
            )
            yearly_rows = cur.fetchall()
            if yearly_rows:
                return [
                    {
                        "year": to_int(row[3], year),
                        "grid_id": to_int(row[0], 0),
                        "safety_score": round(to_float(row[1], 0.0), 2),
                        "convenience_score": round(to_float(row[2], 0.0), 2),
                    }
                    for row in yearly_rows
                ]
        except Exception:
            conn.rollback()

        # Fallback to default schema: one snapshot in grid table.
        cur.execute(
            (
                "SELECT grid_id, safety_score, COALESCE(convenience_score, 0) "
                "FROM grid "
                "WHERE safety_score IS NOT NULL "
                "ORDER BY grid_id ASC"
            )
        )
        rows = cur.fetchall()
        return [
            {
                "year": year,
                "grid_id": to_int(row[0], 0),
                "safety_score": round(to_float(row[1], 0.0), 2),
                "convenience_score": round(to_float(row[2], 0.0), 2),
            }
            for row in rows
        ]
    except Exception as exc:
        raise RuntimeError(f"Failed querying grid table: {exc}") from exc
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()


def write_csv(rows: list[dict[str, Any]], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["year", "grid_id", "safety_score", "convenience_score"],
        )
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read safety map data directly from DB grid table (no generated predictions)."
    )
    parser.add_argument("--year", type=int, default=2026, help="Year label for output rows when grid has no year column.")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT))
    parser.add_argument("--no-output", action="store_true", help="Only print DB summary without writing CSV.")
    args = parser.parse_args()

    rows = fetch_grid_safety_from_db(args.year)
    print(f"Fetched {len(rows)} grid rows from database table `grid`.")
    if rows:
        preview = rows[:3]
        print(f"Sample rows: {preview}")

    if not args.no_output:
        output_path = write_csv(rows, Path(args.output))
        print(f"CSV written: {output_path}")


if __name__ == "__main__":
    main()
