"""SQL Second Opinion — Slack app entrypoint."""

from __future__ import annotations

import json
import logging
import os

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request

from app.format_reply import format_error, format_success
from app.modal import CALLBACK_ID, build_modal, parse_submission
from app.runner import SqlucentError, analyze_sql

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = App(
    token=os.environ["SLACK_BOT_TOKEN"],
    signing_secret=os.environ["SLACK_SIGNING_SECRET"],
)


@app.command("/sql")
def handle_sql_command(ack, body, client):
    ack()
    channel_id = body["channel_id"]
    client.views_open(
        trigger_id=body["trigger_id"],
        view=build_modal(channel_id=channel_id),
    )


@app.view(CALLBACK_ID)
def handle_modal_submit(ack, body, client, view):
    ack()
    user_id = body["user"]["id"]
    try:
        sql, dialect, schema, channel_id = parse_submission(view)
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        logger.exception("bad modal payload")
        return

    client.chat_postMessage(
        channel=channel_id,
        text=f"<@{user_id}> submitted SQL for analysis — running sqlucent…",
    )

    try:
        result = analyze_sql(sql, dialect=dialect, schema_ddl=schema)
        text = format_success(result, requested_by=user_id)
    except SqlucentError as exc:
        text = format_error(exc)

    client.chat_postMessage(channel=channel_id, text=text, mrkdwn=True)


def create_flask_app() -> Flask:
    flask_app = Flask(__name__)
    handler = SlackRequestHandler(app)

    @flask_app.route("/slack/events", methods=["POST"])
    def slack_events():
        return handler.handle(request)

    @flask_app.route("/health", methods=["GET"])
    def health():
        return {"ok": True}

    return flask_app


def main() -> None:
    app_token = os.environ.get("SLACK_APP_TOKEN")
    if app_token:
        logger.info("Starting Socket Mode handler")
        SocketModeHandler(app, app_token).start()
        return

    port = int(os.environ.get("PORT", "3000"))
    flask_app = create_flask_app()
    logger.info("Starting HTTP server on port %s", port)
    flask_app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
