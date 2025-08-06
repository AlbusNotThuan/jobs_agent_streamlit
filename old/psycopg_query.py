import os
import psycopg
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

DB_CONNECTION = os.getenv('DB_CONNECTION')

if not DB_CONNECTION:
    raise ValueError('Biến môi trường DB_CONNECTION chưa được thiết lập.')

def query_database(query: str, params: Optional[list[str]] = None) -> list:
    """
    Executes a SQL query on a PostgreSQL database using psycopg and returns the results.

    Args:
        query (str): The SQL query string to execute.
        params (list[str], optional): List of string parameters to pass with the query. Defaults to None.

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
                return cur.fetchall()
            return None

if __name__ == "__main__":
    # Ví dụ truy vấn: Liệt kê các bảng trong schema 'public' của PostgreSQL
    sql = """
    SELECT tablename FROM pg_tables WHERE schemaname = 'public';

    """
    result = query_database(sql)
    print("Kết quả truy vấn:", result)
