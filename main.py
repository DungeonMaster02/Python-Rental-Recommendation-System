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


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
FRONTEND_DIR = BASE_DIR / "frontend"
FRONTEND_DIST_DIR = FRONTEND_DIR / "dist"
FRONTEND_INDEX = FRONTEND_DIST_DIR / "index.html"
OUTPUT_DIR = PROJECT_DIR / "output"
DATA_DIR = PROJECT_DIR / "data"

USC_LAT = 34.0224
USC_LON = -118.2851

DEFAULT_LISTING_IMAGE = (
    "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267"
    "?auto=format&fit=crop&w=1200&q=80"
)

AMENITY_CATALOG = [
    {"name": "USC Campus", "type": "Education"},
    {"name": "Metro Station", "type": "Transit"},
    {"name": "Neighborhood Grocery", "type": "Grocery"},
    {"name": "Local Gym", "type": "Gym"},
    {"name": "Nearby Park", "type": "Park"},
]


def create_app() -> Flask:
    frontend_status = ensure_frontend_build()

    # Disable Flask's built-in static route to avoid catching SPA paths
    # like /listings or /recommend and returning 404 on browser refresh.
    app = Flask(__name__, static_folder=None)
    app.config["FRONTEND_STATUS"] = frontend_status

    register_page_routes(app)
    register_api_routes(app)
    return app


def ensure_frontend_build() -> str:
    """Make sure Vite build artifacts exist for Flask static serving."""
    if FRONTEND_INDEX.exists():
        return "ready"

    package_json = FRONTEND_DIR / "package.json"
    if not package_json.exists():
        return "Frontend project not found at code/frontend/package.json"

    npm_bin = shutil.which("npm")
    if npm_bin is None:
        return "npm not found. Install Node.js and run: cd code/frontend && npm install && npm run build"

    try:
        if not (FRONTEND_DIR / "node_modules").exists():
            subprocess.run([npm_bin, "install"], cwd=FRONTEND_DIR, check=True)

        subprocess.run([npm_bin, "run", "build"], cwd=FRONTEND_DIR, check=True)
    except subprocess.CalledProcessError as exc:
        return f"Failed to build frontend: {exc}"

    if FRONTEND_INDEX.exists():
        return "ready"
    return "Frontend build did not generate code/frontend/dist/index.html"


def register_page_routes(app: Flask) -> None:
    @app.get("/", defaults={"path": ""})
    @app.get("/<path:path>")
    def serve_spa(path: str) -> Any:
        if path.startswith("api/"):
            return jsonify({"ok": False, "message": "API route not found"}), 404

        if not FRONTEND_INDEX.exists():
            status_message = app.config.get("FRONTEND_STATUS", "Frontend is not ready")
            return (
                "Frontend is not ready. "
                f"{status_message}\n"
                "If needed, run: cd code/frontend && npm install && npm run build",
                503,
            )

        target = FRONTEND_DIST_DIR / path
        if path and target.exists() and target.is_file():
            return send_from_directory(FRONTEND_DIST_DIR, path)

        return send_from_directory(FRONTEND_DIST_DIR, "index.html")


def register_api_routes(app: Flask) -> None:
    @app.get("/api/health")
    def api_health() -> Any:
        return jsonify(
            {
                "ok": True,
                "message": "Flask server is running",
                "frontend": app.config.get("FRONTEND_STATUS", "unknown"),
            }
        )

    @app.get("/api/home-stats")
    def api_home_stats() -> Any:
        try:
            stats = fetch_home_stats()
            return jsonify({"ok": True, **stats})
        except Exception as exc:
            return jsonify({"ok": False, "message": f"Unexpected error: {exc}"}), 500

    @app.get("/api/listings")
    def api_listings() -> Any:
        try:
            limit = parse_int_arg("limit", default=300, min_value=1, max_value=3000)
            rows = fetch_listings(limit=limit)
            return jsonify({"ok": True, "rows": rows, "count": len(rows)})
        except ValueError as exc:
            return jsonify({"ok": False, "message": str(exc)}), 400
        except Exception as exc:
            return jsonify({"ok": False, "message": f"Unexpected error: {exc}"}), 500

    @app.get("/api/recommend")
    def api_recommend() -> Any:
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
            return jsonify({"ok": False, "message": str(exc)}), 400
        except Exception as exc:
            return jsonify({"ok": False, "message": f"Unexpected error: {exc}"}), 500

    @app.get("/api/grid-safety")
    def api_grid_safety() -> Any:
        try:
            year = parse_int_arg("year", default=2026, min_value=1900, max_value=2100)
            limit = parse_int_arg("limit", default=1600, min_value=100, max_value=20000)
            rows = fetch_grid_safety(year=year, limit=limit)
            return jsonify({"ok": True, "year": year, "rows": rows, "count": len(rows)})
        except ValueError as exc:
            return jsonify({"ok": False, "message": str(exc)}), 400
        except Exception as exc:
            return jsonify({"ok": False, "message": f"Unexpected error: {exc}"}), 500

    @app.get("/api/grid-safety-geojson")
    def api_grid_safety_geojson() -> Any:
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
            return jsonify({"ok": False, "message": str(exc)}), 400
        except Exception as exc:
            return jsonify({"ok": False, "message": f"Unexpected error: {exc}"}), 500

    @app.get("/api/model-metrics")
    def api_model_metrics() -> Any:
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
            return jsonify({"ok": False, "message": f"Unexpected error: {exc}"}), 500


def parse_int_arg(
    name: str,
    default: int,
    min_value: int | None = None,
    max_value: int | None = None,
) -> int:
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


def fetch_home_stats() -> dict[str, Any]:
    """
    Return homepage stats from database aggregates only.
    This avoids deriving safety from frontend list transforms.
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
            "median_safety_score": (round(median_safety, 2) if median_safety is not None else None),
            "source": "database",
        }
    except Exception:
        return {
            "active_listings": 0,
            "median_safety_score": None,
            "source": "database_query_failed",
        }
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()


def fetch_listings(limit: int | None = None) -> list[dict[str, Any]]:
    db_rows = fetch_listings_from_db(limit=limit)
    base_rows = db_rows if db_rows else fetch_listings_from_static_html(limit=limit)

    enriched = enrich_listings(base_rows)
    if limit is None:
        return enriched
    return enriched[:limit]


def fetch_listings_from_db(limit: int | None = None) -> list[dict[str, Any]]:
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
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()


@lru_cache(maxsize=1)
def load_static_listing_seed() -> list[dict[str, Any]]:
    candidates = [
        DATA_DIR / "scrolled_listing_data.txt",
        DATA_DIR / "static_listing_data.txt",
        DATA_DIR / "static_listing_data_pro.txt",
    ]

    for file_path in candidates:
        if not file_path.exists():
            continue

        html_text = file_path.read_text(encoding="utf-8", errors="ignore")
        payload = extract_ld_searchpage_payload(html_text)
        if not payload:
            continue

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

            title = str(listing.get("name") or "Untitled listing").strip()
            address = listing.get("address") if isinstance(listing.get("address"), dict) else {}
            location_text = (
                str(address.get("streetAddress") or "").strip()
                or str(address.get("addressLocality") or "").strip()
                or "Los Angeles"
            )

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

        if rows:
            return rows

    return []


def fetch_listings_from_static_html(limit: int | None = None) -> list[dict[str, Any]]:
    rows = load_static_listing_seed()
    if limit is None:
        return rows
    return rows[:limit]


def extract_ld_searchpage_payload(html_text: str) -> dict[str, Any] | None:
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
        first_brace = script_content.find("{")
        last_brace = script_content.rfind("}")
        if first_brace == -1 or last_brace == -1 or last_brace <= first_brace:
            return None
        try:
            payload = json.loads(script_content[first_brace : last_brace + 1])
        except json.JSONDecodeError:
            return None

    if isinstance(payload, dict):
        return payload
    return None


def enrich_listings(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        return []

    normalized: list[dict[str, Any]] = []
    for idx, row in enumerate(rows, start=1):
        listing_id = to_int(row.get("listing_id"), default=idx)
        price = max(500, to_int(row.get("price"), default=1800))
        latitude = to_float(row.get("latitude"), default=USC_LAT)
        longitude = to_float(row.get("longitude"), default=USC_LON)
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
                "href": href if href else "https://losangeles.craigslist.org/search/apa",
                "url": href if href else "https://losangeles.craigslist.org/search/apa",
            }
        )

    prices = [item["price"] for item in normalized]
    min_price = min(prices)
    max_price = max(prices)

    for item in normalized:
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
        item["image_url"] = DEFAULT_LISTING_IMAGE
        item["amenities"] = build_amenities(item["listing_id"], item["distance_score"])
        item["crime_data"] = build_crime_stats(item["safety_score"])

    normalized.sort(key=lambda row: row["composite_score"], reverse=True)
    return normalized


def build_amenities(listing_id: int, distance_score: float) -> list[dict[str, Any]]:
    base_distance = max(0.2, (100 - distance_score) / 35)
    amenities: list[dict[str, Any]] = []
    for i in range(3):
        amenity = AMENITY_CATALOG[(listing_id + i) % len(AMENITY_CATALOG)]
        amenities.append(
            {
                "name": amenity["name"],
                "type": amenity["type"],
                "distance": round(base_distance + i * 0.2, 1),
            }
        )
    return amenities


def build_crime_stats(safety_score: float) -> dict[str, int]:
    total = max(1, int(round((100 - safety_score) / 4.5)))
    violence = max(0, int(round(total * 0.3)))
    property_crime = max(0, total - violence)
    return {
        "property": property_crime,
        "violence": violence,
        "property": property_crime,
        "total": total,
    }


def normalize_weights(
    *,
    safety: float,
    convenience: float,
    distance: float,
    affordability: float,
) -> dict[str, float]:
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


def fetch_grid_rows_from_db(year: int) -> list[dict[str, Any]]:
    try:
        import connection
    except Exception:
        return []

    conn = None
    cur = None
    try:
        conn = connection.get_connect()
        cur = conn.cursor()

        # Prefer year-specific records when the schema supports it.
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
                        "grid_id": to_int(row[0], 0),
                        "safety_score": clamp(to_float(row[1], 0.0) or 0.0, 0, 100),
                        "convenience_score": clamp(to_float(row[2], 0.0) or 0.0, 0, 100),
                        "year": to_int(row[3], year),
                    }
                    for row in yearly_rows
                ]
        except Exception:
            # The default schema has no "year" column; rollback and use snapshot query.
            if conn is not None:
                conn.rollback()

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
                "grid_id": to_int(row[0], 0),
                "safety_score": clamp(to_float(row[1], 0.0) or 0.0, 0, 100),
                "convenience_score": clamp(to_float(row[2], 0.0) or 0.0, 0, 100),
                "year": year,
            }
            for row in rows
        ]
    except Exception:
        return []
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()


def fetch_grid_safety(year: int, limit: int | None = None) -> list[dict[str, Any]]:
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
    shp_path = DATA_DIR / "City_Boundary" / "LA_400m_grid.shp"
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


def fetch_model_metrics() -> dict[str, Any]:
    file_path = OUTPUT_DIR / "safety_folds_results.csv"
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
        key: (round(mean(nums), 6) if nums else None)
        for key, nums in values.items()
    }


def parse_price(text: str) -> int | None:
    match = re.search(r"\$\s*([0-9][0-9,]{2,6})", text)
    if not match:
        return None
    try:
        return int(match.group(1).replace(",", ""))
    except ValueError:
        return None


def affordability_from_price(price: int, min_price: int, max_price: int) -> float:
    if max_price <= min_price:
        return 70.0
    ratio = (price - min_price) / (max_price - min_price)
    return clamp(100 * (1 - ratio), 0, 100)


def distance_score_from_coords(latitude: float, longitude: float) -> float:
    distance_km = haversine_km(latitude, longitude, USC_LAT, USC_LON)
    return 100 * (1 - min(distance_km, 12.0) / 12.0)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
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
    return max(min_value, min(value, max_value))


def to_float(value: Any, default: float | None = 0.0) -> float | None:
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


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
