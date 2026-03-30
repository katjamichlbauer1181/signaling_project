import csv
import json
import os
import random
import time

from otree.api import *

doc = """
Image Labelling Task.

Participants view images one at a time and provide free-text answers to
image-specific questions. The experiment has two 90-minute task blocks
separated by an optional 15-minute break.

Session config keys:
  task_minutes  (int, default 90)  — duration of each task block in minutes
  break_minutes (int, default 15)  — duration of the break in minutes
"""


# ---------------------------------------------------------------------------
# Load image data at module import time
# ---------------------------------------------------------------------------

def _load_image_data():
    csv_path = os.path.join(os.path.dirname(__file__), 'images_data.csv')
    images = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            images.append({
                'filename': row['filename'].strip(),
                'question': row['question'].strip(),
            })
    return images


def _load_captcha_data():
    """Load captcha image data from images_data_captcha.csv (project root)."""
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
    """Load ordered-selection image data from images_data_ordered.csv (project root).

    Each row has a 'targets' column containing a JSON array of dicts:
      [{"name": "head", "box": [x1, y1, x2, y2]}, ...]
    where box coordinates are normalised fractions of image width/height (0–1).
    """
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
    """Load symbol-search + memory-question data from images_data_symbol.csv."""
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


IMAGE_DATA   = _load_image_data()
CAPTCHA_DATA = _load_captcha_data()
ORDERED_DATA = _load_ordered_data()
SYMBOL_DATA  = _load_symbol_data()

# Symbol-search grid constants
NUM_SYMBOL_TYPES    = 8
SYMBOL_GRID_SIZE    = 49   # 7 × 7
NUM_TARGETS_IN_GRID = 8    # how many target symbols are placed in the grid


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

class C(BaseConstants):
    NAME_IN_URL = 'image_labelling'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

    TASK_MINUTES_DEFAULT = 90
    BREAK_MINUTES_DEFAULT = 15

    TRAINING_IMAGE = 'training_example.svg'
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
        """Assign shuffled image orders to every player when the session is created."""
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
    # Shuffled list of IMAGE_DATA indices, serialised as JSON
    image_order = models.LongStringField()
    # Points to the next image to show (incremented after each submission)
    current_image_index = models.IntegerField(initial=0)

    # Break decision (set on BreakChoice page)
    break_choice = models.BooleanField(
        label='Would you like to take a 15-minute break before continuing?',
        choices=[
            [True,  'Yes, I would like to take a 15-minute break'],
            [False, 'No, I will continue working'],
        ],
        widget=widgets.RadioSelect,
    )

    # Training answer — stored for completeness but not analysed
    training_answer = models.LongStringField(
        label='Your answer (practice)',
        blank=True,
    )

    # Captcha task state
    captcha_image_order   = models.LongStringField()
    current_captcha_index = models.IntegerField(initial=0)

    # Ordered-selection task state
    ordered_image_order   = models.LongStringField()
    current_ordered_index = models.IntegerField(initial=0)

    # Symbol-search task state
    symbol_image_order      = models.LongStringField()
    current_symbol_index    = models.IntegerField(initial=0)
    symbol_current_attempts = models.IntegerField(initial=0)

    # Server-side timestamps (Unix epoch, seconds)
    captcha_start_time  = models.FloatField(null=True)
    captcha2_start_time = models.FloatField(null=True)
    ordered_start_time  = models.FloatField(null=True)
    ordered2_start_time = models.FloatField(null=True)
    symbol_start_time   = models.FloatField(null=True)


class Answer(ExtraModel):
    """One row per free-text image-labelling response."""
    player = models.Link(Player)

    # 1 = first 90-min block, 2 = bridge, 3 = second 90-min block
    block            = models.IntegerField()
    image_index      = models.IntegerField()
    image_filename   = models.StringField()
    question         = models.StringField()
    answer_text      = models.LongStringField()
    response_time_ms = models.FloatField()
    timestamp        = models.FloatField()


class CaptchaAnswer(ExtraModel):
    """One row per CAPTCHA grid-selection response."""
    player = models.Link(Player)

    image_index      = models.IntegerField()
    image_filename   = models.StringField()
    target_object    = models.StringField()
    question         = models.StringField()
    selected_cells   = models.LongStringField()   # JSON array, e.g. "[0, 3, 4]"
    correct_cells    = models.LongStringField()   # JSON array from annotation
    is_correct       = models.BooleanField()
    response_time_ms = models.FloatField()
    timestamp        = models.FloatField()


class OrderedAnswer(ExtraModel):
    """One row per ordered-selection response."""
    player = models.Link(Player)

    image_index      = models.IntegerField()
    image_filename   = models.StringField()
    question         = models.StringField()
    click_sequence   = models.LongStringField()  # JSON [{x,y}, ...] submitted by participant
    targets_json     = models.LongStringField()  # JSON [{name, box}, ...] from annotation
    is_correct       = models.BooleanField()
    response_time_ms = models.FloatField()
    timestamp        = models.FloatField()


class SymbolAnswer(ExtraModel):
    """One row per symbol-search + memory-question response."""
    player = models.Link(Player)

    image_index        = models.IntegerField()
    image_filename     = models.StringField()
    question           = models.StringField()
    attempt_number     = models.IntegerField()       # 1-indexed; >1 means a retry
    target_symbol      = models.IntegerField()       # 0–7
    target_cells       = models.LongStringField()    # JSON sorted [int, ...]
    clicked_cells      = models.LongStringField()    # JSON sorted [int, ...]
    symbol_correct     = models.BooleanField()
    symbol_time_ms     = models.FloatField()
    answer_options     = models.LongStringField()    # JSON ["A","B","C","D"]
    correct_answer     = models.StringField()
    participant_answer = models.StringField()
    answer_correct     = models.BooleanField()
    response_time_ms   = models.FloatField()
    timestamp          = models.FloatField()


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _get_image_payload(player):
    """Return the next image dict for a player, or None if pool exhausted."""
    # Initialise image_order here as a fallback in case creating_session was
    # not called (e.g. when reusing an existing session / stale database).
    if player.field_maybe_none('image_order') is None:
        order = list(range(len(IMAGE_DATA)))
        random.shuffle(order)
        player.image_order = json.dumps(order)
    order = json.loads(player.image_order)
    idx = player.current_image_index
    if idx >= len(order):
        return None
    img = IMAGE_DATA[order[idx]]
    return {
        'filename': img['filename'],
        'question':  img['question'],
        'index':     idx,
        'total':     len(order),
    }


def _task_live_method(player, data, block):
    """
    Handles two message types from the client:
      'request_image'  — send the current image to the participant
      'submit_answer'  — save the answer, advance index, send next image
    """
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
            player=player,
            block=block,
            image_index=idx,
            image_filename=img.get('filename', ''),
            question=img.get('question', ''),
            answer_text=data.get('answer', ''),
            response_time_ms=data.get('response_time_ms', 0),
            timestamp=time.time(),
        )
        player.current_image_index += 1

        payload = _get_image_payload(player)
        if payload:
            return {player.id_in_group: {'type': 'image', **payload}}
        return {player.id_in_group: {'type': 'pool_exhausted'}}

    return {}


def _task_duration(player):
    return int(player.session.config.get('task_minutes',  C.TASK_MINUTES_DEFAULT)  * 60)


def _break_duration(player):
    return int(player.session.config.get('break_minutes', C.BREAK_MINUTES_DEFAULT) * 60)


def _get_captcha_payload(player):
    """Return the next captcha image dict for a player, or None if pool exhausted."""
    if player.field_maybe_none('captcha_image_order') is None:
        captcha_order = list(range(len(CAPTCHA_DATA)))
        random.shuffle(captcha_order)
        player.captcha_image_order = json.dumps(captcha_order)
    order = json.loads(player.captcha_image_order)
    idx = player.current_captcha_index
    if idx >= len(order) or not CAPTCHA_DATA:
        return None
    img = CAPTCHA_DATA[order[idx]]
    return {
        'filename':      img['filename'],
        'question':      img['question'],
        'target_object': img['target_object'],
        'correct_cells': json.loads(img['correct_cells']),
        'index':         idx,
        'total':         len(order),
    }


def _captcha_live_method(player, data):
    if data.get('type') == 'submit_answer':
        selected = sorted(data.get('selected_cells', []))

        order = json.loads(player.captcha_image_order)
        idx   = player.current_captcha_index
        img   = CAPTCHA_DATA[order[idx]] if idx < len(order) else {}
        correct = sorted(json.loads(img.get('correct_cells', '[]')))
        is_correct = (selected == correct)

        CaptchaAnswer.create(
            player=player,
            image_index=idx,
            image_filename=img.get('filename', ''),
            target_object=img.get('target_object', ''),
            question=img.get('question', ''),
            selected_cells=json.dumps(selected),
            correct_cells=img.get('correct_cells', '[]'),
            is_correct=is_correct,
            response_time_ms=data.get('response_time_ms', 0),
            timestamp=time.time(),
        )
        player.current_captcha_index += 1

        next_payload = _get_captcha_payload(player)
        return {player.id_in_group: {
            'type':          'feedback',
            'is_correct':    is_correct,
            'correct_cells': correct,
            'next_image':    next_payload,
        }}

    return {}


def _point_in_box(x, y, box):
    """Check whether normalised point (x, y) falls inside box [x1, y1, x2, y2]."""
    x1, y1, x2, y2 = box
    return x1 <= x <= x2 and y1 <= y <= y2


def _get_ordered_payload(player):
    """Return the next ordered-selection image dict for a player, or None if pool exhausted.
    Does NOT send the target boxes to the client — only num_targets is revealed.
    """
    if player.field_maybe_none('ordered_image_order') is None:
        ordered_order = list(range(len(ORDERED_DATA)))
        random.shuffle(ordered_order)
        player.ordered_image_order = json.dumps(ordered_order)
    order = json.loads(player.ordered_image_order)
    idx = player.current_ordered_index
    if idx >= len(order) or not ORDERED_DATA:
        return None
    img = ORDERED_DATA[order[idx]]
    targets = json.loads(img['targets'])
    return {
        'filename':    img['filename'],
        'question':    img['question'],
        'num_targets': len(targets),   # how many clicks are expected
        'index':       idx,
        'total':       len(order),
    }


def _ordered_live_method(player, data):
    if data.get('type') == 'submit_answer':
        # clicks = [{x: 0.42, y: 0.15}, ...] — normalised coords from client
        clicks = data.get('click_sequence', [])

        order = json.loads(player.ordered_image_order)
        idx   = player.current_ordered_index
        img   = ORDERED_DATA[order[idx]] if idx < len(order) else {}
        targets = json.loads(img.get('targets', '[]'))

        # Correct if every click lands in the corresponding target box, in order
        is_correct = (
            len(clicks) == len(targets) and
            all(_point_in_box(c['x'], c['y'], t['box'])
                for c, t in zip(clicks, targets))
        )

        OrderedAnswer.create(
            player=player,
            image_index=idx,
            image_filename=img.get('filename', ''),
            question=img.get('question', ''),
            click_sequence=json.dumps(clicks),
            targets_json=img.get('targets', '[]'),
            is_correct=is_correct,
            response_time_ms=data.get('response_time_ms', 0),
            timestamp=time.time(),
        )
        player.current_ordered_index += 1

        next_payload = _get_ordered_payload(player)
        return {player.id_in_group: {
            'type':        'feedback',
            'is_correct':  is_correct,
            'targets':     targets,     # sent now so client can show correct boxes
            'next_image':  next_payload,
        }}

    return {}


def _generate_symbol_grid(target_symbol):
    """Return (grid, target_cells) where grid is a list of SYMBOL_GRID_SIZE ints
    and target_cells is the sorted list of positions containing target_symbol."""
    non_targets = [s for s in range(NUM_SYMBOL_TYPES) if s != target_symbol]
    grid = [random.choice(non_targets) for _ in range(SYMBOL_GRID_SIZE)]
    target_cells = random.sample(range(SYMBOL_GRID_SIZE), NUM_TARGETS_IN_GRID)
    for cell in target_cells:
        grid[cell] = target_symbol
    return grid, sorted(target_cells)


def _get_symbol_payload(player):
    """Return the next symbol-task image dict, or None if pool exhausted.
    Generates a fresh random grid on each call.
    """
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
        'filename':       img['filename'],
        'question':       img['question'],
        'answer_options': json.loads(img['answer_options']),
        'target_symbol':  target_symbol,
        'symbol_grid':    grid,          # list of 36 ints (symbol indices)
        'target_cells':   target_cells,  # sorted list of correct positions
        'index':          idx,
        'total':          len(order),
    }


def _symbol_live_method(player, data):
    if data.get('type') == 'submit_answer':
        clicked      = sorted(data.get('clicked_cells', []))
        target_cells = sorted(data.get('target_cells', []))
        symbol_correct = (clicked == target_cells)

        order = json.loads(player.symbol_image_order)
        idx   = player.current_symbol_index
        img   = SYMBOL_DATA[order[idx]] if idx < len(order) else {}

        participant_answer = data.get('answer', '')
        answer_correct = (participant_answer == img.get('correct_answer', ''))
        attempt_number = player.symbol_current_attempts + 1

        # Record every attempt (including failed ones) for analysis
        SymbolAnswer.create(
            player=player,
            image_index=idx,
            image_filename=img.get('filename', ''),
            question=img.get('question', ''),
            attempt_number=attempt_number,
            target_symbol=data.get('target_symbol', 0),
            target_cells=json.dumps(target_cells),
            clicked_cells=json.dumps(clicked),
            symbol_correct=symbol_correct,
            symbol_time_ms=data.get('symbol_time_ms', 0),
            answer_options=img.get('answer_options', '[]'),
            correct_answer=img.get('correct_answer', ''),
            participant_answer=participant_answer,
            answer_correct=answer_correct,
            response_time_ms=data.get('response_time_ms', 0),
            timestamp=time.time(),
        )

        if answer_correct:
            # Correct — advance to next image
            player.current_symbol_index    += 1
            player.symbol_current_attempts  = 0
            next_payload = _get_symbol_payload(player)
            return {player.id_in_group: {
                'type':       'feedback',
                'next_image': next_payload,
            }}
        else:
            # Wrong — retry same image with a fresh symbol grid, no answer revealed
            player.symbol_current_attempts += 1
            same_payload = _get_symbol_payload(player)   # same idx → same filename/question, new grid
            return {player.id_in_group: {
                'type':       'retry',
                'same_image': same_payload,
            }}

    return {}


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

class Welcome(Page):
    pass


class Instructions(Page):
    pass


class TrainingExample(Page):
    form_model  = 'player'
    form_fields = ['training_answer']

    @staticmethod
    def vars_for_template(player):
        return {
            'training_image':    C.TRAINING_IMAGE,
            'training_question': C.TRAINING_QUESTION,
        }


class Task1(Page):
    template_name = 'image_labelling/TaskPage.html'

    @staticmethod
    def get_timeout_seconds(player):
        return _task_duration(player)

    @staticmethod
    def js_vars(player):
        return dict(first_image=_get_image_payload(player) or {})

    @staticmethod
    def vars_for_template(player):
        player.task1_start_time = time.time()
        return {
            'duration_seconds': _task_duration(player),
            'block_label': 'Session 1 of 2',
        }

    @staticmethod
    def live_method(player, data):
        return _task_live_method(player, data, block=1)


class BreakChoice(Page):
    form_model  = 'player'
    form_fields = ['break_choice']


class BreakWait(Page):
    """Locked break screen for participants who chose to take a break."""

    @staticmethod
    def is_displayed(player):
        return player.break_choice == True

    @staticmethod
    def get_timeout_seconds(player):
        return _break_duration(player)

    @staticmethod
    def vars_for_template(player):
        return {'duration_seconds': _break_duration(player)}


class BridgeTask(Page):
    """15-minute task continuation for participants who chose NOT to take a break."""
    template_name = 'image_labelling/TaskPage.html'

    @staticmethod
    def is_displayed(player):
        return player.break_choice == False

    @staticmethod
    def get_timeout_seconds(player):
        return _break_duration(player)

    @staticmethod
    def js_vars(player):
        return dict(first_image=_get_image_payload(player) or {})

    @staticmethod
    def vars_for_template(player):
        return {
            'duration_seconds': _break_duration(player),
            'block_label': 'Session 1 of 2 (continuing through break)',
        }

    @staticmethod
    def live_method(player, data):
        return _task_live_method(player, data, block=2)


class Task2(Page):
    template_name = 'image_labelling/TaskPage.html'

    @staticmethod
    def get_timeout_seconds(player):
        return _task_duration(player)

    @staticmethod
    def js_vars(player):
        return dict(first_image=_get_image_payload(player) or {})

    @staticmethod
    def vars_for_template(player):
        player.task2_start_time = time.time()
        return {
            'duration_seconds': _task_duration(player),
            'block_label': 'Session 2 of 2',
        }

    @staticmethod
    def live_method(player, data):
        return _task_live_method(player, data, block=3)


class CaptchaTask(Page):
    """CAPTCHA block 1 — before the break."""

    @staticmethod
    def is_displayed(player):
        return player.session.config.get('task_type', 'captcha') == 'captcha'

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
    """CAPTCHA block 2 — after the break. Continues from where block 1 left off."""
    template_name = 'image_labelling/CaptchaTask.html'

    @staticmethod
    def is_displayed(player):
        return player.session.config.get('task_type', 'captcha') == 'captcha'

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
    """Ordered-selection block 1 — before the break."""

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
    """Ordered-selection block 2 — after the break."""
    template_name = 'image_labelling/OrderedTask.html'

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
    """Symbol-search + memory-question task."""

    @staticmethod
    def is_displayed(player):
        return player.session.config.get('task_type') == 'symbol'

    @staticmethod
    def get_timeout_seconds(player):
        return _task_duration(player)

    @staticmethod
    def js_vars(player):
        return dict(
            first_image=_get_symbol_payload(player) or {},
            viewing_seconds=8,
        )

    @staticmethod
    def vars_for_template(player):
        player.symbol_start_time = time.time()
        return {'duration_seconds': _task_duration(player)}

    @staticmethod
    def live_method(player, data):
        return _symbol_live_method(player, data)


class Goodbye(Page):
    pass


page_sequence = [
    Welcome,
    Instructions,
    TrainingExample,
    CaptchaTask,
    OrderedTask,
    SymbolTask,
    BreakChoice,
    BreakWait,
    CaptchaTask2,
    OrderedTask2,
    Goodbye,
]
