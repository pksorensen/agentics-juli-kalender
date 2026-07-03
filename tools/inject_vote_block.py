#!/usr/bin/env python3
# Patches the vote-campaign block ("agx-vote") into all 31 existing day-N.html
# pages IN PLACE. The block sits inside the fixed story card, between the tags
# row (<div class="agx-tags">) and the guess widget (<div class="agx-guess">),
# so it is always visible on the non-scrolling day pages.
#
# IDEMPOTENT: any file already containing 'agx-vote' is skipped, so re-running
# is always safe (day-2 is a video page — only its <aside> chrome is touched).
#
# tools/assemble.py imports VOTE_CSS / vote_block / ALIVE / VOTE_ROSTER from
# this module, so a future full regeneration produces byte-identical markup.
#
# Usage: python3 tools/inject_vote_block.py
import html
import sys
from urllib.parse import quote

DIR = "/home/claude-desktop/experiments/animated-avatar"

# day -> (slug, name, emoji, accent) — vote address is <slug>@agent.agentics.dk
VOTE_ROSTER = {
 1:("aura","AURA","🔮","#38e6ff"),
 2:("raev","Ræv","🦊","#ff9a3d"),
 3:("agent01","Agent-01","🤖","#5eead4"),
 4:("nova","Nova","🫧","#ff5cc8"),
 5:("comet","Comet","👨‍🚀","#ff7a3d"),
 6:("boo","Boo","👻","#c8b6ff"),
 7:("neko","Neko","🐱","#ff8a3d"),
 8:("tsuru","Tsuru","🕊️","#b83b2e"),
 9:("bit","Bit","👾","#00f0c8"),
 10:("lumen","Lumen","🪼","#3ff0d8"),
 11:("ugla","Ugla","🦉","#ffb45a"),
 12:("chrome","Chrome","🪞","#c8b6ff"),
 13:("ember","Ember","🔥","#ff7a18"),
 14:("koi","Koi","🐟","#4aa8ff"),
 15:("golem","Golem","🗿","#9fb0a0"),
 16:("sprout","Sprout","🌱","#6ee07a"),
 17:("draco","Draco","🐉","#ff5a3c"),
 18:("aster","Aster","✨","#b98cff"),
 19:("lundi","Lundi","🐦","#ff8a4a"),
 20:("mochi","Mochi","🍡","#ffb3d1"),
 21:("volt","Volt","⚡","#ffe14a"),
 22:("prism","Prism","💎","#7ad0ff"),
 23:("nimbus","Nimbus","☁️","#bcd3ff"),
 24:("ravn","Ravn","🐦‍⬛","#8a7dff"),
 25:("cog","Cog","⚙️","#d0a24a"),
 26:("frost","Frost","❄️","#9fe8ff"),
 27:("beacon","Beacon","🗼","#ffd24a"),
 28:("sol","Sol","☀️","#ffb02e"),
 29:("luna","Luna","🌙","#c0c8ff"),
 30:("bi","Bi","🐝","#ffcf33"),
 31:("vega","Vega","🚀","#ff7a3d"),
}

# days whose avatar is ALREADY animated (video) — card shows the thank-you state
# instead of the vote plea; the vote meter is still shown (extra votes still count)
ALIVE = {2}

# ---- CSS: appended into the existing <style id="agx-chrome-css"> block, right
#      before the '.agx-guess{margin:0 0 12px' rule. Matches chrome aesthetics
#      (rgba surfaces, 10px radii, accent via var(--agx)). Compact: <~110px. ----
VOTE_CSS = (
""".agx-vote{margin:0 0 12px;padding-top:10px;border-top:1px solid rgba(255,255,255,.09)}
.agx-vote .vt{font-size:12.5px;font-weight:700;letter-spacing:.01em;margin-bottom:2px}
.agx-vote.alive .vt{color:#a4f5be}
.agx-vote .vp{font-size:11.5px;color:#aeb6c6;line-height:1.45;margin-bottom:7px}
.agx-vote .vp a{color:var(--agx);font-weight:600;text-decoration:none}
.agx-vote .vp a:hover{text-decoration:underline}
.agx-vote .vbtn{display:block;text-align:center;padding:7px 10px;border-radius:10px;border:1px solid var(--agx);
  background:rgba(255,255,255,.05);color:#eef1f7;font-size:12.5px;font-weight:700;text-decoration:none;
  transition:transform .15s,background .15s,box-shadow .15s}
.agx-vote .vbtn:hover{transform:translateY(-1px);background:rgba(255,255,255,.1);box-shadow:0 6px 18px -8px var(--agx)}
.agx-vote .vbtn:focus-visible{outline:2px solid var(--agx);outline-offset:2px}
.agx-vote .vmeter{margin-top:8px}
.agx-vote .vbar{height:5px;border-radius:999px;background:rgba(255,255,255,.08);overflow:hidden}
.agx-vote .vbar i{display:block;height:100%;width:0;border-radius:999px;background:var(--agx);
  transition:width .6s cubic-bezier(.2,.7,.2,1)}
.agx-vote .vstat{margin-top:5px;font-size:10.5px;color:#aeb6c6;letter-spacing:.02em;line-height:1.45}
""")

# ---- HTML+JS template. fetch() MUST stay RELATIVE ('api/votes', no leading /):
#      the pages are hosted under a sub-path (agentics.dk/julikalender) behind a
#      prefix-stripping proxy. If the fetch fails (static hosting, file://) the
#      meter simply stays hidden and the mailto CTA keeps working. ----
VOTE_TMPL = """  <div class="agx-vote__ALIVECLS__" id="agxVote" data-slug="__SLUG__">
    __VHEAD__
    __VPLEA__
__VCTA__    <div class="vmeter" id="agxVoteMeter" hidden>
      <div class="vbar"><i id="agxVoteFill"></i></div>
      <div class="vstat" id="agxVoteStat"></div>
    </div>
  </div>
  <script>(function(){
    var box=document.getElementById('agxVote'); if(!box) return;
    var SLUG=box.getAttribute('data-slug');
    fetch('api/votes').then(function(r){ if(!r.ok) throw 0; return r.json(); }).then(function(d){
      var v=d.votes||{}, mine=v[SLUG]||0, leader=1, rank=1, n=0;
      Object.keys(v).forEach(function(s){ n++; if(v[s]>leader) leader=v[s]; if(v[s]>mine) rank++; });
      document.getElementById('agxVoteFill').style.width=Math.round(100*mine/leader)+'%';
      document.getElementById('agxVoteStat').textContent=mine+(mine===1?' stemme':' stemmer')
        +' · nr. '+rank+' af '+(n||31)+' · flest stemmer animeres først';
      document.getElementById('agxVoteMeter').hidden=false;
    }).catch(function(){ /* statisk hosting / offline: skjul måler, behold CTA */ });
  })();</script>"""


def mailto_href(day):
    """mailto: URL for one vote — subject/body in Danish, fully percent-encoded
    (spaces, æøå, emoji), & separator escaped for the HTML attribute."""
    slug, name, emoji, _ = VOTE_ROSTER[day]
    subject = f"Stem på {name} {emoji}"
    body = (f"Jeg stemmer på {name}! 🎬\r\n"
            f"Animér {name} først — denne mail tæller som én stemme.")
    href = (f"mailto:{slug}@agent.agentics.dk"
            f"?subject={quote(subject, safe='')}&body={quote(body, safe='')}")
    return html.escape(href, quote=True)


def vote_block(day):
    """The full agx-vote HTML+JS for one day (no trailing newline)."""
    slug, name, emoji, _ = VOTE_ROSTER[day]
    nm = html.escape(name)
    if day in ALIVE:
        alivecls = " alive"
        head = f'<div class="vt">✓ {nm} er levende!</div>'
        plea = (f'<div class="vp">Tak for jeres stemmer — de vækkede mig. 🧡 '
                f'<a href="calendar.html">Stem de andre levende →</a></div>')
        cta = ""
    else:
        alivecls = ""
        head = f'<div class="vt">🎬 Hjælp {nm} til live</div>'
        plea = '<div class="vp">Jeg er stadig kun kode. Send én mail og stem mig levende:</div>'
        cta = f'    <a class="vbtn" href="{mailto_href(day)}">✉️ Stem på {nm}</a>\n'
    return (VOTE_TMPL
            .replace("__ALIVECLS__", alivecls)
            .replace("__SLUG__", slug)
            .replace("__VHEAD__", head)
            .replace("__VPLEA__", plea)
            .replace("__VCTA__", cta))


# stable anchors, both verified to occur exactly once per generated day page
CSS_ANCHOR = ".agx-guess{margin:0 0 12px"
HTML_ANCHOR = '  <div class="agx-guess"'


def patch_file(path, day):
    doc = open(path, encoding="utf-8").read()
    if "agx-vote" in doc:
        return "skipped (already patched)"
    if doc.count(CSS_ANCHOR) != 1 or doc.count(HTML_ANCHOR) != 1:
        return (f"ERROR: anchors not unique (css={doc.count(CSS_ANCHOR)}, "
                f"html={doc.count(HTML_ANCHOR)}) — not touched")
    doc = doc.replace(CSS_ANCHOR, VOTE_CSS + CSS_ANCHOR, 1)
    doc = doc.replace(HTML_ANCHOR, vote_block(day) + "\n" + HTML_ANCHOR, 1)
    open(path, "w", encoding="utf-8").write(doc)
    return "patched"


def main():
    patched = skipped = errors = 0
    for day in range(1, 32):
        path = f"{DIR}/day-{day}.html"
        try:
            result = patch_file(path, day)
        except FileNotFoundError:
            result = "ERROR: file not found"
        if result == "patched":
            patched += 1
        elif result.startswith("skipped"):
            skipped += 1
        else:
            errors += 1
        print(f"  day-{day}.html: {result}")
    print(f"done: {patched} patched, {skipped} skipped, {errors} errors (of 31)")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
