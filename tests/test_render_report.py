import copy
import base64
import tempfile
import importlib.util
import json
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('renderer', ROOT/'scripts/render_report.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)

class RendererTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT/'assets/example-report.json').read_text())

    def test_complete_example_offline_native_controls(self):
        out = r.render(self.data)
        self.assertIn('虚构示例', out)
        self.assertIn('<details>', out)
        self.assertNotIn('<details open', out)
        self.assertIn('data-label="方向"', out)
        self.assertIn('区间 12–28 美元', out)
        self.assertIn('中位 19.5 美元', out)
        self.assertNotIn('preventDefault', out)
        self.assertNotIn('replaceState', out)
        self.assertNotIn('src="http', out)

    def test_input_cannot_inject_markup_or_script(self):
        self.data['title'] = '<script>alert("x")</script>'
        self.data['sections'][0]['blocks'][0]['items'][0]['points'][0] = '<img src=x onerror=alert(1)>'
        self.data['links'] = [{'text':'<click>', 'url':'https://example.com/?q=" onmouseover="x'}]
        with self.assertRaises(ValueError): r.render(self.data)  # spaces rejected in URL
        self.data['links'][0]['url'] = 'https://example.com/?q="x"'
        out = r.render(self.data)
        self.assertIn('&lt;script&gt;', out)
        self.assertIn('&lt;img', out)
        self.assertIn('q=&quot;x&quot;', out)
        self.assertEqual(out.count('<script>'), 1)

    def test_bad_urls_rejected(self):
        for url in ('javascript:alert(1)', 'data:text/html,x', '//example.com', '/local', 'https://user:pass@example.com', 'https://example.com/\nhi'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                r.link({'text':'source','url':url})

    def test_required_editorial_structure(self):
        for field in ('subtitle', 'key_points'):
            d = copy.deepcopy(self.data)
            del d['sections'][0][field]
            with self.assertRaises(ValueError): r.render(d)
        self.data['sections'][0]['blocks'] = [{'type':'paragraphs','paragraphs':['long text']*8}]
        with self.assertRaises(ValueError): r.render(self.data)

    def test_collapsed_core_rejected(self):
        self.data['sections'][0]['blocks'] = [{'type':'details','title':'all conclusions','blocks':[{'type':'notes','items':['hidden']}]}]
        with self.assertRaises(ValueError): r.render(self.data)

    def test_range_missing_is_not_zero(self):
        for value in (None, '12', float('nan'), float('inf'), True):
            d = copy.deepcopy(self.data)
            d['sections'][1]['blocks'][0]['rows'][0]['low'] = value
            with self.subTest(value=value), self.assertRaises(ValueError): r.render(d)

    def test_invalid_range_and_denominator_rejected(self):
        d = copy.deepcopy(self.data)
        d['sections'][1]['blocks'][0]['rows'][0]['median'] = 99
        with self.assertRaises(ValueError): r.render(d)
        d = copy.deepcopy(self.data)
        d['sections'][1]['blocks'][0]['rows'][0]['n'] = 0
        with self.assertRaises(ValueError): r.render(d)

    def test_unknown_source_and_bad_row_rejected(self):
        d = copy.deepcopy(self.data)
        del d['sections'][1]['blocks'][0]['source']
        with self.assertRaises(ValueError): r.render(d)
        d = copy.deepcopy(self.data)
        d['sections'][1]['blocks'][1]['rows'][0].pop()
        with self.assertRaises(ValueError): r.render(d)


    def test_illustration_embeds_local_raster(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'scene.png').write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl6VAAAAABJRU5ErkJggg=='))
            b = {'type':'illustration','path':'scene.png','alt':'场景示意','caption':'不能证明真实产品效果','source':'AI示意','label':'示意图'}
            self.data['sections'][0]['blocks'].append(b)
            out = r.render(self.data, root)
            self.assertIn('src="data:image/png;base64,', out)
            self.assertIn('alt="场景示意"', out)
            self.assertIn('不能证明真实产品效果', out)
            del b['alt']
            with self.assertRaises(ValueError): r.render(self.data, root)

    def test_illustration_unsafe_missing_paths_and_svg_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'unsafe.svg').write_text('<svg onload="alert(1)"></svg>')
            for path in ('../outside.png', '/tmp/absolute.png', 'missing.png', 'unsafe.svg'):
                b = {'type':'illustration','path':path,'alt':'场景','caption':'示意','source':'作者','label':'示意图'}
                with self.subTest(path=path), self.assertRaises(ValueError): r.block(b, asset_root=root)

    def test_compact_comparison_keeps_mobile_matrix(self):
        table = self.data['sections'][1]['blocks'][1]
        table['mobile_layout'] = 'compact'
        out = r.render(self.data)
        self.assertIn('<table class="compact-comparison"><thead>', out)
        self.assertIn('table.compact-comparison{display:table;', out)
        self.assertIn('.compact-comparison tr{display:table-row;', out)
        self.assertIn('.compact-comparison tbody th:before{display:none}', out)
        table['columns'].append('fourth')
        with self.assertRaises(ValueError): r.render(self.data)

    def test_duplicate_ids_rejected(self):
        self.data['sections'][1]['id'] = self.data['sections'][0]['id']
        with self.assertRaises(ValueError): r.render(self.data)

if __name__ == '__main__': unittest.main()
