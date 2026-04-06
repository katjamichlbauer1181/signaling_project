# signaling_project — Developer Guide

## What this project is

An oTree experiment studying break-taking behaviour in a cognitive task. Participants complete a symbol-matching task (find all matching symbols in an 8×8 grid) across two timed sessions separated by an optional break. The main experimental manipulation is whether participants can choose their break, are forced to take one, or have none.

---

## How to run locally

```bash
cd signaling_project
source venv/bin/activate
otree devserver          # http://localhost:8000/demo
```

For a second instance (e.g. running alongside another project):
```bash
otree devserver 8001
```

---

## File structure

```
signaling_project/
├── settings.py                        # Session configs (task_minutes, break_minutes, conditions)
├── symbols.csv                        # Symbol pool — edit to change available symbols
├── symbol_matrix/
│   ├── __init__.py                    # oTree entry point: models, pages, page_sequence, export
│   ├── data_loaders.py                # Loads all CSV data at startup (no oTree dependency)
│   ├── task_logic.py                  # Pure task logic: grid generation, timing, conditions
│   └── templates/symbol_matrix/
│       ├── FieldIDEntry.html          # Participant enters 3-digit field ID
│       ├── Welcome.html               # One-page overview: task + structure + pay
│       ├── Consent.html               # Informed consent checkbox
│       ├── MatrixInstructions.html    # 6-step interactive tutorial (2nd step is free-form demo)
│       ├── MatrixStartScreen.html     # "Ready to begin" reminder — participant taps Start
│       ├── MatrixTask.html            # Real task (used by Session 1, Bridge, Session 2)
│       ├── BreakChoice.html           # Two-card choice: take break vs keep working
│       ├── BreakWait.html             # Break countdown — screen locked, cannot advance early
│       ├── Demographics.html          # Post-task survey
│       └── Goodbye.html              # Payoff summary
└── _static/
    ├── images/                        # Drop JPG/PNG images here (served at /static/images/)
    └── katex/                         # KaTeX math rendering library (fully bundled, no CDN)
```

---

## The three experimental conditions

Assigned by the **first digit of the participant's 3-digit Field ID**:

| Field ID prefix | Condition | What happens |
|---|---|---|
| `1xx` | `no_break` | Work continuously (seg1 → bridge → seg2, no choice offered) |
| `2xx` | `forced_break` | Forced break between sessions (no choice offered) |
| `3xx` | `choice` | Participant chooses: take break or keep working |

---

## Payment structure

- **Show-up fee:** $3.00
- **Session 1 + bridge:** 1 token per correct trial = $0.004
- **Session 2:** 2 tokens per correct trial = $0.008
- **Formula:** `$3.00 + (seg1_correct + bridge_correct) × $0.004 + seg2_correct × $0.008`

Calculated in `Goodbye.vars_for_template()` inside `__init__.py`.

---

## Symbol pool (`symbols.csv`)

36 symbols in 6 visually-similar groups. On each trial, all symbols on the grid (target + distractors) are drawn from the **same group**, making look-alikes the default challenge.

| Group | Symbols |
|---|---|
| `loop_greek` | α ε ρ σ ω ν |
| `complex_greek` | β ζ η θ φ ψ |
| `angular_caps` | Γ Δ Λ Ξ Π Σ |
| `circle_ops` | ⊕ ⊗ ⊙ ∅ Θ Φ |
| `set_ops` | ∈ ∉ ⊂ ⊃ ∩ ∪ |
| `logic_ops` | ∀ ∃ ¬ ∧ ∨ ∂ |

To change the symbol pool: edit `symbols.csv` and restart the server. No code changes needed.

---

## Common edits and where to make them

| What to change | Where |
|---|---|
| Session duration | `settings.py` → `task_minutes`, `break_minutes` |
| Symbol pool | `symbols.csv` |
| How grids are generated | `task_logic.py` → `_generate_matrix_task()` |
| Grid size (default 8×8=64) | `task_logic.py` → `MATRIX_GRID_SIZE` **and** `MatrixTask.html` → `repeat(8, 1fr)` |
| Target count range | `task_logic.py` → `MATRIX_MIN_TARGETS`, `MATRIX_MAX_TARGETS` |
| Payment formula | `__init__.py` → `Goodbye.vars_for_template()` |
| Break choice screen text | `BreakChoice.html` |
| Tutorial steps | `MatrixInstructions.html` |
| Condition → field ID mapping | `task_logic.py` → `_get_condition()` |
| Data export columns | `__init__.py` → `custom_export()` |

---

## Field deployment (offline, laptop as server)

1. **Morning setup on MacBook:**
   ```bash
   # Share WiFi hotspot (System Settings → Sharing → Internet Sharing)
   ipconfig getifaddr bridge100          # get your hotspot IP (e.g. 192.168.2.1)
   source venv/bin/activate
   OTREE_PRODUCTION=1 OTREE_ADMIN_PASSWORD=yourpassword otree prodserver 0.0.0.0:8000
   ```
2. **Admin panel:** `http://localhost:8000/admin` → Sessions → Create → set participant count
3. **Per tablet:** connect to hotspot WiFi → Chrome → `http://192.168.2.1:8000`
4. **Data export (end of day):**
   - Trial CSV: `http://localhost:8000/api/export_app_custom?app=symbol_matrix`
   - Full CSV: `http://localhost:8000/ExportWide`
   - DB backup: copy `db.sqlite3` via USB
