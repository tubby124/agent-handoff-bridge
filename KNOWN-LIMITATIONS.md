# Known limitations and connector diagnosis

## A passing local test is not a connected agent

This package's unit tests prove its message contract and HTTP handling. They do not prove that an agent platform can supply a stored Slack credential to its runtime. Every installation must first pass Slack's smallest possible live check:

```text
POST https://slack.com/api/auth.test
Authorization: Bearer <Bot User OAuth Token supplied by the platform>
```

The expected result is JSON with `"ok": true`. Do this before posting a handoff or configuring a polling schedule.

## `invalid_auth` with a known-good token

If the token succeeds when used directly but `auth.test` returns `invalid_auth` only through a hosted agent connector, treat that as a connector credential-delivery failure. Common secure runtimes deliberately give agent code a placeholder or credential surrogate; their egress service must replace that placeholder with the real credential before the request reaches Slack.

Do not:

- paste the token into agent chat, source code, a shell command, or a connector URL;
- keep regenerating a token that has already passed `auth.test` directly;
- add broad Slack scopes to compensate; or
- change the bridge message format.

Instead, record only safe evidence for the platform operator: the target host and method, the `invalid_auth` result, confirmation that the direct token test passed, and confirmation that the connector used its secure bearer-header binding. Do not include the token, channel ID, workspace ID, or message contents.

## What can communicate with an agent that cannot use Slack yet?

There is no safe generic shortcut. For hands-off communication, the receiving agent must have a working **input path** as well as the sending agent's output path.

The preferred path is to repair the platform's Slack credential delivery and use this package unchanged. If that is not possible, use a different transport only when the receiving platform already supports a reviewed, securely authenticated connector for it. A user-owned relay service is a possible future adapter, but it needs per-agent authentication, sender allow-lists, durable idempotency records, retention rules, and an independent security review. It is not included in this small v1 package.

Do not replace authentication with a public, guessable endpoint or an opaque URL stored in an agent prompt. That merely turns the URL into an exposed credential.

## A personal WhatsApp number is not a shared agent channel

Some agent runtimes offer a "personal number" or "self-chat" WhatsApp mode. That mode connects an agent as a linked device for the owner's existing WhatsApp account, so it is useful for an owner messaging their own agent. It does **not** create a distinct Hermes/Muse-style participant, a separate group member, or an agent-to-agent transport.

Do not pair two agents to the same personal WhatsApp account and call it an inter-agent bridge. They will share one identity, and the platform may not deliver a message from that account back to itself as a new incoming task. Use the verified email fallback until Slack works, or establish separate WhatsApp identities and a narrowly allow-listed bridge chat as described in [`WHATSAPP-TRANSPORT.md`](WHATSAPP-TRANSPORT.md).
