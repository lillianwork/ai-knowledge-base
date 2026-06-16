"""Step 2: Extract AI智能体 sub-page tree via CDP."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp_utils import CDPClient

AGENTS_URL = 'https://tauacgr5lqv.feishu.cn/wiki/XdMvwRjw1iKlzukZzJAc6lJtnif'
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'extracted', 'agents')
os.makedirs(OUT_DIR, exist_ok=True)

client = CDPClient()
print(f'Starting tab: {client.tab["title"][:80]}')

# Navigate to AI智能体 page
print(f'\nNavigating to AI智能体 page...')
client.navigate(AGENTS_URL, wait=8)

title = client.evaluate('document.title')
print(f'PAGE TITLE: {title}')

# Extract all sub-page links from the page
print('\n--- Extracting sub-page links from DOM ---')
links_js = """
(function() {
    var results = [];
    // Look for links in the page list/grid area
    var links = document.querySelectorAll('a[href*="/wiki/"]');
    var seen = new Set();
    links.forEach(function(a) {
        var href = a.href;
        var text = a.textContent.trim();
        // Filter out nav/sidebar links
        if (text && text.length > 2 && text.length < 100 && !seen.has(href)) {
            seen.add(href);
            var token = href.split('/wiki/')[1]?.split('?')[0] || '';
            results.push({title: text, url: href, token: token});
        }
    });
    return JSON.stringify(results);
})()
"""
links_raw = client.evaluate(links_js)
if links_raw:
    links = json.loads(links_raw)
    # Filter to unique by token
    seen_tokens = set()
    unique_links = []
    for l in links:
        if l['token'] and l['token'] not in seen_tokens:
            seen_tokens.add(l['token'])
            unique_links.append(l)

    print(f'Found {len(unique_links)} unique sub-page links:')
    for i, l in enumerate(unique_links):
        print(f'  {i+1}. [{l["token"]}] {l["title"]}')

    with open(os.path.join(OUT_DIR, 'agents_subpages.json'), 'w', encoding='utf-8') as f:
        json.dump(unique_links, f, ensure_ascii=False, indent=2)
    print(f'\nSaved to extracted/agents/agents_subpages.json')
else:
    print('No links found!')

# Also get the page's innerText to understand structure
print('\n--- Page body (first 2000 chars) ---')
body = client.get_page_text(2000)
print(body)

# Try to extract wiki token list from page state
print('\n--- Page JS state ---')
state = client.evaluate("""
(function() {
    var data = {};
    try {
        // Feishu stores page data in various places
        if (window.__INITIAL_STATE__) data.initState = Object.keys(window.__INITIAL_STATE__);
    } catch(e) {}
    return JSON.stringify(data);
})()
""")
print(f'State keys: {state}')

client.close()
