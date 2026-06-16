"""Step 3d: Extract main content for each AI智能体 sub-page by clicking sidebar items."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp_utils import CDPClient

AGENTS_URL = 'https://tauacgr5lqv.feishu.cn/wiki/XdMvwRjw1iKlzukZzJAc6lJtnif'
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'extracted', 'agents')
os.makedirs(OUT_DIR, exist_ok=True)

SUB_PAGES = [
    '通用智能体对比', '基础概念学习指南', '理论知识学习指南',
    'Gemin3 pro从零基础到精通学习手册', 'Coze从零基础到精通',
    'n8n从零基础到精通', 'GPTs从零基础到精通', 'Manus从零基础到精通',
    'flowith从零基础到精通', 'Lovart.ai从零基础到精通',
    'Skywork 天工从零基础到精通', 'MiniMax Agent从零基础到精通',
    'OpenClaw从零基础到精通', 'Skills从零基础到精通', 'Claude code',
    'WorkBuddy 从零基础到精通实操手册', 'Obsidian从零基础到精通学习手册完整版',
    'Hermes Agent从零基础到精通', 'Codex入门教程完整版',
    'Vibe Coding 从入门到精通学习手册',
]

# JS to click a sidebar item by title
def make_click_js(title):
    return f"""
    (function() {{
        var nodes = document.querySelectorAll('[data-node-level="3"]');
        for (var i = 0; i < nodes.length; i++) {{
            var text = nodes[i].textContent.trim();
            if (text.includes('{title}')) {{
                nodes[i].click();
                return 'clicked ' + text.substring(0, 40);
            }}
        }}
        return 'not found';
    }})()
    """

# JS to extract main content (exclude sidebar, nav, header, footer)
GET_CONTENT_JS = """
(function() {
    // Try to find the main article content
    var selectors = [
        '[class*="page-content"]', '[class*="doc-content"]', '[class*="wiki-content"]',
        '[class*="article"]', '[class*="editor-content"]', '[class*="block-container"]',
        '[class*="catalogue-content"]', '[class*="detail-content"]',
        'main', '[role="main"]'
    ];
    var content = null;
    for (var s of selectors) {
        content = document.querySelector(s);
        if (content && content.textContent.trim().length > 200) break;
    }
    if (!content) {
        // Fallback: get body text minus sidebar
        var body = document.body.innerText;
        // Remove known sidebar strings
        var sidebarEnd = body.indexOf('上传日志');
        if (sidebarEnd > 0) {
            body = body.substring(0, sidebarEnd);
        }
        return body.substring(0, 20000);
    }
    return content.innerText.substring(0, 20000);
})()
"""

client = CDPClient()

for i, title in enumerate(SUB_PAGES):
    print(f'\n[{i+1}/20] {title}')

    # Navigate to AI智能体 page
    client.navigate(AGENTS_URL, wait=7)

    # Click the sub-page
    click_result = client.evaluate(make_click_js(title), timeout=8)
    print(f'  Click: {click_result}')

    if 'clicked' in str(click_result):
        time.sleep(4)

        # Extract the main content
        content = client.evaluate(GET_CONTENT_JS, timeout=10)
        content_len = len(content) if content else 0
        print(f'  Content: {content_len} chars')

        # Get actual URL (may have hash or query param for this section)
        url = client.get_current_url()

        # Save
        safe_name = title.replace('/', '_').replace(' ', '_').replace(':', '').replace('：', '')
        filename = f'{i+1:02d}_{safe_name}.txt'
        filepath = os.path.join(OUT_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f'TITLE: {title}\n')
            f.write(f'URL: {url}\n')
            f.write(f'CONTENT_LENGTH: {content_len}\n')
            f.write('='*60 + '\n\n')
            f.write(content or 'NO CONTENT')
        print(f'  Saved: {filename}')
    else:
        safe_name = title.replace('/', '_').replace(' ', '_').replace(':', '').replace('：', '')
        filename = f'{i+1:02d}_{safe_name}.txt'
        filepath = os.path.join(OUT_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f'TITLE: {title}\nURL: N/A\nFAILED TO CLICK\n')
        print(f'  FAILED')

    time.sleep(0.5)

print('\n===== DONE =====')
client.close()
