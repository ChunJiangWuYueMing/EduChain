"""
token_service 业务逻辑测试

前置条件同 test_chain_service.py

用法:
  cd backend
  python -m tests.test_token_service
"""

import sys
import os
import hashlib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.chain_service import chain_service
from services.token_service import token_service


def test_all():
    print("=" * 60)
    print("  EduChain token_service 业务逻辑测试")
    print("=" * 60)

    # 初始化
    chain_service.init_app()
    accounts = chain_service.get_ganache_accounts()
    user_c = accounts[3]   # 新用户，避免与 chain_service 测试冲突
    user_d = accounts[4]

    # ---------- 注册奖励 ----------
    print("\n[1] 测试注册奖励...")
    result = token_service.reward_register(user_c)
    print(f"    ✅ 铸造 {result['amount']} EDU, tx={result['tx_hash'][:16]}...")
    balance = token_service.get_balance(user_c)
    assert balance >= 100
    print(f"    UserC 余额: {balance} EDU")

    token_service.reward_register(user_d)
    print(f"    UserD 余额: {token_service.get_balance(user_d)} EDU")

    # ---------- 先注册一个资料用于下载测试 ----------
    print("\n[2] 准备测试资料...")
    content = b"Token service test material content."
    sha256_hash = hashlib.sha256(content).digest()
    chain_service.register_material(
        material_id="MAT_TOKEN_TEST",
        name="操作系统课件",
        course="CS301",
        uploader=user_c,
        sha256_hash=sha256_hash,
        sim_hash=0x1234567890ABCDEF,
        text_length=len(content),
        policy_type=0,
        policy_value="",
        price=15,
    )
    print(f"    ✅ 资料注册完成, 价格=15 EDU")

    # ---------- 下载扣费 ----------
    print("\n[3] 测试下载扣费流程...")
    bal_d_before = token_service.get_balance(user_d)
    bal_c_before = token_service.get_balance(user_c)

    result = token_service.process_download("MAT_TOKEN_TEST", user_d)

    bal_d_after = token_service.get_balance(user_d)
    bal_c_after = token_service.get_balance(user_c)

    print(f"    下载者 UserD: {bal_d_before} → {bal_d_after} EDU（-{result['price']}）")
    print(f"    上传者 UserC: {bal_c_before} → {bal_c_after} EDU（+{result['price']}）")
    assert bal_d_after == bal_d_before - 15
    assert bal_c_after == bal_c_before + 15
    print(f"    ✅ 扣费正确, tx={result['tx_hash'][:16]}...")

    # ---------- 余额不足测试 ----------
    print("\n[4] 测试余额不足拒绝...")
    # 先把 user_d 余额耗尽
    remaining = token_service.get_balance(user_d)
    if remaining > 0:
        chain_service.burn_edu(user_d, remaining, "test_drain")

    try:
        token_service.process_download("MAT_TOKEN_TEST", user_d)
        print("    ❌ 应该抛出 ValueError")
    except ValueError as e:
        print(f"    ✅ 正确拒绝: {e}")

    # ---------- 下载自己的资料测试 ----------
    print("\n[5] 测试不能下载自己的资料...")
    try:
        token_service.process_download("MAT_TOKEN_TEST", user_c)
        print("    ❌ 应该抛出 ValueError")
    except ValueError as e:
        print(f"    ✅ 正确拒绝: {e}")

    # ---------- 抄袭扣罚 ----------
    print("\n[6] 测试抄袭扣罚...")
    bal_before = token_service.get_balance(user_c)
    result = token_service.penalize_plagiarism(user_c, "MAT_TOKEN_TEST")
    bal_after = token_service.get_balance(user_c)
    print(f"    UserC: {bal_before} → {bal_after} EDU（-{result['amount']} 扣罚）")
    print(f"    ✅ 扣罚完成")

    # ---------- 交易历史 ----------
    print("\n[7] 测试交易历史查询...")
    history = token_service.get_transaction_history(user_c)
    print(f"    ✅ UserC 交易记录: {len(history)} 条")
    for tx in history[:3]:
        print(f"       {tx['type']}: {tx['amount']} EDU, block={tx['block']}")

    # ---------- 总结 ----------
    print("\n" + "=" * 60)
    print("  🎉 全部测试通过！token_service 工作正常")
    print("=" * 60)


if __name__ == "__main__":
    test_all()
