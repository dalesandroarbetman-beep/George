import re
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOTS = (
    ROOT / "video-script-workflow" / "skills",
    ROOT / "jewelry-listing" / "skills",
    ROOT / "GEO优化发布大师" / "skills",
)


class SkillInventoryTests(unittest.TestCase):
    def test_all_skills_are_in_standard_directory_and_names_match(self):
        files = sorted(path for root in SKILL_ROOTS for path in root.glob("*/SKILL.md"))
        self.assertEqual(len(files), 12)
        for path in files:
            with self.subTest(skill=path.parent.name):
                text = path.read_text(encoding="utf-8-sig")
                match = re.search(r"^name:\s*['\"]?([^'\"\r\n]+)", text, re.MULTILINE)
                self.assertIsNotNone(match)
                self.assertEqual(match.group(1).strip(), path.parent.name)

    def test_markdown_references_resolve_inside_each_skill(self):
        pattern = re.compile(r"\[[^]]+\]\((references/[^)#]+)")
        for skill_file in sorted(path for root in SKILL_ROOTS for path in root.glob("*/SKILL.md")):
            text = skill_file.read_text(encoding="utf-8-sig")
            for relative in pattern.findall(text):
                with self.subTest(skill=skill_file.parent.name, reference=relative):
                    self.assertTrue((skill_file.parent / relative).is_file())

    def test_contract_schemas_are_valid_json_and_have_ids(self):
        files = sorted(path for root in (
            ROOT / "video-script-workflow" / "contracts",
            ROOT / "jewelry-listing" / "contracts",
            ROOT / "GEO优化发布大师" / "contracts",
        ) for path in root.glob("*.schema.json"))
        self.assertEqual(len(files), 4)
        for path in files:
            with self.subTest(contract=path.name):
                data = json.loads(path.read_text(encoding="utf-8"))
                self.assertTrue(data.get("$id"))
                self.assertEqual(data.get("type"), "object")


if __name__ == "__main__":
    unittest.main()
