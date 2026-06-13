"""
user_service.py — 用户数据服务

职责：
  1. 从 users.json 加载用户数据
  2. 首次启动时自动分配 Ganache 账户和私钥
  3. 登录验证（密码哈希）
  4. 按 student_id / eth_address 查找用户
  5. 课程权限查询

注意：
  - 账户 0 保留给 deployer/owner，用户从账户 1 开始分配
  - 密码使用 werkzeug.security 哈希，禁止明文存储
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from werkzeug.security import generate_password_hash, check_password_hash

from config import config


USERS_FILE = Path(__file__).parent.parent / "users.json"


@dataclass
class User:
    """用户数据"""
    student_id: str
    name: str
    password_hash: str
    eth_address: str
    eth_private_key: str
    courses: list[str] = field(default_factory=list)
    role: str = "student"

    def to_dict(self, include_private: bool = False) -> dict:
        """转为 dict（默认不暴露私钥和密码哈希）"""
        d = {
            "student_id": self.student_id,
            "name": self.name,
            "eth_address": self.eth_address,
            "courses": self.courses,
            "role": self.role,
        }
        if include_private:
            d["eth_private_key"] = self.eth_private_key
            d["password_hash"] = self.password_hash
        return d

    def to_session(self) -> dict:
        """写入 Flask session 的数据"""
        return {
            "student_id": self.student_id,
            "name": self.name,
            "eth_address": self.eth_address,
            "courses": self.courses,
            "role": self.role,
        }


class UserService:
    """用户数据服务"""

    def __init__(self):
        self._users: dict[str, User] = {}          # student_id -> User
        self._addr_index: dict[str, str] = {}       # eth_address.lower() -> student_id
        self._users_with_keys: list[User] = []
        self._users_without_keys: list[User] = []
        self._initialized = False

    # 项目固定助记词（与 deploy.py、Ganache 启动命令保持一致）
    _FALLBACK_MNEMONIC = "test test test test test test test test test test test junk"

    def init_users(self, ganache_accounts: list[str], ganache_keys: Optional[list[str]] = None) -> None:
        """
        初始化用户数据。

        私钥来源优先级（逐级尝试，取第一个非空值）：
          1. ganache_keys 参数（调用方显式传入）
          2. users.json 中已有的 eth_private_key
          3. 环境变量 ACCOUNT_{n}_PRIVATE_KEY（deploy.py 写入 .env）
          4. 从项目固定助记词派生（开发环境兜底）
        """
        if self._initialized:
            return

        if not USERS_FILE.exists():
            raise FileNotFoundError(f"用户数据文件不存在: {USERS_FILE}")

        with open(USERS_FILE, encoding="utf-8") as f:
            data = json.load(f)

        users_data = data.get("users", [])

        # 准备助记词派生的密钥作为兜底
        derived_keys = self._derive_fallback_keys(len(ganache_accounts))

        account_offset = 1
        needs_save = False

        for i, u in enumerate(users_data):
            account_index = account_offset + i
            resolved_address = u.get("eth_address", "")
            if account_index < len(ganache_accounts):
                resolved_address = ganache_accounts[account_index]

            if not resolved_address:
                continue

            if resolved_address != u.get("eth_address"):
                u["eth_address"] = resolved_address
                needs_save = True

            # 分配私钥（按优先级逐级尝试）
            resolved_key = ""

            # 优先级 1：调用方参数
            if ganache_keys and account_index < len(ganache_keys):
                resolved_key = ganache_keys[account_index]
            # 优先级 2：users.json 已有值
            if not resolved_key and u.get("eth_private_key"):
                resolved_key = u["eth_private_key"]
            # 优先级 3：环境变量（deploy.py 写入 .env）
            if not resolved_key:
                resolved_key = os.environ.get(f"ACCOUNT_{account_index}_PRIVATE_KEY", "")
            # 优先级 4：助记词派生兜底
            if not resolved_key and account_index < len(derived_keys):
                resolved_key = derived_keys[account_index]

            if resolved_key and resolved_key != u.get("eth_private_key"):
                u["eth_private_key"] = resolved_key
                needs_save = True

            # 设置默认密码（学号）
            if not u.get("password_hash"):
                u["password_hash"] = generate_password_hash(u["student_id"])
                needs_save = True

            user = User(
                student_id=u["student_id"],
                name=u["name"],
                password_hash=u["password_hash"],
                eth_address=resolved_address,
                eth_private_key=u.get("eth_private_key", ""),
                courses=u.get("courses", []),
                role=u.get("role", "student"),
            )
            self._users[user.student_id] = user
            if user.eth_address:
                self._addr_index[user.eth_address.lower()] = user.student_id

        # 回写更新后的数据
        if needs_save:
            data["users"] = users_data
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

        # 初始化后审计：统计私钥覆盖情况
        self._users_with_keys = [
            u for u in self._users.values() if u.eth_private_key
        ]
        self._users_without_keys = [
            u for u in self._users.values() if not u.eth_private_key
        ]

        self._initialized = True

    @property
    def signing_ready(self) -> bool:
        """是否有至少一个用户拥有私钥（签名交易可用）"""
        return len(self._users_with_keys) > 0

    @property
    def key_summary(self) -> dict:
        """私钥覆盖情况摘要"""
        return {
            "total_users": len(self._users),
            "with_keys": len(self._users_with_keys),
            "without_keys": len(self._users_without_keys),
            "missing": [u.student_id for u in self._users_without_keys],
        }

    @staticmethod
    def _derive_fallback_keys(count: int) -> list[str]:
        """
        从项目固定助记词派生私钥（开发环境兜底）。

        返回长度为 count 的列表，index i 对应 Ganache 账户 i 的私钥。
        如果 eth_account 不可用，返回空列表（不中断启动）。
        """
        try:
            from eth_account import Account
            Account.enable_unaudited_hdwallet_features()
            keys = []
            for i in range(count):
                acct = Account.from_mnemonic(
                    UserService._FALLBACK_MNEMONIC,
                    account_path=f"m/44'/60'/0'/0/{i}",
                )
                private_key = acct.key.hex()
                if not private_key.startswith("0x"):
                    private_key = "0x" + private_key
                keys.append(private_key)
            return keys
        except Exception:
            return []

    # ---------- 查询 ----------

    def get_user(self, student_id: str) -> Optional[User]:
        """按学号查找用户"""
        return self._users.get(student_id)

    def get_user_by_address(self, eth_address: str) -> Optional[User]:
        """按以太坊地址查找用户"""
        sid = self._addr_index.get(eth_address.lower())
        return self._users.get(sid) if sid else None

    def get_all_users(self) -> list[User]:
        """获取所有用户"""
        return list(self._users.values())

    # ---------- 认证 ----------

    def verify_login(self, student_id: str, password: str) -> Optional[User]:
        """
        验证登录。

        Args:
            student_id: 学号
            password:   密码明文

        Returns:
            验证通过返回 User，否则返回 None
        """
        user = self._users.get(student_id)
        if user is None:
            return None
        if check_password_hash(user.password_hash, password):
            return user
        return None

    # ---------- 注册 ----------

    @staticmethod
    def validate_student_id(student_id: str) -> Optional[str]:
        """
        校验学号格式。

        格式: 10位数字, 2023116100
          - 前4位: 入学年份 (2000-2099)
          - 第5-7位: 学院代码 (100-999)
          - 第8-10位: 学生编号 (000-999)

        注意: 转专业不改学号，因此不校验学院代码与当前专业是否匹配。

        Returns:
            错误消息字符串，格式正确返回 None
        """
        import re
        if not re.match(r'^\d{10}$', student_id):
            return "学号必须为10位数字"
        year = int(student_id[:4])
        if year < 2000 or year > 2099:
            return "入学年份不合理"
        college = int(student_id[4:7])
        if college < 100:
            return "学院代码不合理"
        return None

    def register_user(self, student_id: str, name: str, password: str,
                      eth_address: str, eth_private_key: str = "",
                      courses: list[str] = None) -> User:
        """
        注册新用户。

        Args:
            student_id:   学号
            name:         姓名
            password:     密码明文
            eth_address:  以太坊地址
            eth_private_key: 私钥（可选）
            courses:      选修课程列表

        Returns:
            新创建的 User

        Raises:
            ValueError: 学号已存在 / 格式无效
        """
        if student_id in self._users:
            raise ValueError("该学号已注册")

        err = self.validate_student_id(student_id)
        if err:
            raise ValueError(err)

        password_hash = generate_password_hash(password)
        user = User(
            student_id=student_id,
            name=name,
            password_hash=password_hash,
            eth_address=eth_address,
            eth_private_key=eth_private_key,
            courses=courses or [],
            role="student",
        )
        self._users[student_id] = user
        self._addr_index[eth_address.lower()] = student_id
        self._persist_users()
        return user

    def _persist_users(self) -> None:
        """将当前用户数据写回 users.json"""
        users_data = []
        for u in self._users.values():
            users_data.append({
                "student_id": u.student_id,
                "name": u.name,
                "password_hash": u.password_hash,
                "eth_address": u.eth_address,
                "eth_private_key": u.eth_private_key,
                "courses": u.courses,
                "role": u.role,
            })
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump({"users": users_data, "_注释": "学号格式: 10位数字"}, f, ensure_ascii=False, indent=4)

    # ---------- 权限 ----------

    def has_course(self, student_id: str, course: str) -> bool:
        """检查用户是否选修了某课程"""
        user = self._users.get(student_id)
        if user is None:
            return False
        if user.role == "admin":
            return True
        return course in user.courses

    def is_admin(self, student_id: str) -> bool:
        """是否管理员"""
        user = self._users.get(student_id)
        return user is not None and user.role == "admin"


# 全局单例
user_service = UserService()
