"""Step 3c: Verify if clicking sidebar actually changes content."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp_utils import CDPClient

AGENTS_URL = 'https://tauacgr5lqv.feishu.cn/wiki/XdMvwRjw1iKlzukZzJAc6lJtnif'

client = CDPClient()
client.navigate(AGENTS_URL, wait=8)

# Get initial content
before = client.get_page_text(3000)
print(f'BEFORE (first 500): {before[:500]}')
print(f'BEFORE length: {len(before or "")}')

# Click "通用智能体对比" in sidebar
click_js = """
(function() {
    var nodes = document.querySelectorAll('.workspace-tree-view-node-wrapper, [class*="tree-view-node"]');
    for (var i = 0; i < nodes.length; i++) {
        var text = nodes[i].textContent.trim();
        if (text.includes('通用智能体对比')) {
            var clickable = nodes[i].querySelector('[class*="content"], [class*="title"], span') || nodes[i];
            clickable.click();
            return 'clicked idx=' + i + ' text=' + text.substring(0, 30);
        }
    }
    return 'NOT FOUND';
})()
"""
print(f'\nClick result: {client.evaluate(click_js, timeout=8)}')
time.sleep(5)

# Get content after click
after = client.get_page_text(3000)
print(f'\nAFTER (first 500): {after[:500]}')
print(f'AFTER length: {len(after or "")}')

# Diff
if before != after:
    print('\nCONTENT CHANGED!')
else:
    print('\nCONTENT SAME - clicking sidebar does not change page content')

# Also check URL
url_after = client.get_current_url()
print(f'\nURL after click: {url_after}')
print(f'Page title: {client.evaluate("document.title")}')

# Try navigating directly to a sub-page using a guessed URL pattern
# Feishu URLs are: /wiki/{wiki_token}
# The sub-pages should have their own tokens
print('\n--- Trying to find sub-page tokens ---')
# Check if the sidebar tree has onClick handlers that reveal URLs
find_onclick = """
(function() {
    var results = [];
    var nodes = document.querySelectorAll('.workspace-tree-view-node-wrapper, [class*="tree-view-node"]');
    nodes.forEach(function(node) {
        var text = node.textContent.trim().substring(0, 80);
        if (text.includes('通用智能体对比') || text.includes('Coze从零基础到精通')) {
            // Check all event listeners by examining inner elements
            var children = node.querySelectorAll('*');
            var attrs = [];
            children.forEach(function(child) {
                for (var i = 0; i < child.attributes.length; i++) {
                    var a = child.attributes[i];
                    attrs.push(a.name + '=' + a.value.substring(0, 80));
                }
            });
            results.push({text: text, attrs: attrs.slice(0, 10)});
        }
    });
    return JSON.stringify(results);
})()
"""
print(client.evaluate(find_onclick, timeout=10))

client.close()
