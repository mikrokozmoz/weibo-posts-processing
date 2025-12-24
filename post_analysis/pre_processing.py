"""
微博数据预处理模块

此模块提供数据加载和特征提取的核心函数。
"""

import os
from pathlib import Path
import pandas as pd


def load_posts_from_folder(folder_path, keyword_column='关键词'):
    """
    从指定文件夹加载所有CSV文件，合并为单个DataFrame。
    
    参数：
    -----------
    folder_path : str or Path
        包含CSV文件的文件夹路径
    keyword_column : str, optional
        新增列的名称，用于存储关键词（默认为'关键词'）。
        
    返回值：
    -----------
    pd.DataFrame
        合并后的DataFrame，包含所有CSV数据及新增的关键词列。
        关键词值为CSV文件名（不含扩展名）。
        
    异常：
    -----------
    ValueError
        当文件夹不存在或不包含CSV文件时抛出。
        
    示例：
    -----------
    >>> data = load_posts_from_folder('./posts')
    >>> print(data.head())
    >>> print(data['关键词'].unique())
    """
    folder_path = Path(folder_path)
    
    if not folder_path.is_dir():
        raise ValueError(f"指定路径不存在或不是文件夹: {folder_path}")
    
    # 获取文件夹内所有CSV文件
    csv_files = list(folder_path.glob('*.csv'))
    
    if not csv_files:
        raise ValueError(f"文件夹 {folder_path} 中未找到任何CSV文件")
    
    dfs = []
    
    for csv_file in sorted(csv_files):
        # 读取CSV文件
        df = pd.read_csv(csv_file)

        # 提取文件名（不含扩展名）作为关键词
        keyword = csv_file.stem  # .stem 获取不含扩展名的文件名

        # 如果文件名形如 %23关键词%23，则去掉前后 %23
        if isinstance(keyword, str) and keyword.startswith('%23') and keyword.endswith('%23'):
            keyword = keyword[3:-3]

        # 新增关键词列
        df[keyword_column] = keyword

        dfs.append(df)
        print(f"已加载: {csv_file.name} (行数: {len(df)}, 关键词: {keyword})")
    
    # 合并所有DataFrame
    combined_df = pd.concat(dfs, ignore_index=True)
    
    print(f"\n合并完成！总行数: {len(combined_df)}, 关键词列表: {sorted(combined_df[keyword_column].unique().tolist())}")
    
    return combined_df


def extract_top_topics(df, topics_column='话题', id_column='id'):
    """
    从话题列中提取前三个话题，拆分为独立的列。
    
    参数：
    -----------
    df : pd.DataFrame
        输入DataFrame，必须包含话题列
    topics_column : str, optional
        包含逗号分隔话题的列名（默认为'话题'）
    id_column : str, optional
        ID列的列名（默认为'id'），用于合并结果
        
    返回值：
    -----------
    pd.DataFrame
        添加了'第一话题'、'第二话题'、'第三话题'列的DataFrame。
        原始的话题列会被移除。
        
    说明：
    -----------
    - 假设话题使用逗号分隔
    - 如果某一位置的话题缺失，该字段将为NaN
    - 返回的是原DataFrame的拷贝，不会修改原数据
        
    示例：
    -----------
    >>> df = pd.DataFrame({
    ...     'id': [1, 2],
    ...     '话题': ['话题A,话题B,话题C', '话题X,话题Y']
    ... })
    >>> result = extract_top_topics(df)
    >>> print(result)
    """
    # 复制DataFrame以避免修改原始数据
    df_result = df.copy()
    
    # 检查必要列是否存在
    if topics_column not in df_result.columns:
        raise ValueError(f"DataFrame中不存在列'{topics_column}'")
    if id_column not in df_result.columns:
        raise ValueError(f"DataFrame中不存在列'{id_column}'")
    
    # 提取ID和话题列
    df_topic = df_result.loc[:, [id_column, topics_column]].copy()
    
    # 分割话题，扩展为三列（第一、二、三话题）
    split_topics = df_topic[topics_column].str.split(",", n=3, expand=True)
    
    # 为新列赋予标准名称
    df_topic["第一话题"] = split_topics[0]
    df_topic["第二话题"] = split_topics[1]
    df_topic["第三话题"] = split_topics[2]
    
    # 移除原始话题列
    df_topic.drop(columns=[topics_column], inplace=True)
    
    # 将提取的话题列合并回原DataFrame
    df_result = df_result.merge(df_topic, on=id_column, how="left")
    
    print("✓ 话题提取成功完成")
    
    return df_result


def dedupe_posts(df, keyword_col='关键词', text_col='微博正文_cleaned', time_col='发布时间',
                sum_cols=None, similarity_threshold=0.88, min_len_for_similarity=6,
                debug=False, debug_pairs_path=None, auto_clean=False):
    """
    在每个关键词分组内合并重复的正文（按清洗后的正文匹配），并把数值列求和。

    参数：
    -----------
    df : pd.DataFrame
        待处理的DataFrame（不会在原地修改，函数返回新的DataFrame）
    keyword_col : str
        用于分组的关键词列名（默认 '关键词'）
    text_col : str
        用于判断重复的清洗后正文列名（默认 '微博正文_cleaned'）
    time_col : str
        用于选择保留哪一条记录的时间列（默认 '发布时间'），按升序保留最早一条
    sum_cols : list or None
        需要求和的数值列列表，默认包括 ['点赞数','评论数','转发数','互动总数']
    auto_clean : bool
        当指定的text_col不存在时，是否自动基于'微博正文'进行清洗（默认 False）。
        如果为False，则直接使用原始文本进行比对。

    返回值：
    -----------
    pd.DataFrame
        去重并合并数值列后的新DataFrame
    """
    import re

    if debug:
        print("开始去重处理...")
        print(f"参数: similarity_threshold={similarity_threshold}, min_len_for_similarity={min_len_for_similarity}")

    if sum_cols is None:
        sum_cols = ['点赞数', '评论数', '转发数', '互动总数']

    import re
    import jieba
    import difflib

    print("开始去重处理...")

    if sum_cols is None:
        sum_cols = ['点赞数', '评论数', '转发数', '互动总数']

    df_proc = df.copy()
    if debug:
        print(f"原始行数: {len(df_proc)}")

    # 必要列检查
    if keyword_col not in df_proc.columns:
        raise ValueError(f"DataFrame中不存在列 '{keyword_col}'")

    # 缺少清洗列时的处理
    if text_col not in df_proc.columns:
        if auto_clean:
            if debug:
                print(f"未检测到清洗列 '{text_col}'，尝试基于 '微博正文' 生成清洗列...")

            def _clean_text_local(text):
                if pd.isna(text):
                    return ''
                text = str(text)
                text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
                text = re.sub(r'[^\\u4e00-\\u9fa5a-zA-Z0-9]', '', text)
                return text

            if '微博正文' in df_proc.columns:
                df_proc[text_col] = df_proc['微博正文'].apply(_clean_text_local)
                if debug:
                    print(f"已基于 '微博正文' 生成清洗列 '{text_col}'")
            else:
                df_proc[text_col] = ''
                if debug:
                    print(f"未找到 '微博正文'，已创建空列 '{text_col}' 以继续处理")
        else:
            # auto_clean=False 时，直接使用原始文本列
            if '微博正文' in df_proc.columns:
                df_proc[text_col] = df_proc['微博正文']
                if debug:
                    print(f"未检测到清洗列 '{text_col}'，直接使用原始文本列 '微博正文'")
            else:
                df_proc[text_col] = ''
                if debug:
                    print(f"未找到 '微博正文'，已创建空列 '{text_col}' 以继续处理")

    df_proc[text_col] = df_proc[text_col].fillna('')

    # 尝试转换时间列
    if time_col in df_proc.columns:
        try:
            df_proc[time_col] = pd.to_datetime(df_proc[time_col])
        except Exception:
            if debug:
                print(f"警告: 无法将列 '{time_col}' 转换为 datetime")
            pass

    # 确保数值列存在
    created_cols = []
    for c in sum_cols:
        if c not in df_proc.columns:
            df_proc[c] = 0
            created_cols.append(c)
    if created_cols and debug:
        print(f"为兼容性创建了缺失的数值列: {created_cols}")

    # 第一步：精确匹配去重（按关键词 + 清洗正文）
    group_keys = [keyword_col, text_col]
    group_sizes = df_proc.groupby(group_keys).size()
    dup_keys = group_sizes[group_sizes > 1].index.tolist()
    if debug:
        print(f"精确重复组数量: {len(dup_keys)}")

    drop_indices = []
    for key in dup_keys:
        kw, text = key
        mask = (df_proc[keyword_col] == kw) & (df_proc[text_col] == text)
        sub = df_proc[mask].copy()
        if time_col in sub.columns:
            sub_sorted = sub.sort_values(time_col)
        else:
            sub_sorted = sub
        earliest_idx = sub_sorted.index[0]
        sums = sub_sorted[sum_cols].sum()
        sums = sums.reindex(sum_cols).fillna(0)
        df_proc.loc[earliest_idx, sum_cols] = sums.values
        drop_indices.extend(list(sub_sorted.index[1:]))

    data_exact_deduped = df_proc.drop(index=drop_indices).reset_index(drop=True)
    if debug:
        print(f"精确去重后行数: {len(data_exact_deduped)} (删除 {len(drop_indices)} 条)")

    # 第二步：近似去重 —— 处理词替换但主体相同的情况
    near_dup_drop = []
    near_dup_groups = 0
    debug_matches = []
    keywords = data_exact_deduped[keyword_col].unique()
    for kw in keywords:
        sub = data_exact_deduped[data_exact_deduped[keyword_col] == kw].copy()
        texts = sub[text_col].tolist()
        indices = sub.index.tolist()

        # Build length buckets to reduce comparisons
        buckets = {}
        for idx, text in zip(indices, texts):
            L = len(text)
            key_bucket = (L // 10)
            buckets.setdefault(key_bucket, []).append((idx, text))

        # Compare within buckets
        for bucket_items in buckets.values():
            n = len(bucket_items)
            for i in range(n):
                idx_i, text_i = bucket_items[i]
                if idx_i in near_dup_drop:
                    continue
                # skip very short texts
                if len(text_i) < min_len_for_similarity:
                    if debug:
                        print(f"跳过短文本 (idx={idx_i}, len={len(text_i)})")
                    continue
                tokens_i = set(jieba.lcut(text_i))
                for j in range(i+1, n):
                    idx_j, text_j = bucket_items[j]
                    if idx_j in near_dup_drop:
                        continue
                    if len(text_j) < min_len_for_similarity:
                        if debug:
                            print(f"跳过短文本 (idx={idx_j}, len={len(text_j)})")
                        continue
                    # quick length ratio filter
                    if max(len(text_i), len(text_j)) > 0 and abs(len(text_i)-len(text_j))/max(len(text_i), len(text_j)) > 0.25:
                        if debug:
                            print(f"跳过长度比例差异大 (idx_i={idx_i}, idx_j={idx_j}, len_i={len(text_i)}, len_j={len(text_j)})")
                        continue
                    tokens_j = set(jieba.lcut(text_j))
                    # compute Jaccard
                    union = tokens_i | tokens_j
                    if not union:
                        continue
                    jaccard = len(tokens_i & tokens_j) / len(union)
                    similar = False
                    if jaccard >= similarity_threshold:
                        similar = True
                    else:
                        # fallback to sequence ratio
                        ratio = difflib.SequenceMatcher(None, text_i, text_j).ratio()
                        if ratio >= similarity_threshold:
                            similar = True

                    if debug:
                        print(f"比较 idx_i={idx_i} idx_j={idx_j} jaccard={jaccard:.3f} ratio={ratio:.3f} similar={similar}")

                    if similar:
                        # decide canonical by earliest发布时间 if available, else keep lower index
                        row_i = data_exact_deduped.loc[idx_i]
                        row_j = data_exact_deduped.loc[idx_j]
                        if time_col in data_exact_deduped.columns:
                            t_i = pd.to_datetime(row_i.get(time_col)) if pd.notna(row_i.get(time_col)) else pd.NaT
                            t_j = pd.to_datetime(row_j.get(time_col)) if pd.notna(row_j.get(time_col)) else pd.NaT
                            if pd.isna(t_i) and pd.isna(t_j):
                                keep_idx, drop_idx = (idx_i, idx_j) if idx_i < idx_j else (idx_j, idx_i)
                            elif pd.isna(t_i):
                                keep_idx, drop_idx = (idx_j, idx_i)
                            elif pd.isna(t_j):
                                keep_idx, drop_idx = (idx_i, idx_j)
                            else:
                                keep_idx, drop_idx = (idx_i, idx_j) if t_i <= t_j else (idx_j, idx_i)
                        else:
                            keep_idx, drop_idx = (idx_i, idx_j) if idx_i < idx_j else (idx_j, idx_i)

                        # sum numeric cols from drop_idx into keep_idx
                        sums = data_exact_deduped.loc[[keep_idx, drop_idx]][sum_cols].sum()
                        data_exact_deduped.loc[keep_idx, sum_cols] = sums.values
                        near_dup_drop.append(drop_idx)
                        near_dup_groups += 1
                        if debug:
                            snippet_i = text_i if len(text_i) <= 200 else text_i[:200] + '...'
                            snippet_j = text_j if len(text_j) <= 200 else text_j[:200] + '...'
                            reason = 'jaccard' if jaccard >= similarity_threshold else 'ratio'
                            print(f"判定近似重复 (keyword={kw}) keep={keep_idx} drop={drop_idx} reason={reason} jaccard={jaccard:.3f} ratio={ratio:.3f}")
                            print(f"  text_i[{idx_i}]: {snippet_i}")
                            print(f"  text_j[{idx_j}]: {snippet_j}")
                            debug_matches.append({
                                'keyword': kw,
                                'keep_idx': keep_idx,
                                'drop_idx': drop_idx,
                                'jaccard': jaccard,
                                'ratio': ratio,
                                'text_i': text_i,
                                'text_j': text_j,
                            })

    # Remove near-duplicates
    data_final = data_exact_deduped.drop(index=near_dup_drop).reset_index(drop=True)

    # 如果要求把匹配明细写入文件
    if debug and debug_pairs_path and debug_matches:
        try:
            df_debug = pd.DataFrame(debug_matches)
            df_debug.to_csv(debug_pairs_path, index=False, encoding='utf-8-sig')
            print(f"已将近似匹配明细保存到: {debug_pairs_path}")
        except Exception as e:
            print(f"无法保存 debug_pairs_path: {e}")

    # 尝试类型恢复
    for c in sum_cols:
        if c in data_final.columns and pd.api.types.is_float_dtype(data_final[c]):
            if data_final[c].notna().all():
                try:
                    if (data_final[c] % 1 == 0).all():
                        data_final[c] = data_final[c].astype('int64')
                except Exception:
                    pass

    print(f"近似重复组数量: {near_dup_groups}，删除了 {len(near_dup_drop)} 条近似重复行")
    print(f"去重后总行数: {len(data_final)}")
    print('\n已生成 DataFrame近似去重版')

    return data_final
