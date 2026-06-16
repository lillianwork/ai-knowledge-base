"""Step 3e: Navigate directly to each sub-page wiki token and extract clean content."""
import sys, os, json, time, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp_utils import CDPClient

BASE_URL = 'https://tauacgr5lqv.feishu.cn/wiki/'
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'extracted', 'agents')

# Load token map
with open(os.path.join(OUT_DIR, 'token_map.json'), 'r', encoding='utf-8') as f:
    token_map = json.load(f)

# JS to extract only the article body (exclude sidebar, nav, comments, etc.)
CLEAN_CONTENT_JS = """
(function() {
    // Try finding the main page content div
    var selectors = [
        '.page-content-wrapper', '.wiki-content', '.doc-content',
        '[class*="page-content"]', '[class*="article-content"]',
        '.block-container', '[class*="editor-wrapper"]',
        '[class*="catalog-content"]', '[class*="detail-wrapper"]',
    ];
    var container = null;
    for (var s of selectors) {
        var el = document.querySelector(s);
        if (el && el.textContent.trim().length > 100) {
            container = el;
            break;
        }
    }

    if (!container) {
        // Fallback: get all text, then try to split at known boundaries
        var body = document.body.innerText;
        // Find the actual page title in the content area (not sidebar)
        // The sidebar ends and real content begins at "分享" marker
        var parts = body.split('分享\\n');
        if (parts.length >= 2) {
            // Take the last segment which is usually the content
            body = parts.slice(-2).join('\\n');
        }
        // Remove trailing chrome
        var chromeMarkers = ['评论', '上传日志', '联系客服', '你可能还想问'];
        for (var m of chromeMarkers) {
            var idx = body.indexOf(m);
            if (idx > 100) {
                body = body.substring(0, idx);
            }
        }
        return body.trim().substring(0, 15000);
    }

    var text = container.innerText;

    // Remove trailing chrome
    var chromeMarkers = ['评论', '上传日志', '联系客服', '你可能还想问'];
    for (var m of chromeMarkers) {
        var idx = text.indexOf(m);
        if (idx > 100) {
            text = text.substring(0, idx);
        }
    }
    return text.trim().substring(0, 15000);
})()
"""

client = CDPClient()
clean_dir = os.path.join(OUT_DIR, 'clean')
os.makedirs(clean_dir, exist_ok=True)

for idx, (token, info) in enumerate(token_map.items()):
    title = info['title']
    url = f'{BASE_URL}{token}'
    print(f'\n[{idx+1}/20] {title}')
    print(f'  URL: {url}')

    # Navigate directly
    client.navigate(url, wait=8)

    # Get page title
    page_title = client.evaluate('document.title')
    print(f'  Page: {page_title}')

    # Extract clean content
    content = client.evaluate(CLEAN_CONTENT_JS, timeout=10)
    content_len = len(content) if content else 0
    print(f'  Content: {content_len} chars')

    # Save clean version
    safe_name = f'{idx+1:02d}_{token}.txt'
    filepath = os.path.join(clean_dir, safe_name)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f'TOKEN: {token}\n')
        f.write(f'TITLE: {title}\n')
        f.write(f'URL: {url}\n')
        f.write(f'PAGE_TITLE: {page_title}\n')
        f.write(f'CONTENT_LENGTH: {content_len}\n')
        f.write('='*60 + '\n\n')
        f.write(content or 'NO CONTENT')
    print(f'  Saved: clean/{safe_name}')

    # Also save a metadata record
    info['token'] = token
    info['page_title'] = page_title
    info['content_length'] = content_len

    time.sleep(1)

# Save updated metadata
with open(os.path.join(OUT_DIR, 'subpage_metadata.json'), 'w', encoding='utf-8') as f:
    json.dump(token_map, f, ensure_ascii=False, indent=2)

print('\n===== DONE =====')
client.close()
