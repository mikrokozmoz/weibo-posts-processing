# 微博帖子分析工具包

一个用于处理、分析和挖掘微博帖子数据的 Python 工具包。本项目提供了数据预处理、文本清洗、分词、以及大规模微博语料的统计分析等实用功能。
## 项目简介

本工具包可将原始微博数据（推荐使用 [weibo-search](https://github.com/dataabc/weibo-search) 抓取）处理为结构化数据集，适用于语言学、社交媒体和情感分析等研究。
## 功能特性

- **数据加载**：批量加载文件夹下的 CSV 文件，自动从文件名提取关键词
- **文本预处理**：清洗和规范化微博文本（去除网址、表情、特殊字符等）
- **分词**：基于 Jieba 的中文分词，支持自定义词长过滤
- **统计分析**：
  - 按关键词/话题统计词频
  - 话题提取与排序
  - 帖子去重
- **可视化**：根据词频生成词云图片

## 安装方法
```bash
# 克隆仓库
git clone <repo-url>
cd post_analysis

# 安装依赖
pip install pandas jieba wordcloud matplotlib
```

## 快速上手

### 加载微博帖子
```python
from post_analysis import load_posts_from_folder

# 加载文件夹下所有 CSV 文件
# 文件名无 %23 前缀：关键词直接取自文件名
# 文件名有 %23 前缀：如 %23关键词%23 → 关键词提取为“关键词”
data = load_posts_from_folder('./posts')

print(data.head())
print(data['关键词'].unique())  # 查看所有关键词
```

### 文本分析

```python
from post_analysis import clean_text, tokenize_and_count_words, create_word_frequency_dataframe

# 文本清洗
cleaned_text = clean_text("这是微博文本 http://example.com 😊")

# 按关键词分词并统计词频
word_freq_by_keyword = tokenize_and_count_words(
  data,
  text_column='微博正文',
  keyword_column='关键词',
  word_length_range=(2, 4)
)

# 生成词频 DataFrame
freq_df = create_word_frequency_dataframe(word_freq_by_keyword)
```

### 生成词云

```python
from post_analysis import create_wordclouds

# 为每个关键词生成并保存词云图片
create_wordclouds(word_freq_by_keyword, output_dir='./wordclouds')
```

### 话题提取

```python
from post_analysis import extract_top_topics

# 从帖子中提取前3个热门话题
data_with_topics = extract_top_topics(data, topics_column='话题')
```

## 文件命名规范

抓取多关键词帖子时，工具支持 URL 编码的文件名：

- **标准格式**：`keyword.csv` → 关键词为“keyword”
- **URL 编码格式**：`%23keyword%23.csv` → 关键词为“keyword”

加载器会自动识别并处理上述两种格式。

## 数据格式

输入的 CSV 文件应包含微博数据的标准字段，例如：
- `微博正文`（帖子内容）
- `话题`（话题/标签）
- `id`（帖子ID）
- 其他元数据字段

## 去重

去除重复帖子，同时保留关键词关联：

```python
from post_analysis import dedupe_posts

dedupe_df = dedupe_posts(data, id_column='id', keyword_column='关键词')
```

## 模块结构

- **`pre_processing.py`**：数据加载、话题提取与去重
- **`corpus_analysis.py`**：文本清洗、分词、词频分析与可视化
- **`__init__.py`**：包导出与版本信息

## 依赖要求

- Python 3.7+
- pandas
- jieba
- wordcloud
- matplotlib

## 数据来源

原始微博数据推荐使用 [weibo-search](https://github.com/dataabc/weibo-search) 工具抓取。

## 许可证

MIT License

## 贡献

欢迎提交 issue 或 pull request 参与贡献！