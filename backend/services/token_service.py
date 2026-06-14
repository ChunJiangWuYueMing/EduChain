"""
token_service.py — 通证业务逻辑层

纯通证职责：余额查询、注册奖励、抄袭扣罚、交易历史。
审查修正：下载扣费编排已迁至 material_service.py。
"""

from dataclasses import dataclass
import threading
from typing import Optional

from config import config
from services.chain_service import chain_service


@dataclass
class TokenTransaction:
    """通证交易记录（应用层，非链上）"""
    tx_type: str        # mint / transfer / burn
    from_addr: str
    to_addr: str
    amount: int
    reason: str
    block_number: int

    def to_dict(self) -> dict:
        return {
            "type": self.tx_type,
            "from": self.from_addr,
            "to": self.to_addr,
            "amount": self.amount,
            "reason": self.reason,
            "block_number": self.block_number,
        }


class TokenService:
    """通证业务服务（纯通证操作，不编排资料业务）"""

    def __init__(self):
        self._reward_locks: dict[str, threading.Lock] = {}
        self._reward_locks_guard = threading.Lock()

    def _reward_lock(self, address: str) -> threading.Lock:
        key = address.lower()
        with self._reward_locks_guard:
            if key not in self._reward_locks:
                self._reward_locks[key] = threading.Lock()
            return self._reward_locks[key]

    # ---------- 查询 ----------

    @staticmethod
    def get_balance(address: str) -> int:
        """查询用户 EDU 余额"""
        return chain_service.get_edu_balance(address)

    @staticmethod
    def get_allowance(owner: str, spender: str) -> int:
        """查询授权额度"""
        return chain_service.get_edu_allowance(owner, spender)

    # ---------- 注册奖励 ----------

    @staticmethod
    def reward_register(user_address: str) -> dict:
        """
        用户注册奖励：铸造 100 EDU

        Returns:
            交易回执
        """
        receipt = chain_service.mint_edu(
            to=user_address,
            amount=config.REGISTER_REWARD,
            reason="register",
        )
        return {
            "amount": config.REGISTER_REWARD,
            "tx_hash": receipt["transactionHash"].hex(),
            "block": receipt["blockNumber"],
        }

    @staticmethod
    def reward(user_address: str, amount: int, reason: str = "admin_reward") -> dict:
        receipt = chain_service.mint_edu(
            to=user_address,
            amount=amount,
            reason=reason,
        )
        return {
            "rewarded": user_address,
            "amount": amount,
            "reason": reason,
            "tx_hash": receipt["transactionHash"].hex(),
            "block": receipt["blockNumber"],
        }

    def ensure_register_reward(self, user, user_service) -> tuple[int, int]:
        """Grant the one-time student login reward safely.

        Returns (current_balance, newly_granted_amount).
        """
        if user.role != "student":
            return chain_service.get_edu_balance(user.eth_address), 0

        with self._reward_lock(user.eth_address):
            current = user_service.get_user(user.student_id)
            balance = chain_service.get_edu_balance(user.eth_address)
            if current is None or current.register_reward_granted:
                return balance, 0

            granted = 0
            if balance == 0:
                result = self.reward_register(user.eth_address)
                granted = result["amount"]
                balance = chain_service.get_edu_balance(user.eth_address)

            user_service.mark_register_reward_granted(user.student_id)
            return balance, granted

    # ---------- 抄袭扣罚 ----------

    @staticmethod
    def penalize_plagiarism(
        uploader_address: str,
        material_id: str,
        amount: Optional[int] = None,
    ) -> dict:
        """
        抄袭扣罚：销毁上传者 50 EDU

        Args:
            uploader_address: 被扣罚的上传者地址
            material_id:      涉及的资料 ID（记录用）

        Returns:
            扣罚详情
        """
        balance = chain_service.get_edu_balance(uploader_address)
        requested_penalty = (
            config.PLAGIARISM_PENALTY if amount is None else amount
        )
        actual_penalty = min(requested_penalty, balance)

        if actual_penalty > 0:
            receipt = chain_service.burn_edu(
                from_addr=uploader_address,
                amount=actual_penalty,
                reason=f"plagiarism:{material_id}",
            )
            return {
                "penalized": uploader_address,
                "amount": actual_penalty,
                "material_id": material_id,
                "tx_hash": receipt["transactionHash"].hex(),
                "block": receipt["blockNumber"],
            }
        else:
            return {
                "penalized": uploader_address,
                "amount": 0,
                "material_id": material_id,
                "note": "余额为 0，无法扣罚",
            }

    # ---------- 交易历史（从链上事件解析） ----------

    @staticmethod
    def get_transaction_history(address: str, limit: int = 50) -> list[dict]:
        """
        获取用户相关的通证交易历史。

        从 EduToken 合约的 Transfer 事件中过滤。
        包括：收到铸造、发出转账、收到转账。
        """
        token = chain_service._token
        addr = chain_service.w3.to_checksum_address(address)

        transactions = []
        block_timestamps = {}

        def get_timestamp(block_number: int) -> int:
            if block_number not in block_timestamps:
                block = chain_service.w3.eth.get_block(block_number)
                block_timestamps[block_number] = int(block["timestamp"])
            return block_timestamps[block_number]

        # 一次性读取 Transfer 日志后在客户端过滤。eth_getLogs 在 Ganache
        # 和标准节点上都比临时 filter 稳定，且不会依赖节点保留 filter 状态。
        try:
            events = token.events.Transfer.get_logs(
                fromBlock=0,
                toBlock="latest",
            )
            for event in events:
                from_addr = event["args"]["from"]
                to_address = event["args"]["to"]
                block_number = event["blockNumber"]
                common = {
                    "from": from_addr,
                    "to": to_address,
                    "amount": event["args"]["value"],
                    "block": block_number,
                    "tx_hash": event["transactionHash"].hex(),
                    "timestamp": get_timestamp(block_number),
                }

                if to_address.lower() == addr.lower():
                    is_mint = (
                        from_addr.lower()
                        == "0x0000000000000000000000000000000000000000"
                    )
                    transactions.append({
                        **common,
                        "type": "mint" if is_mint else "receive",
                    })

                if from_addr.lower() == addr.lower():
                    is_burn = (
                        to_address.lower()
                        == "0x0000000000000000000000000000000000000000"
                    )
                    transactions.append({
                        **common,
                        "type": "burn" if is_burn else "send",
                    })
        except Exception:
            # 节点暂不可用时保持钱包页面可访问。
            pass

        # 按区块号排序，取最近 limit 条
        transactions.sort(key=lambda x: x["block"], reverse=True)
        return transactions[:limit]


# 全局单例
token_service = TokenService()
