# WhatsApp transport boundary

WhatsApp can be an optional future transport for an agent handoff, but it is not included in the Slack v1 code in this repository.

## Personal-number mode: control only

Many agent runtimes offer a QR-based WhatsApp setup using the owner's existing number. This is usually called **self-chat** mode: the owner opens WhatsApp's "Message Yourself" conversation to talk to the agent.

That is not an agent-to-agent channel. It gives the agent the owner's WhatsApp identity, not its own identity. Two agents attached to one account cannot reliably hand work to each other as separate WhatsApp participants.

Use personal-number mode only when all of these are true:

- the owner wants a private control inbox for one agent;
- the runtime has an explicit owner allow-list;
- the agent is not allowed to scan, reply to, or automate other personal conversations; and
- external sends still require the owner's approval.

## A real WhatsApp bridge: separate identities

For a bridge, give at least one agent a dedicated WhatsApp number and create one explicit bridge conversation or group. Configure each runtime with only that chat and only the other approved participant as a sender. Do not use the owner's general inbox as the bridge.

Before enabling a schedule, verify with synthetic data:

1. Agent A sends one versioned handoff envelope to the bridge chat.
2. Agent B receives it, rejects an unexpected sender, and writes a same-thread or correlated synthetic result.
3. Agent A reads the result exactly once using an idempotency key.
4. Both agents reject a normal personal chat and refuse to take an external action without approval.

## Do not use this as a Slack bypass

If Slack credential injection is broken on a hosted platform, report and repair that defect. A WhatsApp bridge has different account, retention, identity, and approval risks; it is an independently reviewed alternative, not a way to smuggle a Slack token or grant one agent the other's credentials.
