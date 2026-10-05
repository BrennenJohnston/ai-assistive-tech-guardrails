# Screen Reader Standard (NVDA first)

This is the standard for building and checking anything a screen reader user will
hear: page structure, names, descriptions, status messages and keyboard focus. It
runs from design through code, tests and the screen reader check, to the files you
hand over. It is written so an AI agent can follow it step by step without a human
explaining it, and it says exactly where a human must decide.

It grew out of the first time an AI agent could drive NVDA and read NVDA's own
speech log, instead of guessing from the markup. That run found bugs every
automated tool had passed. The story and the numbers are in
[NVDA_WALKTHROUGH_LESSONS.md](NVDA_WALKTHROUGH_LESSONS.md).

**Measured with:** NVDA 2026.2 and Chrome 150 on Windows 11 (October 2026), and
NVDA 2026.1 in August 2026. Other screen readers (JAWS, VoiceOver, TalkBack,
Narrator) were not measured. The design rules in parts A and P are good practice
for all of them; the behaviours in part K are NVDA + Chrome facts, so re-measure
them when either is updated.

**Tools that come with it:**

- [scripts/nvda-walk.py](../scripts/nvda-walk.py): sends real keys to the browser and
  reads back what NVDA said (Windows, Python standard library only)
- [scripts/live-region-recorder.js](../scripts/live-region-recorder.js): records live
  region writes, attribute changes and lost focus in the browser (for tests)
- [checklists/screen-reader-check.md](../checklists/screen-reader-check.md): the
  short version of this standard, for PRs
- [templates/nvda-walkthrough.md](../templates/nvda-walkthrough.md): the walkthrough
  and results template
- [prompts/17-screen-reader-work.md](../prompts/17-screen-reader-work.md): the prompt
  to start an AI session on screen reader work

---

## How to use this standard

### Which parts apply to your task

| Task | Read and apply | Hand over |
| --- | --- | --- |
| New or changed UI that a screen reader reaches | A, P, T, N, D | D1 |
| A bug reported by a screen reader user or a walkthrough | H, then T (failing test first), the fix, N (re-check) | D3 |
| Writing or updating a walkthrough | W, N | D2 |
| Running a walkthrough | N, K | D2 |
| A release | N (every walkthrough), E | D2 for each walkthrough |

Read the ground rules below once per session. They decide what counts as proof.

### Evidence words

Label every claim you write in a record, a PR or a report:

| Label | Meaning |
| --- | --- |
| MEASURED | You ran it and read the result yourself (a log, a test output, a file) |
| REPORTED | Someone else said it (a user, a document, an earlier session) |
| INFERRED | You reasoned it from code or documents without running anything |
| PREDICTED | You expect a screen reader to say it, from the markup or the accessibility tree, but nobody has heard it yet |

Never write PREDICTED speech as if it were heard. In August 2026 an agent predicted
from the accessibility tree that NVDA would say a button's name twice. NVDA said it
once.

### Stop and ask a human when

1. Wording that users hear needs to change: labels, descriptions, status messages,
   error messages. Draft it, mark it DRAFT, and ask. Never ship it unsigned.
2. A fix would delete visible text, remove an ARIA attribute, or change how much
   is spoken on purpose (for example a long description).
3. The screen reader check cannot be run (no Windows, no NVDA, or no permission to
   send keys). Report the check as NOT RUN and hand over the walkthrough.
4. Something is a matter of taste: too long, tiring, confusing, a symbol read aloud.
   Record it as an observation with the evidence, and let the person decide.
5. Two attempts at the same fix have failed.
6. Another program is in front when keys are due, or anything asks for a password.

---

## Ground rules

**G1. Only listening proves an announcement is useful.** The markup proves
nothing. The accessibility tree proves a control *can* be announced. The screen
reader's own log proves what was said, when, and how many times.

**G2. Automated checks are needed, and they are not enough.** Lighthouse and
axe-core scored 100 while status messages were silent and while warning boxes
failed contrast. Later, every automated check passed while the page said "Normal,
Normal" on every load. Run them, then keep going.

**G3. A passing test is not the verdict on a screen reader bug. The re-check with
the screen reader is.** A fix passed its new test and NVDA still spoke the bug,
because NVDA reacted to an attribute the test did not watch.

**G4. One user action gives one clear announcement, in a useful order. No action
gives silence.** Loading the page is not an action.

**G5. Evidence is the screen reader's own log, saved step by step,** with the
versions of everything involved. Memory and summaries are not evidence.

**G6. The person at the keyboard judges what is pleasant.** The agent measures and
reports. Long, tiring or odd is a human call.

**G7. When a walkthrough and the screen reader disagree, find out which one is
wrong.** If the page is wrong, fix the page. If the walkthrough describes the
screen reader wrongly, fix the walkthrough to what was heard.

---

## Part A: Design rules (before you write code)

### A1. Page structure

- Landmarks: one `header` (banner), one `main`, `nav` and `footer` where they exist.
  Page chrome (theme switch, font size, help, links out) sits outside `main`.
- One `h1`. Section headings are `h2`, the sections inside them `h3`. Never skip a
  level in any state of the page (count again with every panel open).
- A disclosure or accordion button sits inside a heading:
  `<h3><button aria-expanded="false" aria-controls="panel-1">Spacing</button></h3>`.
- Group related controls with `<fieldset>` and `<legend>`. A heading inside a
  legend is valid HTML and gives heading navigation. NVDA then says the name twice
  ("Card sides, grouping, Card sides, heading, level 3"). Decide whether that is
  acceptable for your page; do not swap the fieldset for a `div` to avoid it,
  because the fieldset is what names the radio group.

### A2. Skip links

- Point a skip link at an element that can never be hidden, and give the target
  `tabindex="-1"`. A link to an element that is not focusable does not move focus,
  and a link to a hidden element moves nothing.
- Prefer a heading at the start of the task over a large container. When focus
  lands on a container, NVDA reads all of it: a skip link to `main` made NVDA read
  several hundred words in one go. A skip link to an `h2` read one line.
- With NVDA, the first Tab after a page load goes to the second focusable item
  (see K1). Users reach the first skip link with Shift+Tab or browse mode. Do not
  build a flow that only works if the first Tab lands on the first link.

### A3. Accessible names

- Every control has a name, and the name contains the visible label (WCAG 2.5.3).
- If a group's heading text changes at runtime, name the group with
  `aria-labelledby` pointing at that heading. A fieldset named only by its legend
  kept its old name in NVDA after the heading changed (K9).
- Symbols in a name are spoken as words at NVDA's default symbol level: "↓" is
  "down arrow", "→" is "right arrow". Decide on purpose whether a symbol belongs
  in the name. A decorative glyph goes in `<span aria-hidden="true">`.
- Do not copy an `aria-label` into `title`. NVDA hides a description that equals
  the name, but other screen readers may read it twice.

### A4. Descriptions

- An `aria-describedby` description is one short sentence: target 15 words, hard
  ceiling 25. It is spoken on every visit to the control.
- It says what the user needs at that control that the name does not already say.
  Never restate the name.
- One description, one control. If a note applies to a group, describe the
  fieldset once, not each control in it.
- `aria-describedby` can list several ids. Count the words of all of them, in the
  longest state each one can reach (a status line that grows after an action
  counts at its longest).
- Text over the ceiling stays on the page as visible text next to the control and
  is not wired to `aria-describedby`. Browse mode users still read it, when they
  choose. Wire only the one sentence that matters, by putting the id on a `<span>`
  around that sentence (pattern P9).
- `title` becomes a description too, and is read after the value. Keep tooltips
  human words, not internal numbers.
- A placeholder is also sent to speech, after the description. Keep it short and
  free of symbols.
- Visually hidden (`sr-only`) text gets more review than visible text, because no
  sighted reviewer will ever see it.

### A5. Status messages (how the page talks)

- Keep one status channel: an element that is always rendered, visually hidden,
  with `role="status"` (which implies `aria-live="polite"`). Every status message
  goes through it (pattern P1).
- Visible message boxes (warnings, notes, errors) keep their own look and
  position. They do not carry `role="status"` or `aria-live` themselves when they
  are hidden between messages; the channel speaks for them, with the box's own
  text, so what is heard matches what is shown. Two live regions for one message
  risk it being spoken twice.
- Writes are owned: each message names its source, and a source clears the
  channel only if its own message is still the one showing. Otherwise hiding one
  warning silently wipes another.
- A message is spoken once per episode: when it appears. While it stays on screen,
  updates are visual only. When it goes away and comes back, it is spoken again
  (pattern P2).
- A message caused by a control (a radio, a checkbox) is written one task later
  (`setTimeout(..., 0)`), so the control's own state ("checked") is spoken first
  (pattern P3). If one action produces several sentences, build one composed
  message.
- Checks that run while someone types wait for a pause (debounce), and what they
  announce must describe what the person meant to type. Test at two typing paces
  (see T9): a 250 ms pause was shorter than a slow typist's gap between keys, so
  warnings came mid-word with numbers for the half-typed text.
- A check for a control that is hidden, or a mode that is not selected, returns
  without announcing. Check again right before announcing, because a scheduled
  check can run after the user switched modes.
- Loading: say "still loading" only when a press actually has to wait, say it
  once, and take it down when the wait ends.
- A progress line is spoken once per run, not once per step that rewrites it.
- Downloads: the browser may say nothing when a file is saved (K14). The page's
  own message must say the file is ready and what to press.

### A6. Live regions: the hard rules

These five broke in practice. Each one passed Lighthouse and axe-core.

1. **The region exists, shown, before its text is written.** Writing into a
   `display: none` region and then showing it is an insertion, not a change, and
   it is not announced. The first message is lost; a message that appears once
   with fixed text is lost every time.
2. **Nothing is written into a live region while the page loads,** and nothing
   while saved settings are restored. Put the starting text and attributes in the
   HTML. The load must be silent.
3. **Write only when the text changes.** Assigning the same text again still
   replaces the text node, and NVDA can announce it again (`"Normal"` written over
   `"Normal"` was announced).
4. **Keep a live region's attributes stable.** NVDA announced a `title` being
   added, changed or removed on a `role="status"` element. Treat `aria-label` and
   other naming attributes the same way (INFERRED; only `title` was measured).
5. **Never count `role="status"` nodes in a test without waiting for them to
   settle.** Pages add and remove short-lived status nodes.

### A7. Focus

- Never disable or remove the focused element without deciding where focus goes.
  A focused button that disabled itself dropped focus to `body`; NVDA said nothing,
  and the next Tab started again from the landmarks. Give focus back when the work
  ends, but only if focus is still on `body`, so a user who moved on is not pulled
  back (pattern P4).
- Do not move focus on page load. Do not move focus when async work finishes,
  except back to the control that started it.
- A disclosure button keeps focus when it opens, unless the design moves focus to
  the panel's first control. If it does, wait until the panel is rendered.
- A disabled option stays findable in browse mode and says why it is disabled:
  point its `aria-describedby` at the visible note that explains the lock. NVDA
  read both descriptions, the reason included.

### A8. Forms and validation

- Every control that can be invalid must be reachable and its message spoken.
  Native validation on a control that is hidden or collapsed fails silently: the
  button just does nothing. Reveal the control through its real toggle, focus it,
  and show one message, however many fields failed.
- Number fields carry `min` and `max`. Without them Chrome reports a range of 0 to
  0, so a wrong range is announced rather than none.
- Read validity with `element.validity.valid`. `checkValidity()` fires `invalid`
  events, which can trigger handlers during page load.
- Text fields that hold names, codes or other languages: NVDA says "spelling
  error" inside words the browser's spellchecker marks. Decide per field whether
  `spellcheck="false"` is right.

### A9. Keyboard

- Every control works from the keyboard (Tab, Shift+Tab, Enter, Space, Escape,
  arrow keys) and shows a visible `:focus-visible` ring.
- Radio groups move with the arrow keys. Space on a radio that is already checked
  does nothing in Chrome, so never hide an action behind re-selecting the selected
  option. Give it a button.

### A10. Language

- The `lang` attribute on `html` is correct, and other-language text carries its
  own `lang`. NVDA announces a language code its voice cannot speak, for example
  "und (not supported)" for `lang="und-Brai"`. Decide whether that is wanted.

---

## Part P: Code patterns

Copy these and adapt the names. Each one fixes a bug that shipped.

### P1. The status channel

```html
<!-- Always rendered. Hidden visually, never with display:none. -->
<div id="sr-status" class="visually-hidden" role="status"></div>
```

```css
.visually-hidden {
  position: absolute; width: 1px; height: 1px; margin: -1px; padding: 0;
  overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; border: 0;
}
```

```js
// source: the id of the box or feature that owns the message.
function announce(source, message) {
  const region = document.getElementById('sr-status');
  if (!region) return;
  if (message) {
    if (region.dataset.source === source && region.textContent === message) return;
    region.dataset.source = source;
    region.textContent = message;
  } else if (region.dataset.source === source) {
    region.dataset.source = '';
    region.textContent = '';
  }
}
```

### P2. Once per episode

```js
function showWarning(box, text) {
  const wasHidden = box.hidden;
  box.querySelector('.warning-text').textContent = text;
  box.hidden = false;
  if (wasHidden) announce(box.id, box.textContent.replace(/\s+/g, ' ').trim());
}

function hideWarning(box) {
  if (box.hidden) return;
  box.hidden = true;
  announce(box.id, '');
}
```

### P3. Let the control speak first

```js
modeRadios.forEach((radio) => radio.addEventListener('change', () => {
  applyMode(radio.value);
  const message = composeModeMessage(radio.value);
  setTimeout(() => announce('mode', message), 0);
}));
```

Do not "tidy" the `setTimeout` away: there is no declarative way to order a live
region after a control's own state announcement.

### P4. Keep focus when a button disables itself

```js
button.addEventListener('click', async () => {
  const hadFocus = document.activeElement === button;
  button.disabled = true;
  try {
    await doTheWork();
  } finally {
    button.disabled = false;
    if (hadFocus && document.activeElement === document.body) button.focus();
  }
});
```

### P5. A live value with a tooltip

```html
<span id="brightness-value" role="status" title="140% of base lighting">Normal</span>
```

```js
function showValue(el, text, tooltip) {
  if (el.textContent !== text) el.textContent = text;
  if (el.getAttribute('title') !== tooltip) el.setAttribute('title', tooltip);
}
```

The HTML holds the start-up text and tooltip, so start-up writes nothing.

### P6. A group whose heading changes

```html
<fieldset aria-labelledby="entry-heading">
  <legend><h2 id="entry-heading">Enter text</h2></legend>
  ...
</fieldset>
```

### P7. Speak an existing message box without touching its writers

When many places in the code write to one visible box, relay the box instead of
adding an `announce()` call to each writer:

```js
const box = document.getElementById('error-message');
const relay = () => {
  const shown = !box.hidden && getComputedStyle(box).display !== 'none';
  announce('error-message', shown ? box.textContent.replace(/\s+/g, ' ').trim() : '');
};
new MutationObserver(relay).observe(box, {
  childList: true, subtree: true, characterData: true, attributes: true,
});
```

Remove `role="alert"` or `aria-live` from the box itself, or the message can be
spoken twice.

### P8. A skip link that moves focus

```html
<a class="skip-link" href="#task-heading">Skip to text entry</a>
...
<h2 id="task-heading" tabindex="-1">Enter text</h2>
```

### P9. One sentence described, the rest visible

```html
<p class="field-note">
  <span id="braille-help">Accepts braille characters only.</span>
  The longer background stays here as visible text.
</p>
<textarea id="braille" aria-describedby="braille-help"></textarea>
```

---

## Part T: Tests and automated checks

### The five layers

Each layer catches something the one before it cannot. Each one also missed a real
bug (column 4). Run layers 0 to 3 on every change in scope; layer 4 is the verdict.

| Layer | Tool | Catches | Missed in practice |
| --- | --- | --- | --- |
| 0. Markup | W3C Nu validator | Invalid nesting, duplicate ids, bad ARIA attributes | Everything that happens at runtime |
| 1. Rule scanners | axe-core, Lighthouse | Missing names, bad roles, contrast on visible plain backgrounds | Silent live regions; contrast on hidden boxes and gradients; load-time speech |
| 2. Accessibility tree | Playwright + Chrome DevTools Protocol | Computed names, descriptions and word counts, roles, states, tab order, headings, landmarks, number ranges | Whether and when anything is spoken; NVDA's stale group name |
| 3. Event recorder | `scripts/live-region-recorder.js` in Playwright | Live region writes (same text included), attribute changes, insertions, focus lost to `body` | Whether the screen reader spoke it; the order against the control's own state; how NVDA moves |
| 4. Screen reader | NVDA + `scripts/nvda-walk.py` (part N) | What was said, when, how often, in what order | How it sounded, and whether it was pleasant (human judgement) |

### Rules for screen reader tests

**T1. Pin the behaviour, not the markup.** Every change to a live region, to focus
handling, or to a name or description gets a layer 3 test: silence at load, once
per episode, focus kept. Example:

```js
// Playwright. The recorder must load before the page's own scripts.
test.beforeEach(async ({ context }) => {
  await context.addInitScript({ path: 'path/to/live-region-recorder.js' });
});

test('the page is silent while it loads', async ({ page }) => {
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  const atLoad = await page.evaluate(() => window.__srRecorder.since());
  const spoken = atLoad.filter((e) => e.kind === 'write' || e.kind === 'attr');
  expect(spoken).toEqual([]);
});

test('Translate keeps keyboard focus', async ({ page }) => {
  await page.goto('/');
  await page.fill('#text', 'hello');
  await page.evaluate(() => window.__srRecorder.mark());
  await page.focus('#translate');
  await page.keyboard.press('Enter');
  await expect(page.locator('#result')).not.toBeEmpty();
  const lost = (await page.evaluate(() => window.__srRecorder.since()))
    .filter((e) => e.kind === 'lost');
  expect(lost).toEqual([]);
});
```

If the page writes `class` or `style` on a live region at load for layout, narrow
the filter to the attributes that change speech (`title`, `aria-*`, `role`), and
say why in the test.

**T2. A new test fails on the old code first, for the bug's own reason.** Run it on
the code before the fix and keep the failure message. A test that never failed
proves nothing.

**T3. Compare with the element's own text.** A test that filtered announcements on
a word copied from a different message passed on the broken page. Read the text
the page actually shows and compare with that.

**T4. Wait for settled states.** Poll (`expect.poll`) rather than asserting a count
right after load. Short-lived nodes come and go.

**T5. Prove a probe detects before trusting a zero.** Run every new probe on a
version that has the bug. The recorder in this repo was proven on a page with two
real bugs: it reported both, and nothing on the fixed page.

**T6. Measure the running page, never the source file.** Scripts add, show and
rename things after load. Open every collapsed panel through its real toggle
before measuring it; a hidden node is left out of the accessibility tree and drops
out of every count.

**T7. Read the computed accessibility node** (layer 2) for names and descriptions:

```js
// Playwright + Chrome DevTools Protocol: what a screen reader is given.
async function axNode(page, selector) {
  const cdp = await page.context().newCDPSession(page);
  await cdp.send('DOM.enable');
  await cdp.send('Accessibility.enable');
  const { result } = await cdp.send('Runtime.evaluate',
    { expression: `document.querySelector(${JSON.stringify(selector)})` });
  const { node } = await cdp.send('DOM.describeNode', { objectId: result.objectId });
  const { nodes } = await cdp.send('Accessibility.getPartialAXTree',
    { backendNodeId: node.backendNodeId, fetchRelatives: false });
  const ax = nodes.find((n) => n.backendDOMNodeId === node.backendNodeId) || nodes[0];
  return { role: ax.role?.value, name: ax.name?.value, description: ax.description?.value };
}
```

Count description words from `description`, never from the HTML.

**T8. Contrast is measured directly,** against the painted background, with hidden
message boxes forced visible, after any theme transition has finished. Lighthouse
skips hidden elements and elements over gradients.

**T9. Type at two paces** in tests of anything that reacts to typing: fast (under
0.25 s per key) and slow (about 0.4 s per key). Record what is announced at each.

**T10. Check text size and narrow screens** for any moved or new control: 100 %,
150 % and 200 % text, on a 320 px wide portrait and a short landscape viewport.
Layers 0 to 3 run at 100 % and miss clipped panels.

---

## Part N: The NVDA check

### N1. When it is required

- Any change to a live region, to focus handling, to the name, role or
  description of an interactive control, or to headings, landmarks or skip links.
- Every screen reader bug fix: re-run the step that failed, before and after.
- Every release: every walkthrough, in full.

### N2. Who drives

There are two ways, and both use NVDA's own log as the record:

1. **A person drives NVDA, the agent reads the log.** The person follows the
   walkthrough; the agent marks the log before each step and reads it after
   (`nvda-walk.py mark` and `since`).
2. **The agent drives NVDA** with `nvda-walk.py keys`, on the machine owner's
   computer, with their permission for this session. It sends real key presses to
   the browser window, so the person must leave keyboard and mouse alone while it
   runs.

If neither is possible (no Windows machine, no NVDA, no permission), run layers 0
to 3, report the NVDA check as NOT RUN with the reason, and hand the walkthrough to
a person. Never report a screen reader pass without the log.

### N3. One-time setup

1. Install NVDA from nvaccess.org.
2. Set NVDA's logging to input/output: NVDA menu > Preferences > Settings >
   General > Logging level > "input/output". Press any key, then run
   `python scripts/nvda-walk.py check`. It prints the log path, NVDA's version
   and how many input/output entries it found. Zero entries means the logging
   level is not set yet.
3. Leave the symbol level at NVDA's default ("some") unless the walkthrough says
   otherwise, and record it. NVDA+P changes it.
4. Note the voice, the NVDA version, the browser and its version, and Windows'
   version. They go in every record.

**Privacy.** At input/output level NVDA logs every key pressed and everything it
speaks, in every program, passwords included. Turn the level on for the check and
back to "info" afterwards. Never commit a raw log. Save only the stretch of the
log that covers the walkthrough, and read it before sharing it.

**The log restarts with NVDA.** `%TEMP%\nvda.log` starts again when NVDA restarts
(the previous one becomes `nvda-old.log`, overwritten at the next restart). Marks
are byte positions in one file, so save each step's evidence as you go and take a
new mark after any restart.

### N4. Before each run

1. Serve the app locally (a development server), never a site with real user data.
2. Put the app in a known state: clear its saved settings (site data or
   `localStorage`) as the walkthrough says.
3. Load it at an address NVDA has not seen in this session, for example
   `/?fresh=7`, or press Ctrl+Home after the load (K2). Check first that the page
   ignores the query string.
4. Do not click in the page before the first Tab: a click moves the browser's
   starting point for Tab.
5. Record the commit or a hash of the page you are testing.

### N5. Safety when the agent drives

- Ask the machine owner before the first key, and say what will happen: the
  browser will be brought to the front and keys will be pressed in it.
- Always pass `--title` with the app's page title. Before every key the tool checks
  that the window in front is a browser showing that title, and stops (exit code
  2) if not. Never weaken or bypass that check. When it stops, ask the person to
  bring the browser forward, or use `nvda-walk.py focus` only when the app is the
  active tab of its window.
- Never type credentials, payment data or personal data. Never accept prompts or
  dialogs the walkthrough does not name.
- Only download files the walkthrough asks for, and list them in the record.

### N6. Driving rules

- **Check where each key landed before you press Enter, Space, an arrow key or a
  letter.** Batch only keys that move without changing anything: Tab, Shift+Tab
  and NVDA's navigation keys. A fixed sequence sent without looking pressed the
  wrong button twice in one run.
- **After every load, press Ctrl+Home.** NVDA puts its reading position back where
  it was on that address.
- **The first Tab goes to the item after NVDA's reading position,** which on a fresh
  page is the second focusable item (K1). After H, D, E or arrow navigation, Tab
  goes to the next control after that position, which can be an unchecked radio.
- **Know the mode.** After Tab lands on an edit field, combo box, spin button or
  radio, NVDA is in focus mode and letters type into the field. Press Escape
  before quick navigation letters (H, D, E, B, F, K, R, X). In browse mode, Escape
  goes to the page, so press it only in focus mode.
- **To press a radio that is already checked,** press Escape (browse mode), then
  Enter. Space does nothing on it (K11).
- **To hear a control browse mode reached but focus did not** (for example a
  disabled option): NVDA+Numpad 5 on the desktop layout, NVDA+Shift+O on the
  laptop layout. NVDA+Tab reports the focused control.
- **Type at the pace the step asks for,** and record it in seconds per key.
- **Wait after the last key** (2 to 5 seconds, longer for slow work) so late
  announcements land in the same step.

Example, one step of an agent-driven run:

```text
python scripts/nvda-walk.py keys --title "My App" --gap 900 --tail 3000 \
    --out step05.txt "@Step 5: Tab to the text box" tab tab
python scripts/nvda-walk.py keys --title "My App" --chargap 120 \
    --out step06.txt "@Step 6: type" "text:hello world"
python scripts/nvda-walk.py keys --title "My App" --tail 8000 \
    --out step07.txt "@Step 7: Generate" space
```

### N7. Reading the log

- `KEY` lines are the keys NVDA received; `SAY` lines are what NVDA sent to the
  voice, in order, with NVDA's timestamps. The times are when speech was queued,
  not when it was heard. Overlap and interruption are not visible.
- The log holds text before NVDA turns symbols into words. To know how a symbol was
  spoken, look it up in NVDA's symbol table
  (`C:\Program Files\NVDA\locale\en\symbols.dic`) at the recorded symbol level.
- Leave out speech that is not the app: browser bars and notices ("Infobar"), tab
  labels, extension text. List what you left out in the record.
- NVDA's own reading is not an announcement: the automatic read of the page after
  a load, and the readout of the control that receives focus. An announcement is
  speech the page caused through a live region or a description change.
- `nvda-walk.py count NAME "text"` counts how many times a sentence was spoken
  since a mark.

### N8. Judging a step

A step passes when all of these hold:

- The control's **name, role and state** are all there. Their order varies with
  the control and NVDA's settings; order alone is never a fail.
- Each expected announcement is spoken the expected number of times, usually once.
- Where the step expects silence, nothing from the page is spoken.
- Nothing is spoken while the person is still typing, unless the step expects it.
- Names match what is on screen now (no stale group names).

Write down what was said, quoted from the log, and the count. Never write "yes".

### N9. Evidence to keep

- One transcript file per step (`nvda-walk.py keys --out`), plus the stretch of raw
  log for the whole run.
- Versions: NVDA, voice, symbol level, browser, Windows; the commit or page hash;
  date and time.
- Mishaps: any key that landed somewhere unplanned, what it changed, and how it was
  put back.
- Files the run created (downloads).

### N10. Re-checking a fix

- Re-run the exact failing step, before the fix and after, and keep both
  transcripts.
- Pick decisive cases. If the bug is a stale name, the check only proves something
  when the name must change on that step; a stale name can match the right one by
  chance.
- Repeat a bug that does not happen every time, several times, and report the
  count (for example "4 of 4 right").
- If the new test passes but NVDA still says the bug, the fix is not done (G3).
  Find what NVDA reacted to, extend the test to watch it, and fix again.

### N11. What the log cannot tell you

How it sounded, whether speech overlapped, how long a real person needs, and
whether it felt clear or tiring. Ask the person. A timing written by the agent is
not a person's timing; leave "how long" lines to a person.

---

## Part W: Writing walkthroughs

A walkthrough is a script a person or an agent can follow with NVDA, step by step,
with what they should hear. Use [templates/nvda-walkthrough.md](../templates/nvda-walkthrough.md).

- **W1. One flow per walkthrough,** with its purpose, who runs it, how long it
  takes a person, setup, and the known state to start from.
- **W2. Every step is keys, then Expect, then Fail if.** Keys are exact
  ("Tab twice", "Escape, then Enter"). Expect quotes the speech. Fail if names the
  bug the step exists to catch. Where a count matters, the step asks for the count.
- **W3. Write steps from how NVDA moves,** not from how the page looks: Ctrl+Home
  after a load, the first Tab going to the second item, browse and focus mode,
  Escape then Enter on a checked radio.
- **W4. Quote approved wording exactly.** A walkthrough never rewords what the app
  says; if the app's wording changes, the step changes to match.
- **W5. Say the typing pace** wherever the step types into something that reacts.
- **W6. Keep a results table** in the walkthrough, and a history table with dated
  rows. Add rows; never rewrite old ones.
- **W7. Replay every step you changed,** with NVDA, before you call the edit done,
  and record which steps were replayed.
- **W8. Say honestly what has been run.** A banner such as "re-measured in the
  accessibility tree, not yet run with NVDA" stays until NVDA has run it.

---

## Part D: What to hand over

### D1. A UI change

- The code, with the patterns from part P where they apply.
- A layer 3 test that failed on the old code first (its failure message quoted).
- Layer 0 to 2 results: validator errors and warnings, Lighthouse score, axe
  violations, description word counts for changed controls.
- The NVDA check: transcripts for the changed steps, or NOT RUN with the reason
  and the walkthrough handed over.
- The specification or design note updated, and a changelog entry.
- Every new or changed piece of spoken wording listed and marked DRAFT for sign-off.

### D2. A walkthrough run

- The results table for each walkthrough (template), with what NVDA said quoted
  from the log, counts, and pass or fail per step.
- Findings, each with an id, what was heard, what was expected, the evidence file,
  the cause if known (labelled MEASURED or INFERRED), and a proposed fix.
- Observations kept apart from findings: things that pass but may be worth a
  decision.
- Versions, mishaps, files created, and what the log could not tell.

### D3. A screen reader bug fix

Everything in D1, plus the NVDA transcripts of the failing step before and after,
and the finding's status updated (fixed, with the commit).

### D4. Definition of done

- [ ] Layers 0 to 3 pass, and every new test failed first on the old code
- [ ] NVDA check run and recorded (or NOT RUN, with the reason and a handover)
- [ ] Silence at load, once per episode, no focus lost (counts written down)
- [ ] Description word counts within the ceiling, or a recorded human decision
- [ ] Spoken wording changes marked DRAFT and sent for sign-off
- [ ] Walkthrough steps that changed were replayed with NVDA
- [ ] Records labelled MEASURED, REPORTED, INFERRED or PREDICTED

---

## Part E: Accessibility targets

| Target | How it is checked |
| --- | --- |
| WCAG 2.2 Level AA (configure your own target in the rule files) | The rows below |
| 1.3.1 Info and Relationships: headings, landmarks, groups, labels | Layer 2 counts; NVDA H and D navigation |
| 2.1.1 Keyboard | Every control operated by keyboard in the walkthrough |
| 2.4.1 Bypass Blocks: skip links move focus | `document.activeElement` after Enter; NVDA says where it landed |
| 2.4.3 Focus Order: logical, never lost | Recorder: zero `lost` entries in the flows tested |
| 2.4.6 Headings and Labels | Layer 2 names; a person judges whether they describe |
| 2.4.7 Focus Visible | A visible ring on every control, in every theme |
| 2.5.3 Label in Name | Layer 2 name contains the visible label |
| 3.2.1 On Focus, 3.2.2 On Input | No unexpected page change on focus or on input |
| 3.3.1 Error Identification | Every error shown and spoken once |
| 4.1.2 Name, Role, Value | Layer 2, then NVDA |
| 4.1.3 Status Messages | Recorder and NVDA: spoken once, without moving focus |
| W3C validator | 0 errors, 0 warnings |
| Lighthouse accessibility | 100 (necessary, not sufficient) |
| axe-core | 0 violations on every opened state |
| Descriptions | 15 words target, 25 ceiling per control, all ids counted |
| Contrast | 4.5:1 text, 3:1 controls and focus rings, measured directly |
| Touch targets | 44 by 44 px or larger |
| Text size | Usable at 200 % with no clipping or sideways scrolling |
| Load | Zero live region writes and zero attribute changes during load |

---

## Part H: Triage

- **Finding:** the page is wrong (information lost, repeated, stale, or focus lost).
  **Observation:** the page works as designed, but it may be worth a decision
  (verbose, odd wording, a symbol read aloud).
- **Severity:**
  - Blocker: information a user needs is not spoken (a silent warning, a silent
    error), or focus is lost.
  - Major: speech repeats or chatters, a name is stale, the order misleads.
  - Minor: verbosity within reason, odd but correct wording.
- Write each finding with the quote from the log, the expected speech, the evidence
  file, and the cause if you know it.
- The person decides which findings are fixed now and which observations are
  acted on. Ask in one batch, with a recommendation for each.
- Never "fix" a finding by deleting visible text or ARIA without measuring what the
  change does to speech, and never reword approved text on your own.

---

## Part K: Known NVDA and Chrome behaviours (measured)

NVDA 2026.2 + Chrome 150 on Windows 11 unless the row says otherwise. Re-measure
after updating either.

| # | Behaviour | Consequence |
| --- | --- | --- |
| K1 | The first Tab after a page load goes to the second focusable item (9 of 9 loads) | Walkthroughs say "first Tab: second skip link"; reach the first with Shift+Tab |
| K2 | NVDA restores its reading position per address; a skip link adds `#id` to the address | Press Ctrl+Home after every load, or use a never-seen address |
| K3 | D (landmark navigation) announces two landmarks that start at the same place together: five landmarks in three presses | Count landmark names heard, not presses |
| K4 | Focus landing on a large container reads its whole text | Point skip links at headings |
| K5 | A heading inside a group's legend: the name is said twice | Accept or redesign on purpose |
| K6 | A live region written at load is announced; so is a rewrite with the same text, and a `title` added, changed or removed | Rules A6.2 to A6.4 |
| K7 | A live region revealed or inserted with its text already inside is not announced (NVDA 2026.1, August 2026) | Rule A6.1 |
| K8 | A description equal to the name is not spoken (NVDA 2026.1) | Do not count on it for other screen readers |
| K9 | A fieldset named by its legend keeps its old name after the legend's heading changes; `aria-labelledby` fixes it | Rule A3 |
| K10 | A focused button that disables itself drops focus to `body`; NVDA says nothing; the next Tab starts again from the landmarks | Pattern P4 |
| K11 | Space on a radio that is already checked sends no click | Escape, then Enter in walkthroughs; never hide an action behind it |
| K12 | Symbols in names are spoken as words at the default level "some" ("down arrow", "right arrow") | Rule A3 |
| K13 | Words the spellchecker marks are read with "spelling error" when a text field is read back | Rule A8 |
| K14 | Chrome's download bubble said nothing when a file was saved | Rule A5 (downloads) |
| K15 | `lang="und-Brai"` is announced as "und (not supported)" | Rule A10 |
| K16 | A status written inside a control's change handler can be spoken before the control's own state (NVDA, August 2026) | Pattern P3 |
| K17 | A placeholder is sent to speech after the description | Rule A4 |

---

## Appendix: NVDA keys used in walkthroughs

| Keys | What they do |
| --- | --- |
| NVDA key | Insert (or Caps Lock if set up) |
| Tab, Shift+Tab | Next, previous control |
| Enter, Space | Press a button; Space ticks a checkbox |
| Arrow keys | Move in a radio group; in browse mode, move line by line |
| Escape | Leave focus mode |
| NVDA+Space | Switch between browse and focus mode |
| H, D, E, F, B, K, R, X, C | Browse mode: next heading, landmark, edit field, form field, button, link, radio, checkbox, combo box (Shift goes back) |
| NVDA+Down arrow (desktop), NVDA+A (laptop) | Read from here (say all) |
| NVDA+Tab | Report the focused control |
| NVDA+Numpad 5 (desktop), NVDA+Shift+O (laptop) | Report the object at the browse position |
| NVDA+F7 | Elements list (headings, links, landmarks) |
| NVDA+P | Change the symbol level |
| Ctrl | Stop speech |
| NVDA+N | NVDA menu (Tools > Speech viewer, Tools > View log) |

## Related

- [NVDA_WALKTHROUGH_LESSONS.md](NVDA_WALKTHROUGH_LESSONS.md): where these rules came from
- [WEBSITE_REACTIVE_CONTROL_MEASURES.md](WEBSITE_REACTIVE_CONTROL_MEASURES.md): the ARIA-live restraint guardrail
- [AI_TASK_DELEGATION_RULES.md](AI_TASK_DELEGATION_RULES.md): who may write accessibility-critical text
- [checklists/post-edit-verification.md](../checklists/post-edit-verification.md): where the screen reader check sits in tier 2
