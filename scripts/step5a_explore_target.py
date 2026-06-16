"""Step 5a: Explore target wiki page and test content creation via CDP."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp_utils import CDPClient

TARGET_URL = 'https://tauacgr5lqv.feishu.cn/wiki/DFs5wdk1YiHfNNkACcecO5DAn4c'

client = CDPClient()
client.navigate(TARGET_URL, wait=10)

print("=== Target page info ===")
print(f"URL: {client.get_current_url()}")
print(f"Title: {client.evaluate('document.title')}")

# Check page content
body_text = client.evaluate('document.body.innerText.substring(0, 3000)')
print(f"\nBody text (first 500):\n{body_text[:500] if body_text else 'EMPTY'}")
print(f"Body length: {len(body_text or '')}")

# Check if the page is editable - look for edit button or editor presence
edit_check_js = """
(function() {
    var info = {};

    // Check for edit button
    var editBtn = document.querySelector('[class*="edit"], [class*="Edit"], button[class*="edit"]');
    info.hasEditButton = !!editBtn;
    if (editBtn) info.editBtnText = editBtn.textContent.trim().substring(0, 50);

    // Check for editor area
    var editor = document.querySelector('.editor-container, [class*="editor"], [contenteditable="true"]');
    info.hasEditor = !!editor;

    // Check for "添加" or "新建" buttons (add/new page)
    var addBtns = [];
    var allBtns = document.querySelectorAll('button, [role="button"], span[class*="add"], div[class*="add"]');
    allBtns.forEach(function(btn) {
        var text = btn.textContent.trim();
        if (text.includes('新建') || text.includes('添加') || text.includes('添加页面') || text.includes('创建')) {
            addBtns.push({text: text, class: (btn.className || '').substring(0, 80), tag: btn.tagName});
        }
    });
    info.addButtons = addBtns.slice(0, 10);

    // Check sidebar for "+" or add page buttons
    var sidebarAddBtns = document.querySelectorAll('[class*="sidebar"] [class*="add"], [class*="tree"] [class*="add"], [class*="catalogue"] [class*="add"]');
    info.sidebarAddButtons = sidebarAddBtns.length;

    // Check for the page content type
    var pageMain = document.querySelector('.page-main');
    info.hasPageMain = !!pageMain;
    if (pageMain) info.pageMainLen = pageMain.textContent.trim().length;

    // Check if there's a 'plus' or 'new page' icon in the sidebar near this page
    var treeItems = document.querySelectorAll('[class*="tree"] [class*="node"]');
    info.treeNodeCount = treeItems.length;

    return JSON.stringify(info);
})()
"""

info = client.evaluate(edit_check_js, timeout=10)
if info:
    data = json.loads(info)
    print(f"\n=== Page state ===")
    for k, v in data.items():
        print(f"  {k}: {v}")

# Also check what the wiki page looks like - does it have a sidebar tree?
print("\n=== Sidebar/Menu structure ===")
sidebar_js = """
(function() {
    var results = [];
    // Look for the page's own title and structure
    var titleEl = document.querySelector('.page-title, [class*="page-title"], h1, [class*="doc-title"]');
    if (titleEl) {
        results.push({type: 'title', text: titleEl.textContent.trim().substring(0, 100)});
    }

    // Check the workspace tree for existing sub-pages
    var treeNodes = document.querySelectorAll('[data-node-level]');
    var nodes = [];
    treeNodes.forEach(function(node) {
        var level = node.getAttribute('data-node-level');
        var text = node.textContent.trim().substring(0, 80);
        nodes.push({level: level, text: text});
    });
    results.push({type: 'tree_nodes', count: nodes.length, sample: nodes.slice(0, 15)});

    return JSON.stringify(results);
})()
"""

sidebar_data = client.evaluate(sidebar_js, timeout=10)
if sidebar_data:
    items = json.loads(sidebar_data)
    for item in items:
        if item['type'] == 'tree_nodes':
            print(f"  Tree nodes: {item['count']}")
            for n in item.get('sample', []):
                print(f"    [L{n['level']}] {n['text']}")
        else:
            print(f"  {item['type']}: {item.get('text', '')}")

# Now try to find how to create a new page / edit this page
print("\n=== Testing content editing ===")
# First, try to click into the editor area
click_editor_js = """
(function() {
    // Try to find and click the main content area to focus
    var targets = [
        '.page-main', '[class*="page-content"]', '.editor-container',
        '[class*="block-container"]', '.zone-container'
    ];
    for (var s of targets) {
        var el = document.querySelector(s);
        if (el) {
            el.click();
            el.focus();
            return 'clicked ' + s;
        }
    }
    return 'no target found';
})()
"""
print(f"Focus attempt: {client.evaluate(click_editor_js, timeout=5)}")
time.sleep(2)

# Check if page is now in edit mode or if we can type
edit_mode_js = """
(function() {
    var info = {};
    info.contentEditable = document.querySelector('[contenteditable="true"]') ? true : false;
    info.activeElement = document.activeElement ? document.activeElement.tagName + '.' + (document.activeElement.className || '').substring(0, 80) : 'none';
    info.selectionInEditor = document.querySelector('.editor-container [contenteditable="true"]') ? true : false;
    return JSON.stringify(info);
})()
"""
print(f"Edit mode: {client.evaluate(edit_mode_js, timeout=5)}")

client.close()
