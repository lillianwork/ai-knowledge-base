"""Step 3: Click each AI智能体 sub-page in sidebar, extract content & URL."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp_utils import CDPClient

AGENTS_URL = 'https://tauacgr5lqv.feishu.cn/wiki/XdMvwRjw1iKlzukZzJAc6lJtnif'
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'extracted', 'agents')
os.makedirs(OUT_DIR, exist_ok=True)

# Known sub-page titles to extract
SUB_PAGES = [
    '通用智能体对比',
    '基础概念学习指南',
    '理论知识学习指南',
    'Gemin3 pro从零基础到精通学习手册',
    'Coze从零基础到精通',
    'n8n从零基础到精通',
    'GPTs从零基础到精通',
    'Manus从零基础到精通',
    'flowith从零基础到精通',
    'Lovart.ai从零基础到精通',
    'Skywork 天工从零基础到精通',
    'MiniMax Agent从零基础到精通',
    'OpenClaw从零基础到精通',
    'Skills从零基础到精通',
    'Claude code',
    'WorkBuddy 从零基础到精通实操手册',
    'Obsidian从零基础到精通学习手册完整版',
    'Hermes Agent从零基础到精通',
    'Codex入门教程完整版',
    'Vibe Coding 从入门到精通学习手册',
]

client = CDPClient()

for i, title in enumerate(SUB_PAGES):
    print(f'\n===== [{i+1}/20] {title} =====')

    # Navigate to AI智能体 page first
    client.navigate(AGENTS_URL, wait=6)

    # Click the sub-page link in sidebar by finding its text
    click_js = f"""
    (function() {{
        // Find all tree nodes and click the one matching this title
        var nodes = document.querySelectorAll('.workspace-tree-view-node-wrapper, [class*="tree-view-node"]');
        for (var i = 0; i < nodes.length; i++) {{
            var text = nodes[i].textContent.trim();
            if (text.includes('{title}')) {{
                // Find the clickable element inside
                var clickable = nodes[i].querySelector('[class*="content"], [class*="title"], span, a') || nodes[i];
                clickable.click();
                return 'clicked';
            }}
        }}
        // Try clicking by inner text search
        var allElems = document.querySelectorAll('[class*="tree"] *');
        for (var j = 0; j < allElems.length; j++) {{
            if (allElems[j].textContent.trim().includes('{title}') && allElems[j].children.length === 0) {{
                allElems[j].click();
                return 'clicked-v2';
            }}
        }}
        return 'not found';
    }})()
    """
    result = client.evaluate(click_js, timeout=8)
    print(f'Click result: {result}')

    if result and 'clicked' in str(result):
        # Wait for navigation and render
        time.sleep(6)

        # Get the new URL
        new_url = client.get_current_url()
        print(f'URL: {new_url}')

        # Extract wiki token from URL
        token = ''
        if '/wiki/' in (new_url or ''):
            token = new_url.split('/wiki/')[1].split('?')[0]

        # Get page title
        page_title = client.evaluate('document.title')
        print(f'Title: {page_title}')

        # Extract content
        content = client.get_page_text(20000)

        # Save
        filename = f'{i+1:02d}_{title.replace("/", "_").replace(" ", "_")}.txt'
        filepath = os.path.join(OUT_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f'TOKEN: {token}\n')
            f.write(f'URL: {new_url}\n')
            f.write(f'TITLE: {page_title}\n')
            f.write(f'ORIGINAL_SUB_PAGE: {title}\n')
            f.write('='*60 + '\n\n')
            f.write(content or 'NO CONTENT')
        print(f'Saved: {filename} ({len(content or "")} chars)')
    else:
        print(f'  FAILED to click: {result}')
        # Save empty placeholder
        filename = f'{i+1:02d}_{title.replace("/", "_").replace(" ", "_")}.txt'
        filepath = os.path.join(OUT_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f'TOKEN: N/A\nURL: N/A\nTITLE: N/A\nORIGINAL_SUB_PAGE: {title}\n')
            f.write('FAILED TO EXTRACT\n')

    # Small delay between pages
    time.sleep(1)

print('\n===== EXTRACTION COMPLETE =====')
client.close()
