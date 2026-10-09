"""Render a .bpmn file to PNG + SVG with bpmn-js in headless Chromium; report import warnings."""
import sys, json, pathlib
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).parent
VIEWER = (HERE / 'node_modules/bpmn-js/dist/bpmn-viewer.production.min.js').read_text()
CSS = ''.join((HERE / 'node_modules/bpmn-js/dist/assets' / f).read_text()
              for f in ['diagram-js.css', 'bpmn-js.css', 'bpmn-font/css/bpmn.css'])


def render(bpmn_path, png_path, svg_path, scale=1.6):
    xml = pathlib.Path(bpmn_path).read_text()
    html = f"""<html><head><style>{CSS} html,body{{margin:0;background:#fff}} #c{{width:100%;height:100%}}</style></head>
    <body><div id="c"></div><script>{VIEWER}</script></body></html>"""
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': 1600, 'height': 1000}, device_scale_factor=scale)
        pg.set_content(html)
        res = pg.evaluate("""async (xml) => {
            const v = new BpmnJS({container: '#c'});
            const r = await v.importXML(xml);
            const {svg} = await v.saveSVG();
            const box = v.get('canvas').viewbox().inner;
            return {warnings: r.warnings.map(w => w.message), svg, box};
        }""", xml)
        svg = res['svg']
        pathlib.Path(svg_path).write_text(svg)
        box = res['box']
        w, h = int(box['width'] + 60), int(box['height'] + 60)
        pg2 = b.new_page(viewport={'width': w, 'height': h}, device_scale_factor=scale)
        pg2.set_content(f'<html><body style="margin:0;background:#fff">{svg}</body></html>')
        pg2.screenshot(path=png_path, full_page=True)
        b.close()
    return res['warnings'], (w, h)


if __name__ == '__main__':
    warns, size = render(*sys.argv[1:4])
    print('size', size, 'warnings', len(warns))
    for w in warns:
        print(' -', w)
