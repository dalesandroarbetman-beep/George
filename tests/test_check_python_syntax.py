import tempfile
import unittest
from pathlib import Path


from tools.check_python_syntax import check


class PythonSyntaxCheckerTests(unittest.TestCase):
    def test_excludes_bundled_lo_extract_python_stdlib(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bundled = root / "work" / "lo-extract2" / "program" / "python-core-3.13.15" / "lib"
            bundled.mkdir(parents=True)
            (bundled / "stdlib.py").write_text("def broken(:\n    pass\n", encoding="utf-8")
            (root / "project.py").write_text("value = 1\n", encoding="utf-8")

            result = check(root)

        self.assertTrue(result["ok"])
        self.assertEqual(result["checked"], 1)


if __name__ == "__main__":
    unittest.main()
