#!/usr/bin/env python3
"""FFmpeg route of workflow/ASSEMBLY.md: render a review video from a validated plan.

    python3 render_review.py episodes/<slug>/EDIT_PLAN.json OUTPUT.mp4 [--height 360] [--no-text]

The output is a RENDER ONLY. It is not an editable CapCut project. The plan is
validated first and the render is refused if any check fails.

What it renders: picture clips (trim, speed, fit mode, layer order), audio clips
(gain, fades, track default gain), plan-driven music ducking, text overlays when a
font file is found, and the LUT when the .cube file exists.
What it does not render (reported at the end, never silently dropped): dissolve and
continuous_move transitions (rendered as hard cuts), ducking attack/release
shaping, camera movement fields, and graphics.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "timeline"))
import validate_plan as vp  # noqa: E402


def esc_text(text: str) -> str:
    for ch in ("\\", ":", "'", "%"):
        text = text.replace(ch, "\\" + ch)
    return text.replace("\n", " ")


def find_font(family: str) -> str | None:
    """Find a font file for a family name. Uses fontconfig where present, else scans
    the standard font folders (Windows/macOS) for a file name containing the family."""
    if shutil.which("fc-match"):
        out = subprocess.run(["fc-match", "-f", "%{family}|%{file}", family],
                             capture_output=True, text=True).stdout
        if "|" in out:
            matched, file = out.split("|", 1)
            if family.split()[0].lower() in matched.lower() and Path(file).is_file():
                return file
        return None
    wanted = family.lower().replace(" ", "")
    folders = [Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts",
               Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Windows" / "Fonts",
               Path.home() / "Library" / "Fonts", Path("/Library/Fonts"), Path("/System/Library/Fonts")]
    for folder in folders:
        if folder.is_dir():
            for file in sorted(folder.iterdir()):
                if file.suffix.lower() in (".ttf", ".otf") and wanted in file.stem.lower().replace(" ", "").replace("-", ""):
                    return str(file)
    return None


def esc_filter_path(path: str) -> str:
    """Escape a file path for use inside an FFmpeg filter option (drive colons, backslashes)."""
    return path.replace("\\", "/").replace(":", "\\:").replace("'", "\\'")


def anchor_expr(placement: dict, width: int, height: int) -> tuple[str, str]:
    x = f"{placement['x']}*w"
    y = f"{placement['y']}*h"
    anchor = placement["anchor"]
    if anchor.endswith("center") or anchor == "center":
        x = f"{x}-text_w/2"
    elif anchor.endswith("right"):
        x = f"{x}-text_w"
    if anchor.startswith("center") or anchor == "center":
        y = f"{y}-text_h/2"
    elif anchor.startswith("bottom"):
        y = f"{y}-text_h"
    return x, y


def build(plan: dict, plan_dir: Path, out_height: int, with_text: bool):
    ep = plan["episode"]
    fps = ep["fps_num"] / ep["fps_den"]
    fps_str = f"{ep['fps_num']}/{ep['fps_den']}"
    width = ep["width"]
    height = ep["height"]
    out_w = max(2, round(width * out_height / height / 2) * 2)
    out_h = out_height
    total_frames = max(s["start_frame"] + s["duration_frames"] for s in plan["scenes"])
    total_s = total_frames / fps
    assets = {a["asset_id"]: a for a in plan["assets"]}
    tracks = {t["track_id"]: t for t in plan["tracks"]}
    unsupported: list[str] = []

    inputs: list[str] = []
    input_index: dict[tuple, int] = {}

    def add_input(asset_id: str, still_seconds: float | None = None) -> int:
        key = (asset_id, still_seconds)
        if key not in input_index:
            path = str((plan_dir / assets[asset_id]["path"]).resolve())
            if still_seconds is not None:
                inputs.extend(["-loop", "1", "-framerate", fps_str, "-t", f"{still_seconds:.6f}", "-i", path])
            else:
                inputs.extend(["-i", path])
            input_index[key] = len(input_index)
        return input_index[key]

    filters = [f"color=c=black:s={out_w}x{out_h}:r={fps_str}:d={total_s:.6f},format=yuv420p[base0]"]
    label = "base0"

    visual = []
    for scene in plan["scenes"]:
        for clip in scene["clips"]:
            layer = tracks[clip["track_id"]]["layer_order"]
            visual.append((layer, clip["timeline_start_frame"], clip["order"], clip))
    visual.sort(key=lambda item: (item[0], item[1], item[2]))
    for n, (_, _, _, clip) in enumerate(visual):
        asset = assets[clip["asset_id"]]
        start_s = clip["timeline_start_frame"] / fps
        dur_s = clip["duration_frames"] / fps
        for side in ("transition_in", "transition_out"):
            if clip[side] in ("short_dissolve", "continuous_move"):
                unsupported.append(f'{clip["clip_id"]}.{side}={clip[side]} rendered as a hard cut')
        if asset["asset_type"] == "image":
            idx = add_input(clip["asset_id"], dur_s)
            chain = f"[{idx}:v]trim=duration={dur_s:.6f},setpts=PTS-STARTPTS"
        else:
            idx = add_input(clip["asset_id"])
            span = dur_s * clip["speed"]
            chain = (f"[{idx}:v]trim=start={clip['source_in_seconds']:.6f}:duration={span:.6f},"
                     f"setpts=(PTS-STARTPTS)/{clip['speed']}")
        chain += f",fps={fps_str}"
        fit = clip["fit_mode"]
        if fit == "contain":
            chain += f",scale={out_w}:{out_h}:force_original_aspect_ratio=decrease,pad={out_w}:{out_h}:(ow-iw)/2:(oh-ih)/2:color=black"
        elif fit == "cover":
            chain += f",scale={out_w}:{out_h}:force_original_aspect_ratio=increase,crop={out_w}:{out_h}"
        else:
            chain += f",pad=max(iw\\,{out_w}):max(ih\\,{out_h}):(ow-iw)/2:(oh-ih)/2:color=black,crop={out_w}:{out_h}"
        chain += f",setsar=1,format=yuv420p,setpts=PTS+{start_s:.6f}/TB[v{n}]"
        filters.append(chain)
        nxt = f"base{n + 1}"
        filters.append(f"[{label}][v{n}]overlay=eof_action=pass:enable='between(t,{start_s:.6f},{start_s + dur_s - 0.000001:.6f})'[{nxt}]")
        label = nxt

    if with_text:
        font_cache: dict[str, str | None] = {}
        for scene in plan["scenes"]:
            for overlay in scene["overlays"]:
                family = overlay["style"]["font_family"]
                if family not in font_cache:
                    font_cache[family] = find_font(family)
                if font_cache[family] is None:
                    unsupported.append(f'overlay {overlay["overlay_id"]} skipped: font "{family}" not found on this machine')
                    continue
                start_s = (scene["start_frame"] + overlay["start_offset_frames"]) / fps
                end_s = start_s + overlay["duration_frames"] / fps
                x, y = anchor_expr(overlay["placement"], out_w, out_h)
                scale = out_h / height
                style = overlay["style"]
                parts = [f"fontfile='{esc_filter_path(font_cache[family])}'", f"text='{esc_text(overlay['text'])}'",
                         f"fontsize={style['size_px'] * scale:.2f}",
                         f"fontcolor={style['fill_hex']}@{overlay['opacity']}",
                         f"x={x}", f"y={y}", f"enable='between(t,{start_s:.6f},{end_s:.6f})'"]
                shadow = style.get("shadow")
                if shadow:
                    parts += [f"shadowcolor={shadow['color_hex']}", f"shadowx={shadow['offset_x_px'] * scale:.1f}",
                              f"shadowy={shadow['offset_y_px'] * scale:.1f}"]
                filters.append(f"[{label}]drawtext={':'.join(parts)}[t{overlay['overlay_id']}]")
                label = f"t{overlay['overlay_id']}"
                if overlay.get("fade_in_frames") or overlay.get("fade_out_frames"):
                    unsupported.append(f'overlay {overlay["overlay_id"]}: text fades not rendered')
    else:
        unsupported.append("text overlays skipped (--no-text)")

    lut = plan["global_style"].get("lut_path")
    lut_file = (plan_dir / lut).resolve() if lut else None
    if lut_file and lut_file.is_file():
        strength = plan["global_style"].get("lut_strength", 1.0)
        lut_escaped = esc_filter_path(str(lut_file))
        filters.append(f"[{label}]split[la][lb]")
        filters.append(f"[lb]lut3d=file='{lut_escaped}'[lc]")
        filters.append(f"[la][lc]blend=all_opacity={strength}[graded]")
        label = "graded"
    elif lut:
        unsupported.append(f"LUT not applied: file not found ({lut})")
    filters.append(f"[{label}]null[vout]")

    # Audio --------------------------------------------------------------------
    bus_labels: dict[str, str] = {}
    audio_by_track: dict[str, list[dict]] = {}
    for scene in plan["scenes"]:
        for clip in scene["audio_clips"]:
            audio_by_track.setdefault(clip["track_id"], []).append(clip)
    for track_id, clips in audio_by_track.items():
        labels = []
        for k, clip in enumerate(sorted(clips, key=lambda c: c["timeline_start_frame"])):
            idx = add_input(clip["asset_id"])
            dur_s = clip["duration_frames"] / fps
            start_ms = round(clip["timeline_start_frame"] / fps * 1000)
            gain = clip["gain_db"] + tracks[track_id].get("default_gain_db", 0)
            chain = (f"[{idx}:a]atrim=start={clip['source_in_seconds']:.6f}:duration={dur_s:.6f},asetpts=PTS-STARTPTS,"
                     f"volume={gain}dB")
            if clip.get("fade_in_frames"):
                chain += f",afade=t=in:st=0:d={clip['fade_in_frames'] / fps:.6f}"
            if clip.get("fade_out_frames"):
                chain += f",afade=t=out:st={dur_s - clip['fade_out_frames'] / fps:.6f}:d={clip['fade_out_frames'] / fps:.6f}"
            chain += f",aformat=sample_rates=48000:channel_layouts=stereo,adelay={start_ms}|{start_ms}[a_{track_id}_{k}]"
            filters.append(chain)
            labels.append(f"[a_{track_id}_{k}]")
        if len(labels) == 1:
            filters.append(f"{labels[0]}anull[bus_{track_id}]")
        else:
            filters.append(f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0:duration=longest[bus_{track_id}]")
        bus_labels[track_id] = f"bus_{track_id}"

    for track_id, track in tracks.items():
        ducking = track.get("ducking")
        if not ducking or not ducking["enabled"] or track_id not in bus_labels:
            continue
        ranges = []
        for source_id in ducking["duck_under_track_ids"]:
            for clip in audio_by_track.get(source_id, []):
                s0 = clip["timeline_start_frame"] / fps
                ranges.append((s0, s0 + clip["duration_frames"] / fps))
        chain = f"[{bus_labels[track_id]}]"
        steps = [f"volume={ducking['attenuation_db']}dB:enable='between(t,{a:.6f},{b:.6f})'" for a, b in ranges]
        if steps:
            filters.append(chain + ",".join(steps) + f"[duck_{track_id}]")
            bus_labels[track_id] = f"duck_{track_id}"
        unsupported.append(f"track {track_id}: ducking follows narration clip ranges; attack/release not shaped")

    if bus_labels:
        joined = "".join(f"[{lbl}]" for lbl in bus_labels.values())
        filters.append(f"{joined}amix=inputs={len(bus_labels)}:normalize=0:duration=longest,"
                       f"apad=whole_dur={total_s:.6f},atrim=duration={total_s:.6f},alimiter=limit=0.95[aout]")
    else:
        filters.append(f"anullsrc=r=48000:cl=stereo,atrim=duration={total_s:.6f}[aout]")
        unsupported.append("plan has no audio clips; silent audio track added")

    unsupported += [f'scene {s["scene_id"]}: movement "{s["edit"]["movement"]}" is a direction note, not rendered'
                    for s in plan["scenes"] if s["edit"]["movement"] != "static"]
    unsupported += [f'scene {s["scene_id"]}: graphic "{s["edit"]["graphic"]}" not rendered'
                    for s in plan["scenes"] if s["edit"].get("graphic")]
    return inputs, filters, unsupported, (out_w, out_h), total_frames


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("plan", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--height", type=int, default=360, help="review render height in pixels (default 360)")
    parser.add_argument("--no-text", action="store_true")
    args = parser.parse_args(argv)

    if not (shutil.which("ffmpeg") and shutil.which("ffprobe")):
        print("ffmpeg and ffprobe are required", file=sys.stderr)
        return 2
    checks, meta = vp.run_validation(args.plan)
    failed = [c for c in checks if c.status == "fail"]
    skipped = [c.name for c in checks if c.status == "skipped" and c.name != "media_probe"]
    if failed or skipped:
        print(vp.render_text(checks, meta), file=sys.stderr)
        print("\nRefusing to render: the plan did not validate.", file=sys.stderr)
        return 1

    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    inputs, filters, unsupported, (w, h), frames = build(plan, args.plan.resolve().parent, args.height, not args.no_text)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(filters),
           "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "28",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(args.output)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        return 1

    info = vp.probe_media(args.output)
    ep = plan["episode"]
    report = {
        "kind": "review_render",
        "editable_capcut_project": False,
        "output": str(args.output),
        "planned_frames": frames,
        "planned_seconds": round(frames * ep["fps_den"] / ep["fps_num"], 3),
        "probed_duration_seconds": info and info["duration"],
        "dimensions": f"{w}x{h}",
        "frame_rate": f'{ep["fps_num"]}/{ep["fps_den"]}',
        "loudness_and_true_peak": "not measured",
        "not_rendered_or_approximated": sorted(set(unsupported)),
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
