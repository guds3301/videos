# Timeline Data and Validation Specification

This document defines the minimum plan required for reproducible video assembly. Use it when upgrading EDIT_PLAN_TEMPLATE.json and EDIT_PLAN.schema.json.

## Clock and frame rules
- Set project frame rate as rational values: fps_num and fps_den. Example: 24/1 or 30000/1001.
- All timeline positions and durations use integer frames: start_frame and duration_frames.
- Use half-open ranges [start, end). A clip occupying frames 100-124 has start_frame 100 and duration_frames 24.
- Seconds may be used for source-media in/out locations because source files may have a different frame rate. The validator probes source metadata and checks the source range.
- Seconds are derived values for display; never use floating-point seconds as the authoritative timeline clock.
- Convert seconds to frames with one documented rounding rule, round-half-up. Record the conversion in the validator report.
- Do not mix frame rates within a timeline without an explicit frame-rate conversion rule.

## Plan shape
Top-level objects:
- plan_version, episode, global_style, tracks, assets, narration, scenes, unresolved_items, deliverables.
- episode declares ID, language (English by default; specify the accent), rational frame rate, target duration in frames, dimensions, style guide path, and status. The episode directory is the folder containing the plan.
- assets is a registry. Each asset has a unique asset_id, relative path, media type, creator/source/license, rights status, and probe metadata.
- tracks defines stable track_id, track_type, role, layer order, and default audio settings.
- narration declares approved script, master audio or approved audio segments, voice/accent, and pronunciation notes.
- scenes are ordered narrative sections; each has start_frame, duration_frames, act, purpose, narration segment references, ordered visual clips, audio clips, overlays, edit instructions, and verification notes.
- unresolved_items keeps missing facts, media, or permissions visible.
- deliverables declares requested editable project and render locations/format.

## Source clips
Every picture or sound use is a separate clip object, even when multiple clips belong to one scene. Required fields:
- clip_id: unique within the plan.
- asset_id: existing asset registry entry.
- order: integer z/order for items beginning at the same timeline position.
- track_id: existing track.
- source_in_seconds and source_out_seconds: finite non-negative numbers; out > in.
- timeline_start_frame and duration_frames: integer timeline values.
- fit_mode for picture clips: contain, cover, or native; do not use an undocumented value.
- speed: positive number; default 1.0.
- transition_in and transition_out: enum from the style guide.
- overlap_reason (optional): required to explain a same-track overlap unless the later clip uses a short_dissolve or continuous_move transition_in. Clips on different tracks may overlap freely because they are layers.
- duration_frames must equal round-half-up((source_out - source_in) / speed * fps) within 1 frame. Still images have no intrinsic duration and are exempt.

## Narration timing
Before voice generation, scene timing is a draft estimate only. After voice approval:
- Probe the generated narration file(s).
- Store exact source ranges for narration segments.
- Make scene boundaries follow approved phrase/paragraph markers where possible.
- Add explicit room-tone/silence segments for deliberate pauses; do not create unexplained gaps.
- Preserve a single continuous master narration track when it simplifies sync; scene references may point to its source ranges.
- Narration may be absent for an intentional silent beat, but the plan must mark its purpose.

## Audio and mix
Each audio clip requires clip_id, asset_id, track_id, source range, timeline placement, gain_db, and optional fade lengths in frames. Ducking is defined only at track level (never per scene) as an object with enabled, duck_under_track_ids, attenuation_db, attack_ms, release_ms, and optional threshold_db. Use conservative starting values and adjust by listening.

Final mix metadata should include measured integrated loudness and true peak when a meter is available. Proposed targets are advisory; do not misreport measured values.

## Text and graphic overlays
Use start_offset_frames and duration_frames relative to the scene. Include:
- role enum: title, chapter, label, measurement, subtitle, source_credit, other.
- style: font_family, weight, size_px, fill_hex, optional outline/shadow/background.
- placement: normalized x/y, anchor, alignment, safe_margin.
- opacity and fade_in_frames/fade_out_frames.
The validator checks values and timing but cannot judge whether a text block obscures important visual evidence.

## Controlled values
Use enums for scene acts, asset types, track roles, fit modes, movement, and transitions. Initial transition enum: hard_cut, motivated_match_cut, short_dissolve, continuous_move, none. Initial movement enum: static, slow_push_in, slow_pull_out, slow_pan, slow_tilt, macro_track, diagram_reveal, other (with explanation). Use other only with a non-empty explanation.

## Validator responsibilities
JSON Schema validates structure and allowed values. The local validator must additionally:
1. Parse the plan and report JSON Schema errors with a JSON path.
2. Reject duplicate asset IDs and clip IDs.
3. Resolve every relative path against the plan's directory; report missing files.
4. Probe each media file with FFprobe when installed; compare source ranges to actual duration.
5. Reject references to unknown assets/tracks.
6. Confirm timeline values are integers and positive where required.
7. Confirm source_out_seconds > source_in_seconds.
8. Check scene order, overlaps, and gaps. Allow only gaps declared in intentional_gaps; explain any same-track overlap. Picture-role tracks must cover every scene, and every clip and overlay must lie inside its scene.
9. Check target runtime against the final scene end within a configurable tolerance (default one second).
10. Check clip duration_frames against the source range and speed (see Source clips).
11. Reject blocked assets always; reject needs_review assets once episode status is past draft (warn while draft).
12. Require approved narration and reconciled scene timing once status is in_edit, review, or final; an empty narration scene needs silent_beat_purpose.
13. Report whether checks were run, skipped due to missing tools, or failed. Never claim an unrun check passed.

### Draft versus later statuses
While episode.status is draft, missing media files, unresolved rights, unapproved narration, and a runtime mismatch are warnings. From approved onward, missing files, rights, and runtime mismatch are failures; from in_edit onward, unreconciled narration timing is also a failure. Structural errors (schema, duplicate IDs, bad references, non-integer frames, gaps and overlaps) fail at every status.

### Running it
`python3 timeline/validate_plan.py episodes/<slug>/EDIT_PLAN.json` (add `--no-probe` to skip FFprobe, `--json` for machine output). Requires the Python package jsonschema; FFprobe is optional but its absence is reported as skipped. Tests: `python3 -m unittest discover -s timeline/tests`.

### Template paths
EDIT_PLAN_TEMPLATE.json lives in timeline/, but its style_guide and lut_path are written for a copy placed in episodes/<slug>/. Validating the template in place therefore warns that those files are not found; that is expected.

The validator cannot confirm a media license, factual accuracy, aesthetic quality, or whether the chosen visual matches the narration. Those remain explicit human/research review items.
