# Local Tools for Phase 1 Reference Analysis

Claude Code should use locally available tools to create evidence for human review. Tool output is evidence to inspect, not an automatic editorial decision.

## Minimum workflow
1. Probe availability and versions of FFprobe, FFmpeg, PySceneDetect, and a timestamp-capable transcription tool.
2. For each full reference, save metadata: title, URL/path, runtime, frame size, frame rate, audio streams, and review date.
3. Extract candidate shot changes with PySceneDetect or another installed detector. Save candidate timestamps to CSV.
4. Generate contact sheets from representative intervals: opening, mechanism explanation, and later payoff. Use them to validate detected boundaries and identify sequence type.
5. Create or obtain a timestamped transcript. Mark the source (human, auto-caption, or ASR) and manually correct technical names, numbers, and terms.
6. Combine cut timestamps and transcript into a sampled shot log. Calculate mean and median shot duration separately for opening, explanation, diagrams, interviews, and montages.
7. A human reviews the video and corrects false cuts, dissolves, animation changes, and transcript errors. Label unreviewed detector output as machine-estimated.
8. Populate REFERENCE_ANALYSIS_TEMPLATE.md with measurements, timestamps, interpretations, and confidence.

## Do not overclaim
- A cut detector proposes visual changes; it cannot identify the narrative meaning of a shot.
- A transcript cannot measure music, visual emphasis, camera movement, or whether a diagram is accurate.
- A contact sheet is a sample, not proof of full-video rhythm.
- If the video cannot be downloaded or inspected, use an authorized local copy or mark fields not observed. Do not bypass access restrictions.
- Analyze only references the user supplies or approves. Do not copy distinctive shots, scripts, or music.
