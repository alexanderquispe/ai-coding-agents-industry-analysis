#!/usr/bin/env python3
"""
One-time repair script: rebuild Claude checkpoints to match actual output.

Problem: The fetch script overwrote output files across multiple runs,
losing ~2.6M commits. The seen_keys file still has all 2.88M SHAs,
which would prevent re-fetching the lost data. The manifest marks all
31 days as complete even though only Jan 30-31 data survives.

This script:
1. Rebuilds seen_keys from the actual output JSONL (176K keys)
2. Resets manifest: keeps Jan 30-31 as complete, marks Jan 1-29 as pending
3. Backs up originals before modifying
"""

import json
import shutil
from pathlib import Path

CHECKPOINT_DIR = Path("checkpoints")
OUTPUT_DIR = Path("output")

AGENT_KEY = "Claude"
JSONL_FILE = OUTPUT_DIR / "claude_commits.jsonl"
SEEN_KEYS_FILE = CHECKPOINT_DIR / f"seen_keys_{AGENT_KEY}.txt"
MANIFEST_FILE = CHECKPOINT_DIR / f"manifest_{AGENT_KEY}.json"

# --- Step 0: Backup ---
for f in [SEEN_KEYS_FILE, MANIFEST_FILE]:
    backup = f.with_suffix(f.suffix + ".bak")
    if not backup.exists():
        shutil.copy2(f, backup)
        print(f"Backed up: {f} -> {backup}")
    else:
        print(f"Backup already exists: {backup}")

# --- Step 1: Rebuild seen_keys from actual JSONL ---
print(f"\nReading {JSONL_FILE}...")
shas = set()
with open(JSONL_FILE, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            item = json.loads(line)
            shas.add(item["sha"])

print(f"  Found {len(shas):,} unique SHAs in output file")

with open(SEEN_KEYS_FILE, "w") as f:
    for sha in shas:
        f.write(sha + "\n")
print(f"  Wrote {len(shas):,} keys to {SEEN_KEYS_FILE}")

# --- Step 2: Fix manifest ---
manifest = json.load(open(MANIFEST_FILE))
print(f"\nManifest has {len(manifest)} days")

# Figure out which days have data in the output
import pandas as pd
df = pd.read_parquet(OUTPUT_DIR / "claude_commits.parquet")
df["day"] = df["committed_date"].astype(str).str[:10]
days_in_output = set(df["day"].unique())
print(f"Days with data in output: {days_in_output}")

# Reset days that don't have data in the output
reset_count = 0
for day_str in sorted(manifest.keys()):
    if day_str not in days_in_output:
        old_items = manifest[day_str].get("items", 0)
        manifest[day_str] = {"status": "pending", "items": 0}
        reset_count += 1

print(f"Reset {reset_count} days to 'pending'")
kept = [d for d, v in manifest.items() if v.get("status") == "complete"]
print(f"Kept as complete: {kept}")

with open(MANIFEST_FILE, "w") as f:
    json.dump(manifest, f, indent=2)
print(f"Wrote updated manifest to {MANIFEST_FILE}")

print("\n✓ Repair complete. You can now re-run:")
print("  python bulk-fetch/fetch_bulk.py --agent claude --start 2026-01-01 --end 2026-01-31")
print("  The script will re-fetch Jan 1-29 and append to the existing Jan 30-31 data.")
