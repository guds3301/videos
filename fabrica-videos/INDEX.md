# Fabrica Videos Documentation

Claude Code should begin with the root CLAUDE.md, then fabrica-videos/CLAUDE.md and CLAUDE_REVIEW_RESPONSE.md.

## Folders
- style/STYLE_GUIDE.md — channel look, typography, color, movement, sound, and narrative.
- references/REFERENCE_ANALYSIS_TEMPLATE.md — one analysis worksheet per full-video reference.
- references/REFERENCE_TOOLING.md — local metadata, shot-detection, transcript, and human-review workflow.
- workflow/PRODUCTION_WORKFLOW.md — the three production phases.
- workflow/ASSEMBLY.md — adapter selection and the 60-90 second assembly smoke test.
- timeline/TIMELINE_SPEC.md — frame-accurate plan requirements and validator checks.
- timeline/EDIT_PLAN_TEMPLATE.json — starting plan for each episode.
- timeline/EDIT_PLAN.schema.json — structural validation.
- timeline/validate_plan.py — plan v2 validator (schema plus cross-checks, FFprobe when available); tests in timeline/tests/.
- workflow/probe_tools.py — reports which assembly and analysis tools exist on this machine.
- workflow/render_review.py — render-only FFmpeg route that builds a review video from a validated plan; tests in workflow/tests/.
- setup/SETUP-WINDOWS.md and setup/setup-windows.ps1 — check or install the local Windows environment (asks before each install).
- ../graphics/README.md — Remotion graphics (chapter card, measure line, component diagram) rendered as transparent clips for CapCut.
- IMPLEMENTATION_REPORT.md — what was implemented, tested, and what is still untested.
- episodes/<episode-slug>/ — each episode's brief, script, sources, asset log, plan, media, audio, and renders.

## Path convention
All media paths in an episode plan resolve relative to the episode folder. Use forward slashes. The style guide is ../../style/STYLE_GUIDE.md. The LUT is ../../../industrial-cold-warm-core.cube.
