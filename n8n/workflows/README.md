# Importable n8n email workflows

This directory contains n8n workflow JSON files that can be imported into n8n from the editor UI.

n8n workflow JSON files are intentionally stored without credentials. After importing, open each Gmail API HTTP Request node and select the Google OAuth2 credential that has access to Gmail.

## Files

```text
email-search.workflow.json
email-read.workflow.json
email-draft-reply.workflow.json
```

## Import steps

1. In n8n, create a new workflow.
2. Open the workflow menu using the three dots in the top-right editor menu.
3. Select **Import from File**.
4. Select one of the JSON files from this directory.
5. Open each Gmail API HTTP Request node and select the correct Google OAuth2 credential.
6. Save and activate the workflow.

## Production webhook URLs

After activation, the expected production URLs are:

```text
http://192.168.1.81:5678/webhook/email-search
http://192.168.1.81:5678/webhook/email-read
http://192.168.1.81:5678/webhook/email-draft-reply
```

Add these to `mcp-agent-hub/.env`:

```env
EMAIL_SEARCH_WEBHOOK_URL=http://192.168.1.81:5678/webhook/email-search
EMAIL_READ_WEBHOOK_URL=http://192.168.1.81:5678/webhook/email-read
EMAIL_DRAFT_REPLY_WEBHOOK_URL=http://192.168.1.81:5678/webhook/email-draft-reply
```

## Workflow behavior

### email-search.workflow.json

Searches Gmail and returns matching message IDs.

The Gmail list API returns message and thread IDs. Use `email_read` with the returned `message_id` to retrieve the full body, subject, sender, and recipient details.

### email-read.workflow.json

Reads a Gmail message by `message_id`, extracts headers, snippet, labels, and text/html body content, then returns a normalized JSON response.

### email-draft-reply.workflow.json

Reads the source Gmail message, sends the normalized email context plus reply instructions to LangGraph, builds an RFC 2822 MIME reply, and creates a Gmail draft in the original thread.

This workflow creates a draft only. It does not send email.

## Safety rules

- No send operation is included.
- No delete/archive/label mutation is included.
- The draft workflow calls LangGraph at `http://langgraph-gateway:8000/v1/chat/completions`.
- n8n must not call Ollama directly.
- Do not commit n8n credential IDs, OAuth tokens, or exported workflows that contain sensitive headers.
