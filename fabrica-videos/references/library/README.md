# Reference library (intake from Codex, digestion by Claude)

Each analyzed reference lives in `library/<ref-id>/`. `INDEX.csv` is the registry. `HANDOFF.md` is rewritten at the end of every intake so the next session knows exactly what is new.

```
library/
  INDEX.csv                 one row per reference (see header)
  HANDOFF.md                what changed in the last intake, what Claude should digest, open questions
  STYLE_STATE.md            current edit model: locked rules, open questions, what the Remotion project does today
  <ref-id>/
    meta.json               title, creator, url or local path, runtime, resolution, fps, audio streams, date reviewed
    analysis.md             REFERENCE_ANALYSIS_TEMPLATE.md filled in (measured vs interpretation kept apart)
    shots.csv               candidate cut timestamps (machine-estimated until a human corrects them)
    evidence-notes.md       short paraphrased notes; no full transcripts of third-party videos
```

`status` values in INDEX.csv: `new` (intake finished, Claude has not digested it), `digested` (Claude folded it into the style guide candidate rules), `needs_human` (cut detection or transcript needs a person to correct it), `rejected` (not useful, with a reason).

Third-party frames, full transcripts and video files are NOT committed unless the repository is private and the user said so. See `references/CODEX_INTAKE_PROMPT.md`.
