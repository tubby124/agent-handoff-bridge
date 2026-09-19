# Setup

This setup uses one Slack bot per agent. A bot token represents one agent runtime and must never be shared between agents or users.

## 1. Create one app for each agent

Repeat these steps once for each agent. Give each installed app a distinct display name in Slack so people can tell which agent sent a message.

1. Go to [api.slack.com/apps](https://api.slack.com/apps) and sign in to the intended workspace.
2. Select **Create New App** and then **From an app manifest**.
3. Choose the workspace, select the **JSON** tab, and paste this package's `slack-app-manifest.json`.
4. Create the app, select **Install App**, then choose **Install to Workspace**.
5. On **OAuth & Permissions**, copy the **Bot User OAuth Token**. It begins with `xoxb-`.
6. Put that token directly into the owning agent's secure secret store. Configure the agent runtime to expose it only as `SLACK_BOT_TOKEN` while these commands run.

The only requested bot scopes are `channels:read`, `channels:history`, and `chat:write`. No user token, private-channel scope, direct-message scope, Events API, Socket Mode, webhook, or admin scope is used.

## 2. Create the shared public channel

1. Create a new **public** Slack channel with a neutral name such as `agent-handoffs`.
2. Invite each bridge bot to it using Slack's `/invite` command or channel member picker.
3. Copy the channel ID from the channel-details panel. Keep it in each agent's private configuration, never source control.

## 3. Install the package on each agent runtime

Copy this directory to each Linux runtime. Do not copy another agent's state directory, configuration, or token.

```sh
chmod 700 bin/agent-handoff-send bin/agent-handoff-read
python3 -m unittest tests/test_agent_handoff.py
```

## 4. Run a two-agent smoke test

On the sending agent, use its own token:

```sh
./bin/agent-handoff-send \
  --channel <CHANNEL_ID> \
  --from planner \
  --to executor \
  --kind task \
  --summary 'Bridge smoke test' \
  --payload-json '{"check":"send-and-read"}' \
  --correlation-id smoke-1
```

On the receiving agent, use its **different** token:

```sh
./bin/agent-handoff-read \
  --channel <CHANNEL_ID> \
  --as executor \
  --limit 25
```

The first read has `"verified": false` until you pin the sender's Slack bot user ID. Copy the `sender_user` value returned for the known smoke test, then repeat with:

```sh
./bin/agent-handoff-read \
  --channel <CHANNEL_ID> \
  --as executor \
  --allow-user <PLANNER_BOT_USER_ID> \
  --since <LAST_PROCESSED_TS>
```

Once `verified` is `true`, persist only the newest successfully handled `ts` in the receiving agent's private state store. Do not advance that watermark for an unhandled, malformed, or rejected handoff.

## Agent-platform connectors

An agent platform can use this package when its secure connector system injects `SLACK_BOT_TOKEN` into its Linux runtime. Do not paste a Slack token into an agent chat. Use the platform's masked secure credential field only. If it uses a platform-managed credential surrogate rather than an environment variable, its runtime must correctly replace that surrogate before requests leave the VM; this package cannot and should not bypass that protection.
