import os
from pathlib import Path
import unittest
from unittest.mock import patch

from ai_service.traffic_ai.config import ModelPaths, RuntimePaths, ensure_runtime_environment, project_root
from ai_service.traffic_ai.ocr import (
    CHINESE_PLATE_PROVINCES,
    NoopOcrEngine,
    create_default_ocr_engine,
    normalize_plate_text,
    plate_text_has_chinese_province,
)
from ai_service.traffic_ai.rules import IllegalStopRuleEvaluator
from ai_service.traffic_ai.schemas import Detection, DetectionBundle


class ConfigOcrRulesTest(unittest.TestCase):
    def test_model_paths_default_to_repo_models(self):
        paths = ModelPaths.default()

        self.assertEqual(paths.vehicle.name, "car_yolov8s.pt")
        self.assertEqual(paths.license_plate.name, "license.pt")
        self.assertEqual(paths.illegal_stop.name, "illegal_stop.pt")
        self.assertEqual(paths.vehicle.parent.name, "models")
        self.assertEqual(paths.vehicle.parent.parent.name, "ai_service")
        self.assertTrue(paths.vehicle.exists())

    def test_runtime_environment_points_ultralytics_to_project_dirs(self):
        runtime = RuntimePaths(root=Path.cwd() / ".tmp" / "unit-runtime")

        ensure_runtime_environment(runtime)

        self.assertTrue(Path(runtime.tmp_dir).exists())
        self.assertTrue(Path(runtime.yolo_config_dir).exists())
        self.assertTrue(Path(runtime.paddlex_cache_dir).exists())
        self.assertTrue(Path(runtime.matplotlib_config_dir).exists())

    def test_default_runtime_paths_stay_inside_repo_root(self):
        runtime = RuntimePaths.default()

        self.assertEqual(runtime.root, project_root())
        self.assertEqual(runtime.tmp_dir.parent, runtime.root)
        self.assertEqual(runtime.yolo_config_dir.parent, runtime.root)
        self.assertTrue(runtime.paddlex_cache_dir.name.endswith("paddlex"))
        self.assertEqual(runtime.matplotlib_config_dir.parent, runtime.root)

    def test_external_paddlex_cache_avoids_windows_temp_for_non_ascii_root(self):
        runtime = RuntimePaths(root=Path("C:/项目/smart-traffic"), use_external_paddlex_cache=True)

        if os.name == "nt":
            self.assertEqual(runtime.paddlex_cache_dir.drive, "C:")
            self.assertIn("tmp", runtime.paddlex_cache_dir.parts)
            self.assertNotIn("Temp", runtime.paddlex_cache_dir.parts)
        self.assertEqual(runtime.paddlex_cache_dir.name, "smart_traffic_violation_paddlex")

    def test_normalize_plate_text_removes_separators_and_uppercases_ascii(self):
        self.assertEqual(normalize_plate_text(" 粤 a-12345 "), "粤A12345")
        self.assertIsNone(normalize_plate_text(None))
        self.assertIsNone(normalize_plate_text("   "))

    def test_plate_text_has_chinese_province_prefix(self):
        self.assertIn("粤", CHINESE_PLATE_PROVINCES)
        self.assertTrue(plate_text_has_chinese_province("粤A12345"))
        self.assertTrue(plate_text_has_chinese_province("京B12345"))
        self.assertFalse(plate_text_has_chinese_province("XA12345"))

    def test_noop_ocr_returns_none_with_unavailable_status(self):
        result = NoopOcrEngine().recognize(Path("plate.jpg"))

        self.assertIsNone(result.text)
        self.assertEqual(result.engine, "none")
        self.assertEqual(result.status, "unavailable")

    def test_default_ocr_engine_does_not_hide_cache_errors(self):
        with patch("ai_service.traffic_ai.ocr.PaddleOcrEngine", side_effect=PermissionError("cache denied")):
            with self.assertRaises(PermissionError):
                create_default_ocr_engine()

    def test_illegal_stop_rule_matches_illegal_detection(self):
        bundle = DetectionBundle(
            vehicle=[Detection(label="cars", confidence=0.91, bbox=[1, 2, 3, 4], model="vehicle")],
            license_plate=[],
            illegal_stop=[
                Detection(label="illegal", confidence=0.86, bbox=[10, 20, 30, 40], model="illegal_stop")
            ],
        )

        result = IllegalStopRuleEvaluator().evaluate(bundle, plate_text="粤A12345")

        self.assertTrue(result.rule_matched)
        self.assertEqual(result.candidate_violation_type, "illegal_stop")
        self.assertEqual(result.evidence_level, "complete")
        self.assertIn("illegal_stop detection", result.evidence_items)

    def test_illegal_stop_rule_requires_illegal_detection(self):
        result = IllegalStopRuleEvaluator().evaluate(
            DetectionBundle(vehicle=[], license_plate=[], illegal_stop=[]),
            plate_text=None,
        )

        self.assertFalse(result.rule_matched)
        self.assertEqual(result.evidence_level, "insufficient")
        self.assertIn("illegal_stop detection", result.missing_evidence)


if __name__ == "__main__":
    unittest.main()
