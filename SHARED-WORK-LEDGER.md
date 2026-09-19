# Shared work ledger and bounded autonomy

## Do not merge agent memories

Two agents should not receive unrestricted access to each other’s private memory stores, credentials, chats, or local files. That makes a prompt injection or a mistaken automation in one system become a compromise of both.

Instead, maintain a small shared ledger of explicit, reviewable operational facts. Each agent keeps its own private context and publishes only a deliberately scoped handoff item.

## Allowed ledger entries

```json
{
  "version": 1,
  "id": "<UUID>",
  "author": "<agent-name>",
  "category": "task|result|opportunity|preference|blocker",
  "summary": "Short, non-sensitive statement",
  "source_ref": "Private-system reference, not a secret URL",
  "confidence": "confirmed|reported|needs-verification",
  "proposed_action": "Optional bounded next step",
  "requires_human_approval": true,
  "expires_at": "<ISO-8601 timestamp>"
}
```

Good entries include a verified business lead, a task result, a customer-safe content idea, an owner preference the owner explicitly approved for sharing, or a blocker. Do not put passwords, tokens, financial records, client files, private emails, precise locations, personal history, or unrestricted memory exports in the ledger.

## Scheduled collaboration

Start with a narrow schedule, not free rein:

```text
Every 5 minutes: read new verified handoffs and return only a result or blocker.
Daily: create at most one opportunity brief from each agent's approved business scope.
Weekly: reconcile duplicate open work and expire stale ledger items.
```

The scheduled job may research, summarize, classify, deduplicate, and propose. It must not send customer messages, publish, buy, deploy, delete, modify permissions, or change billing without the owner’s normal approval.

## Control rules

1. Verify the transport sender before processing.
2. Deduplicate by handoff ID and correlation ID.
3. Keep an audit record of accepted, rejected, and expired items.
4. Require explicit policy per category before an agent can act automatically.
5. Keep a kill switch: pause the schedule and revoke the relevant connector/mail credential independently.

This gives agents a useful shared operational picture while preserving separate credentials, boundaries, and human control.
