import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from flask import Flask


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from config import config
from routes.auth import auth_bp
from routes.token import token_bp
from services.token_service import TokenService
from services.user_service import UserService


class ServerTestModeTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(TESTING=True, SECRET_KEY="server-test-secret")
        self.app.register_blueprint(auth_bp, url_prefix="/api/auth")
        self.app.register_blueprint(token_bp, url_prefix="/api/token")
        self.client = self.app.test_client()

    def login_admin_session(self):
        with self.client.session_transaction() as session:
            session["user"] = {
                "student_id": "admin_2023112379",
                "role": "admin",
                "eth_address": "0x0000000000000000000000000000000000000002",
            }

    @staticmethod
    def derive_accounts(count=10):
        from eth_account import Account

        Account.enable_unaudited_hdwallet_features()
        accounts = []
        for index in range(count):
            account = Account.from_mnemonic(
                config.GANACHE_MNEMONIC,
                account_path=f"m/44'/60'/0'/0/{index}",
            )
            accounts.append(account.address)
        return accounts

    def test_seed_contains_eight_students_one_admin_and_unique_indexes(self):
        seed = json.loads(
            (BACKEND_DIR / "users.seed.json").read_text(encoding="utf-8")
        )["users"]
        self.assertEqual(len(seed), 9)
        self.assertEqual(sum(item["role"] == "student" for item in seed), 8)
        self.assertEqual(sum(item["role"] == "admin" for item in seed), 1)
        self.assertEqual(len({item["student_id"] for item in seed}), 9)
        self.assertEqual(len({item["account_index"] for item in seed}), 9)
        self.assertNotIn(0, {item["account_index"] for item in seed})

    def test_runtime_initialization_is_idempotent_and_all_logins_work(self):
        accounts = self.derive_accounts()
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_file = Path(temp_dir) / "users.json"
            with mock.patch.object(config, "USERS_FILE", str(runtime_file)):
                with mock.patch.object(
                    config,
                    "USERS_SEED_FILE",
                    str(BACKEND_DIR / "users.seed.json"),
                ):
                    service = UserService()
                    self.assertTrue(service.initialize_runtime_users(accounts))
                    first_content = runtime_file.read_text(encoding="utf-8")
                    self.assertFalse(service.initialize_runtime_users(accounts))
                    self.assertEqual(
                        runtime_file.read_text(encoding="utf-8"),
                        first_content,
                    )
                    service.init_users(accounts)

                    users = service.get_all_users()
                    self.assertEqual(len(users), 9)
                    self.assertEqual(len({user.eth_address.lower() for user in users}), 9)
                    for user in users:
                        self.assertIsNotNone(
                            service.verify_login(user.student_id, "123456")
                        )
                    self.assertTrue(service.is_admin("admin_2023112379"))
                    self.assertNotEqual(
                        service.get_user("2023112379").eth_address,
                        service.get_user("admin_2023112379").eth_address,
                    )

    def test_server_compose_only_publishes_frontend_port(self):
        compose = (PROJECT_DIR / "docker-compose.server.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn('- "80:80"', compose)
        self.assertNotIn('- "5000:5000"', compose)
        self.assertNotIn('- "8545:8545"', compose)
        self.assertIn('ALLOW_PUBLIC_REGISTRATION: "false"', compose)
        self.assertIn('SERVER_MODE: "1"', compose)

    def test_server_mode_rejects_public_registration(self):
        with mock.patch.object(config, "ALLOW_PUBLIC_REGISTRATION", False):
            response = self.client.post(
                "/api/auth/register",
                json={
                    "student_id": "2023999999",
                    "name": "临时用户",
                    "password": "123456",
                },
            )
        self.assertEqual(response.status_code, 403)
        self.assertIn("统一创建", response.get_json()["msg"])

    def test_admin_reward_and_penalty_forward_requested_amounts(self):
        self.login_admin_session()
        target = SimpleNamespace(
            eth_address="0x0000000000000000000000000000000000000003"
        )
        with mock.patch(
            "routes.token.user_service.is_admin",
            return_value=True,
        ), mock.patch(
            "routes.token.user_service.get_user",
            return_value=target,
        ), mock.patch(
            "routes.token.token_service.reward",
            return_value={"tx_hash": "0xreward"},
        ) as reward, mock.patch(
            "routes.token.token_service.penalize_plagiarism",
            return_value={"tx_hash": "0xpenalty"},
        ) as penalize:
            reward_response = self.client.post(
                "/api/token/reward",
                json={
                    "student_id": "2023112385",
                    "amount": 25,
                    "reason": "joint_test_reward",
                },
            )
            penalty_response = self.client.post(
                "/api/token/penalize",
                json={
                    "student_id": "2023112385",
                    "amount": 20,
                    "reason": "joint_test_penalty",
                },
            )

        self.assertEqual(reward_response.status_code, 200)
        self.assertEqual(penalty_response.status_code, 200)
        reward.assert_called_once_with(
            target.eth_address,
            25,
            "joint_test_reward",
        )
        penalize.assert_called_once_with(
            target.eth_address,
            "joint_test_penalty",
            amount=20,
        )

    def test_admin_penalty_rejects_non_positive_amount(self):
        self.login_admin_session()
        with mock.patch(
            "routes.token.user_service.is_admin",
            return_value=True,
        ), mock.patch("routes.token.token_service.penalize_plagiarism") as penalize:
            response = self.client.post(
                "/api/token/penalize",
                json={"student_id": "2023112385", "amount": 0},
            )
        self.assertEqual(response.status_code, 400)
        penalize.assert_not_called()

    def test_admin_never_receives_automatic_register_reward(self):
        service = TokenService()
        admin = SimpleNamespace(
            student_id="admin_2023112379",
            role="admin",
            eth_address="0x0000000000000000000000000000000000000002",
        )
        with mock.patch(
            "services.token_service.chain_service.get_edu_balance",
            return_value=0,
        ):
            with mock.patch.object(service, "reward_register") as reward:
                balance, granted = service.ensure_register_reward(
                    admin,
                    SimpleNamespace(),
                )
        self.assertEqual((balance, granted), (0, 0))
        reward.assert_not_called()

    def test_student_register_reward_is_persistently_idempotent(self):
        service = TokenService()
        student = SimpleNamespace(
            student_id="2023112379",
            role="student",
            eth_address="0x0000000000000000000000000000000000000001",
            register_reward_granted=False,
        )

        class FakeUsers:
            def get_user(self, student_id):
                return student

            def mark_register_reward_granted(self, student_id):
                student.register_reward_granted = True

        balances = [0, 100, 100]
        with mock.patch(
            "services.token_service.chain_service.get_edu_balance",
            side_effect=balances,
        ):
            with mock.patch.object(
                service,
                "reward_register",
                return_value={"amount": 100},
            ) as reward:
                first = service.ensure_register_reward(student, FakeUsers())
                second = service.ensure_register_reward(student, FakeUsers())

        self.assertEqual(first, (100, 100))
        self.assertEqual(second, (100, 0))
        reward.assert_called_once()


if __name__ == "__main__":
    unittest.main()
