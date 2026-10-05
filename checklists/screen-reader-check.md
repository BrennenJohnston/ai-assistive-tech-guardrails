# Screen Reader Check (NVDA)

Run this for any change a screen reader user will hear: live regions and status
messages, focus handling, names and descriptions of controls, headings, landmarks
and skip links. It is the short version of
[SCREEN_READER_STANDARD.md](../docs/SCREEN_READER_STANDARD.md); the rule ids in
brackets point into it.

## Before you write code

| # | Check | Method | Blocking? |
| --- | --- | --- | --- |
| 1 | Every status message goes through the one status channel, owned by its source | Read the design against [A5] and pattern [P1] | Yes |
| 2 | Each message is spoken once per episode, and a control's own state is spoken before the message | Patterns [P2] and [P3] | Yes |
| 3 | Nothing is written into a live region during page load | [A6] rule 2; start-up values live in the HTML [P5] | Yes |
| 4 | No focused element is disabled or removed without a plan for focus | [A7], pattern [P4] | Yes |
| 5 | Groups whose heading changes are named with `aria-labelledby` | [A3], pattern [P6] | Yes |
| 6 | Descriptions: target 15 words, ceiling 25, all ids counted, never restating the name | [A4] | Yes |
| 7 | Spoken wording that is new or changed is marked DRAFT for human sign-off | [Stop and ask a human] | Yes |

## Automated checks (layers 0 to 3)

| # | Check | Method | Blocking? |
| --- | --- | --- | --- |
| 8 | Markup valid | W3C Nu validator: 0 errors, 0 warnings | Yes |
| 9 | Rule scanners clean | axe-core 0 violations on every opened state; Lighthouse accessibility 100 | Yes |
| 10 | Computed names and descriptions read from the running page | Accessibility tree over CDP [T7], every panel opened through its toggle [T6] | Yes |
| 11 | Silent at load, once per episode, no focus lost | `scripts/live-region-recorder.js` in an end-to-end test [T1] | Yes |
| 12 | Every new test failed on the old code first, for the bug's reason | Run it before the fix; keep the failure message [T2] | Yes |
| 13 | Typing-driven checks tested at two paces | Under 0.25 s and about 0.4 s per key [T9] | Warning |
| 14 | Contrast measured directly, hidden boxes forced visible | [T8] | Yes (for style changes) |

## NVDA check (layer 4)

| # | Check | Method | Blocking? |
| --- | --- | --- | --- |
| 15 | NVDA logging at input/output, confirmed | `python scripts/nvda-walk.py check` [N3] | Yes |
| 16 | Known state, fresh address or Ctrl+Home, no click before the first Tab | [N4] | Yes |
| 17 | Changed steps run with NVDA, landing checked before every Enter, Space, arrow or letter | `nvda-walk.py keys --title ...` or a person driving [N2], [N6] | Yes |
| 18 | What NVDA said is quoted from its log, with counts | `nvda-walk.py since` / `count` [N7], [N8] | Yes |
| 19 | For a bug fix: the failing step before and after the fix | [N10] | Yes |
| 20 | Versions, transcripts and mishaps saved; IO logging turned back off | [N3], [N9] | Yes |

If NVDA cannot be run, write NOT RUN with the reason and hand the walkthrough to a
person. Never report a pass without NVDA's log.

## Copy-paste checklist (for PR descriptions)

```markdown
### Screen reader check (NVDA)

**Design**
- [ ] Status messages go through the status channel, once per episode
- [ ] Nothing written into live regions during load
- [ ] Focus never dropped to the page body
- [ ] Changed group headings named with aria-labelledby
- [ ] Descriptions within 25 words (all ids counted)
- [ ] New or changed spoken wording marked DRAFT for sign-off

**Automated (layers 0 to 3)**
- [ ] W3C validator: 0 errors, 0 warnings
- [ ] axe-core: 0 violations; Lighthouse accessibility: 100
- [ ] Names and descriptions read from the accessibility tree of the running page
- [ ] Recorder test: silent at load, once per episode, no focus lost
- [ ] New tests failed on the old code first

**NVDA (layer 4)**
- [ ] NVDA version: ___  Browser: ___  Symbol level: ___
- [ ] Steps run: ___ (transcripts attached or linked)
- [ ] What NVDA said, quoted, with counts
- [ ] Bug fixes: failing step before and after
- [ ] Or: NOT RUN, because ___, walkthrough handed to ___
```

### Project-specific configuration

- **Status channel element:** `[CONFIGURE: e.g., #sr-status]`
- **Walkthroughs folder:** `[CONFIGURE: e.g., docs/development/]`
- **Local app address and page title:** `[CONFIGURE: e.g., http://127.0.0.1:8000/, "My App"]`
- **Where NVDA evidence is kept:** `[CONFIGURE: a folder outside the repository, e.g., ../evidence/nvda/]`
