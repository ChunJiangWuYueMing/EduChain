"""Initialize the nine fixed course-test users from the seed file."""

import argparse
import os
import sys
from pathlib import Path

from web3 import Web3


PROJECT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_DIR / "backend"
if not BACKEND_DIR.exists():
    BACKEND_DIR = PROJECT_DIR
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from config import config  # noqa: E402
from services.user_service import UserService  # noqa: E402


def short_address(address: str) -> str:
    return f"{address[:8]}...{address[-6:]}"


def main() -> int:
    parser = argparse.ArgumentParser(description="初始化 EduChain 联动测试账号")
    parser.add_argument(
        "--force",
        action="store_true",
        help="覆盖已有运行时用户文件并恢复统一测试密码",
    )
    args = parser.parse_args()

    if args.force:
        print("WARNING: --force 将覆盖运行时用户账号文件，但不会重置链上余额。")

    web3 = Web3(Web3.HTTPProvider(config.GANACHE_URL))
    if not web3.is_connected():
        print(f"ERROR: 无法连接 Ganache: {config.GANACHE_URL}")
        return 1

    accounts = list(web3.eth.accounts)
    service = UserService()
    created = service.initialize_runtime_users(
        ganache_accounts=accounts,
        force=args.force,
    )
    service.init_users(ganache_accounts=accounts)

    print("账号已初始化" if not created else "已创建9个联动测试账号")
    for user in service.get_all_users():
        print(
            f"  [{user.account_index}] {user.student_id} "
            f"{user.name} {user.role} {short_address(user.eth_address)}"
        )
    summary = service.get_summary()
    print(
        "检查结果: "
        f"users={summary['users_count']}, "
        f"students={summary['student_count']}, "
        f"admins={summary['admin_count']}, "
        f"wallets={summary['wallets_ready']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
