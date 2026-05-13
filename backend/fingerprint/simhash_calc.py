"""
simhash_calc.py — SimHash 内容指纹算法

算法流程（严格按项目规范）:
  1. jieba.analyse.extract_tags(text, topK=top_n, withWeight=True)
  2. 初始化 v = [0.0] * 64
  3. 每个关键词: h = MD5(word) 取低 64 位
     h 的第 i 位 == 1 则 v[i] += weight，否则 v[i] -= weight
  4. v[i] > 0 则结果第 i 位 = 1
  返回 64 位 int

汉明距离: d = bin(h1 ^ h2).count('1')
相似度: (64 - d) / 64 * 100%
阈值: d ≤ 3 高度相似 | d 4-10 衍生版本 | d > 10 差异较大
"""

import hashlib
from typing import Optional

import jieba
import jieba.analyse


def compute_simhash(text: str, top_n: int = 200) -> int:
    """
    计算文本的 64 位 SimHash 指纹。

    Args:
        text:  输入文本
        top_n: 提取的关键词数量

    Returns:
        64 位整数指纹
    """
    if not text or not text.strip():
        return 0

    # 1. 提取带权重的关键词
    keywords = jieba.analyse.extract_tags(text, topK=top_n, withWeight=True)

    # 过滤空串和单字符（规范要求）
    keywords = [(word, weight) for word, weight in keywords if len(word.strip()) > 1]

    if not keywords:
        return 0

    # 2. 初始化 64 维向量
    v = [0.0] * 64

    # 3. 逐关键词累加
    for word, weight in keywords:
        # MD5 哈希取低 64 位
        h = _md5_low64(word)

        for i in range(64):
            if h & (1 << i):
                v[i] += weight
            else:
                v[i] -= weight

    # 4. 降维：正数位设为 1
    fingerprint = 0
    for i in range(64):
        if v[i] > 0:
            fingerprint |= (1 << i)

    return fingerprint


def hamming_distance(hash1: int, hash2: int) -> int:
    """
    计算两个 SimHash 的汉明距离。

    Args:
        hash1: 第一个 SimHash
        hash2: 第二个 SimHash

    Returns:
        汉明距离 (0-64)
    """
    return bin(hash1 ^ hash2).count("1")


def similarity(hash1: int, hash2: int) -> float:
    """
    计算两个 SimHash 的相似度百分比。

    Args:
        hash1: 第一个 SimHash
        hash2: 第二个 SimHash

    Returns:
        相似度 (0.0 - 100.0)
    """
    d = hamming_distance(hash1, hash2)
    return (64 - d) / 64 * 100


def classify_similarity(hash1: int, hash2: int) -> str:
    """
    根据汉明距离判定相似程度。

    Returns:
        "identical"  - 完全相同 (d == 0)
        "high"       - 高度相似 (d ≤ 3)
        "derived"    - 衍生版本 (d 4-10)
        "different"  - 差异较大 (d > 10)
    """
    d = hamming_distance(hash1, hash2)
    if d == 0:
        return "identical"
    elif d <= 3:
        return "high"
    elif d <= 10:
        return "derived"
    else:
        return "different"


def _md5_low64(word: str) -> int:
    """
    计算关键词 MD5 哈希的低 64 位。

    Args:
        word: 关键词

    Returns:
        64 位整数
    """
    md5_bytes = hashlib.md5(word.encode("utf-8")).digest()  # 16 bytes
    # 取低 8 字节（little-endian）作为 64 位整数
    low64 = int.from_bytes(md5_bytes[:8], byteorder="little")
    return low64
