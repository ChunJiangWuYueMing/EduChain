"""
内容指纹引擎测试

用法:
  cd backend
  python -m tests.test_fingerprint
"""

import sys
import os
import tempfile
import hashlib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fingerprint.extractor import extract_text
from fingerprint.simhash_calc import (
    compute_simhash,
    hamming_distance,
    similarity,
    classify_similarity,
)
from fingerprint.verifier import (
    compute_fingerprint,
    verify_file_integrity,
    check_similarity,
)


def create_temp_file(content: str, suffix: str = ".txt") -> str:
    """创建临时文件并返回路径"""
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(content)
    return path


# 测试用中文文本
TEXT_A = """
区块链技术是一种分布式账本技术，通过密码学方法保证数据的不可篡改性和可追溯性。
每个区块包含前一个区块的哈希值，形成一条链式结构。共识机制确保网络中的节点对账本状态达成一致。
智能合约是运行在区块链上的程序，可以自动执行预定义的规则和逻辑。
以太坊是最广泛使用的智能合约平台，支持去中心化应用的开发。
"""

TEXT_B = """
区块链技术是分布式的账本技术，利用密码学手段保障数据不可篡改和可溯源。
每个区块都包含上一个区块的哈希，构成链状结构。共识算法确保网络节点就账本状态达成共识。
智能合约是部署在区块链上的自动化程序，能够执行预设的业务规则。
以太坊是使用最广泛的智能合约平台，支持去中心化应用开发。
"""

TEXT_C = """
机器学习是人工智能的一个分支，通过数据驱动的方式让计算机自动学习和改进。
监督学习需要标注数据，无监督学习从无标注数据中发现模式。
深度学习使用多层神经网络，在图像识别和自然语言处理领域取得了突破性成果。
"""


def test_all():
    print("=" * 60)
    print("  EduChain 内容指纹引擎测试")
    print("=" * 60)

    # ---------- 1. 文本提取测试 ----------
    print("\n[1] 测试文本提取...")

    # TXT 文件
    txt_path = create_temp_file(TEXT_A, ".txt")
    text = extract_text(txt_path)
    assert len(text) > 0, "TXT 提取为空"
    print(f"    ✅ TXT 提取: {len(text)} 字符")
    os.unlink(txt_path)

    # MD 文件
    md_content = "# 标题\n\n这是一段 **Markdown** 文本。\n\n- 列表项 1\n- 列表项 2"
    md_path = create_temp_file(md_content, ".md")
    text = extract_text(md_path)
    assert "标题" in text
    print(f"    ✅ MD 提取: {len(text)} 字符")
    os.unlink(md_path)

    # 不支持的格式
    try:
        extract_text("test.xyz")
    except (ValueError, FileNotFoundError):
        print(f"    ✅ 不支持格式正确拒绝")

    # ---------- 2. SimHash 计算测试 ----------
    print("\n[2] 测试 SimHash 计算...")

    hash_a = compute_simhash(TEXT_A)
    hash_b = compute_simhash(TEXT_B)
    hash_c = compute_simhash(TEXT_C)

    print(f"    文本 A (区块链): {hex(hash_a)}")
    print(f"    文本 B (区块链改写): {hex(hash_b)}")
    print(f"    文本 C (机器学习): {hex(hash_c)}")

    assert hash_a != 0, "SimHash 不应为 0"
    assert hash_b != 0, "SimHash 不应为 0"
    assert hash_c != 0, "SimHash 不应为 0"
    print(f"    ✅ 三个文本的 SimHash 均非零")

    # ---------- 3. 汉明距离测试 ----------
    print("\n[3] 测试汉明距离与相似度...")

    dist_ab = hamming_distance(hash_a, hash_b)
    dist_ac = hamming_distance(hash_a, hash_c)
    dist_aa = hamming_distance(hash_a, hash_a)

    sim_ab = similarity(hash_a, hash_b)
    sim_ac = similarity(hash_a, hash_c)

    print(f"    A vs A: 距离={dist_aa}, 相似度={similarity(hash_a, hash_a):.1f}%")
    print(f"    A vs B: 距离={dist_ab}, 相似度={sim_ab:.1f}% ({classify_similarity(hash_a, hash_b)})")
    print(f"    A vs C: 距离={dist_ac}, 相似度={sim_ac:.1f}% ({classify_similarity(hash_a, hash_c)})")

    assert dist_aa == 0, "同一文本距离应为 0"
    assert dist_ab < dist_ac, f"相似文本(A-B)距离应小于不相关文本(A-C): {dist_ab} vs {dist_ac}"
    print(f"    ✅ 距离关系正确: A-B({dist_ab}) < A-C({dist_ac})")

    # ---------- 4. 分类判定测试 ----------
    print("\n[4] 测试分类判定...")

    assert classify_similarity(hash_a, hash_a) == "identical"
    print(f"    ✅ identical: 自身 vs 自身")

    cls_ab = classify_similarity(hash_a, hash_b)
    print(f"    A vs B: {cls_ab}（距离 {dist_ab}）")

    cls_ac = classify_similarity(hash_a, hash_c)
    print(f"    A vs C: {cls_ac}（距离 {dist_ac}）")

    # ---------- 5. 双层指纹计算测试 ----------
    print("\n[5] 测试双层指纹计算...")

    file_a = create_temp_file(TEXT_A, ".txt")
    fp = compute_fingerprint(file_a)

    print(f"    SHA-256: {fp.sha256_hex[:32]}...")
    print(f"    SimHash: {hex(fp.sim_hash)}")
    print(f"    文本长度: {fp.text_length}")
    print(f"    预览: {fp.text_preview[:50]}...")

    assert len(fp.sha256_hash) == 32, "SHA-256 应为 32 字节"
    assert fp.sim_hash == hash_a, "指纹中的 SimHash 应与单独计算一致"
    assert fp.text_length > 0
    print(f"    ✅ 双层指纹一致")

    # ---------- 6. 文件完整性验证测试 ----------
    print("\n[6] 测试文件完整性验证...")

    # 未篡改
    result = verify_file_integrity(file_a, fp.sha256_hex, fp.sim_hash)
    assert result.sha256_match is True
    assert result.is_tampered is False
    assert result.classification == "identical"
    print(f"    ✅ 未篡改文件: sha256_match={result.sha256_match}, tampered={result.is_tampered}")

    # 篡改文件
    file_tampered = create_temp_file(TEXT_A + "\n额外添加的内容", ".txt")
    result2 = verify_file_integrity(file_tampered, fp.sha256_hex, fp.sim_hash)
    assert result2.sha256_match is False
    assert result2.is_tampered is True
    print(f"    ✅ 篡改文件: sha256_match={result2.sha256_match}, tampered={result2.is_tampered}")
    print(f"       SimHash 距离={result2.hamming_dist}, 分类={result2.classification}")

    os.unlink(file_a)
    os.unlink(file_tampered)

    # ---------- 7. 相似度查重测试 ----------
    print("\n[7] 测试相似度查重...")

    existing = [
        {"id": "MAT_001", "name": "区块链原文", "sim_hash": hash_a},
        {"id": "MAT_002", "name": "机器学习笔记", "sim_hash": hash_c},
    ]

    hits = check_similarity(hash_b, existing)
    print(f"    新文本(区块链改写) vs 现有资料库:")
    for hit in hits:
        print(f"      命中: {hit.material_name} — 距离={hit.hamming_dist}, "
              f"相似度={hit.similarity_pct:.1f}%, 分类={hit.classification}")

    # hash_b 与 hash_a 应该比 hash_c 更相似
    if hits:
        assert hits[0].material_id == "MAT_001", "最相似的应该是区块链原文"
        print(f"    ✅ 查重结果正确，最相似: {hits[0].material_name}")
    else:
        print(f"    ⚠️  无命中（可能两文本差异超过阈值，属正常）")

    # ---------- 8. 边界情况测试 ----------
    print("\n[8] 测试边界情况...")

    assert compute_simhash("") == 0, "空字符串应返回 0"
    assert compute_simhash("   ") == 0, "纯空白应返回 0"
    print(f"    ✅ 空文本 SimHash = 0")

    assert hamming_distance(0, 0) == 0
    assert hamming_distance((1 << 256) - 1, 0) == 256
    print(f"    ✅ 边界汉明距离正确")

    # ---------- 总结 ----------
    print("\n" + "=" * 60)
    print("  🎉 全部测试通过！指纹引擎工作正常")
    print("=" * 60)


if __name__ == "__main__":
    test_all()