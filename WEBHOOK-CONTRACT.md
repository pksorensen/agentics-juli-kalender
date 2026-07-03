# Julikalender feeding — webhook contract (from pks-agent-inbox)

Every mail to <slug>@agent.agentics.dk (31 slugs, one per day-page data-slug:
aura raev agent01 nova comet boo neko tsuru bit lumen ugla chrome ember koi
golem sprout draco aster lundi mochi volt prism nimbus ravn cog frost beacon
sol luna bi vega) is delivered as:

    POST https://agentics.dk/julikalender/api/feed
    Content-Type: application/json
    X-Inbox-Event: email.received        (or "webhook.test" for test fires)
    X-Inbox-Delivery: <random id>
    X-Inbox-Signature: sha256=<hex hmac-sha256(rawBody, SECRET)>

    {"event":"email.received","id":"<msgId>","inboxId":"…","domain":"agent.agentics.dk",
     "to":["ember@agent.agentics.dk"],"from":"fan@example.com",
     "senderHash":"sha256:<hex of lowercased from>","subject":"🥕 mad",
     "receivedAt":"2026-07-03T21:10:43Z","attachments":["…"]}

ALL 31 webhooks share ONE secret (below). Validate: recompute the HMAC over the
raw request body and constant-time-compare with the header. Reject on mismatch.
Route by the "to" localpart. Use senderHash for unique-feeder counts; avoid
storing the raw from address.

SECRET: b5182369fdb0ee6ddef1e995c221d9a65f7f2c2b48a4a51e

Retries: failed deliveries retry 3x (1s/10s/60s). Endpoint should be idempotent
on X-Inbox-Delivery or message id. Delivery is at-most-once beyond that.
Verified 2026-07-03: full pipeline green (prod SMTP -> signed POST, sig valid).
The /api/feed endpoint returned 404 at handover time — once it deploys, ask
Poul's devcontainer agent to re-run the webhook /test fires.
