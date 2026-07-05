"""SQL Second Opinion — Slack app entrypoint."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_sdk.errors import SlackApiError
from flask import Flask, request

from app.analyze import analyze_and_format
from app.extract_sql import extract_sql_from_text
from app.modal import CALLBACK_ID, build_modal, parse_submission

MESSAGE_SHORTCUT_ID = "analyze_sql_message"

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = App(
    token=os.environ["SLACK_BOT_TOKEN"],
    signing_secret=os.environ["SLACK_SIGNING_SECRET"],
)


def post_message(
    client,
    *,
    channel_id: str,
    user_id: str,
    text: str,
    thread_ts: str | None = None,
    **kwargs,
) -> None:
    """Post to channel; fall back to DM if the bot was not invited."""
    payload = {"channel": channel_id, "text": text, **kwargs}
    if thread_ts:
        payload["thread_ts"] = thread_ts
    try:
        client.chat_postMessage(**payload)
        return
    except SlackApiError as exc:
        if exc.response.get("error") != "not_in_channel":
            raise

    dm = client.conversations_open(users=user_id)["channel"]["id"]
    note = (
        "_I’m not in that channel yet — results posted here. "
        "Invite me with `/invite @SQL Second Opinion` to post in-channel._\n\n"
    )
    client.chat_postMessage(channel=dm, text=note + text, **kwargs)


def _handle_sql_ack(ack, body, client) -> None:
    inline_sql = (body.get("text") or "").strip()
    if not inline_sql:
        client.views_open(
            trigger_id=body["trigger_id"],
            view=build_modal(channel_id=body["channel_id"]),
        )
    ack()


def _handle_sql_work(body, client) -> None:
    inline_sql = (body.get("text") or "").strip()
    if not inline_sql:
        return

    channel_id = body["channel_id"]
    user_id = body["user"]["id"]
    thread_ts = body.get("thread_ts")

    post_message(
        client,
        channel_id=channel_id,
        user_id=user_id,
        text=f"<@{user_id}> submitted SQL for analysis — running sqlucent…",
        thread_ts=thread_ts,
    )
    text = analyze_and_format(inline_sql, requested_by=user_id)
    post_message(
        client,
        channel_id=channel_id,
        user_id=user_id,
        text=text,
        thread_ts=thread_ts,
    )


app.command("/sql")(_handle_sql_ack, _handle_sql_work)


def _handle_modal_submit_ack(ack) -> None:
    ack()


def _handle_modal_submit(body, client, view) -> None:
    user_id = body["user"]["id"]
    try:
        sql, dialect, schema, channel_id = parse_submission(view)
    except (KeyError, ValueError, json.JSONDecodeError):
        logger.exception("bad modal payload")
        return

    post_message(
        client,
        channel_id=channel_id,
        user_id=user_id,
        text=f"<@{user_id}> submitted SQL for analysis — running sqlucent…",
    )

    text = analyze_and_format(
        sql, dialect=dialect, schema_ddl=schema, requested_by=user_id
    )

    post_message(
        client,
        channel_id=channel_id,
        user_id=user_id,
        text=text,
        mrkdwn=True,
    )


app.view(CALLBACK_ID)(_handle_modal_submit_ack, _handle_modal_submit)


def _handle_message_shortcut_ack(ack) -> None:
    ack()


def _handle_message_shortcut(shortcut, client) -> None:
    """Analyze SQL from an existing message (right-click → Shortcuts)."""
    user_id = shortcut["user"]["id"]
    message = shortcut["message"]
    channel_id = shortcut["channel"]["id"]
    thread_ts = message.get("thread_ts") or message["ts"]

    sql = extract_sql_from_text(message.get("text", ""))
    if not sql:
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text=(
                "No SQL found in that message. Use a ```sql … ``` code block, "
                "or run `/sql` to paste manually."
            ),
        )
        return

    post_message(
        client,
        channel_id=channel_id,
        user_id=user_id,
        text=f"<@{user_id}> asked for a second opinion on this SQL — running sqlucent…",
        thread_ts=thread_ts,
    )

    text = analyze_and_format(sql, requested_by=user_id)
    post_message(
        client,
        channel_id=channel_id,
        user_id=user_id,
        text=text,
        thread_ts=thread_ts,
    )


app.shortcut(MESSAGE_SHORTCUT_ID)(_handle_message_shortcut_ack, _handle_message_shortcut)


def create_flask_app() -> Flask:
    flask_app = Flask(__name__)
    handler = SlackRequestHandler(app)

    @flask_app.route("/slack/events", methods=["POST"])
    def slack_events():
        logger.info("POST /slack/events")
        return handler.handle(request)

    @flask_app.route("/health", methods=["GET"])
    def health():
        return {"ok": True}

    return flask_app


def main() -> None:
    app_token = os.environ.get("SLACK_APP_TOKEN")
    if app_token:
        logger.info(
            "Starting Socket Mode (disable Socket Mode in Slack if using HTTP URLs on Render)"
        )
        SocketModeHandler(app, app_token).start()
        return

    port = int(os.environ.get("PORT", "3000"))
    flask_app = create_flask_app()
    logger.info(
        "Starting HTTP server on port %s — Slack Request URL must be "
        "https://<host>/slack/events and Socket Mode must be OFF",
        port,
    )
    flask_app.run(host="0.0.0.0", port=port, threaded=True)


if __name__ == "__main__":
    main()
