# Changes from original repo (this session)

Summary of all modifications made relative to the cloned repo at `katjamichlbauer1181/signaling_project`.

---

## Symbol pool (`symbols.csv`)

- **Reduced** from 60 symbols to **36 symbols** in 6 groups of 6
- **Added `group` column** — each symbol belongs to a named visual-similarity group
- Groups: `loop_greek`, `complex_greek`, `angular_caps`, `circle_ops`, `set_ops`, `logic_ops`
- On each trial, ALL symbols on the grid (target + distractors) are now drawn from the **same group**, so distractors are visually similar to the target (harder)
- Previously: distractors were drawn from the entire 60-symbol pool (easier)

---

## Task generation (`task_logic.py` / `__init__.py`)

- `_generate_matrix_task()` now picks a random group per trial and constrains the whole grid to that group
- Target is still guaranteed to appear at least once (`MATRIX_MIN_TARGETS = 1`)
- Previously: distractors were drawn from any non-target symbol across all 60

---

## Page flow changes

- **Removed `MatrixPractice`** from `page_sequence` — the 2-round unguided practice is gone
- **Extended `MatrixInstructions`** (the tutorial) with a 6th step: after the 5-step guided walkthrough, participants do one free-form demo trial on their own (target: `\beta`) before the real task begins. This replaces the removed practice page.
- **Removed the 20-second auto-advance** from `MatrixStartScreen` — participants must now manually tap "Start task". The page waits indefinitely.

---

## UI / UX changes

### Welcome page
- Rewritten to be a single concise page (~4 lines) covering: task description, session structure (condition-specific), and payment
- Previously: multi-paragraph with a bulleted list

### Tutorial (`MatrixInstructions.html`)
- Target symbol box is now **centered** (was left-aligned, `align-self: flex-start` → `align-self: center`)
- Added 6th progress dot and step 6 (free-form demo with `\beta` as target, no hints)

### Start screen (`MatrixStartScreen.html`)
- Removed the 20s countdown text ("Starts automatically in 20s") and progress bar
- Card widened from 520px to 700px
- Removed `get_timeout_seconds` override — page waits for manual tap

### Task timer (`MatrixTask.html`)
- Added a **visible session timer** at the top of the task screen (was hidden)
- Shows: session label ("Session 1 of 2", "Continue working", "Session 2 of 2") + live countdown
- Turns amber at 60s remaining, red at 30s remaining
- Timer is centered and uses bold display font

### Break choice (`BreakChoice.html`)
- Completely redesigned from a plain radio button to **two large tappable cards**
- Cards are equal height; a "Confirm my choice →" button appears only after one card is tapped
- Text updated to make consequences explicit:
  - Break: "Screen locks for X min and you **won't** be able to work and earn money during this time. After this, Session 2 will start at 2 tokens per correct trial."
  - Work: "Keep working and earning money for X min at 1 token per correct trial. After this, Session 2 will start at 2 tokens per correct trial."
- Fixed a bug where the confirm button never appeared (CSS `display:none` was not properly overridden)
- Fixed form submission: confirm button is now `type="submit"` (directly submits oTree form)

### Cursor / focus fix
- Added `user-select: none; -webkit-tap-highlight-color: transparent; outline: none; caret-color: transparent` to buttons across MatrixStartScreen, MatrixTask, MatrixInstructions, and BreakChoice — removes the blinking text cursor that appeared on Android tablets after tapping buttons

---

## Code structure

- **New file `data_loaders.py`**: all CSV loading functions and module-level data constants extracted from `__init__.py`. Pure Python, no oTree dependency.
- **New file `task_logic.py`**: task generation logic, timing helpers, condition assignment, and grid constants extracted from `__init__.py`. Pure functions, no database writes.
- **`__init__.py`** trimmed: now only contains oTree models, live-method handlers, page classes, `page_sequence`, and `custom_export`.
- **New `CLAUDE.md`**: project documentation covering file structure, conditions, payment, common edits, and deployment.
