"""Step 4: Re-extract all 20 AI智能体 sub-pages using correct DOM selectors."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp_utils import CDPClient

BASE_URL = 'https://tauacgr5lqv.feishu.cn/wiki/'
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'extracted', 'agents')

with open(os.path.join(OUT_DIR, 'token_map.json'), 'r', encoding='utf-8') as f:
    token_map = json.load(f)

# Improved JS: find .page-block-children, remove AI summary, get clean text
CLEAN_EXTRACT_JS = """
(function() {
    // Primary: get the page content blocks container
    var contentEl = document.querySelector('.page-block-children');
    if (!contentEl) {
        // Fallback: get .page-main
        contentEl = document.querySelector('.page-main');
    }
    if (!contentEl) {
        // Last resort: body minus sidebar
        var body = document.body.innerText;
        var idx = body.indexOf('上传日志');
        if (idx > 100) body = body.substring(0, idx);
        return body.substring(0, 20000);
    }

    // Clone so we can remove unwanted elements
    var clone = contentEl.cloneNode(true);

    // Remove AI summary block
    var aiBlocks = clone.querySelectorAll('[class*="ai-summary"], [class*="docx-ai-summary"]');
    aiBlocks.forEach(function(el) { el.remove(); });

    // Remove empty block placeholders
    var allChildren = clone.querySelectorAll('[class*="block"]');
    allChildren.forEach(function(el) {
        var text = el.textContent.trim();
        if (text.length === 0 || text === '​') {
            el.remove();
        }
    });

    var text = clone.textContent.trim();

    // Remove trailing chrome markers
    var chromeMarkers = ['评论', '上传日志', '联系客服', '你可能还想问', '反向引用', '本文引用', '关系图'];
    for (var i = 0; i < chromeMarkers.length; i++) {
        var idx = text.indexOf(chromeMarkers[i]);
        if (idx > 100) {
            text = text.substring(0, idx);
        }
    }

    return text.substring(0, 20000);
})()
"""

client = CDPClient()
clean_dir = os.path.join(OUT_DIR, 'clean_v2')
os.makedirs(clean_dir, exist_ok=True)

results = []

for idx, (token, info) in enumerate(token_map.items()):
    title = info['title']
    url = f'{BASE_URL}{token}'
    print(f'\n[{idx+1}/20] {title}')

    client.navigate(url, wait=8)

    page_title = client.evaluate('document.title') or ''
    content = client.evaluate(CLEAN_EXTRACT_JS, timeout=10)
    content_len = len(content) if content else 0
    print(f'  Content: {content_len} chars | Page: {page_title[:80]}')

    # Detect page type
    is_directory = False
    if content:
        # Directory pages have patterns like "名称所有者修改时间" (table headers)
        if '名称' in content[:200] and '所有者' in content[:200] and '修改时间' in content[:200]:
            is_directory = True
        # Or have "列表" and "显示设置" near the top
        if '列表' in content[:100] and '显示设置' in content[:100]:
            is_directory = True

    page_type = 'directory' if is_directory else 'article'
    print(f'  Type: {page_type}')

    # Save
    safe_name = f'{idx+1:02d}_{token}.txt'
    filepath = os.path.join(clean_dir, safe_name)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f'TOKEN: {token}\n')
        f.write(f'TITLE: {title}\n')
        f.write(f'URL: {url}\n')
        f.write(f'PAGE_TITLE: {page_title}\n')
        f.write(f'PAGE_TYPE: {page_type}\n')
        f.write(f'CONTENT_LENGTH: {content_len}\n')
        f.write('='*60 + '\n\n')
        f.write(content or 'NO CONTENT')

    results.append({
        'idx': idx + 1,
        'token': token,
        'title': title,
        'page_title': page_title,
        'page_type': page_type,
        'content_length': content_len
    })

    time.sleep(1)

# Save results summary
with open(os.path.join(clean_dir, '_summary.json'), 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print('\n===== DONE =====')
print(f'Articles: {sum(1 for r in results if r["page_type"] == "article")}')
print(f'Directories: {sum(1 for r in results if r["page_type"] == "directory")}')
for r in results:
    print(f'  [{r["idx"]:2d}] [{r["page_type"][:5]:5s}] {r["content_length"]:5d} chars | {r["title"]}')

client.close()
