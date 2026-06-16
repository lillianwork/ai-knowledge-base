"""Step 2e: Find sub-page tokens by examining DOM data attributes and React props."""
import sys, os, json, time, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp_utils import CDPClient

AGENTS_TOKEN = 'XdMvwRjw1iKlzukZzJAc6lJtnif'
AGENTS_URL = f'https://tauacgr5lqv.feishu.cn/wiki/{AGENTS_TOKEN}'
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'extracted', 'agents')
os.makedirs(OUT_DIR, exist_ok=True)

client = CDPClient()
print('Navigating to AI智能体...')
client.navigate(AGENTS_URL, wait=10)

# Get the full HTML of the sidebar area
print('\n--- Getting sidebar HTML ---')
sidebar_html = client.evaluate("""
(function() {
    // Find the sidebar/tree container
    var containers = document.querySelectorAll('[class*="sidebar"], [class*="catalog"], [class*="tree"], [class*="page-list"], nav');
    var results = [];
    containers.forEach(function(c) {
        if (c.textContent.includes('通用智能体对比') || c.textContent.includes('Coze')) {
            results.push({
                tag: c.tagName,
                className: c.className,
                innerHTML: c.innerHTML.substring(0, 5000)
            });
        }
    });
    return JSON.stringify(results);
})()
""", timeout=10)
if sidebar_html:
    data = json.loads(sidebar_html)
    for d in data:
        print(f"Container: {d['tag']}.{d['className'][:60]}")
        # Extract wiki tokens from the HTML
        tokens = re.findall(r'/wiki/([A-Za-z0-9]{20,30})', d['innerHTML'])
        if tokens:
            print(f"  Found tokens in HTML: {tokens[:10]}")

# Approach: get ALL links from the entire document
print('\n--- All wiki links in document ---')
all_links_js = """
(function() {
    var links = [];
    // Get all elements that could be links
    var all = document.querySelectorAll('*');
    var seen = new Set();
    all.forEach(function(el) {
        // Check onclick handlers and data attributes
        var attrs = [];
        for (var i = 0; i < el.attributes.length; i++) {
            var attr = el.attributes[i];
            attrs.push(attr.name + '=' + attr.value.substring(0, 100));
        }
        var attrStr = attrs.join('|');
        if (attrStr.includes('/wiki/') && !seen.has(attrStr)) {
            seen.add(attrStr);
            var text = el.textContent.trim().substring(0, 60);
            links.push({text: text, attrs: attrStr.substring(0, 300)});
        }
    });
    // Also check innerHTML for wiki tokens
    var html = document.body.innerHTML;
    var tokens = html.match(/\\/wiki\\/[A-Za-z0-9]{15,30}/g) || [];
    return JSON.stringify({linkCount: links.length, links: links.slice(0, 30), tokensInHtml: [...new Set(tokens)].slice(0, 30)});
})()
"""
all_links = client.evaluate(all_links_js, timeout=15)
if all_links:
    data = json.loads(all_links)
    print(f"Links with wiki attrs: {data['linkCount']}")
    for l in data.get('links', [])[:20]:
        print(f"  {l['text']} | {l['attrs'][:150]}")
    print(f"\nWiki tokens in HTML: {data.get('tokensInHtml', [])}")

# Also try React fiber approach
print('\n--- React fiber search ---')
fiber_js = """
(function() {
    var rootEl = document.getElementById('root') || document.querySelector('[data-reactroot]') || document.body.children[0];
    var fiberKey = Object.keys(rootEl).find(k => k.startsWith('__reactFiber') || k.startsWith('__reactInternalInstance'));
    if (!fiberKey) {
        // Try on document.body
        fiberKey = Object.keys(document.body).find(k => k.startsWith('__react'));
        rootEl = document.body;
    }
    if (!fiberKey) return JSON.stringify({error: 'No React fiber found'});

    // Walk the fiber tree looking for wiki tokens
    var tokens = [];
    var titles = [];
    function walk(fiber, depth) {
        if (!fiber || depth > 30) return;
        try {
            if (fiber.memoizedProps) {
                var props = fiber.memoizedProps;
                // Check for wiki token in props
                JSON.stringify(props, function(key, val) {
                    if (typeof val === 'string' && /^[A-Z][a-zA-Z0-9]{19,25}$/.test(val) && !tokens.includes(val)) {
                        tokens.push(val);
                    }
                    if (typeof val === 'string' && val.includes('从零基础到精通')) {
                        titles.push(val);
                    }
                    return val;
                });
            }
        } catch(e) {}
        walk(fiber.child, depth + 1);
        walk(fiber.sibling, depth + 1);
    }
    walk(rootEl[fiberKey], 0);
    return JSON.stringify({tokens: tokens.slice(0, 30), titles: titles.slice(0, 20)});
})()
"""
fiber_result = client.evaluate(fiber_js, timeout=15)
print(fiber_result[:2000] if fiber_result else "None")

client.close()
