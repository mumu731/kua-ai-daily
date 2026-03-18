# -*- coding: utf-8 -*-
"""
文章分类模块 - 自动分类跨境电商文章
"""
from typing import List, Dict, Any

# 分类规则 - 关键词匹配
CATEGORY_RULES = {
    "platform_policy": {
        "name": "平台动态",
        "name_en": "Platform Policy",
        "keywords": [
            "amazon", "temu", "shopify", "aliexpress", "ebay", "walmart",
            "政策", "policy", "rule", "update", "announcement", "seller",
            "fba", "fulfillment", "fee", "commission", "ban", "suspend",
            "亚马逊", "速卖通", "eBay", "沃尔玛", "卖家", "佣金", "费用"
        ],
        "icon": "🏪",
    },
    "market_trend": {
        "name": "市场趋势",
        "name_en": "Market Trend",
        "keywords": [
            "market", "trend", "growth", "decline", "sales", "revenue",
            "consumer", "buyer", "shopping", "ecommerce", "forecast",
            "share", "volume", "spending", "demand", "survey",
            "市场", "趋势", "增长", "下降", "销售", "收入", "消费者"
        ],
        "icon": "📊",
    },
    "cross_border_logistics": {
        "name": "跨境物流",
        "name_en": "Cross-Border Logistics",
        "keywords": [
            "shipping", "logistics", "delivery", "cargo", "freight",
            "customs", "clearance", "tariff", "duty", "tax",
            "warehouse", "fulfillment", "carrier", "port", "container",
            "物流", "运输", "货运", "清关", "关税", "仓储", "配送"
        ],
        "icon": "🚚",
    },
    "dtc_brand": {
        "name": "独立站品牌",
        "name_en": "DTC Brand",
        "keywords": [
            "dtc", "direct to consumer", "brand", "shopify", "woocommerce",
            "independent", "website", "store", "private label", "own brand",
            "独立站", "品牌", "自建站", "私域", "自主品牌"
        ],
        "icon": "🌐",
    },
    "case_study": {
        "name": "出海案例",
        "name_en": "Case Study",
        "keywords": [
            "case", "story", "success", "failure", "lesson", "learn",
            "how", "strategy", "approach", "experience", "interview",
            "案例", "故事", "成功", "失败", "经验", "策略", "专访"
        ],
        "icon": "📖",
    },
    "payment_finance": {
        "name": "支付金融",
        "name_en": "Payment & Finance",
        "keywords": [
            "payment", "finance", "funding", "investment", "currency",
            "exchange", "rate", "fintech", "bank", "credit", "loan",
            "支付", "金融", "融资", "投资", "汇率", "外汇", "信贷"
        ],
        "icon": "💰",
    },
    "technology": {
        "name": "技术创新",
        "name_en": "Technology",
        "keywords": [
            "ai", "artificial intelligence", "automation", "technology",
            "tool", "software", "platform", "integration", "api",
            "人工智能", "自动化", "技术", "工具", "软件", "平台"
        ],
        "icon": "🤖",
    },
}


def classify_article(article: Dict[str, Any]) -> List[str]:
    """
    对单篇文章进行分类，返回分类key列表
    一篇文章可能属于多个分类
    """
    categories = []
    
    # 合并标题和摘要用于匹配
    text = f"{article.get('title', '')} {article.get('summary', '')}".lower()
    tags = [tag.lower() for tag in article.get("tags", [])]
    
    for cat_key, cat_config in CATEGORY_RULES.items():
        score = 0
        
        # 关键词匹配
        for keyword in cat_config["keywords"]:
            keyword_lower = keyword.lower()
            # 标题匹配权重更高
            if keyword_lower in article.get("title", "").lower():
                score += 3
            # 摘要匹配
            if keyword_lower in article.get("summary", "").lower():
                score += 1
            # 标签匹配
            if keyword_lower in tags:
                score += 2
        
        # 达到一定分数阈值才归类
        if score >= 2:
            categories.append(cat_key)
    
    # 如果没有匹配到任何分类，归为"其他"
    if not categories:
        categories.append("other")
    
    return categories


def classify_articles(articles: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    批量分类文章
    返回按分类组织的文章字典
    """
    result = {cat_key: [] for cat_key in list(CATEGORY_RULES.keys()) + ["other"]}
    
    for article in articles:
        categories = classify_article(article)
        article["categories"] = categories
        
        for cat in categories:
            if cat in result:
                result[cat].append(article)
    
    return result


def get_category_info(cat_key: str) -> Dict[str, Any]:
    """获取分类详细信息"""
    if cat_key in CATEGORY_RULES:
        return CATEGORY_RULES[cat_key]
    return {"name": "其他", "name_en": "Other", "icon": "📌", "keywords": []}


def get_all_categories() -> List[Dict[str, Any]]:
    """获取所有分类信息"""
    return [
        {"key": k, **v} for k, v in CATEGORY_RULES.items()
    ]


if __name__ == "__main__":
    # 测试示例
    test_article = {
        "title": "Amazon Announces New FBA Fee Structure for 2026",
        "summary": "Amazon is updating its Fulfillment by Amazon (FBA) fees...",
        "tags": ["Amazon", "FBA", "Fees"],
    }
    
    categories = classify_article(test_article)
    print(f"文章分类: {categories}")
    for cat in categories:
        info = get_category_info(cat)
        print(f"  - {info['icon']} {info['name']} ({info['name_en']})")