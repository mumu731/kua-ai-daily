# -*- coding: utf-8 -*-
"""
RSS抓取模块 - 从跨境电商数据源抓取文章
"""
import hashlib
import json
import os
from datetime import datetime
from typing import List, Dict, Any

import feedparser
import yaml

from translator import translate_article

# RSS源配置
FEED_SOURCES = [
    {
        "name": "Digital Commerce 360",
        "url": "https://www.digitalcommerce360.com/topic/cross-border-ecommerce/feed/",
        "category": "market",
        "language": "en",
    },
    {
        "name": "Cross-Border Magazine",
        "url": "https://cross-border-magazine.com/feed/",
        "category": "logistics",
        "language": "en",
    },
]

# 数据存储路径
DATA_DIR = "data"
ARTICLES_DIR = os.path.join(DATA_DIR, "articles")
DAILY_DIR = os.path.join(DATA_DIR, "daily")


def ensure_dirs():
    """确保数据目录存在"""
    os.makedirs(ARTICLES_DIR, exist_ok=True)
    os.makedirs(DAILY_DIR, exist_ok=True)


def generate_article_id(url: str) -> str:
    """根据URL生成文章唯一ID"""
    return hashlib.md5(url.encode()).hexdigest()[:12]


def parse_date(entry: Dict) -> datetime:
    """解析文章发布时间"""
    # 尝试不同的日期字段
    date_fields = ["published_parsed", "updated_parsed", "created_parsed"]
    for field in date_fields:
        if field in entry:
            struct_time = entry[field]
            return datetime(*struct_time[:6])
    return datetime.now()


def fetch_feed(source: Dict[str, Any]) -> List[Dict[str, Any]]:
    """抓取单个RSS源"""
    print(f"正在抓取: {source['name']} - {source['url']}")
    
    feed = feedparser.parse(source["url"])
    articles = []
    
    for entry in feed.entries:
        article_id = generate_article_id(entry.get("link", ""))
        pub_date = parse_date(entry)
        
        article = {
            "id": article_id,
            "title": entry.get("title", "").strip(),
            "link": entry.get("link", ""),
            "summary": entry.get("summary", "").strip(),
            "published": pub_date.isoformat(),
            "published_date": pub_date.strftime("%Y-%m-%d"),
            "source": source["name"],
            "source_category": source["category"],
            "language": source["language"],
            "authors": [author.get("name", "") for author in entry.get("authors", [])],
            "tags": [tag.get("term", "") for tag in entry.get("tags", [])],
            "fetched_at": datetime.now().isoformat(),
        }
        articles.append(article)
    
    print(f"  抓取到 {len(articles)} 篇文章")
    return articles


def save_article(article: Dict[str, Any], translate: bool = True) -> bool:
    """保存单篇文章到JSON文件，如果已存在则跳过"""
    filepath = os.path.join(ARTICLES_DIR, f"{article['id']}.json")
    
    if os.path.exists(filepath):
        return False  # 已存在，跳过
    
    # 翻译文章（添加中文字段，有 API 密钥时使用 API 翻译）
    if translate:
        use_api = bool(
            os.environ.get("DEEPSEEK_API_KEY")
            or os.environ.get("DEEPL_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
        )
        article = translate_article(article, use_api=use_api)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(article, f, ensure_ascii=False, indent=2)
    
    return True


def load_article(article_id: str) -> Dict[str, Any]:
    """加载单篇文章"""
    filepath = os.path.join(ARTICLES_DIR, f"{article_id}.json")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_all_articles() -> List[Dict[str, Any]]:
    """加载所有文章"""
    articles = []
    if not os.path.exists(ARTICLES_DIR):
        return articles
    
    for filename in os.listdir(ARTICLES_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(ARTICLES_DIR, filename), "r", encoding="utf-8") as f:
                articles.append(json.load(f))
    
    # 按发布时间排序
    articles.sort(key=lambda x: x.get("published", ""), reverse=True)
    return articles


def fetch_all_feeds() -> Dict[str, Any]:
    """抓取所有RSS源并保存"""
    ensure_dirs()
    
    result = {
        "fetched_at": datetime.now().isoformat(),
        "sources": [],
        "new_articles": 0,
        "total_articles": 0,
    }
    
    for source in FEED_SOURCES:
        articles = fetch_feed(source)
        new_count = 0
        
        for article in articles:
            if save_article(article):
                new_count += 1
        
        result["sources"].append({
            "name": source["name"],
            "total": len(articles),
            "new": new_count,
        })
        result["new_articles"] += new_count
        result["total_articles"] += len(articles)
    
    # 保存抓取记录
    record_path = os.path.join(DATA_DIR, f"fetch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml")
    with open(record_path, "w", encoding="utf-8") as f:
        yaml.dump(result, f, allow_unicode=True, sort_keys=False)
    
    return result


def get_articles_by_date(date_str: str) -> List[Dict[str, Any]]:
    """获取指定日期的文章"""
    all_articles = load_all_articles()
    return [a for a in all_articles if a.get("published_date") == date_str]


def get_recent_articles(days: int = 1) -> List[Dict[str, Any]]:
    """获取最近N天的文章"""
    all_articles = load_all_articles()
    cutoff_date = datetime.now() - __import__("datetime").timedelta(days=days)
    
    return [
        a for a in all_articles
        if datetime.fromisoformat(a.get("published", "1970-01-01")) >= cutoff_date
    ]


if __name__ == "__main__":
    result = fetch_all_feeds()
    print(f"\n抓取完成!")
    print(f"新增文章: {result['new_articles']}")
    print(f"总共文章: {result['total_articles']}")