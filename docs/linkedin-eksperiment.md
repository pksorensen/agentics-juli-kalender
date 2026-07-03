# LinkedIn-eksperiment: Julikalenderen som follower-motor

**Formål:** Afgøre om kommentar→credit + mail→stemme-mekanikken på agentics.dk/julikalender
skaber **netto nye følgere** — ikke bare impressions. 31 dage, én mekanik, hårde tal.

---

## 1. Hypotese & KPI'er

**Hypotese:** En seriel 31-dages kampagne, hvor publikum *ejer udfaldet* (kommentarer funder
avatarerne, mails bestemmer rækkefølgen), konverterer engagement til følgere markant bedre end
almindelige posts — fordi der er en grund til at komme tilbage i morgen, og "følg" er den
naturlige måde at følge serien på.

Vigtigt realitetstjek fra research: virale impressions konverterer typisk kun ~0,1 % til følgere
([Michael Lin, 430k-impression post-mortem](https://www.michaellinwrites.com/p/aftermath-of-a-viral-430k-impression)).
Til gengæld viste et [30-dages challenge-eksperiment](https://zapier.com/blog/linkedin-challenge/)
en stigning fra 5–10 til 10–15+ nye følgere/dag under daglig serie-posting, og
[Growth In Reverse](https://growthinreverse.com/social-challenge-recap/) målte +14k følgere samlet
på tværs af deltagere på 30 dage. Serialisering er driveren — ikke enkeltpostens rækkevidde.

**Primær KPI:** Netto nye følgere pr. dag (mod baseline).
**Sekundære KPI'er:** kommentarer pr. post, mails/stemmer pr. dag, besøg på /julikalender,
antal gæt i modelspillet, profilvisninger.

**Baseline (obligatorisk, FØR launch):** Notér følgertal hver morgen kl. 09 i 7 dage før
launch-posten. Gennemsnittet = baseline netto følgere/dag. Uden baseline er eksperimentet værdiløst.

**Dagligt målepunkt-skema** (udfyldes kl. 09, tager 3 minutter):

| Dag | Dato | Følgere kl. 09 | Nye følgere (Δ) | Kommentarer i går | Mails/stemmer i går | Besøg /julikalender | Gæt i modelspil | Noter (post-type, demotion-tegn?) |
|-----|------|----------------|-----------------|-------------------|---------------------|---------------------|-----------------|-----------------------------------|
| -7…-1 | | | | — | — | | | baseline-uge |
| 1 | | | | | | | | launch |
| 2 | | | | | | | | Ræv-reveal |
| … | | | | | | | | |
| 31 | | | | | | | | finale |

Kilder til tallene: LinkedIn Analytics (følgere, impressions, profilvisninger), inbox-webhook
(stemmer), site-analytics (besøg + gæt).

---

## 2. Mekanik-design

### Hvorfor kommentar→credit + mail→stemme slår "like og del"

1. **Kommentarer er algoritmens stærkeste signal.** Kommentar-drevne posts får op til 8× mere
   rækkevidde end link-posts, og kommentar-*tråde* (svar frem og tilbage) udløser aggressiv
   reach-ekspansion — likes betyder næsten intet
   ([ConnectSafely](https://connectsafely.ai/articles/linkedin-lead-magnet-guide-2026),
   [meet-lea](https://meet-lea.com/en/blog/linkedin-algorithm-explained)).
2. **Kommentaren har en konsekvens i den virkelige verden.** "Din kommentar = 1 credit = en avatar
   kommer tættere på at blive levende" er en mikro-donation med synligt resultat. Det giver folk
   en grund til at skrive noget *ægte* — ikke bare "YES".
3. **Mail→stemme flytter halvdelen af engagementet UD af LinkedIn.** Stemmer via
   `<slug>@agent.agentics.dk` kan aldrig trigge LinkedIns bait-classifier, og de skaber en
   ejerskabsfølelse ("MIN avatar fører").
4. **Leaderboardet = vælg-din-favorit-konkurrence.** Progress bars + top-3 gør det til en
   fodboldkamp: folk vender tilbage dagligt for at se, om deres favorit stadig fører — og
   underdog-fortællinger ("kan nogen redde Boo?") er indbygget dagligt content.
5. **Modelspillet giver en anden grund til at klikke** end selve konkurrencen — det fanger
   AI-nysgerrige (Pouls ICP) frem for gratis-ting-jægere.

### Risiko: engagement-bait demotion — og afbødning

Research er entydig: LinkedIn er i 2025/26 gået fra at nedprioritere til aktivt at *undertrykke*
engagement bait. Fraser som "comment below", "tag a friend" og "comment YES" flagges af en
classifier, og distribution begrænses uanset kontohistorik
([Digital Applied](https://www.digitalapplied.com/blog/linkedin-algorithm-2026-engagement-strategy-guide),
[Hootsuite](https://blog.hootsuite.com/linkedin-algorithm/),
[Synergist](https://future.forem.com/synergistdigitalmedia/linkedins-2026-algorithm-the-engagement-bait-era-is-finally-over-68),
[Botdog](https://www.botdog.co/blog-posts/linkedin-algorithm-2025)). Direkte beder-om-likes/shares/follows straffes også.

**Afbødning (indbygget i alle post-udkast nedenfor):**

- **Stil et ægte spørgsmål** som postens afslutning: *"Hvilken avatar skal vækkes til live først —
  og hvorfor?"* Aldrig imperativer som "kommentér for at stemme".
- **Beskriv mekanikken som en aftale, ikke en opfordring:** "for hver kommentar veksler jeg 1 credit"
  er en beskrivelse af, hvad *Poul* gør — ikke en instruks til læseren. Grænsetilfælde, ja; men
  classifieren jagter imperativ-mønstre ("comment X if…"), ikke omtale af ordet.
- **Undgå imperativerne like/del/kommentér/tag/følg i post-teksten.** "Følg mig"-CTA'er hører til
  i *kommentarsporet og på profilen*, ikke i posten.
- **Svar på ALLE kommentarer inden for den første time** — svar-tråde er det stærkeste
  reach-signal, og det er umuligt at flagge som bait.
- **Link-disciplin:** skriv `agentics.dk/julikalender` som ren tekst (ingen preview-kort), og læg
  det klikbare link i første kommentar. Link-posts taber markant reach.
- **Demotion-alarm:** hvis en post har <30 % af normale impressions efter 2 timer, notér det i
  skemaet og omskriv mekanik-formuleringen i næste post.

---

## 3. Post-plan

**Kadence:** 1 launch-post (dag 1) + dagligt opfølgnings-format resten af juli:

> **Dagligt format (5–10 min at skrive):** ① Hook: dagens leaderboard-drama (fører/underdog).
> ② Dagens nye låge + én konkret teknisk detalje. ③ Modelspils-tease ("dagens hint: låge N er
> bygget af en model, der …"). ④ Ægte spørgsmål. ⑤ `agentics.dk/julikalender` som ren tekst.

De første 2 linjer afgør alt — det er dem, der vises før "…se mere". Hook først, kontekst bagefter.

### Udkast (a) — Launch-posten

> 31 låger. 31 AI-avatarer. Kun én af dem er i live.
>
> I juli har jeg bygget en julekalender på agentics.dk — 31 karakterer, hver tegnet af en
> Claude-model. (Der er et indbygget spil, hvor man gætter hvilken model der byggede hvilken.
> Det er sværere, end det lyder.)
>
> Låge 2 — Ræv — er nu en ægte AI-video-avatar: karakter-still fra Higgsfield GPT Image 2,
> animeret med Seedance 2.0. Pris: ca. 80 credits, omkring 30 kroner.
>
> De andre 29 står stadig stille. Så jeg har lavet en aftale med mig selv:
>
> For hver kommentar på det her opslag lægger jeg 1 credit i puljen. Puljen betaler for at vække
> de næste avatarer til live — og rækkefølgen bestemmer I: én tom mail til fx
> raev@agent.agentics.dk tæller som én stemme. Live leaderboard på sitet.
>
> Mit ærlige spørgsmål: hvilken avatar fortjener at blive levende først — og hvorfor lige den?
>
> Kalenderen og leaderboardet: agentics.dk/julikalender

### Udkast (b) — Dag 2: Ræv-reveal

> Min første AI-video-avatar kostede 30 kroner og ét mislykket forsøg.
>
> Sådan gjorde jeg — hele workflowet:
>
> 1. Karakter-still: Higgsfield GPT Image 2. Prompten beskriver personlighed, ikke kun udseende —
>    det er dét, der gør, at Ræv *ligner sig selv* og ikke en generisk tegneserieræv.
> 2. Image-to-video: Seedance 2.0, kort loop hvor han vågner.
> 3. Re-encode til all-intra, så videoen kan scrubbes med scroll — avataren vågner i takt med,
>    at man ruller ned ad siden.
>
> Det svære var ikke værktøjerne. Det var at få videoen til at matche den SVG-figur, en
> Claude-model oprindeligt tegnede. Første forsøg lignede en helt anden ræv.
>
> Ræv er låge 2 af 31. Hvem der bliver nummer to afgøres af leaderboardet — lige nu fører [X].
>
> Døm selv, om han ligner: agentics.dk/julikalender

### Udkast (c) — Leaderboard/battle-opdatering

> [Ugla] fører med [47] stemmer. [Boo] er [6] bag. Det her var ikke planen.
>
> Status på julikalenderen, dag [N]:
>
> – [X] kommentarer er blevet til [X] credits i puljen — nok til [Y] nye video-avatarer
> – [Z] stemmer er landet i indbakken, fordelt på [W] forskellige avatarer
> – Top 3: [A], [B], [C]
>
> Den avatar, der fører ved midnat, er den næste, der bliver til AI-video. Jeg poster resultatet
> i morgen — inklusive hvad Seedance gør ved [A]s ører.
>
> Til jer i model-gættelegen: dagens hint — låge [N] er bygget af en model med en svaghed for
> gradients.
>
> Er der nogen derude, der kan redde [underdog]? Én mail til [slug]@agent.agentics.dk tæller som
> én stemme.
>
> agentics.dk/julikalender

---

## 4. Followers-konvertering

Impressions bliver ikke til følgere af sig selv (~0,1 % uden aktiv konvertering —
[Michael Lin](https://www.michaellinwrites.com/p/aftermath-of-a-viral-430k-impression)). Konkrete greb:

1. **Svar-med-værdi på hver kommentar** inden for 1. time: et teknisk detalje-svar ("Seedance
   fejler sjovt nok altid på halen — her er min workaround") gør svarerne selv følgeværdige og
   fodrer tråd-signalet.
2. **Profil som landing page:** headline = "Bygger 31 AI-video-avatarer i juli — én om dagen",
   featured-sektion = julikalender-link + Ræv-video. Profilvisninger fra virale posts konverterer
   kun, hvis profilen forklarer, hvad man følger *for*
   ([Supergrow](https://www.supergrow.ai/blog/how-to-get-your-first-1000-followers-on-linkedin)).
3. **"I morgen"-narrativ i hver post:** afslut altid med en cliffhanger ("resultatet i morgen").
   Serialisering er follow-driveren — man følger for ikke at misse dag N+1
   ([PostEverywhere](https://posteverywhere.ai/blog/how-to-go-viral-on-linkedin)).
4. **Følg-CTA i kommentarsporet, ikke i posten:** pin en egen kommentar med det klikbare link +
   "jeg poster leaderboard-status hver morgen her på profilen". Det er CTA'en — uden bait-ord i
   selve posten.
5. **Tag-kultur (organisk, aldrig opfordret):** når nogen tagger en kollega ("det her er dig"),
   svar personligt og hurtigt — det er gratis distribution til et nyt netværk.
6. **DM-flow:** alle der stemmer/kommenterer flere gange får én personlig DM: "Din favorit vandt —
   den går live i morgen kl. 9. Tak for at være med." Ingen pitch. Varme DM'er → connection →
   follower → (senere) kunde.
7. **Ugentlig behind-the-scenes:** én post/uge om *hvordan* (webhook-arkitekturen, credits-økonomien,
   modelspillet) fanger dem, der følger for det agentiske — Pouls egentlige marked.

---

## 5. Tidsplan & budget

**Tidsplan (juli = naturlig 31-dages serie):**

| Fase | Dage | Indhold |
|------|------|---------|
| Baseline | -7 til 0 | Mål følgere dagligt. Klargør profil, webhook-test, leaderboard live |
| Launch | 1–2 | Udkast (a), dagen efter udkast (b) Ræv-reveal |
| Rytme | 3–27 | Dagligt format; battle-post (c) 2–3×/uge; behind-the-scenes 1×/uge |
| Midtvejs | ~15 | Halvvejs-status: tal, læringer, største overraskelse |
| Finale | 28–31 | Nedtælling, sidste avatar vækkes, samlet post-mortem med alle tal |

**Credits-budget** (100 credits ≈ 1 avatar ≈ 30–33 kr; 4000-credit-pakke = 190 USD ≈ 1.330 kr):

| Kommentarer | Credits | Avatarer vækket | Pris ca. |
|-------------|---------|-----------------|----------|
| 100 | 100 | 1 | ~33 kr |
| 500 | 500 | 5 | ~165 kr |
| 1.000 | 1.000 | 10 | ~330 kr |
| Loft: alle 29 | ~2.900 | 29 | ~870 kr — rigeligt dækket af én 4000-credit-pakke |

Worst case-økonomien er altså ~870 kr + genforsøg (budgettér 4000 credits i alt = 190 USD).
Det er billigere end én LinkedIn-annonce — hele risikoen ligger i tid, ikke penge.

---

## 6. Eksperiment-integritet

**Hypotesen er falsificeret hvis:** efter 14 dage er netto følgere/dag ≤ baseline (eller
< 2× baseline, hvis baseline er nær nul), *selvom* kommentarer og impressions er steget markant.
Det ville betyde: mekanikken skaber engagement-teater, ikke publikum.

**Stop-/pivot-kriterier:**

- **Demotion:** 2 posts i træk med <30 % af normal reach efter 2 timer → drop al mekanik-omtale i
  posten; flyt den 100 % til site + pinned kommentar.
- **Spam:** >25 % af kommentarer er indholdsløse ("!", emoji-spam) → credits gælder kun
  kommentarer med et *hvorfor*. Annoncér ændringen åbent — det er i sig selv en god post.
- **Tid:** dagligt format tager >45 min/dag i to uger → skift til 3–4 posts/uge (research viser
  at 3–5/uge er nok: [Zapier](https://zapier.com/blog/linkedin-challenge/)).
- **Budget:** hårdt loft på 4000 credits. Punktum.

**Hvad vi lærer, selv hvis det flopper:**

- Et tal for *vores* impressions→follower-konvertering — genbrugeligt i al fremtidig content.
- Om mail-som-stemme fungerer som friktionsfri off-platform-mekanik (genbrugeligt til
  SminkepigerneDK-akademiet og kundecases: "inbox-webhook som produkt").
- Hvilke post-typer (reveal / battle / behind-the-scenes) der driver hvilken KPI — dag-for-dag-data.
- En offentlig post-mortem med ægte tal er i sig selv en troværdigheds-post for agentics.dk.

---

## Launch-tjekliste (10 punkter)

1. [ ] 7 dages baseline-følgertal noteret i skemaet (afsnit 1).
2. [ ] Inbox-webhook testet: mail til `raev@agent.agentics.dk` tæller synligt på leaderboardet.
3. [ ] Leaderboard + progress bars live på agentics.dk/julikalender, tjekket på mobil.
4. [ ] Modelspillet virker, og der ligger 3–4 hints klar til de første battle-posts.
5. [ ] Profil opdateret: headline med juli-serien, featured-link til kalenderen, Ræv-video.
6. [ ] Launch-post (a) og Ræv-post (b) skrevet færdig; bait-ord tjekket ud af teksten.
7. [ ] Pinned-kommentar klar: klikbart link + "leaderboard-status hver morgen her på profilen".
8. [ ] 4000-credit-pakke købt (190 USD) — hårdt loft bekræftet.
9. [ ] Kalenderblok 60 min hver morgen i juli: post kl. 8–9 + svar på alt inden for 1. time.
10. [ ] Målepunkt-skemaet ligger klar (kopiér tabellen til et ark), inkl. demotion-alarmen fra afsnit 2.
