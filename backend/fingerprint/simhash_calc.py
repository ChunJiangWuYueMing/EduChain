"""
simhash_calc.py — 256 位 SimHash 内容指纹算法

为什么用 256 位而非经典的 64 位？
  1. 区分度：64 位汉明距离范围 0-64，同课程资料共享大量专业术语时
     容易误判为高度相似。256 位范围 0-256，细粒度提升 4 倍。
  2. 算法一致性：文件完整性用 SHA-256，SimHash 哈希基函数也用 SHA-256，
     整个指纹体系统一在同一个密码学原语上。
  3. 链上存储：Solidity uint256 原生支持，无需额外编码。

算法流程:
  1. jieba.analyse.extract_tags(text, topK=top_n, withWeight=True)
  2. 初始化 v = [0.0] * 256
  3. 每个关键词: h = SHA-256(word) → 256 位整数
     h 的第 i 位 == 1 则 v[i] += weight，否则 v[i] -= weight
  4. v[i] > 0 则结果第 i 位 = 1
  返回 256 位 int

汉明距离: d = bin(h1 ^ h2).count('1')
相似度: (256 - d) / 256 * 100%
阈值: d ≤ 12 高度相似 | d 13-40 衍生版本 | d > 40 差异较大
"""

import hashlib

import jieba
import jieba.analyse

# SimHash 维度（全局常量，所有相关计算引用此值）
SIMHASH_BITS = 256


def compute_simhash(text: str, top_n: int = 200) -> int:
    """
    计算文本的 256 位 SimHash 指纹。

    Args:
        text:  输入文本
        top_n: 提取的关键词数量

    Returns:
        256 位整数指纹
    """
    if not text or not text.strip():
        return 0

    # 1. 提取带权重的关键词
    keywords = jieba.analyse.extract_tags(text, topK=top_n, withWeight=True)

    # 过滤空串和单字符
    keywords = [(word, weight) for word, weight in keywords if len(word.strip()) > 1]

    if not keywords:
        return 0

    # 2. 初始化 256 维向量
    v = [0.0] * SIMHASH_BITS

    # 3. 逐关键词累加
    for word, weight in keywords:
        # SHA-256 哈希 → 完整 256 位
        h = _sha256_to_int(word)

        for i in range(SIMHASH_BITS):
            if h & (1 << i):
                v[i] += weight
            else:
                v[i] -= weight

    # 4. 降维：正数位设为 1
    fingerprint = 0
    for i in range(SIMHASH_BITS):
        if v[i] > 0:
            fingerprint |= (1 << i)

    return fingerprint


def hamming_distance(hash1: int, hash2: int) -> int:
    """
    计算两个 SimHash 的汉明距离。

    Returns:
        汉明距离 (0-256)
    """
    return bin(hash1 ^ hash2).count("1")


def similarity(hash1: int, hash2: int) -> float:
    """
    计算两个 SimHash 的相似度百分比。

    Returns:
        相似度 (0.0 - 100.0)
    """
    d = hamming_distance(hash1, hash2)
    return (SIMHASH_BITS - d) / SIMHASH_BITS * 100


def classify_similarity(hash1: int, hash2: int) -> str:
    """
    根据汉明距离判定相似程度。

    阈值设计（256 位，按 64 位经验等比例放大 4 倍）:
      d == 0     → identical  完全相同
      d ≤ 12     → high       高度相似（疑似抄袭）
      d 13-40    → derived    衍生版本（改写/摘抄）
      d > 40     → different  差异较大

    Returns:
        "identical" / "high" / "derived" / "different"
    """
    d = hamming_distance(hash1, hash2)
    if d == 0:
        return "identical"
    elif d <= 12:
        return "high"
    elif d <= 40:
        return "derived"
    else:
        return "different"


def _sha256_to_int(word: str) -> int:
    """
    计算关键词 SHA-256 哈希并转为 256 位整数。

    与文件完整性校验使用同一个密码学原语（SHA-256），
    保证指纹体系的算法一致性。

    Args:
        word: 关键词

    Returns:
        256 位整数
    """
    sha256_bytes = hashlib.sha256(word.encode("utf-8")).digest()  # 32 bytes
    return int.from_bytes(sha256_bytes, byteorder="big")