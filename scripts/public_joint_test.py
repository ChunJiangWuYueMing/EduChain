"""Run the EduChain nine-account joint test against a deployed server."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import requests


ROOT = Path(__file__).resolve().parents[1]
TEST_DOCS = ROOT / "docs" / "test_docs"
RESULTS_ROOT = ROOT / "docs" / "test_results"
PASSWORD = "123456"

ACCOUNTS = [
    ("2023112379", "唐昊", "student"),
    ("admin_2023112379", "唐昊（管理员）", "admin"),
    ("2023112385", "薛雨凇", "student"),
    ("2023112380", "于骐畅", "student"),
    ("2023112318", "周子皓", "student"),
    ("2023112330", "王东涵", "student"),
    ("2023116100", "谢傲宇", "student"),
    ("2023112392", "李子彤", "student"),
    ("2023112317", "方天宇", "student"),
]

FILES = {
    "A": TEST_DOCS / "A_区块链技术及应用课程复习资料.pdf",
    "B": TEST_DOCS / "B_区块链资料完全重复副本.pdf",
    "C": TEST_DOCS / "C_区块链课程复习资料修订版.pdf",
    "D": TEST_DOCS / "D_Solidity智能合约基础.pptx",
    "E": TEST_DOCS / "E_操作系统进程调度复习资料.pdf",
    "F": TEST_DOCS / "F_计算机网络协议总结.pptx",
    "G": TEST_DOCS / "G_数据库原理实验参考资料.pdf",
    "H": TEST_DOCS / "H_人工智能导论知识总结.pptx",
    "I": TEST_DOCS / "I_区块链资料篡改测试版.pdf",
}


@dataclass
class ResponseData:
    status: int
    elapsed: float
    body: Any
    headers: dict[str, str]
    content: bytes


class JointTest:
    def __init__(self, base_url: str, output_dir: Path):
        self.base_url = base_url.rstrip("/")
        self.output_dir = output_dir
        self.download_dir = output_dir / "downloads"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.sessions: dict[str, requests.Session] = {}
        self.users: dict[str, dict] = {}
        self.materials: dict[str, dict] = {}
        self.results: dict[str, Any] = {
            "run": {
                "base_url": self.base_url,
                "started_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                "output_dir": str(output_dir),
            },
            "file_hashes": {},
            "health_before": {},
            "health_after": {},
            "accounts": {},
            "materials": {},
            "balances": {},
            "downloads": {},
            "verification": {},
            "audit": {},
            "cases": [],
            "issues": [],
        }
        self._case_lock = threading.Lock()

    def url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    @staticmethod
    def response_data(response: requests.Response, elapsed: float) -> ResponseData:
        try:
            body: Any = response.json()
        except (requests.JSONDecodeError, ValueError):
            body = None
        return ResponseData(
            status=response.status_code,
            elapsed=round(elapsed, 3),
            body=body,
            headers={key: value for key, value in response.headers.items()},
            content=response.content,
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        session: requests.Session | None = None,
        timeout: int = 120,
        **kwargs,
    ) -> ResponseData:
        client = session or requests
        started = time.perf_counter()
        response = client.request(
            method,
            self.url(path),
            timeout=timeout,
            **kwargs,
        )
        return self.response_data(response, time.perf_counter() - started)

    def add_case(
        self,
        case_id: str,
        operator: str,
        function: str,
        expected: str,
        actual: str,
        passed: bool,
        *,
        balance_change: str = "",
        reference: str = "",
        elapsed: float | None = None,
        notes: str = "",
    ) -> None:
        case = {
            "id": case_id,
            "operator": operator,
            "function": function,
            "expected": expected,
            "actual": actual,
            "passed": bool(passed),
            "balance_change": balance_change,
            "reference": reference,
            "elapsed_seconds": elapsed,
            "notes": notes,
        }
        with self._case_lock:
            self.results["cases"].append(case)
        print(f"[{'PASS' if passed else 'FAIL'}] {case_id} {function}: {actual}")
        self.checkpoint()

    def add_issue(self, title: str, detail: str, severity: str = "medium") -> None:
        self.results["issues"].append(
            {"severity": severity, "title": title, "detail": detail}
        )
        self.checkpoint()

    def checkpoint(self) -> None:
        path = self.output_dir / "joint_test_results.json"
        path.write_text(
            json.dumps(self.results, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def api_data(response: ResponseData) -> Any:
        if isinstance(response.body, dict):
            return response.body.get("data")
        return None

    @staticmethod
    def api_message(response: ResponseData) -> str:
        if isinstance(response.body, dict):
            return str(response.body.get("msg") or response.body)
        return f"HTTP {response.status}"

    def hash_files(self) -> None:
        for label, path in FILES.items():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            self.results["file_hashes"][label] = {
                "name": path.name,
                "bytes": path.stat().st_size,
                "sha256": digest,
            }
        self.add_case(
            "FILE-01",
            "测试工具",
            "测试文件完整性基线",
            "A 与 B SHA-256 完全一致，其他文件具有独立哈希",
            "文件哈希已计算",
            (
                self.results["file_hashes"]["A"]["sha256"]
                == self.results["file_hashes"]["B"]["sha256"]
                and len(
                    {
                        item["sha256"]
                        for key, item in self.results["file_hashes"].items()
                        if key != "B"
                    }
                )
                == 8
            ),
            reference=self.results["file_hashes"]["A"]["sha256"],
        )

    def health(self) -> dict:
        response = self.request("GET", "/api/health", timeout=30)
        if response.status != 200:
            raise RuntimeError(
                f"健康检查失败: HTTP {response.status} {self.api_message(response)}"
            )
        return self.api_data(response) or {}

    def login_worker(self, student_id: str) -> tuple[str, requests.Session, ResponseData]:
        session = requests.Session()
        response = self.request(
            "POST",
            "/api/auth/login",
            session=session,
            json={"student_id": student_id, "password": PASSWORD},
            timeout=120,
        )
        return student_id, session, response

    def concurrent_login(self) -> None:
        with ThreadPoolExecutor(max_workers=9) as executor:
            futures = {
                executor.submit(self.login_worker, account[0]): account
                for account in ACCOUNTS
            }
            for future in as_completed(futures):
                expected = futures[future]
                student_id, session, response = future.result()
                data = self.api_data(response) or {}
                passed = (
                    response.status == 200
                    and data.get("student_id") == student_id
                    and data.get("role") == expected[2]
                )
                self.sessions[student_id] = session
                self.users[student_id] = data
                self.results["accounts"][student_id] = {
                    "name": data.get("name"),
                    "role": data.get("role"),
                    "courses": data.get("courses"),
                    "eth_address": data.get("eth_address"),
                    "first_login_reward": data.get("first_login_reward"),
                    "login_balance": data.get("edu_balance"),
                    "login_elapsed_seconds": response.elapsed,
                }
                expected_reward = 0 if expected[2] == "admin" else 100
                reward_ok = data.get("first_login_reward") == expected_reward
                self.add_case(
                    f"LOGIN-{student_id}",
                    expected[1],
                    "并发登录及首次奖励",
                    f"登录成功，首次奖励 {expected_reward} EDU",
                    (
                        f"HTTP {response.status}，奖励 "
                        f"{data.get('first_login_reward')} EDU，余额 {data.get('edu_balance')}"
                    ),
                    passed and reward_ok,
                    balance_change=f"+{data.get('first_login_reward', 0)} EDU",
                    reference=str(data.get("eth_address") or ""),
                    elapsed=response.elapsed,
                )

        addresses = [
            item.get("eth_address", "").lower()
            for item in self.users.values()
            if item.get("eth_address")
        ]
        unique = len(addresses) == 9 and len(set(addresses)) == 9
        self.add_case(
            "LOGIN-UNIQUE",
            "管理员",
            "九账号钱包唯一性",
            "9 个账号对应 9 个不同钱包",
            f"读取 {len(addresses)} 个钱包，唯一值 {len(set(addresses))}",
            unique,
        )

        def relogin(student_id: str) -> tuple[str, ResponseData]:
            return student_id, self.request(
                "POST",
                "/api/auth/login",
                session=self.sessions[student_id],
                json={"student_id": student_id, "password": PASSWORD},
                timeout=120,
            )

        with ThreadPoolExecutor(max_workers=9) as executor:
            repeats = list(executor.map(lambda item: relogin(item[0]), ACCOUNTS))
        duplicate_rewards = {
            student_id: (self.api_data(response) or {}).get("first_login_reward")
            for student_id, response in repeats
        }
        self.results["duplicate_login_rewards"] = duplicate_rewards
        self.add_case(
            "LOGIN-IDEMPOTENT",
            "全部账号",
            "并发重复登录奖励幂等",
            "重复登录均不再次发放奖励",
            json.dumps(duplicate_rewards, ensure_ascii=False),
            all(value == 0 for value in duplicate_rewards.values()),
        )

    def baseline_negative_tests(self) -> None:
        registration = self.request(
            "POST",
            "/api/auth/register",
            json={
                "student_id": "2023999999",
                "name": "公网临时账号",
                "password": PASSWORD,
            },
            timeout=30,
        )
        self.add_case(
            "AUTH-REGISTER",
            "未登录用户",
            "服务器关闭公开注册",
            "HTTP 403，提示账号由管理员统一创建",
            f"HTTP {registration.status}: {self.api_message(registration)}",
            registration.status == 403 and "统一创建" in self.api_message(registration),
            elapsed=registration.elapsed,
        )

        invalid = self.request(
            "POST",
            "/api/auth/login",
            json={"student_id": "2023112379", "password": "incorrect"},
            timeout=30,
        )
        self.add_case(
            "AUTH-BAD-PASSWORD",
            "唐昊",
            "错误密码登录",
            "HTTP 401",
            f"HTTP {invalid.status}: {self.api_message(invalid)}",
            invalid.status == 401,
            elapsed=invalid.elapsed,
        )

    def get_balance(self, student_id: str) -> int:
        response = self.request(
            "GET",
            "/api/token/balance",
            session=self.sessions[student_id],
            timeout=30,
        )
        if response.status != 200:
            raise RuntimeError(
                f"查询 {student_id} 余额失败: {self.api_message(response)}"
            )
        return int((self.api_data(response) or {})["balance"])

    def balance_snapshot(self, label: str) -> dict[str, int]:
        with ThreadPoolExecutor(max_workers=9) as executor:
            future_map = {
                executor.submit(self.get_balance, account[0]): account[0]
                for account in ACCOUNTS
            }
            values = {
                future_map[future]: future.result()
                for future in as_completed(future_map)
            }
        ordered = {account[0]: values[account[0]] for account in ACCOUNTS}
        self.results["balances"][label] = ordered
        self.checkpoint()
        return ordered

    def upload(
        self,
        student_id: str,
        label: str,
        *,
        course: str,
        policy_type: int,
        price: int = 5,
        policy_value: str = "",
    ) -> ResponseData:
        path = FILES[label]
        mime = (
            "application/pdf"
            if path.suffix.lower() == ".pdf"
            else "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )
        with path.open("rb") as file_obj:
            return self.request(
                "POST",
                "/api/material/upload",
                session=self.sessions[student_id],
                files={"file": (path.name, file_obj, mime)},
                data={
                    "name": path.name,
                    "course": course,
                    "policy_type": str(policy_type),
                    "policy_value": policy_value,
                    "price": str(price),
                },
                timeout=180,
            )

    def save_material(self, label: str, response: ResponseData) -> dict:
        data = self.api_data(response) or {}
        if response.status == 200:
            self.materials[label] = data
            self.results["materials"][label] = data
        else:
            self.results["materials"][label] = {
                "status": response.status,
                "message": self.api_message(response),
            }
        self.checkpoint()
        return data

    def run_uploads(self) -> None:
        before = self.get_balance("2023112379")
        response_a = self.upload(
            "2023112379",
            "A",
            course="BC401",
            policy_type=0,
        )
        data_a = self.save_material("A", response_a)
        after = self.get_balance("2023112379")
        local_sha = self.results["file_hashes"]["A"]["sha256"].lower()
        a_ok = (
            response_a.status == 200
            and data_a.get("sha256_hash", "").lower() == local_sha
            and after - before == 20
        )
        self.add_case(
            "UPLOAD-A",
            "唐昊",
            "上传公开资料 A",
            "上传成功、SHA-256 一致、奖励 20 EDU",
            (
                f"HTTP {response_a.status}，资料 {data_a.get('material_id')}，"
                f"余额 {before}->{after}"
            ),
            a_ok,
            balance_change=f"{before}->{after}",
            reference=f"{data_a.get('material_id', '')} {data_a.get('tx_hash', '')}",
            elapsed=response_a.elapsed,
        )
        if response_a.status != 200:
            raise RuntimeError("资料 A 上传失败，后续关联测试无法继续")

        before_b = self.get_balance("2023112385")
        response_b = self.upload(
            "2023112385",
            "B",
            course="BC401",
            policy_type=0,
        )
        self.save_material("B", response_b)
        after_b = self.get_balance("2023112385")
        self.add_case(
            "UPLOAD-B",
            "薛雨凇",
            "完全重复文件拦截",
            "HTTP 400，不新增资料，不发放奖励",
            f"HTTP {response_b.status}: {self.api_message(response_b)}",
            (
                response_b.status == 400
                and "完全相同" in self.api_message(response_b)
                and before_b == after_b
            ),
            balance_change=f"{before_b}->{after_b}",
            elapsed=response_b.elapsed,
        )

        fang_address = self.users["2023112317"]["eth_address"]
        tasks = {
            "C": ("2023112380", "BC401", 0, ""),
            "D": ("2023112385", "BC401", 1, ""),
            "E": ("2023112318", "CS301", 1, ""),
            "F": ("2023112330", "CS302", 1, ""),
            "G": ("2023116100", "DB201", 2, fang_address),
            "H": ("2023112392", "AI301", 0, ""),
        }
        balances_before = {
            label: self.get_balance(spec[0]) for label, spec in tasks.items()
        }

        with ThreadPoolExecutor(max_workers=6) as executor:
            future_map = {
                executor.submit(
                    self.upload,
                    spec[0],
                    label,
                    course=spec[1],
                    policy_type=spec[2],
                    policy_value=spec[3],
                ): (label, spec)
                for label, spec in tasks.items()
            }
            for future in as_completed(future_map):
                label, spec = future_map[future]
                response = future.result()
                data = self.save_material(label, response)
                after_upload = self.get_balance(spec[0])
                balance_delta = after_upload - balances_before[label]
                similar_ok = True
                note = ""
                if label == "C":
                    hits = data.get("similar_materials") or []
                    similar_ok = any(
                        item.get("material_id") == data_a.get("material_id")
                        for item in hits
                    )
                    note = json.dumps(hits, ensure_ascii=False)
                passed = response.status == 200 and balance_delta == 20 and similar_ok
                self.add_case(
                    f"UPLOAD-{label}",
                    next(item[1] for item in ACCOUNTS if item[0] == spec[0]),
                    f"并发上传资料 {label}",
                    (
                        "上传成功并奖励 20 EDU"
                        + ("，提示与资料 A 相似" if label == "C" else "")
                    ),
                    (
                        f"HTTP {response.status}，资料 {data.get('material_id')}，"
                        f"余额 +{balance_delta}"
                    ),
                    passed,
                    balance_change=(
                        f"{balances_before[label]}->{after_upload}"
                    ),
                    reference=f"{data.get('material_id', '')} {data.get('tx_hash', '')}",
                    elapsed=response.elapsed,
                    notes=note,
                )

    def verify_file(self, label: str, material_label: str) -> ResponseData:
        path = FILES[label]
        with path.open("rb") as file_obj:
            return self.request(
                "POST",
                "/api/material/verify",
                files={"file": (path.name, file_obj)},
                data={"material_id": self.materials[material_label]["material_id"]},
                timeout=180,
            )

    def run_verification(self) -> None:
        original = self.verify_file("A", "A")
        tampered = self.verify_file("I", "A")
        self.results["verification"] = {
            "original_A": self.api_data(original),
            "tampered_I_against_A": self.api_data(tampered),
        }
        original_data = self.api_data(original) or {}
        tampered_data = self.api_data(tampered) or {}
        self.add_case(
            "VERIFY-A",
            "李子彤",
            "资料 A 原文件完整性验证",
            "SHA-256 匹配，未篡改",
            json.dumps(original_data, ensure_ascii=False),
            (
                original.status == 200
                and original_data.get("sha256_match") is True
                and original_data.get("is_tampered") is False
            ),
            reference=self.materials["A"]["material_id"],
            elapsed=original.elapsed,
        )
        self.add_case(
            "VERIFY-I",
            "李子彤",
            "篡改文件 I 对照资料 A",
            "SHA-256 不匹配，判定被篡改",
            json.dumps(tampered_data, ensure_ascii=False),
            (
                tampered.status == 200
                and tampered_data.get("sha256_match") is False
                and tampered_data.get("is_tampered") is True
            ),
            reference=self.materials["A"]["material_id"],
            elapsed=tampered.elapsed,
        )

    def fresh_login(self, student_id: str) -> requests.Session:
        student_id, session, response = self.login_worker(student_id)
        if response.status != 200:
            raise RuntimeError(
                f"操作前登录 {student_id} 失败: {self.api_message(response)}"
            )
        return session

    def download_worker(
        self,
        operation_id: str,
        student_id: str,
        material_label: str,
        expected_status: int,
    ) -> tuple[str, str, str, int, int, ResponseData, str]:
        session = self.fresh_login(student_id)
        balance_before = self.request(
            "GET", "/api/token/balance", session=session, timeout=30
        )
        before = int((self.api_data(balance_before) or {})["balance"])
        material_id = self.materials[material_label]["material_id"]
        response = self.request(
            "GET",
            f"/api/material/{material_id}/download",
            session=session,
            timeout=180,
        )
        balance_after = self.request(
            "GET", "/api/token/balance", session=session, timeout=30
        )
        after = int((self.api_data(balance_after) or {})["balance"])
        saved = ""
        if response.status == 200:
            suffix = FILES[material_label].suffix
            target = self.download_dir / f"{operation_id}_{student_id}_{material_label}{suffix}"
            target.write_bytes(response.content)
            saved = str(target)
        return (
            operation_id,
            student_id,
            material_label,
            before,
            after,
            response,
            saved,
        )

    def run_downloads(self) -> None:
        operations = [
            ("DL-A-XUE", "2023112385", "A", 200, -5, "公开资料正常下载"),
            ("DL-F-YU", "2023112380", "F", 200, -5, "CS302 同课程下载"),
            ("DL-F-TANG-DENY", "2023112379", "F", 400, 0, "无 CS302 权限拒绝"),
            ("DL-E-WANG-DENY", "2023112330", "E", 400, 0, "无 CS301 权限拒绝"),
            ("DL-E-FANG", "2023112317", "E", 200, -5, "CS301 同课程下载"),
            ("DL-G-FANG", "2023112317", "G", 200, -5, "白名单允许下载"),
            ("DL-G-LI-DENY", "2023112392", "G", 400, 0, "白名单外拒绝"),
            ("DL-A-LI", "2023112392", "A", 200, -5, "公开资料正常下载"),
            ("DL-A-FANG", "2023112317", "A", 200, -5, "公开资料正常下载"),
        ]
        uploader_by_material = {
            "A": "2023112379",
            "E": "2023112318",
            "F": "2023112330",
            "G": "2023116100",
        }
        batch_users = {
            item[1] for item in operations
        } | {
            uploader_by_material[item[2]]
            for item in operations
            if item[3] == 200
        }
        batch_before = {
            student_id: self.get_balance(student_id)
            for student_id in batch_users
        }
        expected_net = {student_id: 0 for student_id in batch_users}
        for _, downloader_id, material_label, expected_status, delta, _ in operations:
            if expected_status != 200:
                continue
            price = -delta
            expected_net[downloader_id] -= price
            expected_net[uploader_by_material[material_label]] += price

        with ThreadPoolExecutor(max_workers=9) as executor:
            future_map = {
                executor.submit(
                    self.download_worker,
                    item[0],
                    item[1],
                    item[2],
                    item[3],
                ): item
                for item in operations
            }
            for future in as_completed(future_map):
                expected = future_map[future]
                (
                    operation_id,
                    student_id,
                    material_label,
                    before,
                    after,
                    response,
                    saved,
                ) = future.result()
                actual_delta = after - before
                passed = response.status == expected[3]
                if response.status == 200:
                    expected_hash = self.results["file_hashes"][material_label]["sha256"]
                    actual_hash = hashlib.sha256(response.content).hexdigest()
                    passed = passed and expected_hash.lower() == actual_hash.lower()
                    actual = (
                        f"HTTP 200，{len(response.content)} bytes，下载哈希一致；"
                        f"批次内余额观测 {before}->{after}"
                    )
                else:
                    actual = (
                        f"HTTP {response.status}: {self.api_message(response)}，"
                        f"批次内余额观测 {before}->{after}"
                    )
                self.results["downloads"][operation_id] = {
                    "student_id": student_id,
                    "material": material_label,
                    "status": response.status,
                    "message": self.api_message(response),
                    "balance_before": before,
                    "balance_after": after,
                    "saved_file": saved,
                    "elapsed_seconds": response.elapsed,
                }
                self.add_case(
                    operation_id,
                    next(item[1] for item in ACCOUNTS if item[0] == student_id),
                    expected[5],
                    (
                        f"HTTP {expected[3]}"
                        + ("，文件哈希一致" if expected[3] == 200 else "")
                        + "；余额在并发批次结束后统一核验"
                    ),
                    actual,
                    passed,
                    balance_change=f"{before}->{after}",
                    reference=self.materials[material_label]["material_id"],
                    elapsed=response.elapsed,
                )

        batch_after = {
            student_id: self.get_balance(student_id)
            for student_id in batch_users
        }
        actual_net = {
            student_id: batch_after[student_id] - batch_before[student_id]
            for student_id in batch_users
        }
        self.results["downloads"]["batch_balance"] = {
            "before": batch_before,
            "after": batch_after,
            "expected_net": expected_net,
            "actual_net": actual_net,
        }
        self.add_case(
            "DL-BALANCE-NET",
            "九账号并发批次",
            "并发下载通证净变化",
            json.dumps(expected_net, ensure_ascii=False, sort_keys=True),
            json.dumps(actual_net, ensure_ascii=False, sort_keys=True),
            actual_net == expected_net,
            notes="同一账号可同时下载和获得上传收入，因此按整个并发批次核验净变化。",
        )

        unauth = self.request(
            "GET",
            f"/api/material/{self.materials['A']['material_id']}/download",
            timeout=30,
        )
        self.add_case(
            "DL-UNAUTH",
            "未登录用户",
            "未登录下载拦截",
            "HTTP 401",
            f"HTTP {unauth.status}: {self.api_message(unauth)}",
            unauth.status == 401,
            elapsed=unauth.elapsed,
        )

    def run_privilege_and_token_tests(self) -> None:
        xue = self.sessions["2023112385"]
        student_reward = self.request(
            "POST",
            "/api/token/reward",
            session=xue,
            json={"student_id": "2023112330", "amount": 10},
            timeout=60,
        )
        self.add_case(
            "ACL-STUDENT-REWARD",
            "薛雨凇",
            "学生调用管理员奖励",
            "HTTP 403",
            f"HTTP {student_reward.status}: {self.api_message(student_reward)}",
            student_reward.status == 403,
            elapsed=student_reward.elapsed,
        )

        student_penalty = self.request(
            "POST",
            "/api/token/penalize",
            session=xue,
            json={"student_id": "2023112380", "amount": 20},
            timeout=60,
        )
        self.add_case(
            "ACL-STUDENT-PENALTY",
            "薛雨凇",
            "学生调用管理员扣罚",
            "HTTP 403",
            f"HTTP {student_penalty.status}: {self.api_message(student_penalty)}",
            student_penalty.status == 403,
            elapsed=student_penalty.elapsed,
        )

        wang = self.sessions["2023112330"]
        student_delete = self.request(
            "DELETE",
            f"/api/material/{self.materials['E']['material_id']}",
            session=wang,
            timeout=60,
        )
        self.add_case(
            "ACL-STUDENT-DELETE",
            "王东涵",
            "学生删除他人资料",
            "HTTP 403",
            f"HTTP {student_delete.status}: {self.api_message(student_delete)}",
            student_delete.status == 403,
            elapsed=student_delete.elapsed,
        )

        update_response = self.request(
            "POST",
            f"/api/material/{self.materials['E']['material_id']}/update",
            session=self.sessions["2023112318"],
            json={
                "name": "E_操作系统进程调度复习资料_所有者更新测试.pdf",
                "course": "CS301",
                "policy_type": 1,
                "policy_value": "",
                "price": 5,
            },
            timeout=60,
        )
        detail_after_update = self.request(
            "GET",
            f"/api/material/{self.materials['E']['material_id']}",
            timeout=30,
        )
        persisted_name = (self.api_data(detail_after_update) or {}).get("name")
        update_persisted = persisted_name == "E_操作系统进程调度复习资料_所有者更新测试.pdf"
        self.add_case(
            "OWNER-UPDATE",
            "周子皓",
            "上传者修改自己的资料元数据",
            "接口成功且再次查询可见新名称",
            (
                f"更新 HTTP {update_response.status}，再次查询名称："
                f"{persisted_name}"
            ),
            update_response.status == 200 and update_persisted,
            reference=self.materials["E"]["material_id"],
            elapsed=update_response.elapsed,
        )
        if update_response.status == 200 and not update_persisted:
            self.add_issue(
                "资料更新结果未持久化",
                "资料更新接口返回成功，但再次查询仍是旧名称，链上元数据没有更新。",
                "high",
            )

        fang_before = self.get_balance("2023112317")
        tang_before = self.get_balance("2023112379")
        transfer = self.request(
            "POST",
            "/api/token/transfer",
            session=self.sessions["2023112317"],
            json={
                "to_address": self.users["2023112379"]["eth_address"],
                "amount": 3,
            },
            timeout=120,
        )
        fang_after = self.get_balance("2023112317")
        tang_after = self.get_balance("2023112379")
        transfer_data = self.api_data(transfer) or {}
        self.add_case(
            "TOKEN-TRANSFER",
            "方天宇",
            "普通用户向唐昊转账 3 EDU",
            "发送方 -3，接收方 +3，返回交易哈希",
            (
                f"HTTP {transfer.status}，方 {fang_before}->{fang_after}，"
                f"唐 {tang_before}->{tang_after}"
            ),
            (
                transfer.status == 200
                and fang_after - fang_before == -3
                and tang_after - tang_before == 3
                and bool(transfer_data.get("tx_hash"))
            ),
            balance_change=(
                f"方 {fang_before}->{fang_after}; 唐 {tang_before}->{tang_after}"
            ),
            reference=str(transfer_data.get("tx_hash") or ""),
            elapsed=transfer.elapsed,
        )

        admin = self.sessions["admin_2023112379"]
        wang_before = self.get_balance("2023112330")
        reward = self.request(
            "POST",
            "/api/token/reward",
            session=admin,
            json={
                "student_id": "2023112330",
                "amount": 10,
                "reason": "joint_test_reward",
            },
            timeout=120,
        )
        wang_after = self.get_balance("2023112330")
        reward_data = self.api_data(reward) or {}
        self.add_case(
            "ADMIN-REWARD",
            "管理员",
            "向王东涵发放 10 EDU",
            "余额增加 10 EDU",
            f"HTTP {reward.status}，余额 {wang_before}->{wang_after}",
            reward.status == 200 and wang_after - wang_before == 10,
            balance_change=f"{wang_before}->{wang_after}",
            reference=str(reward_data.get("tx_hash") or ""),
            elapsed=reward.elapsed,
        )

        yu_before = self.get_balance("2023112380")
        penalty = self.request(
            "POST",
            "/api/token/penalize",
            session=admin,
            json={
                "student_id": "2023112380",
                "amount": 20,
                "reason": "joint_test_penalty",
            },
            timeout=120,
        )
        yu_after = self.get_balance("2023112380")
        penalty_data = self.api_data(penalty) or {}
        self.add_case(
            "ADMIN-PENALTY",
            "管理员",
            "对于骐畅扣罚 20 EDU",
            "余额减少 20 EDU",
            f"HTTP {penalty.status}，余额 {yu_before}->{yu_after}",
            penalty.status == 200 and yu_after - yu_before == -20,
            balance_change=f"{yu_before}->{yu_after}",
            reference=str(penalty_data.get("tx_hash") or ""),
            elapsed=penalty.elapsed,
        )

        delete_h = self.request(
            "DELETE",
            f"/api/material/{self.materials['H']['material_id']}",
            session=admin,
            timeout=120,
        )
        detail_h = self.request(
            "GET",
            f"/api/material/{self.materials['H']['material_id']}",
            timeout=30,
        )
        h_data = self.api_data(detail_h) or {}
        admin_delete_ok = delete_h.status == 200 and h_data.get("deleted") is True
        self.add_case(
            "ADMIN-DELETE",
            "管理员",
            "管理员删除李子彤资料 H",
            "删除成功，资料标记为已删除",
            (
                f"HTTP {delete_h.status}: {self.api_message(delete_h)}，"
                f"deleted={h_data.get('deleted')}"
            ),
            admin_delete_ok,
            reference=self.materials["H"]["material_id"],
            elapsed=delete_h.elapsed,
        )
        if not admin_delete_ok:
            self.add_issue(
                "管理员无法删除其他用户资料",
                (
                    "后端权限判断允许管理员，但 MaterialRegistry.softDelete "
                    "仍要求 caller 必须等于上传者，导致管理员删除交易失败。"
                ),
                "high",
            )

    def collect_audit(self) -> None:
        admin = self.sessions["admin_2023112379"]
        global_audit = self.request(
            "GET", "/api/audit/downloads/all", session=admin, timeout=60
        )
        count = self.request("GET", "/api/audit/downloads/count", timeout=30)
        material_a = self.request(
            "GET",
            f"/api/audit/full/{self.materials['A']['material_id']}",
            timeout=60,
        )
        self.results["audit"] = {
            "global": self.api_data(global_audit),
            "count": self.api_data(count),
            "material_A": self.api_data(material_a),
        }
        records = (self.api_data(global_audit) or {}).get("records", [])
        self.add_case(
            "AUDIT-GLOBAL",
            "管理员",
            "全局下载审计",
            "管理员可读取全部成功下载记录",
            f"HTTP {global_audit.status}，记录 {len(records)} 条",
            global_audit.status == 200 and len(records) == 6,
            reference=self.materials["A"]["material_id"],
            elapsed=global_audit.elapsed,
        )

        student_audit = self.request(
            "GET",
            "/api/audit/downloads/all",
            session=self.sessions["2023112385"],
            timeout=30,
        )
        self.add_case(
            "ACL-STUDENT-AUDIT",
            "薛雨凇",
            "学生查看全局审计",
            "HTTP 403",
            f"HTTP {student_audit.status}: {self.api_message(student_audit)}",
            student_audit.status == 403,
            elapsed=student_audit.elapsed,
        )

    def write_reports(self) -> None:
        self.results["run"]["finished_at"] = (
            datetime.now().astimezone().isoformat(timespec="seconds")
        )
        passed = sum(case["passed"] for case in self.results["cases"])
        total = len(self.results["cases"])
        self.results["summary"] = {
            "passed": passed,
            "failed": total - passed,
            "total": total,
            "pass_rate_percent": round(passed / total * 100, 2) if total else 0,
        }
        self.checkpoint()

        csv_path = self.output_dir / "test_cases.csv"
        with csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "id",
                    "operator",
                    "function",
                    "expected",
                    "actual",
                    "passed",
                    "balance_change",
                    "reference",
                    "elapsed_seconds",
                    "notes",
                ],
            )
            writer.writeheader()
            writer.writerows(self.results["cases"])

        lines = [
            "# EduChain 公网九账号联动测试报告",
            "",
            f"- 服务器：`{self.base_url}`",
            f"- 开始时间：{self.results['run']['started_at']}",
            f"- 完成时间：{self.results['run']['finished_at']}",
            f"- 结果：{passed}/{total} 通过，"
            f"{self.results['summary']['pass_rate_percent']}%",
            "",
            "## 环境基线",
            "",
            f"- 测试前区块高度：{self.results['health_before'].get('block_number')}",
            f"- 测试后区块高度：{self.results['health_after'].get('block_number')}",
            f"- 测试前资料数：{self.results['health_before'].get('material_count')}",
            f"- 测试后资料数：{self.results['health_after'].get('material_count')}",
            f"- 测试后下载记录：{self.results['health_after'].get('download_count')}",
            "",
            "## 测试结果",
            "",
            "| 编号 | 操作者 | 功能 | 结论 | 实际结果 | 余额变化 |",
            "|---|---|---|---|---|---|",
        ]
        for case in self.results["cases"]:
            actual = str(case["actual"]).replace("|", "\\|").replace("\n", " ")
            lines.append(
                f"| {case['id']} | {case['operator']} | {case['function']} | "
                f"{'通过' if case['passed'] else '未通过'} | {actual} | "
                f"{case['balance_change']} |"
            )
        lines.extend(["", "## 已发现问题", ""])
        if self.results["issues"]:
            for issue in self.results["issues"]:
                lines.append(
                    f"- **{issue['severity'].upper()}：{issue['title']}**："
                    f"{issue['detail']}"
                )
        else:
            lines.append("- 本轮未发现新的功能问题。")
        lines.extend(
            [
                "",
                "## 未执行项目",
                "",
                "- 未执行后端容器重启与整套 Compose down/up 持久化测试："
                "公网 HTTP 无法控制服务器 Docker，需要 SSH 权限。",
                "- 未采集服务器后端与 Ganache 容器日志：需要 SSH 权限。",
                "",
                "原始响应、完整交易哈希、钱包地址和验证结果见 "
                "`joint_test_results.json`。",
            ]
        )
        (self.output_dir / "TEST_REPORT.md").write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8",
        )
        (RESULTS_ROOT / "LATEST.txt").write_text(
            str(self.output_dir),
            encoding="utf-8",
        )

    def run(self) -> None:
        for label, path in FILES.items():
            if not path.exists():
                raise FileNotFoundError(f"缺少测试文件 {label}: {path}")

        self.hash_files()
        self.results["health_before"] = self.health()
        health = self.results["health_before"]
        clean = health.get("material_count") == 0 and health.get("download_count") == 0
        self.add_case(
            "ENV-HEALTH",
            "管理员",
            "公网健康检查",
            "链、合约、9 个账号和 9 个钱包就绪",
            json.dumps(health, ensure_ascii=False),
            (
                health.get("status") == "running"
                and health.get("chain_connected") is True
                and health.get("contracts_ready") is True
                and health.get("users_count") == 9
                and health.get("wallets_ready") == 9
            ),
            notes=f"初始环境干净={clean}",
        )
        self.baseline_negative_tests()
        self.concurrent_login()
        self.balance_snapshot("after_login")
        self.run_uploads()
        self.balance_snapshot("after_upload")
        self.run_verification()
        self.run_downloads()
        self.balance_snapshot("after_downloads")
        self.run_privilege_and_token_tests()
        self.balance_snapshot("final")
        self.collect_audit()
        self.results["health_after"] = self.health()
        self.add_case(
            "ENV-AFTER",
            "管理员",
            "高并发操作后健康检查",
            "服务、链和合约保持正常",
            json.dumps(self.results["health_after"], ensure_ascii=False),
            (
                self.results["health_after"].get("status") == "running"
                and self.results["health_after"].get("chain_connected") is True
                and self.results["health_after"].get("contracts_ready") is True
            ),
        )
        self.write_reports()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://1.95.47.47")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()

    output_dir = args.output_dir
    if output_dir is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = RESULTS_ROOT / f"public_joint_test_{stamp}"

    test = JointTest(args.base_url, output_dir)
    try:
        test.run()
    except Exception as exc:
        test.results["run"]["aborted_at"] = (
            datetime.now().astimezone().isoformat(timespec="seconds")
        )
        test.results["run"]["error"] = f"{type(exc).__name__}: {exc}"
        test.checkpoint()
        raise

    summary = test.results["summary"]
    print(
        f"\nCompleted: {summary['passed']}/{summary['total']} passed "
        f"({summary['pass_rate_percent']}%)."
    )
    print(f"Results: {output_dir}")


if __name__ == "__main__":
    main()
