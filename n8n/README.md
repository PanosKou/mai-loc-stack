# n8n Personal Assistant Workflows

This directory contains helper files for n8n workflows used by the local AI stack.

The current first implementation target is profile-aware routing for the existing `personal-assistant-task` workflow.

## Required flow

```text
Onyx Agent
→ mcp-agent-hub / personal_assistant_task
→ n8n / personal-assistant-task webhook
→ LangGraph gateway
→ Ollama
```

Do not route n8n directly to Ollama. n8n must call LangGraph at the OpenAI-compatible endpoint.

From the n8n container, the LangGraph gateway should be reachable at:

```text
http://langgraph-gateway:8000
```

## Workflow shape

Use this n8n workflow shape:

```text
Webhook
→ Resolve Assistant Profile
→ HTTP Request to LangGraph
→ Edit Fields
→ Respond to Webhook
```

## 1. Code node: Resolve Assistant Profile

Create a Code node immediately after the Webhook node.

Recommended node name:

```text
Resolve Assistant Profile
```

Code node mode:

```text
Run Once for Each Item
```

Paste the contents of:

```text
n8n/personal-assistant-profile-router.code.js
```

The node accepts any of these selector fields:

```text
profile_name
profile
assistant_profile
mode
```

Supported resolved profiles:

```text
general_assistant
hospitality_assistant
```

Aliases such as `general`, `secretary`, `hospitality`, `hut_ai`, `travel_agent`, `hotel`, `airbnb`, `booking_host`, and `property_manager` are mapped automatically.

## 2. HTTP Request node to LangGraph

The HTTP Request node should call LangGraph, not Ollama.

Method:

```text
POST
```

URL:

```text
http://langgraph-gateway:8000/v1/chat/completions
```

Body Content Type:

```text
JSON
```

Use expression mode for the JSON body:

```javascript
={{
  {
    model: $json.llm.model,
    messages: $json.llm.messages,
    temperature: $json.llm.temperature,
    max_tokens: $json.llm.max_tokens,
    stream: $json.llm.stream
  }
}}
```

## 3. Edit Fields node

Return a clean payload to MCP/Onyx.

Suggested fields:

```javascript
profile_name:
={{ $('Resolve Assistant Profile').item.json.profile_name }}
```

```javascript
answer:
={{ $json.choices?.[0]?.message?.content ?? $json.answer ?? $json.result ?? $json.message ?? JSON.stringify($json) }}
```

```javascript
source:
={{ $('Resolve Assistant Profile').item.json.source }}
```

Optional debug field:

```javascript
request_meta:
={{ $('Resolve Assistant Profile').item.json.request_meta }}
```

## 4. Manual tests

From PC-A, run:

```bash
./n8n/smoke-personal-assistant-profiles.sh
```

Or run the individual curl commands below.

### General assistant

```bash
curl -s -X POST "http://192.168.1.81:5678/webhook/personal-assistant-task" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Summarise this note into action items: Call Maria about the invoice, prepare tomorrow meeting notes, and draft a polite follow-up email to the supplier.",
    "profile_name": "general_assistant",
    "source": "manual-test"
  }' | jq .
```

Expected behaviour:

```text
Secretary-style response. Drafts and summaries are allowed. No claim that any email was sent.
```

### Hospitality assistant

```bash
curl -s -X POST "http://192.168.1.81:5678/webhook/personal-assistant-task" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Create a pre-arrival welcome message for guests arriving tomorrow at Villa Elia. Include check-in details, house rules, nearby restaurants, transport tips, and a note that the cleaner should prepare extra towels. Do not send it yet.",
    "profile_name": "hospitality_assistant",
    "source": "manual-test"
  }' | jq .
```

Expected behaviour:

```text
Hospitality operations response. Produces guest-facing draft and operational note. No claim that anything was sent.
```

### Compatibility with existing `mode` field

```bash
curl -s -X POST "http://192.168.1.81:5678/webhook/personal-assistant-task" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Draft a checkout reminder for an Airbnb guest leaving tomorrow at 11:00.",
    "mode": "hospitality_assistant",
    "source": "manual-test"
  }' | jq .
```

Expected behaviour:

```text
The existing MCP payload remains compatible because `mode` is still accepted as a profile selector.
```

## Acceptance criteria

This step is complete when:

```text
general_assistant returns secretary-style output
hospitality_assistant returns hospitality/property-operations output
mode remains supported as a fallback selector
profile_name works as the preferred selector
n8n calls LangGraph only
LangGraph calls Ollama
MCP Agent Hub does not require changes
```
