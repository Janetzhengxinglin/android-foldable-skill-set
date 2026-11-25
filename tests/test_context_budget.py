import base64
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "skills/android-foldable-page-capture/scripts/image_batches.py"
spec = importlib.util.spec_from_file_location("context_budget", SCRIPT)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class ContextBudgetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.image = self.root / "one.png"
        self.image.write_bytes(base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScLbtAAAAABJRU5ErkJggg=="))
        self.ledger = self.root / "ledger.json"

    def tearDown(self):
        self.tmp.cleanup()

    def event(self, session, status="returned", count=31):
        return {"session": session, "status": status,
                "images": [guard.detail(self.image)] * count}

    def save(self, events, **extra):
        self.ledger.write_text(json.dumps({"schema_version": 2, "events": events, **extra}))

    def test_old_chat_does_not_consume_new_chat_budget(self):
        self.save([self.event("old")])
        result = guard.check(self.ledger, "new", [self.image])
        self.assertTrue(result["ready"])
        self.assertEqual(result["attempted_context_inputs"], 0)
        self.assertEqual(result["historical_reference_inputs"], 31)

    def test_imported_aggregate_is_not_an_actual_image_event(self):
        self.save([self.event("same", "inherited_count_only")])
        result = guard.check(self.ledger, "same", [self.image])
        self.assertTrue(result["ready"])
        self.assertEqual(result["attempted_context_inputs"], 0)

    def test_same_context_count_reminds_without_deadlock(self):
        self.save([self.event("same")])
        result = guard.check(self.ledger, "same", [self.image])
        self.assertTrue(result["ready"])
        self.assertEqual(result["attempted_context_inputs"], 31)
        self.assertIn("context_checkpoint_reminder", result["warnings"])
        self.assertTrue(result["checkpoint_due"])

    def test_verified_same_context_history_is_preserved(self):
        self.save([], context_history={"same": {"attempted_inputs": 31}})
        result = guard.record(self.ledger, "same", "capture", [self.image])
        self.assertEqual(result["session_inputs"], 32)
        self.assertFalse(result["call_budget_exceeded"])

    def test_per_call_limits_still_block(self):
        self.save([])
        result = guard.check(self.ledger, "same", [self.image] * 3)
        self.assertFalse(result["ready"])
        self.assertIn("image_count", result["reasons"])

    def test_actual_repeated_failures_still_block(self):
        self.save([self.event("same", "failed", 1), self.event("same", "failed", 1)])
        result = guard.check(self.ledger, "same", [self.image])
        self.assertFalse(result["ready"])
        self.assertIn("repeated_failures_use_new_context", result["reasons"])
