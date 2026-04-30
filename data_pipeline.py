import data_processing as dp
import crime_data_processing as cdp
import connection
from dotenv import load_dotenv
from pathlib import Path
import glob
import selenium_scraper as ss
import db_execution as dbe
import subprocess
import sys
import geopandas as gpd

load_dotenv()
tables = ('listing','crime','grid','monthly_crime')
columns = {
    'listing':['href','title','price','location_text','latitude','longitude','distance_score','convenience_score','safety_score','bedroom_number'],
    'crime': ['crime_id','latitude','longitude','date', 'type'],
    'grid': ['grid_id', 'safety_score', 'convenience_score'],
    'monthly_crime': ['grid_id', 'month_start','crime_count', 'property_crime', 'violence_crime']
}

def table_schema_matches(cur, table_name):
    cur.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = current_schema() AND table_name = %s
        ORDER BY ordinal_position
        """,
        (table_name,)
    )
    existing_columns = [row[0] for row in cur.fetchall()] # get the first column of each row, which is the column name
    expected_columns = columns[table_name]
    if table_name == 'listing':
        expected_columns = ['listing_id'] + expected_columns
    return existing_columns == expected_columns

def check_db():
    print("Checking database...")
    try:
        conn = connection.get_connect()
        print("Database connection successful!")
    except Exception as e:
        print(f"Database connection failed: {e}")
        return

    cur = conn.cursor()

    for table in tables:
        try:
            print(f"Checking {table} table...")
            if not table_schema_matches(cur, table):
                raise ValueError("schema mismatch")
        except:
            print(f"{table} table does not match the expected schema. Recreating the table...")
            cur.execute(f"DROP TABLE IF EXISTS {table}")
            conn.commit()
            create_table(table)
            print(f"{table} table created successfully.")

    cur.close()
    conn.close()
        
def create_table(table_name):
    conn = connection.get_connect()
    cur = conn.cursor()

    if table_name == 'grid':
        cur.execute("""
            CREATE TABLE IF NOT EXISTS grid (
                grid_id INTEGER PRIMARY KEY,
                safety_score INTEGER NOT NULL DEFAULT 0,
                convenience_score INTEGER NOT NULL DEFAULT 0
            );
        """)

    elif table_name == 'listing':
        cur.execute("""
            CREATE TABLE IF NOT EXISTS listing (
                listing_id SERIAL PRIMARY KEY,
                href TEXT NOT NULL,
                title TEXT NOT NULL,
                price NUMERIC,
                location_text TEXT,
                latitude DOUBLE PRECISION,
                longitude DOUBLE PRECISION,
                distance_score INTEGER,
                convenience_score INTEGER,
                safety_score INTEGER,
                bedroom_number INTEGER
            );
        """)

    elif table_name == 'crime':
        cur.execute("""
            CREATE TABLE IF NOT EXISTS crime (
                crime_id INTEGER PRIMARY KEY,
                latitude DOUBLE PRECISION,
                longitude DOUBLE PRECISION,
                date TIMESTAMP,
                type VARCHAR(100)
            );
        """)

    elif table_name == 'monthly_crime':
        cur.execute("""
            CREATE TABLE IF NOT EXISTS monthly_crime (
                grid_id INTEGER NOT NULL REFERENCES grid(grid_id),
                month_start DATE NOT NULL,
                crime_count INTEGER DEFAULT 0,
                property_crime INTEGER DEFAULT 0,
                violence_crime INTEGER DEFAULT 0,
                PRIMARY KEY (grid_id, month_start)
            );
        """)

    else:
        raise ValueError(f"Unknown table name: {table_name}")

    conn.commit()
    cur.close()
    conn.close()
  
def ensure_inputs():
    # check the minimum required input files
    building_shp = Path("../data/Building_Footprints-shp/building.shp")
    city_boundary_shp = Path("../data/City_Boundary/City_Boundary.shp")
    usc_campus = Path("../data/usc_campus/usc_campus.shp")
    crime_data1 = glob.glob("../data/Crime_Data_from_2010_to_2019*.csv")
    crime_data2 = glob.glob("../data/Crime_Data_from_2020_to_2024*.csv")
    # or
    combined_crime = Path("../data/Crime_Data_from_2010_to_2024.csv")

    if not building_shp.exists():
        raise FileNotFoundError(f"Missing building shapefile: {building_shp}")

    if not city_boundary_shp.exists():
        raise FileNotFoundError(f"Missing city boundary shapefile: {city_boundary_shp}")

    if not usc_campus.exists():
        raise FileNotFoundError(f"Missing USC campus shapefile: {usc_campus}")
    
    if not crime_data1:
        if not combined_crime.exists():
            raise FileNotFoundError("Missing 2010-2019 crime CSV files.")
    
    if not crime_data2:
        if not combined_crime.exists():
            raise FileNotFoundError("Missing 2020-2024 crime CSV files.")

def check_stage():
    data_dir = Path("../data")
    output_dir = Path("../output")
    combined_crime = data_dir / "Crime_Data_from_2010_to_2024.csv"
    grid_shp = data_dir / "City_Boundary/LA_400m_grid.shp"
    
    future_pred = output_dir / "future_monthly_predictions_2025_2026.csv"
    final_grid = output_dir / "final_grid_safety_2026.csv"

    monthly_ready = False
    try:
        conn = connection.get_connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM monthly_crime LIMIT 1")
        monthly_ready = cur.fetchone() is not None # check if there's at least one row in monthly_crime
        cur.close()
        conn.close()
    except Exception:
        monthly_ready = False

    # return the first missing stage
    if not grid_shp.exists():
        return "grid"

    if not combined_crime.exists():
        return "crime"

    if not monthly_ready:
        return "prepare"

    if not future_pred.exists() or not final_grid.exists():
        return "safety"
    
    return False

def refresh_crime_tables():
    combined_crime = Path("../data/Crime_Data_from_2010_to_2024.csv")
    if not combined_crime.exists():
        raise FileNotFoundError("Missing combined crime CSV before loading crime tables.")

    print("Refreshing crime and monthly_crime tables...")
    refresh_grid_table()

    dbe.db_truncate('crime')
    crime_list = dp.get_safety()
    dbe.db_insert('crime', columns['crime'], crime_list)

    dbe.db_truncate('monthly_crime')
    monthly_list = cdp.get_monthly()
    dbe.db_insert('monthly_crime', columns['monthly_crime'], monthly_list)

def refresh_grid_table():
    print("Refreshing grid table...")
    grid = gpd.read_file("../data/City_Boundary/LA_400m_grid.shp")
    grid = grid.to_crs("EPSG:32611").reset_index(drop=True)
    grid["grid_id"] = grid.index + 1
    grid_list = [(int(grid_id), 0, 0) for grid_id in grid["grid_id"]]
    dbe.db_truncate('grid')
    dbe.db_insert('grid', columns['grid'], grid_list)

def data_pipeline():
    ensure_inputs()
    check_db()
    stage = True
    while check_stage():
        stage = check_stage()
        if stage == "grid":
            print("Missing grid data, running map_division.py ...")
            subprocess.run([sys.executable, "map_division.py"], check=True)
        elif stage == "crime":
            print("Missing combined crime data, running crime_data_processing.py ...")
            subprocess.run([sys.executable, "crime_data_processing.py"], check=True)

        elif stage == "prepare":
            refresh_crime_tables()
            print("Missing monthly panel data, running safety_model_prepare.py ...")
            subprocess.run([sys.executable, "safety_model_prepare.py"], check=True)

        elif stage == "safety":
            print("Missing safety model outputs, running safety_main.py ...")
            subprocess.run([sys.executable, "safety_main.py"], check=True)


def main():
    data_pipeline()
    IfScrap = input("Do you want to run the web scraper to update the listing data? (y/n): ")
    if IfScrap.lower() == 'y':
        number = input("How many rounds of scraping do you want to run? each round takes 200 listings roughly. :")
        listing_details = ss.scrap(int(number))
        print(f"Found {len(listing_details)} listings")
        verify = input("Do you want to update these listing data into database? (type yes or no)")
        if verify.lower() == "yes":
            dbe.db_truncate('listing')
            dbe.db_insert('listing', columns['listing'], listing_details)
            ss.scrap_detail()
            dp.get_scores()
        else:
            print("Listing data not updated.")
    

if __name__ == "__main__":
    main()
