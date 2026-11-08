import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest


class UITests(unittest.TestCase):
    def test_demo_and_exports(self):
        app = AppTest.from_file(
            str(Path(__file__).resolve().parents[1] / "app.py")
        ).run(timeout=30)
        self.assertFalse(app.exception)
        self.assertGreaterEqual(len(app.download_button), 5)

    def test_search_interaction(self):
        app = AppTest.from_file(
            str(Path(__file__).resolve().parents[1] / "app.py")
        ).run(timeout=30)
        next(x for x in app.text_input if x.label == "Search the transcript").set_value(
            "overfitting"
        ).run()
        self.assertFalse(app.exception)
