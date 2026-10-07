# Implementation Report: Plan v2, Validator and Review Renderer

Responds to the "Implementation requirements" in CLAUDE_REVIEW_RESPONSE.md.

## Implemented
- `timeline/EDIT_PLAN.schema.json` (plan version 2.0): closed enums, `additionalProperties: false` throughout, rational `fps_num`/`fps_den`, integer-frame timeline, `tracks` with track-level ducking, ordered visual clips with source in/out, speed, fit mode and transitions, audio clips with gain and fades, text overlays with style, placement, opacity and fades, narration segments, `intentional_gaps`, and `timing_status` per scene. `movement` and `shot_type` set to `other` require an explanation.
- `timeline/EDIT_PLAN_TEMPLATE.json`: a version 2 example that passes the schema. Paths are written for a copy placed in `episodes/<slug>/`.
- `timeline/validate_plan.py`: 12 checks reported as pass, warn, fail or skipped with JSON paths. A check that could not run is reported as skipped, never as passed.
- `timeline/TIMELINE_SPEC.md`: clarified overlap rule, clip-duration rule, track-level-only ducking, validator checks 8-13, and draft-versus-later status behaviour.
- `workflow/probe_tools.py`: reports FFmpeg, FFprobe, PySceneDetect, Whisper CLI, jsonschema and CapCut files if present.
- `workflow/render_review.py`: render-only FFmpeg route. Output is never described as a CapCut project.
- Root `CLAUDE.md` is now a short pointer. Source media was not touched.

## Tested here (Linux, FFmpeg 6.1.1, Python 3.11, jsonschema 4.26)
- `python3 -m unittest discover -s fabrica-videos/timeline/tests` runs 24 tests against synthetic media: valid plan, duplicate IDs, bad references, non-integer frames, source ranges, clip duration versus speed, undeclared gaps, scene overlaps, picture coverage, same-track overlap with and without a reason, runtime mismatch, rights, unreconciled narration, silent-beat purpose, source range beyond probed duration, missing files in draft versus later status, skipped probing, and the rounding rule.
- `python3 -m unittest discover -s fabrica-videos/workflow/tests` runs 4 tests: a smoke render whose duration, size, frame rate and audio match the plan, refusal to render an invalid plan, reporting of unsupported features, and a text overlay with an installed font.
- Manual check: a frame with a text overlay differs from the same frame rendered with `--no-text`.

## Not tested, or not possible here
- **CapCut:** no CapCut Desktop, CapCut MCP server or Computer Use exists in this environment. No native CapCut project was created. The CapCut route in `workflow/ASSEMBLY.md` is unverified and must be probed and smoke-tested on the user's machine.
- **LUT:** `industrial-cold-warm-core.cube` was not provided. The LUT code path is written (`lut3d` with strength blending) but never ran against a real LUT.
- **Fonts:** Inter and Cormorant Garamond are not installed here; only the DejaVu Sans fallback path was exercised.
- **Not rendered by `render_review.py`:** dissolve and continuous_move transitions (hard cuts), ducking attack/release shaping (ducking follows narration clip ranges), camera movement, graphics, and overlay fades. These are listed in the render report each time.
- **Loudness and true peak** are not measured.
- **Phase 1 tools:** PySceneDetect and a transcription tool are not installed here, so reference analysis was not run. No reference videos were supplied.
- **Not decided by a script:** licenses, factual accuracy, aesthetics, and whether a visual matches the narration remain human review items.

## Open items for the user
- Provide the LUT file, 3-5 full reference videos or authorized local copies, and real episode media.
- Confirm whether CapCut Desktop, a CapCut MCP server or Computer Use is available on the editing machine.
- Install `pip install jsonschema` where the validator will run.
