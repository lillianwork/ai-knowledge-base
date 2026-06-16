"""Step 4c: Clean extracted content — strip chrome, format, add attribution."""
import sys, os, json, re

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'extracted', 'agents')
CLEAN_DIR = os.path.join(OUT_DIR, 'clean_v2')
FINAL_DIR = os.path.join(OUT_DIR, 'final')
os.makedirs(FINAL_DIR, exist_ok=True)

with open(os.path.join(OUT_DIR, 'token_map.json'), 'r', encoding='utf-8') as f:
    token_map = json.load(f)

def clean_content(text):
    """Clean extracted content by removing chrome elements."""
    if not text:
        return ''

    lines = text.split('\n')
    cleaned = []
    skip_markers = [
        '评论（0）', '你可能还想问', '反向引用', '本文引用', '关系图',
        '推荐内容由 AI 生成', '本文暂未被其它文档引用',
        '真诚点赞，手留余香', '内容由 AI 生成',
        '正在生成 AI 速览...', 'AI 速览', '试用',
        '上传日志', '联系客服',
    ]

    for line in lines:
        stripped = line.strip()
        # Skip empty lines
        if not stripped:
            cleaned.append('')
            continue
        # Skip chrome markers
        if any(m in stripped for m in skip_markers):
            continue
        # Skip lines that are just zero-width characters
        if stripped.replace('​', '').replace('‌', '').replace('‍', '').replace('⁠', '').replace('﻿', '').strip() == '':
            continue
        # Skip pure unicode tag lines (the invisible chars in page titles)
        clean_line = re.sub(r'[​‌‍⁠﻿‬‭‮]', '', stripped)
        # Also remove the "‍⁡​" style invisible chars
        clean_line = re.sub(r'[ -‏ -  -⁯﻿\xad؜᠎]', '', clean_line)
        if not clean_line.strip():
            continue
        cleaned.append(stripped)

    # Collapse 3+ consecutive empty lines into 2
    result = []
    empty_count = 0
    for line in cleaned:
        if line == '':
            empty_count += 1
            if empty_count <= 2:
                result.append(line)
        else:
            empty_count = 0
            result.append(line)

    return '\n'.join(result).strip()

def extract_author_info(text):
    """Try to extract original author from page metadata."""
    # Common patterns in Feishu wiki metadata
    # Look for names near modification dates
    lines = text.split('\n') if text else []
    for line in lines:
        stripped = line.strip()
        # Skip empty lines
        if not stripped:
            continue
        # Look for lines with "修改" (modification)
        if '修改' in stripped and len(stripped) < 30:
            # This is a modification line, the author is usually above it
            continue

    # Default: the original knowledge base
    return '共研社AIGC知识库（原作者：林艾文Ivan 等）'

# Process each file
final_files = []

for idx, (token, info) in enumerate(token_map.items()):
    title = info['title']
    clean_file = os.path.join(CLEAN_DIR, f'{idx+1:02d}_{token}.txt')

    if not os.path.exists(clean_file):
        print(f'  SKIP [{idx+1}] {title} — file not found')
        continue

    with open(clean_file, 'r', encoding='utf-8') as f:
        raw = f.read()

    # Parse the header
    header = {}
    content_start = 0
    lines = raw.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('====='):
            content_start = i + 1
            break
        if ':' in line:
            key, _, val = line.partition(':')
            header[key.strip()] = val.strip()

    body_text = '\n'.join(lines[content_start:]) if content_start < len(lines) else ''

    # Clean the body
    cleaned_body = clean_content(body_text)
    page_type = header.get('PAGE_TYPE', 'article')

    # Extract author
    author = extract_author_info(cleaned_body)

    # Build final markdown
    final_md = f'# {title}\n\n'
    final_md += f'> 原作者：{author}\n\n'
    final_md += f'> 来源：[共研社AIGC知识库]({info["url"]})\n\n'
    final_md += f'---\n\n'

    if page_type == 'directory':
        final_md += f'*本页面为目录页，列出该主题下的所有子文档。*\n\n'
    final_md += cleaned_body
    final_md += f'\n\n---\n\n'
    final_md += f'*编辑整理：李良艳*\n'

    # Save
    safe_title = title.replace('/', '_').replace(' ', '_').replace(':', '').replace('：', '')
    final_path = os.path.join(FINAL_DIR, f'{idx+1:02d}_{safe_title}.md')
    with open(final_path, 'w', encoding='utf-8') as f:
        f.write(final_md)

    char_count = len(cleaned_body)
    print(f'  [{idx+1:2d}] [{page_type:9s}] {char_count:5d} chars | {title}')
    final_files.append({
        'idx': idx + 1,
        'title': title,
        'type': page_type,
        'chars': char_count,
        'file': final_path
    })

# Save index
index_md = '# AI智能体 — 知识库目录\n\n'
index_md += '> 来源：共研社AIGC知识库 | 整理：李良艳\n\n'
index_md += '---\n\n'

for f in final_files:
    t = '📁' if f['type'] == 'directory' else '📄'
    index_md += f'- {t} [{f["idx"]:02d}. {f["title"]}]({os.path.basename(f["file"])}) ({f["chars"]} 字)\n'

index_path = os.path.join(FINAL_DIR, '00_目录_AI智能体.md')
with open(index_path, 'w', encoding='utf-8') as f:
    f.write(index_md)

print(f'\n===== DONE =====')
print(f'Processed {len(final_files)} files')
print(f'Articles: {sum(1 for f in final_files if f["type"] == "article")}')
print(f'Directories: {sum(1 for f in final_files if f["type"] == "directory")}')
print(f'Output: {FINAL_DIR}')
