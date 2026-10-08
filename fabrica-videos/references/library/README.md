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
    transcript.txt          timestamped transcript (source stated: human, auto-caption or ASR)
    contact-sheet-*.jpg     low-resolution sheets from the opening, mechanism and later sequences
    evidence-notes.md       notes with timestamps
```

`status` values in INDEX.csv: `new` (intake finished, Claude has not digested it), `digested` (Claude folded it into the style guide candidate rules), `needs_human` (cut detection or transcript needs a person to correct it), `rejected` (not useful, with a reason).

Video files are not committed (large; ignored by `.gitignore`). Transcripts and contact sheets are committed. If the repository is public, third-party frames and transcripts are visible to everyone; making the repository private avoids copyright takedowns. See `references/CODEX_INTAKE_PROMPT.md`.
