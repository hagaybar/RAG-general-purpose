import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
from pathlib import Path
import sys
import tempfile


# Go up one level from tests_jules to the project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
from scripts.ingestion.email_loader import load_eml


# Assuming the function is in a module called 'email_loader'


class TestLoadEml(unittest.TestCase):
    """Test cases for the load_eml function."""
    
    def setUp(self):
        """Set up test fixtures directory path."""
        self.fixtures_dir = Path("tests_jules/fixtures/emails")
        self.plain_email_path = self.fixtures_dir / "plain_email.eml"
        self.empty_email_path = self.fixtures_dir / "empty_email.eml"
    
    def test_plain_email_returns_text(self):
        """Test that a plain email returns the expected text content."""
        # Skip if the test file doesn't exist yet
        if not self.plain_email_path.exists():
            self.skipTest(f"Test file {self.plain_email_path} not found")
        
        text, metadata = load_eml(self.plain_email_path)
        
        # Check that we get some text content
        self.assertIsInstance(text, str)
        self.assertGreater(len(text), 0)
        
        # Check metadata structure
        self.assertIsInstance(metadata, dict)
        self.assertEqual(set(metadata.keys()), {"source", "content_type"})
        self.assertEqual(metadata["source"], str(self.plain_email_path))
        self.assertEqual(metadata["content_type"], "email")
    
    def test_empty_email_returns_empty_string(self):
        """Test that an empty email returns empty string with correct metadata."""
        # Skip if the test file doesn't exist yet
        if not self.empty_email_path.exists():
            self.skipTest(f"Test file {self.empty_email_path} not found")
        
        text, metadata = load_eml(self.empty_email_path)
        
        # Check that we get empty text
        self.assertEqual(text, "")
        
        # Check metadata structure - Assert metadata keys are exactly {"source", "content_type"}
        self.assertIsInstance(metadata, dict)
        self.assertEqual(set(metadata.keys()), {"source", "content_type"})
        self.assertEqual(metadata["source"], str(self.empty_email_path))
        self.assertEqual(metadata["content_type"], "email")
    
    def test_string_path_input(self):
        """Test that function accepts string path input."""
        with patch('pathlib.Path.open', mock_open(read_data=b'Subject: Test\n\nHello world')):
            with patch('email.parser.BytesParser.parse') as mock_parse:
                # Mock a simple non-multipart message
                mock_msg = MagicMock()
                mock_msg.is_multipart.return_value = False
                mock_body = MagicMock()
                mock_body.get_content.return_value = "Hello world"
                mock_msg.get_body.return_value = mock_body
                mock_parse.return_value = mock_msg
                
                text, metadata = load_eml("test.eml")
                
                self.assertEqual(text, "Hello world")
                self.assertEqual(metadata["source"], "test.eml")
                self.assertEqual(metadata["content_type"], "email")
    
    def test_pathlib_path_input(self):
        """Test that function accepts Path object input."""
        test_path = Path("test.eml")
        with patch('pathlib.Path.open', mock_open(read_data=b'Subject: Test\n\nHello world')):
            with patch('email.parser.BytesParser.parse') as mock_parse:
                # Mock a simple non-multipart message
                mock_msg = MagicMock()
                mock_msg.is_multipart.return_value = False
                mock_body = MagicMock()
                mock_body.get_content.return_value = "Hello world"
                mock_msg.get_body.return_value = mock_body
                mock_parse.return_value = mock_msg
                
                text, metadata = load_eml(test_path)
                
                self.assertEqual(text, "Hello world")
                self.assertEqual(metadata["source"], str(test_path))
                self.assertEqual(metadata["content_type"], "email")
    
    def test_multipart_email_extracts_text_plain(self):
        """Test that multipart email correctly extracts text/plain content."""
        with patch('pathlib.Path.open', mock_open(read_data=b'multipart email')):
            with patch('email.parser.BytesParser.parse') as mock_parse:
                # Mock a multipart message
                mock_msg = MagicMock()
                mock_msg.is_multipart.return_value = True
                
                # Mock parts - HTML part first, then text/plain
                mock_html_part = MagicMock()
                mock_html_part.get_content_type.return_value = "text/html"
                
                mock_text_part = MagicMock()
                mock_text_part.get_content_type.return_value = "text/plain"
                mock_text_part.get_content.return_value = "  Plain text content  "
                
                mock_msg.walk.return_value = [mock_html_part, mock_text_part]
                mock_parse.return_value = mock_msg
                
                text, metadata = load_eml("test.eml")
                
                self.assertEqual(text, "Plain text content")  # Should be stripped
                self.assertEqual(metadata["content_type"], "email")
    
    def test_multipart_email_no_text_plain_returns_empty(self):
        """Test that multipart email with no text/plain parts returns empty string."""
        with patch('pathlib.Path.open', mock_open(read_data=b'multipart email')):
            with patch('email.parser.BytesParser.parse') as mock_parse:
                # Mock a multipart message with only HTML
                mock_msg = MagicMock()
                mock_msg.is_multipart.return_value = True
                
                mock_html_part = MagicMock()
                mock_html_part.get_content_type.return_value = "text/html"
                
                mock_msg.walk.return_value = [mock_html_part]
                mock_parse.return_value = mock_msg
                
                text, metadata = load_eml("test.eml")
                
                self.assertEqual(text, "")
                self.assertEqual(metadata["content_type"], "email")
    
    def test_whitespace_stripping(self):
        """Test that whitespace is properly stripped from content."""
        with patch('pathlib.Path.open', mock_open(read_data=b'email with whitespace')):
            with patch('email.parser.BytesParser.parse') as mock_parse:
                # Mock message with whitespace
                mock_msg = MagicMock()
                mock_msg.is_multipart.return_value = False
                mock_body = MagicMock()
                mock_body.get_content.return_value = "   \n\nContent with whitespace\n\n   "
                mock_msg.get_body.return_value = mock_body
                mock_parse.return_value = mock_msg
                
                text, metadata = load_eml("test.eml")
                
                self.assertEqual(text, "Content with whitespace")
    
    def test_file_not_found_raises_exception(self):
        """Test that FileNotFoundError is raised for non-existent files."""
        with self.assertRaises(FileNotFoundError):
            load_eml("non_existent_file.eml")
    
    def test_return_types(self):
        """Test that function returns correct types."""
        with patch('pathlib.Path.open', mock_open(read_data=b'Subject: Test\n\nTest content')):
            with patch('email.parser.BytesParser.parse') as mock_parse:
                mock_msg = MagicMock()
                mock_msg.is_multipart.return_value = False
                mock_body = MagicMock()
                mock_body.get_content.return_value = "Test content"
                mock_msg.get_body.return_value = mock_body
                mock_parse.return_value = mock_msg
                
                result = load_eml("test.eml")
                
                # Check return type is tuple
                self.assertIsInstance(result, tuple)
                self.assertEqual(len(result), 2)
                
                text, metadata = result
                self.assertIsInstance(text, str)
                self.assertIsInstance(metadata, dict)


if __name__ == '__main__':
    unittest.main()