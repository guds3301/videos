"""Tests for validate_plan.py. Needs ffmpeg/ffprobe to build synthetic media."""
import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import validate_plan as vp  # noqa: E402

TEMPLATE = Path(__file__).resolve().parents[1] / "EDIT_PLAN_TEMPLATE.json"
HAVE_FFMPEG = shutil.which("ffmpeg") and shutil.which("ffprobe")


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def make_workspace(root: Path) -> Path:
    """Build workspace/episodes/ep/ with real synthetic media and return the plan path."""
    episode = root / "episodes" / "ep"
    (episode / "media").mkdir(parents=True)
    (episode / "audio").mkdir()
    (root / "style").mkdir()
    (root / "style" / "STYLE_GUIDE.md").write_text("# test guide\n")
    ffmpeg("-f", "lavfi", "-i", "testsrc2=size=640x360:rate=24:duration=10",
           "-pix_fmt", "yuv420p", str(episode / "media" / "machine.mp4"))
    ffmpeg("-f", "lavfi", "-i", "sine=frequency=220:duration=10", str(episode / "audio" / "narration.wav"))
    ffmpeg("-f", "lavfi", "-i", "sine=frequency=110:duration=10", str(episode / "audio" / "music.wav"))
    return episode / "EDIT_PLAN.json"


def asset(asset_id, path, kind):
    return {"asset_id": asset_id, "path": path, "asset_type": kind, "source_url": None,
            "creator": "Test", "license": "own work", "attribution": None,
            "rights_status": "user_owned"}


def base_plan() -> dict:
    plan = json.loads(TEMPLATE.read_text())
    plan["episode"].update({"id": "ep", "status": "in_edit", "width": 640, "height": 360,
                            "target_duration_frames": 216, "runtime_tolerance_frames": 1,
                            "style_guide": "../../style/STYLE_GUIDE.md"})
    plan["global_style"]["lut_path"] = None
    plan["assets"] = [asset("A001", "media/machine.mp4", "video"),
                      asset("A002", "audio/narration.wav", "audio"),
                      asset("A003", "audio/music.wav", "audio")]
    plan["narration"].update({"approved": True, "segments": [
        {"segment_id": "N001", "asset_id": "A002", "source_in_seconds": 0, "source_out_seconds": 4},
        {"segment_id": "N002", "asset_id": "A002", "source_in_seconds": 4, "source_out_seconds": 9}]})

    def visual(clip_id, start, dur, src_in, src_out, order=1):
        return {"clip_id": clip_id, "asset_id": "A001", "order": order, "track_id": "V1",
                "source_in_seconds": src_in, "source_out_seconds": src_out,
                "timeline_start_frame": start, "duration_frames": dur, "fit_mode": "cover",
                "speed": 1.0, "transition_in": "hard_cut", "transition_out": "hard_cut"}

    def audio(clip_id, asset_id, track, start, dur, src_in, src_out, gain):
        return {"clip_id": clip_id, "asset_id": asset_id, "track_id": track,
                "source_in_seconds": src_in, "source_out_seconds": src_out,
                "timeline_start_frame": start, "duration_frames": dur, "gain_db": gain}

    scene = plan["scenes"][0]
    scene.update({"timing_status": "reconciled", "overlays": [], "duration_frames": 96})
    scene["narration"] = {"text": "One.", "segment_ids": ["N001"]}
    scene["clips"] = [visual("C001", 0, 96, 0, 4)]
    scene["audio_clips"] = [audio("AC001", "A002", "A1", 0, 96, 0, 4, 0),
                            audio("AC002", "A003", "A2", 0, 96, 0, 4, -18)]
    second = copy.deepcopy(scene)
    second.update({"scene_id": "S002", "act": "mechanism", "start_frame": 96, "duration_frames": 120})
    second["narration"] = {"text": "Two.", "segment_ids": ["N002"]}
    second["clips"] = [visual("C002", 96, 72, 4, 7), visual("C003", 168, 48, 7, 9)]
    second["audio_clips"] = [audio("AC003", "A002", "A1", 96, 120, 4, 9, 0),
                             audio("AC004", "A003", "A2", 96, 120, 4, 9, -18)]
    plan["scenes"] = [scene, second]
    return plan


@unittest.skipUnless(HAVE_FFMPEG, "ffmpeg/ffprobe not installed")
class ValidatePlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        cls.plan_path = make_workspace(cls.root)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def run_plan(self, plan, probe=True):
        self.plan_path.write_text(json.dumps(plan))
        checks, _ = vp.run_validation(self.plan_path, probe=probe)
        return {c.name: c for c in checks}

    def assertFails(self, plan, name, text=None):
        checks = self.run_plan(plan)
        self.assertEqual(checks[name].status, "fail", checks[name].to_dict())
        if text:
            self.assertTrue(any(text in e for e in checks[name].errors), checks[name].errors)
        return checks

    def test_valid_plan_has_no_failures_and_probes_media(self):
        checks = self.run_plan(base_plan())
        failing = {n: c.errors for n, c in checks.items() if c.status == "fail"}
        self.assertEqual(failing, {})
        self.assertEqual(checks["media_probe"].status, "pass")
        self.assertEqual(checks["files"].status, "pass")

    def test_template_is_schema_valid_and_reports_unresolved_as_warnings(self):
        template = Path(self.root / "episodes" / "ep" / "TEMPLATE.json")
        template.write_text(TEMPLATE.read_text())
        checks, _ = vp.run_validation(template)
        by_name = {c.name: c for c in checks}
        self.assertEqual(by_name["schema"].status, "pass")
        self.assertNotIn("fail", {c.status for c in checks})
        self.assertEqual(by_name["media_probe"].status, "skipped")

    def test_schema_failure_skips_dependent_checks(self):
        plan = base_plan()
        plan["scenes"][0]["surprise"] = True
        checks = self.run_plan(plan)
        self.assertEqual(checks["schema"].status, "fail")
        self.assertIn("surprise", " ".join(checks["schema"].errors))
        self.assertEqual(checks["timeline"].status, "skipped")

    def test_unknown_enum_values_rejected(self):
        plan = base_plan()
        plan["scenes"][0]["clips"][0]["transition_in"] = "glitch"
        self.assertFails(plan, "schema", "glitch")

    def test_movement_other_requires_explanation(self):
        plan = base_plan()
        plan["scenes"][0]["edit"]["movement"] = "other"
        self.assertFails(plan, "schema")
        plan["scenes"][0]["edit"]["movement_explanation"] = "locked-off rack focus"
        self.assertEqual(self.run_plan(plan)["schema"].status, "pass")

    def test_duplicate_clip_id(self):
        plan = base_plan()
        plan["scenes"][1]["clips"][0]["clip_id"] = "C001"
        self.assertFails(plan, "unique_ids", "C001")

    def test_unknown_asset_and_wrong_track_type(self):
        plan = base_plan()
        plan["scenes"][0]["clips"][0]["asset_id"] = "A999"
        self.assertFails(plan, "references", "A999")
        plan = base_plan()
        plan["scenes"][0]["clips"][0]["track_id"] = "A1"
        self.assertFails(plan, "references", "not a video track")

    def test_float_frames_rejected(self):
        plan = base_plan()
        plan["scenes"][0]["clips"][0]["duration_frames"] = 96.0
        self.assertFails(plan, "integers")

    def test_source_out_not_after_in(self):
        plan = base_plan()
        plan["scenes"][0]["clips"][0]["source_in_seconds"] = 4
        plan["scenes"][0]["clips"][0]["source_out_seconds"] = 4
        self.assertFails(plan, "source_ranges")

    def test_clip_duration_must_match_source_and_speed(self):
        plan = base_plan()
        plan["scenes"][0]["clips"][0]["speed"] = 2.0  # 4s source at 2x is 48 frames, not 96
        self.assertFails(plan, "clip_durations", "implies 48")

    def test_gap_between_scenes_must_be_declared(self):
        plan = base_plan()
        plan["scenes"][1]["start_frame"] = 100
        plan["scenes"][1]["clips"] = plan["scenes"][1]["clips"][:1]
        plan["scenes"][1]["clips"][0].update({"timeline_start_frame": 100, "duration_frames": 72, "clip_id": "C002"})
        plan["scenes"][1]["audio_clips"] = []
        checks = self.assertFails(plan, "timeline", "undeclared gap")
        plan["intentional_gaps"] = [{"start_frame": 96, "duration_frames": 4, "reason": "silent beat"}]
        plan["scenes"][1]["clips"][0]["duration_frames"] = 72
        plan["episode"]["target_duration_frames"] = 172
        again = self.run_plan(plan)
        self.assertFalse(any("undeclared gap" in e for e in again["timeline"].errors), again["timeline"].errors)

    def test_scene_overlap_rejected(self):
        plan = base_plan()
        plan["scenes"][1]["start_frame"] = 90
        self.assertFails(plan, "timeline", "overlap")

    def test_picture_coverage_gap_inside_scene(self):
        plan = base_plan()
        plan["scenes"][1]["clips"][1].update({"timeline_start_frame": 172, "duration_frames": 44,
                                              "source_in_seconds": 7, "source_out_seconds": 9})
        self.assertFails(plan, "timeline", "no picture clip")

    def test_same_track_overlap_needs_reason(self):
        plan = base_plan()
        plan["scenes"][1]["clips"][1].update({"timeline_start_frame": 160, "duration_frames": 56,
                                              "source_in_seconds": 7, "source_out_seconds": 9.33})
        self.assertFails(plan, "timeline", "overlap")
        plan["scenes"][1]["clips"][1]["overlap_reason"] = "cross-dissolve into the diagram"
        again = self.run_plan(plan)
        self.assertFalse(any("overlap by" in e for e in again["timeline"].errors), again["timeline"].errors)

    def test_runtime_mismatch(self):
        plan = base_plan()
        plan["episode"]["target_duration_frames"] = 400
        self.assertFails(plan, "runtime")
        plan["episode"]["status"] = "draft"
        plan["narration"]["approved"] = False
        for scene in plan["scenes"]:
            scene["timing_status"] = "draft"
        self.assertEqual(self.run_plan(plan)["runtime"].status, "warn")

    def test_rights_blocked_and_needs_review(self):
        plan = base_plan()
        plan["assets"][0]["rights_status"] = "blocked"
        self.assertFails(plan, "rights", "blocked")
        plan = base_plan()
        plan["assets"][0]["rights_status"] = "needs_review"
        self.assertFails(plan, "rights", "needs_review")

    def test_unreconciled_timing_fails_while_editing(self):
        plan = base_plan()
        plan["scenes"][0]["timing_status"] = "draft"
        self.assertFails(plan, "narration_sync", "S001")
        plan = base_plan()
        plan["narration"]["approved"] = False
        self.assertFails(plan, "narration_sync", "approved")

    def test_silent_beat_needs_purpose(self):
        plan = base_plan()
        plan["scenes"][0]["narration"] = {"text": "", "segment_ids": []}
        self.assertFails(plan, "narration_sync", "silent_beat_purpose")
        plan["scenes"][0]["narration"]["silent_beat_purpose"] = "pause before the reveal"
        self.assertNotEqual(self.run_plan(plan)["narration_sync"].status, "fail")

    def test_source_range_beyond_real_media_duration(self):
        plan = base_plan()
        clip = plan["scenes"][1]["clips"][1]
        clip["source_out_seconds"] = 11  # file is 10 s; 4 s at 24 fps keeps clip_durations consistent
        clip["source_in_seconds"] = 7
        clip["duration_frames"] = 96
        plan["scenes"][1]["duration_frames"] = 168
        plan["scenes"][1]["audio_clips"] = []
        plan["episode"]["target_duration_frames"] = 264
        checks = self.run_plan(plan)
        self.assertTrue(any("exceeds probed duration" in e for e in checks["media_probe"].errors),
                        checks["media_probe"].errors)

    def test_missing_file_fails_past_draft_but_warns_in_draft(self):
        plan = base_plan()
        plan["assets"][0]["path"] = "media/nope.mp4"
        self.assertFails(plan, "files", "nope.mp4")
        plan["episode"]["status"] = "draft"
        plan["narration"]["approved"] = False
        for scene in plan["scenes"]:
            scene["timing_status"] = "draft"
        self.assertEqual(self.run_plan(plan)["files"].status, "warn")

    def test_no_probe_reports_skipped_not_passed(self):
        checks = self.run_plan(base_plan(), probe=False)
        self.assertEqual(checks["media_probe"].status, "skipped")

    def test_absolute_and_backslash_paths_rejected(self):
        plan = base_plan()
        plan["assets"][0]["path"] = "media\\machine.mp4"
        self.assertFails(plan, "schema")


class RoundingTests(unittest.TestCase):
    def test_round_half_up(self):
        self.assertEqual(vp.round_half_up(Fraction(5, 2)), 3)
        self.assertEqual(vp.round_half_up(Fraction(7, 3)), 2)
        self.assertEqual(vp.seconds_to_frames(0.5, Fraction(25, 1)), 13)
        self.assertEqual(vp.seconds_to_frames(1, Fraction(30000, 1001)), 30)

    def test_fractional_frame_rate_uses_exact_ratio(self):
        self.assertEqual(vp.seconds_to_frames(10, Fraction(30000, 1001)), 300)


if __name__ == "__main__":
    unittest.main()
