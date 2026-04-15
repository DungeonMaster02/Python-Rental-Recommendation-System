# 🏠 USC Housing Recommendation & Safety Analysis System

A comprehensive data-driven housing recommendation system for USC students, integrating rental listings, geospatial crime analysis, amenities data, and predictive safety modeling.

## 📌 Overview

This project helps USC students make smarter housing decisions by analyzing real-world data across Los Angeles. The system evaluates rental neighborhoods using:

* **Safety Predictions** - Machine learning models predicting crime trends
* **Convenience Scores** - Proximity to amenities (hospitals, transit, restaurants, parks, etc.)
* **Distance Assessment** - Walking/transit distance to USC campus
* **Neighborhood Grids** - 400m grid-based geographical analysis

Users can explore housing options with detailed neighborhood safety forecasts and amenity accessibility scores.

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
     - Priority crimes (property crimes)
     - Violence crimes
   - Monthly crime trend prediction by grid
   - Training period: 2010-2024, forecasting 2025-2026

5. **Database Backend** (`connection.py`, `db_execution.py`)
   - PostgreSQL database
   - Tables: listings, crime, grid, monthly_crime
   - Efficient spatial queries and monthly aggregations

6. **Frontend** (`frontend/`, `main.py`)
   - FastAPI REST API
   - Interactive housing search and filtering
   - Real-time neighborhood scoring

---

## 📊 Data Sources

1. **Rental Listings**
   - Source: Craigslist Los Angeles
   - URL: https://losangeles.craigslist.org/search/apa
   - Data: price, location, title, coordinates, bedrooms

2. **Amenities Data**
   - Source: OpenStreetMap (via `osmnx`)
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
  - Public transport: 3.0 (highest priority)
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
├── main.py                      # FastAPI entry point
├── safety_main.py              # Safety model training pipeline
├── data_processing.py           # Listing & convenience processing
├── crime_data_processing.py    # Crime aggregation & monthly stats
├── safety_model_prepare.py     # Data prep for XGBoost
├── safety_modeling.py          # XGBoost model training
├── scraper.py                  # Craigslist scraper
├── connection.py               # PostgreSQL connection
├── db_execution.py             # Database operations
├── map_dividision.py           # Grid processing utilities
├── frontend/                   # Frontend assets

data/
├── Crime_Data_from_2010_2024.csv        # Crime dataset
├── Static_listing_data.txt              # Craigslist cache
├── City_Boundary/                       # LA boundary shapefile
├── LA_400m_grid.shp                     # Grid divisions
├── usc_campus/                          # Campus location
├── Building_Footprints-shp/             # Building data
└── osm_chunks/                          # OSM amenities cache

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
pip install psycopg2-binary python-dotenv fastapi
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

# 4. Train safety models and generate forecasts
python safety_main.py
```

### API Server
```bash
python main.py  # Starts FastAPI on http://localhost:8000
```

### Recommendations Query
```python
# Get top housing recommendations with personalized weights
GET /recommendations?safety=0.4&convenience=0.3&distance=0.2&price=0.1
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

**XGBoost Models** trained on 2010-2024 monthly crime data:
- Target variables: priority_crime_target_next, violence_crime_target_next
- Features: lagged crime counts, seasonal indicators, grid characteristics
- Train/Test split: Historical (2020-2024 forecast window)
- Hyperparameters: max_depth=4, eta=0.03, num_boost_round=600

---

## 🔍 Key Questions Addressed

- Which neighborhoods are safest for students?
- Where can I find the best amenities near USC?
- How far is this listing from campus?
- How have crime trends changed over time?
- What's the predicted safety level next month?

---

## 📝 Output Files

- `final_grid_safety_2026.csv` - Grid safety scores and predictions
- `future_monthly_predictions_2025_2026.csv` - Monthly crime forecasts
- `safety_folds_results.csv` - Model cross-validation results
- Database tables: listings, crime, grid, monthly_crime

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

## 👤 Author

Pengshao Ye
