import os
import json
import unittest
import tempfile
from buddy.sync import sync_conversation, update_journal_file

class TestSyncPolicy(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.journal_file = os.path.join(self.temp_dir.name, "journal.md")
        self.memory_file = os.path.join(self.temp_dir.name, "memory.json")
        self.status_file = os.path.join(self.temp_dir.name, "status.json")
        self.vault_path = self.temp_dir.name

        # Create dummy memory json
        with open(self.memory_file, "w", encoding="utf-8") as f:
            json.dump({"operational_rules": [], "technical_additions": [], "active_projects": {}}, f)

        # Mock brain dir with transcript
        self.brain_dir = os.path.join(self.temp_dir.name, "brain")
        self.conv_id = "test-conv-123"
        self.conv_path = os.path.join(self.brain_dir, self.conv_id)
        self.logs_dir = os.path.join(self.conv_path, ".system_generated", "logs")
        os.makedirs(self.logs_dir, exist_ok=True)

        # Create dummy transcript
        self.transcript_path = os.path.join(self.logs_dir, "transcript.jsonl")
        with open(self.transcript_path, "w", encoding="utf-8") as f:
            f.write(json.dumps({"type": "USER_INPUT", "source": "USER_EXPLICIT", "content": "Hello, work on [rule] Always verify code with unit tests."}) + "\n")
            f.write(json.dumps({"type": "USER_INPUT", "source": "USER_EXPLICIT", "content": "[tech] PyTest unit testing frame"}) + "\n")

        self.config = {
            "memory_file": self.memory_file,
            "journal_file": self.journal_file,
            "status_file": self.status_file,
            "vault_path": self.vault_path,
            "brain_dirs": [self.brain_dir],
            "codex_sessions_root": os.path.join(self.temp_dir.name, "codex"),
            "opencode_db": os.path.join(self.temp_dir.name, "opencode.db"),
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_sync_subagent_and_harness(self):
        res = sync_conversation(
            self.conv_id,
            user_summary="Completed test implementation",
            next_steps="Run test suite",
            config=self.config,
            harness_override="gemini",
            parent_conv_id="parent-session-999",
            subagent_role="Test Engineer"
        )
        self.assertTrue(res)

        with open(self.journal_file, "r", encoding="utf-8") as f:
            journal_content = f.read()

        self.assertIn("### 🛠️ Session Archive: test-conv-123", journal_content)
        self.assertIn("* **Parent Session**: `parent-session-999`", journal_content)
        self.assertIn("* **Subagent Role**: `Test Engineer`", journal_content)
        self.assertIn("* **Summary**: Completed test implementation", journal_content)
        self.assertIn("* **Next Steps**: Run test suite", journal_content)

        with open(self.memory_file, "r", encoding="utf-8") as f:
            mem_data = json.load(f)

        self.assertIn("Always verify code with unit tests.", mem_data["operational_rules"])
        self.assertIn("PyTest unit testing frame", mem_data["technical_additions"])

    def test_idempotent_journal_update(self):
        # Initial sync
        sync_conversation(
            self.conv_id,
            user_summary="Initial summary",
            next_steps="Initial next steps",
            config=self.config
        )

        # Re-sync (mid-session update / checkpoint)
        sync_conversation(
            self.conv_id,
            user_summary="Updated summary milestone",
            next_steps="Final next steps",
            config=self.config
        )

        with open(self.journal_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Should only have one header for test-conv-123
        header_count = content.count(f"### 🛠️ Session Archive: {self.conv_id}")
        self.assertEqual(header_count, 1)
        self.assertIn("Updated summary milestone", content)
        self.assertNotIn("Initial summary", content)

    def test_garbage_filtering(self):
        from buddy.sync import clean_and_filter_prompt, is_garbage_file, is_garbage_command

        self.assertIsNone(clean_and_filter_prompt("You have viewed or edited files, which are associated with..."))
        self.assertIsNone(clean_and_filter_prompt("<ADDITIONAL_METADATA>\ntime: 123\n</ADDITIONAL_METADATA>"))
        self.assertEqual(clean_and_filter_prompt("<USER_REQUEST>\nFix the budget calculations\n</USER_REQUEST>"), "Fix the budget calculations")

        self.assertTrue(is_garbage_file(".DS_Store"))
        self.assertTrue(is_garbage_file("/path/to/pruner_status.json"))
        self.assertFalse(is_garbage_file("main.py"))

        self.assertTrue(is_garbage_command("which buddy"))
        self.assertTrue(is_garbage_command("pwd"))
        self.assertFalse(is_garbage_command("pytest tests/"))

if __name__ == "__main__":
    unittest.main()
