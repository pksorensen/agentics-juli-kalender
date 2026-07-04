#!/usr/bin/env python3
# Patches a dismiss/reopen toggle for the fixed ".agx-story" info card into the
# 29 STATIC day-N.html pages (day-1 and day-4..day-31 — day-2/day-3 are the
# real-video pages and are explicitly OUT OF SCOPE for this script).
#
# On these single-screen 100vh pages the fixed bottom-left ".agx-story" card
# (lore/tags/vote-widget/guess-widget/nav) can visually cover the avatar or a
# CTA behind it. This adds:
#   - a small "✕" dismiss button inside the existing '.agx-story .h' header row
#   - a small round reopen button (that day's emoji) next to the '.agx-badge',
#     hidden by default
#   - CSS for both + '.agx-story.agx-hidden{display:none}'
#   - a tiny inline IIFE that toggles a CSS class (never removes the aside from
#     the DOM, so the existing vote-widget fetch / guess-widget click handlers
#     keep working once reopened) and persists the collapsed state in
#     sessionStorage (NOT localStorage — resets every new browser session so
#     the campaign CTA / guess-widget still gets seen on fresh visits)
#
# IDEMPOTENT / UPGRADEABLE, same discipline as tools/inject_vote_block.py:
#   - marker-based: '<!-- agx-story-toggle -->' present anywhere in the file
#     means this page is already patched -> skipped (no-op).
#   - fresh injection otherwise, via three stable, verified-unique anchors:
#       CSS:    '</style>' that closes '<style id="agx-chrome-css">'
#       header: '<div class="h">...</div>' (single line, right after the
#               '<aside class="agx agx-story"' opening tag)
#       badge:  '<div class="agx agx-badge" ...>...</div>' (single line)
#     plus the script is inserted immediately before the LAST
#     '<script src="track.js" defer></script>' tag, which must stay last.
#
# tools/assemble.py's CHROME template gets the identical CSS/HTML/JS baked in
# (see the sibling edit made alongside this script) so any FUTURE fresh
# generation already includes the toggle — but assemble.py's inject() is never
# invoked by this script; the 29 existing files are patched here, in place.
#
# Usage: python3 tools/add_story_toggle.py
import re
import sys

DIR = "/home/claude-desktop/experiments/animated-avatar"

# day -> emoji (reopen button glyph) — kept in sync with inject_vote_block.VOTE_ROSTER
EMOJI = {
 1:"🔮", 4:"🫧", 5:"👨‍🚀", 6:"👻", 7:"🐱", 8:"🕊️", 9:"👾", 10:"🪼",
 11:"🦉", 12:"🪞", 13:"🔥", 14:"🐟", 15:"🗿", 16:"🌱", 17:"🐉", 18:"✨",
 19:"🐦", 20:"🍡", 21:"⚡", 22:"💎", 23:"☁️", 24:"🐦‍⬛", 25:"⚙️", 26:"❄️",
 27:"🗼", 28:"☀️", 29:"🌙", 30:"🐝", 31:"🚀",
}

TARGET_DAYS = [1] + list(range(4, 32))  # 29 days total, excludes 2 and 3

MARKER = "<!-- agx-story-toggle -->"

STYLE_CLOSE = "</style>"
STYLE_OPEN = '<style id="agx-chrome-css">'
H_ANCHOR_RE = re.compile(r'(<div class="h">.*?</div></div></div>)')
BADGE_RE = re.compile(r'(<div class="agx agx-badge"[^>]*>.*?</div>)')
TRACKJS = '<script src="track.js" defer></script>'

TOGGLE_CSS = f"""/* {MARKER} */
.agx-story.agx-hidden{{display:none}}
.agx-story .x{{position:absolute;top:10px;right:10px;width:26px;height:26px;display:flex;
  align-items:center;justify-content:center;border-radius:999px;border:1px solid rgba(255,255,255,.16);
  background:rgba(255,255,255,.06);color:#eef1f7;font-size:13px;line-height:1;cursor:pointer;
  transition:background .15s,transform .15s;padding:0}}
.agx-story .x:hover{{background:rgba(255,255,255,.14);transform:scale(1.06)}}
.agx-story .x:focus-visible{{outline:2px solid var(--agx);outline-offset:2px}}
.agx-reopen{{left:16px;bottom:16px;width:42px;height:42px;border-radius:999px;display:flex;
  align-items:center;justify-content:center;font-size:19px;line-height:1;cursor:pointer;
  background:rgba(9,11,17,.55);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);
  border:1px solid rgba(255,255,255,.13);color:#eef1f7;padding:0}}
.agx-reopen:hover{{background:rgba(9,11,17,.72)}}
.agx-reopen:focus-visible{{outline:2px solid var(--agx);outline-offset:2px}}
.agx-reopen[hidden]{{display:none}}
@media (max-width:560px){{.agx-reopen{{left:12px;bottom:12px}}}}
"""

def make_x_button():
    return '<button type="button" class="x" id="agxStoryX" aria-label="Skjul info">✕</button>'


def make_reopen_button(day):
    emoji = EMOJI[day]
    name = None  # filled via aria-label text built from page; keep generic-safe fallback
    return (f'<button type="button" class="agx agx-reopen" id="agxStoryReopen" '
            f'aria-label="Vis info om avataren" hidden>{emoji}</button>')


def make_script(day):
    return f"""<script>// {MARKER}
(function(){{
  var DAY={day}, KEY='agx_hide_'+DAY;
  var card=document.querySelector('.agx-story'), reopen=document.getElementById('agxStoryReopen'),
      x=document.getElementById('agxStoryX');
  if(!card||!reopen||!x) return;
  function hide(){{card.classList.add('agx-hidden');reopen.hidden=false;try{{sessionStorage.setItem(KEY,'1');}}catch(e){{}}}}
  function show(){{card.classList.remove('agx-hidden');reopen.hidden=true;try{{sessionStorage.removeItem(KEY);}}catch(e){{}}}}
  var wasHidden=false; try{{wasHidden=sessionStorage.getItem(KEY)==='1';}}catch(e){{}}
  if(wasHidden){{card.classList.add('agx-hidden');reopen.hidden=false;}}
  x.addEventListener('click',hide);
  reopen.addEventListener('click',show);
}})();</script>
"""


def patch_file(path, day):
    doc = open(path, encoding="utf-8").read()
    orig = doc

    if MARKER in doc:
        return "unchanged (already patched)"

    # ---- 1. CSS: insert before the closing </style> of the chrome style block ----
    if STYLE_OPEN not in doc:
        return "ERROR: agx-chrome-css style block not found — not touched"
    style_start = doc.index(STYLE_OPEN)
    style_end = doc.index(STYLE_CLOSE, style_start)
    if style_end == -1:
        return "ERROR: closing </style> not found — not touched"
    doc = doc[:style_end] + TOGGLE_CSS + doc[style_end:]

    # ---- 2. header row: insert the ✕ button inside '.agx-story .h' row ----
    h_matches = list(H_ANCHOR_RE.finditer(doc))
    if len(h_matches) != 1:
        return f"ERROR: '.h' header anchor not unique (found {len(h_matches)}) — not touched"
    m = h_matches[0]
    doc = doc[:m.end(1)] + make_x_button() + doc[m.end(1):]

    # ---- 3. badge row: insert the reopen button right after it ----
    badge_matches = list(BADGE_RE.finditer(doc))
    if len(badge_matches) != 1:
        return f"ERROR: '.agx-badge' anchor not unique (found {len(badge_matches)}) — not touched"
    m = badge_matches[0]
    doc = doc[:m.end(1)] + "\n" + make_reopen_button(day) + doc[m.end(1):]

    # ---- 4. script: insert immediately before the LAST track.js tag ----
    idx = doc.rfind(TRACKJS)
    if idx == -1:
        return "ERROR: track.js script tag not found — not touched"
    doc = doc[:idx] + make_script(day) + doc[idx:]

    if doc == orig:
        return "unchanged (no-op)"
    open(path, "w", encoding="utf-8").write(doc)
    return "patched"


def main():
    changed = unchanged = errors = 0
    for day in TARGET_DAYS:
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
    print(f"done: {changed} changed, {unchanged} unchanged, {errors} errors (of {len(TARGET_DAYS)})")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
