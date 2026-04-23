# 🏠 USC Housing Recommendation & Safety Analysis System

A comprehensive data-driven housing recommendation system for USC students, integrating rental listings, geospatial crime analysis, amenities data, and predictive safety modeling.

**Status**: ✅ **Project Complete**

## 📌 Overview

This project helps USC students make smarter housing decisions by analyzing real-world data across Los Angeles. The system evaluates rental neighborhoods using:

* **Safety Predictions** - Machine learning models predicting crime trends through 2026
* **Convenience Scores** - Proximity to amenities (hospitals, transit, restaurants, parks, etc.)
* **Distance Assessment** - Walking/transit distance to USC campus
* **Neighborhood Grids** - 400m grid-based geographical analysis
* **Interactive Web UI** - React + TypeScript frontend with map visualization

Users can explore housing options with detailed safety forecasts and amenity accessibility scores via the interactive web interface.

---

## 🏗️ Architecture & Components

### Backend Pipeline

1. **Data Collection & Scraping** (`scraper.py`)
   - Craigslist rental listings (Los Angeles)
   - OpenStreetMap amenities data
   - LA Open Data crime incidents (2010-2024)

2. **Data Processing** (`data_processing.py`, `crime_data_processing.py`)
   - Geographic coordinate conversion
   - 400m grid-based LA city division
   - Spatial joining of listings, crimes, and amenities
   - De-duplication and data validation

3. **Feature Engineering**
   - **Safety Score**: Derived from grid-level crime density
   - **Convenience Score**: Weighted amenity scoring (hospitals: 2.5, transit: 3.0, parks: 1.0, etc.)
   - **Distance Score**: Normalized distance to USC centroid (max 12km)
   - **Affordability Score**: Rent-based scoring

4. **Predictive Modeling** (`safety_main.py`, `safety_modeling.py`)
   - **XGBoost time-series models** for crime forecasting
   - Separate models for:
     - Property crimes (property crimes)
     - Violence crimes
   - Monthly crime trend prediction by grid
   - Training period: 2010-2024, forecasting 2025-2026

5. **Database Backend** (`connection.py`, `db_execution.py`)
   - PostgreSQL database
   - Tables: listings, crime, grid, monthly_crime
   - Efficient spatial queries and monthly aggregations

6. **Application Layer** (`frontend/`, `main.py`)
   - Flask REST API + SPA static hosting
   - React + TypeScript frontend (Vite build)
   - Interactive housing search, map exploration, and recommendation UI

---

## 📊 Data Sources

1. **Rental Listings**
   - Source: Craigslist Los Angeles
   - URL: https://losangeles.craigslist.org/search/apa
   - Data: price, location, title, coordinates, bedrooms

2. **Amenities Data**
   - Source: OpenStreetMap (via `osmnx`)
   - Current pipeline does **not** use Google Places API
   - Categories: hospitals, pharmacies, supermarkets, transit stations, restaurants, parks, laundry
   - Weighted scoring for convenience

3. **Crime Data**
   - Source: LA Open Data Portal
   - URL: https://data.lacity.org/Public-Safety/Crime-Data-from-2010-to-2024
   - Coverage: 2010-2024, continuous updates
   - Classification: Property crimes, Violence crimes

4. **Geographic Data**
   - Source: Los Angeles GeoHub
   - LA City Boundary (shapefile)
   - 400m grid divisions (shapefile)
   - Building footprints
   - USC campus location

---

## 📈 Methodology

### Step 1: Geographic Discretization
- Divide LA into 400m × 400m grids
- Assign grid_id to all listings, crimes, and amenities
- Enables efficient spatial aggregation

### Step 2: Crime Analysis
- Aggregate monthly crime counts by grid and crime type
- Train XGBoost models on historical data
- Generate safety predictions for 2025-2026

### Step 3: Amenity Scoring
- Identify amenities within 400m buffer of each grid
- Apply weighted scoring:
  - Public transport: 3.0 (highest property)
  - Supermarkets/hospitals: 2.5
  - Restaurants/transit stops: 1.5-2.0
  - Parks/laundry: 1.0
- Aggregate convenience scores per grid

### Step 4: Listing Scoring
Each listing receives normalized scores (0-100):
- **Safety**: Based on predicted/historical crime levels
- **Convenience**: Sum of nearby amenity weights
- **Distance**: Inverse distance to USC (capped at 12km)
- **Affordability**: Relative to market rent

### Step 5: Ranking & Recommendation
- Combine scores with user-defined weights
- Rank listings by weighted final score
- Display with predicted crime trends and amenity details

---

## 📁 Project Structure

```
code/
├── main.py                           # Flask entry point + API routes
├── safety_main.py                   # Safety model training pipeline
├── data_processing.py               # Listing & convenience scoring
├── crime_data_processing.py         # Crime aggregation & monthly stats
├── safety_model_prepare.py          # Feature engineering for XGBoost
├── safety_modeling.py               # XGBoost training & validation
├── scraper.py                       # Basic Craigslist scraper
├── selenium_scraper.py              # Advanced Selenium scraper
├── safetymap.py                     # Grid safety data utilities
├── connection.py                    # PostgreSQL connection
├── db_execution.py                  # Database CRUD operations
├── map_dividision.py                # Grid processing utilities
├── frontend/                        # React + TypeScript UI
│   ├── src/                         # React components
│   ├── dist/                        # Built static files (Vite)
│   └── package.json                 # Node dependencies
└── cache/                           # OSM cached data
    └── *.json                       # Pre-scraped amenities

data/
├── Crime_Data_from_2010_2024.csv    # Full crime dataset (2010-2024)
├── Crime_Data_from_2010_to_2019_*.csv  # Pre-split historical
├── Crime_Data_from_2020_to_2024_*.csv  # Pre-split recent
├── City_Boundary/                   # LA city boundary
├── LA_400m_grid.shp                 # 400m grid divisions
├── usc_campus/                      # USC campus boundary
├── Building_Footprints-shp/         # LA building footprints
└── osm_chunks/                      # OSM amenities chunks

output/
├── final_grid_safety_2026.csv           # Safety predictions
├── future_monthly_predictions_2025_2026.csv  # Crime forecast
└── safety_folds_results.csv             # Model validation
```

---

## 🛠️ Installation & Setup

### Requirements
- Python 3.8+
- PostgreSQL database
- Conda or venv

### Dependencies
```bash
pip install pandas geopandas osmnx xgboost beautifulsoup4 
pip install psycopg2-binary python-dotenv flask
```

### Configuration
Create `.env` file with PostgreSQL credentials:
```
host=localhost
dbname=housing_db
user=postgres
password=your_password
port=5432
```

### Database Setup
```bash
python connection.py  # Initialize tables
```

---

## 🚀 Usage

### Data Pipeline
```bash
# 1. Scrape listings and process data
python data_processing.py

# 2. Process crime data and calculate monthly stats
python crime_data_processing.py

# 3. Prepare data for modeling
python safety_model_prepare.py

# 4. Train safety models and generate forecasts (generates 2025-2026 predictions)
python safety_main.py

# 5. (Optional) Validate models with cross-validation
python safety_modeling.py
```

### API Server
```bash
python main.py
```

Server configuration (in `main.py`):
- Host: `127.0.0.1`
- Port: `5000`
- Frontend served from `code/frontend/dist` (built with Vite)

### REST API Endpoints

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|-----------|
| `/api/health` | GET | Server health check | - |
| `/api/listings` | GET | Get all rental listings | `limit` (int, default: 100) |
| `/api/recommend` | GET | Get ranked recommendations | `safety`, `convenience`, `distance`, `affordability` (weights, 0.0-1.0) |
| `/api/grid-safety` | GET | Get grid safety scores by year | - |
| `/api/grid-safety-geojson` | GET | Get GeoJSON for map visualization | - |
| `/api/home-stats` | GET | Homepage statistics | - |
| `/api/model-metrics` | GET | ML model validation metrics | - |

**Example Request**:
```bash
# Get top 50 recommendations with custom weights
curl "http://localhost:5000/api/recommend?safety=0.4&convenience=0.3&distance=0.2&affordability=0.1&limit=50"
```

---

## 🎯 Key Features

- **Predictive Safety**: ML-powered crime forecasting by neighborhood
- **Multi-Factor Scoring**: Personalized weighting of factors
- **Geospatial Analysis**: Grid-based neighborhood evaluation
- **Real-Time Updates**: Integrate latest Craigslist and crime data
- **Historical Trends**: Analyze crime patterns (2010-2024)
- **Amenity Accessibility**: Weighted scoring by proximity and type

---

## 📊 Model Performance

**XGBoost Time-Series Models** trained on 2010-2024 monthly crime data:

**Architecture**:
- **Two separate models**: property crimes (property) vs Violence crimes
- **Training data**: 2010-2024 monthly crime counts aggregated by 400m grid
- **Prediction period**: Monthly forecasts for 2025-2026 (24 months)

**Features Engineering**:
- Lagged crime counts: 1, 2, 3, 6, 12 months
- Rolling averages: 3, 6, 12 months
- Seasonal encoding: sin/cos of month for cyclical patterns
- Building density features
- Grid static characteristics

**Hyperparameters**:
- `max_depth`: 4
- `eta` (learning rate): 0.03
- `subsample`: 0.7
- `lambda` (L2 regularization): 2.0
- `num_boost_round`: 600

**Cross-Validation** (5 folds):
- RMSE (Root Mean Squared Error): Track prediction error magnitude
- MAE (Mean Absolute Error): Track average deviation
- Hit Rate: % of correctly predicted crime hotspots
- Jaccard Similarity: Spatial overlap of top 10% dangerous grids

**Evaluation Results**:
- Detailed metrics saved in `output/safety_folds_results.csv`
- Models evaluate past performance to inform 2025-2026 forecasts

---

## 🔍 Key Questions Addressed

- Which neighborhoods are safest for students?
- Where can I find the best amenities near USC?
- How far is this listing from campus?
- How have crime trends changed over time?
- What's the predicted safety level next month?

---

## 📝 Output Files

| File | Format | Purpose | Records |
|------|--------|---------|---------|
| `output/final_grid_safety_2026.csv` | CSV | Annual grid safety scores for 2026 | 1600+ grids |
| `output/future_monthly_predictions_2025_2026.csv` | CSV | Monthly crime predictions by grid | 1600+ grids × 24 months |
| `output/yearly_grid_safety_2020_2026.csv` | CSV | Historical + predicted annual scores | Full historical + forecast |
| `output/safety_folds_results.csv` | CSV | Cross-validation metrics | RMSE, MAE, Hit Rate, Jaccard |
| `output/agent_grid_context_basic.json` | JSON | Grid context for LLM agents | - |
| `output/agent_grid_profile_index_2026.json` | JSON | Grid profiles for ranking | - |

**Database Tables**:
- `listing` - Rental listings with computed scores
- `crime` - Raw crime incidents with locations
- `grid` - LA grid cells with convenience/safety scores
- `monthly_crime` - Aggregated monthly crime by grid and type

---

## ✍️ Authors

USC DSCI-510 Final Project

---

## 📜 License

Educational Project - USC

---

## ❓ Key Questions

This project aims to explore:

* Which listings best match different student preferences?
* How do recommendations change with different weights?
* Are cheaper rentals associated with:

  * Lower safety?
  * Longer distance from USC?

---

## 📦 Expected Output

* Ranked list of rental listings (titles or URLs)
* Top recommendations based on user preferences
* (Optional) Visualizations:

  * Safety vs price
  * Distance vs affordability
  * Amenities comparison

---

## 🚧 Limitations

* Does not analyze **interior conditions** of housing
* Does not include:

  * Image recognition
  * Deep semantic analysis of listings
* Focus is on **external and location-based factors**

---

## 🧠 Future Improvements

* Image-based apartment quality analysis
* NLP-based listing description analysis
* More advanced personalization models

---

## 📚 Key Technical Achievements

1. **Full-Stack Integration**: Web scraping → geospatial processing → ML modeling → interactive UI
2. **Temporal ML**: Time-series XGBoost with proper lag/seasonal features
3. **Geospatial Sophistication**: 400m grid discretization, spatial joins, amenity buffering
4. **Production API**: Flask REST endpoints with PostgreSQL backend
5. **Multi-year Forecasting**: 24-month crime predictions (2025-2026)
6. **Modern Frontend**: React + TypeScript with Vite build system
7. **Personalization**: User-customizable recommendation weighting

## 🔄 Data Flow

```
Craigslist HTML → selenium_scraper.py
Crime CSV → crime_data_processing.py  
OSM Amenities → osmnx library
LA Shapefiles → map_division.py
                    ↓
            Geographic Indexing (400m grid)
                    ↓
            PostgreSQL Database
                    ↓
        Feature Engineering & ML
                    ↓
    XGBoost (property & Violence crimes)
                    ↓
    2025-2026 Forecasts + Scores
                    ↓
    Flask API + React UI
                    ↓
        Interactive Housing Search
```