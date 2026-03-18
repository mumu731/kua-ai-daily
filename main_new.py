# -*- coding: utf-8 -*-
"""
🍑桃子日报生成器
从JSON文章数据生成分类日报和RSS订阅
"""
import argparse
import html
import os
import re
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

import markdown
import yaml
from feedgen.ext.base import BaseExtension
from feedgen.feed import FeedGenerator
from lxml import html as lxml_html
from lxml import etree as lxml_etree
from lxml.etree import tostring

from fetcher import load_all_articles, get_articles_by_date, ensure_dirs, DATA_DIR
from classifier import classify_articles, get_category_info, CATEGORY_RULES

# 配置
PRIMARY_FEED_FILENAME = "rss.xml"
FEED_ICON_PATH = "static/icon.png"
FEED_ICON_SIZE = 144
RSS_SUMMARY_MAX_CHARS = 360
WEBFEEDS_NS = "http://webfeeds.org/rss/1.0"

BACKUP_DIR = "BACKUP"
ANCHOR_NUMBER = 5

# 日报模板
MD_HEAD = """# 🍑桃子日报

> 本仓库自动抓取跨境电商行业资讯，每日生成早报。内容来源于 Digital Commerce 360 和 Cross-Border Magazine。

正式订阅地址：https://mumu731.github.io/kua-ai-daily/rss.xml

## Links

| Platform | Link |
| :--- | :--- |
| RSS Feed | [Subscribe]({feed_subscribe_url}) |
| Markdown 备份 | [BACKUP](https://github.com/{repo_name}/tree/{branch_name}/BACKUP) |
| GitHub Pages | [View](https://mumu731.github.io/kua-ai-daily/) |

---

"""


def format_time(time_str: str) -> str:
    """格式化时间字符串"""
    try:
        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d")
    except:
        return time_str[:10] if len(time_str) >= 10 else time_str


def html_to_plain_text(html_content: str) -> str:
    """将HTML转换为纯文本"""
    try:
        tree = lxml_html.fromstring(html_content)
        text = tree.text_content()
        return re.sub(r'\s+', ' ', text).strip()
    except:
        return html_content


def _valid_xml_char_ordinal(c):
    """检查XML有效字符"""
    codepoint = ord(c)
    return (
        0x20 <= codepoint <= 0xD7FF
        or codepoint in (0x9, 0xA, 0xD)
        or 0xE000 <= codepoint <= 0xFFFD
        or 0x10000 <= codepoint <= 0x10FFFF
    )


def make_rss_summary(content: str, max_chars: int = RSS_SUMMARY_MAX_CHARS) -> str:
    """生成RSS摘要"""
    summary = html_to_plain_text(content)
    summary = ''.join(c for c in summary if _valid_xml_char_ordinal(c))
    if len(summary) > max_chars:
        summary = summary[:max_chars].rsplit(' ', 1)[0] + '...'
    return summary


def generate_daily_markdown(date_str: str, articles: List[Dict[str, Any]], repo_name: str = "user/repo") -> str:
    """生成单日早报Markdown内容"""
    # 分类文章
    categorized = classify_articles(articles)
    
    md_content = f"# [{date_str}](https://github.com/{repo_name}/blob/master/BACKUP/{date_str}.md)\n\n"
    md_content += f"## 🍑 桃子日报 {date_str}\n\n"
    md_content += f"**共收录 {len(articles)} 篇文章**\n\n"
    
    # 概览 - 按分类统计
    md_content += "### 📊 今日概览\n\n"
    md_content += "| 分类 | 数量 |\n"
    md_content += "|------|------|\n"
    
    for cat_key, cat_articles in categorized.items():
        if cat_articles and cat_key != "other":
            cat_info = get_category_info(cat_key)
            md_content += f"| {cat_info['icon']} {cat_info['name']} | {len(cat_articles)} |\n"
    
    md_content += "\n---\n\n"
    
    # 详细内容 - 按分类展示
    for cat_key, cat_articles in categorized.items():
        if not cat_articles or cat_key == "other":
            continue
        
        cat_info = get_category_info(cat_key)
        md_content += f"## {cat_info['icon']} {cat_info['name']}\n\n"
        
        for article in cat_articles:
            title = article.get("title_zh") or article.get("title", "")
            summary = article.get("summary_zh") or article.get("summary", "")
            link = article.get("link", "")
            source = article.get("source", "")
            
            md_content += f"### [{title}]({link})\n\n"
            md_content += f"> 来源: {source}\n\n"
            
            # 清理摘要中的HTML标签
            summary_clean = html_to_plain_text(summary)
            if summary_clean:
                md_content += f"{summary_clean[:300]}"
                if len(summary_clean) > 300:
                    md_content += "..."
                md_content += "\n\n"
            
            md_content += f"[阅读原文]({link})\n\n"
            md_content += "---\n\n"
    
    return md_content


def save_daily_markdown(date_str: str, content: str, dir_name: str = BACKUP_DIR):
    """保存日报Markdown文件"""
    os.makedirs(dir_name, exist_ok=True)
    
    # 查找下一个编号
    existing_files = [f for f in os.listdir(dir_name) if f.endswith('.md') and '_' in f]
    max_num = 0
    for f in existing_files:
        try:
            num = int(f.split('_')[0])
            max_num = max(max_num, num)
        except:
            pass
    
    filename = f"{max_num + 1}_{date_str}.md"
    filepath = os.path.join(dir_name, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"已保存日报: {filepath}")
    return filepath


def generate_rss_feed(repo_name: str, feed_filename: str, articles: List[Dict[str, Any]]):
    """生成RSS订阅文件"""
    generator = FeedGenerator()
    generator.language("zh-CN")
    generator.id(f"https://github.com/{repo_name}")
    generator.title("🍑桃子日报")
    generator.description("每日自动抓取跨境电商行业资讯，包括平台动态、市场趋势、跨境物流等")
    generator.author({"name": "CrossBorder Daily", "email": "crossborder@example.com"})
    generator.link(href=f"https://github.com/{repo_name}", rel="alternate")
    generator.link(href=f"https://mumu731.github.io/kua-ai-daily/{feed_filename}", rel="self")
    
    # 设置图标
    feed_icon_url = f"https://mumu731.github.io/kua-ai-daily/{FEED_ICON_PATH}"
    if os.path.exists(FEED_ICON_PATH):
        generator.logo(feed_icon_url)
    
    # 添加文章到RSS
    recent_articles = articles[:30]  # 最近30篇
    
    for article in recent_articles:
        title = article.get("title_zh") or article.get("title", "")
        link = article.get("link", "")
        summary = article.get("summary_zh") or article.get("summary", "")
        pub_date = article.get("published", "")
        
        entry = generator.add_entry()
        entry.id(link)
        entry.title(title)
        entry.link(href=link)
        entry.description(make_rss_summary(summary))
        
        try:
            dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
            entry.published(dt)
        except:
            entry.published(datetime.now(timezone.utc))
    
    # 保存RSS文件
    generator.rss_file(feed_filename, pretty=True)
    print(f"已生成RSS: {feed_filename}")


def generate_zola_content(date_str: str, md_content: str):
    """生成 Zola 兼容的 content/posts/*.md 文件（带 TOML front matter）"""
    posts_dir = os.path.join("content", "posts")
    os.makedirs(posts_dir, exist_ok=True)

    front_matter = f"""+++
title = "🍑桃子日报 {date_str}"
date = {date_str}T08:00:00+08:00
description = "跨境电商每日资讯 {date_str}"

[taxonomies]
categories = ["日报"]
tags = ["跨境电商", "日报"]
+++

"""
    # 去掉原 md_content 的第一行标题（avoid duplication with front matter title）
    lines = md_content.split("\n")
    body = "\n".join(lines[1:]).lstrip("\n")

    filepath = os.path.join(posts_dir, f"{date_str}.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(front_matter + body)

    print(f"已生成 Zola 内容: {filepath}")


def generate_readme(articles: List[Dict[str, Any]], repo_name: str, branch_name: str = "master"):
    """生成README.md"""
    feed_url = f"https://mumu731.github.io/kua-ai-daily/{PRIMARY_FEED_FILENAME}"
    
    content = MD_HEAD.format(
        feed_subscribe_url=feed_url,
        repo_name=repo_name,
        branch_name=branch_name,
    )
    
    # 最近更新列表
    content += "## 最近更新\n\n"
    recent_articles = articles[:ANCHOR_NUMBER]
    
    for article in recent_articles:
        title = article.get("title_zh") or article.get("title", "")
        link = article.get("link", "")
        date = format_time(article.get("published", ""))
        content += f"- [{title}]({link}) -- {date}\n"
    
    content += "\n---\n\n## License\n\n"
    content += "- 代码: MIT\n"
    content += "- 文章内容: 来源于公开RSS，版权归原作者所有\n"
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)
    
    print("已生成README.md")


def main(repo_name: str = "user/repo", date_str: str = None):
    """主函数"""
    ensure_dirs()
    
    # 如果没有指定日期，使用今天
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    print(f"=== 生成🍑桃子日报: {date_str} ===\n")
    
    # 1. 加载文章
    print("加载文章数据...")
    all_articles = load_all_articles()
    print(f"  共 {len(all_articles)} 篇文章\n")
    
    # 2. 获取指定日期的文章
    daily_articles = get_articles_by_date(date_str)
    if not daily_articles:
        print(f"警告: {date_str} 没有文章，使用最近的文章")
        # 获取最近7天的文章
        cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        daily_articles = [a for a in all_articles if a.get("published_date", "") >= cutoff][:20]
    
    print(f"  今日文章: {len(daily_articles)} 篇\n")
    
    # 3. 生成日报Markdown
    print("生成日报...")
    md_content = generate_daily_markdown(date_str, daily_articles, repo_name)
    save_daily_markdown(date_str, md_content)
    generate_zola_content(date_str, md_content)
    
    # 4. 生成RSS
    print("\n生成RSS订阅...")
    generate_rss_feed(repo_name, PRIMARY_FEED_FILENAME, all_articles)
    
    # 5. 生成README
    print("\n生成README...")
    generate_readme(all_articles, repo_name)
    
    print("\n=== 完成! ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="🍑桃子日报生成器")
    parser.add_argument("--repo", default="user/repo", help="GitHub仓库名 (格式: user/repo)")
    parser.add_argument("--date", help="指定日期 (格式: YYYY-MM-DD)")
    
    args = parser.parse_args()
    main(repo_name=args.repo, date_str=args.date)