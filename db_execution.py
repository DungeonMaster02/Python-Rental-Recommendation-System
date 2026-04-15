import connection
import data_processing as dp

def db_insert(tbname, columns, values):
    if not values:
        return

    conn = connection.get_connect()
    cur = conn.cursor()
    col_str = ", ".join(columns) #pitch iterable variables into a long string seperated by ', '
    placeholders = ", ".join(["%s"] * len(columns)) #for safety
    sql = f"INSERT INTO {tbname}({col_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING" #python sends long strings to sql, sql uses ',' in text to seperate different variables
    cur.executemany(sql, values) #insert multiple rows

    conn.commit()
    cur.close()
    conn.close()

def db_truncate(tbname):
    conn = connection.get_connect()
    cur = conn.cursor()
    cur.execute(f"TRUNCATE TABLE {tbname} RESTART IDENTITY CASCADE")
    conn.commit()
    cur.close()
    conn.close()

def db_update(tbname, updates, where_col, where_val):
    """
    updates: dict{update_col: update_val}
    where_col: positioning Field
    where_val: positioning value
    """
    conn = connection.get_connect()
    cur = conn.cursor()
    set_str = ", ".join([f"{k}=%s" for k in updates.keys()])
    sql = f"UPDATE {tbname} SET {set_str} WHERE {where_col}=%s"
    cur.execute(sql, list(updates.values()) + [where_val])
    conn.commit()
    cur.close()
    conn.close()

if __name__=="__main__":
    listing_col = ['listing_id','href','title','price','location_text','latitude','longitude','is_active','distance_score','convenience_score','safety_score']
    crime_col = ['crime_id','latitude','longitude']

    crime_list = dp.get_safety()
    db_insert('crime', crime_col, crime_list)