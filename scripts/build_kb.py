#!/usr/bin/env python3
"""Generate ai-knowledge-base.html from extracted Feishu Wiki data."""
import json, sys, os

OUTPUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ai-knowledge-base.html')

KB = {
    'title': 'Lillian的AIGC知识库',
    'subtitle': 'Lillian的AIGC知识库 — 超1000+AI文章教程、500+行业报告、300+变现案例',
    'owner': 'Lillian',
    'source_url': 'https://tauacgr5lqv.feishu.cn/wiki/PBcJwyfpfiBZirkAOlzcbQ0ynNh',
    'categories': [
        {
            'id': 'aigc-starter', 'icon': '🌟', 'title': 'AIGC新手入门教程',
            'desc': '从零开始学习AIGC，涵盖AI概念解析、百问百答、主流工具快速上手教程',
            'url': 'https://tauacgr5lqv.feishu.cn/wiki/TEfowFa0hi4ytikar4vc14Z9nwH',
            'sub_pages': [
                ('AI概念解析：从入门到精通的36个关键术语指南', '2025-10-09'),
                ('AIGC百问百答', '2025-09-29'), ('ChatGPT快速上手教程', '2025-09-29'),
                ('Midjourney快速上手教程', '2025-09-17'), ('Stable Diffusion快速上手教程', '2025-10-13'),
                ('AI数字与语音初阶段', '2025-10-28'), ('大厂AIGC实战案例', '2024-07-19'),
                ('AI工具集', '2025-09-09'), ('AIGC实用资料合集', '2025-09-10'),
                ('AI网站精选', '2025-09-09'), ('AI视频与播客', '2025-09-15'),
            ]
        },
        {
            'id': 'xiaohongshu', 'icon': '📕', 'title': '小红书热门资料精选',
            'desc': '小红书平台热门AI资料汇总，含教程文档、PDF、案例拆解、行业工作流等40+资料',
            'url': 'https://tauacgr5lqv.feishu.cn/wiki/QWm1wsGBsi1bSTkZUKOcftRBntO',
            'sub_pages': [
                ('DeepSeek V4 从零基础到精通学习手册', '2025'),
                ('Gemin3 pro从零基础到精通学习手册', '2025'),
                ('Nano Banana手册', '2025'), ('Claude Code从入门到精通-v2.0.0', '2025'),
                ('Manus 学习指南（持续更新）', '2025'), ('Manus内测码申请教程完整版', '2025'),
                ('AI自媒体：Deepseek公众号写作教程', '2025'),
                ('使用DeepSeek写小红书保姆级教程', '2025'),
                ('GPT-4o 风格提示词案例大全', '2025'), ('AI提示词合集', '2025'),
                ('DeepSeek处理Excel数据保姆级教程', '2025'), ('AI做古诗词绘本', '2025'),
                ('AI拆书稿提示词', '2025'), ('大厂AIGC实战案例', '2025'),
                ('AI玄学赛道指南', '2025'), ('豆包使用指南 / 豆包使用宝典', '2025'),
                ('全网最全Sora保姆级教程', '2025'), ('Coze搭建养生赛道智能体', '2025'),
                ('Coze扣子平台使用教程', '2025'), ('扣子空间的学习手册', '2025'),
                ('扣子空间MCP-最全实操案例提示词', '2025'),
                ('如何在ComfyUI从零开始搭建一套商业工作流', '2025'),
                ('AI一人公司行动指南', '2025'),
                ('H1~H6行业工作流批量出图（健康/宠物/美妆/金融/历史等）', '2025'),
                ('DeepSeek接入微信保姆级教程', '2025'), ('Word接入DeepSeek保姆级教程', '2025'),
                ('Kimi画20种流程图提示词', '2025'), ('艾文团队：GPT-4o更新同步', '2025'),
                ('《AI写小说从零基础到精通》学习手册', '2025'),
                ('《可灵从零基础到精通》学习手册', '2025'),
                ('【公众号】将KIMI接入微信公众号', '2025'),
                ('【变现】AI让老照片动起来', '2025'),
                ('【案例拆解】AI我中华工作流拆解与分析', '2025'),
                ('100个"去除AI味儿"的提示词', '2025'), ('行业分析大师-GPT+麦肯锡', '2025'),
                ('用GPT快速阅读100本书/天', '2025'),
                ('AI中文字体生成技巧(100+提示词案例)', '2025'),
                ('Ima知识库工具指南', '2025'), ('Coze扣子案例技术拆解-81套', '2025'),
                ('GPT-5全网最细指南（持续更新）', '2025'), ('AI音乐流派与风格关键词', '2025'),
            ]
        },
        {
            'id': 'prompts', 'icon': '💬', 'title': 'AI提示词',
            'desc': '提示词工程学习资料，含网站合集、官方指南、场景提示词、去AI味提示词等',
            'url': 'https://tauacgr5lqv.feishu.cn/wiki/BYUqwNVRQihCj4k36KOca9uPncA',
            'sub_pages': [
                ('AI提示词网站合集', '2025-02-11'), ('全网精选Prompt网站', '2025-08-22'),
                ('小白入门必看：提示词基础认识（初版）', '2025-09-09'),
                ('大模型官方提示词指南', '2025-02-11'), ('大模型提示词合集', '2025-02-11'),
                ('场景提示词合集', '2025-02-11'), ('Prompt其他资源合集', '2025-08-28'),
                ('去除AI味提示词合集', '2025-02-11'),
            ]
        },
        {
            'id': 'agents', 'icon': '🤖', 'title': 'AI智能体',
            'desc': 'Agent大趋势与各平台从零到精通：Coze、n8n、GPTs、Manus、Claude Code等20个工具',
            'url': 'https://tauacgr5lqv.feishu.cn/wiki/XdMvwRjw1iKlzukZzJAc6lJtnif',
            'sub_pages': [
                ('通用智能体对比', '2025-11-04'), ('基础概念学习指南', '2025-09-29'),
                ('理论知识学习指南', '2025-09-29'),
                ('Gemin3 pro从零基础到精通学习手册', '2026-03-27'),
                ('Coze从零基础到精通', '2025-09-18'), ('n8n从零基础到精通', '2025-09-29'),
                ('GPTs从零基础到精通', '2025-09-29'), ('Manus从零基础到精通', '2025-09-29'),
                ('flowith从零基础到精通', '2025-09-29'),
                ('Lovart.ai从零基础到精通', '2026-05-18'),
                ('Skywork 天工从零基础到精通', '2025-09-29'),
                ('MiniMax Agent从零基础到精通', '2025-09-29'),
                ('OpenClaw从零基础到精通', '2026-03-05'),
                ('Skills从零基础到精通', '2026-03-17'),
                ('Claude code', '2026-06-02'),
                ('WorkBuddy 从零基础到精通实操手册', '2026-06-11'),
                ('Obsidian从零基础到精通学习手册完整版', '2026-06-05'),
                ('Hermes Agent从零基础到精通', '2026-05-09'),
                ('Codex入门教程完整版', '2026-06-01'),
                ('Vibe Coding 从入门到精通学习手册', '2026-05-15'),
            ]
        },
        {
            'id': 'ai-painting', 'icon': '🎨', 'title': 'AI绘画',
            'desc': '主流AI绘画平台教程：Midjourney、Stable Diffusion、即梦、豆包、Nanobanana等',
            'url': 'https://tauacgr5lqv.feishu.cn/wiki/LM2Wwy3MziItSGkPkEncFZS4ne5',
            'sub_pages': [
                ('AI绘画从零到一', '2025-08-27'), ('AI绘画工具全景图对比', '2025-08-25'),
                ('AI绘画：指令合集', '2026-02-11'), ('工具教程：绘画Agent', '2025-08-29'),
                ('工具教程：其他绘画工具', '2025-08-29'), ('工具教程：Midjourney', '2025-08-29'),
                ('工具教程：Stable Diffusion教程', '2025-08-29'), ('工具教程：即梦', '2025-08-29'),
                ('工具教程：豆包', '2025-08-29'), ('工具教程：堆友', '2025-08-29'),
                ('工具教程：通义', '2025-08-29'), ('工具教程：OpenAI GPT', '2025-08-29'),
                ('工具教程：炼丹', '2025-08-28'), ('工具教程：Nanobanana', '2026-04-20'),
                ('工具教程：GPT-image2出图', '2026-04-24'), ('工具教程：Claude Design', '2026-04-23'),
                ('AI绘画：案例教程', '2025-08-28'), ('AI绘画：其他活动和教程', '2025-08-28'),
                ('AI绘画：辅助工具教程', '2025-08-28'), ('小码哥的 MJ 关键词实践', '2025-08-28'),
            ]
        },
        {
            'id': 'ai-video', 'icon': '🎬', 'title': 'AI视频',
            'desc': 'AI视频制作全流程：Sora2、可灵、即梦、剪映、Vidu、Runway、Pika、Google Veo等',
            'url': 'https://tauacgr5lqv.feishu.cn/wiki/IwUawwbnLifIfMkvVC0c2XGenjE',
            'sub_pages': [
                ('AI视频零基础启蒙：从0到1制作AI视频', '2025-08-28'),
                ('工具教程：Sora2', '2025-10-16'), ('工具教程：可灵', '2025-08-28'),
                ('工具教程：Dreamina即梦', '2025-08-26'), ('工具教程：剪映', '2025-08-28'),
                ('工具教程：Vidu', '2025-08-28'), ('工具教程：Seedance 2.0', '2026-02-11'),
                ('工具教程：MiniMax海螺AI', '2025-08-28'), ('工具教程：通义万相', '2025-08-27'),
                ('工具教程：Runway Gen-3', '2025-08-27'), ('工具教程：Midjourney', '2025-08-26'),
                ('工具教程：LuxReal', '2026-02-11'), ('工具教程：拍我AI（PixVerse国内版）', '2025-08-28'),
                ('工具教程：Pika', '2025-08-28'), ('工具教程：Google Veo', '2025-08-28'),
                ('AI视频运动镜头词测试', '2025-08-25'), ('AI视频运动镜头测试收集表', '2025-08-25'),
                ('Prompt Structures 提示结构', '2025-08-25'), ('可复制 Prompt', '2025-08-25'),
                ('《金刚大战哥斯拉》影片剧情分析', '2025-08-25'),
            ]
        },
        {
            'id': 'ai-writing', 'icon': '✍️', 'title': 'AI写作',
            'desc': 'AI写作工具与场景合集，含学术写作、小说创作、写作变现指南',
            'url': 'https://tauacgr5lqv.feishu.cn/wiki/EU0RwQdG9i8BIukVJmbc7jPWnUf',
            'sub_pages': [
                ('AI写作工具合集', '2025-08-28'), ('AI写小说零基础到精通', '2025-08-27'),
                ('AI写作场景合集', '2025-08-28'), ('AI学术写作提示词手册', '2025-08-28'),
                ('写作：AI 写作变现指南', '2025-08-22'),
                ('写作者和非写作者 | Paul Graham', '2025-08-23'),
                ('《救猫叔》互动式 AI 写作框架', '2025-08-25'),
            ]
        },
        {
            'id': 'ai-office', 'icon': '💼', 'title': 'AI办公',
            'desc': 'AI办公效率工具：飞书多维表格、AI PPT、AI Excel、NotebookLM、职场核心指令',
            'url': 'https://tauacgr5lqv.feishu.cn/wiki/CMHCwIkzEiLSBjkdmPDcn8UsnQ4',
            'sub_pages': [
                ('AI办公工具精选1', '2025-11-20'), ('AI办公工具精选2', '2025-11-20'),
                ('NotebookLM 资料汇总', '2026-05-29'), ('工具教程：飞书多维表格', '2025-11-13'),
                ('工具教程：AI PPT', '2025-12-16'), ('工具教程：AI EXCEL', '2025-12-16'),
                ('职场人必看的20个核心办公指令', '2025-12-16'),
                ('360AI浏览器学习手册', '2025-08-25'), ('AI+办公技能实操手册', '2025-12-16'),
            ]
        },
        {
            'id': 'ai-coding', 'icon': '💻', 'title': 'AI编程',
            'desc': 'AI编程工具精选：Claude Code、Trae、Cursor学习专区、GitHub专区、大屏开发实战',
            'url': 'https://tauacgr5lqv.feishu.cn/wiki/JMGqwL6sui7A4ckgmzscY0aKnXe',
            'sub_pages': [
                ('AI编程工具精选', '2025-08-25'), ('Claude code学习专区', '2025-10-08'),
                ('Trae学习专区', '2025-08-28'), ('Cursor学习专区', '2025-08-28'),
                ('精华：Github专区', '2025-08-28'),
                ('AI编程实战：Cursor+Claude4 完成大屏开发', '2025-08-25'),
            ]
        },
        {
            'id': 'ai-education', 'icon': '📚', 'title': 'AI教育',
            'desc': 'AI教育工具与教程：九章等教育平台使用指南',
            'url': 'https://tauacgr5lqv.feishu.cn/wiki/Z0x6wN5gui42iFkVJk2cz29XnUf',
            'sub_pages': [('工具教程：九章', '2025-08-25')]
        },
        {
            'id': 'ai-voice', 'icon': '🎤', 'title': 'AI声音',
            'desc': 'AI声音工具精选与声音克隆教程（Mockingbird等）',
            'url': 'https://tauacgr5lqv.feishu.cn/wiki/ELFGwDp71iH7b9kFx8cc2omCnUd',
            'sub_pages': [
                ('AI声音工具精选', '2025-08-25'), ('声音克隆教程-Mockingbird', '2025-08-25'),
            ]
        },
        {
            'id': 'ai-music', 'icon': '🎵', 'title': 'AI音乐',
            'desc': 'AI音乐创作工具：Suno、Eleven Music、UDIO及音乐提示词合集',
            'url': 'https://tauacgr5lqv.feishu.cn/wiki/Zttbwa0sPi88JDktbibcVzP3nOb',
            'sub_pages': [
                ('工具教程：Suno', '2025-08-28'), ('工具教程：Eleven Music', '2025-08-28'),
                ('工具教程：UDIO', '2025-08-27'), ('AI音乐提示词合集', '2025-08-28'),
            ]
        },
        {
            'id': 'digital-human', 'icon': '👤', 'title': 'AI数字人',
            'desc': '数字人基础、开源项目、HeyGem部署、DUIX交互、形象定制与直播避坑',
            'url': 'https://tauacgr5lqv.feishu.cn/wiki/PkVhwI0l4iB9Txkhz8fc0ISQnWf',
            'sub_pages': [
                ('AI数字人基础认识', '2025-08-25'), ('HeyGem开源数字人部署教程', '2025-08-26'),
                ('DUIX交互平台使用教程', '2025-08-26'), ('如何定制形象', '2025-08-28'),
                ('AI数字人直播避坑手册', '2025-08-25'), ('AI数字人开源项目大全', '2025-08-25'),
                ('最强数字人InfiniteTalk介绍', '2025-08-25'),
            ]
        },
        {
            'id': 'ai-reports', 'icon': '📊', 'title': 'AI研究报告',
            'desc': '行业研究报告精选：OpenAI Agents最佳实践、全球AI创造力报告、AI Coding报告等',
            'url': 'https://tauacgr5lqv.feishu.cn/wiki/OhEmw69D8iQp1fkxX3jc4Cjznne',
            'sub_pages': [
                ('OpenAI 最新报告：构建 Agents 最佳实践', '2025-09-04'),
                ('《智变》白皮书：AI赋能政府与央国企', '2025-09-04'),
                ('2025全球AI创造力发展报告', '2025-09-04'),
                ('AI Coding非共识报告丨AI透镜系列研究', '2025-09-04'),
                ('我们时代的"AI焦虑"，该如何破局？', '2025-09-04'),
                ('AI相关报告合集', '2025-09-05'),
            ]
        },
    ],
    'extra_section': {
        'icon': '💻', 'title': '《一人公司》行动指南知识库',
        'desc': '面向个人创业者的AI行动指南，涵盖独立开发、一人企业运营、AI工具赋能等主题',
        'url': 'https://tauacgr5lqv.feishu.cn/wiki/SooewcUNoi3OnIkQyQ0c6oiInde',
    },
    'academic_sections': [
        {
            'icon': '🎓', 'title': 'LL学姐高校论文资料库分享',
            'desc': 'LL学姐高校论文资料库分享（持续更新中）',
            'url': 'https://ecnq7dxx97wc.feishu.cn/wiki/RwOswzaPQiq8kwkDl8OcytuQn3f',
        },
        {
            'icon': '📝', 'title': '硕博论文交流干货分享——飞书版',
            'desc': '硕博论文交流干货分享，飞书版',
            'url': 'https://ecnq7dxx97wc.feishu.cn/wiki/W38gwIqJPiRXxYkhjk7cR4rQnRd',
        },
        {
            'icon': '📖', 'title': '『Ai』论文博客——用人文视角解读',
            'desc': '用人文视角解读AI与论文写作',
            'url': '',
        },
    ]
}

def build_html():
    cats_html = []
    nav_html = []
    for i, cat in enumerate(KB['categories']):
        cid = cat['id']
        sub_items = '\n'.join(
            f'<li><a href="{cat["url"]}" target="_blank" rel="noopener" title="在飞书中打开">{name}</a><span class="date">{date}</span></li>'
            for name, date in cat['sub_pages']
        )
        nav_html.append(f'<li><a href="#{cid}">{cat["icon"]} {cat["title"]}<span class="count">{len(cat["sub_pages"])}</span></a></li>')
        cats_html.append(f'''
        <section class="category" id="{cid}">
            <div class="cat-header">
                <h2>{cat["icon"]} {cat["title"]}</h2>
                <a class="feishu-link" href="{cat["url"]}" target="_blank" rel="noopener">在飞书中打开 &#8599;</a>
            </div>
            <p class="cat-desc">{cat["desc"]}</p>
            <div class="sub-pages">
                <h3>子文档列表 ({len(cat["sub_pages"])})</h3>
                <ul class="doc-list">{sub_items}</ul>
            </div>
        </section>''')

    extra = KB['extra_section']
    extra_html = f'''
        <section class="category extra-section" id="one-person-company">
            <div class="cat-header">
                <h2>{extra["icon"]} {extra["title"]}</h2>
                <a class="feishu-link" href="{extra["url"]}" target="_blank" rel="noopener">在飞书中打开 &#8599;</a>
            </div>
            <p class="cat-desc">{extra["desc"]}</p>
        </section>'''

    academic_nav = []
    academic_body = []
    for ai, ac in enumerate(KB['academic_sections']):
        aid = f"academic-{ai}"
        academic_nav.append(f'<li><a href="#{aid}">{ac["icon"]} {ac["title"]}</a></li>')
        url_html = f'<a class="feishu-link" href="{ac["url"]}" target="_blank" rel="noopener">在飞书中打开 &#8599;</a>' if ac["url"] else ''
        academic_body.append(f'''
        <section class="category academic-section" id="{aid}">
            <div class="cat-header">
                <h2>{ac["icon"]} {ac["title"]}</h2>
                {url_html}
            </div>
            <p class="cat-desc">{ac["desc"]}</p>
        </section>''')
    academic_nav_html = '\n'.join(academic_nav)
    academic_body_html = '\n'.join(academic_body)

    total_docs = sum(len(c['sub_pages']) for c in KB['categories'])

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{KB["title"]} — AI 知识库</title>
<style>
:root {{
    --bg: #f8f9fa; --surface: #fff; --text: #1a1a2e; --text-secondary: #555;
    --primary: #4f46e5; --primary-light: #eef2ff; --border: #e2e8f0;
    --accent: #f59e0b; --shadow: 0 1px 3px rgba(0,0,0,.08);
    --sidebar-bg: #1e1b4b; --sidebar-text: #e0e0f0; --sidebar-hover: #312e81;
    --sidebar-active: #4f46e5; --tag-bg: #f0f0ff; --tag-text: #4f46e5;
    --radius: 10px; --transition: 0.2s ease;
}}
[data-theme="dark"] {{
    --bg: #0f172a; --surface: #1e293b; --text: #e2e8f0; --text-secondary: #94a3b8;
    --primary: #818cf8; --primary-light: #1e1b4b; --border: #334155;
    --shadow: 0 1px 3px rgba(0,0,0,.3); --sidebar-bg: #0c0a2e;
    --sidebar-text: #c7d2fe; --sidebar-hover: #1e1b4b; --tag-bg: #1e1b4b;
    --tag-text: #a5b4fc;
}}
* {{ box-sizing:border-box; margin:0; padding:0; }}
html {{ scroll-behavior:smooth; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif; background:var(--bg); color:var(--text); line-height:1.6; display:flex; min-height:100vh; }}
a {{ color:var(--primary); text-decoration:none; }}
a:hover {{ text-decoration:underline; }}

/* Sidebar */
.sidebar {{
    width:280px; min-width:280px; background:var(--sidebar-bg); color:var(--sidebar-text);
    position:fixed; top:0; left:0; bottom:0; z-index:100; display:flex; flex-direction:column;
    transition: transform var(--transition); overflow-y:auto;
}}
.sidebar-header {{ padding:24px 20px 16px; border-bottom:1px solid rgba(255,255,255,.1); }}
.sidebar-header h1 {{ font-size:1.1rem; color:#fff; line-height:1.4; }}
.sidebar-header .subtitle {{ font-size:.75rem; color:rgba(255,255,255,.5); margin-top:4px; }}
.sidebar-nav {{ flex:1; padding:12px 0; overflow-y:auto; }}
.sidebar-nav ul {{ list-style:none; }}
.sidebar-nav li a {{
    display:flex; align-items:center; gap:8px; padding:8px 20px; font-size:.88rem;
    color:var(--sidebar-text); transition:background var(--transition); border-left:3px solid transparent;
}}
.sidebar-nav li a:hover {{ background:var(--sidebar-hover); text-decoration:none; border-left-color:var(--primary); }}
.sidebar-nav li a .count {{
    margin-left:auto; background:rgba(255,255,255,.15); color:rgba(255,255,255,.7);
    font-size:.7rem; padding:2px 7px; border-radius:10px; min-width:22px; text-align:center;
}}
.sidebar-footer {{ padding:12px 20px; border-top:1px solid rgba(255,255,255,.1); font-size:.72rem; color:rgba(255,255,255,.4); }}

/* Main */
.main {{ margin-left:280px; flex:1; padding:32px 40px; max-width:1000px; }}
.hero {{ margin-bottom:36px; }}
.hero h1 {{ font-size:2rem; font-weight:800; color:var(--text); }}
.hero .meta {{ color:var(--text-secondary); font-size:.88rem; margin-top:6px; }}
.hero .stats {{ display:flex; gap:16px; margin-top:12px; flex-wrap:wrap; }}
.hero .stat {{ background:var(--primary-light); color:var(--primary); padding:6px 14px; border-radius:20px; font-size:.82rem; font-weight:600; }}

/* Search & Controls */
.controls {{ display:flex; gap:12px; margin-bottom:28px; flex-wrap:wrap; align-items:center; }}
.search-box {{
    flex:1; min-width:200px; padding:10px 16px; border:2px solid var(--border);
    border-radius:var(--radius); font-size:.9rem; background:var(--surface); color:var(--text);
    transition:border-color var(--transition); outline:none;
}}
.search-box:focus {{ border-color:var(--primary); }}
.btn {{
    padding:10px 18px; border:none; border-radius:var(--radius); cursor:pointer;
    font-size:.85rem; font-weight:600; transition:all var(--transition);
    background:var(--surface); color:var(--text); border:2px solid var(--border);
}}
.btn:hover {{ border-color:var(--primary); color:var(--primary); }}
.btn-icon {{ font-size:1.1rem; }}

/* Category cards */
.category {{
    background:var(--surface); border-radius:var(--radius); padding:24px 28px;
    margin-bottom:20px; box-shadow:var(--shadow); border:1px solid var(--border);
    transition: box-shadow var(--transition);
}}
.category:hover {{ box-shadow: 0 4px 12px rgba(0,0,0,.1); }}
.category:target {{ border-color:var(--primary); box-shadow:0 0 0 3px var(--primary-light); }}
.cat-header {{ display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:8px; margin-bottom:8px; }}
.cat-header h2 {{ font-size:1.25rem; font-weight:700; }}
.cat-desc {{ color:var(--text-secondary); font-size:.9rem; margin-bottom:16px; }}
.feishu-link {{ font-size:.8rem; padding:4px 10px; border-radius:6px; background:var(--primary-light); color:var(--primary); white-space:nowrap; }}
.feishu-link:hover {{ text-decoration:none; opacity:.8; }}
.sub-pages h3 {{ font-size:.8rem; text-transform:uppercase; letter-spacing:.05em; color:var(--text-secondary); margin-bottom:8px; }}
.doc-list {{ list-style:none; display:grid; grid-template-columns:repeat(auto-fill, minmax(280px, 1fr)); gap:6px; }}
.doc-list li {{
    display:flex; align-items:center; justify-content:space-between; padding:6px 12px;
    border-radius:6px; background:var(--bg); font-size:.88rem; transition:background var(--transition);
}}
.doc-list li:hover {{ background:var(--primary-light); }}
.doc-list .date {{ font-size:.72rem; color:var(--text-secondary); white-space:nowrap; margin-left:8px; }}

/* Extra section */
.extra-section {{ border:2px dashed var(--primary); background:var(--primary-light); }}

/* Back to top */
.back-top {{
    position:fixed; bottom:24px; right:24px; width:44px; height:44px; border-radius:50%;
    background:var(--primary); color:#fff; border:none; cursor:pointer; font-size:1.2rem;
    box-shadow:0 2px 8px rgba(0,0,0,.2); display:none; align-items:center; justify-content:center;
    z-index:200; transition:opacity var(--transition);
}}

/* Mobile */
@media (max-width:768px) {{
    .sidebar {{ transform:translateX(-100%); }}
    .sidebar.open {{ transform:translateX(0); }}
    .main {{ margin-left:0; padding:20px 16px; }}
    .doc-list {{ grid-template-columns:1fr; }}
    .hero h1 {{ font-size:1.4rem; }}
}}
.menu-toggle {{
    display:none; position:fixed; top:12px; left:12px; z-index:300; width:40px; height:40px;
    border-radius:50%; background:var(--primary); color:#fff; border:none; font-size:1.2rem;
    cursor:pointer; box-shadow:0 2px 8px rgba(0,0,0,.3);
}}
@media (max-width:768px) {{ .menu-toggle {{ display:flex; align-items:center; justify-content:center; }} }}

/* Print */
@media print {{
    .sidebar,.controls,.back-top,.menu-toggle {{ display:none; }}
    .main {{ margin-left:0; }}
    .category {{ break-inside:avoid; box-shadow:none; border:1px solid #ddd; }}
}}

.hidden {{ display:none !important; }}
.no-results {{ text-align:center; padding:40px; color:var(--text-secondary); }}
</style>
</head>
<body>

<button class="menu-toggle" onclick="toggleSidebar()" aria-label="菜单">☰</button>

<aside class="sidebar" id="sidebar">
    <div class="sidebar-header">
        <h1>{KB["title"]}</h1>
        <div class="subtitle">{KB["owner"]} · 持续更新中</div>
    </div>
    <nav class="sidebar-nav">
        <ul>
            {''.join(nav_html)}
            <li style="margin-top:8px;border-top:1px solid rgba(255,255,255,.1);padding-top:8px;">
                <a href="#one-person-company">{extra["icon"]} {extra["title"]}</a>
            </li>
            <li style="margin-top:4px;border-top:1px solid rgba(255,255,255,.1);padding-top:8px;">
                <span style="padding:4px 20px;font-size:.7rem;color:rgba(255,255,255,.4);text-transform:uppercase;letter-spacing:.05em;">论文写作资源</span>
            </li>
            {academic_nav_html}
        </ul>
    </nav>
    <div class="sidebar-footer">
        数据来源：飞书 · Lillian的AIGC知识库<br>
        生成时间：2026-06-15
    </div>
</aside>

<main class="main" id="main">
    <div class="hero">
        <h1>{KB["title"]}</h1>
        <p class="meta">{KB["subtitle"]}</p>
        <div class="stats">
            <span class="stat">📁 {len(KB["categories"])} 个分类</span>
            <span class="stat">📄 {total_docs} 篇文档</span>
            <span class="stat">👤 {KB["owner"]}</span>
            <a href="{KB["source_url"]}" target="_blank" rel="noopener" class="stat" style="text-decoration:none">🔗 飞书原文</a>
        </div>
    </div>

    <div class="controls">
        <input type="text" class="search-box" id="search" placeholder="搜索文档标题..." oninput="doSearch()">
        <button class="btn" onclick="toggleTheme()" title="切换深色/浅色模式">🌓 主题</button>
        <button class="btn" onclick="expandAll()">展开全部</button>
        <button class="btn" onclick="collapseAll()">折叠全部</button>
    </div>

    <div id="no-results" class="no-results hidden">
        <p>没有找到匹配的文档。试试其他关键词？</p>
    </div>

    {''.join(cats_html)}
    {extra_html}
    {academic_body_html}
</main>

<button class="back-top" id="backTop" onclick="window.scrollTo({{top:0,behavior:'smooth'}})">↑</button>

<script>
const sidebar = document.getElementById('sidebar');
const backTop = document.getElementById('backTop');

function toggleSidebar() {{ sidebar.classList.toggle('open'); }}

// Close sidebar on nav click (mobile)
sidebar.querySelectorAll('a').forEach(a => {{
    a.addEventListener('click', () => {{ if(window.innerWidth <= 768) sidebar.classList.remove('open'); }});
}});

// Theme toggle
(function() {{
    const saved = localStorage.getItem('kb-theme');
    if(saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme:dark)').matches)) {{
        document.documentElement.setAttribute('data-theme','dark');
    }}
}})();
function toggleTheme() {{
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('kb-theme', next);
}}

// Back to top
window.addEventListener('scroll', () => {{
    backTop.style.display = window.scrollY > 400 ? 'flex' : 'none';
}});

// Search
function doSearch() {{
    const q = document.getElementById('search').value.toLowerCase().trim();
    const cats = document.querySelectorAll('.category');
    const noResults = document.getElementById('no-results');
    let foundAny = false;
    cats.forEach(cat => {{
        const items = cat.querySelectorAll('.doc-list li');
        let catVisible = false;
        items.forEach(li => {{
            const text = li.textContent.toLowerCase();
            if(!q || text.includes(q)) {{ li.classList.remove('hidden'); catVisible = true; }}
            else {{ li.classList.add('hidden'); }}
        }});
        if(q && !catVisible) {{ cat.classList.add('hidden'); }}
        else {{ cat.classList.remove('hidden'); foundAny = true; }}
    }});
    noResults.classList.toggle('hidden', !q || foundAny);
}}

function expandAll() {{ document.querySelectorAll('.category').forEach(c => c.classList.remove('hidden')); document.querySelectorAll('.doc-list li').forEach(li => li.classList.remove('hidden')); document.getElementById('no-results').classList.add('hidden'); document.getElementById('search').value = ''; }}
function collapseAll() {{ document.querySelectorAll('.doc-list li').forEach(li => li.classList.add('hidden')); }}
</script>
</body>
</html>'''
    return html


if __name__ == '__main__':
    html = build_html()
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'Generated: {OUTPUT}')
    print(f'Size: {len(html):,} bytes')
    print(f'Categories: {len(KB["categories"])}')
    total = sum(len(c['sub_pages']) for c in KB['categories'])
    print(f'Total documents: {total}')
