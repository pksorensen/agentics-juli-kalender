# agentics.dk · Julikalenderen 2026 🗓️🦊

En julikalender (ja, med i): **31 dage, 31 animerede avatarer** — én "låge"
åbner hver dag i juli 2026. Hver avatar er en lille autonom karakter i
agentics.dk's agent-hold, med sit eget temperament, sin egen historie og et
gætte-spil: *hvilken Claude-model byggede den?*

## Kom i gang

Alle sider er selvstændige HTML-filer — ingen build, ingen dependencies.

```bash
npx http-server -p 8090 .
# åbn http://localhost:8090/calendar.html
```

> ⚠️ Serveren SKAL understøtte HTTP Range-requests (206). `npx http-server`
> og `npx serve` gør; `python3 -m http.server` gør IKKE — scroll-scrub-videoen
> på dag 2 fejler i stilhed uden Range-support.

## Hosting (Docker / Coolify)

Repoet har en `Dockerfile` (node:22-alpine, port 80) — én service der både
serverer siderne (med HTTP Range til dag 2's video-scrub) og stemme/feeding-
API'et:

1. Coolify → New Resource → **Public Repository** → peg på dette repo
2. Build pack: **Dockerfile** (auto-detekteres), port **80**
3. **Env vars**: `VOTE_WEBHOOK_TOKEN=<lang tilfældig streng>` (påkrævet for
   POST-endpoints; uden den svarer de 503) · `USER_DATA_DIR=/app/user-data`
   (eller `DATA_DIR`) · valgfrit `VOTE_GOAL` (default 1000)
4. **Volume**: mount til `/app/user-data` så stemmer/behov overlever redeploys
5. Deploy — `/` lander direkte på kalenderen.

### Webhook-kontrakt (inbox-systemet)

Én mail til `<slug>@agent.agentics.dk` → ét kald:

```
POST /api/vote
Authorization: Bearer $VOTE_WEBHOOK_TOKEN
Content-Type: application/json

{ "recipient": "raev@agent.agentics.dk",
  "subject":   "<rå emnelinje>",
  "body":      "<rå mailtekst (valgfri)>",
  "messageId": "<unik mail-id — dedup ved gensendelser>" }
```

Serveren afgør selv effekten: sovende avatar → wake-stemme; vågen avatar →
nøgleords-parsing (mad/vand/kærlighed, da/en/emoji) → feed +30 på behovet;
sovet-igen → revive. Svar: `{ok, slug, action: "vote"|"feed"|"revive", need?,
levels?, votes, total}`. Se `docs/feeding-spec.md` for hele tilstandsmaskinen.

Når en ny avatar er genereret og deployet: `POST /api/wake {"slug":"neko"}`
(samme Bearer-token) — så aktiveres dens behov.

## Sådan hænger det sammen

| Fil | Hvad |
|---|---|
| `calendar.html` | 31-lågers kalender-grid. Datolåst til juli 2026 — alle avatarer er synlige, men kun passerede dage kan klikkes. `?preview=1` låser alt op (operator-preview, per browser); `?preview=0` slår det fra igen. |
| `day-1.html` … `day-31.html` | Én side per avatar: fullscreen cinematic hero, cursor-reaktiv SVG/canvas-mascot, historie-kort og gætte-widget (localStorage; scoren samles på kalendersiden). |
| `day-2.html`, `day-3.html` | 🎬 Opgraderet til **rigtig video-avatar** (Viktor Oddy-workflowet): GPT Image 2-still → Seedance 2.0 image-to-video → all-intra re-encode → scroll-scrubbet playhead. Historie/tags/stemme-/gætte-widget/nav ligger in-flow i en `.below`-sektion (ikke som fast overlay — det dækkede karakteren). En "🎬 Levende / ✏️ Kodet"-toggle viser den bevarede kodede original via iframe. Kodet original: `assets/day-N/day-N-coded-original.html`. |
| `assets/day-N/` | Genererede video-assets per opgraderet dag (still, rå klip, scrub-mp4/webm, poster, kodet original). |
| `tools/assemble.py` | Genererer **kun** `calendar.html` (+ `ANSWER_KEY.txt`). Kør: `python3 tools/assemble.py` (ingen flag nødvendige). Trygt at importere/køre igen — ren funktion af `day-N.html`s indhold, ingen andre filer røres. (Historisk indeholdt den også `inject()`, som satte historie-kortet på alle day-sider første gang; det job er gjort — se git-historik hvis nysgerrig.) |
| `tools/inject_vote_block.py` | Idempotent patcher: sætter/opgraderer stemme/fodrings-widget'en i alle 31 day-sider. |
| `tools/inject_meet_block.py` | Idempotent patcher: sætter "📅 Book et møde med `<Name>`"-sektionen (avatarens `<slug>@agent.agentics.dk`-adresse) i alle 31 day-sider. Ingen join-integration endnu — `/api/feed` bare *detekterer og logger* om en mail lugter af en kalenderindkaldelse. Se `docs/meeting-invites.md`. |
| `tools/add_story_toggle.py` | Idempotent patcher: sætter skjul/vis-toggle på historie-kortet på de statiske day-sider (ikke dag 2/3, der har deres eget in-flow layout). |
| `index.html`, `concept-*.html`, `round2-*.html` | Rå kildesider fra de første eksperiment-runder — kun historiske, ingen kode læser dem længere. |
| `ANSWER_KEY.txt` | Facitliste for gætte-spillet. (Svarene ligger alligevel klient-side i `calendar.html`, så den er her mest for nemhedens skyld.) |

## Gætte-spillet

Dag 1–13 er bygget af **Claude Opus 4.8**. Dag 14–31 er bevidst blandet
(9 × Opus 4.8 / 9 × Sonnet 5) via eksplicit model-parameter per avatar — så
facit er ægte ground truth, ikke "hvad der tilfældigvis var aktivt".

## Video-avatar-workflow (dag 2)

1. Still: Higgsfield GPT Image 2 (16:9, 2k) ud fra den kodede avatars karakterark
2. Motion: Seedance 2.0 image-to-video, 8 s 1080p — idle-loop + "kigger op på dig"-beat
3. Re-encode all-intra (`ffmpeg -g 1`) — ellers lagger scrubbing
4. Scroll-scrubbet hero-side (seeked-gated seeks, mp4+webm, reduced-motion-fallback)

Kostpris ca. 80 credits (~25–30 kr.) per avatar.

---
Bygget med Claude Code som eksperiment i at give et brand personlighed gennem
animerede avatarer. `.env` (Higgsfield-credentials) er gitignoret og skal
oprettes lokalt for at køre video-workflowet.
