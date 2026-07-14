#!/usr/bin/env python3
"""
Regenerate the `data` array in index.html from cpd_data.csv.

Counts total disciplinary cases per year (no category breakdown — see the
"per year" and "cpd-viz" tools for that). Uses the same year-of-record logic
as those tools: Hearing Date, else Effective date of termination, else the
YY- prefix of the report ID (e.g. 17-126 -> 2017).

Setup:
  - Put cpd_data.csv next to this file (or edit CSV_PATH).

Run:
  python3 build_data.py
"""

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

HERE       = Path(__file__).parent
INDEX_HTML = HERE / "index.html"
CSV_PATH   = HERE / "cpd_data.csv"

ID_PAT = re.compile(r"^\s*(\d{2})-\d+")

def year_of(row):
    """Year for a case: Hearing Date, else Effective date of termination,
    else the YY- prefix of the report ID (e.g. 17-126 -> 2017)."""
    for col in ("Hearing Date", "Effective date of termination"):
        m = re.search(r"(20\d\d)", (row.get(col) or "").strip())
        if m:
            return int(m.group(1))
    p = ID_PAT.match(row.get("Link to original report") or "")
    return 2000 + int(p.group(1)) if p else None

YEAR_MIN, YEAR_MAX = 2017, 2025  # exclude partial edge years (2016, 2026)

year_cases = defaultdict(int)

with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        year = year_of(row)
        if year is None or not (YEAR_MIN <= year <= YEAR_MAX):
            continue
        year_cases[year] += 1

years_out = [{"year": y, "hearings": year_cases[y]} for y in sorted(year_cases)]

# ── Write back into index.html ───────────────────────────────────────────────

raw = INDEX_HTML.read_text(encoding="utf-8")
entries = ",\n".join(f"  {{ year: {d['year']}, hearings: {d['hearings']} }}" for d in years_out)
data_js = f"const data = [\n{entries},\n];"

new_raw, n = re.subn(
    r"const data = \[.*?\];",
    data_js,
    raw,
    count=1,
    flags=re.DOTALL,
)
if n == 0:
    raise RuntimeError("Could not find 'const data = [...];' in index.html")
INDEX_HTML.write_text(new_raw, encoding="utf-8")

total = sum(year_cases.values())
print(f"Updated {INDEX_HTML.name} — {total} dated cases across {len(years_out)} years.")
for y in years_out:
    print(f"  {y['year']}: {y['hearings']} cases")
