"""MCP server exposing sqlucent as explain_sql (stdio transport)."""

from __future__ import annotations

import asyncio
import json

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from app.modal import DIALECTS
from app.runner import SqlucentError, analyze_sql

server = Server("sql-second-opinion")

_DIALECT_VALUES = [value for value, _ in DIALECTS]


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="explain_sql",
            description=(
                "Deterministic SQL analysis via sqlucent: step-by-step walkthrough, "
                "column-level lineage, and lint risks. No warehouse connection; "
                "facts come from the parser, not an LLM guess."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SQL query or script to analyze.",
                    },
                    "dialect": {
                        "type": "string",
                        "description": "SQL dialect for parsing.",
                        "enum": _DIALECT_VALUES,
                        "default": "bigquery",
                    },
                    "schema_ddl": {
                        "type": "string",
                        "description": (
                            "Optional CREATE TABLE DDL so SELECT * expands to real columns."
                        ),
                    },
                },
                "required": ["sql"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(
    name: str, arguments: dict
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    if name != "explain_sql":
        raise ValueError(f"Unknown tool: {name}")

    sql = str(arguments.get("sql", ""))
    dialect = str(arguments.get("dialect") or "bigquery")
    schema_ddl = arguments.get("schema_ddl")
    schema = str(schema_ddl).strip() if schema_ddl else None

    try:
        result = analyze_sql(sql, dialect=dialect, schema_ddl=schema)
        payload = result.as_dict()
    except SqlucentError as exc:
        payload = {"error": str(exc)}

    return [types.TextContent(type="text", text=json.dumps(payload, indent=2))]


async def run_server() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main() -> None:
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
