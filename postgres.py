"""PostgreSQL database interaction module.

This module provides classes and functions for managing PostgreSQL database
connections and executing queries.
"""

import psycopg2
import json


class DatabaseParameters:
    """A class to handle PostgreSQL database connection parameters.

    Attributes:
        host (str): The database server host.
        database (str): The name of the database.
        user (str): The username for database connection.
        password (str): The password for database connection.
        port (str): The port number for database connection.
    """

    def __init__(
            self,
            host: str,
            database: str,
            user: str,
            password: str,
            port: str = '5432',
    ) -> None:
        """Initialize DatabaseParameters with connection details.

        Args:
            host: The database server host.
            database: The name of the database.
            user: The username for database connection.
            password: The password for database connection.
            port: The port number for database connection. Defaults to '5432'.
        """
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.port = port

    def to_json(self) -> dict:
        """Convert the database parameters to a JSON-serializable dictionary.

        Returns:
            dict: A dictionary representation of the database parameters.
        """
        return {
            'host': self.host,
            'database': self.database,
            'user': self.user,
            'password': self.password,
            'port': self.port,
        }

    def from_json(self, json_data: dict) -> None:
        """Load database parameters from a JSON-serializable dictionary.

        Args:
            json_data: A dictionary containing database parameters.
        """
        self.host = json_data['host']
        self.database = json_data['database']
        self.user = json_data['user']
        self.password = json_data['password']
        self.port = json_data['port']

    def save(self, path: str) -> None:
        """Save the database parameters to a JSON file.

        Args:
            path: The file path to save the JSON data.
        """
        with open(path, 'w') as f:
            json.dump(self.to_json(), f, indent=4)

    def load(self, path: str) -> None:
        """Load database parameters from a JSON file.

        Args:
            path: The file path to load the JSON data from.
        """
        with open(path, 'r') as f:
            self.from_json(json.load(f))


def check_connection(db_params: DatabaseParameters) -> bool:
    """Check if a connection can be established with the given database parameters.

    Args:
        db_params: DatabaseParameters object containing connection details.

    Returns:
        bool: True if connection is successful, False otherwise.
    """
    try:
        with psycopg2.connect(
            host=db_params.host,
            database=db_params.database,
            user=db_params.user,
            password=db_params.password,
            port=db_params.port
        ) as _:
            return True
    except (Exception, psycopg2.Error) as error:
        print("Error connecting to PostgreSQL database:", error)
        return False


def execute_query(db_params: DatabaseParameters, query: str) -> list[tuple]:
    """Execute a SQL query on a PostgreSQL database and return the result.

    Args:
        db_params: DatabaseParameters object containing connection details.
        query: SQL query to execute.

    Returns:
        list[tuple]: Query result as a list of tuples. The first tuple contains
                     column names, and subsequent tuples contain row data.

    Raises:
        psycopg2.Error: If there is an error executing the SQL query.
    """
    with psycopg2.connect(
        host=db_params.host,
        database=db_params.database,
        user=db_params.user,
        password=db_params.password,
        port=db_params.port
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            conn.commit()
            headers = tuple(col[0] for col in cur.description)
            return [headers] + cur.fetchall()



# import psycopg2
# import json
#
#
# class DatabaseParameters:
#     def __init__(
#             self,
#             host: str,
#             database: str,
#             user: str,
#             password: str,
#             port: str = '5432',
#     ) -> None:
#         self.host = host
#         self.database = database
#         self.user = user
#         self.password = password
#         self.port = port
#
#     def to_json(self):
#         return {
#             'host': self.host,
#             'database': self.database,
#             'user': self.user,
#             'password': self.password,
#             'port': self.port,
#         }
#
#     def from_json(self, json_data):
#         self.host = json_data['host']
#         self.database = json_data['database']
#         self.user = json_data['user']
#         self.password = json_data['password']
#         self.port = json_data['port']
#
#     def save(self, path: str):
#         with open(path, 'w') as f:
#             json.dump(self.to_json(), f, indent=4)
#
#     def load(self, path: str):
#         with open(path, 'r') as f:
#             self.from_json(json.load(f))
#
#
# def check_connection(
#         db_params: DatabaseParameters
# ):
#     try:
#         with psycopg2.connect(
#             host=db_params.host,
#             database=db_params.database,
#             user=db_params.user,
#             password=db_params.password,
#             port=db_params.port
#         ) as _:
#             return True
#     except (Exception, psycopg2.Error) as error:
#         print("Error connecting to PostgreSQL database:", error)
#         return False
#
#
# def execute_query(db_params: DatabaseParameters, query: str) -> list[tuple]:
#     """
#     Execute a SQL query on a PostgreSQL database
#     and return the result as a list of tuples.
#
#     Args:
#         db_params (DatabaseParameters): Database connection parameters.
#         query (str): SQL query to execute.
#
#     Returns:
#         list[tuple]: Query result as a list of tuples.
#
#     Raises:
#         psycopg2.Error: If there is an error executing the SQL query.
#     """
#     with psycopg2.connect(
#         host=db_params.host,
#         database=db_params.database,
#         user=db_params.user,
#         password=db_params.password,
#         port=db_params.port
#     ) as conn:
#         with conn.cursor() as cur:
#             cur.execute(query)
#             conn.commit()
#             headers = tuple(col[0] for col in cur.description)
#             return [headers] + cur.fetchall()
#
