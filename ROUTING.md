# On-demand agent routing

Use this bridge when one agent has a capability the other does not. It is an on-demand handoff, not a background worker: an owner explicitly invokes the sender and receiver for each task.

## Example division of work

| Route to | Good fit |
| --- | --- |
| Build agent | Code, repositories, scripts, local files, test runs, and version-controlled changes. |
| Browser/VM agent | User-directed work in an already authenticated browser session, connected services, and entering a reviewable draft into a portal. |

Capabilities depend on each user's configured agents. Do not assume an agent has an account, browser session, permission, or authoritative data merely because it handled a similar job before.

## Handoff rule

The sender creates one bounded `kind:"task"` envelope describing the objective, inputs already approved by the owner, expected output, and a stopping point. The receiver completes only that work and replies once with `kind:"result"` or `kind:"blocked"`.

No background polling is required. After a sender creates a handoff, the owner explicitly tells the receiving agent to check the bridge and process that task. This avoids idle model use while keeping the work auditable.

## High-impact work

For contracts, regulated forms, payments, signatures, submissions, permission changes, or irreversible actions:

- prepare a reviewable draft only;
- retain the source and completion evidence needed for owner review; and
- require the owner's final, explicit confirmation immediately before the external action.

An agent must never claim an external action happened without target-side confirmation.
