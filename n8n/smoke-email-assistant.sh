#!/usr/bin/env bash
set -euo pipefail

EMAIL_SEARCH_WEBHOOK_URL="${EMAIL_SEARCH_WEBHOOK_URL:-http://192.168.1.81:5678/webhook/email-search}"
EMAIL_READ_WEBHOOK_URL="${EMAIL_READ_WEBHOOK_URL:-http://192.168.1.81:5678/webhook/email-read}"
EMAIL_DRAFT_REPLY_WEBHOOK_URL="${EMAIL_DRAFT_REPLY_WEBHOOK_URL:-http://192.168.1.81:5678/webhook/email-draft-reply}"
MESSAGE_ID="${MESSAGE_ID:-}"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

post_json() {
  local name="$1"
  local url="$2"
  local payload="$3"

  echo
  echo "=== ${name} ==="
  curl -sS --max-time 180 -X POST "$url" \
    -H "Content-Type: application/json" \
    -d "$payload" | jq .
}

require_cmd curl
require_cmd jq

post_json "email-search" "$EMAIL_SEARCH_WEBHOOK_URL" '{
  "query": "newer_than:7d",
  "max_results": 5,
  "unread_only": false,
  "source": "smoke-test"
}'

if [[ -z "$MESSAGE_ID" ]]; then
  echo
  echo "Set MESSAGE_ID=<provider-message-id> to test email-read and email-draft-reply."
  exit 0
fi

post_json "email-read" "$EMAIL_READ_WEBHOOK_URL" "{
  \"message_id\": \"${MESSAGE_ID}\",
  \"include_body\": true,
  \"include_thread\": true,
  \"source\": \"smoke-test\"
}"

post_json "email-draft-reply" "$EMAIL_DRAFT_REPLY_WEBHOOK_URL" "{
  \"message_id\": \"${MESSAGE_ID}\",
  \"reply_instructions\": \"Draft a polite concise reply acknowledging the email and saying I will come back with details. Do not send it.\",
  \"tone\": \"professional\",
  \"create_gmail_draft\": false,
  \"send_email\": false,
  \"source\": \"smoke-test\"
}"

echo
echo "Smoke tests sent. Validate that no email was sent."
