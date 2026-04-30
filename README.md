# USC Housing Recommendation & Safety Analysis System

A data-driven housing recommendation system for USC students. The project combines rental listings, Los Angeles crime data, geospatial features, OpenStreetMap amenities, XGBoost safety forecasting, a PostgreSQL backend, and a React + TypeScript frontend.

The system helps users compare rentals by safety, convenience, distance to USC, and affordability, then displays ranked recommendations and grid-level safety information through a web interface.

## Project Structure

```text
code/
├── data_pipeline.py                # Orchestrates database setup, data loading, and safety modeling
├── main.py                         # Flask API and frontend static server
├── data_processing.py              # Listing processing and scoring
├── crime_data_processing.py        # Crime data merge and database loading
├── safety_model_prepare.py         # Spatial and time-series feature engineering
├── safety_main.py                  # XGBoost training and 2025-2026 forecasting
├── safety_modeling.py              # Model validation script
├── selenium_scraper.py             # Primary Selenium scraper (dynamic pages)
├── scraper.py                      # Static listing fallback scraper
├── connection.py                   # PostgreSQL connection helper
├── db_execution.py                 # Database insert/query helpers
├── map_division.py                 # LA 400m grid construction
├── requirements.txt                # Python dependencies
└── frontend/                       # React + TypeScript frontend
    ├── package.json
    ├── package-lock.json
    └── src/

data/
├── Crime_Data_from_2010_to_2019_*.csv
├── Crime_Data_from_2020_to_2024_*.csv
├── Crime_Data_from_2010_to_2024.csv
├── City_Boundary/
├── Building_Footprints-shp/
├── usc_campus/
├── osm_chunks/
└── osm_raw_buffer400.gpkg

output/
├── final_grid_safety_2026.csv
├── future_monthly_predictions_2025_2026.csv
└── safety_folds_results.csv
```

## Data Sources

This project's crime-safety data source and processing workflow are consistent with the referenced SSCI-586 Project5 pipeline.

| Dataset | Source | Used For |
|---------|--------|----------|
| Crime Data 2010-2019 | LA Open Data: https://data.lacity.org/Public-Safety/Crime-Data-from-2010-to-2019/63jg-8b9z/about_data | Historical incident records |
| Crime Data 2020-2024 | LA Open Data: https://data.lacity.org/Public-Safety/Crime-Data-from-2020-to-2024/2nrs-mtv8/about_data | Recent incident records |
| LA City Boundary | LA GeoHub: https://geohub.lacity.org/datasets/lahub::city-boundary/explore | 400m grid clipping |
| Building Footprints | LA GeoHub: https://geohub.lacity.org/datasets/lahub::building-footprints/explore | Static grid features |
| OpenStreetMap POIs | OpenStreetMap through `osmnx` | Amenity and POI density features |
| Rental Listings | Craigslist Los Angeles apartment search | Housing recommendation candidates (Selenium primary, BeautifulSoup fallback) |
| USC Campus Boundary | Local shapefile in `data/usc_campus/` | Distance-to-campus scoring |

Required data files should be placed under the project-level `data/` directory, one level above `code/`.

## Data Processing Details

### 1. Spatial Grid Construction

`map_division.py` reads the LA city boundary shapefile, reprojects it to `EPSG:32611` so distances are meter-based, creates a fixed `400m x 400m` fishnet, clips cells to the LA boundary, and writes `data/City_Boundary/LA_400m_grid.shp`.

### 2. Crime Data Harmonization

`crime_data_processing.py` combines the 2010-2019 and 2020-2024 LA crime files into `data/Crime_Data_from_2010_to_2024.csv`. Duplicate incidents are removed by `DR_NO`.

The modeling pipeline uses `DR_NO`, `LAT`, `LON`, `DATE OCC`, and `Crm Cd Desc`. It parses coordinates and dates, removes invalid or zero coordinates, converts points from `EPSG:4326` to the grid CRS, and spatially joins incidents to grid cells.

Crime descriptions are grouped into two target categories:

- `violence_crime`: descriptions in the predefined violent-crime set.
- `property_crime`: all other incidents.

The cleaned incidents are aggregated into a complete `grid_id x month_start` panel with missing grid-month combinations filled with zero counts.

### 3. Static Spatial Features

`safety_model_prepare.py` adds static features to each grid:

- Building count.
- Total building intersection area.
- Building coverage ratio.
- Mean building area.
- OSM POI counts and densities.
- POI diversity.

OpenStreetMap features are fetched with `osmnx`, cached by chunks in `data/osm_chunks/`, and merged into `data/osm_raw_buffer400.gpkg`. POIs are classified into groups such as commercial, nightlife, transit, and school before grid-level aggregation.

### 4. Time-Series Feature Engineering

The safety pipeline creates monthly features for both property and violence crime:

- Calendar features: `month`, `year`, `month_sin`, `month_cos`, `time_idx`.
- Lag features: `lag1`, `lag2`, `lag3`, `lag6`, `lag12`.
- Rolling means: `roll3`, `roll6`, `roll12`.
- Next-month prediction labels through `target_next`.

Rows without complete lag history or target labels are excluded from model training.

### 5. Listing Crawling Strategy

The project uses two listing collection paths:

- Primary method: `selenium_scraper.py` (`scrap`) handles Craigslist dynamic result pages by scrolling and extracting listing cards with Selenium.
- Backup method: `scraper.py` uses `requests + BeautifulSoup` and is intended for static HTML fallback workflows.
- In `data_processing.py`, option `2` uses Selenium scraping directly; option `1` parses local static HTML from `data/static_listing_data.txt`.

For coordinates, Selenium detail crawling (`scrap_detail`) reads embedded posting JSON and updates latitude/longitude in the listing table.

### 6. Listing and Recommendation Scoring

Rental listings are assigned to grids and scored with:

- `safety_score`: derived from predicted grid-level crime risk.
- `convenience_score`: weighted nearby amenity score.
- `distance_score`: normalized distance to USC.
- `affordability_score`: rent-based score.

The API combines these scores with user-provided weights and returns ranked housing recommendations.

## Modeling Details

The safety model uses two separate XGBoost regressors:

- Property crime model.
- Violence crime model.

The models are trained on monthly grid-level crime data from 2010-2024 and recursively forecast monthly risk for 2025-2026. Predictions are clipped to non-negative values.

For 2026 annual safety scoring, monthly predictions are aggregated by grid:

```text
pred_property_annual = sum(pred_property)
pred_violence_annual = sum(pred_violence)
risk = 0.4 * pred_property_annual + 0.6 * pred_violence_annual
safety_score = 100 * (1 - risk_percentile)
```

Safety buckets are derived from the final score:

- `Very Unsafe`: <= 20
- `Unsafe`: 20-40
- `Moderate`: 40-60
- `Safe`: 60-80
- `Very Safe`: > 80

`safety_modeling.py` provides validation metrics, including RMSE, MAE, hotspot hit rate, and Jaccard similarity. Results are written to `output/safety_folds_results.csv`.

## Setup

### Python Environment

```bash
cd code
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Frontend Environment

```bash
cd code/frontend
npm install
npm run build
```

### Database Configuration

Create `code/.env` with PostgreSQL credentials:

```text
host=localhost
dbname=housing_db
user=postgres
password=your_password
port=5432
Rent_URL=https://losangeles.craigslist.org/search/apa
```

Initialize database tables:

```bash
cd code
python connection.py
```

## Usage

Run the full data and modeling pipeline:

```bash
cd code
python data_pipeline.py
```

The pipeline checks required input files, initializes database tables, builds missing grid and crime data, prepares monthly crime data, and runs the safety forecasting stage when outputs are missing.

Optional stage-by-stage commands for debugging:

```bash
python map_division.py
python crime_data_processing.py
python safety_model_prepare.py
python safety_main.py
python safety_modeling.py
```

Process listings and load recommendation data:

```bash
python data_processing.py
```

Recommended flow (primary):

- Run `python data_processing.py`, then choose option `2` to scrape with Selenium.
- Enter the number of scrape rounds when prompted.

Fallback flow (backup):

```bash
python scraper.py
python data_processing.py
```

Then choose option `1` in `data_processing.py` to parse `data/static_listing_data.txt`.

Start the Flask API and serve the built frontend:

```bash
python main.py
```

Default server configuration:

- Host: `127.0.0.1`
- Port: `5000`
- Build the frontend with `npm run build` before serving the web app.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Server health check |
| `/api/listings` | GET | Rental listings |
| `/api/recommend` | GET | Weighted housing recommendations |
| `/api/grid-safety` | GET | Grid safety scores |
| `/api/grid-safety-geojson` | GET | Grid safety GeoJSON for map visualization |
| `/api/home-stats` | GET | Homepage summary statistics |
| `/api/model-metrics` | GET | Safety model validation metrics |

Example:

```bash
curl "http://localhost:5000/api/recommend?safety=0.4&convenience=0.3&distance=0.2&affordability=0.1&limit=50"
```

## Outputs

| File | Purpose |
|------|---------|
| `output/final_grid_safety_2026.csv` | Annual 2026 grid safety scores |
| `output/future_monthly_predictions_2025_2026.csv` | Monthly 2025-2026 crime forecasts |
| `output/safety_folds_results.csv` | Validation metrics |
