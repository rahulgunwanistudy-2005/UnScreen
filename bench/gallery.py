"""Capture local gallery pages; the reader image is explicitly a historical golden replay."""
import json
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'gallery'
parser = argparse.ArgumentParser()
parser.add_argument('--browser', help='optional installed Chromium executable')
parser.add_argument('--document', type=Path, help='optional historical golden document; default uses the genuine recording')
parser.add_argument('--base', default='http://localhost:4173')
args = parser.parse_args()
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, executable_path=args.browser)
    page = browser.new_page(viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce', color_scheme='light')
    for slug, url in [('home', '/'), ('benchmark', '/benchmark'), ('help', '/help'), ('privacy', '/privacy')]:
        page.goto(args.base + url)
        page.wait_for_load_state('networkidle')
        page.screenshot(path=str(OUT / f'{slug}-local.png'), full_page=True)
    if args.document:
        page.goto(args.base + '/fixture/reader')
        page.wait_for_load_state('networkidle')
        page.wait_for_function('window.__ready === true')
        document = json.loads(args.document.read_text())
        page.evaluate('(doc) => window.__snapshot(doc)', document)
        page.get_by_role('table').wait_for()
        page.screenshot(path=str(OUT / 'reader-golden-local.png'), full_page=True)
    else:
        page.goto(args.base + '/app')
        page.wait_for_load_state('networkidle')
        page.get_by_role('button', name='Watch a recorded session').click()
        page.locator('main table caption').wait_for()
        page.screenshot(path=str(OUT / 'reader-recording-local.png'), full_page=True)
    page.goto('about:blank')
    page.set_viewport_size({'width': 1400, 'height': 850})
    page.set_content('<html><body style="margin:0">' + (OUT / 'architecture.svg').read_text() + '</body></html>')
    page.screenshot(path=str(OUT / 'architecture.png'), full_page=True)
    browser.close()
print('Saved local gallery images with explicit recorded-reader provenance. No paid model calls made.')
