"""Step 5: Update ai-knowledge-base.html with cleaned AI智能体 content."""
import sys, os, json, re, html

FINAL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'extracted', 'agents', 'final')
HTML_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ai-knowledge-base.html')

# Read the cleaned markdown files
files_data = []
for fname in sorted(os.listdir(FINAL_DIR)):
    if fname.startswith('00_') or not fname.endswith('.md'):
        continue
    fpath = os.path.join(FINAL_DIR, fname)
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()
    files_data.append({'filename': fname, 'content': content})

def md_to_html_simple(text):
    """Simple markdown to HTML conversion for the extracted content."""
    if not text:
        return ''

    # Escape HTML
    text = html.escape(text)

    # Convert markdown headers to HTML
    text = re.sub(r'^### (.+)$', r'<h4>\1</h4>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)

    # Convert bold/italic
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)

    # Convert blockquotes (remove the > prefix and wrap)
    lines = text.split('\n')
    result = []
    in_blockquote = False
    for line in lines:
        if line.startswith('&gt; '):
            if not in_blockquote:
                result.append('<blockquote>')
                in_blockquote = True
            result.append(line[5:])  # Remove "&gt; " prefix
        else:
            if in_blockquote:
                result.append('</blockquote>')
                in_blockquote = False
            result.append(line)
    if in_blockquote:
        result.append('</blockquote>')
    text = '\n'.join(result)

    # Convert horizontal rules
    text = text.replace('---', '<hr>')

    # Convert line breaks to <br> or <p>
    paragraphs = text.split('\n\n')
    html_parts = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        if p.startswith('<h') or p.startswith('<blockquote') or p.startswith('<hr'):
            html_parts.append(p)
        elif p.startswith('<'):
            html_parts.append(p)
        else:
            # Convert single newlines to <br>
            p = p.replace('\n', '<br>')
            html_parts.append(f'<p>{p}</p>')
    return '\n'.join(html_parts)

# Generate the new AI智能体 section HTML
section_html = '''        <section class="category" id="agents">
            <div class="cat-header">
                <h2>🤖 AI智能体</h2>
                <a class="feishu-link" href="https://tauacgr5lqv.feishu.cn/wiki/XdMvwRjw1iKlzukZzJAc6lJtnif" target="_blank" rel="noopener">在飞书中打开 &#8599;</a>
            </div>
            <p class="cat-desc">Agent大趋势与各平台从零到精通：Coze、n8n、GPTs、Manus、Claude Code等20个工具。以下内容整理自共研社AIGC知识库，已清洗排版并重新归类。</p>

            <div class="sub-pages">
                <h3>📋 工具目录与详情 (20)</h3>
                <p style="color:var(--text-secondary);font-size:.82rem;margin-bottom:12px;">点击标题展开/折叠详情。📄 = 文章页 | 📁 = 目录页</p>
'''

for fd in files_data:
    content = fd['content']
    fname = fd['filename']

    # Extract title from filename
    # Format: "01_通用智能体对比.md"
    parts = fname.replace('.md', '').split('_', 1)
    idx = parts[0]
    title = parts[1].replace('_', ' ') if len(parts) > 1 else fname

    # Determine page type from content
    is_directory = '*本页面为目录页*' in content
    icon = '📁' if is_directory else '📄'
    type_label = '目录页' if is_directory else '文章页'

    # Extract the body (remove the header metadata)
    body = content
    # Remove the leading "# Title" and metadata lines until "---"
    body_parts = body.split('---\n', 1)
    if len(body_parts) > 1:
        body = body_parts[1]
    # Remove trailing "---\n\n*编辑整理：Lillian*"
    body = re.sub(r'\n---\n\n\*编辑整理：Lillian\*$', '', body)

    # Remove leading/trailing whitespace
    body = body.strip()

    # Remove the directory note from display (we already show icon)
    body = body.replace('*本页面为目录页，列出该主题下的所有子文档。*\n\n', '')
    body = body.replace('*本页面为目录页，列出该主题下的所有子文档。*', '')

    # Generate a stable ID
    item_id = f'agent-{idx}'

    # Truncate preview (first 150 chars of body without HTML)
    preview_text = body[:200].replace('\n', ' ').strip()
    if len(body) > 200:
        preview_text += '...'

    section_html += f'''
                <div class="agent-item" style="margin-bottom:8px;border:1px solid var(--border);border-radius:8px;overflow:hidden;">
                    <div class="agent-header" onclick="toggleAgent('{item_id}')" style="display:flex;align-items:center;justify-content:space-between;padding:10px 16px;background:var(--bg);cursor:pointer;user-select:none;transition:background var(--transition);">
                        <div style="display:flex;align-items:center;gap:8px;flex:1;min-width:0;">
                            <span style="font-size:1.1rem;">{icon}</span>
                            <span style="font-weight:600;font-size:.92rem;white-space:nowrap;">{idx}. {title}</span>
                            <span style="font-size:.7rem;color:var(--text-secondary);background:var(--tag-bg);padding:2px 8px;border-radius:10px;">{type_label}</span>
                        </div>
                        <span class="agent-arrow" id="{item_id}-arrow" style="font-size:.8rem;transition:transform 0.2s;color:var(--text-secondary);">▼</span>
                    </div>
                    <div class="agent-body" id="{item_id}-body" style="display:none;padding:16px 20px;border-top:1px solid var(--border);font-size:.88rem;line-height:1.8;max-height:600px;overflow-y:auto;background:var(--surface);">
                        {md_to_html_simple(body)}
                        <p style="margin-top:20px;color:var(--text-secondary);font-size:.78rem;border-top:1px solid var(--border);padding-top:8px;">✏️ 编辑整理：Lillian | 来源：共研社AIGC知识库</p>
                    </div>
                </div>'''

section_html += '''
            </div>
        </section>
'''

# Read the current HTML
with open(HTML_PATH, 'r', encoding='utf-8') as f:
    html_content = f.read()

# Find and replace the AI智能体 section
# The section starts at: <section class="category" id="agents">
# And ends at: </section> followed by the next section (id="ai-painting")

old_start = html_content.find('<section class="category" id="agents">')
old_end = html_content.find('<section class="category" id="ai-painting">')

if old_start >= 0 and old_end >= 0:
    new_html = html_content[:old_start] + section_html + '\n' + html_content[old_end:]
    with open(HTML_PATH, 'w', encoding='utf-8') as f:
        f.write(new_html)
    print(f'Updated AI智能体 section in {HTML_PATH}')
    print(f'Old section: {old_end - old_start} chars -> New section: {len(section_html)} chars')
else:
    print(f'ERROR: Could not find markers. start={old_start}, end={old_end}')

# Also add the toggleAgent JavaScript function
js_to_add = '''
function toggleAgent(id) {
    const body = document.getElementById(id + '-body');
    const arrow = document.getElementById(id + '-arrow');
    if (body.style.display === 'none' || !body.style.display) {
        body.style.display = 'block';
        arrow.style.transform = 'rotate(180deg)';
    } else {
        body.style.display = 'none';
        arrow.style.transform = 'rotate(0deg)';
    }
}
'''
# Insert before the existing toggleTheme function
insert_pos = html_content.find('function toggleTheme()')
if insert_pos < 0:
    # Find in the updated content
    with open(HTML_PATH, 'r', encoding='utf-8') as f:
        updated = f.read()
    insert_pos = updated.find('function toggleTheme()')

if insert_pos > 0:
    with open(HTML_PATH, 'r', encoding='utf-8') as f:
        updated = f.read()
    updated = updated[:insert_pos] + js_to_add + '\n' + updated[insert_pos:]
    with open(HTML_PATH, 'w', encoding='utf-8') as f:
        f.write(updated)
    print('Added toggleAgent() JavaScript function')
else:
    print('WARNING: Could not find toggleTheme() to add toggleAgent()')

print('Done!')
