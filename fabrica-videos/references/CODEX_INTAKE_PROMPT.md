# Prompt for Codex: reference intake

Paste everything below the line into Codex, with the repository `videos` open on the machine that holds the reference videos. Replace the three `<<...>>` items first.

---

You are doing the **intake** step of a video style project. A second assistant, Claude, will later read your output from the repository to digest the references and refine the channel's edit model. You gather evidence and package it; you do not make final style decisions.

## Context
Repository root: this `videos` repo. Start with `fabrica-videos/INDEX.md`, then `fabrica-videos/CLAUDE.md`, `fabrica-videos/style/STYLE_GUIDE.md`, `fabrica-videos/references/REFERENCE_ANALYSIS_TEMPLATE.md`, `fabrica-videos/references/REFERENCE_TOOLING.md`, `fabrica-videos/workflow/PRODUCTION_WORKFLOW.md`, and `graphics/README.md`. The channel makes English-language, cinematic and clean documentaries about extreme technology, engineering and science. Videos are assembled with Remotion and CapCut.

## Inputs
- References to analyze (full videos, not thumbnails): `<<LIST OF LOCAL FILE PATHS AND/OR URLS I APPROVE>>`
- Remotion work to summarize as the "edit model": `<<PATH TO MY REMOTION PROJECT, or "graphics/" if none>>`
- Branch to push to: `intake/<<YYYY-MM-DD>>`

## Hard rules
1. Analyze only the references listed above. Do not search for or add others. If a URL cannot be opened or downloaded by ordinary authorized means, mark it `not observed`; never bypass access restrictions.
2. Never invent measurements. Anything you did not measure or watch is `not observed`. A still frame cannot support claims about cut rhythm, sound or narration pace. Keep **measured**, **interpretation** and **creative choice** in separate sections, as the template does.
3. Commit the evidence needed for Claude to digest the references: metadata, measurements, `shots.csv`, a timestamped transcript (state its source: human, auto-caption or ASR), a handful of low-resolution contact sheets or representative frames per video, and your notes. Do not commit the video files themselves (they are large and are ignored by `.gitignore`); keep the originals where they are.
4. No paid API calls, no installs, no downloads, no destructive operations without telling me first and waiting for my approval. Prefer tools already installed (probe with `py -3 fabrica-videos/workflow/probe_tools.py`).
5. Never copy another creator's distinctive shots, script, graphics or music into this project. Extract transferable techniques only.
6. Keep original files untouched. Work in a scratch folder outside the repository and copy only the allowed outputs in.

## For each reference
Use `fabrica-videos/references/REFERENCE_TOOLING.md` as the procedure. Create `fabrica-videos/references/library/<ref-id>/` (`ref-id` = short lowercase slug) containing:
- `meta.json`: title, creator, URL or local path, language, upload date if known, runtime, frame size, frame rate, audio streams, date reviewed, tools and versions used.
- `shots.csv`: candidate cut timestamps (seconds and frame), detector name and threshold, marked `machine-estimated` unless I confirmed them.
- `analysis.md`: `REFERENCE_ANALYSIS_TEMPLATE.md` filled in. Measure at least: the opening/hook, one mechanism explanation, one later sequence. For each, shot count, mean and median shot length, sequence type, on-screen text frequency and duration, transition types, camera movement, music entry/changes/pauses, effects and ambience, how real footage, 3D, diagrams and screen capture are mixed, and where the central question is stated. Also fill "Candidate rules for our channel" with a confidence and an adopt/test/reject proposal for each rule. State explicitly which sections were not observed.
- `transcript.txt`: timestamped transcript, first line stating its source (human, auto-caption or ASR) and whether it was corrected.
- `contact-sheet-<sequence>.jpg` (and any representative frames): low resolution, from the opening, mechanism explanation and later sequence, so Claude can check detected boundaries and sequence types.
- `evidence-notes.md`: your notes with timestamps.
Add one row per reference to `fabrica-videos/references/library/INDEX.csv` with `status=new` (or `needs_human` when cuts or transcript need a person).

## Edit model snapshot
Write `fabrica-videos/references/library/STYLE_STATE.md` describing the current edit model so Claude can compare references against it:
- Rules that are **locked**, **provisional** or **open**, each with where it comes from (STYLE_GUIDE section, measured reference, or my decision).
- What the Remotion project does today: compositions, props, timings, easing, palette, fonts, transitions, text rules, sound rules, with file paths. Describe what the code actually does, not what it should do.
- What has been tried and rejected, if you can see it in the history or notes.
- Gaps: things the references should help decide (for example average shot length by sequence type, caption style, music behavior, graphic reveal timing).

## Handoff
Write `fabrica-videos/references/library/HANDOFF.md` with: date; list of references added (id, title, runtime, status); tools and versions that actually ran; checks you ran and their results; what could not be done and why; questions for me; and a section **"For Claude to digest"** that says in 5-10 bullets what to compare, update or decide next.

## Finish
1. Run `py -3 fabrica-videos/timeline/validate_plan.py` only if you touched an `EDIT_PLAN.json`; otherwise do not touch plans.
2. `git switch -c intake/<<YYYY-MM-DD>>`, commit with a clear message, and `git push -u origin intake/<<YYYY-MM-DD>>`. Do not push to `main` and do not open a pull request.
3. Reply with: the branch name, the files created, and anything you could not verify. Tell me to ask Claude to "digest the intake on branch intake/<<YYYY-MM-DD>>".
