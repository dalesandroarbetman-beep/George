import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT / "skills/geo-optimization-publisher/scripts/geo_workflow.py"
SPEC = importlib.util.spec_from_file_location("geo_workflow", SCRIPT)
geo_workflow = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(geo_workflow)


class GeoWorkflowTests(unittest.TestCase):
    def test_current_project_validates(self):
        manifest_path = PROJECT / "output/geo-program/yohodiy-20260918/workflow_manifest.json"
        manifest, errors, _, events = geo_workflow.validate_project(PROJECT, manifest_path)
        self.assertEqual([], errors)
        states = []
        for item in manifest["items"]:
            content_hash = geo_workflow.sha256(PROJECT / item["variant_path"])
            states.append(geo_workflow.derive_item_state(item, events, content_hash))
        self.assertEqual(["draft", "draft", "draft"], states)

    def test_publish_package_rejects_unapproved_items(self):
        manifest_path = PROJECT / "output/geo-program/yohodiy-20260918/workflow_manifest.json"
        manifest, errors, _, events = geo_workflow.validate_project(PROJECT, manifest_path)
        self.assertEqual([], errors)
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                geo_workflow.package_files(PROJECT, manifest, events, Path(temp) / "publish.zip", "publish")

    def test_review_package_has_hash_manifest(self):
        manifest_path = PROJECT / "output/geo-program/yohodiy-20260918/workflow_manifest.json"
        manifest, errors, _, events = geo_workflow.validate_project(PROJECT, manifest_path)
        self.assertEqual([], errors)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "review.zip"
            geo_workflow.package_files(PROJECT, manifest, events, output, "review")
            import zipfile

            with zipfile.ZipFile(output) as archive:
                payload = json.loads(archive.read("package_manifest.json"))
            self.assertFalse(payload["publishable"])
            self.assertTrue(payload["files"])
            self.assertTrue(all(len(item["sha256"]) == 64 for item in payload["files"]))

    def test_approval_cannot_promote_experimental_item(self):
        manifest_path = PROJECT / "output/geo-program/yohodiy-20260918/workflow_manifest.json"
        manifest, errors, _, events = geo_workflow.validate_project(PROJECT, manifest_path)
        self.assertEqual([], errors)
        item = manifest["items"][0]
        content_hash = geo_workflow.sha256(PROJECT / item["variant_path"])
        forged = {
            "event_type": "content_approval",
            "subject_id": item["content_id"],
            "content_version": item["version"],
            "platform": item["platform"],
            "community": None,
            "target_url": None,
            "content_sha256": content_hash,
            "decision": "approved",
        }
        self.assertEqual("draft", geo_workflow.derive_item_state(item, events + [forged], content_hash))

    def test_review_package_can_select_one_item(self):
        manifest_path = PROJECT / "output/geo-program/yohodiy-20260918/workflow_manifest.json"
        manifest, errors, _, events = geo_workflow.validate_project(PROJECT, manifest_path)
        self.assertEqual([], errors)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "one.zip"
            geo_workflow.package_files(PROJECT, manifest, events, output, "review", ["YOHO-TRIAL-001"])
            import zipfile

            with zipfile.ZipFile(output) as archive:
                payload = json.loads(archive.read("package_manifest.json"))
                names = archive.namelist()
            self.assertEqual(["YOHO-TRIAL-001"], payload["selected_content_ids"])
            self.assertNotIn(manifest["items"][1]["variant_path"], names)


if __name__ == "__main__":
    unittest.main()
