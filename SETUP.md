# 跨境电商早报系统 - 使用说明

## 系统架构

```
RSS源抓取 → 翻译汉化 → 自动分类 → JSON存储 → Markdown日报 → RSS订阅
```

## 核心模块

| 模块          | 功能          | 文件                                     |
| ------------- | ------------- | ---------------------------------------- |
| fetcher.py    | RSS抓取与存储 | 从两个数据源抓取文章，保存为JSON         |
| translator.py | 内容翻译      | 将英文内容翻译为中文（支持API/本地词典） |
| classifier.py | 自动分类      | 按7个维度自动分类文章                    |
| main_new.py   | 日报生成      | 生成分类日报Markdown和RSS订阅            |

## 数据源

1. **Digital Commerce 360** - 全球跨境电商行业新闻
   - URL: https://www.digitalcommerce360.com/topic/cross-border-ecommerce/feed/
   - 重点: 平台政策、市场趋势

2. **Cross-Border Magazine** - 国际电商/出海卖家/跨境物流
   - URL: https://cross-border-magazine.com/feed/
   - 重点: 欧洲市场、独立站、物流

## 内容分类

| 分类       | 图标 | 关键词                               |
| ---------- | ---- | ------------------------------------ |
| 平台动态   | 🏪   | Amazon, Temu, Shopify, TikTok Shop   |
| 市场趋势   | 📊   | market, trend, growth, sales         |
| 跨境物流   | 🚚   | shipping, logistics, customs, tariff |
| 独立站品牌 | 🌐   | DTC, brand, independent website      |
| 出海案例   | 📖   | case, story, success, strategy       |
| 支付金融   | 💰   | payment, finance, investment         |
| 技术创新   | 🤖   | AI, automation, technology           |

## 快速开始

### 1. 安装依赖

**方式一: 使用 pip**

```bash
pip install -r requirements.txt
```

**方式二: 使用 uv (推荐，更快)**

```bash
# 安装 uv
pip install uv

# 使用 uv 安装依赖
uv pip install -r requirements.txt

# 或使用 uv 创建虚拟环境并安装
uv venv
uv pip install -r requirements.txt
```

### 2. 手动抓取文章

```bash
python fetcher.py
```

文章将保存到 `data/articles/` 目录，每个文章一个JSON文件。

### 3. 生成日报

```bash
# 生成今日日报
python main_new.py --repo yourname/crossborder-daily

# 生成指定日期日报
python main_new.py --repo yourname/crossborder-daily --date 2026-03-18
```

### 4. 自动运行（GitHub Actions）

已配置 `.github/workflows/daily_fetch.yml`，每天北京时间10:00自动：

1. 抓取最新RSS文章
2. 生成日报
3. 推送更新

## 数据存储结构

```
data/
├── articles/           # 文章JSON存储
│   ├── a1b2c3d4.json
│   └── ...
├── daily/              # 日报数据（可选）
└── fetch_20260318.yaml # 抓取记录

BACKUP/
├── 1_2026-03-18.md     # 日报Markdown
└── ...

rss.xml                 # RSS订阅文件
```

## 配置说明

### 启用API翻译（推荐）

在 GitHub Secrets 中配置：

- `DEEPSEEK_API_KEY` - DeepSeek API密钥（使用 https://api.deepseek.com，模型 deepseek-chat）
- `DEEPL_API_KEY` - DeepL API密钥（可选）
- `OPENAI_API_KEY` - OpenAI API密钥（可选）

### 修改数据源

编辑 `fetcher.py` 中的 `FEED_SOURCES`：

```python
FEED_SOURCES = [
    {
        "name": "你的数据源名称",
        "url": "https://example.com/feed/",
        "category": "market",
        "language": "en",
    },
]
```

### 自定义分类规则

编辑 `classifier.py` 中的 `CATEGORY_RULES`，添加关键词。

## 替换原系统

如需完全替换原AI早报系统：

```bash
# 备份原文件
mv main.py main_backup.py
mv config.toml config_backup.toml

# 使用新文件
mv main_new.py main.py
mv config_crossborder.toml config.toml
```

## 自定义配置

修改以下占位符：

- `yourname.github.io/crossborder-daily/` → 你的GitHub Pages地址
- `user/repo` → 你的GitHub仓库名
- `crossborder@example.com` → 你的联系邮箱

## 依赖说明

- `feedparser` - RSS解析
- `pyyaml` - YAML配置
- `feedgen` - RSS生成
- `requests` - HTTP请求
- `openai` - API翻译（可选）
- `uv` - 可选，更快的包管理工具
