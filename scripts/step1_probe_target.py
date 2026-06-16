"""Step 1: Probe target wiki page and extract auth info."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp_utils import CDPClient

TARGET_URL = 'https://tauacgr5lqv.feishu.cn/wiki/DFs5wdk1YiHfNNkACcecO5DAn4c'

client = CDPClient()
print(f'Using tab: {client.tab["title"][:60]}')

# Navigate to target page
print(f'\nNavigating to target page...')
client.navigate(TARGET_URL, wait=8)

# Get page info
title = client.evaluate('document.title')
url = client.get_current_url()
text = client.get_page_text(3000)

print(f'TITLE: {title}')
print(f'URL: {url}')
print(f'\n--- Page content (first 3000 chars) ---')
print(text)
print('--- END ---')

# Extract wiki token from URL
if '/wiki/' in url:
    wiki_token = url.split('/wiki/')[1].split('?')[0]
    print(f'\nWiki Token: {wiki_token}')

# Try to get space_id and wiki_token from page JS context
space_id = client.evaluate("""
(function() {
    try {
        var state = window.__INITIAL_STATE__ || window.__SSR_DATA__ || {};
        return JSON.stringify({
            spaceId: state.space?.id || state.spaceId || '',
            wikiToken: state.wikiToken || '',
            objToken: state.objToken || ''
        });
    } catch(e) {
        return '{}';
    }
})()
""")
print(f'Page state: {space_id}')

# Extract cookies
cookies = client.get_cookies('feishu.cn')
print(f'\n--- Cookies ({len(cookies)} total) ---')
cookie_str = '; '.join(f"{c['name']}={c['value']}" for c in cookies)
for c in cookies:
    print(f"  {c['name']}: {c['value'][:30]}... (domain={c.get('domain','')})")

# Save cookies
out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'extracted', 'agents')
os.makedirs(out_dir, exist_ok=True)
with open(os.path.join(out_dir, 'auth_cookies.json'), 'w') as f:
    json.dump({'cookies': cookies, 'cookie_str': cookie_str}, f, ensure_ascii=False, indent=2)
print(f'\nCookies saved to extracted/agents/auth_cookies.json')

client.close()
