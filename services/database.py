"""
Database connection management.

Provides a connection pool via pyodbc for SQL Server.
The connection string is read from the SQL_CONNECTION_STRING environment
variable — never hardcoded.
"""

import os
import logging
import pyodbc

logger = logging.getLogger(__name__)

def _get_connection_string() -> str:
    """Return the connection string, checking local.settings.json first if available, then env."""
    # Check local.settings.json first to ensure local config changes take immediate effect
    settings_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "local.settings.json",
    )
    if os.path.exists(settings_path):
        try:
            import json
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
                val = settings.get("Values", {}).get("SQL_CONNECTION_STRING")
                if val:
                    return val
        except Exception as exc:
            logger.warning("Could not read local.settings.json: %s", exc)

    conn_str = os.environ.get("SQL_CONNECTION_STRING")
    if not conn_str:
        raise EnvironmentError(
            "SQL_CONNECTION_STRING is not set. "
            "Configure it in local.settings.json or Application Settings."
        )
    return conn_str


def get_connection() -> pyodbc.Connection:
    """
    Create and return a new database connection.

    pyodbc uses ODBC connection pooling by default, so repeatedly
    calling this function is inexpensive.
    """
    try:
        conn = pyodbc.connect(_get_connection_string(), timeout=30)
        conn.autocommit = False
        return conn
    except pyodbc.Error as exc:
        logger.error("Database connection failed: %s", exc)
        raise


def execute_query(query: str, params: tuple = (), *, fetch_one: bool = False):
    """
    Execute a SELECT query and return rows as a list of dicts.

    Args:
        query:     SQL query string with ? placeholders.
        params:    Tuple of parameter values.
        fetch_one: If True, return a single dict or None.

    Returns:
        A list of dicts, or a single dict / None when fetch_one=True.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        if fetch_one:
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    except pyodbc.Error as exc:
        logger.error("Query execution failed: %s | Query: %s", exc, query)
        raise
    finally:
        conn.close()


def execute_command(query: str, params: tuple = ()) -> int:
    """
    Execute an INSERT / UPDATE / DELETE and return the affected row count.

    For INSERT with IDENTITY, use execute_scalar instead.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        affected = cursor.rowcount
        conn.commit()
        return affected
    except pyodbc.Error as exc:
        conn.rollback()
        logger.error("Command execution failed: %s | Query: %s", exc, query)
        raise
    finally:
        conn.close()


def execute_scalar(query: str, params: tuple = ()):
    """
    Execute a query that returns a single scalar value
    (e.g., INSERT … ; SELECT SCOPE_IDENTITY()).
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        conn.commit()
        return row[0] if row else None
    except pyodbc.Error as exc:
        conn.rollback()
        logger.error("Scalar execution failed: %s | Query: %s", exc, query)
        raise
    finally:
        conn.close()
