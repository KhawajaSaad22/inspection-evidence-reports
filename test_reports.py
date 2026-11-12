import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from reports import make_demo,load_run,heatmap,save_review,reviews_for,export_html,asset


class ReportTests(unittest.TestCase):
    def test_review_binding_and_escaped_portable_export(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'run'; make_demo(root); _,_,rows=load_run(root); row=rows[1]
            save_review(root,row,'confirmed','Reviewer','<script>alert(1)</script>')
            self.assertEqual(len(reviews_for(root,row)[0]),1)
            out=export_html(root,Path(folder)/'report.html'); text=out.read_text(encoding='utf-8')
            self.assertIn('data:image/png;base64,',text)
            self.assertIn('&lt;script&gt;',text); self.assertNotIn('<script>',text)
            np.save(root/row['heatmap'],np.zeros((64,64),np.uint8))
            valid,stale=reviews_for(root,row)
            self.assertFalse(valid); self.assertEqual(len(stale),1)

    def test_packed_grid_and_path_guards(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'run'; make_demo(root); _,_,rows=load_run(root)
            (root/'heatmaps/maps.bin').write_bytes(bytes(4096)+bytes([200])*4096)
            row={**rows[1],'heatmap':'heatmaps/maps.bin','heatmap_offset_bytes':4096}
            self.assertEqual(int(heatmap(root,row).max()),200)
            with self.assertRaises(ValueError): heatmap(root,{**row,'heatmap_offset_bytes':8192})
            with self.assertRaises(ValueError): asset(root,'../outside.png')
            with self.assertRaises(ValueError): export_html(root,root/'run.json')

    def test_manifest_duplicate_ids_and_invalid_reviewer(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'run'; make_demo(root); _,_,rows=load_run(root)
            with self.assertRaises(ValueError): save_review(root,rows[1],'confirmed',' ')
            with (root/'frames.jsonl').open('a') as stream: stream.write(json.dumps(rows[0])+'\n')
            with self.assertRaisesRegex(ValueError,'unique'): load_run(root)
