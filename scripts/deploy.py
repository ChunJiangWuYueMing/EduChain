"""
EduChain 合约部署脚本

部署顺序（有依赖关系，不可乱序）:
  1. EduToken              — 独立部署
  2. MaterialRegistry      — 构造函数需要 EduToken 地址
  3. DownloadLog           — 独立部署
  4. 授权 MaterialRegistry  — 调用 EduToken.authorizeMinter
  5. 导出账户私钥          — 从助记词派生，写入 .env 供签名交易使用

用法:
  python scripts/deploy.py [--ganache-url http://127.0.0.1:8545]

  Ganache 启动时必须使用同一个助记词:
  ganache --host 127.0.0.1 --port 8545 --wallet.mnemonic "test test test test test test test test test test test junk"

输出:
  - 控制台打印各合约地址
  - 写入 backend/.env 文件（合约地址 + 账户私钥）
"""

import json
import os
import sys
import argparse
from pathlib import Path
from web3 import Web3

# === 常量 ===
# 项目统一助记词（仅用于开发/测试，Ganache 启动时需使用同一个）
DEFAULT_MNEMONIC = "test test test test test test test test test test test junk"

# === 路径 ===
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
BACKEND_DIR = PROJECT_DIR / "backend"
if not BACKEND_DIR.exists():
    # In Docker, backend/ is mounted directly at /app.
    BACKEND_DIR = PROJECT_DIR
COMPILED_DIR = BACKEND_DIR / "compiled"
DEFAULT_ENV_FILE = Path(
    os.getenv("CONTRACTS_ENV_FILE", str(BACKEND_DIR / ".env"))
)


def load_artifact(contract_name: str) -> dict:
    """加载编译后的合约 ABI + Bytecode"""
    path = COMPILED_DIR / f"{contract_name}.json"
    if not path.exists():
        print(f"❌ 找不到编译产物: {path}")
        print("   请先运行: npm run compile (或 node scripts/compile.js)")
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
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


def derive_keys(mnemonic: str, count: int = 10) -> list[dict]:
    """
    从助记词派生账户地址和私钥（BIP-44 路径，与 Ganache 一致）。

    Returns:
        [{"address": "0x...", "private_key": "0x..."}, ...]
    """
    from eth_account import Account
    Account.enable_unaudited_hdwallet_features()

    keys = []
    for i in range(count):
        acct = Account.from_mnemonic(
            mnemonic,
            account_path=f"m/44'/60'/0'/0/{i}",
        )
        private_key = acct.key.hex()
        if not private_key.startswith("0x"):
            private_key = "0x" + private_key
        keys.append({
            "address": acct.address,
            "private_key": private_key,
        })
    return keys


def main():
    parser = argparse.ArgumentParser(description="部署 EduChain 合约")
    parser.add_argument(
        "--ganache-url",
        default=os.getenv("GANACHE_URL", "http://127.0.0.1:8545"),
        help="Ganache RPC 地址 (默认 http://127.0.0.1:8545)",
    )
    parser.add_argument(
        "--mnemonic",
        default=DEFAULT_MNEMONIC,
        help="Ganache 助记词（必须与 Ganache 启动时一致）",
    )
    parser.add_argument(
        "--env-file",
        default=str(DEFAULT_ENV_FILE),
        help="合约地址和测试私钥配置的写入路径",
    )
    args = parser.parse_args()
    env_file = Path(args.env_file)

    # 连接 Ganache
    w3 = Web3(Web3.HTTPProvider(args.ganache_url))
    if not w3.is_connected():
        print(f"❌ 无法连接 Ganache: {args.ganache_url}")
        print("   请确保 Ganache 已启动")
        sys.exit(1)

    accounts = w3.eth.accounts
    deployer = accounts[0]

    # 从助记词派生私钥
    print("🔑 从助记词派生账户私钥...")
    derived = derive_keys(args.mnemonic, count=len(accounts))

    # 验证派生地址与 Ganache 一致
    for i, d in enumerate(derived):
        if i < len(accounts) and d["address"].lower() != accounts[i].lower():
            print(f"⚠️  账户 {i} 地址不匹配:")
            print(f"   Ganache:  {accounts[i]}")
            print(f"   派生:     {d['address']}")
            print(f"   请确保 Ganache 使用相同助记词启动:")
            print(f'   ganache --wallet.mnemonic "{args.mnemonic}"')
            sys.exit(1)

    print(f"   ✅ {len(derived)} 个账户私钥已派生，与 Ganache 一致")

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

    # --- 写入 .env（合约地址 + 私钥） ---
    # 账户 0 = deployer，账户 1-4 = 用户（与 users.json 对应）
    env_lines = [
        "# EduChain 配置（由 deploy.py 自动生成，请勿手动修改）",
        f"GANACHE_URL={args.ganache_url}",
        f"CHAIN_ID=1337",
        f"EDU_TOKEN_ADDRESS={token_address}",
        f"MATERIAL_REGISTRY_ADDRESS={registry_address}",
        f"DOWNLOAD_LOG_ADDRESS={log_address}",
        f"DEPLOYER_ADDRESS={deployer}",
        f"DEPLOYER_PRIVATE_KEY={derived[0]['private_key']}",
        "",
        "# 用户私钥（账户 1-9，与 users.json 中的用户顺序对应）",
    ]
    for i in range(1, len(derived)):
        env_lines.append(f"ACCOUNT_{i}_ADDRESS={derived[i]['address']}")
        env_lines.append(f"ACCOUNT_{i}_PRIVATE_KEY={derived[i]['private_key']}")

    env_file.parent.mkdir(parents=True, exist_ok=True)
    env_file.write_text("\n".join(env_lines) + "\n", encoding="utf-8")
    print(f"\n📝 合约地址 + 私钥已写入: {env_file}")

    # --- 验证部署 ---
    print("\n🔍 验证部署...")
    decimals = token_contract.functions.decimals().call()
    print(f"   EduToken.decimals() = {decimals} {'✅' if decimals == 0 else '❌'}")

    is_minter = token_contract.functions.authorizedMinters(registry_address).call()
    print(f"   MaterialRegistry 铸造权限 = {is_minter} {'✅' if is_minter else '❌'}")

    registry_contract = w3.eth.contract(address=registry_address, abi=registry_artifact["abi"])
    token_addr_in_registry = registry_contract.functions.eduToken().call()
    print(f"   Registry.eduToken() = {token_addr_in_registry} {'✅' if token_addr_in_registry == token_address else '❌'}")

    print("\n🎉 部署完成！")
    print(f"   Ganache 启动命令（必须使用同一助记词）:")
    print(f'   ganache --host 127.0.0.1 --port 8545 --wallet.mnemonic "{args.mnemonic}"')
    print(f"   启动后端: cd backend && python app.py")


if __name__ == "__main__":
    main()
