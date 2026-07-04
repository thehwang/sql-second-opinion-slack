<!-- Devpost draft — Slack Agent Builder Challenge -->

# SQL Second Opinion

**Tagline:** Paste SQL in Slack. Get a parser-backed second opinion — not a guess.

**Track:** New Slack Agent (uses Slack slash command + Bolt; sqlucent as deterministic tool)

---

## Elevator pitch

Data teams discuss SQL in Slack every day, but a generic LLM will happily invent
column names. SQL Second Opinion runs `/sql`, takes the query you paste, and
returns walkthrough, lineage, and lint output from the deterministic
[sqlucent](https://pypi.org/project/sqlucent/) engine — every fact grounded in
a real SQL parser, no warehouse credentials required.

---

## What to submit

| Field | Value |
|-------|--------|
| Demo video | _(YouTube link)_ |
| Repo | `https://github.com/thehwang/sql-second-opinion-slack` |
| Sandbox | _(developer sandbox URL — invite slackhack@salesforce.com, testing@devpost.com)_ |
| Architecture diagram | Slack `/sql` → Bolt app → sqlucent CLI → channel reply |

---

## Project story (short)

### Inspiration

Slack is where data engineers paste SQL snippets, ask "can we merge this?", and
debate `SELECT *`. Generic chatbots answer from vibes. We wanted a tool that
only speaks when you paste SQL — and only says what the parser can prove.

### What it does

- `/sql` opens a modal to paste SQL (+ optional schema DDL).
- Runs sqlucent `--walkthrough`, `--lineage`, `--lint`.
- Posts structured results to the channel.

### How we built it

- **Slack Bolt** (Python) for slash command + modal.
- **sqlucent** on PyPI as a subprocess — same engine as
  [SQL X-Ray](https://github.com/thehwang/sql-xray-orbit) on GitLab.
- No database connection; pure text in, deterministic text out.

### Impact

Reduces wrong merge decisions and hallucinated lineage in daily Slack threads.
Any team with SQL in chat can use it; no repo clone required.

---

## Demo script (~3 min)

1. Problem: "LLMs guess SQL; parsers don't."
2. `/sql` → paste `sample/revenue_daily.sql`.
3. Show walkthrough + lineage for `net_revenue`.
4. Paste a query with `SELECT *` → lint flags it.
5. Architecture slide: Slack → Bolt → sqlucent.
