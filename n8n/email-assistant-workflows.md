# n8n Email Assistant Workflows

These workflows back the Agent Hub `email_assistant` skill.

The MCP tools live in:

```text
mcp-agent-hub/skills/email_assistant/
```

n8n should handle mailbox-provider OAuth and Gmail/mailbox operations. The MCP skill should remain the only Onyx-facing tool surface.

## Required flow

```text
Onyx
  -> mcp-agent-hub / email_assistant skill
  -> n8n email workflow
  -> Gmail / mailbox provider
```

For LLM-generated drafts:

```text
n8n email-draft-reply workflow
  -> read source email/thread
  -> call LangGraph /v1/chat/completions
  -> create draft only
```

Do not route n8n directly to Ollama. n8n must call LangGraph at:

```text
http://langgraph-gateway:8000/v1/chat/completions
```

Do not send email from these workflows.

## 1. email-search workflow

Webhook path:

```text
/email-search
```

Suggested shape:

```text
Webhook
  -> Gmail/Search messages
  -> Normalize Email Search Results
  -> Respond to Webhook
```

Expected request body:

```json
{
  "query": "newer_than:7d",
  "max_results": 5,
  "unread_only": false,
  "from_address": null,
  "subject": null,
  "source": "mcp-agent-hub"
}
```

Expected response:

```json
{
  "messages": [
    {
      "message_id": "provider-message-id",
      "thread_id": "provider-thread-id",
      "from": "Sender <sender@example.com>",
      "subject": "Subject",
      "date": "2026-06-26T12:00:00Z",
      "snippet": "Short preview...",
      "unread": true
    }
  ]
}
```

## 2. email-read workflow

Webhook path:

```text
/email-read
```

Suggested shape:

```text
Webhook
  -> Gmail/Get message or thread
  -> Normalize Email Body
  -> Respond to Webhook
```

Expected request body:

```json
{
  "message_id": "provider-message-id",
  "include_body": true,
  "include_thread": true,
  "source": "mcp-agent-hub"
}
```

Expected response:

```json
{
  "message_id": "provider-message-id",
  "thread_id": "provider-thread-id",
  "subject": "Subject",
  "from": "Sender <sender@example.com>",
  "to": "Recipient <recipient@example.com>",
  "date": "2026-06-26T12:00:00Z",
  "body": "Message body",
  "thread_messages": []
}
```

## 3. email-draft-reply workflow

Webhook path:

```text
/email-draft-reply
```

Suggested shape:

```text
Webhook
  -> Gmail/Get source message or thread
  -> HTTP Request to LangGraph
  -> Gmail/Create draft reply
  -> Respond to Webhook
```

Expected request body:

```json
{
  "message_id": "provider-message-id",
  "reply_instructions": "Write a polite reply confirming availability next week.",
  "tone": "professional",
  "create_gmail_draft": true,
  "send_email": false,
  "source": "mcp-agent-hub"
}
```

The LangGraph request should use:

```javascript
={{
  {
    model: "onyx-fast",
    messages: [
      {
        role: "system",
        content: "You draft email replies. Create a concise reply based only on the provided email/thread and user instructions. Do not claim the email was sent."
      },
      {
        role: "user",
        content: "Email/thread:\n" + JSON.stringify($json.email_context) + "\n\nReply instructions:\n" + $json.reply_instructions + "\n\nTone: " + $json.tone
      }
    ],
    temperature: 0.2,
    max_tokens: 900,
    stream: false
  }
}}
```

Expected response:

```json
{
  "draft_created": true,
  "draft_id": "provider-draft-id",
  "message_id": "provider-message-id",
  "subject": "Re: Subject",
  "draft_body": "Draft reply body",
  "send_email": false
}
```

## Safety rules

- No send operation.
- No delete/archive/label mutation in this first version.
- Draft creation is allowed only when `create_gmail_draft` is true.
- Always return `send_email: false`.
- Do not include raw OAuth tokens, credentials, or provider error bodies in the webhook response.