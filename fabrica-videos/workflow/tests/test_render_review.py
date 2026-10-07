"""Smoke test for render_review.py using synthetic media (needs ffmpeg/ffprobe)."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "timeline" / "tests"))
sys.path.insert(0, str(HERE.parents[1] / "timeline"))
sys.path.insert(0, str(HERE.parent))
import test_validate_plan as helpers  # noqa: E402
import render_review as rr  # noqa: E402

HAVE_FFMPEG = shutil.which("ffmpeg") and shutil.which("ffprobe")


@unittest.skipUnless(HAVE_FFMPEG, "ffmpeg/ffprobe not installed")
class RenderReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.plan_path = helpers.make_workspace(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def render(self, plan, *extra):
        self.plan_path.write_text(json.dumps(plan))
        out = self.root / "renders" / "review.mp4"
        proc = subprocess.run([sys.executable, str(HERE.parent / "render_review.py"),
                               str(self.plan_path), str(out), *extra], capture_output=True, text=True)
        return proc, out

    def test_smoke_render_matches_plan(self):
        plan = helpers.base_plan()
        plan["scenes"][0]["overlays"] = []
        proc, out = self.render(plan, "--height", "180")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        report = json.loads(proc.stdout)
        self.assertFalse(report["editable_capcut_project"])
        self.assertEqual(report["kind"], "review_render")
        info = rr.vp.probe_media(out)
        self.assertEqual((info["width"], info["height"]), (320, 180))
        self.assertTrue(info["has_audio"])
        self.assertAlmostEqual(info["duration"], 9.0, delta=0.15)
        self.assertAlmostEqual(info["fps"], 24.0, delta=0.01)

    def test_refuses_invalid_plan(self):
        plan = helpers.base_plan()
        plan["scenes"][1]["start_frame"] = 100
        proc, out = self.render(plan)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("Refusing to render", proc.stderr)
        self.assertFalse(out.exists())

    def test_unsupported_features_are_reported(self):
        plan = helpers.base_plan()
        plan["scenes"][1]["clips"][1]["transition_in"] = "short_dissolve"
        plan["scenes"][1]["overlays"] = [{
            "overlay_id": "O001", "text": "TEST", "role": "label", "track_id": "T1",
            "start_offset_frames": 0, "duration_frames": 24,
            "style": {"font_family": "Definitely Not A Font", "weight": 400, "size_px": 40, "fill_hex": "#EEF1F3"},
            "placement": {"x": 0.5, "y": 0.9, "anchor": "bottom_center", "alignment": "center", "safe_margin": 0.05},
            "opacity": 1.0}]
        proc, _ = self.render(plan, "--height", "180")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        notes = " ".join(json.loads(proc.stdout)["not_rendered_or_approximated"])
        self.assertIn("rendered as a hard cut", notes)
        self.assertIn("Definitely Not A Font", notes)

    def test_text_overlay_renders_when_font_exists(self):
        font = rr.find_font("DejaVu Sans")
        if font is None:
            self.skipTest("no DejaVu Sans font available")
        plan = helpers.base_plan()
        plan["scenes"][0]["overlays"] = [{
            "overlay_id": "O001", "text": "Scale: 12 m", "role": "label", "track_id": "T1",
            "start_offset_frames": 0, "duration_frames": 48,
            "style": {"font_family": "DejaVu Sans", "weight": 400, "size_px": 40, "fill_hex": "#EEF1F3",
                      "shadow": {"color_hex": "#07090C", "blur_px": 4, "offset_x_px": 0, "offset_y_px": 2}},
            "placement": {"x": 0.5, "y": 0.9, "anchor": "bottom_center", "alignment": "center", "safe_margin": 0.05},
            "opacity": 1.0}]
        proc, out = self.render(plan, "--height", "180")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn("skipped: font", proc.stdout)


if __name__ == "__main__":
    unittest.main()
