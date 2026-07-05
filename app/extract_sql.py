"""Pull SQL out of a Slack message body."""

from __future__ import annotations

import re

_FENCED = re.compile(r"```(?:sql)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)

_SQL_KEYWORDS = ("SELECT", "WITH", "CREATE", "INSERT", "UPDATE", "DELETE", "MERGE")


def extract_sql_from_text(text: str) -> str | None:
    """Return the best SQL snippet from message text, or None."""
    if not text or not text.strip():
        return None

    blocks = [block.strip() for block in _FENCED.findall(text) if block.strip()]
    if blocks:
        return max(blocks, key=len)

    stripped = text.strip()
    upper = stripped.upper()
    if any(keyword in upper for keyword in _SQL_KEYWORDS):
        return stripped

    return None
