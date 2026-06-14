"""
chain_service 端到端冒烟测试

前置条件:
  1. Ganache 运行中（localhost:8545）
  2. 合约已编译（node scripts/compile.js）
  3. 合约已部署（python scripts/deploy.py）
  4. backend/.env 已生成

用法:
  cd backend
  python -m tests.test_chain_service
  或:
  cd educhain
  python -m backend.tests.test_chain_service
"""

import sys
import os
import hashlib
import time

# 确保能 import backend 包
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.chain_service import chain_service


def test_all():
    material_id = f"MAT_TEST_{time.time_ns()}"

    print("=" * 60)
    print("  EduChain chain_service 冒烟测试")
    print("=" * 60)

    # ---------- 初始化 ----------
    print("\n[1] 初始化 ChainService...")
    chain_service.init_app()
    print(f"    ✅ 已连接 Ganache, 区块号: {chain_service.get_block_number()}")

    accounts = chain_service.get_ganache_accounts()
    deployer = accounts[0]
    user_a = accounts[1]   # 模拟上传者
    user_b = accounts[2]   # 模拟下载者
    print(f"    Deployer: {deployer}")
    print(f"    UserA (上传者): {user_a}")
    print(f"    UserB (下载者): {user_b}")

    # ---------- 铸造测试 ----------
    print("\n[2] 测试注册奖励铸造（mint 100 EDU 给 UserA）...")
    chain_service.mint_edu(user_a, 100, reason="register")
    balance_a = chain_service.get_edu_balance(user_a)
    assert balance_a >= 100, f"余额不对: {balance_a}"
    print(f"    ✅ UserA 余额: {balance_a} EDU")

    print("    铸造 100 EDU 给 UserB（模拟注册）...")
    chain_service.mint_edu(user_b, 100, reason="register")
    balance_b = chain_service.get_edu_balance(user_b)
    print(f"    ✅ UserB 余额: {balance_b} EDU")

    # ---------- 资料注册测试 ----------
    print("\n[3] 测试资料注册上链...")
    test_content = (
        f"This is a test document content for EduChain: {material_id}"
    ).encode()
    sha256_hash = hashlib.sha256(test_content).digest()  # 32 bytes
    sim_hash = 0xABCDEF1234567890  # 模拟 SimHash

    chain_service.register_material(
        material_id=material_id,
        name="数据结构期末复习笔记",
        course="CS201",
        uploader=user_a,
        sha256_hash=sha256_hash,
        sim_hash=sim_hash,
        text_length=len(test_content),
        policy_type=0,          # 公开
        policy_value="",
        price=10,               # 下载需 10 EDU
    )
    print(f"    ✅ 资料注册成功")

    # 验证上传奖励（register 内部 mint 20 EDU）
    balance_a_after = chain_service.get_edu_balance(user_a)
    print(f"    UserA 余额: {balance_a} → {balance_a_after} EDU（+20 上传奖励）")
    assert balance_a_after == balance_a + 20, f"上传奖励未到账: {balance_a_after}"

    # ---------- 资料查询测试 ----------
    print("\n[4] 测试链上资料查询...")
    material = chain_service.query_material(material_id)
    assert material is not None, "查询失败"
    assert material.name == "数据结构期末复习笔记"
    assert material.course == "CS201"
    assert material.price == 10
    assert material.version == 1
    assert not material.deleted
    print(f"    ✅ 查询成功: {material.name}")
    print(f"       课程={material.course}, 价格={material.price} EDU, 版本={material.version}")
    print(f"       SimHash={hex(material.sim_hash)}")

    # SHA-256 查重测试
    dup_id = chain_service.get_material_by_hash(sha256_hash)
    assert dup_id == material_id, f"查重失败: {dup_id}"
    print(f"    ✅ SHA-256 查重命中: {dup_id}")

    count = chain_service.get_material_count()
    print(f"    ✅ 资料总数: {count}")

    # ---------- 下载测试 ----------
    print("\n[5] 测试下载（UserB 下载 UserA 的资料，扣 10 EDU）...")
    balance_b_before = chain_service.get_edu_balance(user_b)
    balance_a_before = chain_service.get_edu_balance(user_a)

    chain_service.download_material(material_id, user_b)

    balance_b_after = chain_service.get_edu_balance(user_b)
    balance_a_after2 = chain_service.get_edu_balance(user_a)

    print(f"    UserB: {balance_b_before} → {balance_b_after} EDU（-10）")
    print(f"    UserA: {balance_a_before} → {balance_a_after2} EDU（+10）")
    assert balance_b_after == balance_b_before - 10
    assert balance_a_after2 == balance_a_before + 10
    print(f"    ✅ 通证转移正确")

    # ---------- 下载日志测试 ----------
    print("\n[6] 测试下载日志记录...")
    chain_service.record_download(
        material_id=material_id,
        downloader=user_b,
        uploader=user_a,
        price=10,
        file_hash=sha256_hash,
    )

    logs = chain_service.get_downloads_by_material(material_id)
    assert len(logs) >= 1, f"日志为空"
    print(f"    ✅ 资料下载记录: {len(logs)} 条")
    print(f"       最近: downloader={logs[0].downloader[:10]}..., price={logs[0].price}")

    user_logs = chain_service.get_downloads_by_user(user_b)
    print(f"    ✅ UserB 下载记录: {len(user_logs)} 条")

    # ---------- 版本更新测试 ----------
    print("\n[7] 测试资料版本更新...")
    new_content = b"Updated document content v2."
    new_hash = hashlib.sha256(new_content).digest()
    new_simhash = 0xABCDEF1234567899

    chain_service.update_material(
        material_id=material_id,
        new_sha256_hash=new_hash,
        new_sim_hash=new_simhash,
        new_text_length=len(new_content),
    )

    updated = chain_service.query_material(material_id)
    assert updated.version == 2
    print(f"    ✅ 版本更新: v{updated.version}")

    # ---------- 销毁测试 ----------
    print("\n[8] 测试通证销毁（模拟抄袭扣罚 50 EDU）...")
    bal_before = chain_service.get_edu_balance(user_a)
    chain_service.burn_edu(user_a, 50, reason=f"plagiarism:{material_id}")
    bal_after = chain_service.get_edu_balance(user_a)
    print(f"    UserA: {bal_before} → {bal_after} EDU（-50 扣罚）")
    assert bal_after == bal_before - 50
    print(f"    ✅ 销毁成功")

    # ---------- 软删除测试 ----------
    print("\n[9] 测试软删除...")
    chain_service.soft_delete_material(material_id, user_a)
    deleted = chain_service.query_material(material_id)
    assert deleted.deleted is True
    print(f"    ✅ 软删除成功: deleted={deleted.deleted}")

    # ---------- 总结 ----------
    print("\n" + "=" * 60)
    print("  🎉 全部测试通过！chain_service 工作正常")
    print("=" * 60)
    print(f"\n  最终状态:")
    print(f"    区块号: {chain_service.get_block_number()}")
    print(f"    资料总数: {chain_service.get_material_count()}")
    print(f"    下载记录: {chain_service.get_download_count()}")
    print(f"    UserA 余额: {chain_service.get_edu_balance(user_a)} EDU")
    print(f"    UserB 余额: {chain_service.get_edu_balance(user_b)} EDU")


if __name__ == "__main__":
    test_all()
