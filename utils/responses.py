"""
HTTP response helpers.

Centralises JSON serialisation and standard error responses so that
every function returns a consistent envelope.
"""

import json
import datetime
from decimal import Decimal
from typing import Any

import azure.functions as func


class _CustomEncoder(json.JSONEncoder):
    """Handle Decimal, date, and datetime serialisation."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, Decimal):
            # Preserve two-decimal precision for monetary values
            return float(obj)
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return super().default(obj)


def ok(body: Any, status_code: int = 200) -> func.HttpResponse:
    """Return a 2xx JSON response."""
    return func.HttpResponse(
        body=json.dumps(body, cls=_CustomEncoder),
        status_code=status_code,
        mimetype="application/json",
    )


def created(body: Any) -> func.HttpResponse:
    """201 Created."""
    return ok(body, status_code=201)


def no_content() -> func.HttpResponse:
    """204 No Content (e.g., after DELETE)."""
    return func.HttpResponse(status_code=204)


def bad_request(message: str) -> func.HttpResponse:
    """400 Bad Request."""
    return func.HttpResponse(
        body=json.dumps({"error": message}),
        status_code=400,
        mimetype="application/json",
    )


def not_found(message: str = "Resource not found") -> func.HttpResponse:
    """404 Not Found."""
    return func.HttpResponse(
        body=json.dumps({"error": message}),
        status_code=404,
        mimetype="application/json",
    )


def conflict(message: str) -> func.HttpResponse:
    """409 Conflict (e.g., FK violation)."""
    return func.HttpResponse(
        body=json.dumps({"error": message}),
        status_code=409,
        mimetype="application/json",
    )


def internal_error(message: str = "Internal server error") -> func.HttpResponse:
    """500 Internal Server Error."""
    return func.HttpResponse(
        body=json.dumps({"error": message}),
        status_code=500,
        mimetype="application/json",
    )
