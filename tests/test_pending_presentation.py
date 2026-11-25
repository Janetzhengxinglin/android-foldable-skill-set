import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "skills/android-foldable-adaptation-review/scripts/build_report.py"
spec = importlib.util.spec_from_file_location("pending_report", SCRIPT)
report_builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report_builder)


class PendingPresentationTests(unittest.TestCase):
    def test_example_is_compact_but_gallery_preserves_distinct_locations(self):
        with tempfile.TemporaryDirectory() as folder:
            run = Path(folder)
            source = run / "source.png"
            source.write_bytes(b"test source")
            input_path = run / "review-input.json"
            input_path.write_text("{}")
            review = {"rule_version": "test", "input_path": str(input_path),
                      "scope": {"profile": "screenshot-only", "page_ids": ["a", "b"]},
                      "checks": [], "findings": [],
                      "pending_observations": [{"id": "blur", "title": "Blur",
                          "phenomenon": "Soft text", "judgment": "Source comparison needed",
                          "locations": [{"page_id": pid, "bbox_px": [0, 0, 10, 10]}
                                        for pid in ("a", "b")]}]}
            (run / "review.json").write_text(json.dumps(review))
            contexts = {"inner": {"display": "inner", "size_px": [100, 100]}}
            pages = {pid: {"context_id": "inner", "image_evidence_id": "image"}
                     for pid in ("a", "b")}
            evidence = {"image": {"path": str(source), "sha256": "test",
                                   "width_px": 100, "height_px": 100}}
            with patch.object(report_builder, "validate", return_value={}), \
                 patch.object(report_builder, "load_input", return_value=({}, contexts, evidence, pages)):
                report_builder.build(run, run / "report")
            result = json.loads((run / "report/report.json").read_text())
            sections = result["artboards"][0]["sections"]
            self.assertEqual(len(sections[1]["pending_observations"]), 1)
            self.assertEqual({p["page_id"] for p in sections[2]["pages"]}, {"a", "b"})
            self.assertEqual(len(result["problem_evidence"][0]["locations"]), 2)
            self.assertEqual(result["summary"]["pending_observation_count"], 1)
