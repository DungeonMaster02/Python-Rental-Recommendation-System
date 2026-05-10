from __future__ import annotations

import csv
import json
import math
import re
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path
from statistics import mean
from typing import Any

from flask import Flask, jsonify, request, send_from_directory

from path_config import FRONTEND_DIR, PROCESSED_DIR, RAW_DIR, RESULTS_DIR, ROOT_DIR


# ---------------------------------------------------------------------------
# 1. Small configuration helpers
# ---------------------------------------------------------------------------

def project_paths() -> dict[str, Path]:
    """
    Return important project folders.

    This keeps path setup inside a function, instead of placing many path
    variables at the top of the file.
    """
    base_dir = Path(__file__).resolve().parent
    project_dir = ROOT_DIR
    frontend_dir = FRONTEND_DIR
    frontend_dist_dir = frontend_dir / "dist"

    return {
        "base": base_dir,
        "project": project_dir,
        "frontend": frontend_dir,
        "frontend_dist": frontend_dist_dir,
        "frontend_index": frontend_dist_dir / "index.html",
        "output": RESULTS_DIR,
        "data": RAW_DIR,
        "data_processed": PROCESSED_DIR,
    }


def usc_coordinates() -> tuple[float, float]:
    """Return USC's latitude and longitude."""
    return 34.0224, -118.2851


def default_listing_image() -> str:
    """Return the fallback image used when a listing has no image."""
    return (
        "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267"
        "?auto=format&fit=crop&w=1200&q=80"
    )


def amenity_catalog() -> list[dict[str, str]]:
    """
    Return a small fake amenity list.

    The app uses this only to make listing cards look more complete when
    real amenity data is unavailable.
    """
    return [
        {"name": "USC Campus", "type": "Education"},
        {"name": "Metro Station", "type": "Transit"},
        {"name": "Neighborhood Grocery", "type": "Grocery"},
        {"name": "Local Gym", "type": "Gym"},
        {"name": "Nearby Park", "type": "Park"},
    ]


# ---------------------------------------------------------------------------
# 2. Flask app setup
# ---------------------------------------------------------------------------

def create_app() -> Flask:
    """
    Create and configure the Flask application.

    Flask will call the route functions registered below whenever the browser
    visits a matching URL.
    """
    frontend_status = ensure_frontend_build()

    # Disable Flask's default static route so React/Vite routes like
    # /listings and /recommend can be handled by the frontend.
    app = Flask(__name__, static_folder=None)
    app.config["FRONTEND_STATUS"] = frontend_status

    register_page_routes(app)
    register_api_routes(app)

    return app


def ensure_frontend_build() -> str:
    """
    Make sure the frontend build exists.

    The frontend source code lives in src/frontend.
    The production build should exist in src/frontend/dist.

    If dist/index.html does not exist, this function tries to run:
        npm install
        npm run build
    """
    paths = project_paths()
    frontend_dir = paths["frontend"]
    frontend_index = paths["frontend_index"]

    if frontend_index.exists():
        return "ready"

    package_json = frontend_dir / "package.json"
    if not package_json.exists():
        return "Frontend project not found at src/frontend/package.json"

    npm_bin = shutil.which("npm")
    if npm_bin is None:
        return "npm not found. Install Node.js and run: cd src/frontend && npm install && npm run build"

    try:
        if not (frontend_dir / "node_modules").exists():
            subprocess.run([npm_bin, "install"], cwd=frontend_dir, check=True)

        subprocess.run([npm_bin, "run", "build"], cwd=frontend_dir, check=True)
    except subprocess.CalledProcessError as exc:
        return f"Failed to build frontend: {exc}"

    if frontend_index.exists():
        return "ready"

    return "Frontend build did not generate src/frontend/dist/index.html"


# ---------------------------------------------------------------------------
# 3. Page routes
# ---------------------------------------------------------------------------

def register_page_routes(app: Flask) -> None:
    """
    Register routes that serve frontend pages.

    Because this project uses a single-page frontend, almost every non-API path
    should return index.html. The frontend JavaScript then decides which page to
    show.
    """

    @app.get("/", defaults={"path": ""})
    @app.get("/<path:path>")
    def serve_spa(path: str) -> Any:
        paths = project_paths()
        frontend_dist_dir = paths["frontend_dist"]
        frontend_index = paths["frontend_index"]

        # API URLs should be handled by API routes, not by the frontend.
        if path.startswith("api/"):
            return jsonify({"ok": False, "message": "API route not found"}), 404

        if not frontend_index.exists():
            status_message = app.config.get("FRONTEND_STATUS", "Frontend is not ready")
            return (
                "Frontend is not ready. "
                f"{status_message}\n"
                "If needed, run: cd src/frontend && npm install && npm run build",
                503,
            )

        # If the browser asks for a real static file, such as JS or CSS,
        # return that exact file.
        target = frontend_dist_dir / path
        if path and target.exists() and target.is_file():
            return send_from_directory(frontend_dist_dir, path)

        # Otherwise return the React/Vite entry file.
        return send_from_directory(frontend_dist_dir, "index.html")


# ---------------------------------------------------------------------------
# 4. API routes
# ---------------------------------------------------------------------------

def register_api_routes(app: Flask) -> None:
    """
    Register JSON API routes used by the frontend.

    Each route follows the same pattern:
    1. Read query parameters from the URL.
    2. Call a data/helper function.
    3. Return JSON.
    """

    @app.get("/api/health")
    def api_health() -> Any:
        """Simple route for checking whether the Flask server is running."""
        return jsonify(
            {
                "ok": True,
                "message": "Flask server is running",
                "frontend": app.config.get("FRONTEND_STATUS", "unknown"),
            }
        )

    @app.get("/api/home-stats")
    def api_home_stats() -> Any:
        """Return homepage summary numbers."""
        try:
            stats = fetch_home_stats()
            return jsonify({"ok": True, **stats})
        except Exception as exc:
            return server_error(exc)

    @app.get("/api/listings")
    def api_listings() -> Any:
        """Return housing listings."""
        try:
            limit = parse_int_arg("limit", default=300, min_value=1, max_value=3000)
            rows = fetch_listings(limit=limit)
            return jsonify({"ok": True, "rows": rows, "count": len(rows)})
        except ValueError as exc:
            return bad_request(exc)
        except Exception as exc:
            return server_error(exc)

    @app.get("/api/recommend")
    def api_recommend() -> Any:
        """
        Return recommended listings.

        The frontend can pass weights in the URL, for example:
            /api/recommend?safety=40&distance=30&convenience=20&affordability=10
        """
        try:
            safety = parse_float_arg("safety", default=30.0, min_value=0.0, max_value=100.0)
            convenience = parse_float_arg("convenience", default=25.0, min_value=0.0, max_value=100.0)
            distance = parse_float_arg("distance", default=45.0, min_value=0.0, max_value=100.0)
            affordability = parse_float_arg("affordability", default=0.0, min_value=0.0, max_value=100.0)
            limit = parse_int_arg("limit", default=10, min_value=1, max_value=3000)

            rows = fetch_listings(limit=3000)
            recommendations = rank_recommendations(
                rows,
                safety=safety,
                convenience=convenience,
                distance=distance,
                affordability=affordability,
                limit=limit,
            )

            return jsonify(
                {
                    "ok": True,
                    "rows": recommendations,
                    "count": len(recommendations),
                    "weights": normalize_weights(
                        safety=safety,
                        convenience=convenience,
                        distance=distance,
                        affordability=affordability,
                    ),
                }
            )
        except ValueError as exc:
            return bad_request(exc)
        except Exception as exc:
            return server_error(exc)

    @app.get("/api/grid-safety")
    def api_grid_safety() -> Any:
        """Return safety scores for map grid cells."""
        try:
            year = parse_int_arg("year", default=2026, min_value=1900, max_value=2100)
            limit = parse_int_arg("limit", default=1600, min_value=100, max_value=20000)
            rows = fetch_grid_safety(year=year, limit=limit)
            return jsonify({"ok": True, "year": year, "rows": rows, "count": len(rows)})
        except ValueError as exc:
            return bad_request(exc)
        except Exception as exc:
            return server_error(exc)

    @app.get("/api/grid-safety-geojson")
    def api_grid_safety_geojson() -> Any:
        """
        Return map grid safety data as GeoJSON.

        GeoJSON is a common JSON format for map shapes.
        """
        try:
            year = parse_int_arg("year", default=2026, min_value=1900, max_value=2100)
            limit = parse_int_arg("limit", default=20000, min_value=100, max_value=30000)
            geojson = fetch_grid_safety_geojson(year=year, limit=limit)

            return jsonify(
                {
                    "ok": True,
                    "year": year,
                    "geojson": geojson,
                    "count": len((geojson or {}).get("features", [])),
                }
            )
        except ValueError as exc:
            return bad_request(exc)
        except Exception as exc:
            return server_error(exc)

    @app.get("/api/model-metrics")
    def api_model_metrics() -> Any:
        """Return model evaluation metrics from results/safety_folds_results.csv."""
        try:
            metrics = fetch_model_metrics()
            return jsonify(
                {
                    "ok": True,
                    "combined_rmse": metrics.get("combined_rmse"),
                    "property_rmse": metrics.get("property_rmse"),
                    "violence_rmse": metrics.get("violence_rmse"),
                    "hit_rate": metrics.get("hit_rate"),
                    "jaccard": metrics.get("jaccard"),
                }
            )
        except Exception as exc:
            return server_error(exc)


def bad_request(exc: Exception) -> tuple[Any, int]:
    """Return a 400 response when the user passes an invalid query parameter."""
    return jsonify({"ok": False, "message": str(exc)}), 400


def server_error(exc: Exception) -> tuple[Any, int]:
    """Return a 500 response when something unexpected fails."""
    return jsonify({"ok": False, "message": f"Unexpected error: {exc}"}), 500


# ---------------------------------------------------------------------------
# 5. Query parameter helpers
# ---------------------------------------------------------------------------

def parse_int_arg(
    name: str,
    default: int,
    min_value: int | None = None,
    max_value: int | None = None,
) -> int:
    """
    Read an integer query parameter from the URL.

    Example:
        /api/listings?limit=50

    If the parameter is missing, return the default value.
    """
    raw = request.args.get(name)
    if raw is None or raw == "":
        return default

    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"Query param '{name}' must be integer") from exc

    if min_value is not None and value < min_value:
        raise ValueError(f"Query param '{name}' must be >= {min_value}")
    if max_value is not None and value > max_value:
        raise ValueError(f"Query param '{name}' must be <= {max_value}")

    return value


def parse_float_arg(
    name: str,
    default: float,
    min_value: float | None = None,
    max_value: float | None = None,
) -> float:
    """Read a decimal-number query parameter from the URL."""
    raw = request.args.get(name)
    if raw is None or raw == "":
        return default

    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f"Query param '{name}' must be float") from exc

    if min_value is not None and value < min_value:
        raise ValueError(f"Query param '{name}' must be >= {min_value}")
    if max_value is not None and value > max_value:
        raise ValueError(f"Query param '{name}' must be <= {max_value}")

    return value


# ---------------------------------------------------------------------------
# 6. Data loading
# ---------------------------------------------------------------------------

def fetch_home_stats() -> dict[str, Any]:
    """
    Return homepage summary statistics from the database.

    If the database is unavailable, return safe fallback values so the frontend
    does not crash.
    """
    try:
        import connection
    except Exception:
        return {
            "active_listings": 0,
            "median_safety_score": None,
            "source": "database_unavailable",
        }

    conn = None
    cur = None

    try:
        conn = connection.get_connect()
        cur = conn.cursor()
        cur.execute(
            (
                "SELECT "
                "(SELECT COUNT(*)::int FROM listing) AS active_listings, "
                "("
                "  SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY safety_score)::float "
                "  FROM listing "
                "  WHERE safety_score IS NOT NULL"
                ") AS median_safety_score"
            )
        )

        row = cur.fetchone()
        active_listings = to_int(row[0], default=0) if row else 0
        median_safety = to_float(row[1], default=None) if row else None

        return {
            "active_listings": active_listings,
            "median_safety_score": round(median_safety, 2) if median_safety is not None else None,
            "source": "database",
        }

    except Exception:
        return {
            "active_listings": 0,
            "median_safety_score": None,
            "source": "database_query_failed",
        }

    finally:
        close_db(conn, cur)


def fetch_listings(limit: int | None = None) -> list[dict[str, Any]]:
    """
    Return listing rows.

    The app tries the database first. If that fails or returns no rows, it uses
    static HTML seed data from the data folder.
    """
    db_rows = fetch_listings_from_db(limit=limit)
    base_rows = db_rows if db_rows else fetch_listings_from_static_html(limit=limit)

    enriched = enrich_listings(base_rows)

    if limit is None:
        return enriched

    return enriched[:limit]


def fetch_listings_from_db(limit: int | None = None) -> list[dict[str, Any]]:
    """Read listing rows from the database."""
    try:
        import connection
    except Exception:
        return []

    query = (
        "SELECT listing_id, href, title, price, location_text, latitude, longitude, "
        "bedroom_number, distance_score, convenience_score, safety_score "
        "FROM listing ORDER BY listing_id DESC"
    )

    params: list[Any] = []
    if limit is not None:
        query += " LIMIT %s"
        params.append(limit)

    conn = None
    cur = None

    try:
        conn = connection.get_connect()
        cur = conn.cursor()
        cur.execute(query, params)

        columns = [desc[0] for desc in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]

    except Exception:
        return []

    finally:
        close_db(conn, cur)


@lru_cache(maxsize=1)
def load_static_listing_seed() -> list[dict[str, Any]]:
    """
    Load fallback listing data from static HTML files.

    The @lru_cache means this function runs only once per server process.
    After the first call, Python reuses the previous result.
    """
    data_dir = project_paths()["data"]
    candidates = [
        data_dir / "scrolled_listing_data.txt",
        data_dir / "static_listing_data.txt",
        data_dir / "static_listing_data_pro.txt",
    ]

    for file_path in candidates:
        if not file_path.exists():
            continue

        html_text = file_path.read_text(encoding="utf-8", errors="ignore")
        payload = extract_ld_searchpage_payload(html_text)
        if not payload:
            continue

        rows = listing_rows_from_payload(payload)
        if rows:
            return rows

    return []


def listing_rows_from_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert Craigslist-style JSON-LD data into a simple list of listings."""
    items = payload.get("itemListElement", [])
    rows: list[dict[str, Any]] = []

    for idx, item in enumerate(items, start=1):
        listing = item.get("item") if isinstance(item, dict) else None
        if not isinstance(listing, dict):
            continue

        latitude = to_float(listing.get("latitude"), default=None)
        longitude = to_float(listing.get("longitude"), default=None)
        if latitude is None or longitude is None:
            continue

        address = listing.get("address") if isinstance(listing.get("address"), dict) else {}
        location_text = (
            str(address.get("streetAddress") or "").strip()
            or str(address.get("addressLocality") or "").strip()
            or "Los Angeles"
        )

        title = str(listing.get("name") or "Untitled listing").strip()
        bedroom = to_int(listing.get("numberOfBedrooms"), default=1)
        bathroom = to_int(listing.get("numberOfBathroomsTotal"), default=max(1, bedroom))
        parsed_price = parse_price(title)
        fallback_price = 1200 + bedroom * 650 + (idx % 10) * 80

        rows.append(
            {
                "listing_id": idx,
                "href": str(listing.get("url") or "").strip(),
                "title": title,
                "price": parsed_price if parsed_price is not None else fallback_price,
                "location_text": location_text,
                "latitude": latitude,
                "longitude": longitude,
                "bedroom_number": bedroom,
                "bathroom_number": bathroom,
            }
        )

    return rows


def fetch_listings_from_static_html(limit: int | None = None) -> list[dict[str, Any]]:
    """Return listings from static fallback files."""
    rows = load_static_listing_seed()

    if limit is None:
        return rows

    return rows[:limit]


def extract_ld_searchpage_payload(html_text: str) -> dict[str, Any] | None:
    """
    Extract JSON-LD listing data from an HTML string.

    The static files contain a script tag with id="ld_searchpage_results".
    This function finds that script tag and parses its JSON content.
    """
    marker = 'id="ld_searchpage_results"'
    marker_pos = html_text.find(marker)
    if marker_pos == -1:
        return None

    script_start = html_text.find(">", marker_pos)
    script_end = html_text.find("</script>", script_start)
    if script_start == -1 or script_end == -1:
        return None

    script_content = html_text[script_start + 1 : script_end].strip()
    if not script_content:
        return None

    try:
        payload = json.loads(script_content)
    except json.JSONDecodeError:
        payload = parse_json_object_from_text(script_content)

    if isinstance(payload, dict):
        return payload

    return None


def parse_json_object_from_text(text: str) -> dict[str, Any] | None:
    """
    Try to parse the first JSON object inside a larger text string.

    This is a fallback for messy HTML/script content.
    """
    first_brace = text.find("{")
    last_brace = text.rfind("}")

    if first_brace == -1 or last_brace == -1 or last_brace <= first_brace:
        return None

    try:
        payload = json.loads(text[first_brace : last_brace + 1])
    except json.JSONDecodeError:
        return None

    if isinstance(payload, dict):
        return payload

    return None


# ---------------------------------------------------------------------------
# 7. Listing cleanup and scoring
# ---------------------------------------------------------------------------

def enrich_listings(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Convert raw listing rows into the JSON shape expected by the frontend.

    This function fills missing values, calculates derived scores, and sorts
    listings by their overall score.
    """
    if not rows:
        return []

    normalized = normalize_listing_rows(rows)
    add_listing_scores_and_details(normalized)

    normalized.sort(key=lambda row: row["composite_score"], reverse=True)
    return normalized


def normalize_listing_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Clean raw listing rows and standardize field names."""
    usc_lat, usc_lon = usc_coordinates()
    normalized: list[dict[str, Any]] = []

    for idx, row in enumerate(rows, start=1):
        listing_id = to_int(row.get("listing_id"), default=idx)
        price = max(500, to_int(row.get("price"), default=1800))

        latitude = to_float(row.get("latitude"), default=usc_lat)
        longitude = to_float(row.get("longitude"), default=usc_lon)

        distance_score = to_float(
            row.get("distance_score"),
            default=distance_score_from_coords(latitude, longitude),
        )
        distance_score = clamp(distance_score, 0, 100)

        convenience_score = to_float(
            row.get("convenience_score"),
            default=clamp(0.65 * distance_score + 20 + (listing_id % 15), 0, 100),
        )
        convenience_score = clamp(convenience_score, 0, 100)

        safety_guess = clamp(
            35 + 0.45 * distance_score + 0.25 * convenience_score - (listing_id % 9),
            0,
            100,
        )
        safety_score = clamp(to_float(row.get("safety_score"), default=safety_guess), 0, 100)

        bedrooms = max(0, to_int(row.get("bedroom_number"), default=1))
        bathrooms = max(1, to_int(row.get("bathroom_number"), default=max(1, bedrooms)))

        title = str(row.get("title") or "Listing near USC").strip()
        address = str(row.get("location_text") or "Los Angeles, CA").strip()
        href = str(row.get("href") or "").strip()
        fallback_url = "https://losangeles.craigslist.org/search/apa"

        normalized.append(
            {
                "listing_id": listing_id,
                "title": title,
                "price": price,
                "latitude": latitude,
                "longitude": longitude,
                "distance_score": round(distance_score, 2),
                "convenience_score": round(convenience_score, 2),
                "safety_score": round(safety_score, 2),
                "bedroom_number": bedrooms,
                "bedrooms": bedrooms,
                "bathrooms": bathrooms,
                "location_text": address,
                "address": address,
                "href": href if href else fallback_url,
                "url": href if href else fallback_url,
            }
        )

    return normalized


def add_listing_scores_and_details(listings: list[dict[str, Any]]) -> None:
    """Add affordability, composite score, image, amenities, and crime summary."""
    prices = [item["price"] for item in listings]
    min_price = min(prices)
    max_price = max(prices)

    for item in listings:
        affordability_score = affordability_from_price(item["price"], min_price, max_price)
        composite_score = (
            item["safety_score"]
            + item["convenience_score"]
            + item["distance_score"]
            + affordability_score
        ) / 4.0

        item["affordability_score"] = round(affordability_score, 2)
        item["composite_score"] = round(composite_score, 2)
        item["description"] = (
            f"{item['title']} in {item['address']}. "
            "Scores are computed from the project safety, convenience, and distance pipeline."
        )
        item["image_url"] = default_listing_image()
        item["amenities"] = build_amenities(item["listing_id"], item["distance_score"])
        item["crime_data"] = build_crime_stats(item["safety_score"])


def build_amenities(listing_id: int, distance_score: float) -> list[dict[str, Any]]:
    """
    Build three nearby amenities for a listing.

    This is generated data. The distance is estimated from the distance score.
    """
    base_distance = max(0.2, (100 - distance_score) / 35)
    catalog = amenity_catalog()

    amenities: list[dict[str, Any]] = []
    for i in range(3):
        amenity = catalog[(listing_id + i) % len(catalog)]
        amenities.append(
            {
                "name": amenity["name"],
                "type": amenity["type"],
                "distance": round(base_distance + i * 0.2, 1),
            }
        )

    return amenities


def build_crime_stats(safety_score: float) -> dict[str, int]:
    """
    Convert a safety score into a simple crime summary.

    Higher safety means fewer estimated incidents.
    """
    total = max(1, int(round((100 - safety_score) / 4.5)))
    violence = max(0, int(round(total * 0.3)))
    property_crime = max(0, total - violence)

    return {
        "property": property_crime,
        "violence": violence,
        "total": total,
    }


# ---------------------------------------------------------------------------
# 8. Recommendation scoring
# ---------------------------------------------------------------------------

def normalize_weights(
    *,
    safety: float,
    convenience: float,
    distance: float,
    affordability: float,
) -> dict[str, float]:
    """
    Convert user-selected weights into percentages that sum to 1.

    Example:
        safety=30, convenience=25, distance=45, affordability=0

    becomes approximately:
        safety=0.30, convenience=0.25, distance=0.45, affordability=0.00
    """
    raw = {
        "safety": max(0.0, safety),
        "convenience": max(0.0, convenience),
        "distance": max(0.0, distance),
        "affordability": max(0.0, affordability),
    }

    total = sum(raw.values())

    if total <= 0:
        return {
            "safety": 0.3,
            "convenience": 0.25,
            "distance": 0.25,
            "affordability": 0.2,
        }

    return {key: value / total for key, value in raw.items()}


def rank_recommendations(
    rows: list[dict[str, Any]],
    *,
    safety: float,
    convenience: float,
    distance: float,
    affordability: float,
    limit: int,
) -> list[dict[str, Any]]:
    """Rank listings using weighted scores and return the top results."""
    weights = normalize_weights(
        safety=safety,
        convenience=convenience,
        distance=distance,
        affordability=affordability,
    )

    ranked: list[dict[str, Any]] = []

    for row in rows:
        weighted_score = (
            to_float(row.get("safety_score"), 0.0) * weights["safety"]
            + to_float(row.get("convenience_score"), 0.0) * weights["convenience"]
            + to_float(row.get("distance_score"), 0.0) * weights["distance"]
            + to_float(row.get("affordability_score"), 0.0) * weights["affordability"]
        )

        enriched = dict(row)
        enriched["weighted_score"] = round(weighted_score, 2)
        ranked.append(enriched)

    ranked.sort(key=lambda item: to_float(item.get("weighted_score"), 0.0), reverse=True)

    return ranked[:limit]


# ---------------------------------------------------------------------------
# 9. Grid and map data
# ---------------------------------------------------------------------------

def fetch_grid_rows_from_db(year: int) -> list[dict[str, Any]]:
    """
    Read map grid scores from the database.

    Some database schemas have a year column. Some do not.
    The function first tries the year-specific query, then falls back to the
    simpler query.
    """
    try:
        import connection
    except Exception:
        return []

    conn = None
    cur = None

    try:
        conn = connection.get_connect()
        cur = conn.cursor()

        yearly_rows = fetch_yearly_grid_rows(cur, conn, year)
        if yearly_rows:
            return yearly_rows

        cur.execute(
            (
                "SELECT grid_id, safety_score, COALESCE(convenience_score, 0) "
                "FROM grid "
                "WHERE safety_score IS NOT NULL "
                "ORDER BY grid_id ASC"
            )
        )

        return [
            {
                "grid_id": to_int(row[0], 0),
                "safety_score": clamp(to_float(row[1], 0.0) or 0.0, 0, 100),
                "convenience_score": clamp(to_float(row[2], 0.0) or 0.0, 0, 100),
                "year": year,
            }
            for row in cur.fetchall()
        ]

    except Exception:
        return []

    finally:
        close_db(conn, cur)


def fetch_yearly_grid_rows(cur: Any, conn: Any, year: int) -> list[dict[str, Any]]:
    """Try to read grid rows from a schema that includes a year column."""
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
    except Exception:
        if conn is not None:
            conn.rollback()
        return []

    rows = cur.fetchall()

    return [
        {
            "grid_id": to_int(row[0], 0),
            "safety_score": clamp(to_float(row[1], 0.0) or 0.0, 0, 100),
            "convenience_score": clamp(to_float(row[2], 0.0) or 0.0, 0, 100),
            "year": to_int(row[3], year),
        }
        for row in rows
    ]


def fetch_grid_safety(year: int, limit: int | None = None) -> list[dict[str, Any]]:
    """Return cleaned grid safety rows for the frontend."""
    db_rows = fetch_grid_rows_from_db(year)
    if not db_rows:
        return []

    rows: list[dict[str, Any]] = []

    for row in db_rows:
        safety_score = clamp(to_float(row.get("safety_score"), 0.0) or 0.0, 0, 100)
        safety_bucket = min(10, max(1, int(math.ceil(safety_score / 10.0))))

        rows.append(
            {
                "grid_id": str(row.get("grid_id", "")),
                "convenience_score": round(to_float(row.get("convenience_score"), 0.0) or 0.0, 2),
                "safety_score": round(safety_score, 2),
                "safety_bucket": safety_bucket,
                "year": to_int(row.get("year"), year),
            }
        )

    if limit is not None:
        rows = rows[:limit]

    return rows


@lru_cache(maxsize=1)
def load_grid_geometry_by_id() -> dict[int, dict[str, Any]]:
    """
    Load map grid shapes from the shapefile.

    The result is cached because reading shapefiles can be slow.
    """
    shp_path = project_paths()["data_processed"] / "LA_400m_grid" / "LA_400m_grid.shp"
    if not shp_path.exists():
        return {}

    try:
        import geopandas as gpd
    except Exception:
        return {}

    try:
        gdf = gpd.read_file(shp_path)

        if "grid_id" not in gdf.columns:
            gdf["grid_id"] = gdf.index + 1

        gdf["grid_id"] = gdf["grid_id"].astype(int)
        gdf = gdf[["grid_id", "geometry"]].to_crs("EPSG:4326")

        feature_collection = json.loads(gdf.to_json())

        geometry_map: dict[int, dict[str, Any]] = {}
        for feature in feature_collection.get("features", []):
            props = feature.get("properties") or {}
            geometry = feature.get("geometry")
            grid_id = to_int(props.get("grid_id"), default=0)

            if grid_id > 0 and isinstance(geometry, dict):
                geometry_map[grid_id] = geometry

        return geometry_map

    except Exception:
        return {}


def fetch_grid_safety_geojson(year: int, limit: int | None = None) -> dict[str, Any]:
    """Combine grid scores with grid shapes and return GeoJSON."""
    rows = fetch_grid_safety(year=year, limit=limit)
    if not rows:
        return {"type": "FeatureCollection", "features": []}

    geometry_map = load_grid_geometry_by_id()
    if not geometry_map:
        return {"type": "FeatureCollection", "features": []}

    features: list[dict[str, Any]] = []

    for row in rows:
        grid_id = to_int(row.get("grid_id"), default=0)
        geometry = geometry_map.get(grid_id)

        if geometry is None:
            continue

        features.append(
            {
                "type": "Feature",
                "geometry": geometry,
                "properties": {
                    "grid_id": str(grid_id),
                    "safety_score": round(to_float(row.get("safety_score"), 0.0) or 0.0, 2),
                    "safety_bucket": to_int(row.get("safety_bucket"), 1),
                    "convenience_score": round(to_float(row.get("convenience_score"), 0.0) or 0.0, 2),
                    "year": to_int(row.get("year"), year),
                },
            }
        )

    return {"type": "FeatureCollection", "features": features}


# ---------------------------------------------------------------------------
# 10. Model metrics
# ---------------------------------------------------------------------------

def fetch_model_metrics() -> dict[str, Any]:
    """Read model metrics from results/safety_folds_results.csv."""
    file_path = project_paths()["output"] / "safety_folds_results.csv"

    if not file_path.exists():
        return {}

    metric_keys = [
        "combined_rmse",
        "property_rmse",
        "violence_rmse",
        "hit_rate",
        "jaccard",
    ]

    values: dict[str, list[float]] = {key: [] for key in metric_keys}

    with file_path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            for key in metric_keys:
                value = to_float(row.get(key), default=None)
                if value is not None:
                    values[key].append(value)

    return {
        key: round(nums_mean, 6) if nums else None
        for key, nums in values.items()
        for nums_mean in [mean(nums) if nums else 0]
    }


# ---------------------------------------------------------------------------
# 11. Small utility functions
# ---------------------------------------------------------------------------

def parse_price(text: str) -> int | None:
    """Extract the first price from text such as '$2,100 apartment near USC'."""
    match = re.search(r"\$\s*([0-9][0-9,]{2,6})", text)
    if not match:
        return None

    try:
        return int(match.group(1).replace(",", ""))
    except ValueError:
        return None


def affordability_from_price(price: int, min_price: int, max_price: int) -> float:
    """Convert a rent price into a 0-100 affordability score."""
    if max_price <= min_price:
        return 70.0

    ratio = (price - min_price) / (max_price - min_price)
    return clamp(100 * (1 - ratio), 0, 100)


def distance_score_from_coords(latitude: float, longitude: float) -> float:
    """
    Convert distance from USC into a 0-100 score.

    100 means very close. 0 means 12 km or farther away.
    """
    usc_lat, usc_lon = usc_coordinates()
    distance_km = haversine_km(latitude, longitude, usc_lat, usc_lon)

    return 100 * (1 - min(distance_km, 12.0) / 12.0)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two latitude/longitude points in kilometers.

    This uses the Haversine formula, which is commonly used for map distances.
    """
    radius = 6371.0

    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))

    return radius * c


def clamp(value: float, min_value: float, max_value: float) -> float:
    """Keep a number inside a minimum and maximum range."""
    return max(min_value, min(value, max_value))


def to_float(value: Any, default: float | None = 0.0) -> float | None:
    """Safely convert a value to float."""
    if value is None or value == "":
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def to_int(value: Any, default: int = 0) -> int:
    """Safely convert a value to int."""
    if value is None or value == "":
        return default

    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def close_db(conn: Any, cur: Any) -> None:
    """Close database cursor and connection if they exist."""
    if cur is not None:
        cur.close()

    if conn is not None:
        conn.close()


# ---------------------------------------------------------------------------
# 12. Run the app
# ---------------------------------------------------------------------------

app = create_app()


if __name__ == "__main__":
    # debug=True is useful during development because Flask reloads after edits
    # and shows detailed error pages.
    app.run(host="127.0.0.1", port=5000, debug=True)
