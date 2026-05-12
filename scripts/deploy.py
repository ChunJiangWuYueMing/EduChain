"""
EduChain 合约部署脚本

部署顺序（有依赖关系，不可乱序）:
  1. EduToken              — 独立部署
  2. MaterialRegistry      — 构造函数需要 EduToken 地址
  3. DownloadLog           — 独立部署
  4. 授权 MaterialRegistry  — 调用 EduToken.authorizeMinter

用法:
  python scripts/deploy.py [--ganache-url http://127.0.0.1:8545]

输出:
  - 控制台打印各合约地址
  - 写入 backend/.env 文件供 Flask 读取
"""

import json
import os
import sys
import argparse
from pathlib import Path
from web3 import Web3

# === 路径 ===
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
COMPILED_DIR = PROJECT_DIR / "backend" / "compiled"
ENV_FILE = PROJECT_DIR / "backend" / ".env"


def load_artifact(contract_name: str) -> dict:
    """加载编译后的合约 ABI + Bytecode"""
    path = COMPILED_DIR / f"{contract_name}.json"
    if not path.exists():
        print(f"❌ 找不到编译产物: {path}")
        print("   请先运行: npm run compile (或 node scripts/compile.js)")
        sys.exit(1)
    with open(path) as f:
        return json.load(f)


def deploy_contract(w3: Web3, account: str, artifact: dict, *constructor_args) -> str:
    """部署合约并返回地址"""
    contract = w3.eth.contract(
        abi=artifact["abi"],
        bytecode=artifact["bytecode"],
    )
    tx_hash = contract.constructor(*constructor_args).transact({
        "from": account,
        "gas": 6_000_000,
    })
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)

    if receipt["status"] != 1:
        print(f"❌ 部署失败: {artifact['contractName']}")
        sys.exit(1)

    return receipt["contractAddress"]


def main():
    parser = argparse.ArgumentParser(description="部署 EduChain 合约")
    parser.add_argument(
        "--ganache-url",
        default=os.getenv("GANACHE_URL", "http://127.0.0.1:8545"),
        help="Ganache RPC 地址 (默认 http://127.0.0.1:8545)",
    )
    args = parser.parse_args()

    # 连接 Ganache
    w3 = Web3(Web3.HTTPProvider(args.ganache_url))
    if not w3.is_connected():
        print(f"❌ 无法连接 Ganache: {args.ganache_url}")
        print("   请确保 Ganache 已启动")
        sys.exit(1)

    accounts = w3.eth.accounts
    deployer = accounts[0]  # 第 0 个账户作为部署者/owner
    print(f"🔗 已连接 Ganache: {args.ganache_url}")
    print(f"👤 部署账户: {deployer}")
    print(f"💰 账户余额: {w3.from_wei(w3.eth.get_balance(deployer), 'ether')} ETH")
    print()

    # --- 1. 部署 EduToken ---
    print("📦 [1/4] 部署 EduToken...")
    token_artifact = load_artifact("EduToken")
    token_address = deploy_contract(w3, deployer, token_artifact)
    print(f"   ✅ EduToken: {token_address}")

    # --- 2. 部署 MaterialRegistry ---
    print("📦 [2/4] 部署 MaterialRegistry...")
    registry_artifact = load_artifact("MaterialRegistry")
    registry_address = deploy_contract(w3, deployer, registry_artifact, token_address)
    print(f"   ✅ MaterialRegistry: {registry_address}")

    # --- 3. 部署 DownloadLog ---
    print("📦 [3/4] 部署 DownloadLog...")
    log_artifact = load_artifact("DownloadLog")
    log_address = deploy_contract(w3, deployer, log_artifact)
    print(f"   ✅ DownloadLog: {log_address}")

    # --- 4. 授权 MaterialRegistry 为 EduToken 的铸造者 ---
    print("🔑 [4/4] 授权 MaterialRegistry 铸造权限...")
    token_contract = w3.eth.contract(address=token_address, abi=token_artifact["abi"])
    tx_hash = token_contract.functions.authorizeMinter(registry_address).transact({
        "from": deployer,
        "gas": 100_000,
    })
    w3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)
    print(f"   ✅ MaterialRegistry 已获得铸造权限")

    # --- 写入 .env ---
    env_content = f"""# EduChain 合约地址（由 deploy.py 自动生成，请勿手动修改）
GANACHE_URL={args.ganache_url}
CHAIN_ID=1337
EDU_TOKEN_ADDRESS={token_address}
MATERIAL_REGISTRY_ADDRESS={registry_address}
DOWNLOAD_LOG_ADDRESS={log_address}
DEPLOYER_ADDRESS={deployer}
"""
    ENV_FILE.write_text(env_content)
    print(f"\n📝 合约地址已写入: {ENV_FILE}")

    # --- 验证部署 ---
    print("\n🔍 验证部署...")
    decimals = token_contract.functions.decimals().call()
    print(f"   EduToken.decimals() = {decimals} {'✅' if decimals == 0 else '❌'}")

    is_minter = token_contract.functions.authorizedMinters(registry_address).call()
    print(f"   MaterialRegistry 铸造权限 = {is_minter} {'✅' if is_minter else '❌'}")

    registry_contract = w3.eth.contract(address=registry_address, abi=registry_artifact["abi"])
    token_addr_in_registry = registry_contract.functions.eduToken().call()
    print(f"   Registry.eduToken() = {token_addr_in_registry} {'✅' if token_addr_in_registry == token_address else '❌'}")

    print("\n🎉 部署完成！可以启动后端了: cd backend && python app.py")


if __name__ == "__main__":
    main()
