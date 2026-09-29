"""Focused import-only checks for the migrated finish_scene entry point."""

import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "finish_scene.py"
TASK = SCRIPT.parents[2]
REPO = TASK.parents[3]


def import_script(path):
    spec = importlib.util.spec_from_file_location("finish_scene_entry_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FinishSceneEntryTest(unittest.TestCase):
    def test_import_binds_active_repository_dependencies(self):
        module = import_script(SCRIPT)
        self.assertEqual(module.REPO, REPO)
        self.assertEqual(module.SOURCE, TASK / "source")
        self.assertEqual(
            module.READER,
            REPO / "task-packages/PKG-B-ALG/payload/model/python/h1_reader.py",
        )
        self.assertTrue((module.SOURCE / "export_four.py").is_file())
        self.assertTrue(module.READER.is_file())
        self.assertEqual(Path(module.export.__code__.co_filename).resolve(),
                         (module.SOURCE / "export_four.py").resolve())

    def test_missing_active_marker_fails_before_dependency_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copied = root / "task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/background-target-stop-20260917/finish_scene.py"
            copied.parent.mkdir(parents=True)
            shutil.copyfile(SCRIPT, copied)
            with self.assertRaisesRegex(RuntimeError, "Invalid SoundSight repository root"):
                import_script(copied)

    def test_wrong_task_layout_fails_with_active_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            marker = root / "document/team-workflow.md"
            marker.parent.mkdir(parents=True)
            marker.touch()
            copied = root / "task-packages/PKG-A-ACQ/tasks/wrong-task/batches/background-target-stop-20260917/finish_scene.py"
            copied.parent.mkdir(parents=True)
            shutil.copyfile(SCRIPT, copied)
            with self.assertRaisesRegex(RuntimeError, "Invalid SoundSight repository root"):
                import_script(copied)


if __name__ == "__main__":
    unittest.main()
