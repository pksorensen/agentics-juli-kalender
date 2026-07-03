# agentics.dk · Juli-kalender 2026 🗓️🦊

En omvendt julekalender for juli: **31 dage, 31 animerede avatarer** — én "låge"
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

## Sådan hænger det sammen

| Fil | Hvad |
|---|---|
| `calendar.html` | 31-lågers kalender-grid. Datolåst til juli 2026 — alle avatarer er synlige, men kun passerede dage kan klikkes. `?preview=1` låser alt op (operator-preview, per browser); `?preview=0` slår det fra igen. |
| `day-1.html` … `day-31.html` | Én side per avatar: fullscreen cinematic hero, cursor-reaktiv SVG/canvas-mascot, historie-kort og gætte-widget (localStorage; scoren samles på kalendersiden). |
| `day-2.html` | 🎬 Opgraderet til **rigtig video-avatar** (Viktor Oddy-workflowet): GPT Image 2-still → Seedance 2.0 image-to-video → all-intra re-encode → scroll-scrubbet playhead. Den kodede original ligger i `assets/day-2/day-2-coded-original.html`. |
| `assets/day-N/` | Genererede video-assets per opgraderet dag (still, rå klip, scrub-mp4/webm, poster). |
| `tools/assemble.py` | Genererer `calendar.html` + injicerer historie-kort/gætte-widget i alle day-sider. `--calendar-only` springer day-injektionen over (kør ALDRIG fuld injektion to gange — chromen dubleres). |
| `index.html`, `concept-*.html`, `round2-*.html` | Rå kildesider fra de første eksperiment-runder (dag 1–13 peger på indhold herfra). |
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
