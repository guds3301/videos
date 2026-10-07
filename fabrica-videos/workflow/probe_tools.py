#!/usr/bin/env python3
"""Report which assembly and analysis tools actually exist on this machine.

Step 1 of workflow/ASSEMBLY.md. Reports facts only; it installs nothing.
CapCut Desktop, Computer Use and a CapCut MCP server cannot be detected reliably
from a script, so they are reported as 'not detectable' and must be confirmed
by the user or by inspecting the Claude Code configuration.
"""
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def version(cmd, flag="-version"):
    path = shutil.which(cmd)
    if not path:
        return {"found": False}
    try:
        out = subprocess.run([cmd, flag], capture_output=True, text=True, timeout=20)
        first = (out.stdout or out.stderr).strip().splitlines()
        return {"found": True, "path": path, "version": first[0] if first else "unknown"}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"found": True, "path": path, "version": f"could not run: {exc}"}


def python_module(name):
    from importlib import metadata
    try:
        return {"found": True, "version": metadata.version(name)}
    except metadata.PackageNotFoundError:
        return {"found": False}


def capcut_install():
    candidates = []
    system = platform.system()
    if system == "Windows":
        import os
        local = os.environ.get("LOCALAPPDATA", "")
        candidates += [Path(local) / "CapCut" / "Apps", Path(local) / "CapCut"]
    elif system == "Darwin":
        candidates += [Path("/Applications/CapCut.app")]
    found = [str(p) for p in candidates if p.exists()]
    return {"found": bool(found), "paths": found}


def main():
    report = {
        "platform": platform.platform(),
        "ffmpeg": version("ffmpeg"),
        "ffprobe": version("ffprobe"),
        "scenedetect": version("scenedetect", "version"),
        "whisper_cli": version("whisper", "--help") if shutil.which("whisper") else {"found": False},
        "python_jsonschema": python_module("jsonschema"),
        "capcut_desktop_files": capcut_install(),
        "capcut_mcp": "not detectable by script; check the Claude Code MCP configuration",
        "computer_use": "not detectable by script; confirm in Claude Desktop settings",
    }
    print(json.dumps(report, indent=2))
    missing = [k for k in ("ffmpeg", "ffprobe") if not report[k]["found"]]
    if missing:
        print(f"\nMissing required tools: {', '.join(missing)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
