"""Format sqlucent output for Slack mrkdwn."""

from __future__ import annotations

from app.runner import AnalysisResult, SqlucentError

# Slack posts truncate around 40k; keep a safe margin for demo channels.
MAX_SECTION = 2_800
MAX_TOTAL = 12_000


def _clip(text: str, limit: int) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 20].rstrip() + "\n… _(truncated)_"


def _section(title: str, body: str) -> str:
    clipped = _clip(body, MAX_SECTION)
    return f"*{title}*\n```{clipped}```"


def format_success(result: AnalysisResult, *, requested_by: str) -> str:
    parts = [
        f"*SQL Second Opinion* — parser-backed analysis (`{result.dialect}`)",
        f"_Requested by <@{requested_by}> · powered by_ <https://pypi.org/project/sqlucent/|sqlucent>",
        _section("Walkthrough", result.walkthrough),
        _section("Lineage", result.lineage),
        _section("Risks (lint)", result.lint),
        "_Every table/column name above comes from sqlucent output, not from model guessing._",
    ]
    message = "\n\n".join(parts)
    if len(message) > MAX_TOTAL:
        message = message[: MAX_TOTAL - 30] + "\n… _(message truncated)_"
    return message


def format_error(exc: SqlucentError) -> str:
    return (
        "*SQL Second Opinion* could not analyze that SQL.\n"
        f"```{_clip(str(exc), 500)}```\n"
        "Check dialect, syntax, or install sqlucent on the app host."
    )
