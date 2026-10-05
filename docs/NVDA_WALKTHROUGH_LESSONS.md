# Lessons from the First AI-Driven NVDA Checks

In October 2026, for the first time in this playbook's projects, an AI agent drove
a real screen reader and read the screen reader's own record of what it said. It
did not guess from the markup, and it did not wait for a person to describe what
they heard. It pressed the keys, read NVDA's log after every step, found bugs that
every automated check had passed, fixed four of them the same day, and re-checked
each fix with NVDA before calling it done.

This note records what happened and what we learned. The rules that came out of it
are in [SCREEN_READER_STANDARD.md](SCREEN_READER_STANDARD.md).

**Source:** an assistive technology web app that generates 3D-printable braille
parts in the browser, with an accessibility-first UI. Its screen reader work ran
from August to October 2026. Names and project-specific feature names are left
out; dates and measurements are as recorded at the time.

## What was new

Before, screen reader feedback reached the agent second hand. The agent read the
markup or the browser's accessibility tree and predicted what a screen reader
would say, and a person ran NVDA now and then and reported back. Predictions were
sometimes wrong in both directions: a duplicate the tree "proved" was never
spoken, and an announcement the tree "allowed" never happened.

The new loop:

1. NVDA's logging level is set to input/output, so NVDA writes every key it
   receives and every piece of text it sends to the voice into its log, with
   timestamps.
2. The agent sends real key presses to the browser through the Windows SendInput
   API, so NVDA handles them exactly like a keyboard. Before every key it checks
   that the browser window showing the app is in front, and stops if not.
3. After each step the agent reads the new stretch of NVDA's log: the keys, the
   speech, the times. It counts announcements and quotes them.

The tool is [scripts/nvda-walk.py](../scripts/nvda-walk.py). The method is part N
of the standard.

## Timeline

| Date (2026) | What happened | Who drove NVDA |
| --- | --- | --- |
| Aug 18 | The first listen found status messages that were shown on screen and spoken nowhere. An audit then found 8 of 10 live regions missing from the accessibility tree at load. Lighthouse and axe-core had scored 100. | The owner |
| Aug 22 | The first full session: 34 minutes (estimated 12), 15,881 words spoken. Three `aria-describedby` paragraphs were 54% of everything said; one was repeated 59 times. This produced the 15-word target and 25-word ceiling for descriptions. | The owner; the agent read NVDA's log |
| Aug 23 | A predicted "name said twice" never happened: NVDA does not speak a description equal to the name. | The owner; the agent read the log |
| Oct 2 | The three walkthroughs were re-measured in Chromium's accessibility tree. One could not be completed as written: it never typed the text a later step needed. | Nobody (no screen reader) |
| Oct 4, 12:49 to 13:39 | The agent ran all three walkthroughs itself: 792 keys, about 1,100 utterances. Results: 27 of 27 steps, 12 of 13 listening steps, and a page-structure walk whose counts matched or differed only by how NVDA moves. Five findings and seven observations. | The agent |
| Oct 4, afternoon | Four fixes, one at a time: three code fixes, each with a test that failed first, then the walkthrough corrections. Each was re-checked with NVDA and passed CI. One fix needed a second attempt (lesson 3). | The agent |

## What the October run found

| # | What NVDA did | Cause | Fix (standard rule) |
| --- | --- | --- | --- |
| 1 | Every page load said "Normal, Normal" with no context | Start-up code rewrote two live values with the same text and added a `title` to each | Start-up values in the HTML; write text and attributes only when they change (A6, P5) |
| 2 | After pressing a Translate button, focus was gone; the next Tab started again from the landmarks | The button disabled itself while focused, so focus fell to `body` | Give focus back when the work ends, if it is still on `body` (A7, P4) |
| 3 | A section's group name lagged one switch behind its heading after a mode change | The fieldset was named only by its legend, and NVDA kept the old name | `aria-labelledby` on the fieldset, pointing at the heading (A3, P6) |
| 4 | Warnings were spoken mid-word, with numbers for half-typed text, when typing slowly | A 250 ms debounce is shorter than a slow typist's gap between keys | Open: test at two paces and choose a pause that fits slow typists (A5, T9) |
| 5 | Steps in the walkthroughs did not match how NVDA moves | The walkthroughs were written from how the page looks | Walkthroughs written from NVDA's movement and replayed after edits (part W, K1 to K3, K11) |

Observations, for the owner's judgement rather than failures: a skip link to `main`
made NVDA read several hundred words; headings inside legends were said twice;
two sentences read oddly aloud ("1 are available", a negative length in
millimetres); "spelling error" inside text fields; arrows in button names read as
"down arrow"; nothing said when a file downloaded; a placeholder sent to speech;
and a stepper reading its technical tooltip after the new value.

## Lessons

### 1. Direct feedback turns opinions into counts

"NVDA should say the warning once" became "NVDA said it once, at this time to the
millisecond, in these words". Arguments about whether something chattered ended,
because the log answered them. Every finding above came with a quote, a time and a
count.

### 2. Every automated layer missed something

| Bug | Would this layer have caught it? |
| --- | --- |
| "Normal, Normal" on load | Validator: no. Lighthouse and axe: no. Accessibility tree: no. The old live-region recorder: no, because it ignored identical rewrites and attributes. The new recorder: yes (proved on the old page). NVDA: yes. |
| Focus lost after Translate | Validator, Lighthouse, axe, tree: no. A focus check in the browser: yes. NVDA: yes. |
| Stale group name | Validator, Lighthouse, axe: no. Chromium's accessibility tree: no, it had the right name. Only NVDA showed it. |
| Status messages silent (August) | Validator, Lighthouse, axe: no. A tree check across the write: yes. NVDA: yes. |
| Descriptions as half of all speech (August) | Nothing measured it until a word count of the computed descriptions was added. NVDA's log showed it first. |

The layers are all worth running. None of them is the verdict.

### 3. A passing test was not a fix

The first fix for "Normal, Normal" stopped the identical text rewrites. Its new
test failed on the old page and passed on the new one. NVDA still said "Normal,
Normal". Measuring with NVDA listening showed why: adding a `title` to a live
region is announced too, and start-up still added the titles. The second attempt
put the titles in the HTML and extended the test to watch attribute writes; that
test failed on the first attempt's page, and NVDA went quiet. The rule since then:
the screen reader re-check decides, and when it disagrees with the test, the test
is missing something.

### 4. A recorder has blind spots until it is proven on a real bug

The live-region recorder used before the walk only noted text that changed, and
never looked at attributes, so it could not see the "Normal, Normal" bug. The
recorder in this repo records identical rewrites, attribute changes, insertions
and focus lost to `body`. Run on the page from before the fixes, it reported 4
start-up writes on the two values and 1 lost focus after Translate; on the fixed
page, 0 and 0. Prove a probe on a known bug before you trust its zero.

### 5. Walkthroughs drift away from what a screen reader does

The walkthroughs were careful and still wrong for NVDA users:

- NVDA's first Tab after a load goes to the second focusable item, so "Tab, Tab,
  Enter" pressed the wrong button.
- NVDA reopens a page where you last were on that address, so "reload, then Tab"
  did not start at the top.
- Five landmarks are reached in three presses, because NVDA announces two that
  start at the same place together.
- Space does nothing on a radio that is already checked; Escape then Enter works.

Write walkthrough steps from NVDA's movement, and replay every changed step with
NVDA before calling the edit done.

### 6. Never send keys blind

A fixed key sequence, sent without checking where each key landed, pressed
"Decrease font size" twice and changed the preview contrast once. Each was put
back, and from then on the agent read the log after every move before pressing
Enter, Space, an arrow or a letter. Batching is only safe for keys that move
without changing anything.

### 7. The safety check earned its place

During a re-check another program was in front when keys were due. The tool
refused to send anything and stopped, and no key reached that program. Keep the
check, never bypass it, and ask the person to bring the browser forward.

### 8. Save evidence as you go

The owner restarted NVDA during the work. NVDA started a new log, and the old one
is overwritten at the next restart. Evidence that had already been copied out step
by step was safe; marks into the old log were not. Save each step's transcript as
you go, and take a new mark after any restart. The browser extension's tab group
also disappeared after the restart, so check which tab is in front before
continuing.

### 9. Choose checks that can fail

The stale group name only showed on some switches. A switch where the old and new
names happen to match proves nothing. The before-run counted decisive switches
only (the name failed to change in 6 of 7), and the after-run did four switches in
a row where the name had to change (4 of 4 right).

### 10. Typing speed changes what is heard

The same warning was spoken once at the end of typing at 0.24 s per key, and once
in the middle of a word at 0.41 s per key, with numbers for the half-typed text. A
pause between digits announced a warning for a value nobody meant. Test anything
that reacts to typing at two paces.

### 11. Some questions stay human

The log shows the words and the order, not how they sounded, whether they
overlapped, or whether the page felt tiring. The owner accepted the agent's run as
the release walk, and the "how long does this take" lines were left for a person
to time. An agent-driven walk is a strong correctness and regression check. It
does not replace a blind user's experience of the page.

### 12. Ask in one batch, with a recommendation

The run produced five findings and seven observations. They went to the owner as
four questions, each with a recommended answer. The owner chose four fixes now and
moved the rest to a later round, and the fixes started within minutes. Mixing the
observations into the fix list would have delayed the release for matters of
taste.

### 13. The August lessons still hold

These came from the owner's NVDA sessions and are in the standard too:

- A live region must be in the accessibility tree, shown, before its text is
  written (A6).
- Long descriptions crowd out everything else: 15-word target, 25-word ceiling (A4).
- A message caused by a control must wait one task so the control's own state is
  heard first (P3).
- A warning that recomputes on every key is spoken once per episode, not per key:
  measured 3 announcements before the gate and 1 after, and 11 before and 1 after
  for a note that never changes its text (A5, P2).
- A skip link target needs `tabindex="-1"` and must never be hideable (A2).
- Native form validation on a collapsed control fails silently (A8).

## What we would do from the start next time

1. Load the live-region recorder in the end-to-end tests from day one, with a
   "silent at load" test and a "no focus lost" test for every flow.
2. Write walkthroughs from NVDA's movement (Ctrl+Home, first Tab, modes), not from
   the page's look.
3. Run the NVDA check on every live-region or focus change, not only before a
   release. A short re-check of one step takes minutes.
4. Test typing at two paces wherever text drives a warning.
5. Keep findings and observations apart from the first report.

## Related

- [SCREEN_READER_STANDARD.md](SCREEN_READER_STANDARD.md): the rules
- [checklists/screen-reader-check.md](../checklists/screen-reader-check.md): the checklist
- [templates/nvda-walkthrough.md](../templates/nvda-walkthrough.md): the walkthrough template
- [LESSONS_LEARNED.md](LESSONS_LEARNED.md): lessons from the plan history
