"""
chain_service.py — Web3 统一封装层

架构红线：所有 Web3 调用必须通过本模块，路由层禁止直接操作 Web3。

职责：
  1. 管理 Web3 连接和合约实例（单例）
  2. 封装所有合约读写操作
  3. 统一交易发送逻辑（gas、from、receipt 等待）
  4. 将链上原始数据转换为 Python dict
"""

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from web3 import Web3
from web3.contract import Contract

from config import config


# ========== 合约 ABI 加载 ==========

# chain_service.py 在 backend/services/ 下，compiled 在 backend/compiled/ 下
COMPILED_DIR = Path(__file__).parent.parent / "compiled"


def _load_abi(contract_name: str) -> list:
    """加载合约 ABI"""
    path = COMPILED_DIR / f"{contract_name}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"找不到编译产物: {path}\n请先运行: node scripts/compile.js"
        )
    with open(path) as f:
        return json.load(f)["abi"]


# ========== 数据类型 ==========

@dataclass
class MaterialData:
    """链上资料数据的 Python 表示"""
    id: str
    name: str
    course: str
    uploader: str
    sha256_hash: str      # hex string (0x...)
    sim_hash: int         # uint256 SimHash（256 位）
    text_length: int
    policy_type: int      # 0=公开, 1=同课程, 2=指定用户
    policy_value: str
    price: int
    version: int
    deleted: bool
    timestamp: int

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "course": self.course,
            "uploader": self.uploader,
            "sha256_hash": self.sha256_hash,
            "sim_hash": self.sim_hash,
            "text_length": self.text_length,
            "policy_type": self.policy_type,
            "policy_value": self.policy_value,
            "price": self.price,
            "version": self.version,
            "deleted": self.deleted,
            "timestamp": self.timestamp,
        }


@dataclass
class DownloadRecord:
    """链上下载记录的 Python 表示"""
    material_id: str
    downloader: str
    uploader: str
    price: int
    file_hash: str        # hex string (0x...)
    timestamp: int

    def to_dict(self) -> dict:
        return {
            "material_id": self.material_id,
            "downloader": self.downloader,
            "uploader": self.uploader,
            "price": self.price,
            "file_hash": self.file_hash,
            "timestamp": self.timestamp,
        }


# ========== ChainService 主类 ==========

class ChainService:
    """
    链交互统一服务（单例模式）

    用法:
        chain = ChainService()
        chain.init_app()   # 连接 Ganache，实例化合约
        balance = chain.get_edu_balance("0x...")
        chain.register_material(...)
    """

    def __init__(self):
        self.w3: Optional[Web3] = None
        self.deployer: Optional[str] = None
        self.deployer_key: Optional[str] = None  # deployer 私钥（签名部署交易用）

        # 合约实例
        self._token: Optional[Contract] = None
        self._registry: Optional[Contract] = None
        self._download_log: Optional[Contract] = None

        # 用户私钥注册表: address.lower() -> private_key
        # 由 app.py 在初始化 user_service 后注入
        self._user_keys: dict[str, str] = {}

        self._initialized = False

    # ---------- 初始化 ----------

    def init_app(self) -> None:
        """
        初始化 Web3 连接和合约实例。
        需要在 Flask app 创建后、第一次请求前调用。
        """
        if self._initialized:
            return

        # 加载 .env（如果存在）
        # .env 在 backend/ 目录下，chain_service.py 在 backend/services/ 下
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            self._load_env(env_path)

        # 连接 Ganache
        self.w3 = Web3(Web3.HTTPProvider(config.GANACHE_URL))
        if not self.w3.is_connected():
            raise ConnectionError(f"无法连接 Ganache: {config.GANACHE_URL}")

        # 部署者账户
        accounts = self.w3.eth.accounts
        self.deployer = accounts[config.DEPLOYER_ACCOUNT_INDEX]

        # 实例化合约
        self._token = self._get_contract("EduToken", config.EDU_TOKEN_ADDRESS)
        self._registry = self._get_contract("MaterialRegistry", config.MATERIAL_REGISTRY_ADDRESS)
        self._download_log = self._get_contract("DownloadLog", config.DOWNLOAD_LOG_ADDRESS)

        self._initialized = True

    def _load_env(self, env_path: Path) -> None:
        """简易 .env 解析，将值设入 config"""
        import os
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()
        # 重新读取环境变量到 config
        config.GANACHE_URL = os.getenv("GANACHE_URL", config.GANACHE_URL)
        config.EDU_TOKEN_ADDRESS = os.getenv("EDU_TOKEN_ADDRESS", config.EDU_TOKEN_ADDRESS)
        config.MATERIAL_REGISTRY_ADDRESS = os.getenv("MATERIAL_REGISTRY_ADDRESS", config.MATERIAL_REGISTRY_ADDRESS)
        config.DOWNLOAD_LOG_ADDRESS = os.getenv("DOWNLOAD_LOG_ADDRESS", config.DOWNLOAD_LOG_ADDRESS)

    def _get_contract(self, name: str, address: str) -> Contract:
        """根据名称和地址创建合约实例"""
        if not address:
            raise ValueError(
                f"合约地址为空: {name}\n"
                "请先运行 python scripts/deploy.py 部署合约"
            )
        abi = _load_abi(name)
        return self.w3.eth.contract(
            address=Web3.to_checksum_address(address),
            abi=abi,
        )

    def _ensure_init(self) -> None:
        """确保已初始化"""
        if not self._initialized:
            raise RuntimeError("ChainService 未初始化，请先调用 init_app()")

    # ---------- 通用交易发送 ----------

    def _send_tx(self, contract_fn, from_addr: Optional[str] = None, gas: int = 500_000) -> dict:
        """
        发送交易并等待回执（Ganache unlocked account 模式）。

        适用于：deployer/owner 发起的管理交易、Ganache 开发环境。
        """
        sender = from_addr or self.deployer
        tx_hash = contract_fn.transact({
            "from": sender,
            "gas": gas,
        })
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)
        if receipt["status"] != 1:
            raise RuntimeError(f"交易失败: tx={tx_hash.hex()}")
        return dict(receipt)

    def _send_signed_tx(
        self,
        contract_fn,
        private_key: str,
        from_addr: str,
        gas: int = 500_000,
    ) -> dict:
        """
        签名发送交易（私钥签名模式）。

        适用于：用户发起的交易（approve、transfer 等），
        以及未来迁移到真实网络时的统一发送方式。

        Args:
            contract_fn:  已构建的合约函数调用
            private_key:  发送者私钥（hex 字符串，带或不带 0x 前缀）
            from_addr:    发送者地址
            gas:          gas 上限
        """
        nonce = self.w3.eth.get_transaction_count(
            Web3.to_checksum_address(from_addr)
        )
        tx = contract_fn.build_transaction({
            "from": Web3.to_checksum_address(from_addr),
            "gas": gas,
            "gasPrice": self.w3.eth.gas_price,
            "nonce": nonce,
            "chainId": config.CHAIN_ID,
        })
        signed = self.w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)
        if receipt["status"] != 1:
            raise RuntimeError(f"交易失败: tx={tx_hash.hex()}")
        return dict(receipt)

    # ---------- 用户私钥管理 ----------

    def register_user_key(self, address: str, private_key: str) -> None:
        """注册用户私钥（由 app.py 初始化时调用）"""
        self._user_keys[address.lower()] = private_key

    def get_user_key(self, address: str) -> Optional[str]:
        """获取用户私钥"""
        return self._user_keys.get(address.lower())

    def _send_user_tx(self, contract_fn, user_addr: str, gas: int = 500_000) -> dict:
        """
        发送用户侧交易（使用用户私钥签名）。

        适用于：approve、transfer 等必须由代币持有者本人发起的交易。
        与 _send_tx（deployer 管理交易）明确区分。

        Raises:
            ValueError: 用户私钥未注册
        """
        key = self.get_user_key(user_addr)
        if key is None:
            raise ValueError(
                f"用户私钥未注册: {user_addr}\n"
                "请确保 user_service 已初始化并注入私钥到 chain_service"
            )
        return self._send_signed_tx(contract_fn, key, user_addr, gas)

    # ======================================================
    #  EduToken 操作
    # ======================================================

    def get_edu_balance(self, address: str) -> int:
        """查询 EDU 余额"""
        self._ensure_init()
        addr = Web3.to_checksum_address(address)
        return self._token.functions.balanceOf(addr).call()

    def mint_edu(self, to: str, amount: int, reason: str = "mint") -> dict:
        """
        铸造 EDU 通证（仅 deployer/owner 可调用）

        Args:
            to:     接收地址
            amount: 数量
            reason: 原因（register/upload/reward）
        """
        self._ensure_init()
        addr = Web3.to_checksum_address(to)
        fn = self._token.functions.mintWithReason(addr, amount, reason)
        return self._send_tx(fn)

    def burn_edu(self, from_addr: str, amount: int, reason: str = "penalty") -> dict:
        """销毁 EDU（抄袭扣罚等）"""
        self._ensure_init()
        addr = Web3.to_checksum_address(from_addr)
        fn = self._token.functions.burnFrom(addr, amount, reason)
        return self._send_tx(fn)

    def approve_edu(self, owner_addr: str, spender_addr: str, amount: int) -> dict:
        """
        授权代扣（下载前需要下载者授权 MaterialRegistry 合约代扣）。

        使用 owner 的私钥签名，因为只有代币持有者本人能授权。
        """
        self._ensure_init()
        owner_ck = Web3.to_checksum_address(owner_addr)
        spender_ck = Web3.to_checksum_address(spender_addr)
        fn = self._token.functions.approve(spender_ck, amount)
        return self._send_user_tx(fn, owner_ck)

    def get_edu_allowance(self, owner_addr: str, spender_addr: str) -> int:
        """查询授权额度"""
        self._ensure_init()
        return self._token.functions.allowance(
            Web3.to_checksum_address(owner_addr),
            Web3.to_checksum_address(spender_addr),
        ).call()

    def transfer_edu(self, from_addr: str, to_addr: str, amount: int) -> dict:
        """直接转账 EDU（使用发送者私钥签名）"""
        self._ensure_init()
        from_ck = Web3.to_checksum_address(from_addr)
        fn = self._token.functions.transfer(
            Web3.to_checksum_address(to_addr), amount
        )
        return self._send_user_tx(fn, from_ck)

    # ======================================================
    #  MaterialRegistry 操作
    # ======================================================

    def register_material(
        self,
        material_id: str,
        name: str,
        course: str,
        uploader: str,
        sha256_hash: bytes,
        sim_hash: int,
        text_length: int,
        policy_type: int,
        policy_value: str,
        price: int,
    ) -> dict:
        """
        注册资料上链（同时自动铸造 20 EDU 给上传者）

        Args:
            material_id: 后端生成的唯一 ID
            sha256_hash: 32 字节的 SHA-256 哈希（bytes）
            sim_hash:    256 位 SimHash 整数
            其余参数见 MaterialRegistry.register
        """
        self._ensure_init()
        fn = self._registry.functions.register(
            material_id,
            name,
            course,
            Web3.to_checksum_address(uploader),
            sha256_hash,        # bytes32
            sim_hash,           # uint256
            text_length,        # uint32
            policy_type,        # uint8
            policy_value,
            price,
        )
        return self._send_tx(fn, gas=1_000_000)

    def query_material(self, material_id: str) -> Optional[MaterialData]:
        """查询链上资料详情"""
        self._ensure_init()
        try:
            raw = self._registry.functions.query(material_id).call()
        except Exception as e:
            error_msg = str(e)
            # 仅对合约明确的 "material not found" revert 返回 None
            if "MaterialRegistry: material not found" in error_msg:
                return None
            # 其他异常（ABI 不匹配、节点故障、EVM 错误等）向上抛出
            raise
        return self._parse_material(raw)

    def update_material(
        self,
        material_id: str,
        new_sha256_hash: bytes,
        new_sim_hash: int,
        new_text_length: int,
    ) -> dict:
        """更新资料版本"""
        self._ensure_init()
        fn = self._registry.functions.update(
            material_id, new_sha256_hash, new_sim_hash, new_text_length
        )
        return self._send_tx(fn)

    def download_material(self, material_id: str, downloader: str) -> dict:
        """
        下载资料（通证转移）

        调用前需确保：
          1. downloader 余额 >= price
          2. downloader 已 approve MaterialRegistry 合约足够额度
        """
        self._ensure_init()
        dl_addr = Web3.to_checksum_address(downloader)

        # 查询资料价格并自动处理 approve
        material = self.query_material(material_id)
        if material is None:
            raise ValueError(f"资料不存在: {material_id}")
        if material.deleted:
            raise ValueError(f"资料已删除: {material_id}")
        if material.price > 0:
            registry_addr = self._registry.address
            current_allowance = self.get_edu_allowance(dl_addr, registry_addr)
            if current_allowance < material.price:
                self.approve_edu(dl_addr, registry_addr, material.price)

        fn = self._registry.functions.download(material_id, dl_addr)
        return self._send_tx(fn)

    def soft_delete_material(self, material_id: str, caller: str) -> dict:
        """软删除资料"""
        self._ensure_init()
        fn = self._registry.functions.softDelete(
            material_id, Web3.to_checksum_address(caller)
        )
        return self._send_tx(fn)

    def get_material_count(self) -> int:
        """获取资料总数"""
        self._ensure_init()
        return self._registry.functions.getMaterialCount().call()

    def get_material_by_hash(self, sha256_hash: bytes) -> str:
        """通过 SHA-256 查询资料 ID（查重用）"""
        self._ensure_init()
        return self._registry.functions.getMaterialByHash(sha256_hash).call()

    # ======================================================
    #  DownloadLog 操作
    # ======================================================

    def record_download(
        self,
        material_id: str,
        downloader: str,
        uploader: str,
        price: int,
        file_hash: bytes,
    ) -> dict:
        """记录下载日志"""
        self._ensure_init()
        fn = self._download_log.functions.recordDownload(
            material_id,
            Web3.to_checksum_address(downloader),
            Web3.to_checksum_address(uploader),
            price,
            file_hash,
        )
        return self._send_tx(fn)

    def get_downloads_by_material(self, material_id: str) -> list[DownloadRecord]:
        """按资料 ID 查询下载记录"""
        self._ensure_init()
        raw_list = self._download_log.functions.queryByMaterial(material_id).call()
        return [self._parse_download_record(r) for r in raw_list]

    def get_downloads_by_user(self, downloader: str) -> list[DownloadRecord]:
        """按下载者地址查询下载记录"""
        self._ensure_init()
        addr = Web3.to_checksum_address(downloader)
        raw_list = self._download_log.functions.queryByDownloader(addr).call()
        return [self._parse_download_record(r) for r in raw_list]

    def get_download_count(self) -> int:
        """获取总下载记录数"""
        self._ensure_init()
        return self._download_log.functions.getRecordCount().call()

    # ======================================================
    #  辅助方法
    # ======================================================

    def get_ganache_accounts(self) -> list[str]:
        """获取 Ganache 所有测试账户"""
        self._ensure_init()
        return self.w3.eth.accounts

    def get_eth_balance(self, address: str) -> float:
        """获取 ETH 余额（ether 单位）"""
        self._ensure_init()
        wei = self.w3.eth.get_balance(Web3.to_checksum_address(address))
        return float(self.w3.from_wei(wei, "ether"))

    def get_block_number(self) -> int:
        """当前区块号"""
        self._ensure_init()
        return self.w3.eth.block_number

    def is_connected(self) -> bool:
        """Ganache 是否连通"""
        if self.w3 is None:
            return False
        return self.w3.is_connected()

    @staticmethod
    def _parse_material(raw: tuple) -> MaterialData:
        """将合约返回的 tuple 转换为 MaterialData"""
        # Solidity struct 按定义顺序返回 tuple
        return MaterialData(
            id=raw[0],
            name=raw[1],
            course=raw[2],
            uploader=raw[3],
            sha256_hash=raw[4].hex() if isinstance(raw[4], bytes) else raw[4],
            sim_hash=raw[5],
            text_length=raw[6],
            policy_type=raw[7],
            policy_value=raw[8],
            price=raw[9],
            version=raw[10],
            deleted=raw[11],
            timestamp=raw[12],
        )

    @staticmethod
    def _parse_download_record(raw: tuple) -> DownloadRecord:
        """将合约返回的 tuple 转换为 DownloadRecord"""
        return DownloadRecord(
            material_id=raw[0],
            downloader=raw[1],
            uploader=raw[2],
            price=raw[3],
            file_hash=raw[4].hex() if isinstance(raw[4], bytes) else raw[4],
            timestamp=raw[5],
        )


# ========== 全局单例 ==========
chain_service = ChainService()