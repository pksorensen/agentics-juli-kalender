#!/usr/bin/env python3
# Patches a "book a meeting" block ("agx-meet") into all 31 day-N.html pages
# IN PLACE. The block sits right after the agx-vote block and before the
# agx-guess widget — same story-card flow, same idempotent marker convention
# as tools/inject_vote_block.py (safe to re-run any time).
#
# What it does: shows the avatar's own address (<slug>@agent.agentics.dk) and
# tells visitors to add it as a guest on a Teams/Google Meet invite. There is
# no join/auto-attend integration yet — server.js only DETECTS and LOGS that
# an invite arrived (see docs/meeting-invites.md), so this is deliberately
# framed as "I'm watching" rather than "I'll show up".
#
# Usage: python3 tools/inject_meet_block.py
import html
import os
import re
import sys

DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# day -> (slug, name) — reuses the same roster as inject_vote_block.py
ROSTER = {
 1:("aura","AURA"), 2:("raev","Ræv"), 3:("agent01","Agent-01"), 4:("nova","Nova"),
 5:("comet","Comet"), 6:("boo","Boo"), 7:("neko","Neko"), 8:("tsuru","Tsuru"),
 9:("bit","Bit"), 10:("lumen","Lumen"), 11:("ugla","Ugla"), 12:("chrome","Chrome"),
 13:("ember","Ember"), 14:("koi","Koi"), 15:("golem","Golem"), 16:("sprout","Sprout"),
 17:("draco","Draco"), 18:("aster","Aster"), 19:("lundi","Lundi"), 20:("mochi","Mochi"),
 21:("volt","Volt"), 22:("prism","Prism"), 23:("nimbus","Nimbus"), 24:("ravn","Ravn"),
 25:("cog","Cog"), 26:("frost","Frost"), 27:("beacon","Beacon"), 28:("sol","Sol"),
 29:("luna","Luna"), 30:("bi","Bi"), 31:("vega","Vega"),
}

CSS_MARK_START = "/* agx-meet-css:start */"
CSS_MARK_END = "/* agx-meet-css:end */"
HTML_MARK_START = "<!-- agx-meet:start -->"
HTML_MARK_END = "<!-- agx-meet:end -->"

MEET_CSS = (CSS_MARK_START + "\n" +
""".agx-meet{margin:0 0 12px;padding-top:10px;border-top:1px solid rgba(255,255,255,.09)}
.agx-meet .mt{font-size:12.5px;font-weight:700;letter-spacing:.01em;margin-bottom:2px;color:#eef1f7}
.agx-meet .mp{font-size:11.5px;color:#aeb6c6;line-height:1.45;margin-bottom:6px}
.agx-meet .maddr{display:block;font-size:11.5px;font-weight:700;color:var(--agx);word-break:break-all;
  padding:6px 9px;border-radius:8px;border:1px dashed rgba(255,255,255,.2);background:rgba(255,255,255,.03);
  text-decoration:none;margin-bottom:5px}
.agx-meet .maddr:hover{border-color:var(--agx);background:rgba(255,255,255,.06)}
.agx-meet .mnote{font-size:10px;color:#7d8494;line-height:1.4}
""" + CSS_MARK_END + "\n")

# Danish copy — matches the tone/language of the rest of the day pages.
HTML_TMPL = """  <!-- agx-meet:start -->
  <div class="agx-meet">
    <div class="mt">📅 Book et møde med __NAME__</div>
    <div class="mp">Tilføj __NAME__ som gæst på en Teams- eller Google Meet-invitation:</div>
    <a class="maddr" href="mailto:__SLUG__@agent.agentics.dk">__SLUG__@agent.agentics.dk</a>
    <div class="mnote">Eksperimentelt: __NAME__ dukker endnu ikke selv op til mødet — vi holder bare øje med hvem der spørger. 👀</div>
  </div>
  <!-- agx-meet:end -->"""


def meet_block(day):
    slug, name = ROSTER[day]
    return (HTML_TMPL
            .replace("__SLUG__", slug)
            .replace("__NAME__", html.escape(name, quote=True)))


def _region(doc, start_mark, end_mark):
    s = doc.index(start_mark)
    e = doc.index(end_mark, s) + len(end_mark)
    while s > 0 and doc[s - 1] in " \t":
        s -= 1
    if e < len(doc) and doc[e] == "\n":
        e += 1
    return s, e


def patch(day):
    path = f"{DIR}/day-{day}.html"
    with open(path, "r", encoding="utf-8") as f:
        doc = f.read()

    css = meet_css = MEET_CSS
    html_block = meet_block(day)

    if CSS_MARK_START in doc:
        s, e = _region(doc, CSS_MARK_START, CSS_MARK_END)
        doc = doc[:s] + meet_css + doc[e:]
    else:
        anchor = "/* agx-vote-css:end */\n"
        i = doc.index(anchor) + len(anchor)
        doc = doc[:i] + meet_css + doc[i:]

    if HTML_MARK_START in doc:
        s, e = _region(doc, HTML_MARK_START, HTML_MARK_END)
        doc = doc[:s] + html_block + "\n" + doc[e:]
    else:
        anchor = "<!-- agx-vote:end -->\n"
        i = doc.index(anchor) + len(anchor)
        indent = re.match(r"[ \t]*", doc[i:]).group(0)
        doc = doc[:i] + indent + html_block + "\n" + doc[i:]

    with open(path, "w", encoding="utf-8") as f:
        f.write(doc)


def main():
    for day in range(1, 32):
        patch(day)
        print(f"day-{day}.html: patched")


if __name__ == "__main__":
    sys.exit(main())
