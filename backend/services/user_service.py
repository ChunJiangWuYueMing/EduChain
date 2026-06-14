"""User seed initialization, authentication, persistence, and authorization."""

import json
import os
import re
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from eth_account import Account
from werkzeug.security import check_password_hash, generate_password_hash

from config import config
from course_catalog import COURSE_CATALOG


@dataclass
class User:
    student_id: str
    name: str
    password_hash: str
    eth_address: str
    eth_private_key: str
    courses: list[str] = field(default_factory=list)
    role: str = "student"
    gender: str = ""
    account_index: int = -1
    register_reward_granted: bool = False

    def to_dict(self, include_private: bool = False) -> dict:
        data = {
            "student_id": self.student_id,
            "name": self.name,
            "gender": self.gender,
            "eth_address": self.eth_address,
            "courses": self.courses,
            "role": self.role,
        }
        if include_private:
            data.update({
                "password_hash": self.password_hash,
                "eth_private_key": self.eth_private_key,
                "account_index": self.account_index,
                "register_reward_granted": self.register_reward_granted,
            })
        return data

    def to_session(self) -> dict:
        return {
            "student_id": self.student_id,
            "name": self.name,
            "gender": self.gender,
            "eth_address": self.eth_address,
            "courses": self.courses,
            "role": self.role,
        }


class UserService:
    _FALLBACK_MNEMONIC = (
        "test test test test test test test test test test test junk"
    )

    def __init__(self):
        self._users: dict[str, User] = {}
        self._addr_index: dict[str, str] = {}
        self._users_with_keys: list[User] = []
        self._users_without_keys: list[User] = []
        self._initialized = False
        self._file_lock = threading.RLock()

    @property
    def users_file(self) -> Path:
        return Path(config.USERS_FILE)

    @property
    def seed_file(self) -> Path:
        return Path(config.USERS_SEED_FILE)

    def init_users(
        self,
        ganache_accounts: list[str],
        ganache_keys: Optional[list[str]] = None,
    ) -> None:
        if self._initialized:
            return

        with self._file_lock:
            if not self.users_file.exists():
                self.initialize_runtime_users(
                    ganache_accounts=ganache_accounts,
                    ganache_keys=ganache_keys,
                )

            data = self._read_json(self.users_file)
            records = data.get("users", [])
            self._validate_records(records, ganache_accounts)
            self._load_records(records)
            self._initialized = True

    def initialize_runtime_users(
        self,
        ganache_accounts: list[str],
        ganache_keys: Optional[list[str]] = None,
        force: bool = False,
    ) -> bool:
        """Create runtime users from the committed seed file.

        Returns True when a new runtime file was written, False when an
        existing file was kept.
        """
        with self._file_lock:
            if self.users_file.exists() and not force:
                return False
            if not self.seed_file.exists():
                raise FileNotFoundError(f"用户种子文件不存在: {self.seed_file}")
            if len(ganache_accounts) < 10:
                raise ValueError(
                    f"Ganache 至少需要10个账户，当前只有 {len(ganache_accounts)} 个"
                )

            seed_records = self._read_json(self.seed_file).get("users", [])
            derived_keys = ganache_keys or self._derive_fallback_keys(
                len(ganache_accounts)
            )
            if len(derived_keys) < len(ganache_accounts):
                raise ValueError("无法获得完整的 Ganache 私钥列表")

            runtime_records = []
            for seed in seed_records:
                account_index = int(seed["account_index"])
                if account_index == config.DEPLOYER_ACCOUNT_INDEX:
                    raise ValueError("Ganache account[0] 只能作为合约部署者")
                if account_index >= len(ganache_accounts):
                    raise ValueError(
                        f"{seed['student_id']} 的 account_index 超出 Ganache 账户范围"
                    )

                address = ganache_accounts[account_index]
                private_key = derived_keys[account_index]
                self._validate_key_pair(address, private_key, seed["student_id"])
                runtime_records.append({
                    "student_id": seed["student_id"],
                    "name": seed["name"],
                    "gender": seed.get("gender", ""),
                    "role": seed.get("role", "student"),
                    "courses": seed.get("courses", []),
                    "account_index": account_index,
                    "password_hash": generate_password_hash(
                        config.TEST_USER_PASSWORD
                    ),
                    "eth_address": address,
                    "eth_private_key": private_key,
                    "register_reward_granted": False,
                })

            self._validate_records(runtime_records, ganache_accounts)
            self._write_json_atomic(
                self.users_file,
                {
                    "users": runtime_records,
                    "_notice": "Runtime test data. Do not commit this file.",
                },
            )
            return True

    def _load_records(self, records: list[dict]) -> None:
        self._users.clear()
        self._addr_index.clear()
        for record in records:
            user = User(
                student_id=record["student_id"],
                name=record["name"],
                gender=record.get("gender", ""),
                password_hash=record["password_hash"],
                eth_address=record["eth_address"],
                eth_private_key=record.get("eth_private_key", ""),
                courses=record.get("courses", []),
                role=record.get("role", "student"),
                account_index=int(record.get("account_index", -1)),
                register_reward_granted=bool(
                    record.get("register_reward_granted", False)
                ),
            )
            self._users[user.student_id] = user
            self._addr_index[user.eth_address.lower()] = user.student_id

        self._users_with_keys = [
            user for user in self._users.values() if user.eth_private_key
        ]
        self._users_without_keys = [
            user for user in self._users.values() if not user.eth_private_key
        ]

    def _validate_records(
        self,
        records: list[dict],
        ganache_accounts: Optional[list[str]] = None,
    ) -> None:
        if not records:
            raise ValueError("用户数据为空")

        ids = [record.get("student_id", "") for record in records]
        if len(ids) != len(set(ids)):
            raise ValueError("登录账号存在重复")

        addresses = [
            record.get("eth_address", "").lower()
            for record in records
            if record.get("eth_address")
        ]
        if len(addresses) != len(records) or len(addresses) != len(set(addresses)):
            raise ValueError("用户钱包地址缺失或重复")

        admins = [record for record in records if record.get("role") == "admin"]
        students = [
            record for record in records if record.get("role", "student") == "student"
        ]
        if len(admins) != 1:
            raise ValueError(f"必须且只能有1个管理员，当前为 {len(admins)} 个")
        if len(students) != 8 or len(records) != 9:
            raise ValueError("课程联动测试要求8个学生账号和1个管理员账号")
        if "2023112379" not in ids or "admin_2023112379" not in ids:
            raise ValueError("唐昊的学生账号和管理员账号必须同时存在")

        account_indexes = [int(record.get("account_index", -1)) for record in records]
        if len(account_indexes) != len(set(account_indexes)):
            raise ValueError("Ganache account_index 存在重复")
        if config.DEPLOYER_ACCOUNT_INDEX in account_indexes:
            raise ValueError("Ganache account[0] 不能分配给登录用户")

        for record in records:
            unknown_courses = set(record.get("courses", [])) - set(COURSE_CATALOG)
            if unknown_courses:
                raise ValueError(
                    f"{record['student_id']} 包含未知课程: "
                    f"{', '.join(sorted(unknown_courses))}"
                )
            self._validate_key_pair(
                record["eth_address"],
                record.get("eth_private_key", ""),
                record["student_id"],
            )
            if ganache_accounts:
                index = int(record["account_index"])
                if index >= len(ganache_accounts):
                    raise ValueError(
                        f"{record['student_id']} 的钱包索引超出 Ganache 范围"
                    )
                if record["eth_address"].lower() != ganache_accounts[index].lower():
                    raise ValueError(
                        f"{record['student_id']} 的钱包与 Ganache account[{index}] 不一致"
                    )

    @staticmethod
    def _validate_key_pair(address: str, private_key: str, student_id: str) -> None:
        if not private_key:
            raise ValueError(f"{student_id} 缺少钱包私钥")
        derived = Account.from_key(private_key).address
        if derived.lower() != address.lower():
            raise ValueError(f"{student_id} 的钱包地址与私钥不匹配")

    @staticmethod
    def _derive_fallback_keys(count: int) -> list[str]:
        Account.enable_unaudited_hdwallet_features()
        mnemonic = config.GANACHE_MNEMONIC or UserService._FALLBACK_MNEMONIC
        keys = []
        for index in range(count):
            account = Account.from_mnemonic(
                mnemonic,
                account_path=f"m/44'/60'/0'/0/{index}",
            )
            private_key = account.key.hex()
            keys.append(
                private_key if private_key.startswith("0x") else f"0x{private_key}"
            )
        return keys

    @staticmethod
    def _read_json(path: Path) -> dict:
        with path.open(encoding="utf-8") as file:
            return json.load(file)

    @staticmethod
    def _write_json_atomic(path: Path, data: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(f"{path.suffix}.tmp")
        temporary.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, path)

    @property
    def signing_ready(self) -> bool:
        return (
            bool(self._users)
            and len(self._users_with_keys) == len(self._users)
        )

    @property
    def key_summary(self) -> dict:
        return {
            "total_users": len(self._users),
            "with_keys": len(self._users_with_keys),
            "without_keys": len(self._users_without_keys),
            "missing": [user.student_id for user in self._users_without_keys],
        }

    def get_summary(self) -> dict:
        users = self.get_all_users()
        return {
            "users_count": len(users),
            "student_count": sum(user.role == "student" for user in users),
            "admin_count": sum(user.role == "admin" for user in users),
            "wallets_ready": sum(
                bool(user.eth_address and user.eth_private_key) for user in users
            ),
        }

    def get_user(self, student_id: str) -> Optional[User]:
        return self._users.get(student_id)

    def get_user_by_address(self, eth_address: str) -> Optional[User]:
        student_id = self._addr_index.get(eth_address.lower())
        return self._users.get(student_id) if student_id else None

    def get_all_users(self) -> list[User]:
        return list(self._users.values())

    def verify_login(self, student_id: str, password: str) -> Optional[User]:
        user = self._users.get(student_id)
        if user and check_password_hash(user.password_hash, password):
            return user
        return None

    @staticmethod
    def validate_student_id(student_id: str) -> Optional[str]:
        if not re.match(r"^\d{10}$", student_id):
            return "学号必须为10位数字"
        year = int(student_id[:4])
        if year < 2000 or year > 2099:
            return "入学年份不合理"
        if int(student_id[4:7]) < 100:
            return "学院代码不合理"
        return None

    def register_user(
        self,
        student_id: str,
        name: str,
        password: str,
        eth_address: str,
        eth_private_key: str = "",
        courses: Optional[list[str]] = None,
    ) -> User:
        if student_id in self._users:
            raise ValueError("该学号已注册")
        error = self.validate_student_id(student_id)
        if error:
            raise ValueError(error)

        user = User(
            student_id=student_id,
            name=name,
            password_hash=generate_password_hash(password),
            eth_address=eth_address,
            eth_private_key=eth_private_key,
            courses=courses or [],
        )
        self._users[student_id] = user
        self._addr_index[eth_address.lower()] = student_id
        self._persist_users()
        return user

    def mark_register_reward_granted(self, student_id: str) -> None:
        with self._file_lock:
            user = self._users.get(student_id)
            if user is None or user.register_reward_granted:
                return
            user.register_reward_granted = True
            self._persist_users()

    def _persist_users(self) -> None:
        with self._file_lock:
            records = [
                user.to_dict(include_private=True)
                for user in self._users.values()
            ]
            self._write_json_atomic(
                self.users_file,
                {
                    "users": records,
                    "_notice": "Runtime test data. Do not commit this file.",
                },
            )

    def has_course(self, student_id: str, course: str) -> bool:
        user = self._users.get(student_id)
        if user is None:
            return False
        return user.role == "admin" or course in user.courses

    def is_admin(self, student_id: str) -> bool:
        user = self._users.get(student_id)
        return user is not None and user.role == "admin"


user_service = UserService()
