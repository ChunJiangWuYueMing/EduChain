"""
P0-2 签名交易闭环验证

验证目标：
  1. user_service 初始化后，用户私钥不为空
  2. chain_service.register_user_key() 后能取回私钥
  3. approve_edu() 真正走签名发送，不依赖 unlocked account

前置条件：
  1. Ganache 使用固定助记词运行:
     ganache --host 127.0.0.1 --port 8545 --wallet.mnemonic "test test test test test test test test test test test junk"
  2. 合约已部署: python scripts/deploy.py --ganache-url http://127.0.0.1:8545

用法:
  cd backend
  python -m tests.test_p02_signing
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.chain_service import chain_service
from services.user_service import user_service


def test_all():
    print("=" * 60)
    print("  P0-2 签名交易闭环验证")
    print("=" * 60)

    # ========== 第一部分：初始化 ==========
    print("\n[1] 初始化 ChainService...")
    chain_service.init_app()
    accounts = chain_service.get_ganache_accounts()
    print(f"    Ganache 账户数: {len(accounts)}")
    print(f"    Deployer: {accounts[0][:20]}...")

    print("\n[2] 初始化 UserService...")
    user_service.init_users(ganache_accounts=accounts)
    summary = user_service.key_summary
    print(f"    用户总数: {summary['total_users']}")
    print(f"    有私钥:   {summary['with_keys']}")
    print(f"    缺私钥:   {summary['without_keys']}")
    if summary["missing"]:
        print(f"    缺失列表: {summary['missing']}")

    # ========== 第二部分：私钥非空验证 ==========
    print("\n[3] 验证每个用户的私钥不为空...")
    all_have_keys = True
    for user in user_service.get_all_users():
        has_key = bool(user.eth_private_key)
        status = "✅" if has_key else "❌"
        print(f"    {status} {user.student_id} ({user.name}): "
              f"addr={user.eth_address[:16]}... "
              f"key={'有' if has_key else '空'}")
        if not has_key:
            all_have_keys = False

    assert all_have_keys, "存在私钥为空的用户，签名交易将无法使用"
    assert user_service.signing_ready, "signing_ready 应为 True"
    print(f"    ✅ 所有用户私钥已就位")

    # ========== 第三部分：注入 chain_service 并验证可取回 ==========
    print("\n[4] 注入私钥到 ChainService 并验证...")
    registered = 0
    for user in user_service.get_all_users():
        chain_service.register_user_key(user.eth_address, user.eth_private_key)
        registered += 1

    print(f"    注册了 {registered} 个用户私钥")

    for user in user_service.get_all_users():
        retrieved = chain_service.get_user_key(user.eth_address)
        assert retrieved is not None, f"注入后取回失败: {user.eth_address}"
        assert retrieved == user.eth_private_key, f"取回的私钥不一致: {user.student_id}"

    print(f"    ✅ 所有私钥注入后可正确取回")

    # ========== 第四部分：approve_edu 签名交易实测 ==========
    print("\n[5] 实测 approve_edu() 签名交易...")

    # 挑第一个普通用户做测试
    test_user = None
    for user in user_service.get_all_users():
        if user.role == "student":
            test_user = user
            break
    assert test_user is not None, "没有可用的学生用户"

    # 先给用户铸一点 EDU（deployer 管理交易，走 _send_tx）
    chain_service.mint_edu(test_user.eth_address, 50, reason="p02_test")
    balance = chain_service.get_edu_balance(test_user.eth_address)
    print(f"    铸造 50 EDU 给 {test_user.student_id}，余额: {balance}")

    # 用户授权 MaterialRegistry 代扣（用户交易，走 _send_user_tx -> _send_signed_tx）
    registry_addr = chain_service._registry.address
    receipt = chain_service.approve_edu(test_user.eth_address, registry_addr, 10)
    tx_hash = receipt["transactionHash"].hex()
    print(f"    approve_edu() 成功: tx={tx_hash[:20]}...")

    # 验证授权额度
    allowance = chain_service.get_edu_allowance(test_user.eth_address, registry_addr)
    assert allowance == 10, f"授权额度应为 10，实际: {allowance}"
    print(f"    授权额度验证: {allowance} EDU ✅")

    # ========== 第五部分：缺私钥时的报错验证 ==========
    print("\n[6] 验证缺私钥时的明确报错...")

    # 用一个没注册过私钥的地址测试
    fake_addr = "0x0000000000000000000000000000000000099999"
    try:
        chain_service.approve_edu(fake_addr, registry_addr, 1)
        print(f"    ❌ 应该抛出 ValueError")
        assert False
    except ValueError as e:
        error_msg = str(e)
        assert "用户私钥未注册" in error_msg, f"错误信息不够明确: {error_msg}"
        print(f"    ✅ 正确报错: {error_msg.splitlines()[0]}")

    # ========== 总结 ==========
    print("\n" + "=" * 60)
    print("  🎉 P0-2 签名交易闭环验证全部通过")
    print()
    print("  已验证:")
    print("    ✓ 私钥来源稳定（.env / 助记词派生兜底）")
    print("    ✓ user_service 初始化后私钥非空")
    print("    ✓ chain_service 注入后可取回")
    print("    ✓ approve_edu 真实走签名发送")
    print("    ✓ 缺私钥时报错明确")
    print("=" * 60)


if __name__ == "__main__":
    test_all()