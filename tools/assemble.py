#!/usr/bin/env python3
# Assembles the agentics.dk "juli" avatar advent calendar:
#  - injects uniform story chrome into all 31 day pages (day-1..31.html)
#  - generates calendar.html (date-locked 31-door grid)
# Usage: python3 assemble.py <workflow_task_output.json>
import sys, json, html, re, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# single source of truth for the vote-campaign block — tools/inject_vote_block.py
# patches existing day pages in place; we import the exact same builders here so
# a future FULL regeneration produces byte-identical vote markup.
from inject_vote_block import VOTE_CSS, VOTE_ROSTER, vote_block

DIR = "/home/claude-desktop/experiments/animated-avatar"

# day -> (name, emoji, accent, source_file_or_None[in-place day-N.html])
ROSTER = {
 1:("AURA","🔮","#38e6ff","concept-a.html"),
 2:("Ræv","🦊","#ff9a3d","concept-b.html"),
 3:("Agent-01","🤖","#5eead4","index.html"),
 4:("Nova","🫧","#ff5cc8","round2-01-nova.html"),
 5:("Comet","👨‍🚀","#ff7a3d","round2-02-comet.html"),
 6:("Boo","👻","#c8b6ff","round2-03-boo.html"),
 7:("Neko","🐱","#ff8a3d","round2-04-neko.html"),
 8:("Tsuru","🕊️","#b83b2e","round2-05-tsuru.html"),
 9:("Bit","👾","#00f0c8","round2-06-bit.html"),
 10:("Lumen","🪼","#3ff0d8","round2-07-lumen.html"),
 11:("Ugla","🦉","#ffb45a","round2-08-ugla.html"),
 12:("Chrome","🪞","#c8b6ff","round2-09-chrome.html"),
 13:("Ember","🔥","#ff7a18","round2-10-ember.html"),
 14:("Koi","🐟","#4aa8ff",None),
 15:("Golem","🗿","#9fb0a0",None),
 16:("Sprout","🌱","#6ee07a",None),
 17:("Draco","🐉","#ff5a3c",None),
 18:("Aster","✨","#b98cff",None),
 19:("Lundi","🐦","#ff8a4a",None),
 20:("Mochi","🍡","#ffb3d1",None),
 21:("Volt","⚡","#ffe14a",None),
 22:("Prism","💎","#7ad0ff",None),
 23:("Nimbus","☁️","#bcd3ff",None),
 24:("Ravn","🐦‍⬛","#8a7dff",None),
 25:("Cog","⚙️","#d0a24a",None),
 26:("Frost","❄️","#9fe8ff",None),
 27:("Beacon","🗼","#ffd24a",None),
 28:("Sol","☀️","#ffb02e",None),
 29:("Luna","🌙","#c0c8ff",None),
 30:("Bi","🐝","#ffcf33",None),
 31:("Vega","🚀","#ff7a3d",None),
}

# ground truth for the "guess the model" game — days 1-13 all truthfully built on Opus 4.8
# (this whole session ran on Opus 4.8 until the mid-session /model switch); days 14-31 were
# built with an EXPLICIT forced model param per avatar (see juli-calendar-mixed-model workflow),
# guaranteeing real, verifiable ground truth rather than "whatever happened to be active".
MODEL = {d: "opus" for d in range(1, 14)}
MODEL.update({
    14: "opus", 15: "sonnet", 16: "sonnet", 17: "opus", 18: "sonnet",
    19: "opus", 20: "sonnet", 21: "opus", 22: "sonnet", 23: "opus",
    24: "sonnet", 25: "opus", 26: "opus", 27: "sonnet", 28: "opus",
    29: "sonnet", 30: "opus", 31: "sonnet",
})
MODEL_LABEL = {"opus": "Claude Opus 4.8", "sonnet": "Claude Sonnet 5"}

# ---- args: optional workflow-output path + --calendar-only (skip re-injecting chrome into
#      day-N.html, since those files are ALSO the injection target — re-running inject() on
#      an already-injected file would double-append the chrome block) ----
CALENDAR_ONLY = "--calendar-only" in sys.argv
pos_args = [a for a in sys.argv[1:] if not a.startswith("--")]

# ---- load stories from workflow output ----
stories = {}
if pos_args:
    raw = open(pos_args[0]).read()
    try:
        data = json.loads(raw)
    except Exception:
        i = raw.find('{'); data = json.loads(raw[i:])
    st = (data.get("result") or data).get("stories") or {}
    for k, v in st.items():
        stories[int(k)] = v

def story_for(day):
    s = stories.get(day) or {}
    name = ROSTER[day][0]
    return (
        s.get("tagline") or "En agent i agentics.dk-holdet",
        s.get("lore") or f"{name} er en del af agentics.dk's agent-hold — en lille autonom karakter med sit helt eget temperament.",
        s.get("tags") or ["agentisk","autonom","dansk"],
    )

CHROME = """
<style id="agx-chrome-css">
.agx{position:fixed;z-index:2147483000;font-family:-apple-system,"Segoe UI",Inter,system-ui,sans-serif;box-sizing:border-box}
.agx a{cursor:pointer}
.agx-badge{right:16px;bottom:16px;display:flex;gap:7px;align-items:center;padding:8px 13px;border-radius:999px;
  background:rgba(9,11,17,.55);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);
  border:1px solid rgba(255,255,255,.13);color:#eef1f7;font-size:11px;letter-spacing:.16em;text-transform:uppercase;font-weight:600}
.agx-badge b{color:var(--agx);font-size:13px}
.agx-story{left:16px;bottom:16px;max-width:min(360px,calc(100vw - 32px));padding:16px 16px 13px;border-radius:16px;
  background:rgba(9,11,17,.62);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);
  border:1px solid rgba(255,255,255,.13);color:#eef1f7;box-shadow:0 24px 70px -26px rgba(0,0,0,.85)}
.agx-story .h{display:flex;align-items:center;gap:11px;margin-bottom:9px}
.agx-story .em{font-size:26px;line-height:1;filter:drop-shadow(0 3px 11px var(--agx))}
.agx-story .nm{font-size:17px;font-weight:700;letter-spacing:-.01em;line-height:1.1}
.agx-story .tl{color:var(--agx);font-size:12px;font-weight:600;margin-top:3px}
.agx-story p{margin:0 0 11px;color:#c6ccd9;font-size:13px;line-height:1.56}
.agx-tags{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:12px}
.agx-tags span{font-size:10.5px;letter-spacing:.09em;text-transform:uppercase;color:#aeb6c6;
  border:1px solid rgba(255,255,255,.15);border-radius:999px;padding:3px 9px}
__VOTECSS__.agx-guess{margin:0 0 12px;padding-top:11px;border-top:1px solid rgba(255,255,255,.09)}
.agx-guess .gq{font-size:11.5px;color:#aeb6c6;margin-bottom:8px;letter-spacing:.01em}
.agx-guess .gbtns{display:flex;gap:8px}
.agx-guess .gbtn{flex:1;padding:8px 8px;border-radius:10px;border:1px solid rgba(255,255,255,.15);
  background:rgba(255,255,255,.03);color:#eef1f7;font-size:12px;font-weight:600;cursor:pointer;
  transition:transform .15s,border-color .15s,background .15s,opacity .15s;font-family:inherit}
.agx-guess .gbtn:hover:not(:disabled){border-color:var(--agx);background:rgba(255,255,255,.07);transform:translateY(-1px)}
.agx-guess .gbtn:focus-visible{outline:2px solid var(--agx);outline-offset:2px}
.agx-guess .gbtn:disabled{cursor:default}
.agx-guess .gbtn.correct{border-color:#5eea8f;background:rgba(94,234,143,.16);color:#a4f5be;opacity:1}
.agx-guess .gbtn.wrong{border-color:#ff6a6a;background:rgba(255,106,106,.14);color:#ffb9b9;opacity:1}
.agx-guess .gbtn.dim{opacity:.45}
.agx-guess .greveal{margin-top:9px;font-size:11.5px;line-height:1.55;color:#c6ccd9}
.agx-guess .greveal b{color:#eef1f7}
.agx-nav{display:flex;align-items:center;gap:13px;font-size:12.5px;border-top:1px solid rgba(255,255,255,.09);padding-top:11px}
.agx-nav a{color:#eef1f7;text-decoration:none;opacity:.82}
.agx-nav a:hover{opacity:1;color:var(--agx)}
.agx-nav .home{margin-right:auto;font-weight:600}
.agx-nav a[aria-disabled=true]{opacity:.32;pointer-events:none}
@media (max-width:560px){.agx-story{left:12px;right:12px;bottom:12px;max-width:none}.agx-badge{display:none}}
@media (prefers-reduced-motion:reduce){.agx-story .em{filter:none}}
</style>
<div class="agx agx-badge" style="--agx:__ACC__">AGENTICS · JULI <b>__DD__</b></div>
<aside class="agx agx-story" style="--agx:__ACC__" aria-label="Avatarens historie">
  <div class="h"><div class="em">__EMOJI__</div><div><div class="nm">__NAME__</div><div class="tl">__TAGLINE__</div></div></div>
  <p>__LORE__</p>
  <div class="agx-tags">__TAGS__</div>
__VOTE__
  <div class="agx-guess" id="agxGuess">
    <div class="gq">🤖 Hvilken Claude-model byggede __NAME__?</div>
    <div class="gbtns">
      <button type="button" class="gbtn" data-m="opus">Opus 4.8</button>
      <button type="button" class="gbtn" data-m="sonnet">Sonnet 5</button>
    </div>
    <div class="greveal" id="agxReveal" hidden></div>
  </div>
  <nav class="agx-nav">
    <a class="home" href="calendar.html">← Kalender</a>
    __PREV__
    __NEXT__
  </nav>
</aside>
<script>(function(){var n=document.querySelector('.agx-nav a[data-day]');if(!n)return;var d=+n.getAttribute('data-day');
if(new Date()<new Date(2026,6,d)){n.setAttribute('aria-disabled','true');n.textContent='næste (åbner '+d+'. juli)';}})();</script>
<script>(function(){
  var DAY=__DAYNUM__, MODEL='__MODEL__', NAME='__NAMEJS__';
  var KEY='agx_guess_'+DAY;
  var wrap=document.getElementById('agxGuess');
  if(!wrap) return;
  var btns=Array.prototype.slice.call(wrap.querySelectorAll('.gbtn'));
  var reveal=document.getElementById('agxReveal');
  var TXT={
    opus:'🧠 Rigtigt svar: <b>Claude Opus 4.8</b> byggede '+NAME+'.',
    sonnet:'⚡ Rigtigt svar: <b>Claude Sonnet 5</b> byggede '+NAME+'.'
  };
  function render(saved){
    btns.forEach(function(b){
      b.disabled=true;
      var m=b.getAttribute('data-m');
      if(m===MODEL) b.classList.add('correct');
      else if(m===saved) b.classList.add('wrong'); else b.classList.add('dim');
    });
    var extra = saved===MODEL ? ' Du gættede rigtigt! 🎉' : ' Forkert gæt denne gang — bedre held i morgen.';
    reveal.innerHTML=TXT[MODEL]+extra;
    reveal.hidden=false;
  }
  var prior=localStorage.getItem(KEY);
  if(prior){ render(prior); return; }
  btns.forEach(function(b){
    b.addEventListener('click', function(){
      var g=b.getAttribute('data-m');
      try{ localStorage.setItem(KEY, g); }catch(e){}
      render(g);
    });
  });
})();</script>
"""

def inject(day):
    name, emoji, acc, src = ROSTER[day]
    tagline, lore, tags = story_for(day)
    srcpath = f"{DIR}/{src}" if src else f"{DIR}/day-{day}.html"
    doc = open(srcpath, encoding="utf-8").read()
    tags_html = "".join(f"<span>{html.escape(str(t))}</span>" for t in tags[:3])
    prev = (f'<a href="day-{day-1}.html">‹ forrige</a>' if day > 1
            else '<a aria-disabled="true">‹ forrige</a>')
    nxt = (f'<a data-day="{day+1}" href="day-{day+1}.html">næste ›</a>' if day < 31
           else '<a aria-disabled="true">finale 🎉</a>')
    name_js = json.dumps(name)  # safe JS string literal, handles æøå/quotes
    chrome = (CHROME.replace("__ACC__", acc).replace("__DD__", f"{day:02d}")
              .replace("__EMOJI__", emoji).replace("__NAME__", html.escape(name))
              .replace("__TAGLINE__", html.escape(tagline)).replace("__LORE__", html.escape(lore))
              .replace("__TAGS__", tags_html).replace("__PREV__", prev).replace("__NEXT__", nxt)
              .replace("__DAYNUM__", str(day)).replace("__MODEL__", MODEL[day])
              .replace("'__NAMEJS__'", name_js)
              .replace("__VOTECSS__", VOTE_CSS).replace("__VOTE__", vote_block(day)))
    if "</body>" in doc:
        doc = doc.replace("</body>", chrome + "\n</body>", 1)
    else:
        doc = doc + chrome
    open(f"{DIR}/day-{day}.html", "w", encoding="utf-8").write(doc)

# ---- build all 31 day pages ----
if not CALENDAR_ONLY:
    made = []
    for d in range(1, 32):
        try:
            inject(d); made.append(d)
        except FileNotFoundError:
            print(f"  ! missing source for day {d}: {ROSTER[d][3]}")
    print(f"injected chrome into {len(made)}/31 day pages")
else:
    print("--calendar-only: skipped day-page injection")

# ---- calendar.html ----
# every avatar's art/name is always shown; only the CLICK-THROUGH to day-N.html is date-gated
# (see the calendar's inline script) — visitors browse the whole cast, but can't open the story
# page until its day arrives.
# LIVE days (avatars already awakened as real AI-video) are detected at BUILD TIME by the
# presence of assets/day-N/poster.jpg on disk — their tile renders the poster as cover art
# with a scrim, a pulsing "● LEVENDE" badge and a soft glow ring. Runtime refinement from
# api/votes (asleep_again badge, hunger chip) happens in the calendar's vote script.
LIVE_DAYS = {d for d in range(1, 32) if os.path.exists(f"{DIR}/assets/day-{d}/poster.jpg")}
DAY_SLUG = {d: VOTE_ROSTER[d][0] for d in range(1, 32)}

def door_html(d):
    name, emoji, acc, _ = ROSTER[d]
    slug = DAY_SLUG[d]
    if d in LIVE_DAYS:
        return f'''    <a class="door live" data-day="{d}" data-slug="{slug}" data-live="1" style="--c:{acc}" aria-label="Dag {d} — {html.escape(name)} (levende AI-video-avatar)">
      <span class="cover" style="background-image:url('assets/day-{d}/poster.jpg')"></span>
      <span class="scrim"></span>
      <span class="corner">{d:02d}</span>
      <span class="lockbadge" aria-hidden="true">🔒</span>
      <span class="livebadge"><i class="ld"></i>LEVENDE</span>
      <span class="hungry" hidden>⚠️ Sulten</span>
      <span class="lmeta"><span class="nm">{html.escape(name)}</span><span class="dag">Dag {d} · ægte AI-video</span></span>
    </a>'''
    return f'''    <a class="door" data-day="{d}" data-slug="{slug}" style="--c:{acc}" aria-label="Dag {d} — {html.escape(name)}">
      <span class="corner">{d:02d}</span>
      <span class="lockbadge" aria-hidden="true">🔒</span>
      <span class="poster">
        <span class="em">{emoji}</span>
        <span class="nm">{html.escape(name)}</span>
        <span class="dag">Dag {d}<span class="when"> · åbner {d}. juli</span></span>
      </span>
    </a>'''

# four door groups interleaved with the three story sections (koncept/vaekning/feeding)
GROUPS = [(1, 8), (9, 16), (17, 24), (25, 31)]
doors_by_group = ["\n".join(door_html(d) for d in range(a, b + 1)) for a, b in GROUPS]

CAL = r"""<!doctype html>
<html lang="da">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>agentics.dk · Julikalenderen 2026</title>
<style>
  :root{--bg:#06070b;--ink:#eef1f7;--dim:#8b93a7;--line:#1a2030;--card:#0e1119;--accent:#5eead4;--ease:cubic-bezier(.2,.7,.2,1)}
  *{box-sizing:border-box}
  [hidden]{display:none!important}
  html{scroll-behavior:smooth}
  html,body{margin:0;background:var(--bg);color:var(--ink);
    font-family:-apple-system,"Segoe UI",Inter,system-ui,sans-serif;-webkit-font-smoothing:antialiased}
  body{min-height:100vh;position:relative;overflow-x:hidden;padding-bottom:56px;
    background:
     radial-gradient(1100px 640px at 82% -6%, rgba(94,234,212,.13), transparent 60%),
     radial-gradient(900px 560px at -8% 26%, rgba(184,166,255,.09), transparent 60%),
     radial-gradient(1000px 620px at 108% 64%, rgba(255,154,210,.07), transparent 60%),
     var(--bg)}
  .grain{position:fixed;inset:0;pointer-events:none;opacity:.05;z-index:0;mix-blend-mode:overlay;
    background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")}
  .wrap{max-width:1140px;margin:0 auto;padding:0 clamp(18px,4vw,48px);position:relative;z-index:1}
  /* ---- scroll-reveals (én gang; prefers-reduced-motion => ingen) ---- */
  .rv{opacity:0;transform:translateY(28px);transition:opacity .85s var(--ease),transform .85s var(--ease)}
  .rv.in{opacity:1;transform:none}
  .hero .rv:nth-child(2){transition-delay:.08s}
  .hero .rv:nth-child(3){transition-delay:.16s}
  .hero .rv:nth-child(4){transition-delay:.24s}
  .points .rv:nth-child(2){transition-delay:.09s}
  .points .rv:nth-child(3){transition-delay:.18s}
  /* ---- hero ---- */
  .hero{padding:clamp(84px,15vh,160px) 0 clamp(20px,3vw,32px);text-align:center}
  .kicker{letter-spacing:.34em;text-transform:uppercase;font-size:12px;color:var(--accent);font-weight:600}
  h1{font-size:clamp(44px,7vw,88px);line-height:1.04;margin:.3em auto .26em;letter-spacing:-.035em;font-weight:760}
  h1 .g{background:linear-gradient(92deg,#5eead4,#b8a6ff 55%,#ff9ad2);-webkit-background-clip:text;background-clip:text;color:transparent}
  .sub{color:var(--dim);font-size:clamp(16px,2vw,20px);max-width:56ch;line-height:1.62;margin:0 auto}
  /* ---- economy strip (1 like = 1 credit · …) ---- */
  .econ{display:flex;flex-wrap:wrap;justify-content:center;gap:10px;margin:30px auto 0}
  .econ span{padding:8px 15px;border-radius:999px;border:1px solid var(--line);background:rgba(255,255,255,.02);
    font-size:13px;font-weight:600;color:var(--ink);white-space:nowrap}
  .econ b{color:var(--accent);font-weight:700}
  /* ---- slim status bar ---- */
  .status{margin:28px 0 4px;display:flex;flex-wrap:wrap;align-items:center;justify-content:center;gap:10px;font-size:13.5px;color:var(--dim)}
  .status .pill{display:inline-flex;align-items:center;gap:8px;padding:7px 14px;border-radius:999px;
    border:1px solid var(--line);background:rgba(255,255,255,.02);color:var(--ink);font-weight:600}
  .status .dot{width:8px;height:8px;border-radius:50%;background:var(--accent);box-shadow:0 0 12px var(--accent)}
  .status .pill.game{display:none;border-color:color-mix(in srgb,#b98cff 45%,var(--line));color:#e3d9ff}
  .status .pill.game .dot{background:#b98cff;box-shadow:0 0 12px #b98cff}
  .status .pill.votes{border-color:color-mix(in srgb,#ff9ad2 40%,var(--line));color:#ffdcee}
  .status .pill.votes .dot{background:#ff9ad2;box-shadow:0 0 12px #ff9ad2}
  .status .pill.preview{border-color:color-mix(in srgb,#ffb45a 45%,var(--line));color:#ffe3c2}
  .status .pill.preview a{color:inherit;text-decoration:underline;text-underline-offset:2px}
  .status .hint{width:100%;text-align:center;font-size:12.5px;color:#5a627a;margin-top:2px}
  /* ---- door groups: FIXED 4 columns desktop (a group = exactly 2 rows), 2 below 720px ---- */
  .ggroup{margin:clamp(34px,5vw,56px) 0 0}
  .glabel{font-size:11.5px;letter-spacing:.26em;text-transform:uppercase;color:#5a627a;font-weight:700;margin:0 0 14px 4px}
  .grid{display:grid;grid-template-columns:repeat(4,1fr);gap:clamp(12px,1.6vw,18px)}
  .door{position:relative;aspect-ratio:1/1;border-radius:20px;overflow:hidden;text-decoration:none;color:inherit;
    background:linear-gradient(180deg,var(--card),#0a0d13);border:1px solid var(--line);
    display:flex;align-items:center;justify-content:center;cursor:default;
    filter:saturate(.4) brightness(.68);
    transition:transform .28s var(--ease),border-color .28s,box-shadow .28s,filter .28s}
  .door .corner{position:absolute;top:12px;left:14px;font-size:12px;font-weight:700;color:var(--dim);letter-spacing:.04em;z-index:2}
  .door::after{content:"";position:absolute;top:0;left:0;right:0;height:2px;background:var(--c);opacity:.3;transition:opacity .28s}
  .door:hover{filter:saturate(.6) brightness(.75);border-color:color-mix(in srgb,var(--c) 35%,var(--line))}
  /* lock badge — shown until the door is actually open */
  .door .lockbadge{position:absolute;top:10px;right:10px;z-index:2;width:26px;height:26px;border-radius:50%;
    display:flex;align-items:center;justify-content:center;font-size:11px;
    background:rgba(6,7,11,.6);border:1px solid rgba(255,255,255,.14);backdrop-filter:blur(6px)}
  .door.open .lockbadge{display:none}
  /* poster — the avatar's art/name, always shown (desaturated via the tile filter when locked) */
  .door .poster{display:flex;flex-direction:column;align-items:center;gap:7px;text-align:center;padding:12px;z-index:1}
  .door .poster .em{font-size:clamp(40px,5vw,64px);line-height:1;filter:drop-shadow(0 6px 18px var(--c))}
  .door .poster .nm{font-size:16px;font-weight:700;letter-spacing:-.01em}
  .door .poster .dag{font-size:11px;color:var(--dim);letter-spacing:.06em;text-transform:uppercase}
  .door .poster .when{text-transform:none;letter-spacing:normal;color:#7a8299}
  .door.open .poster .when{display:none}
  .door.open .poster .em{animation:float 4.5s ease-in-out infinite}
  .door.open{cursor:pointer;filter:none}
  .door.open .corner{color:var(--ink)}
  .door.open::after{opacity:1;box-shadow:0 0 16px var(--c)}
  .door.open:hover{transform:translateY(-5px);border-color:color-mix(in srgb,var(--c) 60%,transparent);
    box-shadow:0 26px 60px -24px var(--c)}
  .door.open::before{content:"";position:absolute;inset:0;background:radial-gradient(160px 120px at 50% 30%,color-mix(in srgb,var(--c) 22%,transparent),transparent 70%);opacity:0;transition:opacity .3s}
  .door.open:hover::before{opacity:1}
  /* preview-unlocked (operator only): still clearly marked apart from a REAL open day */
  .door.open.preview{border-style:dashed}
  .door.open.preview .lockbadge{display:flex;background:rgba(94,234,212,.16);border-color:color-mix(in srgb,var(--c) 55%,transparent)}
  /* today */
  .door.today{border-color:color-mix(in srgb,var(--c) 70%,transparent);box-shadow:0 0 0 1px color-mix(in srgb,var(--c) 45%,transparent),0 22px 55px -26px var(--c)}
  .door.today .ribbon{position:absolute;top:10px;right:10px;z-index:3;font-size:10px;font-weight:800;letter-spacing:.12em;
    background:var(--c);color:#07080c;padding:4px 9px;border-radius:999px}
  .door:focus-visible{outline:2px solid var(--c);outline-offset:3px}
  /* ---- LIVE tiles: awakened AI-video avatars (build-time poster.jpg) ---- */
  .door.live .cover{position:absolute;inset:0;background-size:cover;background-position:center;transition:transform .6s var(--ease)}
  .door.live .scrim{position:absolute;inset:0;background:linear-gradient(180deg,rgba(4,6,10,0) 34%,rgba(4,6,10,.82) 100%)}
  .door.live{border-color:color-mix(in srgb,var(--c) 55%,transparent);
    box-shadow:0 0 0 1px color-mix(in srgb,var(--c) 38%,transparent),0 0 44px -10px var(--c),0 26px 70px -30px var(--c)}
  .door.live.open:hover .cover{transform:scale(1.05)}
  .door.live .corner{color:#fff;text-shadow:0 1px 6px rgba(0,0,0,.6)}
  .door.live .lockbadge{display:none}
  .door.live .livebadge{position:absolute;top:10px;right:10px;z-index:2;display:inline-flex;align-items:center;gap:6px;
    font-size:10px;font-weight:800;letter-spacing:.14em;padding:5px 10px;border-radius:999px;color:var(--c);
    background:rgba(4,6,10,.55);border:1px solid color-mix(in srgb,var(--c) 55%,transparent);backdrop-filter:blur(6px)}
  .door.live .livebadge .ld{width:6px;height:6px;border-radius:50%;background:var(--c);box-shadow:0 0 10px var(--c);
    animation:blink 1.7s ease-in-out infinite}
  .door.live .livebadge.asleep{color:#c3c9d8;border-color:rgba(255,255,255,.2);letter-spacing:.04em}
  .door.live .hungry{position:absolute;top:44px;right:10px;z-index:2;font-size:10.5px;font-weight:700;color:#ffd9c2;
    border:1px solid rgba(255,138,74,.55);background:rgba(20,10,4,.6);border-radius:999px;padding:4px 9px;backdrop-filter:blur(6px)}
  .door.live .lmeta{position:absolute;left:14px;right:14px;bottom:12px;z-index:1;display:flex;flex-direction:column;gap:3px;text-align:left;min-width:0}
  .door.live .lmeta .nm{font-size:17px;font-weight:750;letter-spacing:-.01em;text-shadow:0 1px 8px rgba(0,0,0,.7);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .door.live .lmeta .dag{font-size:10.5px;color:#c9d0e0;letter-spacing:.08em;text-transform:uppercase;text-shadow:0 1px 6px rgba(0,0,0,.7);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .door.live .ribbon{top:auto;bottom:12px;right:12px}
  .door.live.today .lmeta{right:88px}
  .door.resleep{filter:saturate(.45) brightness(.72);box-shadow:none;border-color:var(--line)}
  /* ---- story sections ---- */
  .sec{padding:clamp(90px,11vw,132px) 0 clamp(70px,8vw,100px);--a:var(--accent)}
  #vaekning{--a:#b8a6ff}
  #feeding{--a:#ff9ad2}
  .sec .eyebrow{letter-spacing:.3em;text-transform:uppercase;font-size:12px;color:var(--a);font-weight:700;text-align:center}
  .sec h2{font-size:clamp(32px,4.6vw,56px);line-height:1.06;letter-spacing:-.03em;font-weight:750;margin:16px auto 22px;max-width:680px;text-align:center}
  .sec .body{max-width:640px;margin:0 auto;text-align:center}
  .sec .body p{color:var(--dim);font-size:clamp(16px,1.9vw,19px);line-height:1.66;margin:0 0 1.15em}
  .sec .body p:last-child{margin-bottom:0}
  .sec .body b{color:var(--ink);font-weight:650}
  .points{max-width:1000px;margin:48px auto 0;display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
  .pt{background:linear-gradient(180deg,rgba(255,255,255,.028),rgba(255,255,255,.008));border:1px solid var(--line);
    border-radius:22px;padding:28px 26px 26px;text-align:left}
  .pt .pe{font-size:30px;line-height:1}
  .pt h3{font-size:16px;font-weight:700;letter-spacing:-.01em;margin:16px 0 8px}
  .pt p{font-size:13.5px;color:var(--dim);line-height:1.62;margin:0}
  /* ---- runtime panels (leaderboard + needs) — hidden uden API ---- */
  .panel{max-width:680px;margin:44px auto 0;padding:24px 24px 22px;border-radius:22px;border:1px solid var(--line);
    background:linear-gradient(180deg,rgba(255,255,255,.03),rgba(255,255,255,.01));text-align:left}
  .panel .p-t{font-size:11.5px;letter-spacing:.22em;text-transform:uppercase;color:var(--a);font-weight:700;margin-bottom:12px}
  .lbrow{display:flex;align-items:center;gap:12px;padding:8px 0;font-size:14px}
  .lbrow .rk{width:22px;height:22px;border-radius:50%;background:rgba(255,255,255,.06);display:inline-flex;align-items:center;justify-content:center;
    font-size:11px;font-weight:700;color:var(--dim);flex:none}
  .lbrow .ln{font-weight:700;white-space:nowrap;min-width:8.5em}
  .lbrow .lb{flex:1;height:5px;border-radius:999px;background:rgba(255,255,255,.07);overflow:hidden}
  .lbrow .lb i{display:block;height:100%;border-radius:999px}
  .lbrow .lv{font-variant-numeric:tabular-nums}
  .pbar{margin-top:14px;height:6px;border-radius:999px;background:rgba(255,255,255,.07);overflow:hidden}
  .pbar i{display:block;height:100%;width:0;border-radius:999px;background:linear-gradient(90deg,#5eead4,#b8a6ff 60%,#ff9ad2);transition:width .8s var(--ease)}
  .pmeta{margin-top:9px;font-size:12.5px;color:var(--dim)}
  .pmeta b{color:var(--ink)}
  .ndrow{display:flex;align-items:center;gap:10px 14px;padding:9px 0;font-size:13.5px;flex-wrap:wrap}
  .ndrow .ln{font-weight:700;min-width:7.5em}
  .nb-w{display:inline-flex;align-items:center;gap:6px;font-size:12px}
  .nb{display:inline-block;width:52px;height:5px;border-radius:999px;background:rgba(255,255,255,.08);overflow:hidden}
  .nb i{display:block;height:100%;border-radius:999px}
  .nwarn{font-size:11.5px;font-weight:700;color:#ffd9c2;border:1px solid rgba(255,138,74,.5);background:rgba(255,138,74,.1);border-radius:999px;padding:3px 9px}
  .nok{font-size:11.5px;color:#a4f5be;font-weight:600}
  .ndrow.asleep .ln{color:var(--dim)}
  .ndrow.asleep .nwarn{border:0;background:none;color:var(--dim);font-weight:500;padding:0}
  /* ---- footer CTA ---- */
  .cta{padding:clamp(110px,14vw,168px) 0 20px;text-align:center}
  .cta h2{font-size:clamp(38px,6.4vw,72px);letter-spacing:-.035em;line-height:1.03;font-weight:760;margin:0 0 18px}
  .cta .body{max-width:54ch;margin:0 auto;color:var(--dim);font-size:clamp(15.5px,1.9vw,18.5px);line-height:1.65}
  .cta-btn{display:inline-flex;align-items:center;gap:9px;margin-top:36px;padding:16px 32px;border-radius:999px;
    background:var(--ink);color:#0a0c12;font-weight:700;font-size:15.5px;text-decoration:none;
    transition:transform .22s var(--ease),box-shadow .22s var(--ease)}
  .cta-btn:hover{transform:translateY(-2px);box-shadow:0 20px 44px -18px rgba(238,241,247,.45)}
  .cta-btn:focus-visible{outline:2px solid var(--accent);outline-offset:3px}
  .foot{margin-top:70px;color:#5a627a;font-size:13px;line-height:1.7;text-align:center;border-top:1px solid var(--line);padding-top:28px}
  /* ---- adoptér en agent (konvertering) ---- */
  #adopter{text-align:center}
  .sec .cta-btn.ghost{background:transparent;color:var(--ink);border:1px solid rgba(238,241,247,.35);margin-top:30px}
  .sec .cta-btn.ghost:hover{border-color:var(--accent);color:var(--accent);box-shadow:0 18px 40px -20px rgba(94,234,212,.4)}
  .sec .ps{margin-top:16px;color:#5a627a;font-size:13px}
  @keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-7px)}}
  @keyframes blink{0%,100%{opacity:1}50%{opacity:.35}}
  @media (max-width:720px){
    .kicker{font-size:10.5px;letter-spacing:.24em}
    .grid{grid-template-columns:repeat(2,1fr)}
    .points{grid-template-columns:1fr}
    .lbrow .ln,.ndrow .ln{min-width:0}
    .door.live .lmeta{right:14px}
    .door.live.today .lmeta{right:64px}
    .door.live .lmeta .nm{font-size:15px}
  }
  @media (prefers-reduced-motion:reduce){
    html{scroll-behavior:auto}
    .rv{opacity:1;transform:none;transition:none}
    .door .poster .em{animation:none}
    .door.open:hover{transform:none}
    .door.live .livebadge .ld{animation:none}
    .door.live.open:hover .cover{transform:none}
    .cta-btn:hover{transform:none}
  }
</style>
</head>
<body>
<noscript><style>.rv{opacity:1;transform:none}</style></noscript>
<div class="grain"></div>
<main class="wrap" id="top">

  <header class="hero">
    <div class="kicker rv">Julikalenderen · 31 dage, 31 agenter</div>
    <h1 class="rv">De sover.<br>Du kan <span class="g">vække</span> dem.</h1>
    <p class="sub rv">Hver dag i juli åbner en ny låge med en karakter bygget af AI. Nogle er allerede vågnet som levende video-avatarer — resten venter på likes, mails og en smule kærlighed.</p>
    <div class="econ rv">
      <span>👍 1 like = <b>1 credit</b></span>
      <span>💬 1 kommentar = <b>3 credits</b></span>
      <span>🎬 ~100 credits = <b>1 avatar vækket</b></span>
    </div>
    <div class="status" id="status">
      <span class="pill"><span class="dot"></span><span id="count">…</span></span>
      <span class="pill game" id="scorePill"><span class="dot"></span><span id="scoreTxt"></span></span>
      <span class="pill votes" id="votesPill" hidden><span class="dot"></span><span id="votesTxt"></span></span>
      <span class="hint" id="hint">Nye låger åbner kl. 00 hver dag i juli 2026.</span>
    </div>
  </header>

  <div class="ggroup">
    <div class="glabel rv">Dag 1–8</div>
    <div class="grid rv">
__DOORS1__
    </div>
  </div>

  <section class="sec" id="koncept">
    <div class="eyebrow rv">Konceptet</div>
    <h2 class="rv">En kalender, der kigger tilbage.</h2>
    <div class="body rv">
      <p>En julekalender. Midt i juli. Bag hver af de 31 låger bor en agent — kodet som en levende karakter, der reagerer, når din cursor nærmer sig. Ingen af dem er ens. Alle har en historie.</p>
      <p>To af dem er allerede vågnet. <b>Ræven</b> bag låge 2 og <b>Agent-01</b> bag låge 3 lever nu som ægte AI-video-avatarer — skabt billede for billede, styret af dit scroll.</p>
      <p>Resten venter. På dig.</p>
    </div>
    <div class="points">
      <div class="pt rv"><div class="pe">🎁</div><h3>Én låge om dagen</h3><p>Bag hver låge: en kodet karakter med sin egen personlighed, der følger din cursor rundt på skærmen.</p></div>
      <div class="pt rv"><div class="pe">🎬</div><h3>To er allerede vågne</h3><p>Ræven og Agent-01 er blevet til ægte AI-video — levende avatarer, der bevæger sig, når du scroller.</p></div>
      <div class="pt rv"><div class="pe">🕵️</div><h3>Gæt modellen bag</h3><p>Hver karakter er bygget af enten Claude Opus 4.8 eller Sonnet 5. Kan du se forskel?</p></div>
    </div>
  </section>

  <div class="ggroup">
    <div class="glabel rv">Dag 9–16</div>
    <div class="grid rv">
__DOORS2__
    </div>
  </div>

  <section class="sec" id="vaekning">
    <div class="eyebrow rv">Vækningen</div>
    <h2 class="rv">Din like tæller. Bogstaveligt talt.</h2>
    <div class="body rv">
      <p>Her er Pouls løfte: Hver gang nogen liker eller kommenterer kalenderen på LinkedIn, betaler han af egen lomme. En like bliver til <b>1 credit</b>. En kommentar til <b>3</b>. Ved cirka <b>100 credits</b> — omkring 30 kroner — vækkes en avatar som ægte AI-video.</p>
      <p>Din like tæller altså. Bogstaveligt talt. Den bliver vekslet til liv.</p>
      <p>Og rækkefølgen? Den stemmer du om. En mail til avatarens egen adresse er én stemme — og flest stemmer vækkes først.</p>
    </div>
    <div class="points">
      <div class="pt rv"><div class="pe">👍</div><h3>1 like = 1 credit</h3><p>Hver like på LinkedIn-posten bliver til en credit — betalt af Pouls egen lomme.</p></div>
      <div class="pt rv"><div class="pe">💬</div><h3>1 kommentar = 3 credits</h3><p>Cirka 100 credits — omkring 30 kroner — og en avatar vågner som ægte AI-video.</p></div>
      <div class="pt rv"><div class="pe">📮</div><h3>Mails er stemmer</h3><p>En mail til avatarens adresse på @agent.agentics.dk tæller som én stemme. Flest stemmer vækkes først.</p></div>
    </div>
    <div class="panel rv" id="lbPanel" hidden>
      <div class="p-t">Stemmerne lige nu</div>
      <div id="lbList"></div>
      <div class="pbar"><i id="lbFill"></i></div>
      <div class="pmeta" id="lbTotal"></div>
    </div>
  </section>

  <div class="ggroup">
    <div class="glabel rv">Dag 17–24</div>
    <div class="grid rv">
__DOORS3__
    </div>
  </div>

  <section class="sec" id="feeding">
    <div class="eyebrow rv">Omsorgen</div>
    <h2 class="rv">Nu er de dit ansvar.</h2>
    <div class="body rv">
      <p>En vågen avatar er ikke færdig. Den er sulten. Tre behov — <b>mad</b>, <b>vand</b> og <b>kærlighed</b> — tømmes langsomt og forfalder helt på 48 timer.</p>
      <p>Én mail fodrer ét behov. Det tager ti sekunder og betyder alt for en lille agent på en server.</p>
      <p>Men falder alle tre behov til nul, lukker øjnene sig igen. En Tamagotchi glemmer aldrig, hvem der glemte den.</p>
    </div>
    <div class="points">
      <div class="pt rv"><div class="pe">⏳</div><h3>48 timer pr. behov</h3><p>Mad, vand og kærlighed tømmes langsomt — hvert behov forfalder på 48 timer.</p></div>
      <div class="pt rv"><div class="pe">✉️</div><h3>Én mail, ét behov</h3><p>Hver mail til avataren fodrer ét behov og fylder det helt op igen.</p></div>
      <div class="pt rv"><div class="pe">😴</div><h3>Nul betyder godnat</h3><p>Falder alle behov til nul, sover avataren igen — indtil nogen vækker den på ny.</p></div>
    </div>
    <div class="panel rv" id="needsPanel" hidden>
      <div class="p-t">Sådan har de vågne det lige nu</div>
      <div id="needsList"></div>
    </div>
  </section>

  <div class="ggroup">
    <div class="glabel rv">Dag 25–31</div>
    <div class="grid rv">
__DOORS4__
    </div>
  </div>

  <section class="sec" id="adopter">
    <div class="eyebrow rv">Til din forside</div>
    <h2 class="rv">Forelsket i en af dem?<br>Tag den med hjem.</h2>
    <div class="body rv">
      <p>Hver agent i kalenderen kan blive <b>din</b>. Vi bygger den færdig som et komplet brand til din forside eller dit produkt: karakterdesign, ægte AI-video-avatar, animeret hero-side og en stemme, der passer til den.</p>
      <p>Og det bedste: du behøver ikke udfylde en formular. Skriv direkte til agentens egen mailadresse — den du er faldet for — og bed om et tilbud. Så svarer vi. Agenten læser med.</p>
    </div>
    <a class="cta-btn ghost rv" href="mailto:raev@agent.agentics.dk?subject=Tilbud%20p%C3%A5%20R%C3%A6v%20%F0%9F%A6%8A&body=Hej%20agentics%20%E2%80%94%20jeg%20er%20interesseret%20i%20et%20tilbud%20p%C3%A5%20R%C3%A6v%20som%20avatar/brand%20til%20mit%20projekt.%20Kort%20om%20projektet%3A%20">✉️ Fx: bed Ræv om et tilbud</a>
    <p class="ps rv">PS: En tilbuds-mail tæller naturligvis også som en stemme — eller et måltid. Ræv siger tak.</p>
  </section>

  <section class="cta">
    <h2 class="rv">Én like fra at vågne.</h2>
    <p class="body rv">Hele kalenderen lever på LinkedIn, hvor Poul har lovet at veksle hver like og kommentar til liv. Dagens låge finder du lige her — og et sted derude venter en agent på netop dig.</p>
    <div class="econ rv">
      <span>👍 1 like = <b>1 credit</b></span>
      <span>💬 1 kommentar = <b>3 credits</b></span>
      <span>🎬 ~100 credits = <b>1 avatar vækket</b></span>
    </div>
    <a class="cta-btn rv" id="ctaToday" href="#top">Find dagens låge</a>
  </section>

  <p class="foot">agentics.dk — vi bygger autonome AI-agenter. Denne kalender er selve holdet, én dag ad gangen.<br>
  Alle sider er selvstændige, animerede og cursor-reaktive. #agentics #juli</p>
</main>
<script>
// Sub-path hosting (fx agentics.dk/julikalender): uden trailing slash resolver
// relative links (day-N.html) mod parent-stien og 404'er. Normaliser URL'en
// FØR nogen kan klikke — replaceState ændrer dokumentets base-URL.
(function(){
  var p = location.pathname;
  if (!/\.html$/i.test(p) && p.charAt(p.length-1) !== '/') {
    history.replaceState(null, '', p + '/' + location.search + location.hash);
  }
})();
var AGX_MODELS = __MODELS_JSON__;
(function(){
  var MONTH=6, YEAR=2026; // July 2026 (0-indexed month)

  // ---- operator preview mode: ?preview=1 unlocks every door for clicking (persists via
  // localStorage so it survives reloads); ?preview=0 turns it back off. Does not change what
  // real visitors see — it's per-browser, opt-in only, and clearly flagged when active. ----
  var qp = new URLSearchParams(location.search);
  if (qp.has('preview')) {
    try {
      if (qp.get('preview') === '0') localStorage.removeItem('agx_preview');
      else localStorage.setItem('agx_preview', '1');
    } catch (e) {}
  }
  var PREVIEW = false;
  try { PREVIEW = localStorage.getItem('agx_preview') === '1'; } catch (e) {}

  var now=new Date();
  var doors=[].slice.call(document.querySelectorAll('.door'));
  var open=0, todayDay=null;
  if(now.getFullYear()===YEAR && now.getMonth()===MONTH) todayDay=now.getDate();
  doors.forEach(function(el){
    var d=+el.getAttribute('data-day');
    var unlock=new Date(YEAR,MONTH,d);
    var reallyOpen=now>=unlock;
    var isOpen=reallyOpen||PREVIEW;
    if(isOpen){
      el.classList.add('open');
      el.setAttribute('href','day-'+d+'.html');
      el.removeAttribute('aria-disabled');
      open++;
      if(reallyOpen && d===todayDay){el.classList.add('today');
        var r=document.createElement('span');r.className='ribbon';r.textContent='I DAG';el.appendChild(r);}
      else if(!reallyOpen){
        el.classList.add('preview');
        var lb=el.querySelector('.lockbadge');
        if(lb){lb.textContent='🔓';lb.title='Forhåndsvisning — ikke åben for besøgende endnu';}
      }
    }else{
      el.removeAttribute('href');el.setAttribute('aria-disabled','true');
    }
  });
  var c=document.getElementById('count');
  c.textContent=(PREVIEW?open+' af 31 låger (preview)':open+' af 31 låger åbne');
  if(PREVIEW){
    var pv=document.createElement('span');
    pv.className='pill preview';
    pv.innerHTML='🔓 Preview-tilstand — du kan klikke alle · <a href="calendar.html?preview=0">afslut</a>';
    document.getElementById('status').appendChild(pv);
  }
  if(todayDay===null){
    document.getElementById('hint').textContent = (now<new Date(YEAR,MONTH,1))
      ? 'Kalenderen starter 1. juli 2026.' : 'Juli 2026 er slut — alle 31 agenter er åbne. 🎉';
  }
  // guess-the-model score, aggregated from each day page's localStorage guess
  var guessed=0, correct=0;
  for(var d=1; d<=31; d++){
    var g=null;
    try{ g=localStorage.getItem('agx_guess_'+d); }catch(e){}
    if(g){ guessed++; if(g===AGX_MODELS[d]) correct++; }
  }
  if(guessed>0){
    document.getElementById('scorePill').style.display='inline-flex';
    document.getElementById('scoreTxt').textContent='Din score: '+correct+'/'+guessed+' rigtige gæt';
  }
  // scroll-reveals — fade+rise, én gang; slået fra ved prefers-reduced-motion
  var reduce=false;
  try{ reduce=window.matchMedia('(prefers-reduced-motion: reduce)').matches; }catch(e){}
  var rvs=[].slice.call(document.querySelectorAll('.rv'));
  if(reduce || !('IntersectionObserver' in window)){
    rvs.forEach(function(e){ e.classList.add('in'); });
  }else{
    var io=new IntersectionObserver(function(es){
      es.forEach(function(en){ if(en.isIntersecting){ en.target.classList.add('in'); io.unobserve(en.target); } });
    },{threshold:.1,rootMargin:'0px 0px -36px 0px'});
    rvs.forEach(function(e){ io.observe(e); });
  }
  // footer-CTA: scroll op til dagens (eller første åbne) låge
  var cta=document.getElementById('ctaToday');
  if(cta){
    cta.addEventListener('click', function(ev){
      var t=document.querySelector('.door.today')||document.querySelector('.door.open');
      if(t){ ev.preventDefault(); t.scrollIntoView({behavior:reduce?'auto':'smooth',block:'center'}); }
    });
  }
})();
</script>
<script>
// vote-campaign meter — RELATIVE url ('api/votes', no leading slash): the page
// lives under a sub-path (agentics.dk/julikalender) behind a prefix-stripping
// proxy. On static hosting / file:// the fetch fails and bar+top-3 stay hidden.
var AGX_AVATARS = __AVATARS_JSON__;
(function(){
  fetch('api/votes').then(function(r){ if(!r.ok) throw 0; return r.json(); }).then(function(d){
    var votes=d.votes||{}, goal=d.goal||1000, total=d.total||0, avm=d.avatars||{};
    // slank status-pill: total stemmer mod mål
    document.getElementById('votesTxt').textContent=total+' af '+goal+' stemmer';
    document.getElementById('votesPill').hidden=false;
    // top-3 leaderboard i "vaekning"-sektionen
    var top=Object.keys(votes).sort(function(a,b){ return (votes[b]||0)-(votes[a]||0); }).slice(0,3);
    var max=votes[top[0]]||0, rows='';
    top.forEach(function(s,i){
      var a=AGX_AVATARS[s]||[s,'🤖','#5eead4'], v=votes[s]||0;
      var w=max>0?Math.max(4,Math.round(100*v/max)):4;
      rows+='<div class="lbrow"><span class="rk">'+(i+1)+'</span>'
        +'<span class="ln" style="color:'+a[2]+'">'+a[1]+' '+a[0]+'</span>'
        +'<span class="lb"><i style="width:'+w+'%;background:'+a[2]+'"></i></span>'
        +'<b class="lv">'+v+'</b></div>';
    });
    document.getElementById('lbList').innerHTML=rows;
    document.getElementById('lbFill').style.width=Math.min(100,Math.round(100*total/goal))+'%';
    document.getElementById('lbTotal').innerHTML='<b>'+total+'</b> af '+goal+' stemmer i alt — flest stemmer vækkes først';
    document.getElementById('lbPanel').hidden=false;
    // behovs-status i "feeding"-sektionen: ❤️🍖💧-bars pr. VÅGEN avatar + advarsel når
    // et behov er kritisk (< 25); asleep_again vises som en stille godnat-linje.
    var rows2='';
    Object.keys(avm).forEach(function(s){
      var a=avm[s]||{}, meta=AGX_AVATARS[s]||[s,'🤖','#5eead4'], nd=a.needs||{};
      if(a.state==='awake'){
        function bar(em,lv){lv=Math.round(+lv||0);lv=lv<0?0:(lv>100?100:lv);
          return '<span class="nb-w">'+em+'<span class="nb"><i style="width:'+lv
            +'%;background:'+(lv<25?'#ff6a6a':meta[2])+'"></i></span></span>';}
        var lows=[];
        if(nd.food<25)lows.push('mad');
        if(nd.water<25)lows.push('vand');
        if(nd.love<25)lows.push('kærlighed');
        rows2+='<div class="ndrow"><span class="ln" style="color:'+meta[2]+'">'+meta[1]+' '+meta[0]+'</span>'
          +bar('🍖',nd.food)+bar('💧',nd.water)+bar('❤️',nd.love)
          +(lows.length?'<span class="nwarn">⚠️ mangler '+lows.join(' og ')+'!</span>':'<span class="nok">✓ har det godt</span>')
          +'</div>';
      }else if(a.state==='asleep_again'){
        rows2+='<div class="ndrow asleep"><span class="ln">😴 '+meta[1]+' '+meta[0]+'</span>'
          +'<span class="nwarn">faldt i søvn igen — en mail vækker den</span></div>';
      }
    });
    if(rows2){
      document.getElementById('needsList').innerHTML=rows2;
      document.getElementById('needsPanel').hidden=false;
    }
    // runtime-forfining af LEVENDE tiles: asleep_again => "😴 Sover igen"-badge,
    // kritisk behov => "⚠️ Sulten"-chip
    [].slice.call(document.querySelectorAll('.door[data-live]')).forEach(function(el){
      var a=avm[el.getAttribute('data-slug')]; if(!a) return;
      var b=el.querySelector('.livebadge');
      if(a.state==='asleep_again'){
        if(b){ b.classList.add('asleep'); b.textContent='😴 Sover igen'; }
        el.classList.add('resleep');
      }else if(a.state==='awake'){
        var nd=a.needs||{};
        if(nd.food<25||nd.water<25||nd.love<25){
          var c=el.querySelector('.hungry'); if(c) c.hidden=false;
        }
      }
    });
  }).catch(function(){});
})();
</script>
<script src="track.js" defer></script>
</body>
</html>
"""
models_json = json.dumps({str(d): MODEL[d] for d in range(1, 32)})
# slug -> [name, emoji, accent] for the campaign top-3 (names/emoji are plain
# ASCII/emoji — ensure_ascii keeps the inline JSON safe inside the script tag)
avatars_json = json.dumps(
    {slug: [name, emoji, acc] for slug, name, emoji, acc in VOTE_ROSTER.values()}
)
open(f"{DIR}/calendar.html","w",encoding="utf-8").write(
    CAL.replace("__DOORS1__", doors_by_group[0]).replace("__DOORS2__", doors_by_group[1])
       .replace("__DOORS3__", doors_by_group[2]).replace("__DOORS4__", doors_by_group[3])
       .replace("__MODELS_JSON__", models_json).replace("__AVATARS_JSON__", avatars_json)
)
print(f"wrote calendar.html (live days: {sorted(LIVE_DAYS)})")

# ---- answer key for the operator (not linked from any page) ----
key_lines = ["day\tname\tmodel"]
for d in range(1, 32):
    key_lines.append(f"{d}\t{ROSTER[d][0]}\t{MODEL_LABEL[MODEL[d]]}")
open(f"{DIR}/ANSWER_KEY.txt", "w", encoding="utf-8").write("\n".join(key_lines) + "\n")
print("wrote ANSWER_KEY.txt (operator-only, not linked)")
