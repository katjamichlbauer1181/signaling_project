# Symbol Matrix Task — oTree 6 Field Experiment

Participants see a target LaTeX symbol and must click all matching symbols in an 8×8 grid of 64. No feedback after each trial. Two timed segments separated by a break period whose structure depends on the treatment condition. Designed for offline field deployment in Kenya on Android tablets.

---

## Quick start

```bash
source venv/bin/activate
otree devserver          # dev (single user, auto-reload)
```

Open `http://localhost:8000/demo` → **Symbol Matrix Task (Demo — 3+1+3 min)** to test.

---

## Treatment conditions

Assigned by the **first digit of the participant's 3-digit Field ID**:

| Field ID | Condition | What participants experience |
|---|---|---|
| `1xx` | `no_break` | 50 min work → 40 min work (no break, never told about break) |
| `2xx` | `forced_break` | 40 min work → 10 min forced break → 40 min work |
| `3xx` | `choice` | 40 min work → choose break or continue → 40 min work |

The `xx` part uniquely identifies the participant within their condition (e.g. `101`–`199` for no-break group).

---

## Page sequence (matrix task)

```
FieldIDEntry → Welcome → Consent → MatrixInstructions (tutorial) →
MatrixPractice (2 unscored trials) → MatrixStartScreen →
MatrixTask [seg 1] → BreakChoice* → BreakWait* / MatrixBridgeTask* →
MatrixTask2 [seg 2] → Demographics → Goodbye
```

\* shown/skipped based on condition

---

## Payment

- Show-up fee: **$3.00**
- Session 1 + bridge: **1 token per correct task** = $0.004
- Session 2: **2 tokens per correct task** = $0.008
- Formula: `$3.00 + total_tokens × $0.004`

---

## Field deployment (offline, laptop as server)

**On your MacBook — morning setup (~15 min):**

1. System Settings → Sharing → Internet Sharing → share Wi-Fi → turn on. Network name e.g. `SymbolTask`.
2. Find your hotspot IP: `ipconfig getifaddr bridge100` (typically `192.168.2.1`)
3. Start the server:
   ```bash
   source venv/bin/activate
   OTREE_PRODUCTION=1 OTREE_ADMIN_PASSWORD=yourpassword otree prodserver 0.0.0.0:8000
   ```
4. Admin panel: `http://localhost:8000/admin` → Sessions → Create new session → set participant count.

**Per tablet (30 sec each):**
1. Connect to `SymbolTask` WiFi
2. Open Chrome → `http://192.168.2.1:8000/demo`
3. Bookmark it

**Participants** tap **Symbol Matrix Task (Full — 40+10+40 min)** on the demo page, or you hand them a direct participant URL from the admin panel.

**Data export (end of day):**
- Trial-level CSV: `http://localhost:8000/api/export_app_custom?app=symbol_matrix`
- Participant-level CSV: `http://localhost:8000/ExportWide`
- Raw DB: copy `db.sqlite3` via USB as a backup

---

## Data collected

**Per trial:** block, task_number, target_latex, n_targets, n_correct_clicked, n_missed, n_incorrect_clicked, is_correct, time_taken_ms, clicked_cells, correct_cells, random_seed (grid reproducible from seed)

**Per participant:** field_id, condition, consented, break_choice, seg1/bridge/seg2 task counts, payoff fields, experiment timestamps

**Demographics** (post-task): age, gender, occupation, education, income, hours_slept, breakfast

All participant-level fields repeat on every row of the trial CSV so a single `field_id` filter gives everything.

---

## Quick-change reference

| What | Where |
|---|---|
| Session duration | `settings.py` → `task_minutes`, `break_minutes` |
| Grid size (e.g. 7×7) | `__init__.py` → `MATRIX_GRID_SIZE = 49` **and** `MatrixTask.html` → `repeat(7, 1fr)` |
| Target count range | `__init__.py` → `MATRIX_MIN_TARGETS`, `MATRIX_MAX_TARGETS` |
| Symbol set | `symbols.csv` (columns: symbol_id, latex, category) — restart server after changes |
| Payoff formula | `__init__.py` → `Goodbye.vars_for_template()` |
| Condition mapping | `__init__.py` → `_get_condition()` |

---

## Project structure

```
signaling_project/
├── settings.py                        # session configs
├── symbols.csv                        # 60 LaTeX symbols
├── symbol_matrix/
│   ├── __init__.py                    # all experiment logic
│   └── templates/symbol_matrix/
│       ├── FieldIDEntry.html
│       ├── Welcome.html
│       ├── Consent.html
│       ├── MatrixInstructions.html    # 5-step interactive tutorial
│       ├── MatrixPractice.html        # 2 unscored practice trials
│       ├── MatrixStartScreen.html     # 20s auto-advance reminder
│       ├── MatrixTask.html            # real task (all 3 blocks share this)
│       ├── BreakChoice.html
│       ├── BreakWait.html
│       ├── Demographics.html
│       └── Goodbye.html
├── _static/katex/                     # KaTeX 0.16.11 fully bundled (no CDN)
└── deployment/                        # startup scripts (legacy Termux approach)
```
