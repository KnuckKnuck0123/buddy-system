import os
import unittest
import tempfile
from datetime import datetime
from buddy.log import append_handoff

MOCK_LOG = """# Agent Handoff Log

## Rules
- Rules block here

## Entry Template
- Template here

## 2026-07-13

### 19:52 - Codex / task-1
- Summary: Old entry
"""

class TestLog(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self.temp_dir.name, "HandoffLog.md")
        with open(self.log_path, "w", encoding="utf-8") as f:
            f.write(MOCK_LOG)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_append_new_date(self):
        success = append_handoff(
            self.log_path,
            owner="Gemini",
            task_id="new-task",
            summary="Completed some cool stuff",
            next_step="Do more stuff",
            changed="tests/test_log.py"
        )
        self.assertTrue(success)
        
        with open(self.log_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        today_date = datetime.now().strftime("%Y-%m-%d")
        self.assertTrue(f"## {today_date}" in content)
        self.assertTrue("### " in content)
        self.assertTrue("Gemini / new-task" in content)
        self.assertTrue("Summary: Completed some cool stuff" in content)
        self.assertTrue("Changed: tests/test_log.py" in content)
        self.assertTrue("Next: Do more stuff" in content)

if __name__ == "__main__":
    unittest.main()
