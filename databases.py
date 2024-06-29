"""Database management and query execution module.

This module provides functionality for managing database connections,
executing queries, and handling saved queries.
"""

import json
import psycopg2
import postgres
import sqlite3


# Global variables
DATABASE_PATH = 'server.db'


def initialize_database():
    """
    Initialize the database by creating the necessary tables if they don't exist.
    """
    create_queries_table()
    create_databases_table()


def create_queries_table():
    """
    Create the queries table if it doesn't exist.

    If the table is newly created, it inserts a default query named 'current' with an empty query string.
    """
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS queries (
                name TEXT PRIMARY KEY,
                query TEXT
            )
        """)
        conn.commit()

        # if there are not queries, insert a default one
        cursor.execute("SELECT COUNT(*) FROM queries")
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.execute("INSERT INTO queries (name, query) VALUES ('current', '')")
            conn.commit()


def create_databases_table():
    """Create the databases table if it doesn't exist."""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS databases (
                id TEXT PRIMARY KEY,
                params TEXT
            )
        """)
        conn.commit()


def get_queries():
    """Retrieve all saved queries.

    Returns:
        dict: A dictionary of saved queries.
    """
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, query FROM queries")
            queries = cursor.fetchall()
            return {name: query for name, query in queries}
    except sqlite3.Error as e:
        print(f"Error retrieving queries: {e}")
        return {}


def set_query(query_name: str, query: str):
    """Save a new query or update an existing one.

    Args:
        query_name: The name of the query.
        query: The SQL query string.
    """
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO queries (name, query) VALUES (?, ?)", (query_name, query))
        conn.commit()


def run_query(database_id: str, query: str, sub_query: str | None = None):
    """Execute a SQL query on the specified database.

    Args:
        database_id: The ID of the database to query.
        query: The SQL query to execute.
        sub_query: An optional sub-query to execute first.

    Returns:
        list: Query results as a list of lists, or a dict with an error message.
    """
    if sub_query is None:
        database_params = get_database_params_from_id(database_id)

        try:
            result = postgres.execute_query(database_params, query)
        except psycopg2.Error as e:
            return {'error': str(e)}

        return [list(row) for row in result]

    result = run_query(database_id, sub_query)

    if isinstance(result, dict):
        return result

    headers = result[0]
    table = result[1:]
    new_headers = []
    new_table = []

    for row in table:
        q = query
        for k, v in zip(headers, row):
            key = '{{%s}}' % k
            while key in q:
                q = q.replace(key, f'{v}')

        result = run_query(database_id, q)

        if isinstance(result, dict):
            return result

        new_headers = result[0]
        new_table.extend(result[1:])

    return [new_headers] + new_table


def get_database_params_from_id(database_id: str) -> postgres.DatabaseParameters:
    """Retrieve database parameters for a given database ID.

    Args:
        database_id: The ID of the database.

    Returns:
        postgres.DatabaseParameters: The parameters for the specified database.

    Raises ValueError if the database ID is not found.
    """
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT params FROM databases WHERE id = ?", (database_id,))
        params = cursor.fetchone()
        if params:
            return postgres.DatabaseParameters(**json.loads(params[0]))
        else:
            raise ValueError(f"Database with ID '{database_id}' not found.")


def set_database(database_id: str, database_params: postgres.DatabaseParameters):
    """Add or update a database configuration.

    Args:
        database_id: The ID of the database.
        database_params: The parameters for the database.
    """
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO databases (id, params) VALUES (?, ?)",
                        (database_id, json.dumps(database_params.to_json())))
        conn.commit()


def remove_database(database_id: str):
    """Remove a database configuration.

    Args:
        database_id: The ID of the database to remove.
    """
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM databases WHERE id = ?", (database_id,))
        conn.commit()


def database_exists(database_id: str) -> bool:
    """Check if a database configuration exists.

    Args:
        database_id: The ID of the database to check.

    Returns:
        bool: True if the database exists, False otherwise.
    """
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM databases WHERE id = ?", (database_id, ))
        return cursor.fetchone() is not None


def get_database_ids():
    """Retrieve all configured database IDs.

    Returns:
        list: A list of all database IDs.
    """
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM databases")
        return [row[0] for row in cursor.fetchall()]


