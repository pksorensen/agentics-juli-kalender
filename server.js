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
const DATA_DIR = path.resolve(process.env.DATA_DIR || './data');
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
// Persistens: JSON på disk, atomisk skrivning (tmp + rename), indlæses ved boot.
// ---------------------------------------------------------------------------
const votes = Object.create(null);
for (const slug of SLUGS) votes[slug] = 0;
let seenMessageIds = new Set(); // dedupe
let messageIdOrder = [];        // FIFO-orden for cap

function loadState() {
  try {
    const raw = fs.readFileSync(VOTES_FILE, 'utf8');
    const data = JSON.parse(raw);
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
    if (err.code === 'ENOENT') {
      console.log(`[boot] no existing state at ${VOTES_FILE} — starting fresh`);
    } else {
      console.error(`[boot] could not load ${VOTES_FILE}: ${err.message} — starting fresh`);
    }
  }
}

// Skrivninger serialiseres i en kæde, så tmp+rename aldrig overlapper.
let saveChain = Promise.resolve();
function saveState() {
  const snapshot = JSON.stringify({
    votes: { ...votes },
    messageIds: messageIdOrder.slice(),
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
// App
// ---------------------------------------------------------------------------
const app = express();
app.disable('x-powered-by');

// --- API ---

app.get('/api/health', (req, res) => {
  res.json({ ok: true });
});

app.get('/api/votes', (req, res) => {
  const out = {};
  for (const slug of SLUGS) out[slug] = votes[slug];
  res.json({ goal: VOTE_GOAL, total: totalVotes(), votes: out });
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

  votes[slug] += 1;
  if (messageId) rememberMessageId(messageId);
  saveState();
  console.log(`[vote] slug=${slug} votes=${votes[slug]} total=${totalVotes()} messageId=${messageId || '-'}`);
  res.json({ ok: true, slug, votes: votes[slug], total: totalVotes() });
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
