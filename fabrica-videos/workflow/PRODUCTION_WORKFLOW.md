# Production Workflow

Phase 1 establishes the channel style in one week. Phases 2 and 3 repeat for each episode.

## Phase 1 — Define the style (one week)

### Day 1: choose references
Select 3-5 complete English-language videos. Provide URLs or local files, not thumbnails alone. Choose examples for distinct strengths such as narrative, cinematic images, visual explanation, sound, or clean graphics.

### Days 2-4: observe and measure
Use ../references/REFERENCE_ANALYSIS_TEMPLATE.md for each video. Review its opening, one mechanism explanation, and a later sequence. Record transcript or timestamped notes, cut timestamps, shot counts, mean and median shot length by sequence type, camera movement, transitions, text/captions, music and sound changes, narrative reveals, and payoff.

Separate measurements from interpretation. If a section cannot be watched or transcribed, mark it not observed. Never infer editing metrics from a thumbnail.

### Day 5: synthesize identity
Update ../style/STYLE_GUIDE.md with the fixed visual identity, fonts, palette, caption rules, transitions, sound, and measured pacing ranges. Keep observed evidence separate from creative choices.

### Days 6-7: test and approve
Make a 60-90 second test using a hero wide, a macro detail, one explanatory graphic, a human scale cue, one title or label, narration, and music. Review on desktop and phone. Revise and approve the guide before the full episode.

## Phase 2 — Script and materials (per episode)
1. Write a brief: audience, central question, thesis, target duration, language, and claims that need evidence.
2. Verify technical claims. Log source URL, author/organization, date, and the exact claim supported.
3. Write natural spoken-English narration with a hook, promise, acts, transitions, and payoff.
4. Create a scene list with the spoken line, visual evidence, on-screen copy, provisional duration, source assets, sound, and narrative purpose.
5. Record or synthesize one consistent voice. Add pronunciation notes. Treat scene timing as provisional until approved narration audio exists.
6. Gather footage, images, maps, diagrams, screen recordings, and music. Verify usage rights.
7. Log every external asset: ID, path, creator, source, license/permission, required attribution, and rights status.
8. Before editing, mark missing media, uncertain claims, unsupported visuals, and unresolved rights.

## Phase 3 — Edit plan as data (per episode)
Copy ../timeline/EDIT_PLAN_TEMPLATE.json to the episode folder and complete it. Validate with ../timeline/EDIT_PLAN.schema.json and the validator specified by ../timeline/TIMELINE_SPEC.md.

The final timeline is driven by approved narration audio and uses integer frames. Each visual or audio clip specifies its asset ID, source in/out, order, track, timeline start and duration. Text includes style, position, and timing. Unknown values stay unresolved.

### Pre-assembly
- Resolve each media path relative to the episode plan.
- Probe source duration, resolution, frame rate, and audio.
- Confirm source ranges fit the actual file.
- Check frame integers, ordering, intentional gaps/overlaps, and runtime tolerance.
- Verify on-screen text and facts against the script and sources.

### Assembly and review
Follow ../workflow/ASSEMBLY.md. Probe the tools that are actually available. Build a 60-90 second smoke test before the full edit. Render a low-resolution review copy; inspect the hook, scene joins, diagrams, ending, phone legibility, black detail, highlights, narration clarity, and rights. Keep the plan synchronized with changes. Export final deliverables only after review.

## Folder layout
```
videos/            (repository root)
  CLAUDE.md
  industrial-cold-warm-core.cube
  fabrica-videos/
    CLAUDE.md
    CLAUDE_REVIEW_RESPONSE.md
    INDEX.md
    style/STYLE_GUIDE.md
    references/REFERENCE_ANALYSIS_TEMPLATE.md
    references/REFERENCE_TOOLING.md
    workflow/PRODUCTION_WORKFLOW.md
    workflow/ASSEMBLY.md
    timeline/EDIT_PLAN_TEMPLATE.json
    timeline/EDIT_PLAN.schema.json
    timeline/TIMELINE_SPEC.md
    episodes/<episode-slug>/
      brief.md
      script.md
      sources.md
      asset-log.csv
      EDIT_PLAN.json
      media/
      audio/
      renders/
```

## Completion report
List files produced, actual runtime/export settings if known, checks actually run, missing assets, unresolved claims or rights, and whether the output is a plan, review render, editable project, or final render.
