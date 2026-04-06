"""
task_logic.py
Core experiment logic: timing, condition assignment, and task generation.
_generate_matrix_task() is the main function to edit when changing how grids are built.
All functions here are pure (no database writes) so they are easy to test in isolation.
"""
import random

from .data_loaders import PURE_SYMBOL_GROUPS

# Local fallback defaults (mirrors C.TASK_MINUTES_DEFAULT / C.BREAK_MINUTES_DEFAULT)
_TASK_MINUTES_DEFAULT  = 40
_BREAK_MINUTES_DEFAULT = 10

# Legacy symbol-grid constants
NUM_SYMBOL_TYPES    = 8
SYMBOL_GRID_SIZE    = 64
NUM_TARGETS_IN_GRID = 8

# Matrix task constants
MATRIX_GRID_SIZE   = 64   # 8 × 8
MATRIX_MIN_TARGETS = 1
MATRIX_MAX_TARGETS = 10


def _task_duration(player):
    return int(player.session.config.get('task_minutes',  _TASK_MINUTES_DEFAULT)  * 60)


def _break_duration(player):
    return int(player.session.config.get('break_minutes', _BREAK_MINUTES_DEFAULT) * 60)


def _get_condition(player):
    """Derive experimental condition from field_id.

    Field IDs starting with '1' → no_break   (40 + 10 work + 40, no choice)
    Field IDs starting with '2' → forced_break (40 + 10 break + 40, no choice)
    Field IDs starting with '3' → choice       (40 + choose break/work + 40)
    Any other value              → choice       (safe default)
    """
    fid = (player.field_maybe_none('field_id') or '').strip()
    if fid.startswith('1'):
        return 'no_break'
    if fid.startswith('2'):
        return 'forced_break'
    return 'choice'


def _generate_matrix_task():
    """Return a new random symbol-matrix trial.

    All symbols in a trial (target + distractors) are drawn from the same
    visual-similarity group, making confusable neighbours the default.
    Target count N is uniformly random in [MATRIX_MIN_TARGETS, MATRIX_MAX_TARGETS].
    The target is guaranteed to appear at least once.
    """
    if not PURE_SYMBOL_GROUPS:
        raise RuntimeError('symbols.csv must define at least one group with 2+ symbols.')
    seed = random.randint(0, 2**31 - 1)
    rng  = random.Random(seed)   # isolated RNG — does not affect global state
    group_symbols = rng.choice(list(PURE_SYMBOL_GROUPS.values()))
    target      = rng.choice(group_symbols)
    n_targets   = rng.randint(MATRIX_MIN_TARGETS, MATRIX_MAX_TARGETS)
    non_targets = [s for s in group_symbols if s['symbol_id'] != target['symbol_id']]
    grid = [rng.choice(non_targets) for _ in range(MATRIX_GRID_SIZE)]
    target_positions = rng.sample(range(MATRIX_GRID_SIZE), n_targets)
    for pos in target_positions:
        grid[pos] = target
    correct_cells = sorted(target_positions)
    return {
        'target':        {'id': target['symbol_id'], 'latex': target['latex']},
        'grid':          [{'id': s['symbol_id'], 'latex': s['latex']} for s in grid],
        'correct_cells': correct_cells,
        'n_targets':     n_targets,
        'seed':          seed,
    }


def _generate_symbol_grid(target_symbol):
    non_targets = [s for s in range(NUM_SYMBOL_TYPES) if s != target_symbol]
    grid = [random.choice(non_targets) for _ in range(SYMBOL_GRID_SIZE)]
    target_cells = random.sample(range(SYMBOL_GRID_SIZE), NUM_TARGETS_IN_GRID)
    for cell in target_cells:
        grid[cell] = target_symbol
    return grid, sorted(target_cells)


def _point_in_box(x, y, box):
    x1, y1, x2, y2 = box
    return x1 <= x <= x2 and y1 <= y <= y2
