# Decisions and Handoff for Claude Code

These are the user's decisions and the next implementation tasks. Do not ask the resolved questions again.

## Decisions
1. The channel language is **English**. Narration, titles, captions, and on-screen copy default to English. Specify the English accent per episode.
2. The user asked to organize documents into folders within fabrica-videos/. This organization is authorized. Do not move files outside that directory, do not move source media, and do not replace the root CLAUDE.md; keep it as a short pointer.
3. Use this layout:
   - style/ for the visual style guide.
   - references/ for reference analysis and local analysis tooling.
   - workflow/ for production and assembly instructions.
   - timeline/ for schema, plan template, and frame-accurate timeline specification.
   - episodes/<episode-slug>/ for each episode's brief, script, sources, asset log, plan, media, audio, and renders.
4. The workspace root is the repository root (earlier drafts called it the jarvis folder). Paths inside an episode plan are relative to that plan's directory. Use forward slashes in JSON.
   - Style guide: ../../style/STYLE_GUIDE.md
   - Root LUT: ../../../industrial-cold-warm-core.cube
   - Episode media: media/<filename>
5. No paid service/API calls, outside publication, or destructive overwrite without explicit approval.

## Accepted critique
The previous review correctly found that the first timeline template lacked source in/out points, clip order, audio mix data, text placement, frame rules, a tested assembly route, and a local reference-analysis workflow. The JSON Schema was too permissive. A schema alone cannot verify file existence, cross-references, probed media durations, runtime continuity, or aesthetic accuracy; a local validator and human review are needed.

## Implementation requirements
- Upgrade the plan format to version 2. A scene contains an ordered list of visual clips with unique clip IDs, asset IDs, source_in_seconds, source_out_seconds, track IDs, timeline_start_frame, duration_frames, speed, fit mode, and transitions.
- The project timeline uses integer frames and rational fps_num/fps_den. Source in/out may use seconds because source frame rates vary. Document one rounding rule.
- Draft scene timings may precede narration. Final timings must be reconciled to approved narration audio and phrase/paragraph markers. Record deliberate silent beats explicitly.
- Model tracks and audio clips. Include role, source range, timeline placement, gain_db, fades, and track-level ducking settings. Mix values are starting points; measure and listen to final audio.
- Model text overlays with text role, timing in frames, font, weight, size_px, color, normalized position, anchor, alignment, safe area, opacity, and fades.
- Use closed enums for controlled fields. Reject unknown keys where practical.
- Add a validator that reports JSON paths and checks schema, duplicate IDs, asset/track references, file paths, actual media duration via FFprobe when installed, legal source ranges, integer frames, gaps/overlaps, and target-runtime tolerance. Clearly report skipped checks if tools are unavailable.
- Probe available CapCut Desktop, Computer Use, CapCut MCP, FFmpeg, and FFprobe. Run the 60-90 second smoke test in workflow/ASSEMBLY.md before a full edit. Never claim a native CapCut project exists if only a render was made.
- Use references/REFERENCE_TOOLING.md. Automated scene detection and ASR are aids; human review corrects false cuts and technical transcript errors.

## Path fixes already applied
The template's guide and LUT paths are now set for a plan copied into episodes/<slug>/. Keep these paths consistent in the v2 template and validation.

## Next actions
Proceed with the schema/template upgrade, validator, and assembly adapter documentation/tests against the requirements above. Preserve existing root files and media. Report implemented files and any capability that cannot be tested locally.
