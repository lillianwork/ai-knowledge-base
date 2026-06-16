"""Step 2b: Extract AI智能体 sub-page tokens via in-page API calls."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp_utils import CDPClient

AGENTS_TOKEN = 'XdMvwRjw1iKlzukZzJAc6lJtnif'
AGENTS_URL = f'https://tauacgr5lqv.feishu.cn/wiki/{AGENTS_TOKEN}'
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'extracted', 'agents')
os.makedirs(OUT_DIR, exist_ok=True)

client = CDPClient()
print(f'Navigating to AI智能体 page...')
client.navigate(AGENTS_URL, wait=8)
print(f'Title: {client.evaluate("document.title")}')

# Use in-page fetch to call Feishu wiki API
# This uses the browser's authenticated session automatically
fetch_js = """
(async function() {
    try {
        var resp = await fetch('/space/api/wiki/v2/tree/get_node/', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({wiki_token: '""" + AGENTS_TOKEN + """'})
        });
        var data = await resp.json();
        return JSON.stringify(data);
    } catch(e) {
        return JSON.stringify({error: e.message});
    }
})()
"""
print('\nFetching child nodes via in-page API...')
result = client.evaluate(fetch_js, timeout=20, await_promise=True)
print(f'API Response: {result[:2000] if result else "None"}')

if result:
    try:
        data = json.loads(result)
        if data.get('code') == 0 and 'data' in data:
            nodes = data['data'].get('nodes', {})
            child_map = data['data'].get('child_map', {})
            children = child_map.get(AGENTS_TOKEN, [])

            print(f'\nChildren count: {len(children)}')
            sub_pages = []
            for token in children:
                node = nodes.get(token, {})
                title = node.get('title', '')
                url = node.get('url', '')
                has_child = node.get('has_child', False)
                sub_pages.append({
                    'token': token,
                    'title': title,
                    'url': url,
                    'has_child': has_child
                })
                print(f'  [{token}] {title} (has_child={has_child})')

            with open(os.path.join(OUT_DIR, 'agents_subpages_tree.json'), 'w', encoding='utf-8') as f:
                json.dump(sub_pages, f, ensure_ascii=False, indent=2)
            print(f'\nSaved {len(sub_pages)} sub-pages to agents_subpages_tree.json')
        else:
            print(f'API error: {data.get("msg", "unknown")}')
    except Exception as e:
        print(f'Parse error: {e}')

# Also try without /wiki/ prefix
fetch_js2 = """
(async function() {
    try {
        var resp = await fetch('/wiki/space/api/wiki/v2/tree/get_node/', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({wiki_token: '""" + AGENTS_TOKEN + """'})
        });
        var data = await resp.json();
        return JSON.stringify(data);
    } catch(e) {
        return JSON.stringify({error: e.message});
    }
})()
"""
print('\nTrying with /wiki/ prefix...')
result2 = client.evaluate(fetch_js2, timeout=20, await_promise=True)
print(f'API Response: {result2[:500] if result2 else "None"}')

client.close()
