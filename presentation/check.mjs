#!/usr/bin/env node
/* presentation/check.mjs — the dev-only gate (docs/presentation/checks.md).
 *
 * Dependency-free Node 24 ESM: the globals fetch and WebSocket only, no npm
 * install, no import outside node:*. It is run by hand before a talk; the deck
 * never loads it, never needs it and is never built by it, so D-118's
 * no-build-step rule stands and presentation/index.html stays the shipped file.
 *
 * It drives the deck's public surface only: location.hash to select a slide,
 * a dispatched KeyboardEvent on document for the presenter panes, a dispatched
 * WheelEvent / MouseEvent for P8, and script.evaluate for the probes. No test
 * hook exists in index.html and none is added by this file.
 *
 * Launch form is the measured one: headless Firefox with a pre-created
 * profile, --no-remote, a remote-debugging port, then WebDriver BiDi at
 * ws://127.0.0.1:<port>/session. In this Firefox (155, headless) --width /
 * --height size the window, not the viewport: the window chrome eats 86px of
 * height and nothing of the width, so the height flag carries CHROME_Y. The
 * requested size is then VERIFIED from innerWidth / innerHeight and a mismatch
 * fails the run loudly instead of judging the wrong surface.
 */

import { spawn } from 'node:child_process';
import { mkdirSync, mkdtempSync, readFileSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve, sep } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(HERE, '..');
const SIZES = [[1280, 720], [1600, 1000]];
const CHROME_Y = 86;          /* measured: --height is the window height, the viewport is 86px shorter */
const READY_MS = 12000;       /* poll readiness, then fail loudly with the command it ran */
const DESIGN_W = 1280;
const DESIGN_H = 720;
const OUTSIDE_DESIGN_PX = 2;  /* G7: text inside the active slide, +/- 2 design px */
const CLIP_PX = 3;            /* G4: fractional line boxes and padding only */
const OVERLAP_DESIGN_PX = 4;  /* G5: both axes */
const MIN_FONT = 14;          /* G6: the design floor, measured pre-transform */
const WHEEL_DELTA = 120;
const KINDS = ['outside', 'clipped', 'overlap', 'small', 'hash', 'panel', 'leak'];

const problems = [];

const sleep = (ms) => new Promise((done) => setTimeout(done, ms));

function usage() {
  return 'usage: node presentation/check.mjs [--out <tmpdir>] [--slides 1,3] [--port 9300] [--deck <file>]';
}

/* fail() throws rather than calling process.exit(): one usage error — a
 * --slides index outside the derived total — is raised after the first launch,
 * and that path must still reach withFirefox's finally, which kills the Firefox
 * the gate spawned and removes the temp profile. main()'s catch turns the throw
 * into the same stderr message and exit status 1. */
function fail(message) {
  process.stderr.write(message + '\n');
  const error = new Error(message.split('\n')[0]);
  error.fatal = true;
  throw error;
}

function parseArgs(argv) {
  const opts = { out: null, slides: null, port: 9300, deck: join(HERE, 'index.html') };
  for (let i = 0; i < argv.length; i += 1) {
    const flag = argv[i];
    if (flag === '--out' || flag === '--slides' || flag === '--port' || flag === '--deck') {
      const value = argv[i + 1];
      if (value === undefined) { fail(flag + ' needs a value\n' + usage()); }
      i += 1;
      if (flag === '--out') { opts.out = value; }
      else if (flag === '--slides') { opts.slides = value; }
      else if (flag === '--deck') { opts.deck = resolve(value); }
      else { opts.port = Number(value); }
    } else if (flag === '--help' || flag === '-h') {
      process.stdout.write(usage() + '\n');
      process.exit(0);
    } else {
      fail('unknown argument: ' + flag + '\n' + usage());
    }
  }
  if (!Number.isInteger(opts.port) || opts.port < 1 || opts.port > 65535) {
    fail('--port must be an integer port number\n' + usage());
  }
  /* --slides is validated for SYNTAX here only: its range is the deck's own
   * slide total, which is not known until the first launch has derived it, so
   * opts.slideList stays null until then (an absent list becomes 1..total). */
  opts.slideList = null;
  if (opts.slides !== null) {
    const parts = opts.slides.split(',').map((part) => part.trim());
    for (const part of parts) {
      if (!/^\d+$/.test(part)) {
        fail('--slides takes a comma list of 1-based slide numbers; "' + part + '" in "' + opts.slides + '" is not one\n' + usage());
      }
    }
    opts.slideList = parts.map(Number);
  }
  return opts;
}

function insideRepo(path) {
  return path === REPO || path.startsWith(REPO + sep);
}

/* ---------------------------------------------------------------------------
 * The BiDi client: session.new, browsingContext.getTree, browsingContext.navigate,
 * script.evaluate, browsingContext.captureScreenshot. Nothing else.
 * ------------------------------------------------------------------------- */

class Bidi {
  constructor(socket) {
    this.socket = socket;
    this.nextId = 0;
    this.pending = new Map();
    socket.addEventListener('message', (event) => {
      let message;
      try { message = JSON.parse(event.data); } catch { return; }
      if (!message.id || !this.pending.has(message.id)) { return; }
      const entry = this.pending.get(message.id);
      this.pending.delete(message.id);
      if (message.type === 'error') {
        entry.reject(new Error(message.error + ': ' + (message.message || '')));
      } else {
        entry.resolve(message.result);
      }
    });
  }

  static connect(port, timeoutMs) {
    const url = 'ws://127.0.0.1:' + port + '/session';
    return new Promise((resolvePromise, rejectPromise) => {
      const started = Date.now();
      const attempt = () => {
        const socket = new WebSocket(url);
        socket.addEventListener('open', () => resolvePromise(new Bidi(socket)));
        socket.addEventListener('error', () => {
          try { socket.close(); } catch { /* already closing */ }
          if (Date.now() - started > timeoutMs) {
            rejectPromise(new Error('WebSocket never opened at ' + url));
          } else {
            setTimeout(attempt, 200);
          }
        });
      };
      attempt();
    });
  }

  send(method, params = {}) {
    const id = (this.nextId += 1);
    this.socket.send(JSON.stringify({ id, method, params }));
    return new Promise((resolvePromise, rejectPromise) => {
      this.pending.set(id, { resolve: resolvePromise, reject: rejectPromise });
      setTimeout(() => {
        if (!this.pending.has(id)) { return; }
        this.pending.delete(id);
        rejectPromise(new Error(method + ' timed out'));
      }, 30000);
    });
  }

  close() {
    try { this.socket.close(); } catch { /* already closed */ }
  }
}

async function pollServer(port, timeoutMs) {
  const url = 'http://127.0.0.1:' + port + '/session';
  const started = Date.now();
  for (;;) {
    try {
      const response = await fetch(url);
      await response.text();
      return true;
    } catch {
      if (Date.now() - started > timeoutMs) { return false; }
      await sleep(200);
    }
  }
}

/* Always kills the Firefox this gate spawned and removes the temp profile:
 * no orphan processes, whatever happened inside. */
async function killFirefox(proc) {
  if (!proc || proc.exitCode !== null || proc.signalCode !== null) { return; }
  try { process.kill(-proc.pid, 'SIGKILL'); } catch {
    try { proc.kill('SIGKILL'); } catch { /* already gone */ }
  }
  const started = Date.now();
  while (proc.exitCode === null && proc.signalCode === null && Date.now() - started < 5000) {
    await sleep(50);
  }
}

async function withFirefox(opts, size, body) {
  const profile = mkdtempSync(join(tmpdir(), 'deck-check-prof-'));
  mkdirSync(profile, { recursive: true });   /* Firefox refuses a profile dir that does not exist */
  const args = [
    '--headless',
    '--no-remote',
    '--profile', profile,
    '--remote-debugging-port=' + opts.port,
    '--width', String(size[0]),
    '--height', String(size[1] + CHROME_Y),
    'about:blank',
  ];
  const command = 'firefox ' + args.join(' ');
  const proc = spawn('firefox', args, { stdio: ['ignore', 'ignore', 'pipe'], detached: true });
  let lastStderr = '';
  proc.stderr.setEncoding('utf8');
  proc.stderr.on('data', (chunk) => {
    for (const line of chunk.split('\n')) {
      if (line.trim() !== '') { lastStderr = line.trim(); }
    }
  });
  proc.on('error', (error) => { lastStderr = String(error && error.message ? error.message : error); });

  let bidi = null;
  try {
    if (!(await pollServer(opts.port, READY_MS))) {
      fail('launch failed: the debug server never answered\n  ran: ' + command +
        '\n  last stderr: ' + (lastStderr || '(nothing)'));
    }
    try {
      bidi = await Bidi.connect(opts.port, READY_MS);
    } catch (error) {
      fail('launch failed: ' + error.message + '\n  ran: ' + command +
        '\n  last stderr: ' + (lastStderr || '(nothing)'));
    }
    await bidi.send('session.new', { capabilities: { alwaysMatch: {} } });
    const tree = await bidi.send('browsingContext.getTree', {});
    if (!tree.contexts || tree.contexts.length === 0) {
      fail('launch failed: no browsing context\n  ran: ' + command +
        '\n  last stderr: ' + (lastStderr || '(nothing)'));
    }
    const context = tree.contexts[0].context;
    return await body({ bidi, context, command, stderr: () => lastStderr || '(nothing)' });
  } finally {
    if (bidi) { bidi.close(); }
    await killFirefox(proc);
    rmSync(profile, { recursive: true, force: true });
  }
}

/* ---------------------------------------------------------------------------
 * Page-side probes. Each one is one script.evaluate whose value is a JSON string.
 * ------------------------------------------------------------------------- */

const PAGE_HELPERS = `
  const rectOf = (el) => { const r = el.getBoundingClientRect(); return { x: r.left, y: r.top, w: r.width, h: r.height }; };
  const pathOf = (el) => {
    let out = el.tagName.toLowerCase();
    if (el.id) { out += '#' + el.id; }
    const cls = (typeof el.className === 'string' ? el.className : '').trim();
    if (cls) { out += '.' + cls.split(/\\s+/).join('.'); }
    return out;
  };
  const ownText = (el) => Array.prototype.some.call(el.childNodes, (n) => n.nodeType === 3 && n.nodeValue.trim() !== '');
  const ariaHidden = (el) => el.closest('[aria-hidden="true"]') !== null;
  const scaleOf = () => {
    const inline = parseFloat(document.documentElement.style.getPropertyValue('--scale'));
    if (isFinite(inline) && inline > 0) { return inline; }
    const computed = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--scale'));
    return isFinite(computed) && computed > 0 ? computed : 1;
  };
  const boxOf = (el) => el ? rectOf(el) : null;
  const textRecords = (root) => {
    const out = [];
    for (const el of Array.prototype.slice.call(root.querySelectorAll('*'))) {
      if (!ownText(el)) { continue; }
      const r = rectOf(el);
      if (r.w === 0 && r.h === 0) { continue; }
      const cs = getComputedStyle(el);
      out.push({
        path: pathOf(el), aria: ariaHidden(el), rect: r, fs: parseFloat(cs.fontSize),
        ovx: cs.overflowX, ovy: cs.overflowY,
        sw: el.scrollWidth, cw: el.clientWidth, sh: el.scrollHeight, ch: el.clientHeight,
        truncate: el.getAttribute('data-truncate') === 'ok',
        text: el.textContent.trim().slice(0, 80),
      });
    }
    return out;
  };
  const slidesInfo = () => Array.prototype.map.call(document.querySelectorAll('section.slide'), (s, i) => ({
    n: i + 1, id: s.id, shape: s.getAttribute('data-shape'),
    hasTalk: Array.prototype.some.call(s.children, (c) => c.tagName === 'TEMPLATE' && c.classList.contains('talk')),
    hasMore: Array.prototype.some.call(s.children, (c) => c.tagName === 'TEMPLATE' && c.classList.contains('more')),
  }));
  const templateItems = () => {
    const out = [];
    for (const tpl of Array.prototype.slice.call(document.querySelectorAll('template.talk, template.more'))) {
      for (const li of Array.prototype.slice.call(tpl.content.querySelectorAll('li'))) {
        out.push(li.textContent.replace(/\\s+/g, ' ').trim());
      }
    }
    return out;
  };
`;

const PROBE_SCENE = '(function () {' + PAGE_HELPERS + `
  const slide = document.querySelector('section.slide[data-active]');
  const texts = textRecords(document.body);
  const cards = slide ? Array.prototype.map.call(slide.querySelectorAll('article.card'), (el) => ({ path: pathOf(el), rect: rectOf(el) })) : [];
  const overlap = [];
  const boxes = [];
  for (const el of Array.prototype.slice.call(document.querySelectorAll('*'))) {
    if (!ownText(el) || ariaHidden(el)) { continue; }
    if (!slide || !slide.contains(el)) { continue; }
    /* a text box is the box the text draws in: one box per line, from the range,
       so a line that spills out of its own fixed-height block is seen */
    const range = document.createRange();
    range.selectNodeContents(el);
    for (const r of Array.prototype.slice.call(range.getClientRects())) {
      if (r.width <= 0 || r.height <= 0) { continue; }
      boxes.push({ el, path: pathOf(el), text: el.textContent.trim().slice(0, 40), rect: { x: r.left, y: r.top, w: r.width, h: r.height } });
    }
  }
  for (let i = 0; i < boxes.length; i += 1) {
    for (let j = i + 1; j < boxes.length; j += 1) {
      const a = boxes[i];
      const b = boxes[j];
      if (a.el === b.el || a.el.contains(b.el) || b.el.contains(a.el)) { continue; }
      const ox = Math.min(a.rect.x + a.rect.w, b.rect.x + b.rect.w) - Math.max(a.rect.x, b.rect.x);
      const oy = Math.min(a.rect.y + a.rect.h, b.rect.y + b.rect.h) - Math.max(a.rect.y, b.rect.y);
      if (ox > 0 && oy > 0) { overlap.push({ a: a.path, b: b.path, at: a.text, bt: b.text, ox: ox, oy: oy }); }
    }
  }
  const slideId = slide ? slide.id : '';
  return JSON.stringify({
    scale: scaleOf(), innerW: innerWidth, innerH: innerHeight,
    stage: rectOf(document.getElementById('stage')),
    slide: slide ? { id: slide.id, shape: slide.getAttribute('data-shape'), rect: rectOf(slide) } : null,
    cards, texts, overlap,
    counter: (document.getElementById('counter') || {}).textContent || '',
    live: (document.getElementById('live') || {}).textContent || '',
    hash: location.hash,
    presenterHidden: document.getElementById('presenter').hidden,
    moreBtn: (function () { const b = document.querySelector('.more-btn'); return b ? { count: document.querySelectorAll('#hud .more-btn').length, disabled: b.getAttribute('aria-disabled'), expanded: b.getAttribute('aria-expanded'), text: b.textContent.trim() } : null; })(),
    slides: slidesInfo(),
    /* the HUD's progress dots: a count and which one is lit (1-based), so the
       gate can hold them against the derived total and the active index */
    dots: (function () {
      const all = Array.prototype.slice.call(document.querySelectorAll('#hud .dots .dot'));
      return {
        count: all.length,
        on: all.map(function (el, i) { return el.classList.contains('is-on') ? i + 1 : 0; }).filter(function (i) { return i > 0; }),
      };
    })(),
    inSlidePaths: boxes.map((b) => b.path),
    slideId,
  });
}())`;

const PROBE_PANEL = '(function () {' + PAGE_HELPERS + `
  const presenter = document.getElementById('presenter');
  const notes = document.getElementById('notes');
  const more = document.getElementById('more');
  const slide = document.querySelector('section.slide[data-active]');
  const talkTemplate = slide ? Array.prototype.filter.call(slide.children, (c) => c.tagName === 'TEMPLATE' && c.classList.contains('talk'))[0] : null;
  const bodyOf = (pane) => pane.querySelector('.panel__body');
  const itemTexts = (pane, kind) => Array.prototype.map.call(pane.querySelectorAll(kind === 'talk' ? 'li' : 'li'), (el) => el.textContent.replace(/\\s+/g, ' ').trim());
  const tplItems = talkTemplate ? Array.prototype.map.call(talkTemplate.content.querySelectorAll('li'), (el) => el.textContent.replace(/\\s+/g, ' ').trim()) : [];
  return JSON.stringify({
    scale: scaleOf(), innerW: innerWidth, innerH: innerHeight,
    stage: boxOf(document.getElementById('stage')),
    presenter: {
      hidden: presenter.hidden, rect: boxOf(presenter),
      fs: parseFloat(getComputedStyle(presenter).fontSize),
      transform: getComputedStyle(presenter).transform,
      overflow: getComputedStyle(presenter).overflow,
    },
    notes: {
      hidden: notes.hidden, rect: boxOf(notes),
      items: itemTexts(notes, 'talk'),
      templateItems: tplItems,
      bodyText: (bodyOf(notes) || { innerText: '' }).innerText.replace(/\\s+/g, ' ').trim(),
    },
    more: {
      hidden: more.hidden, rect: boxOf(more),
      refs: Array.prototype.map.call(more.querySelectorAll('.src-ref'), (el) => el.textContent.trim()),
      claims: more.querySelectorAll('.src-claim').length,
    },
    bodies: Array.prototype.slice.call(presenter.querySelectorAll('.panel__body')).map((el) => {
      const cs = getComputedStyle(el);
      return { path: pathOf(el), ovy: cs.overflowY, sh: el.scrollHeight, ch: el.clientHeight, sw: el.scrollWidth, cw: el.clientWidth };
    }),
    closers: Array.prototype.slice.call(presenter.querySelectorAll('.panel__close')).map((el) => ({ label: el.getAttribute('aria-label'), rect: rectOf(el) })),
    panelTexts: textRecords(presenter),
    where: Array.prototype.map.call(presenter.querySelectorAll('.panel__where'), (el) => el.textContent.trim()),
    liveText: (document.getElementById('live') || {}).textContent || '',
    counter: (document.getElementById('counter') || {}).textContent || '',
    hash: location.hash,
    slideId: slide ? slide.id : '',
    slideShape: slide ? slide.getAttribute('data-shape') : '',
    moreBtn: (function () { const b = document.querySelector('.more-btn'); return b ? { count: document.querySelectorAll('#hud .more-btn').length, disabled: b.getAttribute('aria-disabled'), expanded: b.getAttribute('aria-expanded') } : null; })(),
  });
}())`;

const PROBE_LEAK = '(function () {' + PAGE_HELPERS + `
  const norm = (s) => s.replace(/\\s+/g, ' ').trim();
  const bodyText = norm(document.body.innerText);
  const liveText = norm((document.getElementById('live') || {}).textContent || '');
  const found = [];
  for (const item of templateItems()) {
    if (item && (bodyText.indexOf(item) !== -1 || liveText.indexOf(item) !== -1)) {
      found.push(item.slice(0, 60));
    }
  }
  return JSON.stringify({
    leaks: found,
    presenterHidden: document.getElementById('presenter').hidden,
    innerW: innerWidth, innerH: innerHeight,
  });
}())`;

/* ---------------------------------------------------------------------------
 * Reporting
 * ------------------------------------------------------------------------- */

function report(slide, sizeTag, kind, detail) {
  if (!KINDS.includes(kind)) { throw new Error('unknown issue kind: ' + kind); }
  problems.push(String(slide || '-') + ' ' + sizeTag + ' ' + kind + ': ' + detail);
}

/* G1: static checks on the file the gate was pointed at, carried forward
 * mechanically from design.md A1/A2/A6. Kind leak: a network dependency or an
 * unsafe write reaching the presented file is an audience hazard. */
function checkStatic(deckPath) {
  const source = readFileSync(deckPath, 'utf8');
  const bytes = statSync(deckPath).size;
  const must = (label, actual, expected) => {
    if (actual !== expected) {
      report('-', 'static', 'leak', 'G1 ' + label + ': found ' + actual + ', expected ' + expected);
    }
  };
  must('inline <style> blocks', (source.match(/<style(\s|>)/g) || []).length, 1);
  must('inline <script> blocks', (source.match(/<script(\s|>)/g) || []).length, 1);
  for (const banned of ['http', 'url(', '@import', '@font-face', '<link', '<img', 'src=', 'eval', 'new Function', 'innerHTML']) {
    if (source.indexOf(banned) !== -1) {
      report('-', 'static', 'leak', 'G1 the file contains "' + banned + '" (0 allowed): ' + deckPath);
    }
  }
  if (bytes < 12288) {
    report('-', 'static', 'leak', 'G1 the file is ' + bytes + ' bytes, under the 12 kB floor');
  }
}

/* ---------------------------------------------------------------------------
 * The checks, per slide, at one size. Tolerance is stated in design px and
 * divided by --scale where a rule is about the drawing rather than the glass.
 * ------------------------------------------------------------------------- */

function checkScene(sizeTag, probe) {
  const scale = probe.scale;
  const size = sizeTag.split('x').map(Number);
  const want = Math.min(size[0] / DESIGN_W, size[1] / DESIGN_H);
  const slideLabel = probe.slide ? '#' + probe.slide.id : '-';

  if (Math.abs(scale - want) > 0.001) {
    report(slideLabel, sizeTag, 'outside', 'G2 --scale is ' + scale + ', expected ' + want);
  }
  if (!probe.slide) {
    report(slideLabel, sizeTag, 'outside', 'G2 no section.slide[data-active]');
    return;
  }
  const stage = probe.stage;
  if (stage.x < -1 || stage.y < -1 ||
      stage.x + stage.w > probe.innerW + 1 || stage.y + stage.h > probe.innerH + 1) {
    report(slideLabel, sizeTag, 'outside', 'G2 #stage ' + rectText(stage) + ' is not inside the ' + probe.innerW + 'x' + probe.innerH + ' viewport');
  }
  const slideDesignW = probe.slide.rect.w / scale;
  const slideDesignH = probe.slide.rect.h / scale;
  if (Math.abs(slideDesignW - 1192) > 1 || Math.abs(slideDesignH - 568) > 1) {
    report(slideLabel, sizeTag, 'outside', 'G2 the active slide is ' + round(slideDesignW) + 'x' + round(slideDesignH) + ' design px, expected 1192x568');
  }

  /* G7: cards inside the stage, text inside the active slide */
  for (const card of probe.cards) {
    if (card.rect.x < stage.x - 1 || card.rect.y < stage.y - 1 ||
        card.rect.x + card.rect.w > stage.x + stage.w + 1 ||
        card.rect.y + card.rect.h > stage.y + stage.h + 1) {
      report(slideLabel, sizeTag, 'outside', 'G7 ' + card.path + ' ' + rectText(card.rect) + ' is outside #stage ' + rectText(stage));
    }
  }
  const tol = OUTSIDE_DESIGN_PX * scale;
  const slideRect = probe.slide.rect;
  for (const item of probe.texts) {
    if (item.aria || probe.inSlidePaths.indexOf(item.path) === -1) { continue; }
    if (item.rect.x < slideRect.x - tol || item.rect.y < slideRect.y - tol ||
        item.rect.x + item.rect.w > slideRect.x + slideRect.w + tol ||
        item.rect.y + item.rect.h > slideRect.y + slideRect.h + tol) {
      report(slideLabel, sizeTag, 'outside', 'G7 ' + item.path + ' ' + rectText(item.rect) + ' is outside the slide ' + rectText(slideRect));
    }
  }

  /* G5: overlapping text boxes, both axes over 4 design px */
  for (const pair of probe.overlap) {
    if (pair.ox / scale > OVERLAP_DESIGN_PX && pair.oy / scale > OVERLAP_DESIGN_PX) {
      report(slideLabel, sizeTag, 'overlap',
        'G5 ' + pair.a + ' "' + pair.at + '" overlaps ' + pair.b + ' "' + pair.bt +
        '" by ' + round(pair.ox / scale) + 'x' + round(pair.oy / scale) + ' design px');
    }
  }

  /* G4: clipped text on either axis, 3px tolerance, exemptions per checks.md 3.1 */
  for (const item of probe.texts) {
    if (item.truncate) { continue; }
    if (item.ovx === 'hidden' || item.ovx === 'clip') {
      if (item.sw > item.cw + CLIP_PX) {
        report(slideLabel, sizeTag, 'clipped', 'G4 ' + item.path + ' clips ' + (item.sw - item.cw) + 'px horizontally: "' + item.text + '"');
      }
    }
    if (item.ovy === 'hidden' || item.ovy === 'clip') {
      if (item.sh > item.ch + CLIP_PX) {
        report(slideLabel, sizeTag, 'clipped', 'G4 ' + item.path + ' clips ' + (item.sh - item.ch) + 'px vertically: "' + item.text + '"');
      }
    }
  }

  /* G6: text under 14px, computed pre-transform, active slide only */
  for (const item of probe.texts) {
    if (probe.inSlidePaths.indexOf(item.path) === -1) { continue; }
    if (item.fs < MIN_FONT) {
      report(slideLabel, sizeTag, 'small', 'G6 ' + item.path + ' is ' + item.fs + 'px: "' + item.text + '"');
    }
  }
}

function rectText(rect) {
  return '[' + round(rect.x) + ',' + round(rect.y) + ' ' + round(rect.w) + 'x' + round(rect.h) + ']';
}

function round(value) {
  return Math.round(value * 100) / 100;
}

/* ---------------------------------------------------------------------------
 * The run
 * ------------------------------------------------------------------------- */

async function main() {
  const opts = parseArgs(process.argv.slice(2));

  let out = opts.out ? resolve(opts.out) : mkdtempSync(join(tmpdir(), 'deck-check-'));
  if (insideRepo(out)) {
    fail('--out must be outside the repository: ' + out + '\n' + usage());
  }
  mkdirSync(out, { recursive: true });
  if (!opts.deck.endsWith('.html') && !opts.deck.endsWith('.htm')) {
    fail('--deck must be an html file: ' + opts.deck);
  }
  process.stderr.write('check: ' + opts.deck + '\ncheck: screenshots in ' + out + '\n');

  checkStatic(opts.deck);

  const deckUrl = pathToFileURL(opts.deck).href;
  const state = { panel: {}, live: {}, total: null, slideList: null };

  for (const size of SIZES) {
    const sizeTag = size[0] + 'x' + size[1];
    await withFirefox(opts, size, async ({ bidi, context }) => {
      let runTotal = state.total;   /* null until the first launch has derived it from the deck */
      const evaluate = async (expression) => {
        const result = await bidi.send('script.evaluate', {
          expression, target: { context }, awaitPromise: true, resultOwnership: 'none',
        });
        if (result.exceptionDetails) {
          throw new Error('page exception: ' + JSON.stringify(result.exceptionDetails.exception || result.exceptionDetails));
        }
        return result.result.value;
      };
      const json = async (expression) => JSON.parse(await evaluate(expression));
      const key = (name) => `(function () { document.dispatchEvent(new KeyboardEvent('keydown', { key: ${JSON.stringify(name)}, bubbles: true, cancelable: true })); return true; }())`;
      const counterText = async () =>
        String(await evaluate(`(document.getElementById('counter') || {}).textContent || ''`)).trim();
      /* The readiness poll compares against the derived total. Before that total
       * exists — the first launch's opening probe — it accepts any `n / <count>`,
       * because the deck, not the gate, is where the count lives. */
      const counterIs = async (n) => {
        const started = Date.now();
        const anyTotal = new RegExp('^' + n + ' / \\d+$');
        for (;;) {
          const text = await counterText();
          if (runTotal === null ? anyTotal.test(text) : text === n + ' / ' + runTotal) { return true; }
          if (Date.now() - started > 3000) { return false; }
          await sleep(80);
        }
      };
      const goto = async (n) => {
        await bidi.send('browsingContext.navigate', { context, url: deckUrl + '#/' + n, wait: 'complete' });
        const reached = await counterIs(n);
        /* the deck's own 320ms enter pass: a screenshot taken inside it is the
           right layout at the wrong opacity, so let it finish */
        await sleep(360);
        return reached;
      };
      const shoot = async (name) => {
        const shot = await bidi.send('browsingContext.captureScreenshot', { context, origin: 'viewport' });
        writeFileSync(join(out, name), Buffer.from(shot.data, 'base64'));
      };

      /* window size is verified, never assumed */
      const viewport = await json('JSON.stringify({ w: innerWidth, h: innerHeight })');
      if (Math.abs(viewport.w - size[0]) > 1 || Math.abs(viewport.h - size[1]) > 1) {
        fail('window size did not take: requested ' + sizeTag + ', innerWidth/innerHeight are ' +
          viewport.w + 'x' + viewport.h + '\n  ran: firefox --headless --no-remote --profile <tmp> ' +
          '--remote-debugging-port=' + opts.port + ' --width ' + size[0] + ' --height ' + (size[1] + CHROME_Y) +
          ' about:blank\n  (headless window chrome on this build: ' + CHROME_Y + 'px of height, 0px of width)');
      }

      /* The slide map, read once from the deck itself. The total has exactly one
       * home — section.slide in the deck — so it is derived here, printed on
       * stdout the moment the first launch knows it (ahead of any issue line,
       * once per run), and every comparison below uses it. */
      await goto(1);
      let scene = await json(PROBE_SCENE);
      const map = scene.slides;
      const derived = map.length;
      let trusted = true;
      if (state.total === null) {
        state.total = derived;
        process.stdout.write('slides: ' + derived + ' (derived from section.slide)\n');
        /* --slides is resolved AFTER the derivation: parseArgs checked syntax
         * only, because the range is the deck's own total. */
        if (opts.slideList === null) {
          state.slideList = map.map((entry) => entry.n);
        } else {
          for (const n of opts.slideList) {
            if (n < 1 || n > derived) {
              fail('--slides ' + opts.slides + ': ' + n + ' is outside the derived range 1..' + derived +
                ' (the deck has ' + derived + ' section.slide)\n' + usage());
            }
          }
          state.slideList = opts.slideList;
        }
      } else if (derived !== state.total) {
        /* the two launches must agree on the total; if the deck changed
           mid-run, this run's counter and #live strings mean nothing */
        trusted = false;
        report('#s1', sizeTag, 'hash', 'G3 the deck derived ' + derived + ' slides here but ' + state.total +
          ' in the first launch: it changed mid-run, so this run\u2019s #counter, #live and hash strings are not trusted');
      }
      runTotal = derived;
      const withNotes = map.filter((s) => s.hasTalk);
      const withSources = map.filter((s) => s.hasMore);
      state.live[sizeTag] = map;

      /* G3: the deck's own map — slide n is id="s<n>" and carries one data-shape
       * word that no other slide carries (a copied section keeps the old word,
       * and #live then names a shape the slide is not). */
      const shapes = new Map();
      for (const entry of map) {
        if (entry.id !== 's' + entry.n) {
          report('#s' + entry.n, sizeTag, 'hash', 'G3 slide ' + entry.n + ' carries id="' + entry.id + '", expected "s' + entry.n + '"');
        }
        const word = (entry.shape || '').trim();
        if (word === '') {
          report('#s' + entry.n, sizeTag, 'hash', 'G3 #s' + entry.n + ' has no data-shape, so #live announces no shape');
        } else if (shapes.has(word)) {
          report('#s' + entry.n, sizeTag, 'hash', 'G3 #s' + entry.n + ' repeats data-shape "' + word + '" from #s' + shapes.get(word));
        } else {
          shapes.set(word, entry.n);
        }
      }
      /* G3 (b): the HUD holds one dot per derived slide. Reported once per launch
       * on the first probe, because the dots are static markup: one fact about
       * the HUD, not one per slide. Kind hash, with the counter and #live below;
       * no other kind in the closed set names a HUD indicator. */
      if (scene.dots.count !== runTotal) {
        report('#s1', sizeTag, 'hash', 'G3 the HUD holds ' + scene.dots.count + ' .dot elements, expected ' + runTotal);
      }

      /* G10: with no pane open, no template string is in body.innerText or #live */
      const leak = await json(PROBE_LEAK);
      if (!leak.presenterHidden) {
        report('#s' + map[0].n, sizeTag, 'leak', 'G10 #presenter is open before any keypress');
      }
      for (const item of leak.leaks) {
        report('#s' + map[0].n, sizeTag, 'leak', 'G10 template text reached the audience: "' + item + '"');
      }

      /* G9: exactly one More control in the HUD */
      if (!scene.moreBtn) {
        report('#s1', sizeTag, 'panel', 'G9 there is no .more-btn in the HUD');
      } else if (scene.moreBtn.count !== 1) {
        report('#s1', sizeTag, 'panel', 'G9 the HUD holds ' + scene.moreBtn.count + ' .more-btn controls, expected 1');
      }

      /* G3 + G2 + G4 + G5 + G6 + G7 + G9, slide by slide */
      for (const n of state.slideList) {
        const entry = map[n - 1];
        if (!entry) {
          report('#s' + n, sizeTag, 'hash', 'G3 the deck has no slide ' + n + ' (derived ' + runTotal + ')');
          continue;
        }
        if (!(await goto(n)) && trusted) {
          report('#s' + n, sizeTag, 'hash', 'G3 #/' + n + ' did not put "' + n + ' / ' + runTotal + '" in #counter');
        }
        scene = await json(PROBE_SCENE);
        const slideLabel = scene.slide ? '#' + scene.slide.id : '#s' + n;
        if (trusted && scene.counter.trim() !== n + ' / ' + runTotal) {
          report(slideLabel, sizeTag, 'hash', 'G3 #/' + n + ' put "' + scene.counter.trim() + '" in #counter');
        }
        const wantLive = 'Slide ' + n + ' of ' + runTotal + ' \u2014 ' + entry.shape;
        if (trusted && scene.live.trim() !== wantLive) {
          report(slideLabel, sizeTag, 'hash', 'G3 #live reads "' + scene.live.trim() + '", expected "' + wantLive + '"');
        }
        if (!scene.slide || scene.slide.id !== entry.id) {
          report(slideLabel, sizeTag, 'hash', 'G3 #/' + n + ' activated ' + (scene.slide ? '#' + scene.slide.id : 'nothing'));
        }
        /* G3 (b): exactly one dot is lit, and it is this slide's. Kind hash: the
         * dots are navigation state, checked here with the counter and #live,
         * and no other kind in the closed set names a HUD indicator. */
        if (scene.dots.on.length !== 1 || scene.dots.on[0] !== n) {
          report(slideLabel, sizeTag, 'hash', 'G3 the HUD has ' +
            (scene.dots.on.length === 0 ? 'no .dot .is-on' : '.dot ' + scene.dots.on.join(', ') + ' .is-on') +
            ', expected exactly .dot ' + n);
        }
        checkScene(sizeTag, scene);
        await shoot('s' + n + '-' + sizeTag + '.png');

        /* G9: the More control on this slide, and what M does */
        const hasSources = entry.hasMore;
        if (hasSources) {
          if (scene.moreBtn && scene.moreBtn.disabled !== 'false') {
            report(slideLabel, sizeTag, 'panel', 'G9 .more-btn reports aria-disabled="' + (scene.moreBtn ? scene.moreBtn.disabled : 'missing') + '" on a slide with sources');
          }
          await evaluate(key('m'));
          await sleep(80);
          const opened = await json(PROBE_PANEL);
          if (opened.more.hidden || opened.presenter.hidden) {
            report(slideLabel, sizeTag, 'panel', 'G9 M did not open #more on a slide with a template.more');
          }
          if (opened.more.claims !== opened.more.refs.length) {
            report(slideLabel, sizeTag, 'panel', 'G9 ' + opened.more.claims + ' .src-claim against ' + opened.more.refs.length + ' .src-ref');
          }
          for (const ref of opened.more.refs) {
            if (!/(D-\d+)|(strata\/records\/)/.test(ref) || !/\d{4}-\d{2}-\d{2}/.test(ref)) {
              report(slideLabel, sizeTag, 'panel', 'G9 a source entry is not a D-row or strata/records path with an ISO date: "' + ref + '"');
            }
          }
          if (opened.moreBtn && opened.moreBtn.expanded !== 'true') {
            report(slideLabel, sizeTag, 'panel', 'G9 .more-btn aria-expanded is "' + opened.moreBtn.expanded + '" with #more open');
          }
          await evaluate(key('Escape'));
          await sleep(60);
          const closed = await json(PROBE_PANEL);
          if (!closed.more.hidden || !closed.presenter.hidden) {
            report(slideLabel, sizeTag, 'panel', 'G9 Esc did not close #more');
          }
        } else {
          if (scene.moreBtn && scene.moreBtn.disabled !== 'true') {
            report(slideLabel, sizeTag, 'panel', 'G9 .more-btn reports aria-disabled="' + (scene.moreBtn ? scene.moreBtn.disabled : 'missing') + '" on a slide without template.more');
          }
          await evaluate(key('m'));
          await sleep(80);
          const after = await json(PROBE_PANEL);
          if (!after.more.hidden || !after.presenter.hidden) {
            report(slideLabel, sizeTag, 'panel', 'G9 M opened a pane on a slide with no template.more');
          }
        }
      }

      /* G3: the clamped forms are computed from the derived total, never typed:
       * #/0 -> 1, #/<total+1> -> total, #/abc -> 1. */
      const clamped = [[0, 1], [runTotal + 1, runTotal], ['abc', 1]];
      for (const [typed, want] of clamped) {
        await bidi.send('browsingContext.navigate', { context, url: deckUrl + '#/' + typed, wait: 'complete' });
        if (!(await counterIs(want)) && trusted) {
          report('#s' + want, sizeTag, 'hash', 'G3 #/' + typed + ' left "' + (await counterText()) +
            '" in #counter, expected "' + want + ' / ' + runTotal + '"');
        }
      }
      /* The documented follow-on (design §6, A3): the address bar is rewritten
       * only by a move that CHANGES slides, so the press made after a clamped
       * load is the one that moves. A press at the clamped end rewrites nothing
       * and that is correct behaviour, not a defect: nothing is asserted for it. */
      if (runTotal > 1) {
        const prev = runTotal - 1;
        await bidi.send('browsingContext.navigate', { context, url: deckUrl + '#/' + (runTotal + 1), wait: 'complete' });
        await counterIs(runTotal);
        await evaluate(key('ArrowLeft'));
        await sleep(120);
        const rewritten = await json('JSON.stringify({ hash: location.hash, counter: (document.getElementById(\'counter\') || {}).textContent || \'\' })');
        if (trusted && rewritten.hash !== '#/' + prev) {
          report('#s' + prev, sizeTag, 'hash', 'G3 after a clamped load the first navigation left the hash at "' +
            rewritten.hash + '", expected "#/' + prev + '"');
        }
      }

      /* G8: the presenter drawer, on a slide that has notes */
      if (withNotes.length === 0) {
        report('#s1', sizeTag, 'panel', 'G8 no slide carries a template.talk, so the notes pane cannot be checked');
      } else {
        const notesSlide = withNotes[0].n;
        await goto(notesSlide);
        const before = await json(PROBE_PANEL);
        if (!before.presenter.hidden) {
          report('#s' + notesSlide, sizeTag, 'panel', 'G8 #presenter is open before N');
        }
        await evaluate(key('n'));
        await sleep(260);
        const open = await json(PROBE_PANEL);
        if (open.presenter.hidden || open.notes.hidden) {
          report('#s' + notesSlide, sizeTag, 'panel', 'G8 N did not open #notes and #presenter');
        }
        if (open.notes.items.length === 0) {
          report('#s' + notesSlide, sizeTag, 'panel', 'G8 #notes is empty on a slide with a template.talk');
        }
        const wantItems = open.notes.templateItems.join(' | ');
        if (open.notes.items.join(' | ') !== wantItems) {
          report('#s' + notesSlide, sizeTag, 'panel', 'G8 the notes pane does not show the slide\u2019s own lines');
        }
        const wantWhere = 'Slide ' + notesSlide + ' of ' + runTotal + ' \u2014 ' + open.slideShape;
        for (const where of open.where) {
          if (where !== wantWhere) {
            report('#s' + notesSlide, sizeTag, 'panel', 'G8 .panel__where reads "' + where + '", expected "' + wantWhere + '"');
          }
        }
        if (!open.presenter.rect || open.presenter.rect.w < 1 || open.presenter.rect.h < 1) {
          report('#s' + notesSlide, sizeTag, 'panel', 'G8 #presenter has no box');
        } else if (open.presenter.rect.x < 0 || open.presenter.rect.y < 0 ||
            open.presenter.rect.x + open.presenter.rect.w > open.innerW + 1 ||
            open.presenter.rect.y + open.presenter.rect.h > open.innerH + 1) {
          report('#s' + notesSlide, sizeTag, 'panel', 'G8 #presenter ' + rectText(open.presenter.rect) + ' is not inside the ' + open.innerW + 'x' + open.innerH + ' viewport');
        }
        if (open.notes.rect && (open.notes.rect.x < 0 || open.notes.rect.y < 0 ||
            open.notes.rect.x + open.notes.rect.w > open.innerW + 1 ||
            open.notes.rect.y + open.notes.rect.h > open.innerH + 1)) {
          report('#s' + notesSlide, sizeTag, 'panel', 'G8 #notes ' + rectText(open.notes.rect) + ' is not inside the viewport');
        }
        if (open.presenter.transform !== 'none') {
          report('#s' + notesSlide, sizeTag, 'panel', 'G8 #presenter has computed transform "' + open.presenter.transform + '" (it must not be scaled)');
        }
        for (const item of open.panelTexts) {
          if (item.fs < MIN_FONT) {
            report('#s' + notesSlide, sizeTag, 'small', 'G8 ' + item.path + ' is ' + item.fs + 'px inside the drawer: "' + item.text + '"');
          }
          if (!item.truncate && (item.ovx === 'hidden' || item.ovx === 'clip') && item.sw > item.cw + CLIP_PX) {
            report('#s' + notesSlide, sizeTag, 'clipped', 'G4 ' + item.path + ' clips ' + (item.sw - item.cw) + 'px horizontally in the drawer: "' + item.text + '"');
          }
          if (!item.truncate && (item.ovy === 'hidden' || item.ovy === 'clip') && item.sh > item.ch + CLIP_PX) {
            report('#s' + notesSlide, sizeTag, 'clipped', 'G4 ' + item.path + ' clips ' + (item.sh - item.ch) + 'px vertically in the drawer: "' + item.text + '"');
          }
        }
        for (const body of open.bodies) {
          if ((body.sh > body.ch || body.sw > body.cw) && body.ovy !== 'auto' && body.ovy !== 'scroll') {
            report('#s' + notesSlide, sizeTag, 'clipped',
              'G8 ' + body.path + ' overflows but is not the declared scroller (overflow-y: ' + body.ovy + ')');
          }
        }
        for (const closer of open.closers) {
          if (closer.rect.w === 0 && closer.rect.h === 0) { continue; }   /* that pane is closed */
          if (closer.rect.w < 32 || closer.rect.h < 32) {
            report('#s' + notesSlide, sizeTag, 'panel', 'G8 the close control ' + (closer.label || '') + ' is ' + round(closer.rect.w) + 'x' + round(closer.rect.h) + ' window px, under 32x32');
          }
        }
        /* the drawer is specified in window px, not stage px (presenter.md 2):
           its width is min(460px, 34vw) and follows the window, never --scale */
        const wantWidth = Math.min(460, open.innerW * 0.34);
        if (!open.presenter.rect || Math.abs(open.presenter.rect.w - wantWidth) > 2) {
          report('#s' + notesSlide, sizeTag, 'panel', 'G8 #presenter is ' +
            round(open.presenter.rect ? open.presenter.rect.w : 0) + 'px wide, expected min(460px, 34vw) = ' + round(wantWidth) + 'px');
        }
        /* the drawer must not move the stage (P3, P9) */
        if (Math.abs(open.stage.x - before.stage.x) > 1 || Math.abs(open.stage.y - before.stage.y) > 1 ||
            Math.abs(open.stage.w - before.stage.w) > 1 || Math.abs(open.stage.h - before.stage.h) > 1) {
          report('#s' + notesSlide, sizeTag, 'panel', 'G8 opening the drawer moved #stage from ' + rectText(before.stage) + ' to ' + rectText(open.stage));
        }
        if (Math.abs(open.scale - before.scale) > 0.001) {
          report('#s' + notesSlide, sizeTag, 'panel', 'G8 opening the drawer changed --scale from ' + before.scale + ' to ' + open.scale);
        }
        if (open.liveText !== before.liveText) {
          report('#s' + notesSlide, sizeTag, 'leak', 'G10 opening #notes changed #live to "' + open.liveText + '"');
        }
        for (const leakItem of await json(PROBE_LEAK).then((r) => r.leaks)) {
          if (open.liveText.indexOf(leakItem) !== -1) {
            report('#s' + notesSlide, sizeTag, 'leak', 'G10 #live carries template text with #notes open: "' + leakItem + '"');
          }
        }
        await shoot('s' + notesSlide + '-' + sizeTag + '-notes.png');
        state.panel[sizeTag] = {
          fs: open.presenter.fs, width: open.presenter.rect ? open.presenter.rect.w : 0, slide: notesSlide,
        };
        /* wheel and click go quiet while the drawer is open, and step after it closes (P8) */
        const hashBefore = open.hash;
        await evaluate(`(function () { window.dispatchEvent(new WheelEvent('wheel', { deltaY: ${WHEEL_DELTA}, bubbles: true })); return true; }())`);
        await evaluate(`(function () { window.dispatchEvent(new MouseEvent('click', { clientX: Math.round(innerWidth * 0.9), clientY: Math.round(innerHeight * 0.5), button: 0, bubbles: true })); return true; }())`);
        await sleep(240);
        const quiet = await json(PROBE_PANEL);
        if (quiet.counter.trim() !== open.counter.trim() || quiet.hash !== hashBefore) {
          report('#s' + notesSlide, sizeTag, 'panel',
            'G8 wheel and click navigated while the drawer was open: counter "' + quiet.counter.trim() + '", hash "' + quiet.hash + '"');
        }
        await evaluate(key('Escape'));
        await sleep(420);
        const afterEsc = await json(PROBE_PANEL);
        if (!afterEsc.notes.hidden || !afterEsc.presenter.hidden) {
          report('#s' + notesSlide, sizeTag, 'panel', 'G8 Esc did not close the notes pane');
        }
        if (afterEsc.hash !== hashBefore || afterEsc.slideId !== open.slideId) {
          report('#s' + notesSlide, sizeTag, 'panel',
            'G8 Esc navigated: ' + open.slideId + '@' + hashBefore + ' became ' + afterEsc.slideId + '@' + afterEsc.hash);
        }
        await evaluate(`(function () { window.dispatchEvent(new WheelEvent('wheel', { deltaY: ${WHEEL_DELTA}, bubbles: true })); return true; }())`);
        await sleep(240);
        const afterWheel = await json(PROBE_PANEL);
        if (afterWheel.slideId === afterEsc.slideId) {
          report('#s' + notesSlide, sizeTag, 'panel', 'G8 the wheel no longer navigates after the drawer closed');
        }
        await evaluate(`(function () { window.dispatchEvent(new MouseEvent('click', { clientX: Math.round(innerWidth * 0.9), clientY: Math.round(innerHeight * 0.5), button: 0, bubbles: true })); return true; }())`);
        await sleep(160);
        const afterClick = await json(PROBE_PANEL);
        if (afterClick.slideId === afterWheel.slideId) {
          report('#s' + notesSlide, sizeTag, 'panel', 'G8 the click zone no longer navigates after the drawer closed');
        }

        /* P4: a slide with no template.talk says so, so "no notes" is never a silent keypress */
        const emptyOne = map.filter((entry) => !entry.hasTalk)[0];
        if (emptyOne) {
          await goto(emptyOne.n);
          await evaluate(key('n'));
          await sleep(220);
          const empty = await json(PROBE_PANEL);
          if (empty.notes.hidden || empty.presenter.hidden) {
            report('#s' + emptyOne.n, sizeTag, 'panel', 'G8 N did not open #notes on a slide with no template.talk');
          } else if (empty.notes.bodyText === '') {
            report('#s' + emptyOne.n, sizeTag, 'panel', 'G8 the notes pane is empty on a slide with no template.talk');
          }
          for (const item of empty.panelTexts) {
            if (item.fs < MIN_FONT) {
              report('#s' + emptyOne.n, sizeTag, 'small', 'G8 ' + item.path + ' is ' + item.fs + 'px inside the drawer: "' + item.text + '"');
            }
          }
          await evaluate(key('n'));
          await sleep(80);
        }
      }
    });
  }

  /* G8: the drawer's type is independent of the window size. Its width is
   * min(460px, 34vw) by presenter.md 2, so it follows the window and never
   * --scale: the width test above pins each size to that formula. */
  const tags = Object.keys(state.panel);
  if (tags.length === 2) {
    const a = state.panel[tags[0]];
    const b = state.panel[tags[1]];
    if (Math.abs(a.fs - b.fs) > 0.01) {
      report('#s' + a.slide, tags[0], 'panel', 'G8 #presenter font-size is ' + a.fs + 'px at ' + tags[0] + ' and ' + b.fs + 'px at ' + tags[1] + ': it is being scaled');
    }
  }

  if (problems.length > 0) {
    process.stdout.write(problems.join('\n') + '\n');
    process.exitCode = 1;
  } else {
    process.stdout.write('no issues\n');
    process.exitCode = 0;
  }
}

main().catch((error) => {
  if (error && error.fatal === true) {
    /* fail() has already written its message; throwing let withFirefox's
       finally kill Firefox and remove the profile on the way out */
    process.exit(1);
  }
  process.stderr.write('check failed: ' + (error && error.stack ? error.stack : String(error)) + '\n');
  process.exit(1);
});
