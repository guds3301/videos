#!/usr/bin/env python3
"""Turn a graphics manifest.json into EDIT_PLAN asset entries.

    python3 graphics_assets.py OUT_DIR/manifest.json --plan-dir episodes/<slug> [--merge EDIT_PLAN.json]

Without --merge the entries are printed as JSON. With --merge the missing ones are appended to the
plan's "assets" (existing asset IDs are never touched) and the file is rewritten.
Asset paths are written relative to --plan-dir, with forward slashes, as the plan format requires.
Clips are marked user_owned because they are generated from this repository's own code; change that
if a spec embeds third-party material.
"""
import argparse
import json
import os
import sys
from pathlib import Path


def entries(manifest_path: Path, plan_dir: Path):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    out = []
    for clip in manifest["clips"]:
        file = manifest_path.parent / clip["file"]
        rel = os.path.relpath(file, plan_dir).replace("\\", "/")
        out.append({
            "asset_id": f"G-{clip['id']}",
            "path": rel,
            "asset_type": "video",
            "source_url": None,
            "creator": "own work (Remotion graphics)",
            "license": "own work",
            "attribution": None,
            "rights_status": "user_owned",
            "probe": {"duration_seconds": round(clip["duration_frames"] / clip["fps"], 3),
                      "width": clip["width"], "height": clip["height"], "fps": clip["fps"],
                      "has_audio": False},
            "notes": f"{clip['composition']} graphic with alpha channel ({clip['format']}), "
                     f"{clip['duration_frames']} frames @ {clip['fps']} fps. Clip id {clip['id']}.",
        })
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--plan-dir", type=Path, required=True)
    parser.add_argument("--merge", type=Path)
    args = parser.parse_args()
    if not args.manifest.is_file():
        sys.exit(f"manifest not found: {args.manifest}")
    new = entries(args.manifest, args.plan_dir)
    if not args.merge:
        print(json.dumps(new, indent=2))
        return
    plan = json.loads(args.merge.read_text(encoding="utf-8"))
    existing = {a["asset_id"] for a in plan["assets"]}
    added = [a for a in new if a["asset_id"] not in existing]
    plan["assets"].extend(added)
    args.merge.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"added {len(added)} asset(s); skipped {len(new) - len(added)} already present")


if __name__ == "__main__":
    main()
