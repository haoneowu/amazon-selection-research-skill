#!/usr/bin/env python3
"""Render an editorially structured report to a standalone, offline HTML file."""
import argparse
import base64
import html
import json
import math
import re
from pathlib import Path
from urllib.parse import urlsplit


def text(value, name='text', limit=1000):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f'{name}: expected nonempty text, maximum {limit} characters')
    return html.escape(value, quote=True)


def link(value):
    if isinstance(value, str):
        return text(value)
    if not isinstance(value, dict):
        raise ValueError('cell/link must be text or {text, url}')
    label = text(value.get('text'), 'link.text')
    url = value.get('url')
    if not isinstance(url, str) or any(ord(c) < 33 for c in url):
        raise ValueError('link.url: invalid URL')
    parsed = urlsplit(url)
    if parsed.scheme not in ('http', 'https') or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError('link.url: only absolute http(s) URLs without credentials allowed')
    return f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">{label} ↗</a>'


def items(value, name, minimum=1, maximum=20):
    if not isinstance(value, list) or not minimum <= len(value) <= maximum:
        raise ValueError(f'{name}: expected {minimum}–{maximum} items')
    return value


def bullets(values, name='points'):
    return '<ul>' + ''.join('<li>' + text(v, name, 160) + '</li>' for v in items(values, name, 1, 4)) + '</ul>'


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('range value must be a finite number; missing is not zero')
    return value


def fmt(value):
    return f'{value:,.2f}'.rstrip('0').rstrip('.') if isinstance(value, float) else f'{value:,}'


def block(b, depth=0, asset_root=None):
    if not isinstance(b, dict) or depth > 2:
        raise ValueError('invalid block or excessively nested details')
    kind = b.get('type')
    title = '<h3>' + text(b['title'], 'block.title', 80) + '</h3>' if 'title' in b else ''
    body = ''
    if kind == 'illustration':
        alt = text(b.get('alt'), 'illustration.alt', 180)
        caption = text(b.get('caption'), 'illustration.caption', 240)
        source = link(b.get('source'))
        label = text(b.get('label'), 'illustration.label', 40)
        raw_path = b.get('path')
        if asset_root is None or not isinstance(raw_path, str) or not raw_path:
            raise ValueError('illustration requires an input directory and a relative path')
        root = Path(asset_root).resolve()
        path = Path(raw_path)
        if path.is_absolute():
            raise ValueError('illustration.path must be relative to the input JSON directory')
        path = (root / path).resolve()
        try:
            path.relative_to(root)
        except ValueError:
            raise ValueError('illustration.path must not escape the input JSON directory')
        if not path.is_file():
            raise ValueError(f'illustration file is missing: {raw_path}')
        if path.stat().st_size > 4 * 1024 * 1024:
            raise ValueError('illustration must be no larger than 4 MiB')
        raw = path.read_bytes()
        if path.suffix.lower() == '.png' and raw.startswith(b'\x89PNG\r\n\x1a\n'):
            mime = 'image/png'
        elif path.suffix.lower() in ('.jpg', '.jpeg') and raw.startswith(b'\xff\xd8\xff'):
            mime = 'image/jpeg'
        else:
            raise ValueError('illustration must be a PNG or JPEG file; SVG and other types are not accepted')
        encoded = base64.b64encode(raw).decode('ascii')
        body = '<figure class="illustration"><img src="data:' + mime + ';base64,' + encoded + '" alt="' + alt + '"><figcaption><strong>' + label + '</strong> · ' + caption + '<span class="source">' + source + '</span></figcaption></figure>'
    elif kind == 'cards':
        body = '<div class="cards">'
        for c in items(b.get('items'), 'cards', 1, 4):
            body += '<article class="candidate"><h4>' + text(c.get('title'), 'card.title', 60) + '</h4><p class="verdict">' + text(c.get('verdict'), 'card.verdict', 100) + '</p>' + bullets(c.get('points')) + '</article>'
        body += '</div>'
    elif kind == 'comparison':
        columns = items(b.get('columns'), 'columns', 2, 6)
        headers = [text(v, 'column', 60) for v in columns]
        layout = b.get('mobile_layout', 'cards')
        if layout not in ('cards', 'compact') or (layout == 'compact' and len(columns) != 3):
            raise ValueError('comparison.mobile_layout compact requires exactly 3 columns')
        table_class = ' class="compact-comparison"' if layout == 'compact' else ''
        body = '<table' + table_class + '><thead><tr>' + ''.join('<th scope="col">' + v + '</th>' for v in headers) + '</tr></thead><tbody>'
        for row in items(b.get('rows'), 'rows', 1, 24):
            if not isinstance(row, list) or len(row) != len(headers):
                raise ValueError('comparison row width must match columns')
            body += '<tr>'
            for i, cell in enumerate(row):
                tag = 'th' if i == 0 else 'td'
                scope = ' scope="row"' if i == 0 else ''
                body += f'<{tag}{scope} data-label="{headers[i]}">' + link(cell) + f'</{tag}>'
            body += '</tr>'
        body += '</tbody></table>'
        body += '<p class="source">' + link(b.get('source')) + '</p>'
    elif kind == 'ranges':
        unit = text(b.get('unit'), 'range.unit', 40)
        source = link(b.get('source'))
        rows = items(b.get('rows'), 'ranges', 1, 12)
        for row in rows:
            lo, mid, hi = [number(row.get(k)) for k in ('low', 'median', 'high')]
            if not lo <= mid <= hi:
                raise ValueError('range requires low ≤ median ≤ high')
            if not isinstance(row.get('n'), int) or isinstance(row['n'], bool) or row['n'] < 1:
                raise ValueError('range.n must be a positive sample count')
        lo_axis = min(0, min(r['low'] for r in rows))
        hi_axis = max(r['high'] for r in rows)
        span = hi_axis - lo_axis or 1
        body = '<p class="legend">区间：最低—最高；圆点：中位数。单位：' + unit + '。各行使用相同刻度。</p><div class="ranges">'
        for row in rows:
            left, mid, right = [(row[k] - lo_axis) / span * 100 for k in ('low','median','high')]
            body += '<div class="range-row"><div class="range-heading"><b>' + text(row.get('label'), 'range.label', 60) + '</b><span>n = ' + str(row['n']) + '</span></div>'
            body += f'<div class="track" aria-hidden="true"><i style="left:{left:.5f}%;width:{right-left:.5f}%"></i><b style="left:{mid:.5f}%"></b></div>'
            body += '<p class="range-values">区间 ' + fmt(row['low']) + '–' + fmt(row['high']) + ' ' + unit + ' <strong>中位 ' + fmt(row['median']) + ' ' + unit + '</strong></p></div>'
        body += '<div class="axis" aria-hidden="true"><span>' + fmt(lo_axis) + '</span><span>' + fmt(hi_axis) + ' ' + unit + '</span></div></div><p class="source">' + source + '</p>'
    elif kind == 'issues':
        for item in items(b.get('items'), 'issues', 1, 8):
            body += '<article class="issue"><h4>' + text(item.get('problem'), 'problem', 80) + '</h4><dl><dt>证据</dt><dd>' + text(item.get('evidence'), 'evidence', 250) + '</dd><dt>产品行动</dt><dd>' + text(item.get('action'), 'action', 200) + '</dd></dl></article>'
        body += '<p class="source">' + link(b.get('source')) + '</p>'
    elif kind == 'steps':
        body = '<ol class="steps">'
        for item in items(b.get('items'), 'steps', 1, 6):
            body += '<li><h4>' + text(item.get('title'), 'step.title', 80) + '</h4><p>' + text(item.get('action'), 'step.action', 200) + '</p></li>'
        body += '</ol>'
    elif kind == 'details':
        summary = text(b.get('title'), 'details.title', 100)
        inner = ''.join(block(v, depth + 1, asset_root) for v in items(b.get('blocks'), 'details.blocks', 1, 6))
        return '<details><summary>' + summary + '</summary><div class="details-body">' + inner + '</div></details>'
    elif kind == 'notes':
        if depth == 0:
            raise ValueError('notes belong in collapsed details; use key_points for visible conclusions')
        body = '<ul class="notes">' + ''.join('<li>' + link(v) + '</li>' for v in items(b.get('items'), 'notes', 1, 20)) + '</ul>'
    else:
        raise ValueError(f'unsupported block type: {kind!r}; long paragraph arrays are not a report layout')
    if 'note' in b:
        body += '<p class="caveat">' + text(b['note'], 'note', 240) + '</p>'
    return '<div class="block">' + title + body + '</div>'


CSS = '''
:root{--bg:#f3f7fc;--ink:#192437;--muted:#53647a;--blue:#2466d8;--pale:#e9f1ff;--line:#d6e3f5;--nav-height:70px}*{box-sizing:border-box}html{scroll-padding-top:calc(var(--nav-height) + 20px)}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.75 -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;overflow-wrap:anywhere}main{max-width:960px;padding:0 32px 48px;margin:auto}header{text-align:center;padding:60px 0 30px}h1{font-size:40px;line-height:1.35;letter-spacing:-1px;margin:16px auto;max-width:800px}h2{font-size:27px;line-height:1.45;margin:8px 0}h3{font-size:19px;line-height:1.5;margin:0 0 14px}h4{font-size:16px;line-height:1.5;margin:0 0 8px}p{margin:8px 0}a{color:#174caa;text-underline-offset:3px}a:focus-visible,summary:focus-visible{outline:3px solid #2466d8;outline-offset:4px}.eyebrow,.chapter{color:var(--blue);font-weight:700;font-size:12px;letter-spacing:1px}.subtitle,.meta,.source,.legend{color:var(--muted)}header>.subtitle{max-width:680px;margin:0 auto;font-size:17px}.meta{font-size:12px;margin-top:18px}.nav{position:sticky;top:0;z-index:10;display:flex;flex-wrap:wrap;gap:4px;justify-content:center;background:rgba(243,247,252,.98);padding:10px 0;border-bottom:1px solid var(--line)}.nav a{font-size:13px;padding:8px 10px;text-decoration:none;border-radius:8px;min-height:40px;display:flex;align-items:center}.nav a:hover,.nav a[aria-current]{background:var(--pale)}section{padding-top:32px;margin-top:24px;border-top:1px solid var(--line);scroll-margin-top:0}.key-points{padding:16px 20px 16px 36px;border-left:3px solid var(--blue);background:var(--pale);margin:20px 0}.block{padding:24px;background:#fff;border:1px solid var(--line);border-radius:18px;margin:18px 0}.cards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}.candidate{min-width:0;padding:18px;background:#f6f9fd;border-radius:12px}.verdict{color:#174caa;font-weight:650}.candidate ul{padding-left:19px;font-size:14px}li{margin:6px 0}table{width:100%;border-collapse:collapse;table-layout:fixed;font-size:13px;text-align:left}th,td{padding:12px 10px;border-bottom:1px solid var(--line);vertical-align:top}thead{background:#edf3fb}tbody tr:nth-child(even){background:#f6f9fd}.source,.legend,.range-values,.caveat{font-size:13px}.source{margin-top:16px}.caveat{padding:12px 16px;border-left:3px solid #bc872c;background:#fff7e9}.range-row{padding:14px 0;border-bottom:1px solid var(--line)}.range-heading,.axis{display:flex;justify-content:space-between;gap:16px}.range-heading span{font-size:12px;color:var(--muted)}.track{position:relative;height:24px;margin:10px 8px;background:linear-gradient(to right,#e6edf7,#e6edf7) center/100% 1px no-repeat}.track i{position:absolute;top:10px;height:5px;background:#a9c9f7;border-radius:5px}.track b{position:absolute;top:6px;width:13px;height:13px;border:2px solid white;border-radius:50%;background:var(--blue);transform:translateX(-50%);box-shadow:0 0 0 1px var(--blue)}.range-values{display:flex;justify-content:space-between;flex-wrap:wrap;gap:4px 16px}.range-values strong{color:#174caa}.axis{font-size:12px;color:var(--muted);margin:10px 8px}.issue{border-bottom:1px solid var(--line);padding:16px 0}.issue:first-of-type{padding-top:0}.issue:last-of-type{border-bottom:0}dl{display:grid;grid-template-columns:68px minmax(0,1fr);gap:8px 16px;margin:12px 0}dt{font-size:13px;color:var(--blue);font-weight:650}dd{margin:0;font-size:14px}.steps{padding-left:24px}.steps li{padding-left:8px;margin:0 0 20px}.steps li::marker{color:var(--blue);font-weight:700}.steps p{font-size:14px}details{border-top:1px solid var(--line);margin:16px 0}summary{cursor:pointer;padding:18px 8px;min-height:52px;font-weight:650;color:#174caa}.details-body{padding:0 8px 12px}.details-body .block{padding:18px;margin:6px 0;border-radius:12px}.notes{font-size:13px;padding-left:18px}.illustration{margin:0}.illustration img{display:block;width:100%;height:auto;border-radius:12px}.illustration figcaption{font-size:13px;color:var(--muted);margin-top:12px}.illustration figcaption .source{display:block;margin-top:5px}.footer{color:var(--muted);font-size:12px;margin-top:32px}.skip{position:absolute;left:16px;top:-100px;background:#fff;padding:10px;z-index:20}.skip:focus{top:8px}@media(max-width:640px){main{padding:0 16px 36px}header{padding-top:36px}h1{font-size:29px}h2{font-size:23px}h3{font-size:18px}header>.subtitle{font-size:15px}.block{padding:18px 14px}.cards{grid-template-columns:1fr;gap:12px}.candidate{padding:16px}.nav{gap:2px}.nav a{font-size:12px;padding:8px;flex:1 1 28%;justify-content:center;text-align:center}.key-points{padding-right:14px}table,tbody,tr,td,tbody th{display:block;width:100%}thead{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)}tbody tr{padding:10px 0;border-bottom:1px solid var(--line)}tbody th,td{border:0;padding:7px 8px}td:before,tbody th:before{content:attr(data-label);display:block;font-size:11px;color:var(--muted);font-weight:400;margin-bottom:2px}dl{grid-template-columns:1fr;gap:3px}dd{margin-bottom:10px}.details-body{padding-left:0;padding-right:0}}@media(max-width:640px){table.compact-comparison{display:table;table-layout:fixed;font-size:12px;line-height:1.6}.compact-comparison thead{position:static;display:table-header-group;width:auto;height:auto;overflow:visible;clip-path:none}.compact-comparison tbody{display:table-row-group;width:auto}.compact-comparison tr{display:table-row;width:auto;padding:0}.compact-comparison th,.compact-comparison td,.compact-comparison tbody th{display:table-cell;width:auto;padding:9px 6px;border-bottom:1px solid var(--line)}.compact-comparison th:first-child,.compact-comparison td:first-child{width:25%}.compact-comparison td:before,.compact-comparison tbody th:before{display:none}.compact-comparison tbody th{font-size:11px;color:var(--muted)}}@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
'''
JS = '''
const nav=document.querySelector('.nav');
const sections=[...document.querySelectorAll('main>section')];
const links=[...nav.querySelectorAll('a')];
function sizing(){document.documentElement.style.setProperty('--nav-height',nav.getBoundingClientRect().height+'px');}
function highlight(){let current=sections[0];for(const s of sections){if(s.getBoundingClientRect().top<=nav.getBoundingClientRect().bottom+30)current=s;}if(innerHeight+scrollY>=document.documentElement.scrollHeight-3)current=sections[sections.length-1];links.forEach(a=>{if(a.hash==='#'+current.id)a.setAttribute('aria-current','location');else a.removeAttribute('aria-current');});}
function align(){requestAnimationFrame(()=>requestAnimationFrame(()=>{sizing();const s=sections.find(s=>'#'+s.id===location.hash);if(s){s.scrollIntoView({block:'start',behavior:'instant'});s.querySelector('h2').focus({preventScroll:true});}highlight();}));}
new ResizeObserver(()=>{sizing();highlight();}).observe(nav);
addEventListener('hashchange',align);addEventListener('popstate',align);addEventListener('scroll',highlight,{passive:true});addEventListener('resize',()=>{sizing();highlight();});addEventListener('pageshow',()=>{sizing();highlight();});sizing();if(location.hash)align();else highlight();
'''


def render(data, asset_root=None):
    title = text(data.get('title'), 'title', 90)
    subtitle = text(data.get('subtitle'), 'subtitle', 160)
    metadata = data.get('metadata', {})
    meta = ' · '.join(text(metadata.get(k), f'metadata.{k}', 80) for k in ('owner', 'status', 'updated', 'version'))
    sections = items(data.get('sections'), 'sections', 2, 9)
    nav, contents, seen = [], [], set()
    for i, sec in enumerate(sections, 1):
        sid = sec.get('id')
        if not isinstance(sid, str) or not re.fullmatch('[a-z][a-z0-9-]{0,40}', sid) or sid in seen:
            raise ValueError('section.id must be unique lowercase ASCII slug')
        seen.add(sid)
        headline = text(sec.get('headline'), 'headline', 70)
        nav_label = text(sec.get('nav_label', sec.get('headline')), 'nav_label', 24)
        deck = text(sec.get('subtitle'), 'section.subtitle', 160)
        points = bullets(sec.get('key_points'), 'key_points')
        bs = items(sec.get('blocks'), 'blocks', 1, 8)
        if not any(v.get('type') not in ('details', 'notes', 'illustration') for v in bs):
            raise ValueError('each section needs a default-visible analytical block')
        inner = ''.join(block(v, asset_root=asset_root) for v in bs)
        nav.append(f'<a href="#{sid}">{nav_label}</a>')
        contents.append(f'<section id="{sid}"><span class="chapter">{i:02d}</span><h2 tabindex="-1">{headline}</h2><p class="subtitle">{deck}</p><div class="key-points">{points}</div>{inner}</section>')
    appendix = ''.join(block(b, asset_root=asset_root) for b in data.get('appendix', []))
    for b in data.get('appendix', []):
        if b.get('type') != 'details':
            raise ValueError('appendix must consist of collapsed details blocks')
    footer_links = ' · '.join(link(v) for v in data.get('links', []))
    demo = '<p class="caveat">虚构示例，仅演示版式；所有数字均非真实市场研究。</p>' if data.get('fictional_example') else ''
    return '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+title+'</title><style>'+CSS+'</style></head><body><a class="skip" href="#'+sections[0]['id']+'">跳到结论</a><main><header><span class="eyebrow">选品研究</span><h1>'+title+'</h1><p class="subtitle">'+subtitle+'</p><p class="meta">'+meta+'</p>'+demo+'</header><nav class="nav" aria-label="报告章节">'+''.join(nav)+'</nav>'+''.join(contents)+'<aside aria-label="来源与附录">'+appendix+'</aside><footer class="footer">'+footer_links+'<p>'+meta+'</p><a href="#">回到顶部 ↑</a></footer></main><script>'+JS+'</script></body></html>'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path, nargs='?')
    parser.add_argument('--output', dest='output_option', type=Path)
    args = parser.parse_args()
    if bool(args.output) == bool(args.output_option):
        parser.error('provide one output path, positional or --output')
    args.output = args.output or args.output_option
    result = render(json.loads(args.input.read_text(encoding='utf-8')), args.input.parent)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(result, encoding='utf-8')
    print(f'Wrote {args.output} ({len(result.encode())} bytes)')


if __name__ == '__main__':
    main()
