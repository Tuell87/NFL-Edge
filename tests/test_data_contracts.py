import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location("contracts","scripts/check_data_contracts.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
class ContractTests(unittest.TestCase):
    def test_complete_valid_dataset(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for filename, fields in mod.REQUIRED.items():
                data={"status":"ok"}
                for field in fields:
                    data[field]={} if filename=="evaluation.json" and field=="metrics" else []
                (root/filename).write_text(json.dumps(data))
            self.assertEqual(mod.validate(root),[])
    def test_missing_and_malformed_data_fail(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"odds.json").write_text('{"status":"ok","markets":NaN}')
            errors=mod.validate(root)
            self.assertTrue(any("odds.json" in e for e in errors))
            self.assertTrue(any("games.json" in e for e in errors))
    def test_wrong_shape_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"odds.json").write_text('{"status":"ok","markets":{}}')
            self.assertTrue(any("markets must be list" in e for e in mod.validate(root)))
if __name__=="__main__":
    unittest.main()
