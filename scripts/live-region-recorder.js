/*
 * Live Region Recorder
 *
 * Runs IN THE BROWSER PAGE, not in Node. Records everything a screen reader
 * could announce from a live region, and where keyboard focus goes, with
 * milliseconds since the page started loading. Use it in automated tests and
 * probes before (never instead of) a screen reader check. See
 * docs/SCREEN_READER_STANDARD.md, part T.
 *
 * Entry kinds:
 *   write   text written into a live region. same: true when the new text
 *           equals the old: a rewrite with identical text is still a DOM
 *           change, and NVDA has announced such rewrites. shown: false when
 *           the region is hidden; wasHidden: true with shown: true when the
 *           text arrived together with the region's reveal, which screen
 *           readers often treat as an insertion and do not announce.
 *   attr    an attribute of a live region changed (title, aria-label, role,
 *           style, ...). NVDA 2026.2 announced a title added, changed or
 *           removed on a role="status" element.
 *   insert  a live region was added to the page with its text already inside.
 *           Insertions are usually NOT announced: a region must exist (and be
 *           shown) before its text is written.
 *   focus   keyboard focus moved to an element.
 *   lost    focus fell back to <body>, for example because the focused button
 *           was disabled or removed.
 *
 * Load it before the page's own scripts, so start-up writes are caught:
 *   Playwright: await context.addInitScript({ path: 'scripts/live-region-recorder.js' });
 *   DevTools:   paste the file into the console (records from that moment on).
 *
 * Read it:
 *   window.__srRecorder.entries()   every entry so far
 *   window.__srRecorder.since()     entries since the last since() or mark(), then marks
 *   window.__srRecorder.mark()      start a new window
 *   window.__srRecorder.lines(list) entries as readable text lines
 *
 * Limits: it sees the DOM, not the accessibility tree and not speech. It cannot
 * tell whether a screen reader spoke an entry, only that it could have.
 *
 * License: MIT
 */
(() => {
  if (window.__srRecorder) return;

  const LIVE_ROLES = new Set(['status', 'alert', 'log', 'marquee', 'timer']);
  const WATCHED = ['title', 'aria-label', 'aria-labelledby', 'aria-describedby',
    'aria-description', 'role', 'aria-live', 'aria-atomic', 'aria-relevant',
    'aria-busy', 'aria-hidden', 'hidden', 'class', 'style'];

  const entries = [];
  let markAt = 0;
  const lastText = new WeakMap();
  const lastShown = new WeakMap();

  const now = () => Math.round(performance.now());
  const squash = (s) => String(s == null ? '' : s).replace(/\s+/g, ' ').trim();
  const isRegion = (el) => !!el && el.nodeType === 1 && (
    LIVE_ROLES.has(el.getAttribute('role')) ||
    (el.hasAttribute('aria-live') && el.getAttribute('aria-live') !== 'off'));
  const regionOf = (node) => {
    let el = node && (node.nodeType === 1 ? node : node.parentElement);
    while (el) {
      if (isRegion(el)) return el;
      el = el.parentElement;
    }
    return null;
  };
  const describe = (el) => {
    if (!el || el.nodeType !== 1) return String(el);
    if (el === document.body) return 'body';
    if (el.id) return '#' + el.id;
    const cls = typeof el.className === 'string' && el.className.trim()
      ? '.' + el.className.trim().split(/\s+/)[0] : '';
    return el.tagName.toLowerCase() + cls;
  };
  const shown = (el) => {
    try {
      const cs = getComputedStyle(el);
      return cs.display !== 'none' && cs.visibility !== 'hidden';
    } catch (e) {
      return null;
    }
  };
  const push = (entry) => entries.push(Object.assign({ t: now() }, entry));
  const parsing = () => document.readyState === 'loading';
  const regionsIn = (node) => {
    const found = isRegion(node) ? [node] : [];
    if (node.querySelectorAll) {
      node.querySelectorAll('[role],[aria-live]').forEach((el) => {
        if (isRegion(el)) found.push(el);
      });
    }
    return found;
  };
  const scan = () => {
    document.querySelectorAll('[role],[aria-live]').forEach((el) => {
      if (isRegion(el)) {
        lastText.set(el, squash(el.textContent));
        lastShown.set(el, shown(el));
      }
    });
  };

  // The observer runs once per batch of changes (at the end of the task that
  // made them), so text and visibility are read then. Entries keep the order
  // of the first change to each region; wasHidden says the region was hidden
  // at the end of the previous batch, so "wasHidden and now shown" is a write
  // that arrived together with its reveal, which screen readers often skip.
  new MutationObserver((mutations) => {
    const pending = new Map();
    const touched = new Set();
    for (const m of mutations) {
      if (m.type === 'attributes') {
        if (isRegion(m.target)) {
          touched.add(m.target);
          push({ kind: 'attr', target: describe(m.target), name: m.attributeName,
            old: m.oldValue, value: m.target.getAttribute(m.attributeName),
            shown: shown(m.target) });
        }
        continue;
      }
      if (m.type === 'childList') {
        for (const n of m.addedNodes) {
          if (n.nodeType !== 1) continue;
          for (const r of regionsIn(n)) {
            const text = squash(r.textContent);
            lastText.set(r, text);
            lastShown.set(r, shown(r));
            if (!parsing() && text) {
              push({ kind: 'insert', target: describe(r), text, shown: shown(r) });
            }
          }
        }
        // The parser adding a region's first text is not a write. A script
        // replacing text removes the old node, so that still counts.
        if (parsing() && m.removedNodes.length === 0) continue;
      }
      const region = regionOf(m.target);
      if (region && !pending.has(region)) {
        const entry = { t: now(), kind: 'write', target: describe(region) };
        pending.set(region, entry);
        entries.push(entry);
      }
    }
    for (const [region, entry] of pending) {
      const text = squash(region.textContent);
      entry.text = text;
      entry.same = lastText.get(region) === text;
      entry.shown = shown(region);
      entry.wasHidden = lastShown.get(region) === false;
      lastText.set(region, text);
      touched.add(region);
    }
    for (const region of touched) lastShown.set(region, shown(region));
  }).observe(document, { subtree: true, childList: true, characterData: true,
    attributes: true, attributeOldValue: true, attributeFilter: WATCHED });

  if (parsing()) {
    document.addEventListener('DOMContentLoaded', scan, { once: true });
  } else {
    scan();
  }

  let lastFocus = null;
  document.addEventListener('focusin', (e) => {
    lastFocus = e.target;
    push({ kind: 'focus', target: describe(e.target) });
  }, true);
  setInterval(() => {
    const active = document.activeElement;
    if ((!active || active === document.body) && lastFocus && lastFocus !== document.body) {
      push({ kind: 'lost', target: 'body', from: describe(lastFocus) });
      lastFocus = document.body;
    }
  }, 50);

  const fmt = (e) => {
    const t = String(e.t).padStart(7) + ' ms  ' + e.kind.padEnd(6) + ' ' + e.target;
    if (e.kind === 'write') {
      const seen = e.shown === false ? '  (hidden)'
        : (e.wasHidden ? '  (revealed with its text: likely silent)' : '');
      return t + (e.same ? '  (same text)' : '') + seen + '  "' + e.text + '"';
    }
    if (e.kind === 'insert') return t + (e.shown === false ? '  (hidden)' : '') + '  "' + e.text + '"';
    if (e.kind === 'attr') return t + '  ' + e.name + ': ' + JSON.stringify(e.old) + ' -> ' + JSON.stringify(e.value);
    if (e.kind === 'lost') return t + '  (from ' + e.from + ')';
    return t;
  };

  window.__srRecorder = {
    entries: () => entries.slice(),
    mark: () => { markAt = entries.length; },
    since: () => {
      const out = entries.slice(markAt);
      markAt = entries.length;
      return out;
    },
    lines: (list) => (list || entries).map(fmt),
  };
})();
