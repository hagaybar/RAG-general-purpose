import unittest
import os
from pathlib import Path
import sys
import os


# Go up one level from tests_jules to the project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
from scripts.ingestion.email_loader import load_eml


class TestEmailLoader(unittest.TestCase):
    def setUp(self):
        self.fixtures_dir = Path("tests_jules/fixtures/emails")
        os.makedirs(self.fixtures_dir, exist_ok=True)
        self.plain_email_path = self.fixtures_dir / "plain_email.eml"
        self.empty_email_path = self.fixtures_dir / "empty_email.eml"

    def test_plain_email_returns_text(self):
        text, metadata = load_eml(self.plain_email_path)
        self.assertEqual(text, "This is a test email with plain text content.")
        self.assertEqual(set(metadata.keys()), {"source", "content_type"})

    def test_empty_email_returns_empty_string(self):
        text, metadata = load_eml(self.empty_email_path)
        self.assertEqual(text, "")
        self.assertEqual(set(metadata.keys()), {"source", "content_type"})

    def tearDown(self):
        try:
            os.remove(self.plain_email_path)
        except FileNotFoundError:
            pass  # Or log a warning, or re-raise if this is unexpected
        try:
            os.remove(self.empty_email_path)
        except FileNotFoundError:
            pass  # Or log a warning, or re-raise if this is unexpected

if __name__ == '__main__':
    unittest.main()
