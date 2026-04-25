import connection

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

def update(tbname, updates, where_col, where_val):
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

def query(tbname, columns, where_col=None, where_val=None):
    conn = connection.get_connect()
    cur = conn.cursor()
    col_str = ", ".join(columns)
    sql = f"SELECT {col_str} FROM {tbname}"
    if where_col and where_val:
        sql += f" WHERE {where_col}=%s"
        cur.execute(sql, (where_val,))
    else:
        cur.execute(sql)
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results

def delete(tbname, where_col, where_val):
    conn = connection.get_connect()
    cur = conn.cursor()
    sql = f"DELETE FROM {tbname} WHERE {where_col}=%s"
    cur.execute(sql, (where_val,))
    conn.commit()
    cur.close()
    conn.close()

if __name__=="__main__":
    pass