# Hermes + Gmail temporary adapter

This optional reference adapter lets a Hermes cron job receive only explicitly addressed handoff mail through an already approved Gmail CLI. It is a temporary route while a preferred transport, such as Slack, is unavailable.

It is intentionally narrow:

- searches only a fixed `[Agent Handoff]` subject marker;
- reads a message only after the narrow search returns it;
- accepts only configured sender addresses and envelopes addressed to `hermes`;
- stores processed source message IDs in a local file with mode `0600`; and
- replies in the existing Gmail thread, then records the source message as processed.

It does not read a general inbox, create a mailbox, acquire OAuth credentials, or run a scheduler itself.

## Prerequisites

1. An approved Gmail command-line tool whose path is supplied as `AGENT_HANDOFF_GMAIL_CLI`.
2. A dedicated bridge mailbox or an owner-approved, tightly labelled fallback mailbox.
3. An exact sender allow-list. Do not use `*`.
4. A private state path outside this repository, for example `/var/lib/agent-handoff/hermes-gmail-state.json`.

## Smoke test

Run the poller with a synthetic message only:

```sh
export AGENT_HANDOFF_GMAIL_CLI=/path/to/gmail.py
./agent-handoff-gmail-poll \
  --allowed-from <BRIDGE_SENDER_EMAIL> \
  --state-file /var/lib/agent-handoff/hermes-gmail-state.json
```

For a returned `message_id`, send a synthetic result in the same thread:

```sh
./agent-handoff-gmail-reply \
  --message-id <MESSAGE_ID> \
  --state-file /var/lib/agent-handoff/hermes-gmail-state.json \
  --result-json '{"id":"demo-result-1","from":"hermes","to":"muse","kind":"result","summary":"Synthetic canary complete","payload":{"synthetic":true}}'
```

Only create a Hermes cron job after the two directions have been verified with synthetic data. The job prompt must forbid general inbox access and require approval for any external action beyond the bridge reply.
