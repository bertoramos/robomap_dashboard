
import sqlite3
import pandas as pd

def load_db(db_file):
    """Load the database and return the tables in dataframe format."""
    # Mostrar las tablas disponibles
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables_names = cursor.fetchall()
        
        tables = {}
        for table_name in tables_names:
            table_name = table_name[0]
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            tables[table_name] = df
    return tables
