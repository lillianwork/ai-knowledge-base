"""Step 4 v2: Re-extract targeting .page-main directly (clean content, no sidebar)."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp_utils import CDPClient

BASE_URL = 'https://tauacgr5lqv.feishu.cn/wiki/'
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'extracted', 'agents')

with open(os.path.join(OUT_DIR, 'token_map.json'), 'r', encoding='utf-8') as f:
    token_map = json.load(f)

# Extract from .page-main which has sidebarScore=0 and high text content
CLEAN_EXTRACT_JS = """
(function() {
    var el = document.querySelector('.page-main');
    if (!el) {
        // Fallback: get body text and strip sidebar using markers
        var body = document.body.innerText;
        // The sidebar has identifiable end markers, find the actual content start
        var markers = ['上传日志', '分享'];
        for (var i = 0; i < markers.length; i++) {
            var idx = body.indexOf(markers[i]);
            if (idx > 100) {
                body = body.substring(0, idx);
            }
        }
        return body.substring(0, 20000);
    }

    var text = el.innerText;

    // Remove the AI summary block text if present
    var aiSummaryEl = el.querySelector('[class*="ai-summary"]');
    if (aiSummaryEl) {
        var aiText = aiSummaryEl.innerText;
        var idx = text.indexOf(aiText);
        if (idx >= 0) {
            text = text.substring(0, idx) + text.substring(idx + aiText.length);
        }
    }

    // Clean up excessive newlines
    text = text.replace(/\\n{4,}/g, '\\n\\n\\n');

    return text.trim().substring(0, 20000);
})()
"""

# Additional JS: try clicking "展开" (expand) if present, to reveal full content
EXPAND_JS = """
(function() {
    var expandButtons = document.querySelectorAll('[class*="expand"], [class*="fold"], [class*="unfold"]');
    var clicked = 0;
    expandButtons.forEach(function(btn) {
        var text = btn.textContent.trim();
        if (text.includes('展开') || text.includes('更多') || text.includes('全文')) {
            btn.click();
            clicked++;
        }
    });
    // Also try clicking elements with "展开" text
    if (clicked === 0) {
        var allEls = document.querySelectorAll('span, div, button');
        for (var i = 0; i < allEls.length; i++) {
            if (allEls[i].textContent.trim() === '展开') {
                allEls[i].click();
                clicked++;
                break;
            }
        }
    }
    return 'clicked ' + clicked + ' expand buttons';
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

    # Try expanding folded content
    expand_result = client.evaluate(EXPAND_JS, timeout=5)
    if expand_result and 'clicked 0' not in str(expand_result):
        print(f'  Expanded: {expand_result}')
        time.sleep(2)

    page_title = client.evaluate('document.title') or ''
    content = client.evaluate(CLEAN_EXTRACT_JS, timeout=10)
    content_len = len(content) if content else 0
    print(f'  Content: {content_len} chars | Page: {page_title[:80]}')

    # Detect page type
    is_directory = False
    if content:
        if '名称' in content[:300] and '所有者' in content[:300] and '修改时间' in content[:300]:
            is_directory = True
        if '列表' in content[:200] and '显示设置' in content[:200]:
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
        'page_type': page_type,
        'content_length': content_len
    })

    time.sleep(1)

# Save results summary
with open(os.path.join(clean_dir, '_summary.json'), 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print('\n===== DONE =====')
articles = [r for r in results if r['page_type'] == 'article']
directories = [r for r in results if r['page_type'] == 'directory']
print(f'Articles: {len(articles)} ({sum(r["content_length"] for r in articles)} total chars)')
print(f'Directories: {len(directories)} ({sum(r["content_length"] for r in directories)} total chars)')
for r in results:
    print(f'  [{r["idx"]:2d}] [{r["page_type"][:5]:5s}] {r["content_length"]:5d} chars | {r["title"]}')

client.close()
