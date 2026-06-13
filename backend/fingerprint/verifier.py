"""
verifier.py — 双层验证引擎

第一层: SHA-256 精确校验（文件级完整性）
  - 上传时计算文件 SHA-256，存链上
  - 下载前服务端重新计算，与链上比对
  - 不一致说明文件被篡改

第二层: SimHash 相似度检测（内容级防抄袭）
  - 上传时计算文本 SimHash，存链上
  - 新上传时与所有已有资料比对汉明距离
  - d ≤ 12 高度相似，d 13-40 衍生版本
"""

import hashlib
from dataclasses import dataclass
from typing import Optional

from config import config
from fingerprint.extractor import extract_text
from fingerprint.simhash_calc import (
    compute_simhash,
    hamming_distance,
    similarity,
    classify_similarity,
)


@dataclass
class FingerprintResult:
    """指纹计算结果"""
    sha256_hash: bytes          # 32 字节原始哈希
    sha256_hex: str             # 十六进制字符串
    sim_hash: int               # 256 位 SimHash
    text_length: int            # 提取文本长度
    text_preview: str           # 文本前 200 字预览

    def to_dict(self) -> dict:
        return {
            "sha256_hash": self.sha256_hex,
            "sim_hash": self.sim_hash,
            "sim_hash_hex": hex(self.sim_hash),
            "text_length": self.text_length,
            "text_preview": self.text_preview,
        }


@dataclass
class VerifyResult:
    """验证结果"""
    sha256_match: bool          # SHA-256 是否一致
    sha256_local: str           # 本地计算的哈希
    sha256_chain: str           # 链上记录的哈希
    sim_hash_local: int         # 本地计算的 SimHash
    sim_hash_chain: int         # 链上记录的 SimHash
    hamming_dist: int           # 汉明距离
    similarity_pct: float       # 相似度百分比
    classification: str         # identical/high/derived/different
    is_tampered: bool           # 综合判定：是否被篡改
    common_keywords: list       # 共同关键词
    added_keywords: list        # 待验证文件中新增的关键词
    removed_keywords: list      # 待验证文件中缺失的关键词
    text_length_local: int      # 本地文件文本长度
    text_length_chain: int      # 链上记录的文本长度

    def to_dict(self) -> dict:
        return {
            "sha256_match": self.sha256_match,
            "sha256_local": self.sha256_local,
            "sha256_chain": self.sha256_chain,
            "sim_hash_local": hex(self.sim_hash_local),
            "sim_hash_chain": hex(self.sim_hash_chain),
            "hamming_distance": self.hamming_dist,
            "similarity_percent": round(self.similarity_pct, 2),
            "classification": self.classification,
            "is_tampered": self.is_tampered,
            "common_keywords": self.common_keywords,
            "added_keywords": self.added_keywords,
            "removed_keywords": self.removed_keywords,
            "text_length_local": self.text_length_local,
            "text_length_chain": self.text_length_chain,
        }


@dataclass
class SimilarityHit:
    """相似度命中记录"""
    material_id: str
    material_name: str
    hamming_dist: int
    similarity_pct: float
    classification: str         # high / derived / different

    def to_dict(self) -> dict:
        return {
            "material_id": self.material_id,
            "material_name": self.material_name,
            "hamming_distance": self.hamming_dist,
            "similarity_percent": round(self.similarity_pct, 2),
            "classification": self.classification,
        }


# ========== 核心函数 ==========


def compute_fingerprint(file_path: str) -> FingerprintResult:
    """
    计算文件的双层指纹（SHA-256 + SimHash）。

    上传流程中调用，返回结果供上链使用。

    Args:
        file_path: 文件路径

    Returns:
        FingerprintResult 包含 SHA-256 和 SimHash
    """
    # --- SHA-256（对原始文件字节计算） ---
    sha256_hash = _compute_file_sha256(file_path)
    sha256_hex = sha256_hash.hex()

    # --- 文本提取 + SimHash ---
    text = extract_text(file_path)
    sim_hash = compute_simhash(text, top_n=config.SIMHASH_TOP_N)

    return FingerprintResult(
        sha256_hash=sha256_hash,
        sha256_hex=sha256_hex,
        sim_hash=sim_hash,
        text_length=len(text),
        text_preview=text[:200] if text else "",
    )


def verify_file_integrity(
    file_path: str,
    chain_sha256_hex: str,
    chain_sim_hash: int,
    original_text: str = "",
) -> VerifyResult:
    """
    验证文件完整性（与链上记录比对）。

    下载前服务端预校验 + 独立验证接口使用。

    Args:
        file_path:        待验证文件路径
        chain_sha256_hex: 链上记录的 SHA-256（hex 字符串）
        chain_sim_hash:   链上记录的 SimHash
        original_text:    原始文件的文本内容（用于关键词对比）

    Returns:
        VerifyResult 包含逐层比对结果
    """
    # 本地重新计算
    fp = compute_fingerprint(file_path)

    # SHA-256 比对
    sha256_match = fp.sha256_hex == chain_sha256_hex.replace("0x", "").lower()

    # SimHash 比对
    h_dist = hamming_distance(fp.sim_hash, chain_sim_hash)
    sim_pct = similarity(fp.sim_hash, chain_sim_hash)
    classification = classify_similarity(fp.sim_hash, chain_sim_hash)

    # 综合判定：SHA-256 不一致即为篡改
    is_tampered = not sha256_match

    # 关键词差异分析
    local_text = extract_text(file_path)
    local_kw = set(extract_keywords(local_text))
    original_kw = set(extract_keywords(original_text)) if original_text else set()

    common_keywords = sorted(local_kw & original_kw) if original_kw else []
    added_keywords = sorted(local_kw - original_kw) if original_kw else []
    removed_keywords = sorted(original_kw - local_kw) if original_kw else []

    return VerifyResult(
        sha256_match=sha256_match,
        sha256_local=fp.sha256_hex,
        sha256_chain=chain_sha256_hex,
        sim_hash_local=fp.sim_hash,
        sim_hash_chain=chain_sim_hash,
        hamming_dist=h_dist,
        similarity_pct=sim_pct,
        classification=classification,
        is_tampered=is_tampered,
        common_keywords=common_keywords,
        added_keywords=added_keywords,
        removed_keywords=removed_keywords,
        text_length_local=len(local_text),
        text_length_chain=0,
    )


def check_similarity(
    new_sim_hash: int,
    existing_materials: list[dict],
) -> list[SimilarityHit]:
    """
    将新资料的 SimHash 与已有资料对比，检测相似内容。

    上传时调用，用于查重 / 抄袭检测。

    Args:
        new_sim_hash:       新资料的 SimHash
        existing_materials: 已有资料列表，每项需包含:
                           {"id": str, "name": str, "sim_hash": int}

    Returns:
        相似度达到衍生版本阈值以上的命中列表（按汉明距离升序）
    """
    hits = []
    for mat in existing_materials:
        mat_simhash = mat["sim_hash"]
        if mat_simhash == 0:
            continue

        h_dist = hamming_distance(new_sim_hash, mat_simhash)

        # 只报告衍生版本及以上的相似度（d ≤ 10）
        if h_dist <= config.SIMHASH_DERIVED_THRESHOLD:
            hits.append(SimilarityHit(
                material_id=mat["id"],
                material_name=mat["name"],
                hamming_dist=h_dist,
                similarity_pct=similarity(new_sim_hash, mat_simhash),
                classification=classify_similarity(new_sim_hash, mat_simhash),
            ))

    # 按汉明距离排序（最相似的在前）
    hits.sort(key=lambda h: h.hamming_dist)
    return hits


def extract_keywords(text: str, top_n: int = 20) -> list[str]:
    """提取文本的 Top-N 关键词"""
    if not text or not text.strip():
        return []
    try:
        import jieba.analyse
        keywords = jieba.analyse.extract_tags(text, topK=top_n)
        return [kw for kw in keywords if len(kw.strip()) > 1]
    except Exception:
        return []


# ========== 内部工具 ==========


def _compute_file_sha256(file_path: str) -> bytes:
    """
    计算文件的 SHA-256 哈希。

    对原始文件字节计算（不是提取后的文本），
    这样任何字节级修改都能检测到。

    Returns:
        32 字节的哈希值
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            sha256.update(chunk)
    return sha256.digest()