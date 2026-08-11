import io
import tempfile
import unittest
from unittest.mock import Mock, patch

from app import app, extract_text_from_pdf


class PdfExtractionTests(unittest.TestCase):
    def test_extracts_and_combines_text_from_pages(self):
        first_page = Mock()
        first_page.extract_text.return_value = "Jane Doe\nSoftware Engineer"
        empty_page = Mock()
        empty_page.extract_text.return_value = ""
        last_page = Mock()
        last_page.extract_text.return_value = "Experience and education"

        fake_reader = Mock()
        fake_reader.is_encrypted = False
        fake_reader.pages = [first_page, empty_page, last_page]

        with patch("app.PdfReader", return_value=fake_reader):
            extracted_text = extract_text_from_pdf("resume.pdf")

        self.assertEqual(
            extracted_text,
            "Jane Doe\nSoftware Engineer\n\nExperience and education",
        )

    def test_upload_renders_message_when_extraction_returns_no_text(self):
        app.config["TESTING"] = True
        client = app.test_client()

        with tempfile.TemporaryDirectory() as upload_folder:
            app.config["UPLOAD_FOLDER"] = upload_folder
            with patch("app.extract_text_from_pdf", return_value=""):
                response = client.post(
                    "/upload-resume",
                    data={"resume": (io.BytesIO(b"PDF contents"), "resume.pdf")},
                    content_type="multipart/form-data",
                )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Resume uploaded successfully.", response.data)
        self.assertIn(b"Could not extract readable text", response.data)


if __name__ == "__main__":
    unittest.main()