from pathlib import Path
import tempfile
import unittest
from streamlit.testing.v1 import AppTest
from reports import make_demo


class AppTests(unittest.TestCase):
    def test_review_and_export_workflow(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'run'; make_demo(root)
            source=Path('app.py').read_text().replace("'outputs/demo'",repr(str(root)))
            app=AppTest.from_string(source).run(timeout=20)
            self.assertFalse(app.exception)
            self.assertEqual(app.selectbox[0].value,1)
            app.text_input[1].set_value('Synthetic Test Reviewer').run()
            app.button[0].click().run()
            self.assertEqual(len(list((root/'reviews').glob('*.json'))),1)
            app.button[1].click().run()
            self.assertEqual(len(list(root.glob('report-*.html'))),1)
            self.assertFalse(app.exception)
