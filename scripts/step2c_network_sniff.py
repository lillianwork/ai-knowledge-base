"""Step 2c: Sniff network requests to find API endpoints, then extract sub-page tokens."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp_utils import CDPClient

AGENTS_TOKEN = 'XdMvwRjw1iKlzukZzJAc6lJtnif'
AGENTS_URL = f'https://tauacgr5lqv.feishu.cn/wiki/{AGENTS_TOKEN}'
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'extracted', 'agents')
os.makedirs(OUT_DIR, exist_ok=True)

client = CDPClient()

# Enable Network domain
client.send('Network.enable')
client.recv_result(client._mid, 5)

# Navigate
print('Navigating to AI智能体...')
client.navigate(AGENTS_URL, wait=10)

# Check received network events
print(f'\nCaptured {len(client._events)} events')

# Extract XHR/fetch requests from events
api_calls = []
for ev in client._events:
    if 'method' in ev:
        method = ev['method']
        params = ev.get('params', {})
        if 'request' in params:
            url = params['request'].get('url', '')
            if '/api/' in url:
                api_calls.append({'method': params['request'].get('method', 'GET'), 'url': url})

print(f'\nAPI calls detected:')
for ac in api_calls:
    print(f'  {ac["method"]} {ac["url"][:120]}')

# Now try to extract all interactive elements (sidebar links)
print('\n--- Extracting links via DOM query ---')
links_js = """
(function() {
    var results = [];
    // Feishu sidebar uses a specific structure - look for all links
    var allLinks = document.querySelectorAll('a');
    allLinks.forEach(function(a) {
        var href = a.getAttribute('href') || '';
        var text = a.textContent.trim().replace(/\\s+/g, ' ');
        if (href.includes('/wiki/') && text.length > 2) {
            var token = href.split('/wiki/')[1]?.split('?')[0]?.split('#')[0] || '';
            if (token && token !== '""" + AGENTS_TOKEN + """') {
                results.push({title: text, token: token, href: href});
            }
        }
    });
    return JSON.stringify(results);
})()
"""
links_raw = client.evaluate(links_js, timeout=10, await_promise=False)
if links_raw:
    try:
        links = json.loads(links_raw)
        unique = {}
        for l in links:
            if l['token'] not in unique:
                unique[l['token']] = l
        links = list(unique.values())
        print(f'Found {len(links)} links:')
        for l in links:
            print(f'  [{l["token"]}] {l["title"]}')
        with open(os.path.join(OUT_DIR, 'agents_subpages_dom.json'), 'w', encoding='utf-8') as f:
            json.dump(links, f, ensure_ascii=False, indent=2)
    except:
        print(f'Parse error: {links_raw[:500]}')

# Also try: Feishu data attributes
print('\n--- Looking for React data ---')
react_js = """
(function() {
    var results = [];
    // Look for elements with data-view or data-id attributes that might contain wiki tokens
    document.querySelectorAll('[data-token], [data-wiki-token], [data-node-token]').forEach(function(el) {
        results.push({
            token: el.getAttribute('data-token') || el.getAttribute('data-wiki-token') || el.getAttribute('data-node-token'),
            text: el.textContent.trim().substring(0, 60)
        });
    });
    return JSON.stringify(results.slice(0, 30));
})()
"""
react_data = client.evaluate(react_js, timeout=10)
print(f'React data tokens: {react_data}')

client.close()
