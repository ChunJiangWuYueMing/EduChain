import importlib
import os
import sys
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


class LocalAppBehaviorTests(unittest.TestCase):
    def test_default_ganache_url_uses_localhost_for_local_runs(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            config_module = importlib.import_module("config")
            config_module = importlib.reload(config_module)

        self.assertEqual(config_module.config.GANACHE_URL, "http://127.0.0.1:8545")

    def test_chain_service_falls_back_to_localhost_when_docker_hostname_is_unreachable(self):
        config_module = importlib.import_module("config")
        chain_module = importlib.import_module("services.chain_service")

        config_module.config.GANACHE_URL = "http://ganache:8545"
        config_module.config.EDU_TOKEN_ADDRESS = "0x0000000000000000000000000000000000000001"
        config_module.config.MATERIAL_REGISTRY_ADDRESS = "0x0000000000000000000000000000000000000002"
        config_module.config.DOWNLOAD_LOG_ADDRESS = "0x0000000000000000000000000000000000000003"

        class FakeWeb3:
            def __init__(self, provider):
                self.provider = provider
                self.eth = SimpleNamespace(accounts=["0xdeployer", "0xuser1"])

            def is_connected(self):
                return self.provider == "http://127.0.0.1:8545"

            @staticmethod
            def HTTPProvider(url):
                return url

        service = chain_module.ChainService()
        with mock.patch.object(chain_module, "Web3", FakeWeb3):
            with mock.patch.object(service, "_get_contract", return_value=object()):
                service.init_app()

        self.assertEqual(config_module.config.GANACHE_URL, "http://127.0.0.1:8545")
        self.assertEqual(service.deployer, "0xdeployer")

    def test_frontend_routes_fall_back_to_index_html(self):
        try:
            import flask  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("Flask is not installed in the active Python runtime")

        with mock.patch.dict(os.environ, {"GANACHE_URL": "http://127.0.0.1:8545"}, clear=False):
            app_module = importlib.import_module("app")
            app_module = importlib.reload(app_module)

        app = app_module.create_app()
        client = app.test_client()

        root_response = client.get("/")
        route_response = client.get("/wallet")

        self.assertEqual(root_response.status_code, 200)
        self.assertEqual(route_response.status_code, 200)
        self.assertIn("EduChain", root_response.get_data(as_text=True))
        self.assertIn("EduChain", route_response.get_data(as_text=True))

    def test_api_routes_are_not_swallowed_by_frontend_fallback(self):
        try:
            import flask  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("Flask is not installed in the active Python runtime")

        with mock.patch.dict(os.environ, {"GANACHE_URL": "http://127.0.0.1:8545"}, clear=False):
            app_module = importlib.import_module("app")
            app_module = importlib.reload(app_module)

        app = app_module.create_app()
        client = app.test_client()
        response = client.get("/api/auth/me")
        payload = response.get_json()

        self.assertEqual(response.status_code, 401)
        self.assertIsInstance(payload, dict)
        self.assertEqual(payload["code"], 401)

    def test_material_list_returns_empty_payload_when_chain_is_unavailable(self):
        try:
            import flask  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("Flask is not installed in the active Python runtime")

        with mock.patch.dict(os.environ, {"GANACHE_URL": "http://127.0.0.1:8545"}, clear=False):
            app_module = importlib.import_module("app")
            app_module = importlib.reload(app_module)

        app = app_module.create_app()
        client = app.test_client()

        empty_result = {"total": 0, "page": 1, "page_size": 8, "items": []}
        with mock.patch("routes.material.material_service.list_materials", return_value=empty_result):
            response = client.get("/api/material/list?page=1&page_size=8")

        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["code"], 200)
        self.assertEqual(payload["data"]["items"], [])

    def test_zero_byte_upload_is_rejected_before_fingerprint_processing(self):
        try:
            import flask  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("Flask is not installed in the active Python runtime")

        with mock.patch.dict(os.environ, {"GANACHE_URL": "http://127.0.0.1:8545"}, clear=False):
            app_module = importlib.import_module("app")
            app_module = importlib.reload(app_module)

        app = app_module.create_app()
        client = app.test_client()
        with client.session_transaction() as session:
            session["user"] = {"student_id": "2023116100", "eth_address": "0xabc"}

        with mock.patch("routes.material.material_service.upload") as upload_mock:
            response = client.post(
                "/api/material/upload",
                data={
                    "file": (BytesIO(b""), "empty.docx"),
                    "course": "CS201",
                    "price": "5",
                    "policy_type": "0",
                },
                content_type="multipart/form-data",
            )

        payload = response.get_json()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(payload["code"], 400)
        upload_mock.assert_not_called()

    def test_material_list_rejects_invalid_pagination(self):
        try:
            import flask  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("Flask is not installed in the active Python runtime")

        with mock.patch.dict(os.environ, {"GANACHE_URL": "http://127.0.0.1:8545"}, clear=False):
            app_module = importlib.import_module("app")
            app_module = importlib.reload(app_module)

        app = app_module.create_app()
        client = app.test_client()
        response = client.get("/api/material/list?page=abc&page_size=8")
        payload = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(payload["code"], 400)

    def test_upload_uses_material_id_for_stored_filename(self):
        material_module = importlib.import_module("services.material_service")

        with tempfile.TemporaryDirectory() as temp_dir:
            upload_path = Path(temp_dir) / "upload.txt"
            upload_path.write_text("sample content", encoding="utf-8")

            fp = SimpleNamespace(
                sha256_hash=b"\x01" * 32,
                sha256_hex="01" * 32,
                sim_hash=123,
                text_length=14,
            )

            chain = SimpleNamespace(
                get_material_by_hash=mock.Mock(return_value=""),
                get_material_count=mock.Mock(return_value=0),
                register_material=mock.Mock(return_value={"transactionHash": bytes.fromhex("02" * 32)}),
            )
            fake_uuid = SimpleNamespace(hex="abcdef0123456789")

            with mock.patch.object(material_module.config, "UPLOAD_FOLDER", temp_dir):
                with mock.patch.object(material_module, "compute_fingerprint", return_value=fp):
                    with mock.patch.object(material_module, "chain_service", chain):
                        with mock.patch.object(material_module.time, "time", return_value=123456):
                            with mock.patch.object(material_module.uuid, "uuid4", return_value=fake_uuid):
                                result = material_module.MaterialService.upload(
                                    file_path=str(upload_path),
                                    original_name="资料?复习",
                                    course="CS201",
                                    uploader_address="0x0000000000000000000000000000000000000001",
                                    price=5,
                                )

            self.assertEqual(result.material_id, "MAT_123456_abcdef01")
            stored_files = [p.name for p in Path(temp_dir).iterdir()]
            self.assertEqual(stored_files, ["MAT_123456_abcdef01.txt"])

    def test_download_name_keeps_stored_file_extension(self):
        material_module = importlib.import_module("services.material_service")

        with tempfile.TemporaryDirectory() as temp_dir:
            stored = Path(temp_dir) / "MAT_001_original.pptx"
            stored.write_bytes(b"pptx bytes")
            material = SimpleNamespace(
                uploader="0x0000000000000000000000000000000000000001",
                deleted=False,
                price=0,
                sha256_hash="0x" + "0" * 64,
                sim_hash=0,
                name="大学物理模板",
            )
            chain = SimpleNamespace(
                query_material=mock.Mock(return_value=material),
                get_downloads_by_material=mock.Mock(return_value=[]),
                record_download=mock.Mock(),
            )
            verification = SimpleNamespace(is_tampered=False)

            with mock.patch.object(material_module.config, "UPLOAD_FOLDER", temp_dir):
                with mock.patch.object(material_module, "chain_service", chain):
                    with mock.patch.object(material_module, "verify_file_integrity", return_value=verification):
                        result = material_module.MaterialService.download(
                            material_id="MAT_001",
                            downloader_address=material.uploader,
                            downloader_courses=[],
                        )

            self.assertEqual(result.file_name, "大学物理模板.pptx")

    def test_verify_temp_file_uses_original_extension_when_download_name_has_none(self):
        try:
            import flask  # noqa: F401
        except ModuleNotFoundError:
            self.skipTest("Flask is not installed in the active Python runtime")

        with mock.patch.dict(os.environ, {"GANACHE_URL": "http://127.0.0.1:8545"}, clear=False):
            app_module = importlib.import_module("app")
            app_module = importlib.reload(app_module)

        app = app_module.create_app()
        client = app.test_client()

        with tempfile.TemporaryDirectory() as temp_dir:
            original = Path(temp_dir) / "MAT_001_original.pptx"
            original.write_bytes(b"pptx bytes")
            captured = {}

            def fake_verify(file_path, material_id):
                captured["file_path"] = Path(file_path)
                captured["material_id"] = material_id
                return {"ok": True}

            with mock.patch("routes.material.config.UPLOAD_FOLDER", temp_dir):
                with mock.patch("routes.material.material_service.verify", side_effect=fake_verify):
                    response = client.post(
                        "/api/material/verify",
                        data={
                            "material_id": "MAT_001",
                            "file": (BytesIO(b"downloaded bytes"), "大学物理模板"),
                        },
                        content_type="multipart/form-data",
                    )

            payload = response.get_json()
            self.assertEqual(response.status_code, 200)
            self.assertEqual(payload["code"], 200)
            self.assertEqual(captured["material_id"], "MAT_001")
            self.assertEqual(captured["file_path"].suffix, ".pptx")

    def test_deploy_derived_keys_have_single_hex_prefix(self):
        deploy_module = importlib.import_module("scripts.deploy")
        keys = deploy_module.derive_keys(deploy_module.DEFAULT_MNEMONIC, count=1)

        self.assertTrue(keys[0]["private_key"].startswith("0x"))
        self.assertFalse(keys[0]["private_key"].startswith("0x0x"))
        self.assertEqual(len(keys[0]["private_key"]), 66)

    def test_send_signed_tx_accepts_camel_case_raw_transaction(self):
        chain_module = importlib.import_module("services.chain_service")
        service = chain_module.ChainService()

        class FakeContractFn:
            @staticmethod
            def build_transaction(tx):
                return tx

        class FakeAccount:
            @staticmethod
            def sign_transaction(tx, private_key):
                return SimpleNamespace(rawTransaction=b"signed-raw-tx")

        class FakeEth:
            gas_price = 1
            account = FakeAccount()

            def __init__(self):
                self.sent_raw_tx = None

            @staticmethod
            def get_transaction_count(address, block_identifier=None):
                assert block_identifier == "pending"
                return 7

            def send_raw_transaction(self, raw_tx):
                self.sent_raw_tx = raw_tx
                return bytes.fromhex("03" * 32)

            @staticmethod
            def wait_for_transaction_receipt(tx_hash, timeout=30):
                return {"status": 1, "transactionHash": tx_hash}

        fake_eth = FakeEth()
        service.w3 = SimpleNamespace(eth=fake_eth)

        receipt = service._send_signed_tx(
            FakeContractFn(),
            private_key="0x" + "1" * 64,
            from_addr="0x0000000000000000000000000000000000000001",
        )

        self.assertEqual(fake_eth.sent_raw_tx, b"signed-raw-tx")
        self.assertEqual(receipt["status"], 1)

    def test_material_metadata_update_is_persisted_and_applied(self):
        material_module = importlib.import_module("services.material_service")
        chain_module = importlib.import_module("services.chain_service")
        material = chain_module.MaterialData(
            id="MAT_META_001",
            name="旧名称",
            course="CS201",
            uploader="0x0000000000000000000000000000000000000001",
            sha256_hash="0x" + "1" * 64,
            sim_hash=1,
            text_length=10,
            policy_type=0,
            policy_value="",
            price=5,
            version=1,
            deleted=False,
            timestamp=1,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            metadata_file = Path(temp_dir) / "material_metadata.json"
            with mock.patch.object(
                material_module.config,
                "MATERIAL_METADATA_FILE",
                str(metadata_file),
            ):
                material_module.MaterialService.update_metadata(
                    material.id,
                    name="新名称",
                    course="CS301",
                    policy_type=1,
                    policy_value="CS301",
                    price=9,
                )
                with mock.patch.object(
                    material_module.chain_service,
                    "query_material",
                    return_value=material,
                ):
                    result = material_module.MaterialService.get_material(
                        material.id
                    )

            self.assertTrue(metadata_file.exists())
            self.assertEqual(result["name"], "新名称")
            self.assertEqual(result["course"], "CS301")
            self.assertEqual(result["price"], 9)

    def test_paid_download_is_refunded_when_audit_write_fails(self):
        material_module = importlib.import_module("services.material_service")
        chain_module = importlib.import_module("services.chain_service")
        uploader = "0x0000000000000000000000000000000000000001"
        downloader = "0x0000000000000000000000000000000000000002"
        material = chain_module.MaterialData(
            id="MAT_REFUND_001",
            name="退款测试",
            course="CS201",
            uploader=uploader,
            sha256_hash="0x" + "2" * 64,
            sim_hash=2,
            text_length=10,
            policy_type=0,
            policy_value="",
            price=5,
            version=1,
            deleted=False,
            timestamp=1,
        )

        class FakeChain:
            def __init__(self):
                self.balances = {uploader: 20, downloader: 100}

            def query_material(self, material_id):
                return material

            def get_edu_balance(self, address):
                return self.balances[address]

            def get_downloads_by_material(self, material_id):
                return []

            def download_material(self, material_id, address):
                self.balances[downloader] -= material.price
                self.balances[uploader] += material.price
                return {"transactionHash": bytes.fromhex("04" * 32)}

            def record_download(self, **kwargs):
                raise TimeoutError("audit timeout")

            def transfer_edu(self, from_addr, to_addr, amount):
                self.balances[from_addr] -= amount
                self.balances[to_addr] += amount
                return {"transactionHash": bytes.fromhex("05" * 32)}

        fake_chain = FakeChain()
        verification = SimpleNamespace(is_tampered=False)
        with tempfile.TemporaryDirectory() as temp_dir:
            stored = Path(temp_dir) / "MAT_REFUND_001.txt"
            stored.write_text("refund test", encoding="utf-8")
            with mock.patch.object(material_module.config, "UPLOAD_FOLDER", temp_dir):
                with mock.patch.object(material_module, "chain_service", fake_chain):
                    with mock.patch.object(
                        material_module,
                        "verify_file_integrity",
                        return_value=verification,
                    ):
                        with self.assertRaisesRegex(
                            RuntimeError,
                            "支付已自动退回",
                        ):
                            material_module.MaterialService.download(
                                material.id,
                                downloader,
                                [],
                            )

        self.assertEqual(fake_chain.balances[downloader], 100)
        self.assertEqual(fake_chain.balances[uploader], 20)

    def test_admin_delete_passes_uploader_to_legacy_contract(self):
        from flask import Flask

        material_routes = importlib.import_module("routes.material")
        user_module = importlib.import_module("services.user_service")
        app = Flask(__name__)
        app.config.update(TESTING=True, SECRET_KEY="test")
        app.register_blueprint(
            material_routes.material_bp,
            url_prefix="/api/material",
        )
        client = app.test_client()
        admin_address = "0x0000000000000000000000000000000000000009"
        uploader = "0x0000000000000000000000000000000000000001"
        with client.session_transaction() as session:
            session["user"] = {
                "student_id": "admin_2023112379",
                "eth_address": admin_address,
            }

        material_data = {
            "id": "MAT_ADMIN_DELETE",
            "uploader": uploader,
        }
        with mock.patch.object(
            material_routes.material_service,
            "get_material",
            return_value=material_data,
        ), mock.patch.object(
            user_module.user_service,
            "is_admin",
            return_value=True,
        ), mock.patch.object(
            material_routes.material_service,
            "soft_delete",
            return_value={"deleted": True},
        ) as soft_delete:
            response = client.delete(
                "/api/material/MAT_ADMIN_DELETE"
            )

        self.assertEqual(response.status_code, 200)
        soft_delete.assert_called_once_with("MAT_ADMIN_DELETE", uploader)


if __name__ == "__main__":
    unittest.main()
