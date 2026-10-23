import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from compare import build_report


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.input = self.root / "collected"
        self.output = self.root / "output"
        self.lock = self.root / "refs.json"
        self.pins = {"php-8.4.27": "a" * 40, "php-8.5.12": "b" * 40}
        self.lock.write_text(json.dumps({"entries": self.pins}))
        self.cases = ("control", "sprintf_width", "pack_pad", "bin2hex_growth",
            "base64_encode_growth", "base64_encode_13m", "urlencode_growth")
        for key, sha in self.pins.items():
            folder = self.input / ("evidence-" + key)
            folder.mkdir(parents=True)
            data = {"snapshot": key, "source_sha": sha, "build_config": "debug",
                    "results": {name: {"classification": "NORMAL_COMPLETION",
                                       "returncode": 0, "shutdown_seen": True}
                                for name in self.cases}}
            (folder / "oom-results.json").write_text(json.dumps(data))

    def test_generates_report(self):
        out = build_report(self.input, self.lock, self.output)
        self.assertEqual(out["differences"], [])
        self.assertEqual(len(out["rows"]), len(self.pins) * len(self.cases))
        self.assertTrue((self.output / "oom-comparison.md").exists())

    def test_rejects_wrong_sha(self):
        p = self.input / "evidence-php-8.4.27" / "oom-results.json"
        data = json.loads(p.read_text())
        data["source_sha"] = "0" * 40
        p.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "SHA mismatch"):
            build_report(self.input, self.lock, self.output)

    def test_detects_missing_snapshot(self):
        p = self.input / "evidence-php-8.5.12" / "oom-results.json"
        p.unlink()
        with self.assertRaisesRegex(ValueError, "missing snapshots"):
            build_report(self.input, self.lock, self.output)

    def test_control_must_pass(self):
        p = self.input / "evidence-php-8.5.12" / "oom-results.json"
        data = json.loads(p.read_text())
        data["results"]["control"]["shutdown_seen"] = False
        p.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "invalid control"):
            build_report(self.input, self.lock, self.output)


if __name__ == "__main__":
    unittest.main()
