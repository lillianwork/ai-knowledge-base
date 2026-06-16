"""Step 4: Explore DOM structure to find correct content selectors."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp_utils import CDPClient

# Test with a content-rich page: Hermes Agent
TEST_URL = 'https://tauacgr5lqv.feishu.cn/wiki/Ey1sw5L1tij6WLkBhNQc092Lnrd'

client = CDPClient()
client.navigate(TEST_URL, wait=8)

# 1. Find the main content area by exploring class names and structure
explore_js = """
(function() {
    var results = [];

    // Check all major container divs
    var allDivs = document.querySelectorAll('div[class*="page"], div[class*="content"], div[class*="doc"], div[class*="editor"], div[class*="article"], div[class*="catalog"], div[class*="detail"], div[class*="block"], main, article, section');
    var seen = new Set();

    allDivs.forEach(function(el) {
        var cls = el.className || '';
        if (typeof cls !== 'string') cls = '';
        var textLen = el.textContent.trim().length;
        var key = cls.substring(0, 60);

        if (textLen > 200 && !seen.has(key)) {
            seen.add(key);
            results.push({
                tag: el.tagName,
                class: cls.substring(0, 100),
                id: el.id || '',
                textLen: textLen,
                textPreview: el.textContent.trim().substring(0, 100)
            });
        }
    });

    // Sort by text length
    results.sort(function(a, b) { return b.textLen - a.textLen; });

    return JSON.stringify(results.slice(0, 20));
})()
"""

print("=== Major content containers ===")
data = client.evaluate(explore_js, timeout=15)
if data:
    items = json.loads(data)
    for item in items:
        print(f"  [{item['tag']}] class='{item['class']}' id='{item['id']}' len={item['textLen']}")
        print(f"    Preview: {item['textPreview'][:120]}")

# 2. Specifically check for the page content wrapper
print("\n=== Specific selector tests ===")
selector_tests = [
    '.page-content-wrapper',
    '[class*="page-content"]',
    '[class*="doc-content"]',
    '[class*="editor-content"]',
    '[class*="wiki-content"]',
    '[class*="catalog-content"]',
    '[class*="detail-content"]',
    '[class*="block-container"]',
    '[class*="article"]',
    'main',
    '[role="main"]',
    '[class*="docs"]',
    '[class*="render"]',
    '[class*="view"]',
    '[class*="canvas"]',
    '[class*="sheet"]',
]

test_js_template = """
(function() {
    var results = [];
    var selectors = %s;
    selectors.forEach(function(s) {
        var el = document.querySelector(s);
        if (el) {
            results.push({
                selector: s,
                textLen: el.textContent.trim().length,
                childCount: el.children.length,
                class: (el.className || '').substring(0, 100)
            });
        }
    });
    return JSON.stringify(results);
})()
"""

test_data = client.evaluate(test_js_template % json.dumps(selector_tests), timeout=10)
if test_data:
    items = json.loads(test_data)
    for item in items:
        print(f"  FOUND: {item['selector']} -> class='{item['class']}' len={item['textLen']} children={item['childCount']}")

# 3. Find the content area that has article body but NOT sidebar
print("\n=== Looking for article-only content (excluding sidebar) ===")
find_article_js = """
(function() {
    // The sidebar in Feishu has specific structure - find elements OUTSIDE the sidebar
    var sidebarSelectors = [
        '[class*="sidebar"]', '[class*="side-bar"]', '[class*="Sidebar"]',
        '[class*="left-panel"]', '[class*="tree-view"]', '[class*="navigation"]',
        '[class*="catalogue"]', '[class*="workspace-tree"]'
    ];

    // Find sidebar elements
    var sidebarEls = [];
    sidebarSelectors.forEach(function(s) {
        var els = document.querySelectorAll(s);
        els.forEach(function(el) { sidebarEls.push(el); });
    });

    // Get the main scrollable area - often a specific div
    var scrollContainers = document.querySelectorAll('[class*="scroll"], [class*="Scroll"]');
    var scrollInfo = [];
    scrollContainers.forEach(function(el) {
        var cls = el.className || '';
        if (typeof cls !== 'string') cls = '';
        scrollInfo.push({
            class: cls.substring(0, 100),
            textLen: el.textContent.trim().length,
            children: el.children.length
        });
    });

    // Also try to find the "right side" content area
    // In Feishu, the layout typically has a left sidebar and right content
    var allTopDivs = document.querySelectorAll('body > div, #app > div, [id="app"] > div');
    var topInfo = [];
    allTopDivs.forEach(function(el) {
        var cls = el.className || '';
        if (typeof cls !== 'string') cls = '';
        topInfo.push({
            tag: el.tagName,
            class: cls.substring(0, 120),
            id: el.id || '',
            children: el.children.length,
            textLen: el.textContent.trim().length
        });
    });

    return JSON.stringify({
        scrollContainers: scrollInfo.slice(0, 10),
        topLevelDivs: topInfo.slice(0, 10),
        sidebarCount: sidebarEls.length
    });
})()
"""

info = client.evaluate(find_article_js, timeout=10)
if info:
    data = json.loads(info)
    print(f"Sidebar elements found: {data.get('sidebarCount', 0)}")
    print(f"\nScroll containers:")
    for item in data.get('scrollContainers', []):
        print(f"  class='{item['class']}' len={item['textLen']} children={item['children']}")
    print(f"\nTop-level divs:")
    for item in data.get('topLevelDivs', []):
        print(f"  [{item['tag']}] class='{item['class']}' id='{item['id']}' children={item['children']} len={item['textLen']}")

# 4. Try to get clean content by finding the largest text block that's NOT the sidebar
print("\n=== Clean content extraction attempt ===")
clean_extract_js = """
(function() {
    // Strategy: Find all text-containing divs, sort by text length,
    // and pick the one that doesn't contain sidebar markers

    var sidebarMarkers = ['共研社AIGC知识库', 'AI智能体', 'AI绘画', 'AI视频', 'AI写作',
                          'AI办公', 'AI编程', 'AI教育', 'AI声音', 'AI音乐', 'AI数字人',
                          'AIGC新手入门教程', '小红书热门资料精选', 'AI提示词', 'AI研究报告',
                          '《一人公司》行动指南知识库', '广州沐瓜科技有限公司'];

    var allDivs = document.querySelectorAll('div, section, article, main');
    var candidates = [];

    allDivs.forEach(function(el) {
        var text = el.textContent.trim();
        var len = text.length;
        if (len > 500) {
            // Count how many sidebar markers appear
            var sidebarScore = 0;
            sidebarMarkers.forEach(function(m) {
                if (text.includes(m)) sidebarScore++;
            });
            candidates.push({
                tag: el.tagName,
                class: (el.className || '').substring(0, 100),
                textLen: len,
                sidebarScore: sidebarScore,
                textPreview: text.substring(0, 200)
            });
        }
    });

    // Sort: prefer elements with low sidebar score but high text length
    candidates.sort(function(a, b) {
        if (a.sidebarScore !== b.sidebarScore) return a.sidebarScore - b.sidebarScore;
        return b.textLen - a.textLen;
    });

    return JSON.stringify(candidates.slice(0, 10));
})()
"""

clean_data = client.evaluate(clean_extract_js, timeout=15)
if clean_data:
    items = json.loads(clean_data)
    for item in items:
        print(f"  [{item['tag']}] sidebarScore={item['sidebarScore']} len={item['textLen']} class='{item['class']}'")
        print(f"    Preview: {item['textPreview'][:150]}")
        print()

client.close()
