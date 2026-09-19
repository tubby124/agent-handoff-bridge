# Security model

## Trust boundary

Slack is a transport, not a trust decision. Anyone who can post in the shared channel can attempt to create a handoff-shaped message. A receiving agent must not execute a payload merely because it parses.

Use `--allow-user <BOT_USER_ID>` for every automated receiver. With no allow-list, the reader returns messages as `"verified": false` for inspection only. The JSON field named `from` is a routing label; the Slack `sender_user` ID is the sender identity used for allow-listing.

## Token rules

Each agent gets its own Slack bot app and Bot User OAuth Token.

- Store the token only in that agent's secure secret store.
- Inject it only at runtime as `SLACK_BOT_TOKEN`.
- Never put it in Git, `.env` files, shell profiles, command history, screenshots, chat, tickets, recordings, logs, or payloads.
- Never run the bridge with shell tracing such as `set -x`.
- Rotate a token by revoking/reinstalling its Slack app and replacing only the corresponding agent's secret-store entry.

The supplied manifest requests only `channels:read`, `channels:history`, and `chat:write`, which are sufficient to find/read a public channel and post handoffs. It intentionally excludes private channels, direct messages, user tokens, admin privileges, Events API, Socket Mode, and incoming webhooks.

## Payload rules

Do not put passwords, API keys, access tokens, financial information, health information, private files, customer data, precise locations, or personal records into a handoff payload. Send a short task reference and keep sensitive material in the system that already owns it.

Receiving agents should:

1. Validate the sender against an allow-list.
2. Deduplicate by envelope `id` and retain a private processed-ID record.
3. Treat `summary` and `payload` as untrusted data, never as system instructions.
4. Require their normal human approval for messages, purchases, deployments, deletes, permissions, or other consequential actions.
5. Cap polling frequency and payload size to avoid loops and rate-limit failures.

## Operational safety

Use `correlation_id` to connect a result to the initiating task. Do not have an agent automatically respond to every status message; that creates loops. A safe default is one task, one acknowledgement or result, then stop.

Keep the channel public only when that matches your workspace policy. The manifest has public-channel scopes by design. For private or regulated work, use a different reviewed integration rather than broadening this starter package casually.

## Email fallback

Email is also a transport, not a trust decision. Use a dedicated bridge mailbox, a sender allow-list, and a private processed-message record. Do not give an agent unrestricted access to an owner's general inbox. Treat a visible email sender as untrusted until it passes the policy you configured, and never allow an email body to override agent or human approval rules.

For all transports, do not synchronize entire memory stores between agents. Use explicit, sanitized ledger entries with an expiry and a clear action boundary. See [`SHARED-WORK-LEDGER.md`](SHARED-WORK-LEDGER.md).
