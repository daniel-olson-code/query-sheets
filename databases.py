"""Database management and query execution module.

This module provides functionality for managing database connections,
executing queries, and handling saved queries.
"""

import json
import os
import psycopg2
import postgres

# Global variables
selected_database: str | None = None
databases = {}
DATABASE_PATH = 'databases.json'

saved_queries = {'current': ''}
SAVED_QUERIES_PATH = 'saved_queries.json'


def load_saved_queries():
    """Load saved queries from a JSON file."""
    global saved_queries
    if os.path.exists(SAVED_QUERIES_PATH):
        with open(SAVED_QUERIES_PATH, 'r') as f:
            saved_queries = json.load(f)


def save_saved_queries():
    """Save queries to a JSON file."""
    global saved_queries
    with open(SAVED_QUERIES_PATH, 'w') as f:
        json.dump(saved_queries, f, indent=4)


def get_queries():
    """Retrieve all saved queries.

    Returns:
        dict: A dictionary of saved queries.
    """
    global saved_queries
    return saved_queries


def set_query(query_name: str, query: str):
    """Save a new query or update an existing one.

    Args:
        query_name: The name of the query.
        query: The SQL query string.
    """
    global saved_queries
    saved_queries[query_name] = query
    save_saved_queries()


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
    """
    global databases
    return postgres.DatabaseParameters(**databases[database_id])


def load_databases():
    """Load database configurations from a JSON file."""
    global databases
    if os.path.exists(DATABASE_PATH):
        with open(DATABASE_PATH, 'r') as f:
            databases = json.load(f)


def save_databases():
    """Save database configurations to a JSON file."""
    global databases
    with open(DATABASE_PATH, 'w') as f:
        json.dump(databases, f, indent=4)


def set_database(database_id: str, database_params: postgres.DatabaseParameters):
    """Add or update a database configuration.

    Args:
        database_id: The ID of the database.
        database_params: The parameters for the database.
    """
    global databases
    databases[database_id] = database_params.to_json()
    save_databases()


def remove_database(database_id: str):
    """Remove a database configuration.

    Args:
        database_id: The ID of the database to remove.
    """
    global databases
    del databases[database_id]
    save_databases()


def database_exists(database_id: str) -> bool:
    """Check if a database configuration exists.

    Args:
        database_id: The ID of the database to check.

    Returns:
        bool: True if the database exists, False otherwise.
    """
    global databases
    return database_id in databases


def get_database_ids():
    """Retrieve all configured database IDs.

    Returns:
        list: A list of all database IDs.
    """
    global databases
    return list(databases.keys())

# import json
# import os
# import psycopg2
# import postgres
#
#
# selected_database: str | None = None
# databases = {}
# DATABASE_PATH = 'databases.json'
#
#
# saved_queries = {'current': ''}
# SAVED_QUERIES_PATH = 'saved_queries.json'
#
#
# def load_saved_queries():
#     global saved_queries
#     if os.path.exists(SAVED_QUERIES_PATH):
#         with open(SAVED_QUERIES_PATH, 'r') as f:
#             saved_queries = json.load(f)
#
#
# def save_saved_queries():
#     global saved_queries
#     with open(SAVED_QUERIES_PATH, 'w') as f:
#         json.dump(saved_queries, f, indent=4)
#
#
# def get_queries():
#     global saved_queries
#     return saved_queries
#
#
# def set_query(query_name: str, query: str):
#     global saved_queries
#     saved_queries[query_name] = query
#     save_saved_queries()
#
#
# def run_query(database_id: str, query: str, sub_query: str | None = None):
#     if sub_query is None:
#         database_params = get_database_params_from_id(database_id)
#
#         try:
#             result = postgres.execute_query(database_params, query)
#         except psycopg2.Error as e:
#             return {'error': str(e)}
#
#         return [list(row) for row in result]
#
#     result = run_query(database_id, sub_query)
#
#     if isinstance(result, dict):
#         return result
#
#     headers = result[0]
#     table = result[1:]
#     new_headers = []
#     new_table = []
#
#     for row in table:
#         q = query
#         for k, v in zip(headers, row):
#             key = '{{%s}}' % k
#             while key in q:
#                 q = q.replace(key, f'{v}')
#
#         result = run_query(database_id, q)
#
#         if isinstance(result, dict):
#             return result
#
#         new_headers = result[0]
#         new_table.extend(result[1:])
#
#     return [new_headers] + new_table
#
#
# def get_database_params_from_id(database_id: str) -> postgres.DatabaseParameters:
#     global databases
#     return postgres.DatabaseParameters(**databases[database_id])
#
#
# def load_databases():
#     global databases
#     if os.path.exists(DATABASE_PATH):
#         with open(DATABASE_PATH, 'r') as f:
#             databases = json.load(f)
#
#
# def save_databases():
#     global databases
#     with open(DATABASE_PATH, 'w') as f:
#         json.dump(databases, f, indent=4)
#
#
# def set_database(database_id: str, database_params: postgres.DatabaseParameters):
#     global databases
#     databases[database_id] = database_params.to_json()
#     save_databases()
#
#
# def remove_database(database_id: str):
#     global databases
#     del databases[database_id]
#     save_databases()
#
#
# def database_exists(database_id: str) -> bool:
#     global databases
#     return database_id in databases
#
#
# def get_database_ids():
#     global databases
#     return list(databases.keys())
#
#
#
#
#
#
#
