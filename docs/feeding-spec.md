# Feeding-system spec (v1) — "Hold dem i live"

Tre-lags engagement-tragt:

1. **LinkedIn-kommentarer** → credits (funding). 1 kommentar = 1 credit; ~100 credits vækker én avatar.
2. **Mails til sovende avatarer** → stemmer ("væk mig først!"). Flest stemmer animeres først.
3. **Mails til vågne avatarer** → MAD/VAND/KÆRLIGHED. Behov forfalder over tid — folk har ansvar
   for at holde dem i live. Tamagotchi-loopet er retention-motoren.

## Livscyklus pr. avatar

```
 SOVENDE (kodet, ikke animeret)
    │  mails = wake-stemmer; leaderboard afgør rækkefølgen
    ▼  Poul genererer video-avatar + kalder POST /api/wake
 VÅGEN (animeret)
    │  behov: kærlighed ❤️ · mad 🍖 · vand 💧  (hver 0-100)
    │  forfald: 100 → 0 på 48 timer (lazy-beregnet: level - 2.0833/time)
    │  mail med behovs-nøgleord: +30 på det behov (cap 100), tæller stadig i total
    ▼  alle tre behov = 0
 SOVET IGEN (trist tilstand, ikke død)
    │  én hvilken som helst feed-mail genopliver (alle behov sættes til 40)
    ▼
 VÅGEN igen
```

## Nøgleords-parsing (server-side, subject + body, case-insensitive)

| Behov | Nøgleord (da/en/emoji) |
|---|---|
| food  | mad, food, foder, 🍖, 🍕, 🍎 |
| water | vand, water, 💧, 🌊 |
| love  | kærlighed, love, elsker, hjerte, ❤️, 💛, 🧡 |

Prioritet ved flere match: subject før body; derefter food > water > love.
Intet match → sovende: wake-stemme; vågen: love (+30).
Én mail fodrer ét behov (flere mails = mere engagement — det er pointen).

## API (udvidelse af vote-API'et — bagudkompatibelt)

- `GET /api/votes` — beholder shape `{goal,total,votes:{slug:n}}` og FÅR EKSTRA felt
  `avatars:{slug:{state:"sleeping"|"awake"|"asleep_again", needs:{love,food,water}(0-100,
  decay-fremskrevet), feeds:{love,food,water}, awokeAt}}`.
- `POST /api/vote` — uændret auth (Bearer VOTE_WEBHOOK_TOKEN). Body får valgfrit
  `subject`, `body` (rå mailtekst — serveren parser nøgleord). Svar:
  `{ok,slug,action:"vote"|"feed"|"revive",need?,levels?,votes,total}`. messageId-dedup uændret.
- `POST /api/wake` — Bearer-authed, `{"slug":"raev"}` → state=awake, behov = 100/100/100.
  (Kaldes når en avatar er blevet genereret og deployet.)
- Ræv (dag 2) er allerede vågen: seedes awake ved første boot.

## UI-tilstande (agx-vote-blokken i story-kortet)

- **SOVENDE**: nuværende vote-UI ("Stem mig levende" + bar + rang).
- **VÅGEN**: statuslinje ("Ræv har det godt" / "Ræv er SULTEN!" hvis et behov < 25) +
  tre mini-bars (❤️🍖💧, avatarens accentfarve, rød-tint ved < 25) + tre mailto-knapper:
  "🍖 Giv mad" (subject "Mad til Ræv 🍖"), "💧 Giv vand", "❤️ Giv kærlighed".
- **SOVET IGEN**: "😴 Ræv er faldet i søvn igen… send en mail og væk hende" + én CTA.
- Kalender-banner: total-progress + top-3 + NYT: "kritisk sultne" advarsler
  ("⚠️ Ræv mangler vand!") — det er dét, der trækker folk tilbage dagligt.

## LinkedIn-vinkel

Daglige opdateringer skriver sig selv: "Ræv har ikke fået vand i 20 timer 💧 — hvem redder
hende?" Ansvarsfølelse + serialisering = follow-driver. (Uddybes i linkedin-eksperiment.md.)
