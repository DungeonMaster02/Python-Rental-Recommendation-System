# USC Housing Recommendation and Safety Analysis

This project is a data-driven housing recommendation system for USC students.
It combines Craigslist rental listings, Los Angeles crime records, city
geospatial data, OpenStreetMap points of interest, a PostgreSQL data backend,
an XGBoost safety forecasting model, and a React + TypeScript web interface.

The application helps users compare rental options by:

- Safety around the listing location.
- Convenience based on nearby amenities, transit, and local services.
- Distance to the USC University Park Campus.
- Monthly rent and affordability.

The final web app provides ranked housing recommendations, listing browsing,
favorite saving, and a 2026 Los Angeles grid-level safety heat map.

## Project Status

The repository currently contains:

- Backend Python scripts for scraping, cleaning, database loading, geospatial
  processing, model training, and serving the Flask API.
- A React + TypeScript frontend built with Vite, React Router, Leaflet,
  Recharts, Radix UI components, Tailwind, and lucide-react icons.
- Raw and processed data folders under the project-level `data/` directory.
- Model and prediction outputs under the project-level `results/` directory.

Unless a command explicitly says otherwise, run backend commands from the
project root.

## Quick Start

1. Create a Python environment and install backend dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r src/backend/requirements.txt
```

2. Create a PostgreSQL database and configure `.env`.

The code resolves `.env` from the first existing path among:

- `.env`
- `src/.env`
- `src/backend/.env`

Example:

```text
host=localhost
dbname=housing_db
user=postgres
password=your_password
port=5432
Rent_URL=https://losangeles.craigslist.org/search/apa
```

3. Install and build the frontend:

```bash
cd src/frontend
npm install
npm run build
cd ../..
```

4. Run the data pipeline:

```bash
python3 src/backend/data_pipeline.py
```

5. Start the Flask server:

```bash
python3 src/backend/main.py
```

Open the app at:

```text
http://127.0.0.1:5000
```

## Repository Structure

```text
.
|-- data/
|   |-- raw/
|   |   |-- Crime_Data_from_2010_to_2019_*.csv
|   |   |-- Crime_Data_from_2020_to_2024_*.csv
|   |   |-- City_Boundary/
|   |   |-- Building_Footprints-shp/
|   |   |-- osm_chunks/
|   |   |-- osm_raw_buffer400.gpkg
|   |   `-- static_listing_data.txt
|   `-- processed/
|       |-- Crime_Data_from_2010_to_2024.csv
|       |-- LA_400m_grid/
|       `-- usc_campus/
|-- documents/
|   `-- project notes, proposal, report, diagrams, and references
|-- results/
|   |-- final_grid_safety_2026.csv
|   |-- future_monthly_predictions_2025_2026.csv
|   `-- safety_folds_results.csv
`-- src/
    |-- backend/
    |   |-- main.py
    |   |-- data_pipeline.py
    |   |-- data_processing.py
    |   |-- crime_data_processing.py
    |   |-- map_division.py
    |   |-- safety_model_prepare.py
    |   |-- safety_main.py
    |   |-- safety_modeling.py
    |   |-- selenium_scraper.py
    |   |-- scraper.py
    |   |-- path_config.py
    |   `-- requirements.txt
    |-- frontend/
    |   |-- package.json
    |   |-- vite.config.ts
    |   `-- src/
    `-- utils/
        |-- connection.py
        `-- db_execution.py
```

      ## Assignment Mapping

      The course rubric expects a set of scripts named `get_data.py`, `clean_data.py`,
      `integrate_data.py`, and `analyze_visualize.py`. This project uses the
      following equivalents under `src/backend/`:

      | Required Script | Project Equivalent | Purpose |
      | --- | --- | --- |
      | `get_data.py` | `scraper.py`, `selenium_scraper.py` | Collect Craigslist listing data |
      | `clean_data.py` | `crime_data_processing.py`, `data_processing.py` | Clean crime + listing data |
      | `integrate_data.py` | `data_pipeline.py` | Orchestrate data loads + database integration |
      | `analyze_visualize.py` | `safety_main.py`, `safety_modeling.py` | Modeling + analysis outputs |

      If a TA is following the standard script names, point them to the equivalents
      above. The main pipeline entry point is still `src/backend/data_pipeline.py`.

## Data Sources

| Dataset | Source | Used For |
| --- | --- | --- |
| Crime Data 2010-2019 | LA Open Data: `Crime Data from 2010 to 2019` | Historical crime incidents |
| Crime Data 2020-2024 | LA Open Data: `Crime Data from 2020 to 2024` | Recent crime incidents |
| LA City Boundary | LA GeoHub city boundary shapefile | Clipping the study area and building grid cells |
| Building Footprints | LA GeoHub building footprint shapefile | Static built-environment features |
| OpenStreetMap POIs | OpenStreetMap through `osmnx` | Amenity, transit, commercial, school, and nightlife features |
| Rental Listings | Craigslist Los Angeles apartment search | Housing recommendation candidates |
| USC Campus Boundary | Local shapefile under `data/processed/usc_campus/` | Distance-to-campus scoring |

Required input files are expected under the project-level `data/` directory.

## Backend Components

### `path_config.py`

Defines shared paths for the project. Important resolved directories include:

- `ROOT_DIR`: project root.
- `DATA_DIR`: `data/`.
- `RAW_DIR`: `data/raw/`.
- `PROCESSED_DIR`: `data/processed/`.
- `RESULTS_DIR`: `results/`.
- `FRONTEND_DIR`: `src/frontend/`.
- `USC_CAMPUS_DIR`: first existing USC campus shapefile directory among
  `data/usc_campus/`, `data/processed/usc_campus/`, and
  `data/raw/usc_campus/`.

### `data_pipeline.py`

Orchestrates the main backend workflow:

1. Checks required input files.
2. Checks and recreates PostgreSQL tables if the schema does not match.
3. Builds the 400m LA grid if missing.
4. Merges raw crime CSV files if the processed crime file is missing.
5. Refreshes `crime`, `grid`, and `monthly_crime` database tables.
6. Builds monthly grid-level crime panels.
7. Runs the safety model if prediction outputs are missing.
8. Optionally runs the Selenium scraper and updates listing data.

The pipeline uses the following database tables:

| Table | Purpose |
| --- | --- |
| `listing` | Rental listings and recommendation scores |
| `crime` | Cleaned crime records |
| `grid` | Grid IDs, safety scores, and convenience scores |
| `monthly_crime` | Complete grid-month crime panel |

### `main.py`

Creates the Flask application and serves both the API and the built frontend.
If `src/frontend/dist/index.html` is missing, it attempts to run `npm install`
and `npm run build` automatically.

API endpoints:

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/health` | GET | Server health check |
| `/api/home-stats` | GET | Homepage listing and safety summary |
| `/api/listings` | GET | Rental listing rows |
| `/api/recommend` | GET | Weighted recommendation results |
| `/api/grid-safety` | GET | Grid safety rows from PostgreSQL |
| `/api/grid-safety-geojson` | GET | GeoJSON grid polygons with safety scores |
| `/api/model-metrics` | GET | Average validation metrics from `results/safety_folds_results.csv` |

Example:

```bash
curl "http://127.0.0.1:5000/api/recommend?safety=30&convenience=25&distance=45&affordability=0&limit=10"
```

## Frontend Components

The frontend lives in `src/frontend/` and is a Vite React application.

Main routes:

| Route | Page | Purpose |
| --- | --- | --- |
| `/` | `HomePage` | Project overview and live summary stats |
| `/listings` | `ListingsPage` | Browse and filter housing listings |
| `/recommend` | `RecommendPage` | Adjust weights and view top recommendations |
| `/safety-map` | `SafetyMapPage` | Leaflet heat map for 2026 grid safety |
| `/favorites` | `FavoritesPage` | Locally saved favorite listings |
| `/about` | `AboutPage` | Project details |

Frontend scripts:

```bash
cd src/frontend
npm run dev       # Vite dev server
npm run build     # production build
npm run typecheck # TypeScript check
```

The Vite dev server proxies `/api` requests to `http://127.0.0.1:5000`.
For deployments where the API is hosted elsewhere, set `VITE_API_BASE_URL`.

## Data Processing Workflow

### Crime Data

`crime_data_processing.py` merges LA crime files from 2010-2019 and 2020-2024
into:

```text
data/processed/Crime_Data_from_2010_to_2024.csv
```

The cleaning process:

- Strips inconsistent source column names.
- Drops duplicate incidents by `DR_NO`.
- Keeps incident ID, coordinates, date, and crime description fields.
- Classifies crime descriptions into `Violence` and `Property` groups.
- Spatially joins incidents to 400m LA grid cells.
- Creates a complete `grid_id x month_start` monthly panel.

### Geospatial Grid

`map_division.py` reads the LA city boundary shapefile and creates 400m x 400m
grid cells. It uses `EPSG:32611` so distances and areas are measured in meters,
then writes the grid shapefile to:

```text
data/processed/LA_400m_grid/
```

### Static Grid Features

`safety_model_prepare.py` builds static grid features used by the safety model:

- Building count.
- Building area.
- Building coverage ratio.
- Mean building area.
- Commercial POI density.
- Nightlife POI density.
- Transit POI density.
- School POI density.
- Total POI count.
- POI diversity.

OpenStreetMap data is fetched through `osmnx`, tiled into small chunks, and
cached under:

```text
data/raw/osm_chunks/
data/raw/osm_raw_buffer400.gpkg
```

The cache allows interrupted or long OSM collection runs to resume without
starting from zero.

These POI features are used by the safety modeling pipeline. The recommendation
API reads `grid.convenience_score` from PostgreSQL, but the current main
pipeline initializes that column to `0` unless convenience scores are populated
separately or the convenience insertion block in `data_processing.py` is
enabled.

### Rental Listings

Rental listing processing is handled by `data_processing.py`,
`selenium_scraper.py`, and `scraper.py`.

Supported listing workflows:

- Selenium scraping from Craigslist search result pages.
- Static fallback parsing from `data/raw/static_listing_data.txt`.
- Selenium detail scraping to update listing latitude and longitude.

Each listing is enriched with:

- `distance_score`: normalized straight-line distance to USC.
- `convenience_score`: grid-level convenience score.
- `safety_score`: grid-level predicted safety score.
- `affordability_score`: generated by the API from listing rent distribution.

## Safety Modeling

`safety_main.py` trains two XGBoost regression models:

- Property crime model.
- Violence crime model.

The model uses monthly crime history from 2010-2024 plus static grid features.
It recursively forecasts monthly crime counts for January 2025 through December
2026.

The 2026 annual safety score is computed from annual predicted risk:

```text
pred_property_annual = sum(pred_property for 2026)
pred_violence_annual = sum(pred_violence for 2026)
risk = 0.4 * pred_property_annual + 0.6 * pred_violence_annual
safety_score = 100 * (1 - risk_percentile)
```

Generated outputs:

| File | Purpose |
| --- | --- |
| `results/future_monthly_predictions_2025_2026.csv` | Monthly 2025-2026 property and violence crime forecasts |
| `results/final_grid_safety_2026.csv` | Annual 2026 safety score, risk rank, and safety level by grid |
| `results/safety_folds_results.csv` | Cross-validation metrics |

`safety_modeling.py` runs rolling validation folds from 2020 through 2024 and
writes fold-level RMSE, MAE, hotspot hit rate, and Jaccard similarity.

## Recommendation Logic

The backend and frontend rank listings with user-adjustable weights.

Default recommendation weights:

| Factor | Default Weight |
| --- | --- |
| Safety | 30 |
| Convenience | 25 |
| Distance to USC | 45 |
| Affordability | 0 |

`/api/recommend` normalizes the weights so they sum to 1, computes a weighted
score for each listing, and returns the top results.

The frontend recommendation page currently exposes sliders for safety,
convenience, and distance. Price is handled with a direct rent range filter
instead of being included in the visible slider weights.

## Running Common Tasks

### Build or Refresh the Main Pipeline

```bash
python3 src/backend/data_pipeline.py
```

This command may truncate and recreate project tables. Use a dedicated project
database.

### Generate Safety Predictions Only

```bash
python3 src/backend/safety_main.py
```

### Run Model Validation

```bash
python3 src/backend/safety_modeling.py
```

### Recalculate Existing Listing Scores

```bash
python3 src/backend/data_processing.py
```

The standalone script still prompts for static data or scraping, but its active
code path recalculates scores for listings already stored in PostgreSQL. To
refresh the listing table from Craigslist, use the optional scraper branch in
`data_pipeline.py`.

### Run the Full Web App

```bash
cd src/frontend
npm install
npm run build
cd ../..
python3 src/backend/main.py
```

Default Flask server:

```text
Host: 127.0.0.1
Port: 5000
URL:  http://127.0.0.1:5000
```

### Run Frontend Development Server

Terminal 1:

```bash
python3 src/backend/main.py
```

Terminal 2:

```bash
cd src/frontend
npm run dev
```

The Vite development server serves the frontend and proxies API calls to Flask.

## Reproducibility Notes

- PostgreSQL must be running before executing the pipeline.
- The configured database should already exist before the pipeline starts.
- `data_pipeline.py` can truncate `listing`, `crime`, `grid`, and
  `monthly_crime`.
- Selenium scraping requires Chrome and a compatible ChromeDriver setup.
- Craigslist page structure can change and may require scraper updates.
- OpenStreetMap requests can be slow and network-dependent; cached GPKG files
  reduce repeated requests.
- GeoPandas/Shapely/Fiona dependencies may require system geospatial libraries,
  depending on the local Python environment.
- The Flask API can return fallback listing data from local static HTML if the
  database is unavailable or empty, but the safety map requires populated grid
  data and grid shapefiles.
- `grid.convenience_score` is part of the schema, but the current pipeline does
  not automatically populate it from POI features.
- The frontend production build is stored in `src/frontend/dist/`.

## Current Limitations

The current project assigns each rental listing to a single 400m grid cell and
uses that grid cell's safety and convenience scores. This is simple and
interpretable, but listings near grid boundaries may receive different scores
even when they are physically close.

The system also uses straight-line distance to USC rather than walking,
cycling, driving, or transit travel time. It does not yet model time-of-day
safety, route-level safety, housing quality, landlord reliability, or real-time
listing availability.

Future improvements could include:

- Network-distance buffers around listings.
- Route-based safety to USC.
- Smaller or adaptive spatial units.
- Distance-weighted crime exposure.
- Transit travel time and walkability.
- Richer listing quality signals.
- More robust scraper monitoring and stale-listing detection.
