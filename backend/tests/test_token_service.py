"""
token_service 业务逻辑测试

测试纯通证操作：注册奖励、抄袭扣罚、交易历史。
下载扣费测试已迁至 material_service 测试。

用法:
  cd backend
  python -m tests.test_token_service
"""

import sys
import os
import hashlib
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.chain_service import chain_service
from services.token_service import token_service


def test_all():
    material_id = f"MAT_TOKEN_TEST_{time.time_ns()}"

    print("=" * 60)
    print("  EduChain token_service 业务逻辑测试")
    print("=" * 60)

    # 初始化
    chain_service.init_app()
    accounts = chain_service.get_ganache_accounts()
    user_c = accounts[3]
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

    # ---------- 抄袭扣罚 ----------
    print("\n[2] 测试抄袭扣罚...")
    # 先注册一个资料供扣罚引用
    content = f"Token service test material content: {material_id}".encode()
    sha256_hash = hashlib.sha256(content).digest()
    chain_service.register_material(
        material_id=material_id,
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

    bal_before = token_service.get_balance(user_c)
    result = token_service.penalize_plagiarism(user_c, material_id)
    bal_after = token_service.get_balance(user_c)
    print(f"    UserC: {bal_before} → {bal_after} EDU（-{result['amount']} 扣罚）")
    print(f"    ✅ 扣罚完成")

    # ---------- 余额为零时扣罚 ----------
    print("\n[3] 测试余额不足时扣罚...")
    remaining = token_service.get_balance(user_d)
    if remaining > 0:
        chain_service.burn_edu(user_d, remaining, "test_drain")
    result = token_service.penalize_plagiarism(user_d, material_id)
    assert result["amount"] == 0
    print(f"    ✅ 余额为 0，扣罚 0 EDU: {result['note']}")

    # ---------- 交易历史 ----------
    print("\n[4] 测试交易历史查询...")
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
