"""Read-only health check for the shared EduChain test environment."""

import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_DIR / "backend"
if not BACKEND_DIR.exists():
    BACKEND_DIR = PROJECT_DIR
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from config import config  # noqa: E402
from services.chain_service import chain_service  # noqa: E402
from services.user_service import user_service  # noqa: E402


def short_address(address: str) -> str:
    return f"{address[:8]}...{address[-6:]}"


def main() -> int:
    chain_service.init_app()
    accounts = chain_service.get_ganache_accounts()
    user_service.init_users(accounts)

    summary = user_service.get_summary()
    print("EduChain test environment")
    print(f"  chain_id: {chain_service.get_chain_id()}")
    print(f"  block_number: {chain_service.get_block_number()}")
    print(f"  users: {summary['users_count']}")
    print(f"  students: {summary['student_count']}")
    print(f"  admins: {summary['admin_count']}")
    print(f"  wallets_ready: {summary['wallets_ready']}")
    print(f"  material_count: {chain_service.get_material_count()}")
    print(f"  download_count: {chain_service.get_download_count()}")
    print("  contracts:")
    print(f"    EduToken: {config.EDU_TOKEN_ADDRESS or 'not configured'}")
    print(f"    MaterialRegistry: {config.MATERIAL_REGISTRY_ADDRESS or 'not configured'}")
    print(f"    DownloadLog: {config.DOWNLOAD_LOG_ADDRESS or 'not configured'}")
    print("  accounts:")
    for user in user_service.get_all_users():
        balance = chain_service.get_edu_balance(user.eth_address)
        print(
            f"    {user.student_id}: {short_address(user.eth_address)}, "
            f"{balance} EDU"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
