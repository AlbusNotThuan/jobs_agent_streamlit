import os
import psycopg
from typing import Optional
from dotenv import load_dotenv
import json
from datetime import datetime, date

load_dotenv()

DB_CONNECTION = os.getenv('DB_CONNECTION')

if not DB_CONNECTION:
    raise ValueError('Biến môi trường DB_CONNECTION chưa được thiết lập.')

def query_database(query: str, params: Optional[list[str]] = None) -> list:
    """
    Executes a SQL query on a PostgreSQL database using psycopg and returns the results.

    Args:
        query (str): The SQL query string to execute.
        params (Optional[list[str]]): List of string parameters to pass with the query. Defaults to None.

    Returns:
        list: A list of rows (each row is a tuple) returned by the query, or None if no results.
    """

    print(f"Executing query: {query}")
    if params:
        print(f"With parameters: {params}")
    with psycopg.connect(DB_CONNECTION) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            if cur.description:
                results = cur.fetchall()
                # Convert datetime objects to strings for JSON serialization
                converted_results = []
                for row in results:
                    converted_row = []
                    for item in row:
                        if isinstance(item, (datetime, date)):
                            converted_row.append(item.isoformat())
                        else:
                            converted_row.append(item)
                    converted_results.append(tuple(converted_row))
                return converted_results
            return None

if __name__ == "__main__":
    """
    Example usage: List all tables in the 'public' schema of PostgreSQL.

    Args:
        None

    Returns:
        None
    """
    sql = """
    SELECT tablename FROM pg_tables WHERE schemaname = 'public';
    """
    result = query_database(sql)
    print("Kết quả truy vấn:", result)
