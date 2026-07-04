/* Live feedback på dag-siderne: lytter på /api/events (SSE) og reagerer når
 * NETOP denne avatar fodres/stemmes — toast + behovs-bars opdateres uden
 * reload. Kalenderen har sin egen toast-håndtering; denne fil no-op'er uden
 * en #agxVote-boks. Ingen tredjeparter, ingen cookies.
 */
(function () {
  'use strict';

  var box = document.getElementById('agxVote');
  if (!box || typeof EventSource === 'undefined') return;

  var SLUG = box.getAttribute('data-slug');
  var NAME = box.getAttribute('data-name') || SLUG;
  var NEED_LABEL = { food: '🍖 mad', water: '💧 vand', love: '❤️ kærlighed' };

  // --- toast ----------------------------------------------------------------
  var css = document.createElement('style');
  css.textContent =
    '.agx-toast{position:fixed;left:50%;bottom:88px;transform:translate(-50%,16px);' +
    'background:rgba(9,11,17,.92);border:1px solid rgba(255,255,255,.16);color:#eef1f7;' +
    'padding:10px 16px;border-radius:999px;font:600 13px/1.4 -apple-system,"Segoe UI",Inter,system-ui,sans-serif;' +
    'z-index:2147483200;opacity:0;transition:opacity .25s ease,transform .25s ease;' +
    'box-shadow:0 18px 50px -18px rgba(0,0,0,.9);pointer-events:none;max-width:min(90vw,420px);text-align:center}' +
    '.agx-toast.show{opacity:1;transform:translate(-50%,0)}';
  document.head.appendChild(css);

  var toastEl = null, toastTimer = null;
  function toast(msg) {
    if (!toastEl) {
      toastEl = document.createElement('div');
      toastEl.className = 'agx-toast';
      toastEl.setAttribute('role', 'status');
      document.body.appendChild(toastEl);
    }
    toastEl.textContent = msg;
    // reflow så transition genstarter ved hurtige beskeder
    toastEl.classList.remove('show');
    void toastEl.offsetWidth;
    toastEl.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toastEl.classList.remove('show'); }, 4200);
  }

  // --- DOM-opdatering af den allerede renderede widget -----------------------
  function refresh() {
    fetch('api/votes').then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(function (d) {
      var av = (d.avatars || {})[SLUG];
      if (!av) return;

      var bars = box.querySelectorAll('.nrow .need');
      if (av.state === 'awake' && bars.length === 3) {
        var order = ['love', 'food', 'water'];
        var low = false;
        for (var i = 0; i < 3; i++) {
          var lv = Math.max(0, Math.min(100, Math.round(av.needs[order[i]] || 0)));
          if (lv < 25) low = true;
          bars[i].classList.toggle('low', lv < 25);
          var fill = bars[i].querySelector('.nb i');
          if (fill) fill.style.width = lv + '%';
        }
        var vt = box.querySelector('.vt');
        if (vt) {
          vt.className = 'vt ' + (low ? 'low' : 'ok');
          vt.textContent = NAME + (low ? ' er SULTEN!' : ' har det godt');
        }
        return;
      }

      // Sovende: opdater stemmetal/bar hvis den visning er på skærmen
      var stat = box.querySelector('.vstat');
      if (stat && d.votes) {
        var mine = d.votes[SLUG] || 0, leader = 1, rank = 1, cnt = 0;
        Object.keys(d.votes).forEach(function (s) {
          cnt++;
          if (d.votes[s] > leader) leader = d.votes[s];
          if (d.votes[s] > mine) rank++;
        });
        stat.textContent = mine + (mine === 1 ? ' stemme' : ' stemmer') + ' · nr. ' + rank + ' af ' + (cnt || 31) + ' · flest stemmer animeres først';
        var bar = box.querySelector('.vbar i');
        if (bar) bar.style.width = Math.round(100 * mine / leader) + '%';
      }

      // Tilstandsskift (vækket/genoplivet/faldet i søvn) kræver widget-rerender
      // — den inline renderer kører kun ved load, så tag et reload dér.
      var renderedAwake = bars.length === 3;
      if ((av.state === 'awake') !== renderedAwake) {
        setTimeout(function () { location.reload(); }, 1800);
      }
    }).catch(function () { /* offline/statisk: stille */ });
  }

  // --- SSE ------------------------------------------------------------------
  var es = new EventSource('api/events');
  es.addEventListener('activity', function (e) {
    var ev;
    try { ev = JSON.parse(e.data); } catch (err) { return; }
    if (!ev || ev.slug !== SLUG) return;

    if (ev.type === 'feed' && ev.need) {
      toast(NAME + ' fik ' + (NEED_LABEL[ev.need] || ev.need) + ' — tak! 🧡');
    } else if (ev.type === 'revive') {
      toast('😴→😃 ' + NAME + ' blev genoplivet' + (ev.need ? ' med ' + (NEED_LABEL[ev.need] || ev.need) : '') + '!');
    } else if (ev.type === 'wake') {
      toast('🎬 ' + NAME + ' er vågnet!');
    } else {
      toast('✉️ Ny stemme til ' + NAME + ' — ' + ev.votes + ' i alt!');
    }
    refresh();
  });
  // backlog-eventet ignoreres bevidst: ingen toasts for historik ved load.
})();
