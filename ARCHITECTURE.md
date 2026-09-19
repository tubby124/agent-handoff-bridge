# Architecture and public roadmap

## v1: portable Slack handoff transport

The shipped code is intentionally a small, self-hosted command-line transport. It supports two or more agents that have:

- a Linux runtime with stock `python3`;
- their own Slack bot token in a secure store;
- access to one shared public channel; and
- their own polling loop and private watermark state.

```text
sender agent -- own bot token --> Slack public channel <-- own bot token -- receiver agent
```

The sender writes a versioned envelope. The receiver polls oldest-first, ignores itself, filters by recipient, and can pin allowed Slack bot user IDs. Slack contains only handoff metadata; each agent retains its own tool access and private context.

## Why this is not a direct agent-to-agent API

The agents may have different security models, runtimes, owners, and approval requirements. A shared, auditable transport prevents either agent from silently gaining the other agent's credentials or local-machine access. Slack is not a database or a task executor; it is the durable handoff log for this small v1.

## v2: reviewed connector adapters

After the core contract is stable, adapters can expose the same four operations to agent platforms that support secure connectors:

| Operation | Meaning |
| --- | --- |
| `send_handoff` | Validate and post a versioned work item. |
| `read_handoffs` | Read recipient-matched items after a watermark. |
| `acknowledge` | Post a bounded acknowledgement for a correlation ID. |
| `publish_result` | Post a result or explicit blocked state. |

An adapter must use the host platform's credential store and action-approval system. It must not ask users to paste tokens into chat or bypass credential surrogation. A platform must correctly resolve any credential surrogate before a reviewed adapter can be called production-ready.

If a platform cannot pass Slack `auth.test` with its stored credential, it has no safe Slack output path yet. A separate relay is not a drop-in workaround: the receiving agent would still need an approved, authenticated way to poll it. [`KNOWN-LIMITATIONS.md`](KNOWN-LIMITATIONS.md) defines the safe diagnosis and the boundary for future relay work.

## Temporary email fallback

Email is an acceptable temporary transport only where both agents already have an approved mail connector. It preserves the same envelope and correlation model while using a dedicated bridge mailbox and strict sender policy. The transport was proven with a synthetic Gmail canary; its portable setup and rollback criteria are in [`EMAIL-TRANSPORT.md`](EMAIL-TRANSPORT.md).

## Shared context without shared private memory

The bridge carries explicit work items, not unrestricted memory synchronization. A shared work ledger can carry reviewed opportunities, tasks, results, and owner-approved preferences while each agent keeps its private context and credentials separate. [`SHARED-WORK-LEDGER.md`](SHARED-WORK-LEDGER.md) defines its schema and the limited scheduled autonomy policy.

## Public distribution gate

Before publishing a directory connector or hosted service, add:

1. A stable API/OpenAPI contract and version policy.
2. OAuth or per-user secret storage; never a shared operator token.
3. Sender allow-lists, payload-size limits, rate limits, and idempotency storage.
4. A privacy policy, support route, disclosure of data retention, and security review.
5. End-to-end tests using disposable Slack workspaces and synthetic data only.

Until then, this MIT package is the safe public artifact: users run it in their own environment with their own Slack bots and data.
