"""Step 2d: Extract sub-page tokens from React fiber/state."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp_utils import CDPClient

AGENTS_TOKEN = 'XdMvwRjw1iKlzukZzJAc6lJtnif'
AGENTS_URL = f'https://tauacgr5lqv.feishu.cn/wiki/{AGENTS_TOKEN}'
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'extracted', 'agents')
os.makedirs(OUT_DIR, exist_ok=True)

client = CDPClient()
print('Navigating...')
client.navigate(AGENTS_URL, wait=10)

# Approach 1: Try multiple API endpoints via in-page fetch with awaitPromise
api_paths = [
    '/space/api/wiki/v2/tree/get_node/',
    '/api/wiki/v2/tree/get_node/',
    '/wiki/api/v2/tree/get_node/',
]

for path in api_paths:
    js = f"""
    (async function() {{
        try {{
            var resp = await fetch('{path}', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{wiki_token: '{AGENTS_TOKEN}'}})
            }});
            var text = await resp.text();
            return JSON.stringify({{status: resp.status, text: text.substring(0, 300)}});
        }} catch(e) {{
            return JSON.stringify({{error: e.message}});
        }}
    })()
    """
    result = client.evaluate(js, timeout=15, await_promise=True)
    print(f'\n{path}: {result[:300] if result else "None"}')

# Approach 2: Search for wiki tokens in all script/JSON content on the page
print('\n--- Searching for tokens in page DOM ---')
search_js = """
(function() {
    var html = document.documentElement.innerHTML;
    var pattern = /[A-Z][a-zA-Z0-9]{19,30}/g;
    var matches = html.match(pattern) || [];
    var unique = [...new Set(matches)].slice(0, 50);
    return JSON.stringify(unique);
})()
"""
tokens = client.evaluate(search_js, timeout=10)
print(f'Potential tokens: {tokens[:500] if tokens else "None"}')

# Approach 3: Extract from the sidebar list items
print('\n--- Extracting sidebar list items ---')
sidebar_js = """
(function() {
    var results = [];
    // Find all text elements in the sidebar page-list region
    var container = document.querySelector('[class*="page-list"]') ||
                    document.querySelector('[class*="sidebar"]') ||
                    document.querySelector('[class*="tree"]') ||
                    document.querySelector('[class*="catalog"]');

    if (container) {
        results.push({type: 'container', class: container.className});
    }

    // Try to find list items that look like sub-pages
    var items = document.querySelectorAll('[class*="item"], [class*="node"], [class*="row"]');
    var relatedItems = [];
    items.forEach(function(el) {
        var text = el.textContent.trim();
        // Filter for items that look like the agent sub-pages
        if (text.includes('从零基础到精通') || text.includes('教程') || text.includes('指南') ||
            text.includes('对比') || text.includes('Claude code') || text.includes('Vibe Coding')) {
            relatedItems.push({
                text: text.substring(0, 80),
                className: el.className,
                onclick: el.onclick ? 'has onclick' : 'no onclick',
                childCount: el.children.length
            });
        }
    });
    results.push({type: 'items', items: relatedItems});
    return JSON.stringify(results);
})()
"""
sidebar = client.evaluate(sidebar_js, timeout=10)
print(sidebar[:2000] if sidebar else "None")

# Approach 4: Try to get children with the API using a different body format
print('\n--- Trying alternative API formats ---')
alt_js = """
(async function() {
    var results = [];
    var token = '""" + AGENTS_TOKEN + """';

    // Try different body formats
    var formats = [
        {wiki_token: token},
        {token: token},
        {node_token: token},
        {parent_token: token},
    ];

    for (var f of formats) {
        try {
            var resp = await fetch('/space/api/wiki/v2/tree/get_node/', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(f)
            });
            var text = await resp.text();
            results.push({body: JSON.stringify(f), status: resp.status, preview: text.substring(0, 200)});
        } catch(e) {
            results.push({body: JSON.stringify(f), error: e.message});
        }
    }
    return JSON.stringify(results);
})()
"""
alt_result = client.evaluate(alt_js, timeout=20, await_promise=True)
print(alt_result[:2000] if alt_result else "None")

client.close()
