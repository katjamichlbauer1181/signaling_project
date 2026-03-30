from os import environ

SESSION_CONFIGS = [
    dict(
        name='image_labelling',
        display_name='Image Labelling Task (Full — 90+15+90 min)',
        app_sequence=['image_labelling'],
        num_demo_participants=1,
        task_minutes=90,
        break_minutes=15,
        task_type='captcha',
    ),
    dict(
        name='image_labelling_demo',
        display_name='Image Labelling Task (Demo — short timers)',
        app_sequence=['image_labelling'],
        num_demo_participants=1,
        task_minutes=2,
        break_minutes=1,
        task_type='captcha',
    ),
    dict(
        name='captcha_demo',
        display_name='CAPTCHA Grid Task (Demo)',
        app_sequence=['image_labelling'],
        num_demo_participants=1,
        task_minutes=3,
        break_minutes=1,
        task_type='captcha',
    ),
    dict(
        name='ordered_demo',
        display_name='Ordered Selection Task (Demo)',
        app_sequence=['image_labelling'],
        num_demo_participants=1,
        task_minutes=3,
        break_minutes=1,
        task_type='ordered',
    ),
    dict(
        name='symbol_demo',
        display_name='Symbol Search Task (Demo)',
        app_sequence=['image_labelling'],
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

DEMO_PAGE_INTRO_HTML = 'Image Labelling Experiment Demo'

SECRET_KEY = 'change-this-secret-key-before-deployment'

INSTALLED_APPS = ['otree']
