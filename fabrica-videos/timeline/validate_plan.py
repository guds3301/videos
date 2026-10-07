#!/usr/bin/env python3
"""Validate a Fabrica Videos EDIT_PLAN.json (plan version 2).

Usage:
    python3 validate_plan.py EPISODE/EDIT_PLAN.json [--schema PATH] [--no-probe] [--json]

Implements the validator responsibilities of TIMELINE_SPEC.md. Every check is
reported as pass / warn / fail / skipped. A check that could not run is reported
as skipped and is never counted as passed.

Exit codes: 0 no failures, 1 at least one failure, 2 the plan could not be read.
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

try:
    import jsonschema
except ImportError:  # pragma: no cover - reported at runtime
    jsonschema = None

DEFAULT_SCHEMA = Path(__file__).resolve().parent / "EDIT_PLAN.schema.json"
# Statuses at which unresolved material is no longer acceptable.
PAST_DRAFT = {"approved", "in_edit", "review", "final"}
EDITING = {"in_edit", "review", "final"}
OVERLAP_TRANSITIONS = {"short_dissolve", "continuous_move"}
SOURCE_EPSILON_SECONDS = 0.001


def round_half_up(value: Fraction) -> int:
    """The single documented seconds-to-frames rounding rule."""
    return math.floor(value + Fraction(1, 2))


def seconds_to_frames(seconds, fps: Fraction) -> int:
    return round_half_up(Fraction(repr(seconds)) * fps)


def is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


class Check:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.notes: list[str] = []
        self.skipped: str | None = None

    @property
    def status(self) -> str:
        if self.skipped is not None:
            return "skipped"
        if self.errors:
            return "fail"
        if self.warnings:
            return "warn"
        return "pass"

    def problem(self, strict: bool, message: str) -> None:
        (self.errors if strict else self.warnings).append(message)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "errors": self.errors,
            "warnings": self.warnings,
            "notes": self.notes,
            "skipped_reason": self.skipped,
        }


def probe_media(path: Path) -> dict | None:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries",
            "format=duration:stream=codec_type,width,height,avg_frame_rate,r_frame_rate",
            "-of", "json", str(path),
        ],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return None
    data = json.loads(result.stdout or "{}")
    info = {"duration": None, "width": None, "height": None, "fps": None,
            "has_video": False, "has_audio": False}
    try:
        info["duration"] = float(data.get("format", {}).get("duration"))
    except (TypeError, ValueError):
        pass
    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video" and not info["has_video"]:
            info["has_video"] = True
            info["width"] = stream.get("width")
            info["height"] = stream.get("height")
            rate = stream.get("avg_frame_rate") or stream.get("r_frame_rate") or "0/1"
            try:
                num, den = rate.split("/")
                info["fps"] = float(Fraction(int(num), int(den))) if int(den) else None
            except (ValueError, ZeroDivisionError):
                pass
        elif stream.get("codec_type") == "audio":
            info["has_audio"] = True
    return info


def iter_visual_clips(plan):
    for si, scene in enumerate(plan["scenes"]):
        for ci, clip in enumerate(scene["clips"]):
            yield f"$.scenes[{si}].clips[{ci}]", scene, clip


def iter_audio_clips(plan):
    for si, scene in enumerate(plan["scenes"]):
        for ci, clip in enumerate(scene["audio_clips"]):
            yield f"$.scenes[{si}].audio_clips[{ci}]", scene, clip


def run_validation(plan_path: Path, schema_path: Path = DEFAULT_SCHEMA,
                   probe: bool = True) -> tuple[list[Check], dict]:
    checks: list[Check] = []
    meta = {"plan": str(plan_path), "probe_requested": probe}

    def new(name: str, description: str) -> Check:
        check = Check(name, description)
        checks.append(check)
        return check

    # 1. Parse + JSON Schema --------------------------------------------------
    schema_check = new("schema", "JSON parses and matches the JSON Schema")
    plan = None
    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        schema_check.errors.append(f"cannot read plan: {exc}")
    schema_ok = False
    missing_dependency = False
    if plan is not None:
        if jsonschema is None:
            schema_check.skipped = ("python package 'jsonschema' is not installed "
                                    "(install it with: py -3 -m pip install --user jsonschema)")
            missing_dependency = True
        else:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            validator = jsonschema.Draft202012Validator(schema)
            for err in sorted(validator.iter_errors(plan), key=lambda e: list(e.absolute_path)):
                path = "$" + "".join(
                    f"[{p}]" if isinstance(p, int) else f".{p}" for p in err.absolute_path
                )
                schema_check.errors.append(f"{path}: {err.message}")
            schema_ok = not schema_check.errors

    later = [
        ("unique_ids", "asset, track, clip, scene, overlay and segment IDs are unique"),
        ("references", "clips, overlays, narration and ducking reference existing assets/tracks of the right type"),
        ("integers", "timeline positions and durations are integer frames"),
        ("source_ranges", "source_out_seconds is greater than source_in_seconds"),
        ("clip_durations", "clip duration_frames matches its source range and speed"),
        ("timeline", "scene order, overlaps, gaps, picture coverage and clip containment"),
        ("runtime", "final scene end matches the target runtime within tolerance"),
        ("rights", "clips only use assets whose rights are resolved"),
        ("narration_sync", "scene timing is reconciled to approved narration"),
        ("files", "relative media paths exist"),
        ("media_probe", "FFprobe durations/streams fit the planned source ranges"),
    ]
    if not schema_ok:
        if plan is None:
            reason = "plan unreadable"
        elif missing_dependency:
            reason = "python package 'jsonschema' is not installed, so the plan could not be validated"
        else:
            reason = "schema validation did not pass; structural checks cannot be trusted"
        for name, description in later:
            check = new(name, description)
            check.skipped = reason
        return checks, meta

    episode = plan["episode"]
    status = episode["status"]
    fps = Fraction(episode["fps_num"], episode["fps_den"])
    meta["fps"] = f'{episode["fps_num"]}/{episode["fps_den"]}'
    meta["rounding_rule"] = "round-half-up: floor(seconds * fps_num / fps_den + 1/2)"
    plan_dir = plan_path.resolve().parent
    not_draft = status in PAST_DRAFT
    editing = status in EDITING

    assets = {a["asset_id"]: a for a in plan["assets"]}
    tracks = {t["track_id"]: t for t in plan["tracks"]}
    segments = {s["segment_id"]: s for s in plan["narration"]["segments"]}

    # 2. Unique IDs -----------------------------------------------------------
    c = new("unique_ids", later[0][1])
    namespaces = {
        "asset_id": [a["asset_id"] for a in plan["assets"]],
        "track_id": [t["track_id"] for t in plan["tracks"]],
        "scene_id": [s["scene_id"] for s in plan["scenes"]],
        "segment_id": [s["segment_id"] for s in plan["narration"]["segments"]],
        "clip_id": [cl["clip_id"] for _, _, cl in iter_visual_clips(plan)]
                   + [cl["clip_id"] for _, _, cl in iter_audio_clips(plan)],
        "overlay_id": [o["overlay_id"] for s in plan["scenes"] for o in s["overlays"]],
    }
    for label, values in namespaces.items():
        seen: set[str] = set()
        for value in values:
            if value in seen:
                c.errors.append(f"duplicate {label}: {value}")
            seen.add(value)

    # 3. References -----------------------------------------------------------
    c = new("references", later[1][1])
    for track in plan["tracks"]:
        ducking = track.get("ducking")
        if ducking and ducking["enabled"]:
            for ref in ducking["duck_under_track_ids"]:
                if ref not in tracks:
                    c.errors.append(f'track {track["track_id"]}: ducking references unknown track {ref}')
                elif tracks[ref]["track_type"] != "audio":
                    c.errors.append(f'track {track["track_id"]}: ducking source {ref} is not an audio track')
            if track["track_type"] != "audio":
                c.errors.append(f'track {track["track_id"]}: ducking is only valid on audio tracks')
    for segment in plan["narration"]["segments"]:
        asset = assets.get(segment["asset_id"])
        if asset is None:
            c.errors.append(f'narration segment {segment["segment_id"]}: unknown asset {segment["asset_id"]}')
        elif asset["asset_type"] != "audio":
            c.errors.append(f'narration segment {segment["segment_id"]}: asset {asset["asset_id"]} is not audio')
    for path, scene, clip in iter_visual_clips(plan):
        asset, track = assets.get(clip["asset_id"]), tracks.get(clip["track_id"])
        if asset is None:
            c.errors.append(f'{path}: unknown asset {clip["asset_id"]}')
        elif asset["asset_type"] not in ("video", "image"):
            c.errors.append(f'{path}: asset {asset["asset_id"]} is {asset["asset_type"]}, not video/image')
        if track is None:
            c.errors.append(f'{path}: unknown track {clip["track_id"]}')
        elif track["track_type"] != "video":
            c.errors.append(f'{path}: track {track["track_id"]} is not a video track')
    for path, scene, clip in iter_audio_clips(plan):
        asset, track = assets.get(clip["asset_id"]), tracks.get(clip["track_id"])
        if asset is None:
            c.errors.append(f'{path}: unknown asset {clip["asset_id"]}')
        elif asset["asset_type"] != "audio":
            c.errors.append(f'{path}: asset {asset["asset_id"]} is {asset["asset_type"]}, not audio')
        if track is None:
            c.errors.append(f'{path}: unknown track {clip["track_id"]}')
        elif track["track_type"] != "audio":
            c.errors.append(f'{path}: track {track["track_id"]} is not an audio track')
    for si, scene in enumerate(plan["scenes"]):
        for seg_id in scene["narration"]["segment_ids"]:
            if seg_id not in segments:
                c.errors.append(f'$.scenes[{si}].narration: unknown segment {seg_id}')
        for oi, overlay in enumerate(scene["overlays"]):
            track = tracks.get(overlay["track_id"])
            if track is None:
                c.errors.append(f'$.scenes[{si}].overlays[{oi}]: unknown track {overlay["track_id"]}')
            elif track["track_type"] != "text":
                c.errors.append(f'$.scenes[{si}].overlays[{oi}]: track {track["track_id"]} is not a text track')

    # 4. Integer frames -------------------------------------------------------
    c = new("integers", later[2][1])
    for key in ("fps_num", "fps_den", "target_duration_frames"):
        if not is_int(episode[key]):
            c.errors.append(f"$.episode.{key} must be an integer, got {episode[key]!r}")
    for si, scene in enumerate(plan["scenes"]):
        for key in ("start_frame", "duration_frames"):
            if not is_int(scene[key]):
                c.errors.append(f"$.scenes[{si}].{key} must be an integer, got {scene[key]!r}")
        for ci, clip in enumerate(scene["clips"] + scene["audio_clips"]):
            for key in ("timeline_start_frame", "duration_frames", "fade_in_frames", "fade_out_frames"):
                if key in clip and not is_int(clip[key]):
                    c.errors.append(f'$.scenes[{si}] clip {clip["clip_id"]}: {key} must be an integer, got {clip[key]!r}')
        for oi, overlay in enumerate(scene["overlays"]):
            for key in ("start_offset_frames", "duration_frames", "fade_in_frames", "fade_out_frames"):
                if key in overlay and not is_int(overlay[key]):
                    c.errors.append(f"$.scenes[{si}].overlays[{oi}].{key} must be an integer, got {overlay[key]!r}")
    for gi, gap in enumerate(plan.get("intentional_gaps", [])):
        for key in ("start_frame", "duration_frames"):
            if not is_int(gap[key]):
                c.errors.append(f"$.intentional_gaps[{gi}].{key} must be an integer, got {gap[key]!r}")
    if c.errors:
        for name, description in later[3:]:
            check = new(name, description)
            check.skipped = "non-integer frame values; timeline arithmetic would be meaningless"
        return checks, meta

    # 5. Source ranges --------------------------------------------------------
    c = new("source_ranges", later[3][1])
    ranges = []
    for path, _, clip in list(iter_visual_clips(plan)) + list(iter_audio_clips(plan)):
        ranges.append((path, clip["source_in_seconds"], clip["source_out_seconds"]))
    for si, segment in enumerate(plan["narration"]["segments"]):
        ranges.append((f"$.narration.segments[{si}]", segment["source_in_seconds"], segment["source_out_seconds"]))
    for path, src_in, src_out in ranges:
        if not (math.isfinite(src_in) and math.isfinite(src_out)) or src_out <= src_in:
            c.errors.append(f"{path}: source_out_seconds ({src_out}) must be greater than source_in_seconds ({src_in})")

    # 6. Clip duration vs source range and speed -------------------------------
    c = new("clip_durations", later[4][1])
    tolerance = 1
    c.notes.append(f"tolerance {tolerance} frame; {meta['rounding_rule']}")
    for path, _, clip in iter_visual_clips(plan):
        asset = assets.get(clip["asset_id"])
        if asset is None or asset["asset_type"] == "image":
            continue  # a still image has no intrinsic duration
        if clip["source_out_seconds"] <= clip["source_in_seconds"]:
            continue
        span = Fraction(repr(clip["source_out_seconds"])) - Fraction(repr(clip["source_in_seconds"]))
        expected = round_half_up(span / Fraction(repr(clip["speed"])) * fps)
        if abs(clip["duration_frames"] - expected) > tolerance:
            c.errors.append(
                f'{path} ({clip["clip_id"]}): duration_frames {clip["duration_frames"]} but source range '
                f'at speed {clip["speed"]} implies {expected} frames')
    for path, _, clip in iter_audio_clips(plan):
        if clip["source_out_seconds"] <= clip["source_in_seconds"]:
            continue
        span = Fraction(repr(clip["source_out_seconds"])) - Fraction(repr(clip["source_in_seconds"]))
        expected = round_half_up(span * fps)
        if abs(clip["duration_frames"] - expected) > tolerance:
            c.errors.append(
                f'{path} ({clip["clip_id"]}): duration_frames {clip["duration_frames"]} but source range '
                f"implies {expected} frames")

    # 7. Timeline structure ---------------------------------------------------
    c = new("timeline", later[5][1])
    scenes = plan["scenes"]
    gaps = [(g["start_frame"], g["start_frame"] + g["duration_frames"]) for g in plan.get("intentional_gaps", [])]

    def gap_covers(start: int, end: int) -> bool:
        return any(g0 <= start and end <= g1 for g0, g1 in gaps)

    previous_end = 0
    for si, scene in enumerate(scenes):
        start, end = scene["start_frame"], scene["start_frame"] + scene["duration_frames"]
        if start < previous_end:
            c.errors.append(f'$.scenes[{si}] ({scene["scene_id"]}): starts at {start}, before the previous scene ends at {previous_end} '
                            "(scenes must be ordered and must not overlap)")
        elif start > previous_end and not gap_covers(previous_end, start):
            c.errors.append(f'$.scenes[{si}] ({scene["scene_id"]}): undeclared gap of {start - previous_end} frames '
                            f"[{previous_end}, {start}); declare it in intentional_gaps or close it")
        previous_end = max(previous_end, end)

        for path, _, clip in [x for x in iter_visual_clips(plan) if x[1] is scene] + \
                             [x for x in iter_audio_clips(plan) if x[1] is scene]:
            c0, c1 = clip["timeline_start_frame"], clip["timeline_start_frame"] + clip["duration_frames"]
            if c0 < start or c1 > end:
                c.errors.append(f'{path} ({clip["clip_id"]}): frames [{c0}, {c1}) fall outside scene {scene["scene_id"]} [{start}, {end})')
        for oi, overlay in enumerate(scene["overlays"]):
            if overlay["start_offset_frames"] + overlay["duration_frames"] > scene["duration_frames"]:
                c.errors.append(f'$.scenes[{si}].overlays[{oi}] ({overlay["overlay_id"]}): ends after scene {scene["scene_id"]} ends')

        # Picture coverage: picture-role tracks must cover the scene.
        picture = sorted(
            (cl["timeline_start_frame"], cl["timeline_start_frame"] + cl["duration_frames"])
            for cl in scene["clips"] if tracks.get(cl["track_id"], {}).get("role") == "picture")
        cursor = start
        for c0, c1 in picture:
            if c0 > cursor and not gap_covers(cursor, c0):
                c.errors.append(f'scene {scene["scene_id"]}: no picture clip for frames [{cursor}, {c0}); declare an intentional gap or add a clip')
            cursor = max(cursor, c1)
        if cursor < end and not gap_covers(cursor, end):
            c.errors.append(f'scene {scene["scene_id"]}: no picture clip for frames [{cursor}, {end}); declare an intentional gap or add a clip')
        if not picture and not gap_covers(start, end):
            pass  # already reported by the coverage loop above

    # Same-track overlaps need an explanation.
    for kind, iterator in (("visual", iter_visual_clips), ("audio", iter_audio_clips)):
        by_track: dict[str, list] = {}
        for path, _, clip in iterator(plan):
            by_track.setdefault(clip["track_id"], []).append((clip["timeline_start_frame"], path, clip))
        for track_id, items in by_track.items():
            items.sort(key=lambda item: (item[0], item[2].get("order", 0)))
            for (s0, p0, c0), (s1, p1, c1) in zip(items, items[1:]):
                end0 = s0 + c0["duration_frames"]
                if s1 < end0:
                    explained = bool(c1.get("overlap_reason")) or bool(c0.get("overlap_reason"))
                    if kind == "visual":
                        explained = explained or c1["transition_in"] in OVERLAP_TRANSITIONS
                    else:
                        explained = explained or (c1.get("fade_in_frames", 0) > 0 and c0.get("fade_out_frames", 0) > 0)
                    if not explained:
                        c.errors.append(
                            f'track {track_id}: {c0["clip_id"]} and {c1["clip_id"]} overlap by {end0 - s1} frames '
                            "without overlap_reason, a dissolve/continuous_move transition, or crossfading fades")

    # 8. Runtime --------------------------------------------------------------
    c = new("runtime", later[6][1])
    final_end = max(s["start_frame"] + s["duration_frames"] for s in scenes)
    target = episode["target_duration_frames"]
    allowed = episode.get("runtime_tolerance_frames", max(1, round(float(fps))))
    c.notes.append(f"final scene end {final_end}, target {target}, tolerance {allowed} frames")
    if abs(final_end - target) > allowed:
        c.problem(not_draft, f"final scene end is frame {final_end} ({final_end / float(fps):.2f}s) but target is "
                              f"{target} ({target / float(fps):.2f}s); difference exceeds {allowed} frames"
                              + ("" if not_draft else " (warning only while status is draft)"))

    # 9. Rights ---------------------------------------------------------------
    c = new("rights", later[7][1])
    used: dict[str, list[str]] = {}
    for path, _, clip in list(iter_visual_clips(plan)) + list(iter_audio_clips(plan)):
        used.setdefault(clip["asset_id"], []).append(clip["clip_id"])
    for segment in plan["narration"]["segments"]:
        used.setdefault(segment["asset_id"], []).append(segment["segment_id"])
    for asset_id, users in sorted(used.items()):
        asset = assets.get(asset_id)
        if asset is None:
            continue  # reported by references
        where = ", ".join(users)
        if asset["rights_status"] == "blocked":
            c.errors.append(f"asset {asset_id} is blocked but used by {where}")
        elif asset["rights_status"] == "needs_review":
            c.problem(not_draft, f"asset {asset_id} still needs_review but used by {where}"
                                  + ("" if not_draft else " (warning only while status is draft)"))
        elif asset["rights_status"] == "cleared" and not (asset.get("license") and asset.get("creator")):
            c.warnings.append(f"asset {asset_id} is marked cleared but license or creator is empty")
    c.notes.append("This validator cannot confirm that a license is real; that stays a human review item.")

    # 10. Narration reconciliation ---------------------------------------------
    c = new("narration_sync", later[8][1])
    if editing and not plan["narration"]["approved"]:
        c.errors.append(f"status is {status} but narration.approved is false; timing must follow approved narration audio")
    elif not plan["narration"]["approved"]:
        c.warnings.append("narration is not approved; all scene timing is a draft estimate")
    for si, scene in enumerate(scenes):
        narration = scene["narration"]
        if scene["timing_status"] == "draft":
            c.problem(editing, f'scene {scene["scene_id"]}: timing_status is draft'
                               + ("" if editing else " (warning only before in_edit)"))
        if not narration["segment_ids"] and not narration.get("silent_beat_purpose"):
            c.problem(scene["timing_status"] == "reconciled",
                      f'scene {scene["scene_id"]}: no narration segments and no silent_beat_purpose')

    # 11. Files ---------------------------------------------------------------
    c = new("files", later[9][1])
    resolved: dict[str, Path] = {}
    for index, asset in enumerate(plan["assets"]):
        raw = asset["path"]
        if Path(raw).is_absolute() or raw.startswith("/"):
            c.errors.append(f'$.assets[{index}] ({asset["asset_id"]}): path must be relative to the plan folder, got {raw}')
            continue
        target_path = (plan_dir / raw).resolve()
        resolved[asset["asset_id"]] = target_path
        if not target_path.is_file():
            c.problem(not_draft, f'$.assets[{index}] ({asset["asset_id"]}): file not found: {raw}'
                                  + ("" if not_draft else " (warning only while status is draft)"))
    for label, raw in (("episode.style_guide", episode["style_guide"]),
                       ("global_style.lut_path", plan["global_style"].get("lut_path"))):
        if raw and not (plan_dir / raw).resolve().is_file():
            c.warnings.append(f"{label}: file not found: {raw}")

    # 12. Media probe ---------------------------------------------------------
    c = new("media_probe", later[10][1])
    if not probe:
        c.skipped = "probing disabled with --no-probe"
    elif shutil.which("ffprobe") is None:
        c.skipped = "ffprobe is not installed"
    else:
        info_by_asset: dict[str, dict] = {}
        for asset_id, file_path in resolved.items():
            asset = assets[asset_id]
            if asset["asset_type"] not in ("video", "audio", "image") or not file_path.is_file():
                continue
            info = probe_media(file_path)
            if info is None:
                c.errors.append(f"asset {asset_id}: ffprobe could not read {asset['path']}")
                continue
            info_by_asset[asset_id] = info
            declared = asset.get("probe", {})
            if declared.get("duration_seconds") is not None and info["duration"] is not None \
                    and abs(declared["duration_seconds"] - info["duration"]) > 0.05:
                c.warnings.append(f"asset {asset_id}: declared duration {declared['duration_seconds']}s but probed {info['duration']:.3f}s")
            for key in ("width", "height"):
                if declared.get(key) is not None and info[key] is not None and declared[key] != info[key]:
                    c.warnings.append(f"asset {asset_id}: declared {key} {declared[key]} but probed {info[key]}")
        c.notes.append(f"probed {len(info_by_asset)} of {len(assets)} assets")
        if not info_by_asset and not c.errors:
            c.skipped = "no media files exist yet, so nothing could be probed"

        def check_range(path: str, clip: dict, wants_video: bool | None, wants_audio: bool | None):
            asset_id = clip["asset_id"]
            info = info_by_asset.get(asset_id)
            asset = assets.get(asset_id)
            if info is None or asset is None:
                return
            if asset["asset_type"] != "image" and info["duration"] is not None \
                    and clip["source_out_seconds"] > info["duration"] + SOURCE_EPSILON_SECONDS:
                c.errors.append(f'{path} ({clip.get("clip_id", asset_id)}): source_out_seconds {clip["source_out_seconds"]} '
                                f'exceeds probed duration {info["duration"]:.3f}s of {asset["path"]}')
            if wants_video and not info["has_video"]:
                c.errors.append(f'{path} ({clip.get("clip_id", asset_id)}): {asset["path"]} has no video stream')
            if wants_audio and not info["has_audio"]:
                c.errors.append(f'{path} ({clip.get("clip_id", asset_id)}): {asset["path"]} has no audio stream')
            if wants_video and info["fps"] and abs(info["fps"] - float(fps)) > 0.01 and asset["asset_type"] == "video":
                c.warnings.append(f'{path} ({clip.get("clip_id", asset_id)}): source is {info["fps"]:.3f} fps but the project is {float(fps):.3f} fps; '
                                  "the editor must convert the frame rate explicitly")

        for path, _, clip in iter_visual_clips(plan):
            check_range(path, clip, True if assets.get(clip["asset_id"], {}).get("asset_type") != "image" else None, None)
        for path, _, clip in iter_audio_clips(plan):
            check_range(path, clip, None, True)
        for si, segment in enumerate(plan["narration"]["segments"]):
            check_range(f"$.narration.segments[{si}]", segment, None, True)

    return checks, meta


def render_text(checks: list[Check], meta: dict) -> str:
    symbols = {"pass": "PASS", "warn": "WARN", "fail": "FAIL", "skipped": "SKIP"}
    lines = [f"Plan: {meta['plan']}"]
    if "fps" in meta:
        lines.append(f"Frame rate {meta['fps']}; seconds to frames: {meta['rounding_rule']}")
    lines.append("")
    for check in checks:
        lines.append(f"[{symbols[check.status]}] {check.name}: {check.description}")
        if check.skipped:
            lines.append(f"       skipped: {check.skipped}")
        for note in check.notes:
            lines.append(f"       note: {note}")
        for message in check.errors:
            lines.append(f"       error: {message}")
        for message in check.warnings:
            lines.append(f"       warning: {message}")
    counts = {key: sum(1 for c in checks if c.status == key) for key in symbols}
    lines.append("")
    lines.append(f"Summary: {counts['pass']} passed, {counts['warn']} with warnings, "
                 f"{counts['fail']} failed, {counts['skipped']} skipped (not run, not passed).")
    lines.append("Human review is still required for licenses, facts, aesthetics and visual/narration match.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--no-probe", action="store_true", help="skip FFprobe checks")
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    args = parser.parse_args(argv)
    if not args.plan.is_file():
        print(f"plan not found: {args.plan}", file=sys.stderr)
        return 2
    checks, meta = run_validation(args.plan, args.schema, probe=not args.no_probe)
    if args.json:
        print(json.dumps({"meta": meta, "checks": [c.to_dict() for c in checks]}, indent=2))
    else:
        print(render_text(checks, meta))
    if checks[0].errors and not checks[0].skipped and "cannot read plan" in " ".join(checks[0].errors):
        return 2
    return 1 if any(c.status == "fail" for c in checks) else 0


if __name__ == "__main__":
    sys.exit(main())
