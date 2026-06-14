"""EduChain 全局配置"""
import os
from dataclasses import dataclass, field
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def env_bool(name: str, default: bool) -> bool:
    return os.getenv(name, "true" if default else "false").strip().lower() in {
        "1", "true", "yes", "on",
    }


@dataclass
class Config:
    """应用配置（所有链相关参数集中管理）"""

    # --- Flask ---
    SECRET_KEY: str = os.getenv("SECRET_KEY", "educhain-dev-secret-key-change-in-prod")
    DEBUG: bool = env_bool("FLASK_DEBUG", True)
    SERVER_MODE: bool = env_bool("SERVER_MODE", False)
    ALLOW_PUBLIC_REGISTRATION: bool = env_bool("ALLOW_PUBLIC_REGISTRATION", True)
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "")

    # --- 文件上传 ---
    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "uploads"))
    MAX_CONTENT_LENGTH: int = 50 * 1024 * 1024  # 50 MB
    ALLOWED_EXTENSIONS: set = field(default_factory=lambda: {"pdf", "docx", "pptx", "txt", "md"})

    # --- 持久化运行时数据 ---
    USERS_FILE: str = os.getenv("USERS_FILE", str(BASE_DIR / "runtime" / "users.json"))
    USERS_SEED_FILE: str = os.getenv("USERS_SEED_FILE", str(BASE_DIR / "users.seed.json"))
    CONTRACTS_ENV_FILE: str = os.getenv(
        "CONTRACTS_ENV_FILE",
        str(BASE_DIR / ".env"),
    )
    TEST_USER_PASSWORD: str = os.getenv("TEST_USER_PASSWORD", "123456")
    GANACHE_MNEMONIC: str = os.getenv(
        "GANACHE_MNEMONIC",
        "test test test test test test test test test test test junk",
    )

    # --- Ganache / Web3 ---
    GANACHE_URL: str = os.getenv("GANACHE_URL", "http://127.0.0.1:8545")
    CHAIN_ID: int = int(os.getenv("CHAIN_ID", "1337"))

    # 部署合约的账户索引（Ganache 默认 10 个账户，用第 0 个做 owner）
    DEPLOYER_ACCOUNT_INDEX: int = 0

    # --- 合约地址（部署后由 deploy 脚本写入 .env 或环境变量） ---
    EDU_TOKEN_ADDRESS: str = os.getenv("EDU_TOKEN_ADDRESS", "")
    MATERIAL_REGISTRY_ADDRESS: str = os.getenv("MATERIAL_REGISTRY_ADDRESS", "")
    DOWNLOAD_LOG_ADDRESS: str = os.getenv("DOWNLOAD_LOG_ADDRESS", "")

    # --- 通证经济参数 ---
    REGISTER_REWARD: int = 100   # 注册奖励
    UPLOAD_REWARD: int = 20      # 上传奖励（合约内 mint）
    PLAGIARISM_PENALTY: int = 50 # 抄袭扣罚

    # --- SimHash（256 位） ---
    SIMHASH_BITS: int = 256          # 指纹维度
    SIMHASH_TOP_N: int = 200         # 关键词数量
    SIMHASH_SIMILAR_THRESHOLD: int = 12   # 汉明距离 ≤12 判定高度相似
    SIMHASH_DERIVED_THRESHOLD: int = 40   # 汉明距离 13-40 判定衍生版本


config = Config()
