"""Shared analyze + reply helpers."""

from __future__ import annotations

from app.format_reply import format_error, format_success
from app.runner import SqlucentError, analyze_sql


def analyze_and_format(
    sql: str,
    *,
    dialect: str = "bigquery",
    schema_ddl: str | None = None,
    requested_by: str,
) -> str:
    try:
        result = analyze_sql(sql, dialect=dialect, schema_ddl=schema_ddl)
        return format_success(result, requested_by=requested_by)
    except SqlucentError as exc:
        return format_error(exc)
