# Agent Handoff Bridge

An open-source, stdlib-only Slack transport for handing bounded work between two or more AI agents.

It is deliberately small: every agent owns its own Slack bot token, all agents meet in one shared **public** channel, and agents poll rather than requiring a hosted webhook, socket, or event server. It is MIT licensed and contains no workspace identifiers, channel identifiers, bot tokens, agent memories, or personal data.

## What it is for

Use this when one agent needs another agent to do a bounded piece of work it is better equipped to handle. Typical examples are a planner asking an executor to run a repository task, or a research agent returning a cited result to a coordinator.

It is a transport and handoff format, not an unrestricted command runner. Receiving agents must treat every payload as untrusted input, apply their own authorization rules, and maintain their own processed-message watermark.

## Architecture

```text
Agent A + bot token A                         Agent B + bot token B
        |                                              |
        +--- agent-handoff-send --> shared channel <--+
        +--- agent-handoff-read  <-- shared channel <--+
```

Each message is a versioned JSON envelope inside ordinary Slack text. It includes a unique ID, sender, recipient, kind, summary, optional JSON payload, and optional correlation ID. The reader emits messages oldest-first and never returns messages sent by its own Slack bot.

## Quick start

1. Create one Slack bot app for **each** agent from [`slack-app-manifest.json`](slack-app-manifest.json). Do not share bot tokens between agents.
2. Create one public Slack channel and invite each bot.
3. Copy this directory to each agent's Linux runtime. Configure each runtime's own bot token only through its secret store as `SLACK_BOT_TOKEN`.
4. Send a handoff from the first agent:

   ```sh
   ./bin/agent-handoff-send \
     --channel <CHANNEL_ID> \
     --from planner \
     --to executor \
     --kind task \
     --summary 'Review the staging deployment' \
     --payload-json '{"environment":"staging"}' \
     --correlation-id deploy-42
   ```

5. Poll from the receiving agent:

   ```sh
   ./bin/agent-handoff-read \
     --channel <CHANNEL_ID> \
     --as executor \
     --allow-user <PLANNER_BOT_USER_ID> \
     --since <LAST_PROCESSED_TS>
   ```

The reader prints a JSON array. Persist the newest successfully handled Slack timestamp in the receiving agent's own private state store. See [`SETUP.md`](SETUP.md) for the full setup and [`SECURITY.md`](SECURITY.md) before enabling automated handling.

## Email fallback

When a hosted agent platform cannot correctly deliver a Slack credential, email can be a temporary, auditable transport **only when both agents already have a reviewed mail path**. A synthetic Gmail canary has been verified with this envelope pattern: sender email → receiving agent's Gmail connector → same-thread result → sender mailbox readback.

This is not a replacement for a broken Slack connector forever. It is a narrow fallback with a separate dedicated bridge mailbox, sender allow-list, correlation ID, and polling state. See [`EMAIL-TRANSPORT.md`](EMAIL-TRANSPORT.md) for the protocol and [`SHARED-WORK-LEDGER.md`](SHARED-WORK-LEDGER.md) for the boundary on what agents may share.

## WhatsApp is not a drop-in bridge

A personal WhatsApp number can be useful as an agent's **self-chat control inbox**, but it does not give that agent a separate WhatsApp identity. If both agents are attached to the same personal account, they cannot exchange messages with each other as distinct participants. A genuine WhatsApp bridge needs separate agent identities (normally a dedicated number for one agent) and an explicitly allow-listed chat. See [`WHATSAPP-TRANSPORT.md`](WHATSAPP-TRANSPORT.md) before attempting that setup.

## Compatibility

The package needs only stock Linux `python3`; no `pip`, server, Docker image, or framework is required. It can be used by any agent that can safely execute local commands and receive a bot token through its own secure environment.

An agent platform's connector or credential-injection behavior is outside this package. The package works when `SLACK_BOT_TOKEN` is correctly injected into the agent runtime. See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the public-product boundaries and future connector path.

Before treating an installation as ready, run the connector's smallest authentication check: Slack `auth.test`. If a direct Bot User OAuth Token succeeds but the same stored credential produces `invalid_auth` through an agent platform, the platform is not resolving or injecting the credential correctly. Do not rotate the token repeatedly, widen Slack scopes, or weaken the bridge's security model. See [`KNOWN-LIMITATIONS.md`](KNOWN-LIMITATIONS.md) for the safe diagnosis and fallback decision.

## Verify locally

```sh
chmod 700 bin/agent-handoff-send bin/agent-handoff-read
python3 -m unittest tests/test_agent_handoff.py
./bin/agent-handoff-send --help
./bin/agent-handoff-read --help
```

## License

MIT. See [`LICENSE`](LICENSE).
