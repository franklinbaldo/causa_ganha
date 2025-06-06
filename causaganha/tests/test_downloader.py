import unittest
from unittest.mock import patch, MagicMock, call
import pathlib
import datetime
import requests # Required for requests.exceptions.RequestException
import sys
import shutil # For tearDown
import logging # Added import (one instance)

# Ensure the project root is in sys.path for imports
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from causaganha.core.downloader import fetch_tjro_pdf, fetch_latest_tjro_pdf

# Suppress logging output during tests
logging.disable(logging.CRITICAL)

class TestFetchTjroPdf(unittest.TestCase):
    def setUp(self):
        self.test_date = datetime.date(2024, 7, 25)
        # Define a specific dummy directory for downloader tests
        self.dummy_data_root = PROJECT_ROOT / "causaganha_test_data" # temp root for test data
        self.download_dir = self.dummy_data_root / "data" / "diarios"

        # Create the dummy directory if it doesn't exist
        self.download_dir.mkdir(parents=True, exist_ok=True)

        # Override the output_dir logic within fetch_tjro_pdf by patching pathlib.Path
        # This is to ensure downloaded files go to our controlled test directory.
        # The original downloader.py has:
        # output_dir = pathlib.Path(__file__).resolve().parent.parent / "data" / "diarios"
        # We need to make sure this path points to self.download_dir during the test.
        # A robust way is to patch the specific `pathlib.Path` instantiation that builds `output_dir`
        # or to pass `output_dir` as an argument to `fetch_tjro_pdf` (if refactored).
        # For now, let's assume fetch_tjro_pdf can be refactored or we patch carefully.
        # Simpler for now: fetch_tjro_pdf will create files relative to where it *thinks*
        # `causaganha/data/diarios` is. We will check for that file and then clean it up.
        # The current `fetch_tjro_pdf` uses `pathlib.Path(__file__).resolve().parent.parent / "data" / "diarios"`
        # So, it will try to write into the real `causaganha/data/diarios` if this test file is in `causaganha/tests`.
        # This is acceptable for now, and tearDown will clean it.

        # Expected file name based on test_date
        self.expected_file_name = f"dj_{self.test_date.strftime('%Y%m%d')}.pdf"
        self.expected_file_path = self.download_dir / self.expected_file_name

        # Ensure no leftover file from previous tests
        if self.expected_file_path.exists():
            self.expected_file_path.unlink()

    def tearDown(self):
        # Remove the dummy directory and its contents after tests
        if self.dummy_data_root.exists():
            shutil.rmtree(self.dummy_data_root)

        # Also clean up any file that might have been created in the actual data path
        # due to the non-patched output_dir logic in the current fetch_tjro_pdf
        actual_data_dir_in_project = PROJECT_ROOT / "causaganha" / "data" / "diarios"
        leftover_file_in_actual_dir = actual_data_dir_in_project / self.expected_file_name
        if leftover_file_in_actual_dir.exists():
            leftover_file_in_actual_dir.unlink()


    @patch('requests.get')
    def test_successful_download(self, mock_requests_get):
        # Mock the HTML page that contains the PDF link
        html_content = (
            "<a href='https://www.tjro.jus.br/novodiario/2024/20240725001-NR100.pdf'>PDF</a>"
        )
        mock_page_response = MagicMock()
        mock_page_response.status_code = 200
        mock_page_response.text = html_content
        mock_page_response.raise_for_status = MagicMock()

        # Mock the actual PDF download response
        mock_pdf_response = MagicMock()
        mock_pdf_response.status_code = 200
        mock_pdf_response.content = b'pdf dummy content'
        mock_pdf_response.raise_for_status = MagicMock()

        mock_requests_get.side_effect = [mock_page_response, mock_pdf_response]

        # --- Mocking pathlib.Path to control output directory ---
        # When `pathlib.Path(__file__).resolve().parent.parent / "data" / "diarios"` is called
        # in downloader.py, we want it to resolve to our test download directory.
        # Let's make `Path().resolve().parent.parent / "data" / "diarios"` return `self.download_dir`

        # This is a bit tricky. The `Path(__file__)...` is one chain.
        # Let's assume `output_dir` inside `fetch_tjro_pdf` will be `self.download_dir`
        # by controlling what `Path( ... ) / "data" / "diarios"` returns.
        # A simpler way: the `output_dir` is `pathlib.Path(__file__).resolve().parent.parent / "data" / "diarios"`
        # The `__file__` in `downloader.py` is `.../causaganha/core/downloader.py`.
        # So `parent.parent` is `.../causaganha/`.
        # So `output_dir` becomes `.../causaganha/data/diarios/`.
        # We can patch `pathlib.Path.mkdir` and `pathlib.Path.open` if direct path patching is too complex.

        # For this test, we'll assume `fetch_tjro_pdf` writes to a predictable location
        # that we can check and clean up. The `self.expected_file_path` is set up to use
        # `self.download_dir`. We need to ensure `fetch_tjro_pdf` uses this.
        # The most straightforward way is to modify `fetch_tjro_pdf` to accept `output_dir`
        # or to perform a more complex patch of `pathlib.Path`.

        # Let's patch the `output_dir` object inside `fetch_tjro_pdf` after it's constructed.
        # No, that's not feasible from here.
        # We will rely on `fetch_tjro_pdf` writing to its default location, and then check that file.
        # The `tearDown` will clean it. The `setUp` makes `self.expected_file_path` point to `self.download_dir`.
        # This test will pass if `fetch_tjro_pdf` *actually* writes to `self.download_dir`.
        # The current `fetch_tjro_pdf` writes to `PROJECT_ROOT/causaganha/data/diarios`.
        # So, we adjust `self.expected_file_path` for this test.

        real_output_dir = PROJECT_ROOT / "causaganha" / "data" / "diarios"
        real_expected_file_path = real_output_dir / self.expected_file_name
        if real_expected_file_path.exists(): # Clean before test
             real_expected_file_path.unlink()

        # Make the mock_path_constructor return our controlled path for the final output file
        # This means when `output_dir / file_name` is called, it resolves to our test path.
        # We need `output_dir` to be our `self.download_dir`
        # Let's assume the `Path(__file__)...` part resolves, and then `output_dir / file_name` is called.
        # Patch the final `open` call on the Path object.

        # This is getting complicated. Let's simplify:
        # The test will check the *actual default path* used by `fetch_tjro_pdf`.
        # `setUp` and `tearDown` will manage files in that *actual default path*.
        self.download_dir = PROJECT_ROOT / "causaganha" / "data" / "diarios"
        self.download_dir.mkdir(parents=True, exist_ok=True) # Ensure actual dir exists
        self.expected_file_path = self.download_dir / self.expected_file_name
        if self.expected_file_path.exists():
            self.expected_file_path.unlink()


        result_path = fetch_tjro_pdf(self.test_date)

        # Assertions
        self.assertEqual(result_path, self.expected_file_path)
        self.assertTrue(self.expected_file_path.exists())
        with open(self.expected_file_path, 'rb') as f:
            content = f.read()
            self.assertEqual(content, b'pdf dummy content')

        expected_pdf_url = (
            "https://www.tjro.jus.br/novodiario/2024/20240725001-NR100.pdf"
        )
        self.assertEqual(
            mock_requests_get.call_args_list,
            [
                call("https://www.tjro.jus.br/diario_oficial/", timeout=30),
                call(expected_pdf_url, timeout=30),
            ],
        )
        mock_page_response.raise_for_status.assert_called_once()
        mock_pdf_response.raise_for_status.assert_called_once()

        # Clean up the created file
        if self.expected_file_path.exists():
            self.expected_file_path.unlink()

    @patch('requests.get')
    def test_download_failure_404(self, mock_requests_get):
        html_content = (
            "<a href='https://www.tjro.jus.br/novodiario/2024/20240725001-NR100.pdf'>PDF</a>"
        )
        mock_page_response = MagicMock()
        mock_page_response.status_code = 200
        mock_page_response.text = html_content
        mock_page_response.raise_for_status = MagicMock()

        mock_pdf_response = MagicMock()
        mock_pdf_response.status_code = 404
        mock_pdf_response.raise_for_status = MagicMock(
            side_effect=requests.exceptions.HTTPError("404 Client Error")
        )

        mock_requests_get.side_effect = [mock_page_response, mock_pdf_response]

        self.download_dir = PROJECT_ROOT / "causaganha" / "data" / "diarios"
        self.expected_file_path = self.download_dir / self.expected_file_name # Used for cleanup check

        result_path = fetch_tjro_pdf(self.test_date)

        self.assertIsNone(result_path)
        self.assertFalse(self.expected_file_path.exists())

        expected_pdf_url = "https://www.tjro.jus.br/novodiario/2024/20240725001-NR100.pdf"
        self.assertEqual(
            mock_requests_get.call_args_list,
            [
                call("https://www.tjro.jus.br/diario_oficial/", timeout=30),
                call(expected_pdf_url, timeout=30),
            ],
        )
        mock_page_response.raise_for_status.assert_called_once()
        mock_pdf_response.raise_for_status.assert_called_once()  # raise_for_status is called, then exception handled

    @patch('requests.get')
    def test_download_request_exception(self, mock_requests_get):
        mock_requests_get.side_effect = requests.exceptions.RequestException("Connection error")

        self.download_dir = PROJECT_ROOT / "causaganha" / "data" / "diarios"
        self.expected_file_path = self.download_dir / self.expected_file_name

        result_path = fetch_tjro_pdf(self.test_date)

        self.assertIsNone(result_path)
        self.assertFalse(self.expected_file_path.exists())

        self.assertEqual(
            mock_requests_get.call_args_list,
            [call("https://www.tjro.jus.br/diario_oficial/", timeout=30)],
        )


class TestFetchLatestTjroPdf(unittest.TestCase):
    def setUp(self):
        self.dummy_data_root = PROJECT_ROOT / "causaganha_test_data_latest"
        self.download_dir = self.dummy_data_root / "data" / "diarios"
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.expected_file_name = "dj_20240725.pdf"
        self.expected_file_path = self.download_dir / self.expected_file_name

    def tearDown(self):
        if self.dummy_data_root.exists():
            shutil.rmtree(self.dummy_data_root)
        real_path = PROJECT_ROOT / "causaganha" / "data" / "diarios" / self.expected_file_name
        if real_path.exists():
            real_path.unlink()

    @patch('causaganha.core.downloader.fetch_tjro_pdf')
    @patch('requests.get')
    def test_fetch_latest_success(self, mock_get, mock_fetch):
        html_content = (
            "<a href='https://www.tjro.jus.br/novodiario/2024/20240725001-NR100.pdf'>PDF</a>"
        )
        mock_page = MagicMock()
        mock_page.status_code = 200
        mock_page.text = html_content
        mock_page.raise_for_status = MagicMock()

        self.download_dir = PROJECT_ROOT / "causaganha" / "data" / "diarios"
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.expected_file_path = self.download_dir / self.expected_file_name
        mock_get.return_value = mock_page
        mock_fetch.return_value = self.expected_file_path
        if self.expected_file_path.exists():
            self.expected_file_path.unlink()

        result = fetch_latest_tjro_pdf()

        self.assertEqual(result, self.expected_file_path)
        self.assertEqual(
            mock_get.call_args_list,
            [call("https://www.tjro.jus.br/diario_oficial/ultimo-diario.php", timeout=30)],
        )
        mock_fetch.assert_called_once_with(datetime.date(2024, 7, 25))
        mock_page.raise_for_status.assert_called_once()


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
