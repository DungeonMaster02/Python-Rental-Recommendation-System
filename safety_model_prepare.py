import os
import numpy as np
import pandas as pd
import geopandas as gpd
import osmnx as ox
import time
import math
import shapely.geometry as geom
import connection

def get_grid() -> gpd.GeoDataFrame:
    """Load grid once and standardize fields."""
    grid = gpd.read_file("../data/City_Boundary/LA_400m_grid.shp").to_crs("EPSG:32611").reset_index(drop=True)

    if "grid_id" not in grid.columns:
        grid["grid_id"] = grid.index + 1

    grid["grid_id"] = grid["grid_id"].astype(int)
    grid["grid_area"] = grid.geometry.area
    return grid[["grid_id", "geometry", "grid_area"]]


def get_monthly_panel() -> pd.DataFrame:
    """Read monthly crime panel from database."""
    conn = connection.get_connect()
    try:
        panel = pd.read_sql(
            """
            SELECT grid_id, month_start, crime_count, priority_crime, violence_crime
            FROM monthly_crime
            """,
            conn,
        )
    finally:
        conn.close()

    panel["grid_id"] = panel["grid_id"].astype(int)
    panel["month_start"] = pd.to_datetime(panel["month_start"])

    for col in ["crime_count", "priority_crime", "violence_crime"]:
        panel[col] = panel[col].fillna(0).astype(int)

    return panel.sort_values(["grid_id", "month_start"]).reset_index(drop=True)


def get_building_feature() -> pd.DataFrame:
    """Compute building features by grid."""
    grid = get_grid()
    buildings = gpd.read_file("../data/Building_Footprints-shp/building.shp").to_crs(grid.crs)
    buildings = buildings[buildings.geometry.notna()].copy()

    base = grid[["grid_id", "grid_area"]].copy()

    if buildings.empty:
        return base.assign(
            building_count=0.0,
            building_area_sum=0.0,
            building_coverage_ratio=0.0,
            mean_building_area=0.0,
        )[["grid_id", "building_count", "building_area_sum", "building_coverage_ratio", "mean_building_area"]]

    centroids = buildings.copy()
    centroids["geometry"] = centroids.geometry.centroid
    count_df = (
        gpd.sjoin(
            centroids[["geometry"]],
            grid[["grid_id", "geometry"]],
            how="inner",
            predicate="within",
        )
        .groupby("grid_id")
        .size()
        .reset_index(name="building_count")
    )

    inter = gpd.overlay(
        buildings[["geometry"]],
        grid[["grid_id", "geometry"]],
        how="intersection",
    )

    if inter.empty:
        area_df = pd.DataFrame({"grid_id": [], "building_area_sum": []})
    else:
        inter["inter_area"] = inter.geometry.area
        area_df = (
            inter.groupby("grid_id")["inter_area"]
            .sum()
            .reset_index(name="building_area_sum")
        )

    feat = base.merge(count_df, on="grid_id", how="left").merge(area_df, on="grid_id", how="left")
    feat[["building_count", "building_area_sum"]] = feat[["building_count", "building_area_sum"]].fillna(0.0)

    feat["building_coverage_ratio"] = np.where(
        feat["grid_area"] > 0,
        feat["building_area_sum"] / feat["grid_area"],
        0.0,
    )
    feat["mean_building_area"] = np.where(
        feat["building_count"] > 0,
        feat["building_area_sum"] / feat["building_count"],
        0.0,
    )

    return feat[["grid_id", "building_count", "building_area_sum", "building_coverage_ratio", "mean_building_area"]]


def get_osm_raw(grid: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Load cached OSM data or fetch it in batches, then project to EPSG:32611
    and apply a 400-meter buffer to geometries.

    This function:
    1. Splits the study area into small tiles to reduce OSM query timeout risk.
    2. Caches each tile result separately so interrupted runs can resume.
    3. Keeps only the columns needed for downstream POI classification.
    4. Merges all chunk files into one GeoDataFrame.
    5. Projects to EPSG:32611 and applies a 400m buffer.
    6. Saves the final processed result to a GeoPackage cache.
    """
    import os
    import math
    import time
    import pandas as pd
    import geopandas as gpd
    from shapely.geometry import box
    import osmnx as ox

    final_cache = "../data/osm_raw_buffer400.gpkg"
    chunk_dir = "../data/osm_chunks"

    os.makedirs("../data", exist_ok=True)
    os.makedirs(chunk_dir, exist_ok=True)

    # Return final cached file if it already exists
    if os.path.exists(final_cache):
        osm = gpd.read_file(final_cache)
        if osm.crs is None:
            osm = osm.set_crs("EPSG:32611")
        return osm

    # Define OSM tags to fetch
    tags = {
        "amenity": True,
        "shop": True,
        "highway": ["bus_stop"],
        "public_transport": True,
        "railway": ["station", "halt"],
    }

    # Build study area boundary in WGS84 for OSM queries
    boundary_wgs84 = grid.to_crs("EPSG:4326").geometry.union_all()

    # Use bounding box of the study area to generate query tiles
    minx, miny, maxx, maxy = boundary_wgs84.bounds

    # Tile size in degrees; reduce this value if timeout still happens
    tile_size = 0.03

    x_steps = math.ceil((maxx - minx) / tile_size)
    y_steps = math.ceil((maxy - miny) / tile_size)

    chunk_paths = []

    # Query each tile separately
    for i in range(x_steps):
        for j in range(y_steps):
            x1 = minx + i * tile_size
            x2 = min(x1 + tile_size, maxx)
            y1 = miny + j * tile_size
            y2 = min(y1 + tile_size, maxy)

            tile = box(x1, y1, x2, y2).intersection(boundary_wgs84)

            if tile.is_empty:
                continue

            chunk_path = os.path.join(chunk_dir, f"osm_chunk_{i}_{j}.gpkg")
            chunk_paths.append(chunk_path)

            # Skip existing chunk file to support resume
            if os.path.exists(chunk_path):
                continue

            try:
                part = ox.features_from_polygon(tile, tags=tags)

                # Convert to GeoDataFrame if needed
                if not isinstance(part, gpd.GeoDataFrame):
                    part = gpd.GeoDataFrame(part, geometry="geometry", crs="EPSG:4326")
                elif part.crs is None:
                    part = part.set_crs("EPSG:4326")

                part = part.reset_index(drop=False)

                # Handle empty chunk explicitly
                if part.empty:
                    print(f"Chunk ({i}, {j}) has no matching features.")
                    empty_gdf = gpd.GeoDataFrame(columns=["geometry"], geometry="geometry", crs="EPSG:4326")
                    empty_gdf.to_file(chunk_path, driver="GPKG")
                    continue

                # Keep only fields needed later for POI classification
                keep_cols = ["geometry", "amenity", "shop", "highway", "public_transport", "railway"]
                keep_cols = [c for c in keep_cols if c in part.columns]
                part = part[keep_cols].copy()

                # Convert non-geometry columns to string to avoid GPKG field errors
                for c in part.columns:
                    if c != "geometry":
                        part[c] = part[c].astype(str)

                part.to_file(chunk_path, driver="GPKG")

                # Small pause to reduce request pressure
                time.sleep(1)

            except Exception as e:
                msg = str(e)

                # Treat "No matching features" as empty chunk, not failure
                if "No matching features" in msg:
                    print(f"Chunk ({i}, {j}) has no matching features.")
                    empty_gdf = gpd.GeoDataFrame(columns=["geometry"], geometry="geometry", crs="EPSG:4326")
                    empty_gdf.to_file(chunk_path, driver="GPKG")
                else:
                    print(f"Failed chunk ({i}, {j}) due to real error: {e}")
                continue

    # Read all cached chunk files
    gdfs = []
    for chunk_path in chunk_paths:
        if not os.path.exists(chunk_path):
            continue

        try:
            g = gpd.read_file(chunk_path)
            if g.crs is None:
                g = g.set_crs("EPSG:4326")

            if not g.empty:
                gdfs.append(g)

        except Exception as e:
            print(f"Cannot read chunk file {chunk_path}: {e}")

    # Return empty GeoDataFrame if all chunks are empty
    if not gdfs:
        return gpd.GeoDataFrame(columns=["geometry"], geometry="geometry", crs="EPSG:32611")

    # Merge all chunk results
    osm = pd.concat(gdfs, ignore_index=True)
    osm = gpd.GeoDataFrame(osm, geometry="geometry", crs="EPSG:4326")

    # Clip merged data back to the study area boundary
    boundary_gdf = gpd.GeoDataFrame(geometry=[boundary_wgs84], crs="EPSG:4326")
    osm = gpd.clip(osm, boundary_gdf)

    # Remove duplicates after tiled queries
    dedup_cols = [c for c in ["amenity", "shop", "highway", "public_transport", "railway", "geometry"] if c in osm.columns]
    if dedup_cols:
        osm = osm.drop_duplicates(subset=dedup_cols)
    else:
        osm = osm.drop_duplicates()

    # Project to metric CRS and apply 400m buffer
    osm = osm.to_crs("EPSG:32611").reset_index(drop=True)
    osm["geometry"] = osm.geometry.buffer(400)

    # Keep only required columns before writing final cache
    keep_cols = ["geometry", "amenity", "shop", "highway", "public_transport", "railway"]
    keep_cols = [c for c in keep_cols if c in osm.columns]
    osm = osm[keep_cols].copy()

    # Convert non-geometry columns to string to prevent file write issues
    for c in osm.columns:
        if c != "geometry":
            osm[c] = osm[c].astype(str)

    # Save final processed cache
    osm.to_file(final_cache, driver="GPKG")

    return osm


def poi_classification(row: pd.Series) -> str | None:
    """Classify POI into categories."""
    amenity = str(row.get("amenity", "")).lower()
    shop = str(row.get("shop", "")).lower()
    highway = str(row.get("highway", "")).lower()
    public_transport = str(row.get("public_transport", "")).lower()
    railway = str(row.get("railway", "")).lower()

    if amenity in {"bar", "pub", "nightclub"}:
        return "nightlife"

    if (shop and shop != "nan") or amenity in {
        "restaurant", "cafe", "fast_food", "marketplace", "pharmacy", "bank", "atm"
    }:
        return "commercial"

    if highway == "bus_stop" or (public_transport and public_transport != "nan") or railway in {"station", "halt"}:
        return "transit"

    if amenity in {"school", "college", "university", "kindergarten"}:
        return "school"

    return None


def entropy(values: np.ndarray) -> float:
    total = float(values.sum())
    if total <= 0:
        return 0.0
    p = values / total
    p = p[p > 0]
    return float(-(p * np.log(p)).sum())


def get_poi_feature() -> pd.DataFrame:
    """Compute buffered POI features by grid."""
    grid = get_grid()
    raw = get_osm_raw(grid)
    raw = raw[raw.geometry.notna()].copy()

    base = grid[["grid_id", "grid_area"]].copy()

    if raw.empty:
        return base.assign(
            commercial_density=0.0,
            nightlife_density=0.0,
            transit_density=0.0,
            school_density=0.0,
            poi_total_count=0.0,
            poi_diversity=0.0,
        )[["grid_id", "commercial_density", "nightlife_density", "transit_density", "school_density", "poi_total_count", "poi_diversity"]]

    poi = raw.to_crs(grid.crs).copy()
    poi["poi_category"] = poi.apply(poi_classification, axis=1)
    poi = poi[poi["poi_category"].notna()].copy().reset_index(drop=True)

    if poi.empty:
        return base.assign(
            commercial_density=0.0,
            nightlife_density=0.0,
            transit_density=0.0,
            school_density=0.0,
            poi_total_count=0.0,
            poi_diversity=0.0,
        )[["grid_id", "commercial_density", "nightlife_density", "transit_density", "school_density", "poi_total_count", "poi_diversity"]]

    joined = gpd.sjoin(
        poi[["poi_category", "geometry"]],
        grid[["grid_id", "geometry"]],
        how="inner",
        predicate="intersects",
    ).reset_index(drop=True)
    
    if joined.empty:
        return base.assign(
            commercial_density=0.0,
            nightlife_density=0.0,
            transit_density=0.0,
            school_density=0.0,
            poi_total_count=0.0,
            poi_diversity=0.0,
        )[["grid_id", "commercial_density", "nightlife_density", "transit_density", "school_density", "poi_total_count", "poi_diversity"]]


    counts = pd.crosstab(joined["grid_id"], joined["poi_category"])
    for c in ["commercial", "nightlife", "transit", "school"]:
        if c not in counts.columns:
            counts[c] = 0.0

    counts = counts[["commercial", "nightlife", "transit", "school"]].astype(float)
    counts["poi_total_count"] = counts.sum(axis=1)
    counts["poi_diversity"] = counts[["commercial", "nightlife", "transit", "school"]].apply(
        lambda r: entropy(r.to_numpy()),
        axis=1,
    )
    counts = counts.reset_index()

    feat = base.merge(counts, on="grid_id", how="left").fillna(0.0)

    for c in ["commercial", "nightlife", "transit", "school"]:
        feat[f"{c}_density"] = np.where(
            feat["grid_area"] > 0,
            feat[c] / feat["grid_area"],
            0.0,
        )

    return feat[[
        "grid_id",
        "commercial_density",
        "nightlife_density",
        "transit_density",
        "school_density",
        "poi_total_count",
        "poi_diversity",
    ]]


def add_time_feature(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["month"] = out["month_start"].dt.month
    out["year"] = out["month_start"].dt.year
    out["month_sin"] = np.sin(2 * np.pi * out["month"] / 12.0) # Create cyclical features for month to capture seasonality patterns in crime data, since month 1 and month 12 are close in time but far in numeric value, we use sine and cosine transformations to reflect this cyclic nature.
    out["month_cos"] = np.cos(2 * np.pi * out["month"] / 12.0)
    out["time_idx"] = (
        (out["year"] - out["year"].min()) * 12 + out["month"]
    )
    return out


def add_lag_features(df: pd.DataFrame, target_col: str) -> pd.DataFrame:
    out = df.sort_values(["grid_id", "month_start"]).copy() # order by grid id first, then by time to ensure correct lagging

    out[f"{target_col}_lag1"] = out.groupby("grid_id")[target_col].shift(1) # Lag of 1 month for the target column, grouped by grid_id to ensure lags are calculated within each grid's time series
    out[f"{target_col}_lag2"] = out.groupby("grid_id")[target_col].shift(2)
    out[f"{target_col}_lag3"] = out.groupby("grid_id")[target_col].shift(3)
    out[f"{target_col}_lag6"] = out.groupby("grid_id")[target_col].shift(6) # Lag of 6 months to capture half-year seasonality
    out[f"{target_col}_lag12"] = out.groupby("grid_id")[target_col].shift(12) # Lag of 12 months to capture full-year seasonality
    out[f"{target_col}_roll3"] = out.groupby("grid_id")[target_col].transform( # transform is similar to map in spark
        lambda s: s.shift(1).rolling(3, min_periods=3).mean() #rolling: selecet a at least 3 months size window to calculate, beginning from the current row to the past
    )
    out[f"{target_col}_roll6"] = out.groupby("grid_id")[target_col].transform(
        lambda s: s.shift(1).rolling(6, min_periods=6).mean()
    )
    out[f"{target_col}_roll12"] = out.groupby("grid_id")[target_col].transform(
        lambda s: s.shift(1).rolling(12, min_periods=12).mean()
    )

    out[f"{target_col}_target_next"] = out.groupby("grid_id")[target_col].shift(-1) # one step ahead target

    return out.dropna(subset=[
        f"{target_col}_lag1",
        f"{target_col}_lag2",
        f"{target_col}_lag3",
        f"{target_col}_lag6",
        f"{target_col}_lag12",
        f"{target_col}_roll3",
        f"{target_col}_roll6",
        f"{target_col}_roll12",
        f"{target_col}_target_next",
    ])


def prepare_safety_data(target_cols: list[str] | None = None) -> dict[str, pd.DataFrame]:
    """Prepare panel data for safety modeling.
    1. Loads the grid and computes static features (building and POI) by grid
    2. Loads the monthly crime panel data and merges with static features
    3. Adds time features (month, year, cyclical month) to capture seasonality
    4. For each target column, adds lag features (1,2,3,6,12 months) and rolling mean features (3,6,12 months) to capture temporal dependencies
    5. Returns a dictionary containing the final panel and separate DataFrames for each target column with lag features ready for modeling
    """
    if target_cols is None:
        target_cols = ["crime_count"]

    grid = get_grid()
    static = (
        grid[["grid_id"]]
        .merge(get_building_feature(), on="grid_id", how="left")
        .merge(get_poi_feature(), on="grid_id", how="left")
        .fillna(0.0)
    )

    panel = get_monthly_panel().merge(static, on="grid_id", how="left").fillna(0.0)
    panel = add_time_feature(panel)

    result = {"panel": panel}
    for col in target_cols:
        result[col] = add_lag_features(panel, col)

    return result


if __name__ == "__main__":
    ##Check data preparation
    # data = prepare_safety_data(["crime_count"])
    # print("safety data ready")

    # print("panel shape:", data["panel"].shape)
    # print("crime_count shape:", data["crime_count"].shape)

    # print("\ncolumns:")
    # print(data["crime_count"].columns.tolist())

    # print("\nmissing values:")
    # print(data["crime_count"].isna().sum().sort_values(ascending=False).head(20))

    # poi_cols = [
    #     "commercial_density",
    #     "nightlife_density",
    #     "transit_density",
    #     "school_density",
    #     "poi_total_count",
    #     "poi_diversity"
    # ]
    # print("\npoi summary:")
    # print(data["panel"][poi_cols].describe())

    # print("\nhead:")
    # print(data["crime_count"].head())
    pass