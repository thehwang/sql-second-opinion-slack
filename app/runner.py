"""Run sqlucent as a subprocess — deterministic, no LLM."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AnalysisResult:
    walkthrough: str
    lineage: str
    lint: str
    dialect: str

    def as_dict(self) -> dict[str, str]:
        return {
            "dialect": self.dialect,
            "walkthrough": self.walkthrough,
            "lineage": self.lineage,
            "lint": self.lint,
        }


class SqlucentError(Exception):
    """sqlucent failed or is not installed."""


def _ensure_sqlucent() -> str:
    path = shutil.which("sqlucent")
    if path is None:
        raise SqlucentError(
            "sqlucent is not on PATH. Install with: `pip install sqlucent`"
        )
    return path


def _run(
    executable: str,
    sql_path: Path,
    dialect: str,
    extra_args: list[str],
    schema_path: Path | None,
) -> str:
    cmd = [executable, str(sql_path), "--dialect", dialect, *extra_args]
    if schema_path is not None:
        cmd.extend(["--schema", str(schema_path)])

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "unknown error").strip()
        raise SqlucentError(detail)
    return proc.stdout.strip()


def analyze_sql(
    sql: str,
    *,
    dialect: str = "bigquery",
    schema_ddl: str | None = None,
) -> AnalysisResult:
    if not sql.strip():
        raise SqlucentError("SQL is empty.")

    executable = _ensure_sqlucent()

    with tempfile.TemporaryDirectory(prefix="sso-") as tmp:
        tmp_path = Path(tmp)
        sql_path = tmp_path / "query.sql"
        sql_path.write_text(sql, encoding="utf-8")

        schema_path: Path | None = None
        if schema_ddl:
            schema_path = tmp_path / "schema.sql"
            schema_path.write_text(schema_ddl, encoding="utf-8")

        walkthrough = _run(
            executable, sql_path, dialect, ["--walkthrough"], schema_path
        )
        lineage = _run(executable, sql_path, dialect, ["--lineage"], schema_path)
        lint = _run(executable, sql_path, dialect, ["--lint"], schema_path)

    return AnalysisResult(
        walkthrough=walkthrough,
        lineage=lineage,
        lint=lint,
        dialect=dialect,
    )
