"""Step 2f: Extract wiki tokens from tree nodes."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp_utils import CDPClient

AGENTS_URL = 'https://tauacgr5lqv.feishu.cn/wiki/XdMvwRjw1iKlzukZzJAc6lJtnif'
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'extracted', 'agents')
os.makedirs(OUT_DIR, exist_ok=True)

client = CDPClient()
print('Navigating to AI智能体...')
client.navigate(AGENTS_URL, wait=10)

# Extract tree node data - look for all attributes and React props
print('\n--- Tree node data ---')
tree_js = """
(function() {
    var results = [];
    var nodes = document.querySelectorAll('.workspace-tree-view-node-wrapper, [class*="tree-view-node"]');
    nodes.forEach(function(node) {
        var text = node.textContent.trim().substring(0, 80);
        // Get all attributes
        var attrs = {};
        for (var i = 0; i < node.attributes.length; i++) {
            var a = node.attributes[i];
            attrs[a.name] = a.value.substring(0, 100);
        }
        // Get React fiber key
        var reactKey = Object.keys(node).find(k => k.startsWith('__reactFiber') || k.startsWith('__reactProps'));
        var fiberData = null;
        if (reactKey) {
            try {
                var fiber = node[reactKey];
                fiberData = {
                    key: fiber.key,
                    hasProps: !!fiber.memoizedProps,
                    propsKeys: fiber.memoizedProps ? Object.keys(fiber.memoizedProps).slice(0, 30) : []
                };
                // Look for token/data in props
                if (fiber.memoizedProps) {
                    var p = fiber.memoizedProps;
                    if (p.node) fiberData.nodeKeys = Object.keys(p.node).slice(0, 20);
                    if (p.data) fiberData.dataKeys = Object.keys(p.data).slice(0, 20);
                    if (p.token) fiberData.token = p.token;
                    if (p.wikiToken) fiberData.wikiToken = p.wikiToken;
                }
            } catch(e) {
                fiberData = {error: e.message};
            }
        }
        if (text.length > 2 && (text.includes('精通') || text.includes('教程') || text.includes('指南') || text.includes('Agent') || text.includes('Code'))) {
            results.push({text: text, attrs: attrs, fiber: fiberData});
        }
    });
    return JSON.stringify(results.slice(0, 30));
})()
"""
tree_data = client.evaluate(tree_js, timeout=15)
if tree_data:
    data = json.loads(tree_data)
    print(f'Found {len(data)} tree nodes:')
    for d in data:
        print(f'  {d["text"]}')
        if d.get('fiber'):
            print(f'    fiber: {json.dumps(d["fiber"], ensure_ascii=False)[:200]}')

# Also get the full inner HTML of the tree container
print('\n--- Tree container HTML (extracting wiki tokens) ---')
tree_html = client.evaluate("""
(function() {
    var container = document.querySelector('.wiki-tree-inner-container');
    if (!container) container = document.querySelector('[class*="tree-view-container"]');
    if (!container) return 'No container';
    return container.innerHTML.substring(0, 8000);
})()
""", timeout=10)
if tree_html:
    import re
    tokens = re.findall(r'/wiki/([A-Za-z0-9]{15,30})', str(tree_html))
    print(f'Wiki tokens in tree HTML: {tokens}')
    # Also find any URL-like patterns
    urls = re.findall(r'https?://[^"\\s<>]+', str(tree_html))
    print(f'URLs in tree HTML: {urls[:10]}')

client.close()
