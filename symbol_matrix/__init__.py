import csv
import json
import os
import random
import time

from otree.api import *

doc = """
Symbol Matrix Task experiment.

Participants complete an 8×8 symbol-matching task in two timed sessions separated
by an optional break. On each trial they see a target symbol and must select all
matching symbols from a grid of 64.  No feedback is shown — the next trial loads
immediately after confirmation.

Symbol pool is loaded from symbols.csv at the project root; swap that file at any
time (the code reads it fresh on server restart).

Session config keys:
  task_type     (str)  — 'matrix' for this experiment; legacy values still work
  task_minutes  (int)  — duration of each task segment   (default 40)
  break_minutes (int)  — duration of break / bridge      (default 10)
"""


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _load_image_data():
    csv_path = os.path.join(os.path.dirname(__file__), 'images_data.csv')
    if not os.path.exists(csv_path):
        return []
    images = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            images.append({'filename': row['filename'].strip(),
                           'question':  row['question'].strip()})
    return images


def _load_captcha_data():
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'images_data_captcha.csv')
    if not os.path.exists(csv_path):
        return []
    images = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            images.append({
                'filename':      row['filename'].strip(),
                'question':      row['question'].strip(),
                'target_object': row.get('target_object', '').strip(),
                'correct_cells': row.get('correct_cells', '[]').strip(),
            })
    return images


def _load_ordered_data():
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'images_data_ordered.csv')
    if not os.path.exists(csv_path):
        return []
    images = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            images.append({
                'filename': row['filename'].strip(),
                'question': row['question'].strip(),
                'targets':  row.get('targets', '[]').strip(),
            })
    return images


def _load_symbol_data():
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'images_data_symbol.csv')
    if not os.path.exists(csv_path):
        return []
    images = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            images.append({
                'filename':       row['filename'].strip(),
                'question':       row['question'].strip(),
                'answer_options': row.get('answer_options', '[]').strip(),
                'correct_answer': row.get('correct_answer', '').strip(),
            })
    return images


def _load_pure_symbols():
    """Load the symbol database from symbols.csv at the project root.

    Required columns: symbol_id (int), latex (str), category (str)
    Add, remove, or swap rows in that file; restart the server to apply changes.
    Falls back to 8 Greek letters if the file is missing (dev convenience only).
    """
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'symbols.csv')
    if not os.path.exists(csv_path):
        fallback = [
            (1, r'\alpha'), (2, r'\beta'),   (3, r'\gamma'), (4, r'\delta'),
            (5, r'\epsilon'),(6, r'\zeta'), (7, r'\eta'),   (8, r'\theta'),
        ]
        return [{'symbol_id': sid, 'latex': latex, 'category': 'fallback'}
                for sid, latex in fallback]
    symbols = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            symbols.append({
                'symbol_id': int(row['symbol_id']),
                'latex':     row['latex'].strip(),
                'category':  row.get('category', '').strip(),
            })
    return symbols


IMAGE_DATA       = _load_image_data()
CAPTCHA_DATA     = _load_captcha_data()
ORDERED_DATA     = _load_ordered_data()
SYMBOL_DATA      = _load_symbol_data()
PURE_SYMBOL_DATA = _load_pure_symbols()

# Legacy symbol-grid constants
NUM_SYMBOL_TYPES    = 8
SYMBOL_GRID_SIZE    = 64
NUM_TARGETS_IN_GRID = 8

# Matrix task constants
MATRIX_GRID_SIZE   = 64   # 8 × 8
MATRIX_MIN_TARGETS = 1
MATRIX_MAX_TARGETS = 10


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

class C(BaseConstants):
    NAME_IN_URL       = 'task'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS        = 1

    TASK_MINUTES_DEFAULT  = 40
    BREAK_MINUTES_DEFAULT = 10

    TRAINING_IMAGE    = 'training_example.svg'
    TRAINING_QUESTION = (
        'This is a practice trial to familiarise you with the task. '
        'Describe what you see in this image in one or two sentences. '
        'Your answer here will not be recorded.'
    )


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class Subsession(BaseSubsession):
    def creating_session(self):
        for player in self.get_players():
            order = list(range(len(IMAGE_DATA)))
            random.shuffle(order)
            player.image_order = json.dumps(order)

            captcha_order = list(range(len(CAPTCHA_DATA)))
            random.shuffle(captcha_order)
            player.captcha_image_order = json.dumps(captcha_order)

            ordered_order = list(range(len(ORDERED_DATA)))
            random.shuffle(ordered_order)
            player.ordered_image_order = json.dumps(ordered_order)

            symbol_order = list(range(len(SYMBOL_DATA)))
            random.shuffle(symbol_order)
            player.symbol_image_order = json.dumps(symbol_order)


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    # ----- Legacy image task -----
    image_order         = models.LongStringField(initial='[]')
    current_image_index = models.IntegerField(initial=0)

    break_choice = models.BooleanField(
        label='Would you like to take a break before the second session?',
        choices=[
            [True,  'Yes, I would like to take a break'],
            [False, 'No, I will continue working'],
        ],
        widget=widgets.RadioSelect,
    )

    training_answer = models.LongStringField(label='Your answer (practice)', blank=True)

    # ----- Legacy CAPTCHA task -----
    captcha_image_order   = models.LongStringField(initial='[]')
    current_captcha_index = models.IntegerField(initial=0)

    # ----- Legacy ordered-selection task -----
    ordered_image_order   = models.LongStringField(initial='[]')
    current_ordered_index = models.IntegerField(initial=0)

    # ----- Legacy symbol+image task -----
    symbol_image_order      = models.LongStringField(initial='[]')
    current_symbol_index    = models.IntegerField(initial=0)
    symbol_current_attempts = models.IntegerField(initial=0)

    # ----- Matrix (pure symbol) task — internal state -----
    matrix_task_number = models.IntegerField(initial=0)
    # Server stores the current trial's ground truth so the client cannot manipulate it
    matrix_current_correct_cells = models.LongStringField(initial='[]')
    matrix_current_target_id     = models.IntegerField(initial=0)
    matrix_current_n_targets     = models.IntegerField(initial=0)
    matrix_current_seed          = models.IntegerField(initial=0)

    # ----- Matrix — segment-level summaries (incremented per answer) -----
    seg1_tasks_attempted   = models.IntegerField(initial=0)
    seg1_tasks_correct     = models.IntegerField(initial=0)
    bridge_tasks_attempted = models.IntegerField(initial=0)   # no-break period only
    bridge_tasks_correct   = models.IntegerField(initial=0)
    seg2_tasks_attempted   = models.IntegerField(initial=0)
    seg2_tasks_correct     = models.IntegerField(initial=0)

    # ----- Matrix — experiment-wide totals (computed at Goodbye) -----
    total_tasks_attempted = models.IntegerField(initial=0)
    total_tasks_correct   = models.IntegerField(initial=0)

    # ----- Payoff (computed at Goodbye) -----
    # 1 credit per correct task in seg1 + bridge; 2 credits per correct task in seg2
    payoff_seg1_bridge_credits = models.IntegerField(initial=0)
    payoff_seg2_credits        = models.IntegerField(initial=0)
    # $3 show-up fee + $0.01 per credit
    final_payoff_dollars = models.FloatField(initial=0.0)

    # ----- Field ID (entered by participant at check-in) -----
    field_id = models.StringField(label='Field ID')

    # ----- Condition (derived from field_id, stored for export) -----
    # 'no_break'     — forced continuous work (seg1 + bridge + seg2)
    # 'forced_break' — forced break between seg1 and seg2
    # 'choice'       — participant chooses whether to take a break
    condition = models.StringField(initial='')

    # ----- Consent -----
    consented = models.BooleanField(
        label='I have read and understood the information above and I agree to participate.',
        widget=widgets.CheckboxInput,
        initial=False,
    )

    # ----- Demographics -----
    demo_age = models.IntegerField(
        label='What is your age (in years)?',
        choices=list(range(15, 86)),
    )
    demo_gender = models.StringField(
        label='What is your gender?',
        choices=['Male', 'Female', 'Non-binary / gender diverse', 'Prefer not to say'],
    )
    demo_occupation = models.LongStringField(
        label='What is your current occupation? (e.g. farmer, teacher, student, trader)',
    )
    demo_education = models.StringField(
        label='What is the highest level of education you have completed?',
        choices=[
            'No formal schooling',
            'Primary school (completed)',
            'Secondary school (completed)',
            'Vocational / technical training',
            'Some university or college (not completed)',
            "University degree (Bachelor's or equivalent)",
            "Postgraduate degree (Master's or PhD)",
        ],
    )
    demo_income = models.StringField(
        label='What is your approximate monthly household income?',
        choices=[
            'Less than KES 5,000',
            'KES 5,000 – 14,999',
            'KES 15,000 – 29,999',
            'KES 30,000 – 59,999',
            'KES 60,000 – 99,999',
            'KES 100,000 or more',
            'Prefer not to say',
        ],
    )
    demo_hours_slept = models.IntegerField(
        label='How many hours did you sleep last night?',
        choices=list(range(0, 13)),
    )
    demo_breakfast = models.LongStringField(
        label='What did you have for breakfast today? (write "nothing" if you skipped it)',
        blank=True,
    )

    # ----- Timestamps -----
    captcha_start_time   = models.FloatField(null=True)
    captcha2_start_time  = models.FloatField(null=True)
    ordered_start_time   = models.FloatField(null=True)
    ordered2_start_time  = models.FloatField(null=True)
    symbol_start_time    = models.FloatField(null=True)
    symbol2_start_time   = models.FloatField(null=True)
    combined_start_time  = models.FloatField(null=True)
    combined2_start_time = models.FloatField(null=True)
    matrix_start_time    = models.FloatField(null=True)
    matrix2_start_time   = models.FloatField(null=True)
    experiment_end_time  = models.FloatField(null=True)  # set when Goodbye page loads


# ---------------------------------------------------------------------------
# Extra models
# ---------------------------------------------------------------------------

class Answer(ExtraModel):
    player           = models.Link(Player)
    block            = models.IntegerField()
    image_index      = models.IntegerField()
    image_filename   = models.StringField()
    question         = models.StringField()
    answer_text      = models.LongStringField()
    response_time_ms = models.FloatField()
    timestamp        = models.FloatField()


class CaptchaAnswer(ExtraModel):
    player           = models.Link(Player)
    image_index      = models.IntegerField()
    image_filename   = models.StringField()
    target_object    = models.StringField()
    question         = models.StringField()
    selected_cells   = models.LongStringField()
    correct_cells    = models.LongStringField()
    is_correct       = models.BooleanField()
    response_time_ms = models.FloatField()
    timestamp        = models.FloatField()


class OrderedAnswer(ExtraModel):
    player           = models.Link(Player)
    image_index      = models.IntegerField()
    image_filename   = models.StringField()
    question         = models.StringField()
    click_sequence   = models.LongStringField()
    targets_json     = models.LongStringField()
    is_correct       = models.BooleanField()
    response_time_ms = models.FloatField()
    timestamp        = models.FloatField()


class SymbolAnswer(ExtraModel):
    player             = models.Link(Player)
    image_index        = models.IntegerField()
    image_filename     = models.StringField()
    question           = models.StringField()
    attempt_number     = models.IntegerField()
    target_symbol      = models.IntegerField()
    target_cells       = models.LongStringField()
    clicked_cells      = models.LongStringField()
    symbol_correct     = models.BooleanField()
    symbol_time_ms     = models.FloatField()
    answer_options     = models.LongStringField()
    correct_answer     = models.StringField()
    participant_answer = models.StringField()
    answer_correct     = models.BooleanField()
    response_time_ms   = models.FloatField()
    timestamp          = models.FloatField()


class MatrixAnswer(ExtraModel):
    """One row per symbol-matrix trial.

    block:              1 = segment 1, 2 = bridge (no-break), 3 = segment 2
    n_targets:          correct symbols that existed in the grid
    n_correct_clicked:  true positives  (clicked ∩ correct)
    n_missed:           false negatives (correct − clicked)
    n_incorrect_clicked:false positives (clicked − correct)
    n_errors:           n_missed + n_incorrect_clicked  (symmetric difference)
    """
    player              = models.Link(Player)
    block               = models.IntegerField()
    task_number         = models.IntegerField()
    target_symbol_id    = models.IntegerField()
    target_latex        = models.StringField()
    n_targets           = models.IntegerField()
    n_correct_clicked   = models.IntegerField()
    n_missed            = models.IntegerField()
    n_incorrect_clicked = models.IntegerField()
    n_errors            = models.IntegerField()
    random_seed         = models.IntegerField()      # seed to reproduce this exact grid
    clicked_cells       = models.LongStringField()  # JSON sorted list of ints
    correct_cells       = models.LongStringField()  # JSON sorted list of ints
    is_correct          = models.BooleanField()
    time_taken_ms       = models.FloatField()
    timestamp           = models.FloatField()


# ---------------------------------------------------------------------------
# Helpers — timing
# ---------------------------------------------------------------------------

def _task_duration(player):
    return int(player.session.config.get('task_minutes',  C.TASK_MINUTES_DEFAULT)  * 60)


def _break_duration(player):
    return int(player.session.config.get('break_minutes', C.BREAK_MINUTES_DEFAULT) * 60)


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


# ---------------------------------------------------------------------------
# Helpers — legacy image task
# ---------------------------------------------------------------------------

def _get_image_payload(player):
    if player.field_maybe_none('image_order') is None:
        order = list(range(len(IMAGE_DATA)))
        random.shuffle(order)
        player.image_order = json.dumps(order)
    order = json.loads(player.image_order)
    idx = player.current_image_index
    if idx >= len(order) or not IMAGE_DATA:
        return None
    img = IMAGE_DATA[order[idx]]
    return {'filename': img['filename'], 'question': img['question'],
            'index': idx, 'total': len(order)}


def _task_live_method(player, data, block):
    if data.get('type') == 'request_image':
        payload = _get_image_payload(player)
        if payload:
            return {player.id_in_group: {'type': 'image', **payload}}
        return {player.id_in_group: {'type': 'pool_exhausted'}}
    if data.get('type') == 'submit_answer':
        order = json.loads(player.image_order)
        idx   = player.current_image_index
        img   = IMAGE_DATA[order[idx]] if idx < len(order) else {}
        Answer.create(
            player=player, block=block, image_index=idx,
            image_filename=img.get('filename', ''), question=img.get('question', ''),
            answer_text=data.get('answer', ''),
            response_time_ms=data.get('response_time_ms', 0), timestamp=time.time(),
        )
        player.current_image_index += 1
        payload = _get_image_payload(player)
        if payload:
            return {player.id_in_group: {'type': 'image', **payload}}
        return {player.id_in_group: {'type': 'pool_exhausted'}}
    return {}


# ---------------------------------------------------------------------------
# Helpers — CAPTCHA task
# ---------------------------------------------------------------------------

def _get_captcha_payload(player):
    if player.field_maybe_none('captcha_image_order') is None:
        order = list(range(len(CAPTCHA_DATA)))
        random.shuffle(order)
        player.captcha_image_order = json.dumps(order)
    order = json.loads(player.captcha_image_order)
    idx = player.current_captcha_index
    if idx >= len(order) or not CAPTCHA_DATA:
        return None
    img = CAPTCHA_DATA[order[idx]]
    return {
        'filename': img['filename'], 'question': img['question'],
        'target_object': img['target_object'],
        'correct_cells': json.loads(img['correct_cells']),
        'index': idx, 'total': len(order),
    }


def _captcha_live_method(player, data):
    if data.get('type') != 'submit_answer':
        return {}
    selected = sorted(data.get('selected_cells', []))
    order  = json.loads(player.captcha_image_order)
    idx    = player.current_captcha_index
    img    = CAPTCHA_DATA[order[idx]] if idx < len(order) else {}
    correct = sorted(json.loads(img.get('correct_cells', '[]')))
    is_correct = (selected == correct)
    CaptchaAnswer.create(
        player=player, image_index=idx,
        image_filename=img.get('filename', ''), target_object=img.get('target_object', ''),
        question=img.get('question', ''), selected_cells=json.dumps(selected),
        correct_cells=img.get('correct_cells', '[]'), is_correct=is_correct,
        response_time_ms=data.get('response_time_ms', 0), timestamp=time.time(),
    )
    player.current_captcha_index += 1
    next_payload = _get_captcha_payload(player)
    return {player.id_in_group: {
        'type': 'feedback', 'is_correct': is_correct,
        'correct_cells': correct, 'next_image': next_payload,
    }}


# ---------------------------------------------------------------------------
# Helpers — ordered-selection task
# ---------------------------------------------------------------------------

def _point_in_box(x, y, box):
    x1, y1, x2, y2 = box
    return x1 <= x <= x2 and y1 <= y <= y2


def _get_ordered_payload(player):
    if player.field_maybe_none('ordered_image_order') is None:
        order = list(range(len(ORDERED_DATA)))
        random.shuffle(order)
        player.ordered_image_order = json.dumps(order)
    order = json.loads(player.ordered_image_order)
    idx = player.current_ordered_index
    if idx >= len(order) or not ORDERED_DATA:
        return None
    img = ORDERED_DATA[order[idx]]
    targets = json.loads(img['targets'])
    return {
        'filename': img['filename'], 'question': img['question'],
        'num_targets': len(targets), 'index': idx, 'total': len(order),
    }


def _ordered_live_method(player, data):
    if data.get('type') != 'submit_answer':
        return {}
    clicks  = data.get('click_sequence', [])
    order   = json.loads(player.ordered_image_order)
    idx     = player.current_ordered_index
    img     = ORDERED_DATA[order[idx]] if idx < len(order) else {}
    targets = json.loads(img.get('targets', '[]'))
    is_correct = (
        len(clicks) == len(targets) and
        all(_point_in_box(c['x'], c['y'], t['box']) for c, t in zip(clicks, targets))
    )
    OrderedAnswer.create(
        player=player, image_index=idx,
        image_filename=img.get('filename', ''), question=img.get('question', ''),
        click_sequence=json.dumps(clicks), targets_json=img.get('targets', '[]'),
        is_correct=is_correct,
        response_time_ms=data.get('response_time_ms', 0), timestamp=time.time(),
    )
    player.current_ordered_index += 1
    next_payload = _get_ordered_payload(player)
    return {player.id_in_group: {
        'type': 'feedback', 'is_correct': is_correct,
        'targets': targets, 'next_image': next_payload,
    }}


# ---------------------------------------------------------------------------
# Helpers — legacy symbol+image task
# ---------------------------------------------------------------------------

def _generate_symbol_grid(target_symbol):
    non_targets = [s for s in range(NUM_SYMBOL_TYPES) if s != target_symbol]
    grid = [random.choice(non_targets) for _ in range(SYMBOL_GRID_SIZE)]
    target_cells = random.sample(range(SYMBOL_GRID_SIZE), NUM_TARGETS_IN_GRID)
    for cell in target_cells:
        grid[cell] = target_symbol
    return grid, sorted(target_cells)


def _get_symbol_payload(player):
    if player.field_maybe_none('symbol_image_order') is None:
        order = list(range(len(SYMBOL_DATA)))
        random.shuffle(order)
        player.symbol_image_order = json.dumps(order)
    order = json.loads(player.symbol_image_order)
    idx = player.current_symbol_index
    if idx >= len(order) or not SYMBOL_DATA:
        return None
    img = SYMBOL_DATA[order[idx]]
    target_symbol = random.randint(0, NUM_SYMBOL_TYPES - 1)
    grid, target_cells = _generate_symbol_grid(target_symbol)
    return {
        'filename': img['filename'], 'question': img['question'],
        'answer_options': json.loads(img['answer_options']),
        'target_symbol': target_symbol, 'symbol_grid': grid,
        'target_cells': target_cells, 'index': idx, 'total': len(order),
    }


def _symbol_live_method(player, data):
    if data.get('type') != 'submit_answer':
        return {}
    clicked      = sorted(data.get('clicked_cells', []))
    target_cells = sorted(data.get('target_cells', []))
    symbol_correct = (clicked == target_cells)
    order = json.loads(player.symbol_image_order)
    idx   = player.current_symbol_index
    img   = SYMBOL_DATA[order[idx]] if idx < len(order) else {}
    participant_answer = data.get('answer', '')
    answer_correct = (participant_answer == img.get('correct_answer', ''))
    attempt_number = player.symbol_current_attempts + 1
    SymbolAnswer.create(
        player=player, image_index=idx,
        image_filename=img.get('filename', ''), question=img.get('question', ''),
        attempt_number=attempt_number, target_symbol=data.get('target_symbol', 0),
        target_cells=json.dumps(target_cells), clicked_cells=json.dumps(clicked),
        symbol_correct=symbol_correct, symbol_time_ms=data.get('symbol_time_ms', 0),
        answer_options=img.get('answer_options', '[]'),
        correct_answer=img.get('correct_answer', ''),
        participant_answer=participant_answer, answer_correct=answer_correct,
        response_time_ms=data.get('response_time_ms', 0), timestamp=time.time(),
    )
    if answer_correct:
        player.current_symbol_index    += 1
        player.symbol_current_attempts  = 0
        next_payload = _get_symbol_payload(player)
        return {player.id_in_group: {'type': 'feedback', 'next_image': next_payload}}
    else:
        player.symbol_current_attempts += 1
        same_payload = _get_symbol_payload(player)
        return {player.id_in_group: {'type': 'retry', 'same_image': same_payload}}


# ---------------------------------------------------------------------------
# Helpers — combined task
# ---------------------------------------------------------------------------

def _get_combined_payload(player):
    captcha = _get_captcha_payload(player)
    if captcha is not None:
        return dict(task_mode='captcha', **captcha)
    ordered = _get_ordered_payload(player)
    if ordered is not None:
        return dict(task_mode='ordered', **ordered)
    symbol = _get_symbol_payload(player)
    if symbol is not None:
        return dict(task_mode='symbol', **symbol)
    return None


def _combined_live_method(player, data):
    task_mode = data.get('task_mode')
    if task_mode == 'captcha':
        if data.get('type') != 'submit_answer':
            return {}
        selected = sorted(data.get('selected_cells', []))
        order  = json.loads(player.captcha_image_order)
        idx    = player.current_captcha_index
        img    = CAPTCHA_DATA[order[idx]] if idx < len(order) else {}
        correct = sorted(json.loads(img.get('correct_cells', '[]')))
        is_correct = (selected == correct)
        CaptchaAnswer.create(
            player=player, image_index=idx,
            image_filename=img.get('filename', ''), target_object=img.get('target_object', ''),
            question=img.get('question', ''), selected_cells=json.dumps(selected),
            correct_cells=img.get('correct_cells', '[]'), is_correct=is_correct,
            response_time_ms=data.get('response_time_ms', 0), timestamp=time.time(),
        )
        player.current_captcha_index += 1
        next_payload = _get_combined_payload(player)
        return {player.id_in_group: {'type': 'feedback', 'task_mode': 'captcha',
                                      'is_correct': is_correct, 'correct_cells': correct,
                                      'next_image': next_payload}}
    if task_mode == 'ordered':
        if data.get('type') != 'submit_answer':
            return {}
        clicks  = data.get('click_sequence', [])
        order   = json.loads(player.ordered_image_order)
        idx     = player.current_ordered_index
        img     = ORDERED_DATA[order[idx]] if idx < len(order) else {}
        targets = json.loads(img.get('targets', '[]'))
        is_correct = (
            len(clicks) == len(targets) and
            all(_point_in_box(c['x'], c['y'], t['box']) for c, t in zip(clicks, targets))
        )
        OrderedAnswer.create(
            player=player, image_index=idx,
            image_filename=img.get('filename', ''), question=img.get('question', ''),
            click_sequence=json.dumps(clicks), targets_json=img.get('targets', '[]'),
            is_correct=is_correct,
            response_time_ms=data.get('response_time_ms', 0), timestamp=time.time(),
        )
        player.current_ordered_index += 1
        next_payload = _get_combined_payload(player)
        return {player.id_in_group: {'type': 'feedback', 'task_mode': 'ordered',
                                      'is_correct': is_correct, 'targets': targets,
                                      'next_image': next_payload}}
    if task_mode == 'symbol':
        if data.get('type') != 'submit_answer':
            return {}
        clicked      = sorted(data.get('clicked_cells', []))
        target_cells = sorted(data.get('target_cells', []))
        symbol_correct = (clicked == target_cells)
        order  = json.loads(player.symbol_image_order)
        idx    = player.current_symbol_index
        img    = SYMBOL_DATA[order[idx]] if idx < len(order) else {}
        participant_answer = data.get('answer', '')
        answer_correct = (participant_answer == img.get('correct_answer', ''))
        attempt_number = player.symbol_current_attempts + 1
        SymbolAnswer.create(
            player=player, image_index=idx,
            image_filename=img.get('filename', ''), question=img.get('question', ''),
            attempt_number=attempt_number, target_symbol=data.get('target_symbol', 0),
            target_cells=json.dumps(target_cells), clicked_cells=json.dumps(clicked),
            symbol_correct=symbol_correct, symbol_time_ms=data.get('symbol_time_ms', 0),
            answer_options=img.get('answer_options', '[]'),
            correct_answer=img.get('correct_answer', ''),
            participant_answer=participant_answer, answer_correct=answer_correct,
            response_time_ms=data.get('response_time_ms', 0), timestamp=time.time(),
        )
        if answer_correct:
            player.current_symbol_index    += 1
            player.symbol_current_attempts  = 0
            next_payload = _get_combined_payload(player)
            return {player.id_in_group: {'type': 'feedback', 'task_mode': 'symbol',
                                          'next_image': next_payload}}
        else:
            player.symbol_current_attempts += 1
            same_payload = _get_symbol_payload(player)
            return {player.id_in_group: {'type': 'retry', 'task_mode': 'symbol',
                                          'same_image': same_payload}}
    return {}


# ---------------------------------------------------------------------------
# Helpers — matrix (pure symbol) task
# ---------------------------------------------------------------------------

def _generate_matrix_task():
    """Return a new random symbol-matrix trial drawn from PURE_SYMBOL_DATA.

    Target count N is uniformly random in [MATRIX_MIN_TARGETS, MATRIX_MAX_TARGETS].
    Distractor cells are filled with replacement from non-target symbols so the
    same distractor can appear multiple times in one grid.
    """
    if len(PURE_SYMBOL_DATA) < 2:
        raise RuntimeError('symbols.csv must have at least 2 rows.')
    seed = random.randint(0, 2**31 - 1)
    rng  = random.Random(seed)   # isolated RNG — does not affect global state
    target      = rng.choice(PURE_SYMBOL_DATA)
    n_targets   = rng.randint(MATRIX_MIN_TARGETS, MATRIX_MAX_TARGETS)
    non_targets = [s for s in PURE_SYMBOL_DATA if s['symbol_id'] != target['symbol_id']]
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


def _matrix_live_method(player, data, block):
    msg_type = data.get('type')

    if msg_type == 'request_task':
        task = _generate_matrix_task()
        player.matrix_current_correct_cells = json.dumps(task['correct_cells'])
        player.matrix_current_target_id     = task['target']['id']
        player.matrix_current_n_targets     = task['n_targets']
        player.matrix_current_seed          = task['seed']
        return {player.id_in_group: {'type': 'task', 'task': task}}

    if msg_type == 'submit_answer':
        clicked     = sorted(data.get('clicked_cells', []))
        correct     = sorted(json.loads(player.matrix_current_correct_cells))
        clicked_set = set(clicked)
        correct_set = set(correct)

        is_correct          = (clicked == correct)
        n_correct_clicked   = len(clicked_set & correct_set)
        n_missed            = len(correct_set - clicked_set)
        n_incorrect_clicked = len(clicked_set - correct_set)
        n_errors            = n_missed + n_incorrect_clicked

        player.matrix_task_number += 1

        # Update segment-level counters
        if block == 1:
            player.seg1_tasks_attempted += 1
            if is_correct:
                player.seg1_tasks_correct += 1
        elif block == 2:
            player.bridge_tasks_attempted += 1
            if is_correct:
                player.bridge_tasks_correct += 1
        elif block == 3:
            player.seg2_tasks_attempted += 1
            if is_correct:
                player.seg2_tasks_correct += 1

        MatrixAnswer.create(
            player=player,
            block=block,
            task_number=player.matrix_task_number,
            target_symbol_id=player.matrix_current_target_id,
            target_latex=data.get('target_latex', ''),
            n_targets=player.matrix_current_n_targets,
            random_seed=player.matrix_current_seed,
            n_correct_clicked=n_correct_clicked,
            n_missed=n_missed,
            n_incorrect_clicked=n_incorrect_clicked,
            n_errors=n_errors,
            clicked_cells=json.dumps(clicked),
            correct_cells=player.matrix_current_correct_cells,
            is_correct=is_correct,
            time_taken_ms=data.get('time_taken_ms', 0),
            timestamp=time.time(),
        )

        # Generate next task and store ground truth immediately (no feedback to client)
        task = _generate_matrix_task()
        player.matrix_current_correct_cells = json.dumps(task['correct_cells'])
        player.matrix_current_target_id     = task['target']['id']
        player.matrix_current_n_targets     = task['n_targets']
        player.matrix_current_seed          = task['seed']
        return {player.id_in_group: {'type': 'next_task', 'task': task}}

    return {}


# ---------------------------------------------------------------------------
# Custom data export
# ---------------------------------------------------------------------------

def custom_export(players):
    """Export one row per MatrixAnswer trial (visible in oTree's Data tab → Custom export).

    Columns mirror the fields researchers care about; internal state fields are omitted.
    """
    yield [
        # Participant identifiers
        'participant_code',
        'participant_id_in_session',
        'session_code',
        'time_started_utc',
        'experiment_end_time',
        # Field ID & condition
        'field_id',
        'condition',
        # Config
        'task_type',
        'task_minutes',
        'break_minutes',
        # Consent & break decision
        'consented',
        'break_choice',
        # Demographics
        'demo_age',
        'demo_gender',
        'demo_occupation',
        'demo_education',
        'demo_income',
        'demo_hours_slept',
        'demo_breakfast',
        # Per-trial fields
        'block',
        'task_number',
        'target_symbol_id',
        'target_latex',
        'n_targets',
        'random_seed',
        'n_correct_clicked',
        'n_missed',
        'n_incorrect_clicked',
        'n_errors',
        'is_correct',
        'time_taken_ms',
        'timestamp',
        'clicked_cells',
        'correct_cells',
    ]
    for player in players:
        participant = player.participant
        session     = player.session
        for ans in MatrixAnswer.filter(player=player):
            yield [
                participant.code,
                participant.id_in_session,
                session.code,
                participant.time_started_utc,
                player.field_maybe_none('experiment_end_time'),
                player.field_maybe_none('field_id'),
                player.field_maybe_none('condition'),
                session.config.get('task_type', ''),
                session.config.get('task_minutes', ''),
                session.config.get('break_minutes', ''),
                player.field_maybe_none('consented'),
                player.field_maybe_none('break_choice'),
                player.field_maybe_none('demo_age'),
                player.field_maybe_none('demo_gender'),
                player.field_maybe_none('demo_occupation'),
                player.field_maybe_none('demo_education'),
                player.field_maybe_none('demo_income'),
                player.field_maybe_none('demo_hours_slept'),
                player.field_maybe_none('demo_breakfast'),
                ans.block,
                ans.task_number,
                ans.target_symbol_id,
                ans.target_latex,
                ans.n_targets,
                ans.random_seed,
                ans.n_correct_clicked,
                ans.n_missed,
                ans.n_incorrect_clicked,
                ans.n_errors,
                ans.is_correct,
                ans.time_taken_ms,
                ans.timestamp,
                ans.clicked_cells,
                ans.correct_cells,
            ]


# ---------------------------------------------------------------------------
# Pages — shared / legacy
# ---------------------------------------------------------------------------

class Welcome(Page):
    @staticmethod
    def vars_for_template(player):
        return {
            'task_minutes':  player.session.config.get('task_minutes',  C.TASK_MINUTES_DEFAULT),
            'break_minutes': player.session.config.get('break_minutes', C.BREAK_MINUTES_DEFAULT),
            'task_type':     player.session.config.get('task_type', ''),
            'condition':     player.field_maybe_none('condition') or 'choice',
        }


class Instructions(Page):
    @staticmethod
    def is_displayed(player):
        return player.session.config.get('task_type', '') != 'matrix'


class TrainingExample(Page):
    form_model  = 'player'
    form_fields = ['training_answer']

    @staticmethod
    def is_displayed(player):
        return player.session.config.get('task_type', '') != 'matrix'

    @staticmethod
    def vars_for_template(player):
        return {'training_image': C.TRAINING_IMAGE, 'training_question': C.TRAINING_QUESTION}


class Task1(Page):
    template_name = 'symbol_matrix/TaskPage.html'

    @staticmethod
    def is_displayed(player):
        return player.session.config.get('task_type', '') not in (
            'captcha', 'ordered', 'symbol', 'combined', 'matrix')

    @staticmethod
    def get_timeout_seconds(player):
        return _task_duration(player)

    @staticmethod
    def js_vars(player):
        return dict(first_image=_get_image_payload(player) or {})

    @staticmethod
    def vars_for_template(player):
        return {'duration_seconds': _task_duration(player), 'block_label': 'Session 1 of 2'}

    @staticmethod
    def live_method(player, data):
        return _task_live_method(player, data, block=1)


class BreakChoice(Page):
    form_model  = 'player'
    form_fields = ['break_choice']

    @staticmethod
    def is_displayed(player):
        return (player.session.config.get('task_type') == 'matrix'
                and _get_condition(player) == 'choice')

    @staticmethod
    def vars_for_template(player):
        return {
            'task_minutes':  player.session.config.get('task_minutes',  C.TASK_MINUTES_DEFAULT),
            'break_minutes': player.session.config.get('break_minutes', C.BREAK_MINUTES_DEFAULT),
        }


class BreakWait(Page):
    @staticmethod
    def is_displayed(player):
        return player.field_maybe_none('break_choice') == True

    @staticmethod
    def get_timeout_seconds(player):
        return _break_duration(player)

    @staticmethod
    def vars_for_template(player):
        return {'duration_seconds': _break_duration(player)}


class BridgeTask(Page):
    """Legacy: continue free-text task during break period (no-break path)."""
    template_name = 'symbol_matrix/TaskPage.html'

    @staticmethod
    def is_displayed(player):
        task_type = player.session.config.get('task_type', '')
        return (task_type not in ('captcha', 'ordered', 'symbol', 'combined', 'matrix')
                and player.field_maybe_none('break_choice') == False)

    @staticmethod
    def get_timeout_seconds(player):
        return _break_duration(player)

    @staticmethod
    def js_vars(player):
        return dict(first_image=_get_image_payload(player) or {})

    @staticmethod
    def vars_for_template(player):
        return {'duration_seconds': _break_duration(player),
                'block_label': 'Session 1 of 2 (continuing through break)'}

    @staticmethod
    def live_method(player, data):
        return _task_live_method(player, data, block=2)


class Task2(Page):
    template_name = 'symbol_matrix/TaskPage.html'

    @staticmethod
    def is_displayed(player):
        return player.session.config.get('task_type', '') not in (
            'captcha', 'ordered', 'symbol', 'combined', 'matrix')

    @staticmethod
    def get_timeout_seconds(player):
        return _task_duration(player)

    @staticmethod
    def js_vars(player):
        return dict(first_image=_get_image_payload(player) or {})

    @staticmethod
    def vars_for_template(player):
        return {'duration_seconds': _task_duration(player), 'block_label': 'Session 2 of 2'}

    @staticmethod
    def live_method(player, data):
        return _task_live_method(player, data, block=3)


class CaptchaTask(Page):
    @staticmethod
    def is_displayed(player):
        return player.session.config.get('task_type') == 'captcha'

    @staticmethod
    def get_timeout_seconds(player):
        return _task_duration(player)

    @staticmethod
    def js_vars(player):
        return dict(first_image=_get_captcha_payload(player) or {})

    @staticmethod
    def vars_for_template(player):
        player.captcha_start_time = time.time()
        return {'duration_seconds': _task_duration(player)}

    @staticmethod
    def live_method(player, data):
        return _captcha_live_method(player, data)


class CaptchaTask2(Page):
    template_name = 'symbol_matrix/CaptchaTask.html'

    @staticmethod
    def is_displayed(player):
        return player.session.config.get('task_type') == 'captcha'

    @staticmethod
    def get_timeout_seconds(player):
        return _task_duration(player)

    @staticmethod
    def js_vars(player):
        return dict(first_image=_get_captcha_payload(player) or {})

    @staticmethod
    def vars_for_template(player):
        player.captcha2_start_time = time.time()
        return {'duration_seconds': _task_duration(player)}

    @staticmethod
    def live_method(player, data):
        return _captcha_live_method(player, data)


class OrderedTask(Page):
    @staticmethod
    def is_displayed(player):
        return player.session.config.get('task_type') == 'ordered'

    @staticmethod
    def get_timeout_seconds(player):
        return _task_duration(player)

    @staticmethod
    def js_vars(player):
        return dict(first_image=_get_ordered_payload(player) or {})

    @staticmethod
    def vars_for_template(player):
        player.ordered_start_time = time.time()
        return {'duration_seconds': _task_duration(player)}

    @staticmethod
    def live_method(player, data):
        return _ordered_live_method(player, data)


class OrderedTask2(Page):
    template_name = 'symbol_matrix/OrderedTask.html'

    @staticmethod
    def is_displayed(player):
        return player.session.config.get('task_type') == 'ordered'

    @staticmethod
    def get_timeout_seconds(player):
        return _task_duration(player)

    @staticmethod
    def js_vars(player):
        return dict(first_image=_get_ordered_payload(player) or {})

    @staticmethod
    def vars_for_template(player):
        player.ordered2_start_time = time.time()
        return {'duration_seconds': _task_duration(player)}

    @staticmethod
    def live_method(player, data):
        return _ordered_live_method(player, data)


class SymbolTask(Page):
    @staticmethod
    def is_displayed(player):
        return player.session.config.get('task_type') == 'symbol'

    @staticmethod
    def get_timeout_seconds(player):
        return _task_duration(player)

    @staticmethod
    def js_vars(player):
        return dict(first_image=_get_symbol_payload(player) or {}, viewing_seconds=8)

    @staticmethod
    def vars_for_template(player):
        player.symbol_start_time = time.time()
        return {'duration_seconds': _task_duration(player)}

    @staticmethod
    def live_method(player, data):
        return _symbol_live_method(player, data)


class SymbolTask2(Page):
    template_name = 'symbol_matrix/SymbolTask.html'

    @staticmethod
    def is_displayed(player):
        return player.session.config.get('task_type') == 'symbol'

    @staticmethod
    def get_timeout_seconds(player):
        return _task_duration(player)

    @staticmethod
    def js_vars(player):
        return dict(first_image=_get_symbol_payload(player) or {}, viewing_seconds=8)

    @staticmethod
    def vars_for_template(player):
        player.symbol2_start_time = time.time()
        return {'duration_seconds': _task_duration(player)}

    @staticmethod
    def live_method(player, data):
        return _symbol_live_method(player, data)


class CombinedTask(Page):
    @staticmethod
    def is_displayed(player):
        return player.session.config.get('task_type') == 'combined'

    @staticmethod
    def get_timeout_seconds(player):
        return _task_duration(player)

    @staticmethod
    def js_vars(player):
        return dict(first_image=_get_combined_payload(player) or {}, viewing_seconds=8)

    @staticmethod
    def vars_for_template(player):
        player.combined_start_time = time.time()
        return {'duration_seconds': _task_duration(player)}

    @staticmethod
    def live_method(player, data):
        return _combined_live_method(player, data)


class CombinedTask2(Page):
    template_name = 'symbol_matrix/CombinedTask.html'

    @staticmethod
    def is_displayed(player):
        return player.session.config.get('task_type') == 'combined'

    @staticmethod
    def get_timeout_seconds(player):
        return _task_duration(player)

    @staticmethod
    def js_vars(player):
        return dict(first_image=_get_combined_payload(player) or {}, viewing_seconds=8)

    @staticmethod
    def vars_for_template(player):
        player.combined2_start_time = time.time()
        return {'duration_seconds': _task_duration(player)}

    @staticmethod
    def live_method(player, data):
        return _combined_live_method(player, data)


def _matrix_practice_live_method(player, data):
    """Serves practice trials — same grid generation, no data recorded.

    Validates the submitted answer and returns is_correct so the client
    can show appropriate feedback, but always advances regardless.
    """
    msg_type = data.get('type')

    if msg_type == 'request_task':
        task = _generate_matrix_task()
        # Store correct cells server-side so the client cannot fake a correct answer
        player.matrix_current_correct_cells = json.dumps(task['correct_cells'])
        return {player.id_in_group: {'type': 'task', 'task': task}}

    if msg_type == 'submit_practice':
        trial = data.get('trial', 1)
        clicked = sorted(data.get('clicked_cells', []))
        correct = sorted(json.loads(player.matrix_current_correct_cells))
        is_correct = (clicked == correct)

        if trial == 1:
            task = _generate_matrix_task()
            player.matrix_current_correct_cells = json.dumps(task['correct_cells'])
            return {player.id_in_group: {
                'type': 'next_task',
                'is_correct': is_correct,
                'task': task,
            }}
        else:
            return {player.id_in_group: {
                'type': 'practice_complete',
                'is_correct': is_correct,
            }}

    return {}


# ---------------------------------------------------------------------------
# Pages — matrix (pure symbol) task
# ---------------------------------------------------------------------------

class MatrixInstructions(Page):
    @staticmethod
    def is_displayed(player):
        return player.session.config.get('task_type') == 'matrix'

    @staticmethod
    def vars_for_template(player):
        return {
            'task_minutes':  player.session.config.get('task_minutes',  C.TASK_MINUTES_DEFAULT),
            'break_minutes': player.session.config.get('break_minutes', C.BREAK_MINUTES_DEFAULT),
            'condition':     player.field_maybe_none('condition') or 'choice',
        }


class MatrixPractice(Page):
    """Two free-form practice trials — no data recorded, no hints."""

    @staticmethod
    def is_displayed(player):
        return player.session.config.get('task_type') == 'matrix'

    @staticmethod
    def live_method(player, data):
        return _matrix_practice_live_method(player, data)


class MatrixStartScreen(Page):
    """Pre-task reminder screen — participant clicks Start (auto-advances after 20 s)."""

    @staticmethod
    def is_displayed(player):
        return player.session.config.get('task_type') == 'matrix'

    @staticmethod
    def get_timeout_seconds(player):
        return 20

    @staticmethod
    def vars_for_template(player):
        return {
            'task_minutes':  player.session.config.get('task_minutes',  C.TASK_MINUTES_DEFAULT),
            'break_minutes': player.session.config.get('break_minutes', C.BREAK_MINUTES_DEFAULT),
            'condition':     player.field_maybe_none('condition') or 'choice',
        }


class MatrixTask(Page):
    """Segment 1 of the matrix task (before the break / bridge)."""

    @staticmethod
    def is_displayed(player):
        return player.session.config.get('task_type') == 'matrix'

    @staticmethod
    def get_timeout_seconds(player):
        return _task_duration(player)

    @staticmethod
    def vars_for_template(player):
        player.matrix_start_time = time.time()
        return {}

    @staticmethod
    def live_method(player, data):
        return _matrix_live_method(player, data, block=1)

    @staticmethod
    def before_next_page(player, timeout_happened):
        condition = _get_condition(player)
        if condition == 'no_break':
            player.break_choice = False   # will trigger MatrixBridgeTask
        elif condition == 'forced_break':
            player.break_choice = True    # will trigger BreakWait


class MatrixBridgeTask(Page):
    """Bridge segment for participants who skip the break (same task UI, no timer)."""
    template_name = 'symbol_matrix/MatrixTask.html'

    @staticmethod
    def is_displayed(player):
        return (player.session.config.get('task_type') == 'matrix'
                and player.field_maybe_none('break_choice') == False)

    @staticmethod
    def get_timeout_seconds(player):
        return _break_duration(player)

    @staticmethod
    def vars_for_template(player):
        return {}

    @staticmethod
    def live_method(player, data):
        return _matrix_live_method(player, data, block=2)


class MatrixTask2(Page):
    """Segment 2 of the matrix task (after break / bridge)."""
    template_name = 'symbol_matrix/MatrixTask.html'

    @staticmethod
    def is_displayed(player):
        return player.session.config.get('task_type') == 'matrix'

    @staticmethod
    def get_timeout_seconds(player):
        return _task_duration(player)

    @staticmethod
    def vars_for_template(player):
        player.matrix2_start_time = time.time()
        return {}

    @staticmethod
    def live_method(player, data):
        return _matrix_live_method(player, data, block=3)


class Goodbye(Page):
    @staticmethod
    def vars_for_template(player):
        # Record end time
        player.experiment_end_time = time.time()

        # Experiment-wide totals
        player.total_tasks_attempted = (
            player.seg1_tasks_attempted +
            player.bridge_tasks_attempted +
            player.seg2_tasks_attempted
        )
        player.total_tasks_correct = (
            player.seg1_tasks_correct +
            player.bridge_tasks_correct +
            player.seg2_tasks_correct
        )

        # Payoff calculation
        player.payoff_seg1_bridge_credits = (
            player.seg1_tasks_correct + player.bridge_tasks_correct
        )   # 1 credit per correct task in seg1 + bridge
        player.payoff_seg2_credits = 2 * player.seg2_tasks_correct
        total_credits = player.payoff_seg1_bridge_credits + player.payoff_seg2_credits
        player.final_payoff_dollars = round(3.00 + 0.01 * total_credits, 2)

        # Also write to oTree's built-in payoff field (in points = dollars here)
        player.payoff = player.final_payoff_dollars

        return {
            'seg1_attempted':      player.seg1_tasks_attempted,
            'seg1_correct':        player.seg1_tasks_correct,
            'bridge_attempted':    player.bridge_tasks_attempted,
            'bridge_correct':      player.bridge_tasks_correct,
            'seg2_attempted':      player.seg2_tasks_attempted,
            'seg2_correct':        player.seg2_tasks_correct,
            'total_attempted':     player.total_tasks_attempted,
            'total_correct':       player.total_tasks_correct,
            'seg1_bridge_credits': player.payoff_seg1_bridge_credits,
            'seg2_credits':        player.payoff_seg2_credits,
            'total_credits':       total_credits,
            'final_payoff':        player.final_payoff_dollars,
            'break_choice':        player.field_maybe_none('break_choice'),
            # Pre-formatted dollar strings (avoids Jinja2 filter issues)
            'seg1_bridge_dollars': '{:.2f}'.format(player.payoff_seg1_bridge_credits * 0.01),
            'seg2_dollars':        '{:.2f}'.format(player.payoff_seg2_credits * 0.01),
            'final_payoff_str':    '{:.2f}'.format(player.final_payoff_dollars),
        }


# ---------------------------------------------------------------------------
# Pages — field ID, consent, demographics
# ---------------------------------------------------------------------------

class FieldIDEntry(Page):
    """First screen: participant enters their field ID (assigned by the research team)."""
    form_model  = 'player'
    form_fields = ['field_id']

    @staticmethod
    def is_displayed(player):
        return player.session.config.get('task_type') == 'matrix'

    @staticmethod
    def error_message(player, values):
        fid = (values.get('field_id') or '').strip()
        if not fid.isdigit() or len(fid) != 3:
            return 'Please enter a valid 3-digit Field ID (e.g. 101, 215, 302).'
        if fid[0] not in ('1', '2', '3'):
            return 'Field ID must start with 1, 2, or 3. Please check with the research assistant.'

    @staticmethod
    def before_next_page(player, timeout_happened):
        player.field_id = player.field_id.strip()
        player.condition = _get_condition(player)


class Consent(Page):
    """Informed consent — must tick checkbox to proceed."""
    form_model  = 'player'
    form_fields = ['consented']

    @staticmethod
    def is_displayed(player):
        return player.session.config.get('task_type') == 'matrix'

    @staticmethod
    def vars_for_template(player):
        return {
            'task_minutes':  player.session.config.get('task_minutes',  C.TASK_MINUTES_DEFAULT),
            'break_minutes': player.session.config.get('break_minutes', C.BREAK_MINUTES_DEFAULT),
        }

    @staticmethod
    def error_message(player, values):
        if not values.get('consented'):
            return 'Please tick the checkbox to confirm your consent before continuing.'


class Demographics(Page):
    """Post-task demographic survey — shown after the second session, before the payoff."""
    form_model  = 'player'
    form_fields = [
        'demo_age', 'demo_gender', 'demo_occupation',
        'demo_education', 'demo_income', 'demo_hours_slept', 'demo_breakfast',
    ]

    @staticmethod
    def is_displayed(player):
        return player.session.config.get('task_type') == 'matrix'


page_sequence = [
    FieldIDEntry,    # matrix: participant enters field ID
    Welcome,
    Consent,         # matrix: informed consent
    # Legacy instructions + training (hidden for matrix)
    Instructions,
    TrainingExample,
    # Legacy task pages (each filtered by is_displayed)
    Task1,
    CaptchaTask,
    OrderedTask,
    SymbolTask,
    CombinedTask,
    # Matrix task — instructions + practice + real segment 1
    MatrixInstructions,
    MatrixPractice,
    MatrixStartScreen,
    MatrixTask,
    # Break
    BreakChoice,
    BreakWait,         # shown only if break_choice == True
    BridgeTask,        # legacy no-break bridge
    MatrixBridgeTask,  # matrix no-break bridge
    # Session 2
    Task2,
    CaptchaTask2,
    OrderedTask2,
    SymbolTask2,
    CombinedTask2,
    MatrixTask2,
    Demographics,    # matrix: post-task demographic survey
    Goodbye,
]
