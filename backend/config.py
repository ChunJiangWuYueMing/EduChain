"""EduChain 全局配置"""
import os
from dataclasses import dataclass, field


@dataclass
class Config:
    """应用配置（所有链相关参数集中管理）"""

    # --- Flask ---
    SECRET_KEY: str = os.getenv("SECRET_KEY", "educhain-dev-secret-key-change-in-prod")
    DEBUG: bool = os.getenv("FLASK_DEBUG", "1") == "1"

    # --- 文件上传 ---
    UPLOAD_FOLDER: str = os.path.join(os.path.dirname(__file__), "uploads")
    MAX_CONTENT_LENGTH: int = 50 * 1024 * 1024  # 50 MB
    ALLOWED_EXTENSIONS: set = field(default_factory=lambda: {"pdf", "docx", "pptx", "txt", "md"})

    # --- Ganache / Web3 ---
    GANACHE_URL: str = os.getenv("GANACHE_URL", "http://ganache:8545")
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

    # --- SimHash ---
    SIMHASH_TOP_N: int = 200     # 关键词数量
    SIMHASH_SIMILAR_THRESHOLD: int = 3   # 汉明距离 ≤3 判定高度相似
    SIMHASH_DERIVED_THRESHOLD: int = 10  # 汉明距离 4-10 判定衍生版本


config = Config()