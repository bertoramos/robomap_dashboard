
import sqlite3
import pandas as pd

def load_db(db_source):
    """Load a SQLite database from a file path or raw bytes into dataframes."""
    if isinstance(db_source, (bytes, bytearray, memoryview)):
        with sqlite3.connect(":memory:") as conn:
            conn.deserialize(bytes(db_source))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables_names = cursor.fetchall()

            tables = {}
            for table_name in tables_names:
                table_name = table_name[0]
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                tables[table_name] = df
            return tables

    with sqlite3.connect(db_source) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables_names = cursor.fetchall()

        tables = {}
        for table_name in tables_names:
            table_name = table_name[0]
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            tables[table_name] = df
    return tables
