"""Step 4b: Explore DOM for directory-type pages (n8n) and refine extraction."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp_utils import CDPClient

# Test with a directory-type page: n8n
TEST_URL = 'https://tauacgr5lqv.feishu.cn/wiki/HisTwsV5Oin8VWkZvnCcLMLInYe'

client = CDPClient()
client.navigate(TEST_URL, wait=8)

explore_js = """
(function() {
    var results = [];
    var sidebarMarkers = ['共研社AIGC知识库', 'AI智能体', 'AI绘画', 'AI视频', 'AI写作',
                          'AI办公', 'AI编程', 'AI教育', 'AI声音', 'AI音乐', 'AI数字人',
                          'AIGC新手入门教程', '小红书热门资料精选', 'AI提示词', 'AI研究报告',
                          '《一人公司》行动指南知识库', '广州沐瓜科技有限公司'];

    var allDivs = document.querySelectorAll('div, section, article, main');
    var candidates = [];

    allDivs.forEach(function(el) {
        var text = el.textContent.trim();
        var len = text.length;
        if (len > 300) {
            var sidebarScore = 0;
            sidebarMarkers.forEach(function(m) {
                if (text.includes(m)) sidebarScore++;
            });
            candidates.push({
                tag: el.tagName,
                class: (el.className || '').substring(0, 100),
                id: el.id || '',
                textLen: len,
                sidebarScore: sidebarScore,
                textPreview: text.substring(0, 200)
            });
        }
    });

    candidates.sort(function(a, b) {
        if (a.sidebarScore !== b.sidebarScore) return a.sidebarScore - b.sidebarScore;
        return b.textLen - a.textLen;
    });

    return JSON.stringify(candidates.slice(0, 15));
})()
"""

print("=== Content containers for n8n (directory-type page) ===")
data = client.evaluate(explore_js, timeout=15)
if data:
    items = json.loads(data)
    for item in items:
        print(f"  [{item['tag']}] sidebarScore={item['sidebarScore']} len={item['textLen']} class='{item['class']}'")
        print(f"    Preview: {item['textPreview'][:150]}")
        print()

# Check specifically for grid/table/list views
print("=== Grid/table/list structure ===")
grid_js = """
(function() {
    var results = [];

    // Check for table views (common in directory pages)
    var tables = document.querySelectorAll('table, [class*="table"], [class*="grid"], [class*="list"], [class*="card"]');
    tables.forEach(function(el) {
        var cls = el.className || '';
        if (typeof cls !== 'string') cls = '';
        var text = el.textContent.trim();
        if (text.length > 50) {
            results.push({
                tag: el.tagName,
                class: cls.substring(0, 100),
                textLen: text.length,
                rowCount: el.querySelectorAll('tr, [class*="row"]').length,
                textPreview: text.substring(0, 200)
            });
        }
    });

    // Also check for the specific page content area
    var pageMain = document.querySelector('.page-main');
    var pageBlockChildren = document.querySelector('.page-block-children');

    return JSON.stringify({
        tables: results.slice(0, 10),
        pageMainExists: !!pageMain,
        pageMainLen: pageMain ? pageMain.textContent.trim().length : 0,
        pageBlockChildrenExists: !!pageBlockChildren,
        pageBlockChildrenLen: pageBlockChildren ? pageBlockChildren.textContent.trim().length : 0,
        pageBlockPreview: pageBlockChildren ? pageBlockChildren.textContent.trim().substring(0, 300) : 'N/A'
    });
})()
"""

info = client.evaluate(grid_js, timeout=10)
if info:
    data = json.loads(info)
    print(f"page-main exists: {data.get('pageMainExists')}, len={data.get('pageMainLen')}")
    print(f"page-block-children exists: {data.get('pageBlockChildrenExists')}, len={data.get('pageBlockChildrenLen')}")
    print(f"page-block-children preview: {data.get('pageBlockPreview', '')[:300]}")
    print(f"\nGrid/table items:")
    for item in data.get('tables', []):
        print(f"  [{item['tag']}] class='{item['class']}' len={item['textLen']} rows={item['rowCount']}")
        print(f"    Preview: {item['textPreview'][:150]}")

client.close()
