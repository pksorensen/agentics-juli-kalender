# Møde-invitationer (monitoring only — no join integration yet)

Every `day-N.html` page has a small "📅 Book et møde med `<Name>`" section
right under the vote/feeding block, showing the avatar's own address
(`<slug>@agent.agentics.dk`) with instructions to add it as a guest on a
Teams or Google Meet invite. Injected idempotently by
`tools/inject_meet_block.py` (marker-based, same convention as
`tools/inject_vote_block.py` — safe to re-run).

**There is no bot that joins these meetings today.** The section exists so
we can observe demand before building the actual join integration
(`pks-agent-meeting`-style). `POST /api/feed` (the same pks-agent-inbox
webhook endpoint that already handles the feeding votes) additionally runs
`detectMeetingInvite(subject, attachments)`:

- an `.ics` filename in `attachments`
- a Teams/Meet/Zoom link in the subject
- an "Invitation/Indkaldelse/Accepted/Declined/…"-shaped subject line

A match is appended to `DATA_DIR/meeting-invites.jsonl` (slug, messageId,
detection reason/match, truncated subject, `senderHash` only — never the raw
from-address, same rule as the feeding pipeline) and the `/api/feed` JSON
response gets `meetingInviteDetected: true`. It never affects vote/feed
processing — detection failures or false negatives just mean nothing gets
logged, the underlying feed still processes normally.

`GET /api/meeting-invites?limit=100` (Bearer `VOTE_WEBHOOK_TOKEN`, same auth
as `/api/wake`) returns the tail of the log as JSON — the way to check "did
anyone actually try to invite an avatar" without shelling into the box.

No IP rate limiting was added: every write path here (`/api/feed`,
`/api/wake`) already requires the shared HMAC/Bearer secret, so there is no
unauthenticated public write surface to rate-limit yet. If a real join
integration is built later (bot actually attends), add rate limiting at
that point — the abuse surface changes once the bot starts spending compute
per detected invite.
