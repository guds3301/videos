# Assembly Adapter and Smoke Test

The edit plan is the source of truth. The adapter translates it into an editor project or a rendered review file without guessing missing values.

## 1. Probe the machine first
Check for:
- CapCut Desktop and its version.
- Claude Desktop Computer Use availability if the user expects GUI operation.
- A configured CapCut MCP server and the tools it exposes.
- FFmpeg and FFprobe.
Report exactly what is available. Do not install plugins or upload media without approval.

Run `python3 workflow/probe_tools.py` for this step.

## 2. Select one explicit output route
### CapCut route
Use an installed CapCut MCP or enabled Computer Use if it can create/edit the required project. Confirm that a simple draft opens and that the requested media, text, and audio tracks are represented. Save to a new project or copy; do not overwrite originals. If only GUI operation is available, use a fresh duplicate project and verify the project after saving.

### FFmpeg route
Use FFmpeg only for a deterministic rendered video when no CapCut route is configured or when the user approves a render-only alternative. An FFmpeg render is not an editable CapCut project. Report that distinction clearly. Do not silently substitute FFmpeg for a requested native project.

The repository provides `python3 workflow/render_review.py episodes/<slug>/EDIT_PLAN.json episodes/<slug>/renders/review.mp4`. It validates the plan, refuses to render if validation fails, and prints a report listing everything it approximated or did not render. See the header of that script for the supported features.

## 3. 60-90 second smoke test
Before assembling a full episode, build a short test containing:
- One narration segment and one intentional pause.
- At least two ordered source clips with known in/out points.
- One text overlay with the final font, placement, and safe margin.
- One music bed with ducking under voice.
- The LUT on a Rec.709/sRGB clip after exposure/white-balance correction.
- One allowed transition and one simple graphic if the plan requests graphics.
- A final timeline at the episode's intended frame rate.

Inspect the render and project. Confirm cut frame positions, narration sync, text readability, audio mix, LUT strength, source paths, and project reopening. Fix the plan or adapter before continuing if a requirement is unsupported.

## 4. Full assembly
- Build only from a validated plan and approved assets.
- Preserve scene/clip IDs in logs so errors map back to the plan.
- Use temporary proxies for review when helpful; keep final source links intact.
- Render a low-resolution review file before final delivery.
- Inspect the opening, scene joins, diagrams, audio transitions, and ending.
- Update the plan when actual durations or edits change.

## 5. Completion report
Report:
- Adapter used and detected version/tool.
- Native project path and/or render path.
- Whether the result is editable or render-only.
- Actual frame rate, dimensions, duration, audio loudness/true peak if measured.
- Smoke-test results and checks actually performed.
- Unsupported effects, missing assets, unresolved rights/facts, and any manual action still needed.
