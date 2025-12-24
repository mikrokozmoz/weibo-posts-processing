"""
微博语料分析模块

此模块提供文本清洗、分词、词频统计等语料处理功能。
"""

import pandas as pd
import jieba
import re
from collections import Counter
from wordcloud import WordCloud
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.pyplot as plt
import math


def clean_text(text):
    """
    清洗文本，移除URL和特殊符号。
    
    参数：
    -----------
    text : str or None
        待清洗的文本
        
    返回值：
    -----------
    str
        清洗后的文本
        
    说明：
    -----------
    - 移除HTTP/HTTPS URL
    - 移除表情符号和特殊符号
    - 保留中文、英文和数字
    
    示例：
    -----------
    >>> text = "这是一条微博 http://example.com 😊 #话题#"
    >>> result = clean_text(text)
    >>> print(result)  # 输出: 这是一条微博话题
    """
    if pd.isna(text):
        return ""
    
    # 转换为字符串
    text = str(text)
    
    # 移除URL
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    
    # 移除表情符号和特殊符号，保留中文、英文和数字
    text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', text)
    
    return text


def tokenize_and_count_words(df, text_column='微博正文', keyword_column='关键词', 
                              word_length_range=(2, 4)):
    """
    按关键词分组进行分词和词频统计。
    
    参数：
    -----------
    df : pd.DataFrame
        输入DataFrame，必须包含文本列和关键词列
    text_column : str, optional
        包含文本的列名（默认为'微博正文'）
    keyword_column : str, optional
        包含关键词的列名（默认为'关键词'）
    word_length_range : tuple, optional
        保留词的长度范围 (最小长度, 最大长度)，默认为(2, 4)
        
    返回值：
    -----------
    dict
        键为关键词，值为该关键词下的词频Counter对象的字典
        
    说明：
    -----------
    - 使用jieba分词
    - 会跳过空白文本行
    - 返回的是各关键词的词频统计字典
        
    示例：
    -----------
    >>> word_freq_by_keyword = tokenize_and_count_words(df)
    >>> print(word_freq_by_keyword['关键词1'].most_common(10))
    """
    # 清洗文本
    print("开始清洗文本...")
    df_clean = df.copy()
    df_clean[f'{text_column}_cleaned'] = df_clean[text_column].apply(clean_text)
    
    # 移除空文本
    df_with_text = df_clean[df_clean[f'{text_column}_cleaned'].str.len() > 0].copy()
    print(f"有效文本数: {len(df_with_text)}")
    
    # 按关键词分别进行分词
    print("\n开始按关键词分词...")
    
    keywords_list = df_with_text[keyword_column].unique()
    word_freq_by_keyword = {}
    min_len, max_len = word_length_range
    
    for keyword in keywords_list:
        keyword_texts = df_with_text[df_with_text[keyword_column] == keyword][f'{text_column}_cleaned']
        
        all_words = []
        for text in keyword_texts:
            # 使用jieba分词
            words = jieba.cut(text)
            # 筛选指定长度的词
            filtered_words = [word for word in words if min_len <= len(word) <= max_len]
            all_words.extend(filtered_words)
        
        # 词频统计
        word_freq = Counter(all_words)
        word_freq_by_keyword[keyword] = word_freq
        print(f"  {keyword}: {len(all_words)} 词，{len(word_freq)} 独特词")
    
    return word_freq_by_keyword


def create_word_frequency_dataframe(word_freq_by_keyword, top_n=100):
    """
    将词频字典转换为长格式的DataFrame。
    
    参数：
    -----------
    word_freq_by_keyword : dict
        键为关键词，值为Counter对象的字典
    top_n : int, optional
        每个关键词保留的前N个高频词（默认为100）
        
    返回值：
    -----------
    pd.DataFrame
        长格式的DataFrame，包含'关键词'、'词'、'词频'三列
        
    说明：
    -----------
    - 每行代表一个(关键词, 词)对及其频率
    - 仅保留各关键词的高频词
    
    示例：
    -----------
    >>> df_word_freq = create_word_frequency_dataframe(word_freq_by_keyword, top_n=50)
    >>> print(df_word_freq.head())
    """
    print("\n创建词频长表...")
    word_freq_list = []
    
    for keyword, word_freq in word_freq_by_keyword.items():
        for idx, (word, freq) in enumerate(word_freq.most_common(top_n), 1):
            word_freq_list.append({
                '关键词': keyword,
                '词': word,
                '词频': freq
            })
    
    df_word_freq = pd.DataFrame(word_freq_list)
    print(f"✓ 词频长表创建完成，共 {len(df_word_freq)} 条记录")
    
    return df_word_freq


def create_wordclouds(df, keyword_column='关键词', text_column='微博正文',
                      word_column='词', freq_column='词频',
                      top_n=30, font_path=r"D:\code\fonts\NotoSansSC-Bold.ttf",
                      colors_list=None, cols=3, figsize=(20, 10),
                      prefer_horizontal=1.0, relative_scaling=0.5, min_font_size=10,
                      show=True):
    """
    为每个关键词生成词云图。函数兼容两种输入：
    - 传入的 `df` 已为词频长表，包含(关键词, 词, 词频)列；
    - 或者传入原始文本表，函数会基于 `text_column` 和 `keyword_column` 自动分词并统计词频后再绘图。

    参数：
    -----------
    df : pd.DataFrame
        输入DataFrame，既可以是词频长表也可以是原始文本表。
    keyword_column : str
        关键词列名（必须）。
    text_column : str
        原始文本列名，仅当传入原始文本表时需要（默认 '微博正文'）。
    word_column : str
        词频表中表示词的列名（默认 '词'）。
    freq_column : str
        词频表中表示频率的列名（默认 '词频'）。
    top_n : int
        每个关键词取前N个词用于绘图（默认30）。
    font_path : str or None
        字体路径，用于支持中文显示。若为None则使用系统默认字体。
    colors_list : list or None
        颜色列表，用于构造colormap（默认蓝绿黄渐变）。
    cols : int
        子图列数（默认3）。
    figsize : tuple
        图像大小（宽, 高）。
    prefer_horizontal, relative_scaling, min_font_size : 参数传递给 WordCloud。
    show : bool
        是否立即调用 `plt.show()` 展示图像。

    返回值：
    -----------
    matplotlib.figure.Figure
        返回生成的 Figure 对象（便于在 notebook 中进一步保存或调整）。

    说明：
    -----------
    - 如果传入的是原始文本表，会调用 `tokenize_and_count_words` 生成词频；
    - 若传入词频长表，请确保包含 `keyword_column`、`word_column` 和 `freq_column`。
    """

    # 准备颜色映射
    if colors_list is None:
        colors_list = ['#208fc6', '#5AABDB', '#80d16a', '#C4DA4C', '#f9c92b']
    custom_cmap = LinearSegmentedColormap.from_list('blue_green_yellow', colors_list)

    # 判断 df 是词频长表还是原始文本表
    is_wordfreq_table = {keyword_column, word_column, freq_column}.issubset(set(df.columns))

    if is_wordfreq_table:
        df_word_freq = df.copy()
    else:
        # 需要原始文本列存在
        if text_column not in df.columns:
            raise ValueError(f"输入DataFrame既不是词频表，也缺少文本列: {text_column}")
        # 使用现有的分词与统计函数
        word_freq_by_keyword = tokenize_and_count_words(df, text_column=text_column, keyword_column=keyword_column)
        df_word_freq = create_word_frequency_dataframe(word_freq_by_keyword, top_n=top_n)

    # 准备关键词列表
    keywords = sorted(df_word_freq[keyword_column].unique())
    n = len(keywords)
    if n == 0:
        raise ValueError("未找到任何关键词用于生成词云")

    rows = math.ceil(n / cols)
    fig, axes = plt.subplots(rows, cols, figsize=figsize)
    # 统一处理 axes 为一维列表
    if isinstance(axes, plt.Axes) or axes.ndim == 0:
        axes = [axes]
    else:
        axes = axes.flatten()

    for idx, keyword in enumerate(keywords):
        ax = axes[idx]
        subset = df_word_freq[df_word_freq[keyword_column] == keyword]
        topn = subset.nlargest(top_n, freq_column)
        freqs = dict(zip(topn[word_column], topn[freq_column]))

        if not freqs:
            ax.axis('off')
            continue

        wc = WordCloud(
            font_path=font_path,
            width=400,
            height=300,
            background_color='white',
            colormap=custom_cmap,
            prefer_horizontal=prefer_horizontal,
            relative_scaling=relative_scaling,
            min_font_size=min_font_size
        ).generate_from_frequencies(freqs)

        ax.imshow(wc, interpolation='bilinear')
        ax.set_title(f'{keyword} - TOP{top_n}热词', fontsize=12, fontweight='bold')
        ax.axis('off')

    # 关闭多余子图
    for j in range(n, len(axes)):
        try:
            axes[j].axis('off')
        except Exception:
            pass

    plt.tight_layout()
    if show:
        # show the plot but do not return the Figure object to avoid
        # Jupyter displaying it twice (once from plt.show() and once
        # from the returned Figure being auto-displayed).
        plt.show()
        return None

    # When not showing immediately, return the Figure so caller can save or display it.
    return fig
