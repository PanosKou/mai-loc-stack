# Email assistant skill

This skill exposes read-only and draft-only email tools through the MCP Agent Hub.

It intentionally does not expose any send, delete, archive, label, or mailbox mutation tool except optional draft creation through the configured workflow.

## Tools

```text
email_search
email_read
email_draft_reply
```

## Runtime flow

```text
Onyx
  -> mcp-agent-hub
  -> email_assistant skill
  -> n8n email workflows
  -> Gmail / mailbox provider
  -> LangGraph for drafting when configured in n8n
  -> Ollama only through LangGraph
```

The skill does not call Ollama directly.

## Environment

Add these to `mcp-agent-hub/.env`:

```env
EMAIL_SEARCH_WEBHOOK_URL=http://192.168.1.81:5678/webhook/email-search
EMAIL_READ_WEBHOOK_URL=http://192.168.1.81:5678/webhook/email-read
EMAIL_DRAFT_REPLY_WEBHOOK_URL=http://192.168.1.81:5678/webhook/email-draft-reply

EMAIL_DEFAULT_MAX_RESULTS=5
EMAIL_MAX_RESULTS_HARD=10
EMAIL_REQUEST_TIMEOUT_SECONDS=90
```

## n8n workflow contracts

### email-search

Input:

```json
{
  "query": "from:example@example.com newer_than:7d",
  "max_results": 5,
  "unread_only": false,
  "from_address": null,
  "subject": null,
  "source": "mcp-agent-hub"
}
```

Expected output:

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

### email-read

Input:

```json
{
  "message_id": "provider-message-id",
  "include_body": true,
  "include_thread": true,
  "source": "mcp-agent-hub"
}
```

Expected output:

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

### email-draft-reply

Input:

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

Expected output:

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

The workflow must never send the message. It should only create a draft or return draft text.
