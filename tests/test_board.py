import os
import unittest
import tempfile
from buddy.board import parse_yaml_like_blocks, format_block, get_section_content, replace_section_content, claim_task, release_task

MOCK_BOARD = """# Agent Coordination Board

## Active Claims

- id: 20260714-working-task
  owner: Gemini
  status: claimed
  task: Active work
  scope: tests/

## Queue

- id: 20260714-queued-task
  owner: unclaimed
  status: ready
  task: Queued work
  scope: src/

## Blocked

No blocked coordination tasks.

## Done

- 2026-07-14: Codex completed task `old-task`
"""

class TestBoard(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.board_path = os.path.join(self.temp_dir.name, "Board.md")
        with open(self.board_path, "w", encoding="utf-8") as f:
            f.write(MOCK_BOARD)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_parse_blocks(self):
        blocks = parse_yaml_like_blocks(MOCK_BOARD)
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0]["id"], "20260714-working-task")
        self.assertEqual(blocks[1]["id"], "20260714-queued-task")

    def test_get_section(self):
        active = get_section_content(MOCK_BOARD, "Active Claims")
        self.assertTrue("- id: 20260714-working-task" in active)

    def test_replace_section(self):
        replaced = replace_section_content(MOCK_BOARD, "Active Claims", "No active claims.")
        self.assertTrue("No active claims." in replaced)
        self.assertFalse("- id: 20260714-working-task" in replaced)

    def test_claim_existing_task(self):
        success = claim_task(self.board_path, "20260714-queued-task", "OpenClaw")
        self.assertTrue(success)
        with open(self.board_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Verify it moved from Queue to Active Claims
        active = get_section_content(content, "Active Claims")
        queue = get_section_content(content, "Queue")
        self.assertTrue("20260714-queued-task" in active)
        self.assertFalse("20260714-queued-task" in queue)
        self.assertTrue("owner: OpenClaw" in active)

    def test_release_task_done(self):
        success = release_task(self.board_path, "20260714-working-task", "done")
        self.assertTrue(success)
        with open(self.board_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        active = get_section_content(content, "Active Claims")
        done = get_section_content(content, "Done")
        self.assertFalse("20260714-working-task" in active)
        self.assertTrue("completed task `20260714-working-task`" in done)

if __name__ == "__main__":
    unittest.main()
