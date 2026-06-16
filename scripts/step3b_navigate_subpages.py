"""Step 3b: Navigate to sub-pages by finding links in main content area, then extract."""
import sys, os, json, time, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp_utils import CDPClient

AGENTS_URL = 'https://tauacgr5lqv.feishu.cn/wiki/XdMvwRjw1iKlzukZzJAc6lJtnif'
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'extracted', 'agents')
os.makedirs(OUT_DIR, exist_ok=True)

client = CDPClient()
client.navigate(AGENTS_URL, wait=10)

# Find all clickable links in the main content area that have wiki tokens
print('--- Finding sub-page links in main content ---')
find_links_js = """
(function() {
    var results = [];
    // Look in the main content area, not sidebar
    var mainArea = document.querySelector('[class*="page-content"], [class*="doc-content"], [class*="wiki-content"], main, [class*="editor"], [class*="catalogue"]');
    if (!mainArea) mainArea = document.body;

    // Find ALL elements that might be links in the grid/list view
    var items = mainArea.querySelectorAll('[class*="card"], [class*="grid"], [class*="list-item"], [class*="row"], a');

    var seen = new Set();
    items.forEach(function(el) {
        var text = el.textContent.trim().substring(0, 100);
        // Look for wiki tokens anywhere in the element
        var html = el.outerHTML || '';
        var tokens = html.match(/[A-Z][a-zA-Z0-9]{19,25}/g) || [];
        var hrefTokens = html.match(/\\/wiki\\/([A-Za-z0-9]{15,30})/g) || [];

        if ((tokens.length > 0 || hrefTokens.length > 0) && text.length > 3 && !seen.has(text)) {
            seen.add(text);
            results.push({
                text: text,
                tokens: [...new Set(tokens)].slice(0, 5),
                hrefTokens: [...new Set(hrefTokens)].slice(0, 5),
                tag: el.tagName,
                className: el.className?.substring?.(0, 80) || ''
            });
        }
    });

    // Also get ALL wiki URLs from entire page HTML
    var fullHtml = document.body.innerHTML;
    var allWikiUrls = fullHtml.match(/\\/wiki\\/[A-Za-z0-9]{15,30}/g) || [];

    return JSON.stringify({
        items: results.slice(0, 40),
        allWikiUrls: [...new Set(allWikiUrls)].slice(0, 30)
    });
})()
"""
links_data = client.evaluate(find_links_js, timeout=15)
if links_data:
    data = json.loads(links_data)
    print(f"Items found: {len(data.get('items', []))}")
    for item in data.get('items', [])[:25]:
        print(f"  [{item['tag']}] {item['text'][:80]}")
        if item['hrefTokens']:
            print(f"    hrefTokens: {item['hrefTokens']}")
    print(f"\nAll wiki URLs in page: {data.get('allWikiUrls', [])}")

# Now try to get the grid items from the catalogue view
print('\n--- Catalogue grid items ---')
grid_js = """
(function() {
    var results = [];
    // The main content shows a grid of sub-documents
    var cells = document.querySelectorAll('[class*="grid"] [class*="cell"], [class*="card"], [class*="item"]');
    cells.forEach(function(cell) {
        var text = cell.textContent.trim().substring(0, 120);
        if (text.length > 5) {
            // Get all attributes
            var attrs = [];
            for (var i = 0; i < cell.attributes.length; i++) {
                attrs.push(cell.attributes[i].name + '=' + cell.attributes[i].value.substring(0, 80));
            }
            results.push({text: text, attrs: attrs.join('|')});
        }
    });
    return JSON.stringify(results.slice(0, 30));
})()
"""
grid_data = client.evaluate(grid_js, timeout=10)
if grid_data:
    items = json.loads(grid_data)
    print(f'Grid items: {len(items)}')
    for item in items:
        print(f"  {item['text'][:100]}")
        if 'wiki' in item.get('attrs', ''):
            print(f"    ATTRS: {item['attrs'][:300]}")

client.close()
