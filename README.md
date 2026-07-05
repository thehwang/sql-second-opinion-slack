# SQL Second Opinion for Slack

Paste SQL in Slack, get a **parser-backed second opinion** — walkthrough,
column lineage, and lint risks — powered by
[sqlucent](https://pypi.org/project/sqlucent/). No warehouse connection, no
hallucinated table names.

Built for the [Slack Agent Builder Challenge](https://slackhack.devpost.com/).

## How it works

Two ways to analyze SQL:

1. **`/sql`** — paste SQL two ways:
   - **Inline:** `/sql SELECT 1` (one line; good for quick probes)
   - **Modal:** `/sql` alone → form opens for multi-line SQL, dialect, optional schema
2. **Message shortcut** — someone posted SQL in a code block; hover that message →
   **More actions** → **Analyze SQL in message**. Results reply in the thread.

```
You:  /sql  →  [modal: paste SQL]
Colleague: posts ```sql … ``` in channel
You:  right-click message → Analyze SQL in message
Bot:  Walkthrough · Lineage · Risks (reply in thread)
```

## Quick start (local)

### 1. Slack app

Create an app at [api.slack.com/apps](https://api.slack.com/apps):

| Setting | Value |
|---------|--------|
| **Slash command** | `/sql` → Request URL `https://<your-host>/slack/events` |
| **Interactivity** | same URL |
| **Message shortcut** | **Analyze SQL in message** → Callback ID `analyze_sql_message` |
| **Bot scopes** | `commands`, `chat:write`, `chat:write.public`, `im:write` |
| **Install** | to your dev workspace |

For local dev, expose port 3000 with [ngrok](https://ngrok.com/) and use the
HTTPS URL.

**Socket Mode (optional):** set `SLACK_APP_TOKEN=xapp-…` and skip ngrok; Bolt
will use WebSocket instead of HTTP.

### 2. Python

```bash
cd sql-second-opinion-slack
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET
python -m app.main
```

### 3. Try it

```
/sql
```

Paste `sample/revenue_daily.sql`, submit, and check the channel reply.

## Project layout

```
app/
  main.py          # Bolt app (/sql + modal submit)
  modal.py         # Modal JSON
  runner.py        # sqlucent subprocess wrapper
  format_reply.py  # Slack message formatting
sample/            # Demo SQL
```

## Hackathon checklist

- [ ] Developer sandbox URL in Devpost
- [ ] Invite `slackhack@salesforce.com` and `testing@devpost.com`
- [ ] ~3 min demo video (`/sql` → walkthrough + lint flag)
- [ ] Architecture diagram (Slack → Bolt → sqlucent CLI)
- [ ] Deploy app host with `sqlucent` on PATH (Railway, Fly.io, etc.)

## Related projects

- **sqlucent engine:** [github.com/thehwang/sql-x-ray](https://github.com/thehwang/sql-x-ray)
- **GitLab SQL X-Ray agent:** separate repo (`sql-xray-orbit`)

## License

MIT
