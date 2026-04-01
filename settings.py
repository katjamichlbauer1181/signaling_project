from os import environ

SESSION_CONFIGS = [
    # ── Matrix (pure symbol) task ──────────────────────────────────────────
    dict(
        name='matrix_demo',
        display_name='Symbol Matrix Task (Demo — 3+1+3 min)',
        app_sequence=['symbol_matrix'],
        num_demo_participants=1,
        task_minutes=3,
        break_minutes=1,
        task_type='matrix',
    ),
    dict(
        name='matrix_full',
        display_name='Symbol Matrix Task (Full — 40+10+40 min)',
        app_sequence=['symbol_matrix'],
        num_demo_participants=1,
        task_minutes=40,
        break_minutes=10,
        task_type='matrix',
    ),
    # ── Legacy demos (kept for reference) ─────────────────────────────────
    dict(
        name='captcha_demo',
        display_name='[Legacy] CAPTCHA Grid Task (Demo)',
        app_sequence=['symbol_matrix'],
        num_demo_participants=1,
        task_minutes=3,
        break_minutes=1,
        task_type='captcha',
    ),
    dict(
        name='ordered_demo',
        display_name='[Legacy] Ordered Selection Task (Demo)',
        app_sequence=['symbol_matrix'],
        num_demo_participants=1,
        task_minutes=3,
        break_minutes=1,
        task_type='ordered',
    ),
    dict(
        name='symbol_demo',
        display_name='[Legacy] Symbol Search + Image Task (Demo)',
        app_sequence=['symbol_matrix'],
        num_demo_participants=1,
        task_minutes=5,
        break_minutes=1,
        task_type='symbol',
    ),
]

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00,
    participation_fee=0.00,
    doc='',
)

PARTICIPANT_FIELDS = []
SESSION_FIELDS = []

LANGUAGE_CODE = 'en'
REAL_WORLD_CURRENCY_CODE = 'USD'
USE_POINTS = False

ROOMS = []

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD', 'admin')

DEMO_PAGE_INTRO_HTML = 'Symbol Matrix Task Experiment'

SECRET_KEY = 'change-this-secret-key-before-deployment'

INSTALLED_APPS = ['otree']
