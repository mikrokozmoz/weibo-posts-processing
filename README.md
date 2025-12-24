# Weibo Post Analysis Toolkit

A Python toolkit for processing, analyzing, and extracting insights from Weibo posts. This project provides utilities for data preprocessing, text cleaning, tokenization, and statistical analysis of large-scale Weibo corpora.

## Overview

This toolkit processes raw Weibo post data (scraped using [weibo-search](https://github.com/dataabc/weibo-search)) into structured datasets suitable for linguistic, social media, and sentiment analysis research.

## Features

- **Data Loading**: Batch load CSV files from folder with automatic keyword extraction from filenames
- **Text Preprocessing**: Clean and normalize Weibo text (remove URLs, emojis, special characters)
- **Tokenization**: Chinese word segmentation using Jieba with configurable word length filtering
- **Statistical Analysis**: 
  - Word frequency analysis by keyword/topic
  - Topic extraction and ranking
  - Deduplication of posts
- **Visualization**: Generate word clouds from frequency data

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd post_analysis

# Install dependencies
pip install pandas jieba wordcloud matplotlib
```

## Quick Start

### Loading Weibo Posts

```python
from post_analysis import load_posts_from_folder

# Load all CSV files from a folder
# Filenames without %23 prefix: keyword extracted from filename
# Filenames with %23: e.g., %23关键词%23 → keyword extracted as "关键词"
data = load_posts_from_folder('./posts')

print(data.head())
print(data['关键词'].unique())  # View all keywords
```

### Text Analysis

```python
from post_analysis import clean_text, tokenize_and_count_words, create_word_frequency_dataframe

# Clean text data
cleaned_text = clean_text("这是微博文本 http://example.com 😊")

# Tokenize and count word frequencies by keyword
word_freq_by_keyword = tokenize_and_count_words(
    data, 
    text_column='微博正文',
    keyword_column='关键词',
    word_length_range=(2, 4)
)

# Create frequency dataframe
freq_df = create_word_frequency_dataframe(word_freq_by_keyword)
```

### Generate Word Clouds

```python
from post_analysis import create_wordclouds

# Create and save word clouds for each keyword
create_wordclouds(word_freq_by_keyword, output_dir='./wordclouds')
```

### Extract Topics

```python
from post_analysis import extract_top_topics

# Extract top 3 topics from posts
data_with_topics = extract_top_topics(data, topics_column='话题')
```

## Filename Convention

When scraping posts with multiple keywords, the tool supports URL-encoded filenames:

- **Standard format**: `keyword.csv` → keyword extracted as "keyword"
- **URL-encoded format**: `%23keyword%23.csv` → keyword extracted as "keyword"

The loader automatically detects and handles both formats.

## Data Format

Input CSV files should contain Weibo post data with standard columns such as:
- `微博正文` (post content)
- `话题` (topics/hashtags)
- `id` (post ID)
- Other metadata fields

## Deduplication

Remove duplicate posts while preserving keyword association:

```python
from post_analysis import dedupe_posts

dedupe_df = dedupe_posts(data, id_column='id', keyword_column='关键词')
```

## Module Structure

- **`pre_processing.py`**: Data loading, topic extraction, and deduplication
- **`corpus_analysis.py`**: Text cleaning, tokenization, word frequency analysis, and visualization
- **`__init__.py`**: Package exports and version info

## Requirements

- Python 3.7+
- pandas
- jieba
- wordcloud
- matplotlib

## Data Source

Raw post data is collected using [weibo-search](https://github.com/dataabc/weibo-search) - a popular Weibo scraping tool.

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.
