import os
import unittest
from buddy.config import load_config, DEFAULT_CONFIG

class TestConfig(unittest.TestCase):
    def test_default_config(self):
        config = load_config()
        self.assertEqual(
            config["memory_file"], os.path.expanduser(DEFAULT_CONFIG["memory_file"])
        )
        self.assertEqual(
            config["vault_path"], os.path.expanduser(DEFAULT_CONFIG["vault_path"])
        )
        
    def test_env_override(self):
        os.environ["BUDDY_VAULT_PATH"] = "/tmp/my_vault"
        config = load_config()
        self.assertEqual(config["vault_path"], "/tmp/my_vault")
        del os.environ["BUDDY_VAULT_PATH"]

if __name__ == "__main__":
    unittest.main()
