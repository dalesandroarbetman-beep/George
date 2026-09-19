import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("contract_checker", ROOT / "tools" / "check_contracts.py")
checker = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(checker)


class ContractTests(unittest.TestCase):
    def test_schemas_examples_and_negative_cases(self):
        result = checker.check_contracts()
        self.assertTrue(result["ok"], result)
        self.assertEqual(len(result["contracts"]), 4)


if __name__ == "__main__":
    unittest.main()
