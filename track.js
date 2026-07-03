/* agentics.dk first-party tracking for the julikalender pages.
 *
 * The calendar runs in its own nginx container but is path-routed on
 * agentics.dk, so the main site's `vid` cookie (path=/) rides along on
 * same-origin requests — we just talk to the existing /api/tracking/*
 * endpoints. No third parties, matching the site's zero-tracker policy.
 */
(function () {
  "use strict";

  // Only track on the real domain (not tunnels, previews, or file://).
  if (location.hostname !== "agentics.dk") return;
  // Respect the site's consent choice (same-origin localStorage, so the main
  // site's banner covers these pages too). Explicit opt-out wins; the
  // undecided state matches the main site's first-party default.
  try {
    var consent = JSON.parse(localStorage.getItem("agentic-consent-v1") || "null");
    if (consent && consent.analytics === false) return;
  } catch (e) { /* no-op */ }

  var DAY = (function () {
    var m = location.pathname.match(/day-(\d+)\.html/);
    return m ? +m[1] : null;
  })();

  var UTM = {};
  try {
    var qs = new URLSearchParams(location.search);
    ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"].forEach(function (k) {
      var v = qs.get(k);
      if (v) UTM[k] = v;
    });
  } catch (e) { /* no-op */ }

  function post(url, payload) {
    var body = JSON.stringify(payload);
    if (navigator.sendBeacon) {
      navigator.sendBeacon(url, new Blob([body], { type: "application/json" }));
    } else {
      fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: body, keepalive: true }).catch(function () {});
    }
  }

  function event(name, props) {
    var p = Object.assign({ page: location.pathname, day: DAY }, UTM, props || {});
    post("/api/tracking/event", { name: name, props: p });
  }

  // 1. Init: creates the vid cookie on first visit and stores first-touch UTM.
  //    Forward this page's query so LinkedIn campaign params reach the store.
  var initUrl = "/api/tracking/init" + (location.search || "");
  fetch(initUrl, { credentials: "same-origin" })
    .then(function () {
      // 2. Pageview (needs the vid cookie to exist).
      post("/api/tracking/pageview", { path: location.pathname, referrer: document.referrer || "" });
      // 3. Campaign-sliceable view event: init only stores UTM on FIRST visit,
      //    so per-visit attribution lives in event props instead.
      event("julikalender_view", {});
    })
    .catch(function () {});

  // --- Interactions ---------------------------------------------------------

  // Calendar doors (calendar.html)
  document.addEventListener("click", function (e) {
    var door = e.target && e.target.closest && e.target.closest("a[href^='day-']");
    if (!door) return;
    var m = (door.getAttribute("href") || "").match(/day-(\d+)/);
    event("julikalender_door_click", { target_day: m ? +m[1] : null });
  });

  // Guess-the-model game (day pages)
  document.addEventListener("click", function (e) {
    var btn = e.target && e.target.closest && e.target.closest(".agx-guess .gbtn");
    if (!btn || btn.disabled) return;
    event("julikalender_guess", { guess: btn.getAttribute("data-m") });
  });

  // Video scrub completion — fires once when the visitor scrolls the avatar
  // clip to (near) the end. Only on day pages with the scrubbed hero.
  var scrubDone = false;
  var scrubTimer = setInterval(function () {
    var v = document.getElementById("heroVideo");
    if (!v) { clearInterval(scrubTimer); return; }
    if (!scrubDone && v.duration && v.currentTime > v.duration - 0.6) {
      scrubDone = true;
      clearInterval(scrubTimer);
      event("julikalender_scrub_complete", {});
    }
  }, 1000);

  // Time on page (same shape as the main site's page_time event).
  var start = Date.now();
  var fired = false;
  function sendDuration() {
    if (fired) return;
    fired = true;
    var duration_sec = Math.round((Date.now() - start) / 1000);
    if (duration_sec < 1) return;
    post("/api/tracking/event", { name: "page_time", props: { path: location.pathname, duration_sec: duration_sec } });
  }
  document.addEventListener("visibilitychange", function () {
    if (document.hidden) sendDuration();
  });
  window.addEventListener("pagehide", sendDuration);
})();
