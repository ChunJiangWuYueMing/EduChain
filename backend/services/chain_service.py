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
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import urlsplit, urlunsplit

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
    with open(path, encoding="utf-8") as f:
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
        # 课程名称映射
        course_names = {
            "CS201": "数据结构", "CS301": "操作系统",
            "CS302": "计算机网络", "MATH101": "高等数学", "PHY101": "大学物理",
        }
        return {
            "id": self.id,
            "name": self.name,
            "course": self.course,
            "course_name": course_names.get(self.course, ""),
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


@dataclass
class UpdateRecord:
    """资料修改记录"""
    material_id: str
    new_version: int
    new_sha256_hash: str
    new_sim_hash: int
    timestamp: int

    def to_dict(self) -> dict:
        return {
            "material_id": self.material_id,
            "new_version": self.new_version,
            "new_sha256_hash": self.new_sha256_hash,
            "new_sim_hash": self.new_sim_hash,
            "timestamp": self.timestamp,
        }


@dataclass
class DeleteRecord:
    """资料删除记录"""
    material_id: str
    caller: str
    timestamp: int

    def to_dict(self) -> dict:
        return {
            "material_id": self.material_id,
            "caller": self.caller,
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

        # 连接 Ganache。Windows 本地迁移时，旧配置里常保留 Docker 主机名 `ganache`，
        # 这里会自动回退到本机回环地址，避免必须手动改 .env 才能启动。
        self.w3 = self._connect_ganache()

        # 部署者账户
        accounts = self.w3.eth.accounts
        self.deployer = accounts[config.DEPLOYER_ACCOUNT_INDEX]

        # 实例化合约
        self._token = self._get_contract("EduToken", config.EDU_TOKEN_ADDRESS)
        self._registry = self._get_contract("MaterialRegistry", config.MATERIAL_REGISTRY_ADDRESS)
        self._download_log = self._get_contract("DownloadLog", config.DOWNLOAD_LOG_ADDRESS)

        self._initialized = True

    def _connect_ganache(self) -> Web3:
        """按候选地址尝试连接 Ganache，优先使用显式配置，其次回退到本机地址。"""
        attempted_urls: list[str] = []
        for candidate_url in self._candidate_ganache_urls(config.GANACHE_URL):
            attempted_urls.append(candidate_url)
            w3 = Web3(Web3.HTTPProvider(candidate_url))
            if w3.is_connected():
                config.GANACHE_URL = candidate_url
                os.environ["GANACHE_URL"] = candidate_url
                return w3

        attempted = ", ".join(attempted_urls)
        raise ConnectionError(f"无法连接 Ganache，已尝试: {attempted}")

    @staticmethod
    def _candidate_ganache_urls(primary_url: str) -> list[str]:
        """生成 Ganache RPC 候选地址，兼容 Docker 主机名与 Windows 本地回环地址。"""
        candidates: list[str] = []

        def add(url: str) -> None:
            if url and url not in candidates:
                candidates.append(url)

        add(primary_url)
        parsed = urlsplit(primary_url)
        host = parsed.hostname

        if not host:
            add("http://127.0.0.1:8545")
            return candidates

        if host == "ganache":
            add(ChainService._replace_url_host(primary_url, "127.0.0.1"))
            add(ChainService._replace_url_host(primary_url, "localhost"))
        elif host == "localhost":
            add(ChainService._replace_url_host(primary_url, "127.0.0.1"))
        elif host == "127.0.0.1":
            add(ChainService._replace_url_host(primary_url, "localhost"))

        return candidates

    @staticmethod
    def _replace_url_host(url: str, host: str) -> str:
        """保留协议、端口和路径，仅替换 URL 主机名。"""
        parsed = urlsplit(url)
        auth = ""
        if parsed.username:
            auth = parsed.username
            if parsed.password:
                auth = f"{auth}:{parsed.password}"
            auth = f"{auth}@"

        netloc = f"{auth}{host}"
        if parsed.port:
            netloc = f"{netloc}:{parsed.port}"

        return urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))

    def _load_env(self, env_path: Path) -> None:
        """
        简易 .env 解析，将值设入 config。

        保护已存在的环境变量（如 Docker Compose 注入的 GANACHE_URL），
        不被 .env 文件覆盖。.env 仅补充未被设置的变量。
        """
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    # 不覆盖已存在的环境变量（Docker Compose 注入优先）
                    if key not in os.environ:
                        os.environ[key] = value.strip()
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
        raw_tx = getattr(signed, "raw_transaction", None)
        if raw_tx is None:
            raw_tx = getattr(signed, "rawTransaction", None)
        if raw_tx is None:
            raise AttributeError("SignedTransaction 缺少 raw transaction 字段")

        tx_hash = self.w3.eth.send_raw_transaction(raw_tx)
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

    def get_all_downloads(self) -> list[DownloadRecord]:
        """读取全部下载记录，供管理员全局审计使用。"""
        self._ensure_init()
        count = self.get_download_count()
        records = []
        for index in range(count):
            raw = self._download_log.functions.allRecords(index).call()
            records.append(self._parse_download_record(raw))
        return records

    def get_download_count(self) -> int:
        """获取总下载记录数"""
        self._ensure_init()
        return self._download_log.functions.getRecordCount().call()

    # ======================================================
    #  修改/删除事件查询
    # ======================================================

    def get_updates_by_material(self, material_id: str) -> list[UpdateRecord]:
        """查询资料的修改记录（从 MaterialUpdated 事件，客户端过滤）"""
        self._ensure_init()
        try:
            target = Web3.keccak(text=material_id).hex()
            events = self._registry.events.MaterialUpdated.get_logs(from_block=0)
            records = []
            for ev in events:
                ev_id = ev.args.id.hex() if isinstance(ev.args.id, bytes) else ev.args.id
                if ev_id == target:
                    records.append(UpdateRecord(
                        material_id=material_id,
                        new_version=ev.args.newVersion,
                        new_sha256_hash="0x" + ev.args.newSha256Hash.hex(),
                        new_sim_hash=ev.args.newSimHash,
                        timestamp=ev.args.timestamp,
                    ))
            return records
        except Exception:
            return []

    def get_deletions_by_material(self, material_id: str) -> list[DeleteRecord]:
        """查询资料的删除记录（从 MaterialDeleted 事件，客户端过滤）"""
        self._ensure_init()
        try:
            target = Web3.keccak(text=material_id).hex()
            events = self._registry.events.MaterialDeleted.get_logs(from_block=0)
            records = []
            for ev in events:
                ev_id = ev.args.id.hex() if isinstance(ev.args.id, bytes) else ev.args.id
                if ev_id == target:
                    records.append(DeleteRecord(
                        material_id=material_id,
                        caller=ev.args.caller,
                        timestamp=ev.args.timestamp,
                    ))
            return records
        except Exception:
            return []

    def get_updates_by_user(self, address: str) -> list[UpdateRecord]:
        """查询某用户上传资料的修改记录（通过资料列表间接查询）"""
        self._ensure_init()
        records = []
        try:
            count = self.get_material_count()
            for i in range(count):
                mat_id = self._registry.functions.materialIds(i).call()
                material = self.query_material(mat_id)
                if material and material.uploader.lower() == address.lower():
                    records.extend(self.get_updates_by_material(mat_id))
            records.sort(key=lambda r: r.timestamp, reverse=True)
        except Exception:
            pass
        return records

    def get_full_audit(self, material_id: str) -> dict:
        """获取资料的完整审计信息（下载+修改+删除）"""
        self._ensure_init()
        material = self.query_material(material_id)
        return {
            "material": material.to_dict() if material else None,
            "downloads": [r.to_dict() for r in self.get_downloads_by_material(material_id)],
            "updates": [r.to_dict() for r in self.get_updates_by_material(material_id)],
            "deletions": [r.to_dict() for r in self.get_deletions_by_material(material_id)],
        }

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

    def get_chain_id(self) -> int:
        """当前连接网络的链 ID。"""
        self._ensure_init()
        return self.w3.eth.chain_id

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
