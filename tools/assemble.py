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
doors = []
for d in range(1, 32):
    name, emoji, acc, _ = ROSTER[d]
    doors.append(
f'''    <a class="door" data-day="{d}" style="--c:{acc}" aria-label="Dag {d} — {html.escape(name)}">
      <span class="corner">{d:02d}</span>
      <span class="lockbadge" aria-hidden="true">🔒</span>
      <span class="poster">
        <span class="em">{emoji}</span>
        <span class="nm">{html.escape(name)}</span>
        <span class="dag">Dag {d}<span class="when"> · åbner {d}. juli</span></span>
      </span>
    </a>''')
doors_html = "\n".join(doors)

CAL = r"""<!doctype html>
<html lang="da">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>agentics.dk · Juli-kalender 2026</title>
<style>
  :root{--bg:#06070b;--ink:#eef1f7;--dim:#8b93a7;--line:#1a2030;--card:#0e1119;--accent:#5eead4}
  *{box-sizing:border-box}
  html,body{margin:0;background:var(--bg);color:var(--ink);
    font-family:-apple-system,"Segoe UI",Inter,system-ui,sans-serif;-webkit-font-smoothing:antialiased}
  body{min-height:100vh;padding:clamp(26px,5vw,72px) clamp(18px,5vw,72px) 72px;position:relative;overflow-x:hidden;
    background:
     radial-gradient(1100px 640px at 82% -12%, rgba(94,234,212,.12), transparent 60%),
     radial-gradient(860px 520px at -6% 108%, rgba(180,140,255,.10), transparent 60%),
     var(--bg)}
  .grain{position:fixed;inset:0;pointer-events:none;opacity:.05;z-index:0;mix-blend-mode:overlay;
    background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")}
  .wrap{max-width:1180px;margin:0 auto;position:relative;z-index:1}
  .kicker{letter-spacing:.34em;text-transform:uppercase;font-size:12px;color:var(--accent);font-weight:600}
  h1{font-size:clamp(34px,6vw,64px);line-height:1.02;margin:.3em 0 .18em;letter-spacing:-.03em;font-weight:750}
  h1 .g{background:linear-gradient(90deg,#5eead4,#b8a6ff 60%,#ff9ad2);-webkit-background-clip:text;background-clip:text;color:transparent}
  .sub{color:var(--dim);font-size:clamp(15px,1.8vw,18px);max-width:60ch;line-height:1.6}
  .status{margin:22px 0 6px;display:flex;flex-wrap:wrap;align-items:center;gap:12px;font-size:13.5px;color:var(--dim)}
  .status .pill{display:inline-flex;align-items:center;gap:8px;padding:7px 13px;border-radius:999px;
    border:1px solid var(--line);background:rgba(255,255,255,.02);color:var(--ink);font-weight:600}
  .status .dot{width:8px;height:8px;border-radius:50%;background:var(--accent);box-shadow:0 0 12px var(--accent)}
  .status .pill.game{display:none;border-color:color-mix(in srgb,#b98cff 45%,var(--line));color:#e3d9ff}
  .status .pill.game .dot{background:#b98cff;box-shadow:0 0 12px #b98cff}
  .grid{margin-top:26px;display:grid;grid-template-columns:repeat(auto-fill,minmax(148px,1fr));gap:14px}
  .door{position:relative;aspect-ratio:1/1;border-radius:18px;overflow:hidden;text-decoration:none;color:inherit;
    background:linear-gradient(180deg,var(--card),#0a0d13);border:1px solid var(--line);
    display:flex;align-items:center;justify-content:center;cursor:default;
    filter:grayscale(.4) brightness(.8);
    transition:transform .28s cubic-bezier(.2,.7,.2,1),border-color .28s,box-shadow .28s,filter .28s}
  .door .corner{position:absolute;top:10px;left:12px;font-size:12px;font-weight:700;color:var(--dim);letter-spacing:.04em}
  .door::after{content:"";position:absolute;top:0;left:0;right:0;height:2px;background:var(--c);opacity:.35;transition:opacity .28s}
  .door:hover{filter:grayscale(.15) brightness(.9);border-color:color-mix(in srgb,var(--c) 40%,var(--line));
    box-shadow:0 16px 40px -26px var(--c)}
  /* lock badge — shown until the door is actually open */
  .door .lockbadge{position:absolute;top:9px;right:9px;width:24px;height:24px;border-radius:50%;
    display:flex;align-items:center;justify-content:center;font-size:11px;
    background:rgba(6,7,11,.6);border:1px solid rgba(255,255,255,.14);backdrop-filter:blur(6px)}
  .door.open .lockbadge{display:none}
  /* poster — the avatar's art/name, always shown */
  .door .poster{display:flex;flex-direction:column;align-items:center;gap:6px;text-align:center;padding:10px}
  .door .poster .em{font-size:clamp(38px,6vw,58px);line-height:1;filter:drop-shadow(0 6px 18px var(--c))}
  .door .poster .nm{font-size:15px;font-weight:700;letter-spacing:-.01em}
  .door .poster .dag{font-size:11px;color:var(--dim);letter-spacing:.06em;text-transform:uppercase}
  .door .poster .when{text-transform:none;letter-spacing:normal;color:#5a627a}
  .door.open .poster .when{display:none}
  .door.open .poster .em{animation:float 4.5s ease-in-out infinite}
  .door.open{cursor:pointer;filter:none}
  .door.open .corner{color:var(--ink)}
  .door.open::after{opacity:1;box-shadow:0 0 16px var(--c)}
  .door.open:hover{transform:translateY(-5px);border-color:color-mix(in srgb,var(--c) 60%,transparent);
    box-shadow:0 26px 60px -24px var(--c)}
  .door.open::before{content:"";position:absolute;inset:0;background:radial-gradient(120px 90px at 50% 30%,color-mix(in srgb,var(--c) 22%,transparent),transparent 70%);opacity:0;transition:opacity .3s}
  .door.open:hover::before{opacity:1}
  /* preview-unlocked (operator only): still clearly marked apart from a REAL open day */
  .door.open.preview{border-style:dashed}
  .door.open.preview .lockbadge{display:flex;background:rgba(94,234,212,.16);border-color:color-mix(in srgb,var(--c) 55%,transparent)}
  /* today */
  .door.today{border-color:color-mix(in srgb,var(--c) 70%,transparent);box-shadow:0 0 0 1px color-mix(in srgb,var(--c) 45%,transparent),0 22px 55px -26px var(--c)}
  .door.today .ribbon{position:absolute;top:9px;right:9px;font-size:10px;font-weight:800;letter-spacing:.12em;
    background:var(--c);color:#07080c;padding:3px 8px;border-radius:999px}
  .door:focus-visible{outline:2px solid var(--c);outline-offset:3px}
  .status .pill.preview{border-color:color-mix(in srgb,#ffb45a 45%,var(--line));color:#ffe3c2}
  .status .pill.preview a{color:inherit;text-decoration:underline;text-underline-offset:2px}
  /* vote-campaign banner */
  .camp{margin:16px 0 0;max-width:780px;padding:14px 16px 13px;border-radius:16px;
    border:1px solid var(--line);background:rgba(255,255,255,.02)}
  .camp [hidden]{display:none!important}
  .camp .ct{font-size:14px;font-weight:700;letter-spacing:.01em;margin-bottom:4px}
  .camp .cx{font-size:12.5px;color:var(--dim);line-height:1.55}
  .camp .cbar{margin-top:10px;height:6px;border-radius:999px;background:rgba(255,255,255,.07);overflow:hidden}
  .camp .cbar i{display:block;height:100%;width:0;border-radius:999px;
    background:linear-gradient(90deg,#5eead4,#b8a6ff 60%,#ff9ad2);transition:width .8s cubic-bezier(.2,.7,.2,1)}
  .camp .cmeta{margin-top:8px;display:flex;flex-wrap:wrap;align-items:center;gap:5px 14px;font-size:12px;color:var(--dim)}
  .camp .cmeta b{color:var(--ink)}
  .camp .ctop span{font-weight:600;white-space:nowrap;margin-right:10px}
  /* feeding: needs-status strip for awake avatars (docs/feeding-spec.md) */
  .camp .cneeds{margin-top:10px;padding-top:9px;border-top:1px solid var(--line);
    display:flex;flex-wrap:wrap;align-items:center;gap:8px 18px;font-size:12.5px}
  .camp .cneeds .cav{display:inline-flex;align-items:center;gap:8px;font-weight:600;white-space:nowrap}
  .camp .cneeds .nmini{display:inline-flex;align-items:center;gap:3px;font-size:11px}
  .camp .cneeds .nmini .nt{display:inline-block;width:30px;height:4px;border-radius:999px;
    background:rgba(255,255,255,.09);overflow:hidden}
  .camp .cneeds .nmini .nt .nf{display:block;height:100%;border-radius:999px}
  .camp .cneeds .warn{display:inline-flex;align-items:center;gap:6px;padding:4px 10px;border-radius:999px;
    font-size:11.5px;font-weight:700;color:#ffd9c2;border:1px solid rgba(255,138,74,.5);background:rgba(255,138,74,.1)}
  .foot{margin-top:40px;color:#5a627a;font-size:13px;line-height:1.6}
  @keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-7px)}}
  @media (prefers-reduced-motion:reduce){.door .poster .em{animation:none}.door.open:hover{transform:none}}
</style>
</head>
<body>
<div class="grain"></div>
<div class="wrap">
  <div class="kicker">agentics.dk · avatar-kalender</div>
  <h1>31 dage. <span class="g">31 agenter.</span></h1>
  <p class="sub">En lille autonom karakter for hver dag i juli — hver med sit eget temperament og sin egen historie. Én ny <b>låge</b> åbner hver morgen. Klik en åben låge for at møde dagens agent, og gæt om <b>Claude Opus 4.8</b> eller <b>Claude Sonnet 5</b> byggede den. Bedst på desktop — de kigger tilbage.</p>
  <div class="status" id="status">
    <span class="pill"><span class="dot"></span><span id="count">…</span></span>
    <span class="pill game" id="scorePill"><span class="dot"></span><span id="scoreTxt"></span></span>
    <span id="hint">Nye låger åbner kl. 00 hver dag i juli 2026.</span>
  </div>
  <div class="camp" id="agxCampaign">
    <div class="ct">🎬 Kampagnen: stem holdet levende</div>
    <div class="cx">1 LinkedIn-kommentar = 1 credit · 1 mail = 1 stemme · flest stemmer animeres først.
      Åbn en låge og send din stemme direkte fra agentens egen side.</div>
    <div class="cbar" id="campBar" hidden><i id="campFill"></i></div>
    <div class="cmeta" id="campMeta" hidden>
      <span id="campTotal"></span>
      <span>Top 3: <span class="ctop" id="campTop"></span></span>
    </div>
    <div class="cneeds" id="campNeeds" hidden></div>
  </div>
  <div class="grid" id="grid">
__DOORS__
  </div>
  <p class="foot">agentics.dk — vi bygger autonome AI-agenter. Denne kalender er selve holdet, én dag ad gangen.<br>
  Alle sider er selvstændige, animerede og cursor-reaktive. #agentics #juli</p>
</div>
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
})();
</script>
<script>
// vote-campaign meter — RELATIVE url ('api/votes', no leading slash): the page
// lives under a sub-path (agentics.dk/julikalender) behind a prefix-stripping
// proxy. On static hosting / file:// the fetch fails and bar+top-3 stay hidden.
var AGX_AVATARS = __AVATARS_JSON__;
(function(){
  fetch('api/votes').then(function(r){ if(!r.ok) throw 0; return r.json(); }).then(function(d){
    var votes=d.votes||{}, goal=d.goal||1000, total=d.total||0;
    document.getElementById('campFill').style.width=Math.min(100,Math.round(100*total/goal))+'%';
    document.getElementById('campTotal').innerHTML='<b>'+total+'</b> af '+goal+' stemmer i alt';
    var top=Object.keys(votes).sort(function(a,b){ return (votes[b]||0)-(votes[a]||0); }).slice(0,3);
    var out='';
    top.forEach(function(s,i){
      var a=AGX_AVATARS[s]||[s,'🤖','#5eead4'];
      out+='<span style="color:'+a[2]+'">'+(i+1)+'. '+a[1]+' '+a[0]+' · '+(votes[s]||0)+'</span>';
    });
    document.getElementById('campTop').innerHTML=out;
    document.getElementById('campBar').hidden=false;
    document.getElementById('campMeta').hidden=false;
    // feeding: needs-status strip — tiny ❤️🍖💧 bars per AWAKE avatar, plus an
    // attention chip when any need is critical (< 25). See docs/feeding-spec.md.
    var avm=d.avatars||{}, bars='', warns='';
    Object.keys(avm).forEach(function(s){
      var a=avm[s]||{};
      if(a.state!=='awake') return;
      var meta=AGX_AVATARS[s]||[s,'🤖','#5eead4'], nd=a.needs||{};
      function mini(em,lv){lv=Math.round(+lv||0);lv=lv<0?0:(lv>100?100:lv);
        return '<span class="nmini">'+em+'<span class="nt"><span class="nf" style="width:'+lv
          +'%;background:'+(lv<25?'#ff6a6a':meta[2])+'"></span></span></span>';}
      bars+='<span class="cav"><span style="color:'+meta[2]+'">'+meta[1]+' '+meta[0]+'</span>'
        +mini('❤️',nd.love)+mini('🍖',nd.food)+mini('💧',nd.water)+'</span>';
      var lows=[];
      if(nd.food<25)lows.push('mad');
      if(nd.water<25)lows.push('vand');
      if(nd.love<25)lows.push('kærlighed');
      if(lows.length)warns+='<span class="warn">⚠️ '+meta[0]+' mangler '+lows.join(' og ')+'!</span>';
    });
    if(bars||warns){
      var cn=document.getElementById('campNeeds');
      cn.innerHTML=bars+warns;
      cn.hidden=false;
    }
  }).catch(function(){});
})();
</script>
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
    CAL.replace("__DOORS__", doors_html).replace("__MODELS_JSON__", models_json)
       .replace("__AVATARS_JSON__", avatars_json)
)
print("wrote calendar.html")

# ---- answer key for the operator (not linked from any page) ----
key_lines = ["day\tname\tmodel"]
for d in range(1, 32):
    key_lines.append(f"{d}\t{ROSTER[d][0]}\t{MODEL_LABEL[MODEL[d]]}")
open(f"{DIR}/ANSWER_KEY.txt", "w", encoding="utf-8").write("\n".join(key_lines) + "\n")
print("wrote ANSWER_KEY.txt (operator-only, not linked)")
