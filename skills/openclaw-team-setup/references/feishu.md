# Feishu Setup Notes

Use this reference when the project wants OpenClaw agents exposed through Feishu or Lark bots.

## What To Configure

At minimum:

- enable the `feishu` plugin
- enable `channels.feishu`
- set `connectionMode`
- define `accounts`
- define routing bindings from `feishu accountId=<id>` to the intended agent

Typical config shape:

```json5
{
  channels: {
    feishu: {
      enabled: true,
      connectionMode: "websocket",
      defaultAccount: "pm",
      dmPolicy: "pairing",
      groupPolicy: "open",
      requireMention: false,
      accounts: {
        pm: {
          appId: "<APP_ID>",
          appSecret: "<APP_SECRET>",
          name: "pm",
        },
        dev: {
          appId: "<APP_ID>",
          appSecret: "<APP_SECRET>",
          name: "dev",
        },
        qa: {
          appId: "<APP_ID>",
          appSecret: "<APP_SECRET>",
          name: "qa",
        },
      },
    },
  },
  bindings: [
    { type: "route", agentId: "pm", match: { channel: "feishu", accountId: "pm" } },
    { type: "route", agentId: "dev", match: { channel: "feishu", accountId: "dev" } },
    { type: "route", agentId: "qa", match: { channel: "feishu", accountId: "qa" } },
  ],
}
```

## Sensitive Fields

Do not place real values in the skill:

- `appId`
- `appSecret`
- any verification or encryption keys

Collect them from the user during execution.

## Recommended Operator Flow

1. Create or confirm each Feishu app
2. Collect the App ID and App Secret for each bot
3. Write them into `channels.feishu.accounts.<id>`
4. Restart the gateway
5. Send a DM to each bot
6. Approve pairing if `dmPolicy` is `pairing`
7. Verify routing by checking both reply behavior and gateway logs

## Pairing Guidance

Common commands:

```bash
openclaw pairing list feishu
openclaw pairing approve feishu <CODE>
```

After pairing, store no extra notes in the skill itself.

## Routing Verification

The fastest test is to send a role-identifying message to each bot:

- pm bot: `请只回复：ROLE=pm`
- dev bot: `请只回复：ROLE=dev`
- qa bot: `请只回复：ROLE=qa`

Then inspect logs if behavior is wrong.

Good sign:

- account recognized correctly
- dispatch goes to the intended agent

Bad sign:

- `feishu[dev] ... dispatching to agent (session=agent:main:main)`

That means the message still routed to `main`, regardless of which bot received it.

## Practical Troubleshooting

If all bots still route to `main`:

- confirm bindings exist in `openclaw.json`
- confirm the gateway was restarted after binding changes
- confirm concurrent config writes did not drop some bindings
- re-run `openclaw agents bindings --json`
- inspect `gateway.log` immediately after a fresh test message

If one bot works and others do not:

- compare account ids under `channels.feishu.accounts`
- compare binding `accountId`
- verify the message log shows the same account id you bound
