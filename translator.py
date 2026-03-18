# -*- coding: utf-8 -*-
"""
翻译模块 - 将英文内容翻译为中文
支持使用 DeepL API、DeepSeek API、OpenAI API 或本地翻译
"""
import os
from typing import Dict, Any, Optional

# 简单的英中术语映射表（作为后备）
TERMINOLOGY_MAP = {
    # 电商平台
    "Amazon": "亚马逊",
    "Shopify": "Shopify",
    "Temu": "Temu",
    "AliExpress": "速卖通",
    "eBay": "eBay",
    "Walmart": "沃尔玛",
    "Shopee": "虾皮",
    "Lazada": "Lazada",
    "TikTok": "TikTok",
    "TikTok Shop": "TikTok Shop",
    
    # 物流相关
    "shipping": "物流运输",
    "logistics": "物流",
    "fulfillment": "履约",
    "warehouse": "仓储",
    "delivery": "配送",
    "cargo": "货运",
    "freight": "货运",
    "customs": "海关",
    "clearance": "清关",
    "tariff": "关税",
    "duty": "税费",
    
    # 商业术语
    "e-commerce": "电子商务",
    "cross-border": "跨境",
    "retail": "零售",
    "wholesale": "批发",
    "B2B": "B2B",
    "B2C": "B2C",
    "DTC": "DTC",
    "marketplace": "电商平台",
    "seller": "卖家",
    "buyer": "买家",
    "consumer": "消费者",
    
    # 财务相关
    "revenue": "收入",
    "profit": "利润",
    "margin": "利润率",
    "investment": "投资",
    "funding": "融资",
    "valuation": "估值",
    
    # 技术术语
    "AI": "人工智能",
    "automation": "自动化",
    "algorithm": "算法",
    "integration": "集成",
    "API": "API",
    
    # 常见动词/形容词
    "announces": "宣布",
    "launches": "推出",
    "acquires": "收购",
    "partners": "合作",
    "expands": "扩张",
    "growth": "增长",
    "decline": "下降",
    "increase": "增加",
    "decrease": "减少",
}


def translate_text(text: str, use_api: bool = False) -> str:
    """
    翻译文本为中文
    
    Args:
        text: 英文原文
        use_api: 是否使用API翻译（需要配置API密钥）
    
    Returns:
        中文翻译结果
    """
    if not text:
        return ""
    
    # 如果使用API翻译
    if use_api:
        api_result = _translate_with_api(text)
        if api_result:
            return api_result
    
    # 使用本地术语映射进行简单翻译
    return _translate_with_local_dict(text)


def _translate_with_api(text: str) -> Optional[str]:
    """使用API进行翻译"""
    # 优先尝试 DeepL API
    deepl_key = os.environ.get("DEEPL_API_KEY")
    if deepl_key:
        return _translate_with_deepl(text, deepl_key)
    
    # 尝试 DeepSeek API
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
    if deepseek_key:
        return _translate_with_deepseek(text, deepseek_key)
    
    # 尝试 OpenAI API
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        return _translate_with_openai(text, openai_key)
    
    return None


def _translate_with_deepl(text: str, api_key: str) -> Optional[str]:
    """使用 DeepL API 翻译"""
    try:
        import requests
        
        url = "https://api-free.deepl.com/v2/translate"
        headers = {"Authorization": f"DeepL-Auth-Key {api_key}"}
        data = {
            "text": text,
            "target_lang": "ZH",
            "source_lang": "EN",
        }
        
        response = requests.post(url, headers=headers, data=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result["translations"][0]["text"]
    except Exception as e:
        print(f"DeepL翻译失败: {e}")
    
    return None


def _translate_with_deepseek(text: str, api_key: str) -> Optional[str]:
    """使用 DeepSeek API 翻译（OpenAI 兼容格式）"""
    try:
        import openai

        client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
        )
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": "你是一个专业的跨境电商领域翻译助手。将英文翻译成地道的中文，保留品牌名和专有名词。"
                },
                {
                    "role": "user",
                    "content": f"请翻译以下内容：\n\n{text}"
                }
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"DeepSeek翻译失败: {e}")

    return None


def _translate_with_openai(text: str, api_key: str) -> Optional[str]:
    """使用 OpenAI API 翻译"""
    try:
        import openai
        
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-5.4-mini",
            messages=[
                {
                    "role": "system",
                    "content": "你是一个专业的跨境电商领域翻译助手。将英文翻译成地道的中文，保留品牌名和专有名词。"
                },
                {
                    "role": "user",
                    "content": f"请翻译以下内容：\n\n{text}"
                }
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI翻译失败: {e}")
    
    return None


def _translate_with_local_dict(text: str) -> str:
    """使用本地术语映射进行简单翻译"""
    translated = text
    
    # 替换术语（不区分大小写）
    for en, zh in TERMINOLOGY_MAP.items():
        # 整词匹配替换
        import re
        pattern = re.compile(r'\b' + re.escape(en) + r'\b', re.IGNORECASE)
        translated = pattern.sub(zh, translated)
    
    return translated


def translate_article(article: Dict[str, Any], use_api: bool = False) -> Dict[str, Any]:
    """
    翻译整篇文章
    
    Args:
        article: 文章字典
        use_api: 是否使用API翻译
    
    Returns:
        添加中文翻译字段的文章字典
    """
    # 保留原文
    article["title_en"] = article.get("title", "")
    article["summary_en"] = article.get("summary", "")
    
    # 翻译标题和摘要
    article["title_zh"] = translate_text(article.get("title", ""), use_api)
    article["summary_zh"] = translate_text(article.get("summary", ""), use_api)
    
    # 翻译标签
    article["tags_zh"] = [translate_text(tag, use_api) for tag in article.get("tags", [])]
    
    return article


def batch_translate(articles: list, use_api: bool = False) -> list:
    """批量翻译文章"""
    return [translate_article(article, use_api) for article in articles]


if __name__ == "__main__":
    # 测试
    test_text = "Amazon Announces New FBA Fee Structure for Cross-Border Sellers"
    print(f"原文: {test_text}")
    print(f"翻译: {translate_text(test_text)}")
    print()
    
    # 测试API翻译（如果有配置密钥）
    if os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY"):
        print("使用API翻译...")
        print(f"API翻译结果: {translate_text(test_text, use_api=True)}")