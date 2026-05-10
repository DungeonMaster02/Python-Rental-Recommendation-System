from bs4 import BeautifulSoup
import pandas as pd
import geopandas as gpd
import osmnx as ox
import json
import re

from path_config import PROCESSED_DIR, RAW_DIR, USC_CAMPUS_DIR

import scraper
import db_execution as dbe
import connection
import selenium_scraper as ss

def get_grid_score_map() -> dict[int, tuple[float, float]]:
    conn = connection.get_connect()
    cur = conn.cursor()
    cur.execute("SELECT grid_id, convenience_score, safety_score FROM grid")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {int(grid_id): (float(convenience_score or 0), float(safety_score or 0)) for grid_id, convenience_score, safety_score in rows}

def to_score(value, score_type):
    """
    value: original value
    score_type: distance, convenience or safety
    max_value: original value maximum
    """
    if score_type == "distance": # 0 means it's out of 12km from usc
        max_val = 12000 
    elif score_type == "convenience":
        max_val = 30
    elif score_type == "safety":
        max_val = 1

    x = max(0, min(value, max_val))

    if score_type in ("distance", "safety"): #the less the better
        return round(100 * (1 - x / max_val), 2)
    elif score_type == "convenience": #the more the better
        return round(100 * (x / max_val), 2)
    else:
        raise ValueError("score_type must be distance, convenience, or safety")

#Extract, Transform
#listings
def choose_scrap():
    option = 0
    while int(option) not in [1,2]:
        option = input("Use static data or scrap pages(type 1, 2):")
        if int(option) == 1:
            with open(RAW_DIR / "static_listing_data.txt", "r") as f:
                rounds = [f.read()]
            return get_listing(rounds)
        elif int(option) == 2:
            round_number = int(input("Please tell me how many rounds do you want to scrap:"))
            return ss.scrap(round_number)
        else:
            print("Please type again")

def get_scores():
    usc = gpd.read_file(USC_CAMPUS_DIR / "usc_campus.shp")
    grid = gpd.read_file(PROCESSED_DIR / "LA_400m_grid" / "LA_400m_grid.shp")
    grid = grid.to_crs("EPSG:32611").reset_index(drop=True)
    grid["grid_id"] = grid.index + 1
    grid_score_map = get_grid_score_map()
    # print(usc.crs) #EPSF: 4326
    usc_center = usc.to_crs("EPSG:32611")
    usc_center = usc_center.geometry.union_all().centroid
    listings = dbe.query('listing', ['href','latitude','longitude'])
    for href, latitude, longitude in listings:
        if latitude is None or longitude is None:
            dbe.delete('listing', 'href', href)
            continue
        distance_score = to_score(get_distance(usc_center,longitude,latitude),"distance")
        listing_point = gpd.GeoSeries(
            gpd.points_from_xy([longitude], [latitude]),
            crs="EPSG:4326"
        ).to_crs("EPSG:32611").iloc[0]
        matched_grid = grid.loc[grid.geometry.intersects(listing_point), "grid_id"]
        if matched_grid.empty:
            convenience_score, safety_score = 0, 0
        else:
            grid_id = int(matched_grid.iloc[0])
            convenience_score, safety_score = grid_score_map.get(grid_id, (0, 0)) #default to 0 if grid_id not found
        dbe.update('listing', {'distance_score': distance_score, 'convenience_score': convenience_score, 'safety_score': safety_score}, 'href', href)

#for static data
def get_listing(rounds: list):
    listing_list = list()
    usc = gpd.read_file(USC_CAMPUS_DIR / "usc_campus.shp")
    grid = gpd.read_file(PROCESSED_DIR / "LA_400m_grid" / "LA_400m_grid.shp")
    grid = grid.to_crs("EPSG:32611").reset_index(drop=True)
    grid["grid_id"] = grid.index + 1
    grid_score_map = get_grid_score_map()
    # print(usc.crs) #EPSF: 4326
    usc_center = usc.to_crs("EPSG:32611")
    usc_center = usc_center.geometry.union_all().centroid
    for page in rounds:
        soup = BeautifulSoup(page, 'html.parser')
        rents = soup.find_all('li',class_ = 'cl-static-search-result')
        details = soup.find('script', id='ld_searchpage_results') #deatails from json
        if details is None or details.string is None:
            continue
        data = json.loads(details.string)
        item_list = data.get('itemListElement', [])
        for i in range(min(len(rents),len(item_list))):
            rent = rents[i]
            detail = item_list[i].get('item', {})
            href = rent.find('a')['href'].strip()
            price_str = rent.find('div', class_ = 'price').text.strip()
            price = int(price_str.replace("$", "").replace(",", ""))
            location = rent.find('div', class_ = 'location').text.strip()
            title = detail.get('name')
            latitude = detail.get('latitude')
            longitude = detail.get('longitude')
            distance_score = 0
            listing_point = gpd.GeoSeries(
                gpd.points_from_xy([longitude], [latitude]),
                crs="EPSG:4326"
            ).to_crs("EPSG:32611").iloc[0]
            matched_grid = grid.loc[grid.geometry.intersects(listing_point), "grid_id"]
            if matched_grid.empty:
                convenience_score, safety_score = 0, 0
            else:
                grid_id = int(matched_grid.iloc[0])
                convenience_score, safety_score = grid_score_map.get(grid_id, (0, 0)) #default to 0 if grid_id not found

            if not re.fullmatch(r'[1-9]', str(detail.get('numberOfBedrooms'))):
                bedroom = 1
            else:
                bedroom = detail.get('numberOfBedrooms')
            listing_list.append((href,title,price,location,latitude,longitude,distance_score,convenience_score,safety_score,bedroom))
    return listing_list

#safety
def get_safety() -> list[tuple[int, float, float]]:
    data = pd.read_csv(PROCESSED_DIR / "Crime_Data_from_2010_to_2024.csv")
    # print(crime)
    # shape = crime.shape
    # print(shape)
    # head = crime.head()
    # print(head)
    # columns = crime.columns
    # print(columns)

    # unique = crime['DR_NO'].nunique()
    # print(unique) #compare nunique() result and shape() result to confirm data duplication
    data.drop_duplicates(inplace=True) #clean duplicated data
    
    crime = data[['DR_NO','LAT','LON',"DATE OCC","Crm Cd Desc"]]
    # types = crime.dtypes
    # print(types)

    # isnum = crime.isnull().sum()
    # print(isnum)

    crime_list = list(crime.itertuples(index=False,name=None)) #only return simple tuples without indexes and objects
    # print(data.columns.tolist())
    return crime_list

def crime_count() -> list[tuple[int,int]]:
    data = pd.read_csv(PROCESSED_DIR / "Crime_Data_from_2010_to_2024.csv")
    data.drop_duplicates(inplace=True)

    crime_gdf = gpd.GeoDataFrame(
        data,
        geometry=gpd.points_from_xy(data["LON"], data["LAT"]),
        crs="EPSG:4326"
    ) #convert DataFrame into GeoDataFrame, every row is a point
    grid = gpd.read_file(PROCESSED_DIR / "LA_400m_grid" / "LA_400m_grid.shp")
    grid = grid.to_crs("EPSG:32611").reset_index(drop=True) #reset the index and drop the old index since the index might be reordered by reprojection
    grid["grid_id"] = grid.index + 1

    crime_gdf = crime_gdf.to_crs("EPSG:32611")

    joined = gpd.sjoin( #sjoin: connect tables by spatial position
        crime_gdf, #first(in the left) table
        grid[["grid_id","geometry"]], #get grid_id and geometry columns to match the cells, get multiple columns: [[]]
        how = "left", #the left table is the main table, if a point doesn't match any cell, it remains
        predicate = "within" #rule: if the point is inside the cell
    )

    #delete the remain points
    matched = joined.dropna(subset = ["grid_id"]) #drop rows with grid_id is empty
    grouped = matched.groupby("grid_id") #same cell same group
    sized = grouped.size() #group sizes, shows how many points are in each group(cell)
    #after tmp, tmp3 get a series, index is grid_id and value is size
    result = sized.reset_index(name="crime_number") #name the column of value(size), convert series into DataFrame

    crime_list = list(result.itertuples(index=False, name=None)) #convert each row into a tuple without index and names
    return crime_list

#convenience
def get_weight(row):
    #set weights
    weights = {
        ("amenity", "hospital"): 2.5,
        ("amenity", "pharmacy"): 2.0,
        ("amenity", "clinic"): 2.0,
        ("amenity", "laundry"): 1.0,
        ("shop", "supermarket"): 2.5,
        ("shop", "convenience"): 1.5,
        ("public_transport", "station"): 3.0,
        ("public_transport", "stop_position"): 2.0,
        ("highway", "bus_stop"): 2.5,
        ("leisure", "park"): 1,
        ("amenity", "restaurant"): 1.5,
        ("amenity", "cafe"): 1.2,
        ("amenity", "fast_food"): 1.5,
    }
    for col in ["amenity", "shop", "public_transport","highway", "leisure"]:
        if col in row and pd.notna(row[col]):
            return weights.get((col, row[col]), 0.0)
    return 0.0

def get_convenience():
    #Timeout:
    # tags = {
    # "amenity": ["supermarket","pharmacy","hospital","school","bank","cafe","restaurant"],
    # "shop": ["supermarket","convenience"],
    # "public_transport": ["station","stop_position"],
    # "leisure": ["fitness_centre","park"]
    # }
    gdf = gpd.read_file(RAW_DIR / "City_Boundary" / "City_Boundary.shp", engine="fiona")
    boundary = gdf.to_crs(4326).union_all()
    # osm = ox.features_from_polygon(boundary, tags=tags)

    osm1 = ox.features_from_polygon(
        boundary,
        tags={
            "amenity": ["pharmacy","hospital","cafe","restaurant","fast_food"],
        }
    )

    osm2 = ox.features_from_polygon(
        boundary,
        tags={
            "public_transport": ["station","stop_position"],
        }
    )

    osm3 = ox.features_from_polygon(
        boundary,
        tags={
            "highway": ["bus_stop"],
            "amenity": ["clinic", "laundry"]
        }
    )
    osm4 = ox.features_from_polygon(
        boundary,
        tags={
            "shop": ["supermarket","convenience"],
            "leisure": ["park"],
        }
    )

    osm = pd.concat([osm1, osm2, osm3, osm4])
    osm = osm[~osm.index.duplicated(keep="first")]
    #clean data
    osm = osm[osm.geometry.notna()]
    if osm.empty:
        return []
    
    #in osm data the amenities might be point, polygon, multipolygon or other types, we choose to drop others and remain points and centers of polygons
    points = osm[osm.geometry.geom_type == "Point"].copy()
    polys = osm[osm.geometry.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
    if not polys.empty:
        polys = polys.to_crs("EPSG:32611")
        polys["geometry"] = polys.geometry.centroid
        polys = polys.to_crs("EPSG:4326")

    amenities = pd.concat([points, polys], ignore_index=True) #pitch the data vertically
    if amenities.empty:
        return []
    
    amenities["weight"] = amenities.apply(get_weight, axis=1)
    amenities_gdf = gpd.GeoDataFrame(amenities, geometry="geometry", crs="EPSG:4326") 
    amenities_gdf = amenities_gdf.to_crs("EPSG:32611").reset_index(drop=True)
    amenities_gdf["geometry"] = amenities_gdf.buffer(400)

    grid = gpd.read_file(PROCESSED_DIR / "LA_400m_grid" / "LA_400m_grid.shp")
    grid = grid.to_crs("EPSG:32611").reset_index(drop=True) #reset the index and drop the old index since the index might be reordered by reprojection
    grid["grid_id"] = grid.index + 1
    
    joined = gpd.sjoin( #sjoin: connect tables by spatial position
        amenities_gdf, #first(in the left) table
        grid[["grid_id","geometry"]], #get grid_id and geometry columns to match the cells, get multiple columns: [[]]
        how = "left", #the left table is the main table, if a point doesn't match any cell, it remains
        predicate = "intersects" #rule: if the point is inside the cell
    )

    #delete the remain points
    matched = joined.dropna(subset=["grid_id"])
    result = matched.groupby("grid_id")["weight"].sum().reset_index(name="convenience_score")
    convenience_list = list(result.itertuples(index=False, name=None))
    return convenience_list

#distance
def get_distance(usc_center,longitude,latitude):
    listing_point = gpd.GeoSeries(
        gpd.points_from_xy([longitude], [latitude]),
        crs="EPSG:4326"
    ).to_crs("EPSG:32611").iloc[0]
    distance_score = int(listing_point.distance(usc_center))
    return distance_score


if __name__ =="__main__":
    listing_details = choose_scrap()

    listing_col = ['href','title','price','location_text','latitude','longitude','distance_score','convenience_score','safety_score','bedroom_number']
    crime_col = ['crime_id','latitude','longitude','date', 'type']
    grid_col = ['grid_id', 'safety_score', 'convenience_score']
    monthly_crime_col = ['grid_id', 'month_start','crime_count', 'property_crime', 'violence_crime']

    # crime = pd.read_csv("../data/Crime_Data_from_2010_to_2024.csv")
    # print(crime.columns)
    # # Insert crime table
    # dbe.db_truncate('crime')
    # crime_list = get_safety()
    # dbe.db_insert('crime', crime_col, crime_list)

    # # Insert grid table's convenience score column
    # dbe.db_truncate('grid')
    # grid = gpd.read_file("../data/City_Boundary/LA_400m_grid.shp")
    # grid = grid.to_crs("EPSG:32611").reset_index(drop=True)
    # grid["grid_id"] = grid.index + 1
    # convenience_list = get_convenience()
    # con_map = {grid_id: to_score(score,"convenience") for grid_id, score in convenience_list}
    # insert_con = []
    # for grid_id in grid["grid_id"]:
    #     insert = (int(grid_id), 0, con_map.get(int(grid_id), 0))
    #     insert_con.append(insert)
    # dbe.db_insert('grid', grid_col, insert_con)

    # Insert listing table
    # print(len(listing_details))
    # verify = input("Do you want to insert the listing data into database? (type yes or no)")
    # if verify.lower() == "yes":
    #     dbe.db_truncate('listing')
    #     dbe.db_insert('listing', listing_col, listing_details)
    #     ss.scrap_detail()
    get_scores()
    # #Insert monthly crime
    # dbe.db_truncate('monthly_crime')
    # monthly_list = cdp.get_monthly()
    # dbe.db_insert('monthly_crime', monthly_crime_col, monthly_list)

    
