#!/usr/bin/env python3
# Patches the vote/feeding-campaign block ("agx-vote") into all 31 existing
# day-N.html pages IN PLACE. The block sits inside the fixed story card,
# between the tags row (<div class="agx-tags">) and the guess widget
# (<div class="agx-guess">), so it is always visible on the day pages.
#
# v2 (feeding system, docs/feeding-spec.md): the block is STATE-DRIVEN at
# runtime — one relative fetch('api/votes') decides which variant renders:
#   sleeping      -> vote plea + mailto CTA + votes meter   (v1 look, unchanged)
#   awake         -> status line + 3 need-bars (❤️🍖💧) + 3 feed-mailto buttons
#   asleep_again  -> "😴 … faldet i søvn igen" + single wake-mailto CTA
#   fetch fails   -> static build-time default stays (sleeping plea; day-2
#                    keeps its alive-thanks default), bars stay hidden.
#
# UPGRADEABLE, three paths per file (idempotent — re-running is always safe):
#   1. marker-based:  <!-- agx-vote:start --> … <!-- agx-vote:end -->  and
#      /* agx-vote-css:start */ … /* agx-vote-css:end */  regions are replaced
#      wholesale (this is the trivial path for all FUTURE upgrades);
#   2. legacy v1 (has 'agx-vote' but no markers): the v1 CSS is matched
#      verbatim (frozen in V1_VOTE_CSS below) and the v1 HTML+JS region is
#      located via its stable start ('<div class="agx-vote') / end
#      ('})();</script>') anchors — both replaced and wrapped in markers;
#   3. fresh page (no 'agx-vote'): injected at the original anchors.
#
# tools/assemble.py imports VOTE_CSS / vote_block / ALIVE / VOTE_ROSTER from
# this module, so a future full regeneration produces byte-identical markup
# (markers included).
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

# days whose avatar is ALREADY animated (video) — the BUILD-TIME default for
# these is the alive/thank-you variant (shown when the fetch fails, e.g. static
# hosting). At runtime the API state overrides the default on every page.
ALIVE = {2}

# ---- region markers: everything between them (inclusive) is replaced on
#      upgrade, so future versions never need anchor archaeology again ----
CSS_MARK_START = "/* agx-vote-css:start */"
CSS_MARK_END = "/* agx-vote-css:end */"
HTML_MARK_START = "<!-- agx-vote:start -->"
HTML_MARK_END = "<!-- agx-vote:end -->"

# ---- CSS: lives inside the existing <style id="agx-chrome-css"> block, right
#      before the '.agx-guess{margin:0 0 12px' rule. Matches chrome aesthetics
#      (rgba surfaces, 10px radii, accent via var(--agx)). All three runtime
#      variants stay compact (tallest ≈ 110px incl. meter). ----
VOTE_CSS = (CSS_MARK_START + "\n" +
""".agx-vote{margin:0 0 12px;padding-top:10px;border-top:1px solid rgba(255,255,255,.09)}
.agx-vote .vt{font-size:12.5px;font-weight:700;letter-spacing:.01em;margin-bottom:2px}
.agx-vote.alive .vt{color:#a4f5be}
.agx-vote .vt.ok{color:#a4f5be}
.agx-vote .vt.low{color:#ffb9b9}
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
.agx-vote .nrow{display:flex;gap:9px;margin:7px 0 9px}
.agx-vote .need{flex:1;display:flex;align-items:center;gap:5px;font-size:11px;line-height:1}
.agx-vote .need .nb{flex:1;height:4px;border-radius:999px;background:rgba(255,255,255,.08);overflow:hidden}
.agx-vote .need .nb i{display:block;height:100%;width:0;border-radius:999px;background:var(--agx);
  transition:width .6s cubic-bezier(.2,.7,.2,1)}
.agx-vote .need.low .nb i{background:#ff6a6a}
.agx-vote .fbtns{display:flex;gap:6px}
.agx-vote .fbtn{flex:1;text-align:center;padding:6px 2px;border-radius:10px;border:1px solid rgba(255,255,255,.15);
  background:rgba(255,255,255,.04);color:#eef1f7;font-size:10.5px;font-weight:600;text-decoration:none;white-space:nowrap;
  transition:transform .15s,border-color .15s,background .15s}
.agx-vote .fbtn:hover{border-color:var(--agx);background:rgba(255,255,255,.08);transform:translateY(-1px)}
.agx-vote .fbtn:focus-visible{outline:2px solid var(--agx);outline-offset:2px}
""" + CSS_MARK_END + "\n")

# ---- FROZEN copy of the v1 CSS exactly as injected by the previous version of
#      this script — used only to locate/replace the legacy region on upgrade.
#      Do NOT edit. ----
V1_VOTE_CSS = (
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
#      prefix-stripping proxy. The static markup below is only the NO-FETCH
#      fallback; on a successful fetch the JS re-renders the box from the
#      avatar's live state (sleeping / awake / asleep_again). All runtime
#      mailto: links are built with encodeURIComponent, which percent-encodes
#      æøå and emoji correctly. ----
VOTE_TMPL = """  <!-- agx-vote:start -->
  <div class="agx-vote__ALIVECLS__" id="agxVote" data-slug="__SLUG__" data-name="__NAME__" data-emoji="__EMOJI__">
    __VHEAD__
    __VPLEA__
__VCTA__  </div>
  <script>(function(){
    var box=document.getElementById('agxVote'); if(!box) return;
    var SLUG=box.getAttribute('data-slug'),NAME=box.getAttribute('data-name')||SLUG,EMOJI=box.getAttribute('data-emoji')||'';
    var NM=String(NAME).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
    function mailto(sub,body){return 'mailto:'+SLUG+'@agent.agentics.dk?subject='+encodeURIComponent(sub)+'&body='+encodeURIComponent(body);}
    function bar(em,lv){lv=Math.round(+lv||0);lv=lv<0?0:(lv>100?100:lv);
      return '<span class="need'+(lv<25?' low':'')+'">'+em+'<span class="nb"><i style="width:'+lv+'%"></i></span></span>';}
    function fbtn(lbl,sub,body){return '<a class="fbtn" href="'+esc(mailto(sub,body))+'">'+lbl+'</a>';}
    function render(inner){box.className='agx-vote';box.innerHTML=inner;}
    fetch('api/votes').then(function(r){ if(!r.ok) throw 0; return r.json(); }).then(function(d){
      var av=(d.avatars||{})[SLUG], state=av?av.state:'sleeping';
      if(state==='awake'){
        var n=av.needs||{}, low=(n.love<25||n.food<25||n.water<25);
        render('<div class="vt '+(low?'low':'ok')+'">'+NM+(low?' er SULTEN!':' har det godt')+'</div>'
          +'<div class="nrow">'+bar('❤️',n.love)+bar('🍖',n.food)+bar('💧',n.water)+'</div>'
          +'<div class="fbtns">'
          +fbtn('🍖 Giv mad','Mad til '+NAME+' 🍖','Her er mad til dig, '+NAME+'! 🍖')
          +fbtn('💧 Giv vand','Vand til '+NAME+' 💧','Her er frisk vand til dig, '+NAME+'! 💧')
          +fbtn('❤️ Giv kærlighed','Kærlighed til '+NAME+' ❤️','Du er elsket, '+NAME+'! ❤️')
          +'</div>');
      }else if(state==='asleep_again'){
        render('<div class="vt">😴 '+NM+' er faldet i søvn igen…</div>'
          +'<div class="vp">Behovene nåede nul. Én mail genopliver '+NM+':</div>'
          +'<a class="vbtn" href="'+esc(mailto('Væk '+NAME+' '+EMOJI,'Vågn op, '+NAME+' — her er lidt kærlighed til at starte på! ❤️'))+'">✉️ Væk '+NM+'</a>');
      }else{
        var v=d.votes||{}, mine=v[SLUG]||0, leader=1, rank=1, cnt=0;
        Object.keys(v).forEach(function(s){ cnt++; if(v[s]>leader) leader=v[s]; if(v[s]>mine) rank++; });
        render('<div class="vt">🎬 Hjælp '+NM+' til live</div>'
          +'<div class="vp">Jeg er stadig kun kode. Send én mail og stem mig levende:</div>'
          +'<a class="vbtn" href="'+esc(mailto('Stem på '+NAME+' '+EMOJI,'Jeg stemmer på '+NAME+'! 🎬\\r\\nAnimér '+NAME+' først — denne mail tæller som én stemme.'))+'">✉️ Stem på '+NM+'</a>'
          +'<div class="vmeter"><div class="vbar"><i style="width:'+Math.round(100*mine/leader)+'%"></i></div>'
          +'<div class="vstat">'+mine+(mine===1?' stemme':' stemmer')+' · nr. '+rank+' af '+(cnt||31)+' · flest stemmer animeres først</div></div>');
      }
    }).catch(function(){ /* statisk hosting / offline: behold standardvisning, ingen behovs-bars */ });
  })();</script>
  <!-- agx-vote:end -->"""


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
    """The full agx-vote HTML+JS for one day (no trailing newline). The static
    markup is the fetch-failure default; live state re-renders it at runtime."""
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
            .replace("__NAME__", html.escape(name, quote=True))
            .replace("__EMOJI__", emoji)
            .replace("__VHEAD__", head)
            .replace("__VPLEA__", plea)
            .replace("__VCTA__", cta))


# stable anchors for FRESH injection, both occur exactly once per generated page
CSS_ANCHOR = ".agx-guess{margin:0 0 12px"
HTML_ANCHOR = '  <div class="agx-guess"'

# stable anchors of the LEGACY v1 block (no markers) for the one-time upgrade
V1_HTML_START = '<div class="agx-vote'
V1_HTML_END = "})();</script>"


def _region(doc, start_mark, end_mark):
    """[start, end) span covering start_mark..end_mark inclusive, plus the
    leading indentation of the start line and one trailing newline."""
    s = doc.index(start_mark)
    e = doc.index(end_mark, s) + len(end_mark)
    while s > 0 and doc[s - 1] in " \t":
        s -= 1
    if e < len(doc) and doc[e] == "\n":
        e += 1
    return s, e


def patch_file(path, day):
    doc = open(path, encoding="utf-8").read()
    orig = doc

    if HTML_MARK_START in doc:
        # ---- marker-based upgrade (v2+ -> current) ----
        if doc.count(HTML_MARK_START) != 1 or doc.count(HTML_MARK_END) != 1:
            return "ERROR: html markers not unique — not touched"
        if doc.count(CSS_MARK_START) != 1 or doc.count(CSS_MARK_END) != 1:
            return "ERROR: css markers not unique — not touched"
        s, e = _region(doc, CSS_MARK_START, CSS_MARK_END)
        doc = doc[:s] + VOTE_CSS + doc[e:]
        s, e = _region(doc, HTML_MARK_START, HTML_MARK_END)
        doc = doc[:s] + vote_block(day) + "\n" + doc[e:]
        label = "upgraded (markers)"
    elif "agx-vote" in doc:
        # ---- legacy v1 upgrade: verbatim CSS + anchor-scanned HTML region ----
        if doc.count(V1_VOTE_CSS) != 1:
            return "ERROR: legacy v1 CSS not found verbatim — not touched"
        s = doc.index(V1_HTML_START)
        e = doc.index(V1_HTML_END, s) + len(V1_HTML_END)
        if not doc[e:].lstrip().startswith('<div class="agx-guess"'):
            return "ERROR: legacy block end anchor mismatch — not touched"
        doc = doc.replace(V1_VOTE_CSS, VOTE_CSS, 1)
        # CSS replacement above shifts offsets — recompute the HTML region
        s = doc.index(V1_HTML_START)
        e = doc.index(V1_HTML_END, s) + len(V1_HTML_END)
        while s > 0 and doc[s - 1] in " \t":
            s -= 1
        if e < len(doc) and doc[e] == "\n":
            e += 1
        doc = doc[:s] + vote_block(day) + "\n" + doc[e:]
        label = "upgraded (v1 -> markers)"
    else:
        # ---- fresh injection into a never-patched page ----
        if doc.count(CSS_ANCHOR) != 1 or doc.count(HTML_ANCHOR) != 1:
            return (f"ERROR: anchors not unique (css={doc.count(CSS_ANCHOR)}, "
                    f"html={doc.count(HTML_ANCHOR)}) — not touched")
        doc = doc.replace(CSS_ANCHOR, VOTE_CSS + CSS_ANCHOR, 1)
        doc = doc.replace(HTML_ANCHOR, vote_block(day) + "\n" + HTML_ANCHOR, 1)
        label = "patched (fresh)"

    if doc == orig:
        return "unchanged (already current)"
    open(path, "w", encoding="utf-8").write(doc)
    return label


def main():
    changed = unchanged = errors = 0
    for day in range(1, 32):
        path = f"{DIR}/day-{day}.html"
        try:
            result = patch_file(path, day)
        except (FileNotFoundError, ValueError) as ex:
            result = f"ERROR: {ex.__class__.__name__}: {ex}"
        if result.startswith("ERROR"):
            errors += 1
        elif result.startswith("unchanged"):
            unchanged += 1
        else:
            changed += 1
        print(f"  day-{day}.html: {result}")
    print(f"done: {changed} changed, {unchanged} unchanged, {errors} errors (of 31)")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
