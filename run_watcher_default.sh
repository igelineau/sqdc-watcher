#!/bin/sh

SLACK_URL=
TOKEN=
PORT=19019
INTERVAL=20
export SLACK_SIGNING_SECRET=

pipenv run python main.py --watch --slack-post-url "$SLACK_URL" --slack-oauth-token "$TOKEN" --watch-interval "$INTERVAL" --slack-port "$PORT"
