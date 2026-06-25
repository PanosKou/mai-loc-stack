#!/usr/bin/env bash
set -euo pipefail

WEBHOOK_URL="${WEBHOOK_URL:-http://192.168.1.81:5678/webhook/personal-assistant-task}"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

post_case() {
  local name="$1"
  local payload="$2"

  echo
  echo "=== ${name} ==="
  curl -sS --max-time 180 -X POST "$WEBHOOK_URL" \
    -H "Content-Type: application/json" \
    -d "$payload" | jq .
}

require_cmd curl
require_cmd jq

echo "Using webhook: ${WEBHOOK_URL}"

post_case "general_assistant" '{
  "task": "Summarise this note into action items: Call Maria about the invoice, prepare tomorrow meeting notes, and draft a polite follow-up email to the supplier.",
  "profile_name": "general_assistant",
  "source": "smoke-test"
}'

post_case "hospitality_assistant" '{
  "task": "Create a pre-arrival welcome message for guests arriving tomorrow at Villa Elia. Include check-in details, house rules, nearby restaurants, transport tips, and a note that the cleaner should prepare extra towels. Do not send it yet.",
  "profile_name": "hospitality_assistant",
  "source": "smoke-test"
}'

post_case "mode compatibility" '{
  "task": "Draft a checkout reminder for an Airbnb guest leaving tomorrow at 11:00.",
  "mode": "hospitality_assistant",
  "source": "smoke-test"
}'

echo
echo "Smoke tests sent. Validate that responses are profile-appropriate and do not claim external actions were performed."
