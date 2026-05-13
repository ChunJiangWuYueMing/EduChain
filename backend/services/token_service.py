"""
token_service.py — 通证业务逻辑层

封装注册奖励、下载扣费、抄袭扣罚等业务场景。
所有链操作通过 chain_service 执行，本模块不直接接触 Web3。
"""

from dataclasses import dataclass
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
    """通证业务服务"""

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

    # ---------- 下载扣费 ----------

    @staticmethod
    def process_download(material_id: str, downloader: str) -> dict:
        """
        处理下载扣费：
          1. 查询资料信息（价格、上传者）
          2. 检查下载者余额
          3. 自动 approve + transferFrom
          4. 记录下载日志

        Returns:
            dict 包含扣费详情

        Raises:
            ValueError: 资料不存在/已删除/余额不足/下载自己的资料
        """
        # 查询资料
        material = chain_service.query_material(material_id)
        if material is None:
            raise ValueError(f"资料不存在: {material_id}")
        if material.deleted:
            raise ValueError(f"资料已被删除: {material_id}")
        if downloader.lower() == material.uploader.lower():
            raise ValueError("不能下载自己上传的资料")

        # 检查余额
        if material.price > 0:
            balance = chain_service.get_edu_balance(downloader)
            if balance < material.price:
                raise ValueError(
                    f"EDU 余额不足: 需要 {material.price}，当前 {balance}"
                )

        # 执行通证转移（chain_service.download_material 内部处理 approve）
        receipt = chain_service.download_material(material_id, downloader)

        # 记录下载日志到 DownloadLog 合约
        file_hash = bytes.fromhex(material.sha256_hash.replace("0x", "").ljust(64, "0")[:64])
        chain_service.record_download(
            material_id=material_id,
            downloader=downloader,
            uploader=material.uploader,
            price=material.price,
            file_hash=file_hash,
        )

        return {
            "material_id": material_id,
            "downloader": downloader,
            "uploader": material.uploader,
            "price": material.price,
            "tx_hash": receipt["transactionHash"].hex(),
            "block": receipt["blockNumber"],
        }

    # ---------- 抄袭扣罚 ----------

    @staticmethod
    def penalize_plagiarism(uploader_address: str, material_id: str) -> dict:
        """
        抄袭扣罚：销毁上传者 50 EDU

        Args:
            uploader_address: 被扣罚的上传者地址
            material_id:      涉及的资料 ID（记录用）

        Returns:
            扣罚详情
        """
        balance = chain_service.get_edu_balance(uploader_address)
        actual_penalty = min(config.PLAGIARISM_PENALTY, balance)

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

        # 查询 Transfer 事件（from=address 或 to=address）
        # Transfer(from, to, value) 是 ERC-20 标准事件
        try:
            # 作为接收方的事件
            to_filter = token.events.Transfer.create_filter(
                from_block=0,
                argument_filters={"to": addr},
            )
            for event in to_filter.get_all_entries():
                from_addr = event["args"]["from"]
                # from=0x0 表示 mint
                is_mint = from_addr == "0x0000000000000000000000000000000000000000"
                transactions.append({
                    "type": "mint" if is_mint else "receive",
                    "from": from_addr,
                    "to": event["args"]["to"],
                    "amount": event["args"]["value"],
                    "block": event["blockNumber"],
                    "tx_hash": event["transactionHash"].hex(),
                })

            # 作为发送方的事件
            from_filter = token.events.Transfer.create_filter(
                from_block=0,
                argument_filters={"from": addr},
            )
            for event in from_filter.get_all_entries():
                to_address = event["args"]["to"]
                is_burn = to_address == "0x0000000000000000000000000000000000000000"
                transactions.append({
                    "type": "burn" if is_burn else "send",
                    "from": event["args"]["from"],
                    "to": to_address,
                    "amount": event["args"]["value"],
                    "block": event["blockNumber"],
                    "tx_hash": event["transactionHash"].hex(),
                })
        except Exception:
            # Ganache 可能不完全支持事件过滤，降级为空列表
            pass

        # 按区块号排序，取最近 limit 条
        transactions.sort(key=lambda x: x["block"], reverse=True)
        return transactions[:limit]


# 全局单例
token_service = TokenService()
