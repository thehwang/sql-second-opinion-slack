"""Build the /sql modal and read submitted values."""

from __future__ import annotations

import json
from typing import Any

CALLBACK_ID = "sql_second_opinion_modal"

DIALECTS = (
    ("bigquery", "BigQuery"),
    ("snowflake", "Snowflake"),
    ("postgres", "PostgreSQL"),
    ("duckdb", "DuckDB"),
    ("spark", "Spark"),
)


def build_modal(*, channel_id: str) -> dict[str, Any]:
    return {
        "type": "modal",
        "callback_id": CALLBACK_ID,
        "private_metadata": json.dumps({"channel_id": channel_id}),
        "title": {"type": "plain_text", "text": "SQL Second Opinion"},
        "submit": {"type": "plain_text", "text": "Analyze"},
        "close": {"type": "plain_text", "text": "Cancel"},
        "blocks": [
            {
                "type": "input",
                "block_id": "sql_block",
                "label": {"type": "plain_text", "text": "SQL"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "sql_input",
                    "multiline": True,
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Paste a query or CREATE TABLE AS SELECT …",
                    },
                },
            },
            {
                "type": "input",
                "block_id": "dialect_block",
                "label": {"type": "plain_text", "text": "SQL dialect"},
                "element": {
                    "type": "static_select",
                    "action_id": "dialect_select",
                    "initial_option": {
                        "text": {"type": "plain_text", "text": "BigQuery"},
                        "value": "bigquery",
                    },
                    "options": [
                        {
                            "text": {"type": "plain_text", "text": label},
                            "value": value,
                        }
                        for value, label in DIALECTS
                    ],
                },
            },
            {
                "type": "input",
                "block_id": "schema_block",
                "optional": True,
                "label": {
                    "type": "plain_text",
                    "text": "Schema DDL (optional, for SELECT *)",
                },
                "element": {
                    "type": "plain_text_input",
                    "action_id": "schema_input",
                    "multiline": True,
                    "placeholder": {
                        "type": "plain_text",
                        "text": "CREATE TABLE raw.orders (id INT, …);",
                    },
                },
            },
        ],
    }


def parse_submission(view: dict[str, Any]) -> tuple[str, str, str | None, str]:
    """Return sql, dialect, optional schema DDL, channel_id."""
    values = view["state"]["values"]
    sql = values["sql_block"]["sql_input"]["value"].strip()
    dialect = values["dialect_block"]["dialect_select"]["selected_option"]["value"]
    schema_raw = values["schema_block"]["schema_input"].get("value")
    schema = schema_raw.strip() if schema_raw else None
    meta = json.loads(view["private_metadata"])
    channel_id = meta["channel_id"]
    return sql, dialect, schema, channel_id
