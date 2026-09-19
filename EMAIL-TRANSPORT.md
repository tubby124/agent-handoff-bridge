# Email transport fallback

## When to use this

Use email only when the preferred Slack bridge cannot authenticate in an agent platform and both agents already have approved, secure email access. It is a temporary, low-volume handoff transport, not a way to expose a personal inbox to every agent.

The pattern below was verified end-to-end with synthetic data: a sender delivered a structured email to a mailbox connected to a receiving agent, the receiving agent found it through its Gmail connector, replied in the same thread, and the sender read the reply back.

## Required setup

1. Create a dedicated bridge mailbox or alias. Do not use an owner’s general-purpose inbox long term.
2. Give the sender agent its own approved SMTP/OAuth send path and the ability to read only its bridge replies.
3. Connect the bridge mailbox to the receiving agent using that platform’s supported mail connector.
4. Allow only the known sender address or domain. Treat the visible `From` header as an input to verify, not proof by itself.
5. Store sender/receiver credentials in their separate secret stores. Never put a password, OAuth code, app password, or access token in a handoff email.

## Envelope

Use a plain-text body beginning with this marker:

```text
[agent-handoff/email-v1]
{"version":1,"id":"<UUID>","from":"planner","to":"executor","kind":"task","summary":"Bounded work item","payload":{},"correlation_id":"<WORK_ID>"}
```

Use an exact subject prefix such as `[Agent Handoff] <UUID>`. A result replies in the same thread and includes a new envelope with `kind` set to `result`, `error`, or `status`. Do not depend on quoted original text as the result; parse only the reply's own marked envelope.

## Polling and state

Each agent owns a private state record containing at least the last processed message ID, processed envelope IDs, and correlation IDs. Poll at a bounded interval (for example, every five minutes), process oldest-first, and advance state only after successful validation and handling. Do not automatically answer every message; one task should produce at most one acknowledgement and one result.

## Live acceptance check

Before real work, use a synthetic canary:

1. Sender emails a single marker envelope with no personal or customer data.
2. Receiver finds that exact subject only and replies in-thread with a marker result.
3. Sender reads the reply, verifies the correlation ID and sender policy, and records it.

Passing this check proves the email transport. It does not authorize either agent to send customer messages, spend money, publish, change accounts, or share private records.

## Migration back to Slack

Keep the same envelope fields and correlation IDs. Once the agent platform passes Slack `auth.test` with its stored bot credential, change only the transport configuration. Run the Slack canary before disabling email, then keep the bridge mailbox available for a short rollback window.
