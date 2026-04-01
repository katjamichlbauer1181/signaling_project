"""
annotate_images.py
------------------
Uses the Gemini Vision API (free tier) to automatically annotate images for
the CAPTCHA-style grid-selection task.

For each image it asks Gemini to:
  1. Identify a clear, salient object visible in part of the image.
  2. Write a short participant instruction ("Click all cells that contain X").
  3. For a 3×3 grid (cells numbered 0–8, left-to-right, top-to-bottom),
     list which cells contain that object.

Output: images_data_captcha.csv
  filename, task_type, target_object, question, correct_cells, notes

Usage:
    python annotate_images.py                # annotate all images
    python annotate_images.py --limit 5      # annotate first 5 (for testing)
    python annotate_images.py --rerun        # re-annotate even if already done
"""

import argparse
import base64
import csv
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv()
API_KEY    = os.environ.get("GEMINI_API_KEY")
IMAGES_DIR = Path("_static/images")
OUTPUT_CSV = Path("images_data_captcha.csv")
MODEL      = "gemini-2.0-flash"
GRID_SIZE  = 3          # 3×3 = 9 cells
DELAY_S    = 4.5        # seconds between requests (~13 RPM, under the 15 RPM limit)

PROMPT = """\
You are helping design a visual attention task for a research experiment.

The image will be shown to participants with a 3×3 grid overlaid on top,
dividing it into 9 equal cells numbered like this:

  0 | 1 | 2
  ---------
  3 | 4 | 5
  ---------
  6 | 7 | 8

(0 = top-left, 2 = top-right, 6 = bottom-left, 8 = bottom-right)

Your job:
1. Identify ONE clear, visually distinct object or category visible in the image
   that appears in SOME cells but NOT ALL (ideally 2–5 cells).
   Good examples: an animal, a vehicle, a person, a tree, a building.
   Avoid: sky, ground, grass if they cover the whole image.

2. Write a short participant instruction of the form:
   "Click all cells that contain [object]."

3. List exactly which cell numbers (0–8) contain that object.
   A cell "contains" the object if the object occupies a noticeable portion
   of that cell (more than ~20% of the cell area).

Return ONLY a JSON object with these fields — no extra text, no markdown:
{
  "target_object": "...",
  "question": "Click all cells that contain ...",
  "correct_cells": [list of integers],
  "notes": "optional short note about ambiguous cases, else empty string"
}
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_done(csv_path: Path) -> set:
    """Return the set of filenames already in the CSV."""
    if not csv_path.exists():
        return set()
    with open(csv_path, newline="", encoding="utf-8") as f:
        return {row["filename"] for row in csv.DictReader(f)}


def append_row(csv_path: Path, row: dict):
    """Append one row to the CSV, creating it with a header if needed."""
    write_header = not csv_path.exists()
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["filename", "task_type", "target_object",
                        "question", "correct_cells", "notes"],
        )
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def annotate_image(client, image_path: Path) -> dict:
    """Send image to Gemini and return parsed annotation dict."""
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    suffix = image_path.suffix.lower()
    mime   = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
              ".png": "image/png", ".webp": "image/webp"}.get(suffix, "image/jpeg")

    response = client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime),
            PROMPT,
        ],
    )
    raw = response.text.strip()

    # Strip markdown code fences if Gemini wraps in ```json ... ```
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    return json.loads(raw)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit",  type=int, default=None,
                        help="Only process this many images (for testing)")
    parser.add_argument("--rerun",  action="store_true",
                        help="Re-annotate images already in the CSV")
    args = parser.parse_args()

    if not API_KEY:
        raise SystemExit("ERROR: GEMINI_API_KEY not found. "
                         "Add it to your .env file and try again.")

    client = genai.Client(api_key=API_KEY)

    images = sorted(IMAGES_DIR.glob("*.jpg")) + \
             sorted(IMAGES_DIR.glob("*.jpeg")) + \
             sorted(IMAGES_DIR.glob("*.png"))

    if not images:
        raise SystemExit(f"No images found in {IMAGES_DIR}/")

    done = set() if args.rerun else load_done(OUTPUT_CSV)
    todo = [p for p in images if p.name not in done]

    if args.limit:
        todo = todo[:args.limit]

    print(f"Images found   : {len(images)}")
    print(f"Already done   : {len(done)}")
    print(f"To annotate    : {len(todo)}")
    print(f"Output         : {OUTPUT_CSV}")
    print()

    ok, failed = 0, []

    for i, img_path in enumerate(todo, 1):
        print(f"[{i}/{len(todo)}] {img_path.name} ...", end=" ", flush=True)
        try:
            result = annotate_image(client, img_path)

            append_row(OUTPUT_CSV, {
                "filename":      img_path.name,
                "task_type":     "captcha_grid",
                "target_object": result.get("target_object", ""),
                "question":      result.get("question", ""),
                "correct_cells": json.dumps(result.get("correct_cells", [])),
                "notes":         result.get("notes", ""),
            })

            cells = result.get("correct_cells", [])
            print(f"OK  →  '{result.get('target_object')}'  cells {cells}")
            ok += 1

        except Exception as e:
            print(f"FAILED — {e}")
            failed.append(img_path.name)

        # Rate-limit: stay under 15 requests/minute (free tier)
        if i < len(todo):
            time.sleep(DELAY_S)

    print()
    print(f"Done. Annotated {ok}/{len(todo)} images.")
    if failed:
        print(f"Failed ({len(failed)}):")
        for name in failed:
            print(f"  {name}")
        print("Re-run the script to retry failures (already-done images are skipped).")


if __name__ == "__main__":
    main()
