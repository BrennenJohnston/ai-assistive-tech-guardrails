# NVDA Walkthrough: [CONFIGURE: flow name, e.g., "Sign-up form warnings"]

<!--
Template from docs/SCREEN_READER_STANDARD.md, part W. Fill every [CONFIGURE: ...],
delete this comment, and keep one flow per walkthrough. Write each step from how
NVDA moves (part N6 and part K), not from how the page looks.
-->

**Purpose:** [CONFIGURE: one or two sentences: what this pass proves, and which
change or risk it covers.]

**Who runs this:** [CONFIGURE: a person with NVDA, or an AI agent with
`scripts/nvda-walk.py` and the machine owner's permission.]
**How long:** [CONFIGURE: a person's timing, in minutes. An agent's run time is
not a person's timing.]
**Created:** [CONFIGURE: date]
**Status:** [CONFIGURE: "Not yet run with NVDA" / "Last run with NVDA on <date>,
<n> of <n> steps passed". Keep this honest (rule W8).]

---

## Before you start

1. NVDA is installed and running. Its logging level is "input/output" (NVDA menu >
   Preferences > Settings > General > Logging level), checked with
   `python scripts/nvda-walk.py check`. Turn it back to "info" when you finish: at
   input/output NVDA logs every key and everything it says, in every program.
2. Start the app: `[CONFIGURE: command, e.g., npm run dev]`, then open
   `[CONFIGURE: local address]` in `[CONFIGURE: browser]`.
3. Put the page in the known state below, then load it at an address NVDA has not
   seen in this session (for example add `?fresh=1`, then `?fresh=2` next time), or
   press Ctrl+Home after the load.

   | Setting | Must be | Why it matters |
   | --- | --- | --- |
   | [CONFIGURE] | [CONFIGURE] | [CONFIGURE: which step depends on it] |

4. Do not click in the page before the first Tab. A click moves where Tab starts.
5. Optional for a person: NVDA menu > Tools > Speech viewer shows what NVDA says.
   The log is still the record.

### How NVDA moves (read this once)

- After every load, press **Ctrl+Home**: NVDA returns to where you last were on
  that address.
- From the top, NVDA's **first Tab goes to the second focusable item**. Shift+Tab
  reaches the first.
- After Tab lands on a text field, combo box, spin button or radio, NVDA is in
  **focus mode** and letters type into the field. Press **Escape** before using
  NVDA's letter keys (H for headings, D for landmarks).
- **Space does nothing on a radio that is already checked.** To press it again:
  Escape, then Enter.

### What "expected" means

NVDA says three things about a control: its **name**, its **role** (button, radio
button, edit) and its **state** (checked, expanded, unavailable). All three must be
there. The order varies, and order alone is never a fail. Where a step is about a
**count**, write the number you heard.

### The rule that matters most here

[CONFIGURE: e.g., "Each warning is spoken once, when it appears, never once per
key. Hearing it repeat while you type is a fail even if the words are right."]

---

## Part 0: Silence at load

**Step 0.** Load the page as in "Before you start" and press nothing for ten
seconds.

> **Expect:** NVDA's own reading of the page (its title, then reading from the top)
> and nothing else. No status message, no value read out of context.

**Fail if:** anything from the page's status messages is spoken before you touch
anything.

---

## Part 1: [CONFIGURE: part name]

**Step 1.** [CONFIGURE: exact keys, e.g., "Press Ctrl+Home, then Tab twice."]

> **Expect:** "[CONFIGURE: quoted speech, e.g., Email, edit, required, blank]"

**Fail if:** [CONFIGURE: the bug this step exists to catch.]

**Step 2.** [CONFIGURE: e.g., "Type `abc` at about one key every 0.4 seconds."]

> **Expect:** [CONFIGURE: e.g., the warning "...", spoken **once**, after you stop
> typing.]

**Count to write down:** [CONFIGURE: e.g., how many times the warning was spoken.]

**Fail if:** [CONFIGURE]

<!-- Repeat the step block as needed. Keep each step to one action and one
expectation. Quote approved wording exactly; never reword it here. -->

---

## For an agent-driven run

Run each step as its own command and read the transcript before the next step.
Only batch keys that move without changing anything (Tab, Shift+Tab).

```text
python scripts/nvda-walk.py check
python scripts/nvda-walk.py keys --title "[CONFIGURE: page title]" --tail 10000 \
    --out step00.txt "@Step 0: load and wait" ctrl+f5
python scripts/nvda-walk.py keys --title "[CONFIGURE: page title]" \
    --out step01.txt "@Step 1" ctrl+home tab tab
python scripts/nvda-walk.py keys --title "[CONFIGURE: page title]" --chargap 400 \
    --out step02.txt "@Step 2" "text:abc"
```

A reload is enough for Step 0, which only listens for silence. When a step depends
on where NVDA starts, load a never-seen address or press Ctrl+Home first.

---

## Results template

Copy this into your records, fill in what NVDA said (quoted from its log), and mark
each step.

```text
NVDA WALKTHROUGH RESULTS: [CONFIGURE: flow name]
Run by: (a person / an agent with nvda-walk.py)
Date and time:
NVDA version:          Voice:          Symbol level:
Browser and version:   Windows version:
App commit or page hash:
Typing pace (seconds per key):

Step | What NVDA said (from its log) | Times heard | Matched expected? | Pass/Fail
-----|-------------------------------|-------------|-------------------|----------
  0  |                               |             |                   |
  1  |                               |             |                   |
  2  |                               |             |                   |

Overall verdict:            /  steps passed
Speech left out as not the app (browser bars, tab labels, extensions):
Anything NVDA said that was not expected at all:

For the person (the log cannot answer these):
  Did anything talk over you while you were typing?
  Was anything tiring, confusing or too long?
  How long did the flow take you?
```

### Findings

One block per finding. A finding means the page is wrong.

```text
Finding id:
What NVDA said (quote, with the step and time):
What was expected:
Evidence file:
Cause, if known (MEASURED or INFERRED):
Proposed fix:
Severity (blocker / major / minor):
Decision needed from:
```

### Observations

Things that pass but may deserve a decision (verbose, odd wording, a symbol read
aloud). Keep them apart from findings.

### Mishaps

Any key that landed somewhere unplanned, what it changed, and how it was put back.

---

## Document history

| Version | Date | Changes |
| --- | --- | --- |
| 1.0 | [CONFIGURE: date] | Created. [CONFIGURE: "Not yet run with NVDA" or the run's result] |
