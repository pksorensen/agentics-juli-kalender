// agentics.dk juli-kalender — statisk site + stemme-API i én lille Node-service.
// Erstatter nginx: index=calendar.html, ingen trailing-slash-redirects (sub-path-proxy),
// Range-support via express.static/send (PÅKRÆVET for dag-2 scroll-scrub-videoen).
'use strict';

const path = require('path');
const fs = require('fs');
const fsp = fs.promises;
const express = require('express');

const ROOT = __dirname;
const PORT = parseInt(process.env.PORT, 10) || 80;
const VOTE_GOAL = parseInt(process.env.VOTE_GOAL, 10) || 1000;
// DATA_DIR har forrang; USER_DATA_DIR matcher Coolify-opsætningens volume-navn
const DATA_DIR = path.resolve(process.env.DATA_DIR || process.env.USER_DATA_DIR || './data');
const VOTES_FILE = path.join(DATA_DIR, 'votes.json');
const MAX_MESSAGE_IDS = 50000; // FIFO-cap på husket dedupe-liste

// Avatar-roster — dag 1..31. GET /api/votes skal ALTID indeholde alle 31 slugs.
const SLUGS = [
  'aura', 'raev', 'agent01', 'nova', 'comet', 'boo', 'neko', 'tsuru',
  'bit', 'lumen', 'ugla', 'chrome', 'ember', 'koi', 'golem', 'sprout',
  'draco', 'aster', 'lundi', 'mochi', 'volt', 'prism', 'nimbus', 'ravn',
  'cog', 'frost', 'beacon', 'sol', 'luna', 'bi', 'vega',
];
const SLUG_SET = new Set(SLUGS);

// ---------------------------------------------------------------------------
// Feeding-system (docs/feeding-spec.md): behov, lazy forfald, livscyklus.
// ---------------------------------------------------------------------------
const NEEDS = ['love', 'food', 'water'];
const NEED_PRIORITY = ['food', 'water', 'love']; // ved flere match i samme tekst
const NEED_KEYWORDS = {
  food: ['mad', 'food', 'foder', '🍖', '🍕', '🍎'],
  water: ['vand', 'water', '💧', '🌊'],
  // '❤' (uden variation selector) matcher også '❤️'
  love: ['kærlighed', 'love', 'elsker', 'hjerte', '❤', '💛', '🧡'],
};
const AVATAR_STATES = new Set(['sleeping', 'awake', 'asleep_again']);
const FEED_AMOUNT = 30;   // +30 pr. feed-mail, cap 100
const REVIVE_LEVEL = 40;  // alle behov ved genoplivning fra asleep_again
const WAKE_LEVEL = 100;   // alle behov ved POST /api/wake
const DECAY_PER_MS = 100 / (48 * 60 * 60 * 1000); // 100 -> 0 på 48 timer (2.0833/time)

// avatars[slug] = { state, needs:{love|food|water:{level,updatedAt-ms}}, feeds, awokeAt }
const avatars = Object.create(null);

function clampLevel(x) {
  return Math.min(100, Math.max(0, x));
}

function round1(x) {
  return Math.round(x * 10) / 10;
}

function makeNeed(level, now) {
  return { level, updatedAt: now };
}

function makeAvatar(state, level, now) {
  return {
    state,
    needs: {
      love: makeNeed(level, now),
      food: makeNeed(level, now),
      water: makeNeed(level, now),
    },
    feeds: { love: 0, food: 0, water: 0 },
    awokeAt: state === 'awake' ? now : null,
  };
}

// Lazy forfald: kun vågne avatarer forfalder; niveauet beregnes ved læsning.
function decayedLevel(need, now) {
  return clampLevel(need.level - (now - need.updatedAt) * DECAY_PER_MS);
}

function currentLevels(avatar, now) {
  const out = {};
  for (const n of NEEDS) {
    out[n] = avatar.state === 'awake'
      ? round1(decayedLevel(avatar.needs[n], now))
      : round1(clampLevel(avatar.needs[n].level));
  }
  return out;
}

// Lazy tilstandsovergang: vågen avatar med alle behov = 0 er "sovet igen".
// Returnerer true hvis tilstanden ændrede sig (kalderen bør persistere).
function refreshAvatar(slug, now) {
  const avatar = avatars[slug];
  if (avatar.state !== 'awake') return false;
  const allZero = NEEDS.every((n) => decayedLevel(avatar.needs[n], now) <= 0);
  if (!allZero) return false;
  for (const n of NEEDS) avatar.needs[n] = makeNeed(0, now);
  avatar.state = 'asleep_again';
  console.log(`[state] ${slug}: awake -> asleep_again (alle behov = 0)`);
  return true;
}

// Nøgleords-parsing: subject før body; derefter food > water > love. null = intet match.
function parseNeed(subject, body) {
  for (const text of [subject, body]) {
    if (typeof text !== 'string' || !text) continue;
    const lower = text.toLowerCase();
    for (const need of NEED_PRIORITY) {
      if (NEED_KEYWORDS[need].some((kw) => lower.includes(kw))) return need;
    }
  }
  return null;
}

function sanitizeAvatar(stored, now) {
  const state = AVATAR_STATES.has(stored.state) ? stored.state : 'sleeping';
  const av = makeAvatar(state, 0, now);
  const needsIn = (stored.needs && typeof stored.needs === 'object') ? stored.needs : {};
  for (const n of NEEDS) {
    const raw = needsIn[n];
    const level = (raw && Number.isFinite(raw.level)) ? clampLevel(raw.level) : 0;
    const updatedAt = (raw && Number.isFinite(raw.updatedAt)) ? raw.updatedAt : now;
    av.needs[n] = { level, updatedAt };
  }
  const feedsIn = (stored.feeds && typeof stored.feeds === 'object') ? stored.feeds : {};
  for (const n of NEEDS) {
    av.feeds[n] = (Number.isInteger(feedsIn[n]) && feedsIn[n] >= 0) ? feedsIn[n] : 0;
  }
  av.awokeAt = Number.isFinite(stored.awokeAt)
    ? stored.awokeAt
    : (state === 'awake' ? now : null);
  return av;
}

// Migration: votes.json uden avatars-felt (eller frisk boot) -> syntetisér:
// alle sover, undtagen ræv (dag 2) og agent01 (dag 3) der seedes vågne med fulde behov.
function hydrateAvatars(raw) {
  const now = Date.now();
  const hasStored = !!(raw && typeof raw === 'object');
  for (const slug of SLUGS) {
    const stored = hasStored ? raw[slug] : undefined;
    if (stored && typeof stored === 'object') {
      avatars[slug] = sanitizeAvatar(stored, now);
    } else if (hasStored) {
      avatars[slug] = makeAvatar('sleeping', 0, now); // ny slug i roster
    } else {
      avatars[slug] = (slug === 'raev' || slug === 'agent01')
        ? makeAvatar('awake', WAKE_LEVEL, now)
        : makeAvatar('sleeping', 0, now);
    }
  }
  if (!hasStored) {
    console.log('[boot] no avatars in state — synthesized (all sleeping, raev+agent01 seeded awake)');
  }
}

// ---------------------------------------------------------------------------
// Persistens: JSON på disk, atomisk skrivning (tmp + rename), indlæses ved boot.
// ---------------------------------------------------------------------------
const votes = Object.create(null);
for (const slug of SLUGS) votes[slug] = 0;
let seenMessageIds = new Set(); // dedupe
let messageIdOrder = [];        // FIFO-orden for cap

function loadState() {
  let data = null;
  try {
    const raw = fs.readFileSync(VOTES_FILE, 'utf8');
    data = JSON.parse(raw);
    if (data && typeof data.votes === 'object' && data.votes !== null) {
      for (const slug of SLUGS) {
        const n = data.votes[slug];
        if (Number.isInteger(n) && n >= 0) votes[slug] = n;
      }
    }
    if (Array.isArray(data && data.messageIds)) {
      messageIdOrder = data.messageIds
        .filter((id) => typeof id === 'string')
        .slice(-MAX_MESSAGE_IDS);
      seenMessageIds = new Set(messageIdOrder);
    }
    console.log(`[boot] loaded state from ${VOTES_FILE} (total=${totalVotes()}, messageIds=${seenMessageIds.size})`);
  } catch (err) {
    data = null;
    if (err.code === 'ENOENT') {
      console.log(`[boot] no existing state at ${VOTES_FILE} — starting fresh`);
    } else {
      console.error(`[boot] could not load ${VOTES_FILE}: ${err.message} — starting fresh`);
    }
  }
  hydrateAvatars(data ? data.avatars : undefined);
}

// Skrivninger serialiseres i en kæde, så tmp+rename aldrig overlapper.
let saveChain = Promise.resolve();
function saveState() {
  const snapshot = JSON.stringify({
    votes: { ...votes },
    messageIds: messageIdOrder.slice(),
    avatars, // serialiseres synkront her, så snapshot er konsistent
  });
  saveChain = saveChain.then(async () => {
    const tmp = `${VOTES_FILE}.tmp`;
    await fsp.writeFile(tmp, snapshot, 'utf8');
    await fsp.rename(tmp, VOTES_FILE);
  }).catch((err) => {
    console.error(`[persist] write failed: ${err.message}`);
  });
  return saveChain;
}

function totalVotes() {
  let total = 0;
  for (const slug of SLUGS) total += votes[slug];
  return total;
}

function rememberMessageId(id) {
  seenMessageIds.add(id);
  messageIdOrder.push(id);
  while (messageIdOrder.length > MAX_MESSAGE_IDS) {
    const oldest = messageIdOrder.shift();
    seenMessageIds.delete(oldest);
  }
}

fs.mkdirSync(DATA_DIR, { recursive: true });
loadState();

// ---------------------------------------------------------------------------
// SSE-aktivitetsstrøm: ring-buffer (seneste 20, ældste først) + klient-Set.
// Ingen persistens; events bærer INGEN afsenderdata (kun slug/type/need/counts).
// ---------------------------------------------------------------------------
const ACTIVITY_BUFFER_MAX = 20;
const recentActivity = []; // ældste først
const sseClients = new Set();

// Skrivning til død klient må aldrig crashe — fjern klienten og gå videre.
function sseWrite(client, chunk) {
  try {
    client.write(chunk);
  } catch (err) {
    sseClients.delete(client);
  }
}

function broadcastActivity(type, slug, need) {
  const event = {
    type,
    slug,
    need: need || null,
    votes: votes[slug],
    total: totalVotes(),
    ts: Date.now(),
  };
  recentActivity.push(event);
  while (recentActivity.length > ACTIVITY_BUFFER_MAX) recentActivity.shift();
  const msg = `event: activity\ndata: ${JSON.stringify(event)}\n\n`;
  for (const client of sseClients) sseWrite(client, msg);
}

// Heartbeat-kommentar hver 25 s, så proxies ikke dræber idle forbindelser.
// unref(): timeren må aldrig holde processen i live ved shutdown.
const sseHeartbeat = setInterval(() => {
  for (const client of sseClients) sseWrite(client, ': hb\n\n');
}, 25000);
sseHeartbeat.unref();

// ---------------------------------------------------------------------------
// App
// ---------------------------------------------------------------------------
const app = express();
app.disable('x-powered-by');

// --- API ---

app.get('/api/health', (req, res) => {
  res.json({ ok: true });
});

// Offentlig SSE-strøm (ingen auth). Backlog ved connect, derefter live events.
app.get('/api/events', (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('X-Accel-Buffering', 'no'); // ingen buffering i nginx/proxies
  res.flushHeaders();

  // 'error' på socket/stream (fx skrivning efter disconnect) må aldrig crashe.
  res.on('error', () => sseClients.delete(res));

  sseWrite(res, `event: backlog\ndata: ${JSON.stringify({ events: recentActivity })}\n\n`);
  sseClients.add(res);
  req.on('close', () => sseClients.delete(res));
});

app.get('/api/votes', (req, res) => {
  const now = Date.now();
  let changed = false;
  for (const slug of SLUGS) {
    if (refreshAvatar(slug, now)) changed = true;
  }
  if (changed) saveState();
  const out = {};
  const avatarsOut = {};
  for (const slug of SLUGS) {
    out[slug] = votes[slug];
    const av = avatars[slug];
    avatarsOut[slug] = {
      state: av.state,
      needs: currentLevels(av, now),
      feeds: { ...av.feeds },
      awokeAt: av.awokeAt,
    };
  }
  res.json({ goal: VOTE_GOAL, total: totalVotes(), votes: out, avatars: avatarsOut });
});

app.post('/api/vote', express.json({ limit: '64kb' }), (req, res) => {
  const token = process.env.VOTE_WEBHOOK_TOKEN;
  if (!token) {
    return res.status(503).json({ ok: false, error: 'not-configured' });
  }
  const auth = req.get('authorization') || '';
  if (auth !== `Bearer ${token}`) {
    return res.status(401).json({ ok: false, error: 'unauthorized' });
  }

  const body = (req.body && typeof req.body === 'object') ? req.body : {};
  let slug = null;
  if (typeof body.slug === 'string' && body.slug.trim()) {
    slug = body.slug.trim().toLowerCase();
  } else if (typeof body.recipient === 'string' && body.recipient.includes('@')) {
    slug = body.recipient.split('@')[0].trim().toLowerCase();
  }
  if (!slug || !SLUG_SET.has(slug)) {
    return res.status(404).json({ ok: false, error: 'unknown-slug' });
  }

  const messageId = (typeof body.messageId === 'string' && body.messageId) ? body.messageId : null;
  if (messageId && seenMessageIds.has(messageId)) {
    return res.json({
      ok: true,
      duplicate: true,
      slug,
      votes: votes[slug],
      total: totalVotes(),
    });
  }

  const now = Date.now();
  const avatar = avatars[slug];
  refreshAvatar(slug, now); // vågen med alle behov forfaldet til 0 -> asleep_again

  votes[slug] += 1; // hver mail tæller stadig som stemme/engagement, uanset tilstand
  if (messageId) rememberMessageId(messageId);

  let action = 'vote'; // sovende avatar: mail = wake-stemme (eksisterende adfærd)
  let need = null;
  let levels = null;
  if (avatar.state === 'awake') {
    action = 'feed';
    need = parseNeed(body.subject, body.body) || 'love'; // intet match -> love
    const fed = Math.min(100, decayedLevel(avatar.needs[need], now) + FEED_AMOUNT);
    avatar.needs[need] = makeNeed(fed, now);
    avatar.feeds[need] += 1;
    levels = currentLevels(avatar, now);
  } else if (avatar.state === 'asleep_again') {
    action = 'revive'; // én hvilken som helst feed-mail genopliver
    need = parseNeed(body.subject, body.body) || 'love';
    for (const n of NEEDS) avatar.needs[n] = makeNeed(REVIVE_LEVEL, now);
    avatar.feeds[need] += 1;
    avatar.state = 'awake';
    avatar.awokeAt = now;
    console.log(`[state] ${slug}: asleep_again -> awake (revive via feed need=${need})`);
    levels = currentLevels(avatar, now);
  }

  saveState();
  broadcastActivity(action, slug, need);
  console.log(`[vote] slug=${slug} action=${action}${need ? ` need=${need}` : ''} votes=${votes[slug]} total=${totalVotes()} messageId=${messageId || '-'}`);
  const response = { ok: true, slug, action, votes: votes[slug], total: totalVotes() };
  if (need) response.need = need;
  if (levels) response.levels = levels;
  res.json(response);
});

// Kaldes når en avatar er genereret og deployet: state=awake, alle behov = 100.
app.post('/api/wake', express.json({ limit: '16kb' }), (req, res) => {
  const token = process.env.VOTE_WEBHOOK_TOKEN;
  if (!token) {
    return res.status(503).json({ ok: false, error: 'not-configured' });
  }
  const auth = req.get('authorization') || '';
  if (auth !== `Bearer ${token}`) {
    return res.status(401).json({ ok: false, error: 'unauthorized' });
  }

  const body = (req.body && typeof req.body === 'object') ? req.body : {};
  const slug = (typeof body.slug === 'string') ? body.slug.trim().toLowerCase() : '';
  if (!slug || !SLUG_SET.has(slug)) {
    return res.status(404).json({ ok: false, error: 'unknown-slug' });
  }

  const now = Date.now();
  const avatar = avatars[slug];
  const prev = avatar.state;
  for (const n of NEEDS) avatar.needs[n] = makeNeed(WAKE_LEVEL, now);
  avatar.state = 'awake';
  if (prev !== 'awake' || !Number.isFinite(avatar.awokeAt)) avatar.awokeAt = now;
  if (prev !== 'awake') {
    console.log(`[state] ${slug}: ${prev} -> awake (POST /api/wake)`);
  }
  saveState();
  broadcastActivity('wake', slug, null);
  res.json({
    ok: true,
    slug,
    state: 'awake',
    needs: currentLevels(avatar, now),
    votes: votes[slug],
    total: totalVotes(),
  });
});

// JSON-parse-fejl fra express.json -> 400 i stedet for HTML-fejlside
app.use('/api', (err, req, res, next) => {
  if (err && err.type === 'entity.parse.failed') {
    return res.status(400).json({ ok: false, error: 'bad-json' });
  }
  next(err);
});

// --- Statiske filer ---

// Server-/konfig-filer må ALDRIG serveres som web-indhold.
const BLOCKED_EXACT = new Set([
  '/server.js',
  '/package.json',
  '/package-lock.json',
  '/dockerfile',
  '/.dockerignore',
  '/.gitignore',
  '/.env',
]);
const BLOCKED_PREFIXES = ['/node_modules/', '/data/', '/.git/'];
// Hvis DATA_DIR ligger inde i web-roden, blokeres også dén sti.
const dataRel = path.relative(ROOT, DATA_DIR);
if (dataRel && !dataRel.startsWith('..') && !path.isAbsolute(dataRel)) {
  const p = '/' + dataRel.split(path.sep).join('/').toLowerCase();
  BLOCKED_EXACT.add(p);
  BLOCKED_PREFIXES.push(p + '/');
}

app.use((req, res, next) => {
  let decoded;
  try {
    decoded = decodeURIComponent(req.path);
  } catch {
    return res.status(400).type('text').send('Bad request');
  }
  const p = decoded.toLowerCase();
  const blocked =
    BLOCKED_EXACT.has(p) ||
    p === '/node_modules' || p === '/data' || p === '/.git' ||
    BLOCKED_PREFIXES.some((prefix) => p.startsWith(prefix)) ||
    // alle dot-filer/dot-mapper (f.eks. /.env, /assets/.hidden)
    p.split('/').some((seg) => seg.startsWith('.') && seg !== '');
  if (blocked) {
    return res.status(404).type('text').send('Not found');
  }
  next();
});

app.use(express.static(ROOT, {
  index: 'calendar.html',   // kalenderen er forsiden
  redirect: false,          // ingen trailing-slash-redirects bag prefix-strippende proxy
  setHeaders(res, filePath) {
    if (filePath.endsWith('.html')) {
      // HTML skal altid revalideres, så nye låger slår igennem
      res.setHeader('Cache-Control', 'no-cache');
    } else if (filePath.startsWith(path.join(ROOT, 'assets') + path.sep)) {
      // genererede video-assets må caches hårdt (versioneres pr. dag-mappe)
      res.setHeader('Cache-Control', 'public, max-age=604800');
    }
  },
}));

app.use((req, res) => {
  res.status(404).type('text').send('Not found');
});

app.listen(PORT, () => {
  console.log(`[boot] agentics juli-kalender listening on :${PORT} (data: ${VOTES_FILE}, goal: ${VOTE_GOAL})`);
});
