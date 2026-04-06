"""
data_loaders.py
Loads all CSV data from disk at server startup.
To change the symbol pool, edit symbols.csv — no code changes needed.
To change image/captcha/ordered data, edit the corresponding CSV files.
"""
import csv
import os


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
            category = row.get('category', '').strip()
            symbols.append({
                'symbol_id': int(row['symbol_id']),
                'latex':     row['latex'].strip(),
                'category':  category,
                'group':     row.get('group', category).strip() or category,
            })
    return symbols


IMAGE_DATA       = _load_image_data()
CAPTCHA_DATA     = _load_captcha_data()
ORDERED_DATA     = _load_ordered_data()
SYMBOL_DATA      = _load_symbol_data()
PURE_SYMBOL_DATA = _load_pure_symbols()

# Group index: {group_name: [symbol_dict, ...]} — only groups with >= 2 symbols
_grp = {}
for _s in PURE_SYMBOL_DATA:
    _grp.setdefault(_s['group'], []).append(_s)
PURE_SYMBOL_GROUPS = {k: v for k, v in _grp.items() if len(v) >= 2}
