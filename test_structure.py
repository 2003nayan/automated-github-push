"""
Simple test to verify the code structure works
"""
import unittest
import tempfile
import shutil
from pathlib import Path

# Test imports work
try:
    from config import Config
    from backup_service import BackupService
    from git_service import GitService
    from github_service import GitHubService
    from folder_watcher import FolderWatcher
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")

class TestStructure(unittest.TestCase):

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_config_creation(self):
        """Test configuration creation"""
        config = Config()
        self.assertIsNotNone(config)
        self.assertTrue(hasattr(config, 'get'))
        self.assertTrue(hasattr(config, 'validate'))

    def test_services_creation(self):
        """Test that services can be created"""
        config = Config()

        # These might fail due to missing dependencies, but should be importable
        git_service = GitService(config)
        github_service = GitHubService(config)

        self.assertIsNotNone(git_service)
        self.assertIsNotNone(github_service)

if __name__ == '__main__':
    # Just run the import test
    print("🧪 Running basic structure test...")
    unittest.main(verbosity=2)
