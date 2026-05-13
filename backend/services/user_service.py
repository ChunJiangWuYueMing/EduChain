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
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from werkzeug.security import generate_password_hash, check_password_hash

from config import config


USERS_FILE = Path(__file__).parent.parent / "users.json"

# Ganache 默认账户私钥（与 ganache --accounts 10 对应）
# 首次 init 时从 Ganache 获取实际地址，私钥需要预配置或从 Ganache 读取
# 这里用 Ganache 的默认 HD 钱包，具体值在 init_users 时动态填充


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
        self._initialized = False

    def init_users(self, ganache_accounts: list[str], ganache_keys: Optional[list[str]] = None) -> None:
        """
        初始化用户数据。

        从 users.json 加载用户，分配 Ganache 账户（从 index 1 开始，0 给 deployer）。
        如果用户还没有密码，设置默认密码为学号。

        Args:
            ganache_accounts: Ganache 账户地址列表
            ganache_keys:     Ganache 账户私钥列表（可选，用于签名模式）
        """
        if self._initialized:
            return

        if not USERS_FILE.exists():
            raise FileNotFoundError(f"用户数据文件不存在: {USERS_FILE}")

        with open(USERS_FILE) as f:
            data = json.load(f)

        users_data = data.get("users", [])

        # 账户 0 给 deployer，用户从 1 开始分配
        account_offset = 1
        needs_save = False

        for i, u in enumerate(users_data):
            account_index = account_offset + i
            if account_index >= len(ganache_accounts):
                break

            # 分配地址
            if not u.get("eth_address"):
                u["eth_address"] = ganache_accounts[account_index]
                needs_save = True

            # 分配私钥
            if not u.get("eth_private_key") and ganache_keys and account_index < len(ganache_keys):
                u["eth_private_key"] = ganache_keys[account_index]
                needs_save = True

            # 设置默认密码（学号）
            if not u.get("password_hash"):
                u["password_hash"] = generate_password_hash(u["student_id"])
                needs_save = True

            user = User(
                student_id=u["student_id"],
                name=u["name"],
                password_hash=u["password_hash"],
                eth_address=u["eth_address"],
                eth_private_key=u.get("eth_private_key", ""),
                courses=u.get("courses", []),
                role=u.get("role", "student"),
            )
            self._users[user.student_id] = user
            self._addr_index[user.eth_address.lower()] = user.student_id

        # 回写更新后的数据
        if needs_save:
            data["users"] = users_data
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

        self._initialized = True

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
