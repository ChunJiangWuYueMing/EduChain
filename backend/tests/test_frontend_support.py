import importlib
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


class FrontendSupportTests(unittest.TestCase):
    def create_app(self):
        with mock.patch.dict(
            os.environ,
            {"GANACHE_URL": "http://127.0.0.1:8545"},
            clear=False,
        ):
            app_module = importlib.import_module("app")
            app_module = importlib.reload(app_module)
        return app_module, app_module.create_app()

    def test_global_audit_requires_admin_and_returns_records(self):
        _, app = self.create_app()
        client = app.test_client()

        response = client.get("/api/audit/downloads/all")
        self.assertEqual(response.status_code, 401)

        with client.session_transaction() as session:
            session["user"] = {
                "student_id": "2023116101",
                "eth_address": "0x0000000000000000000000000000000000000001",
            }

        with mock.patch("routes.audit.user_service.is_admin", return_value=False):
            response = client.get("/api/audit/downloads/all")
        self.assertEqual(response.status_code, 403)

        record = SimpleNamespace(to_dict=lambda: {"material_id": "MAT_TEST_001"})
        with mock.patch("routes.audit.user_service.is_admin", return_value=True):
            with mock.patch(
                "routes.audit.chain_service.get_all_downloads",
                return_value=[record],
            ):
                response = client.get("/api/audit/downloads/all")

        payload = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["data"]["count"], 1)
        self.assertEqual(payload["data"]["records"][0]["material_id"], "MAT_TEST_001")

    def test_health_returns_chain_id_from_connected_node(self):
        _, app = self.create_app()
        chain_module = importlib.import_module("services.chain_service")
        client = app.test_client()

        with mock.patch.object(chain_module.chain_service, "is_connected", return_value=True):
            with mock.patch.object(chain_module.chain_service, "get_block_number", return_value=12):
                with mock.patch.object(chain_module.chain_service, "get_chain_id", return_value=1337):
                    with mock.patch.object(chain_module.chain_service, "get_material_count", return_value=3):
                        with mock.patch.object(chain_module.chain_service, "get_download_count", return_value=5):
                            response = client.get("/api/health")

        payload = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["data"]["chain_id"], 1337)
        self.assertEqual(payload["data"]["block_number"], 12)

    def test_token_history_includes_timestamp_and_caches_block_reads(self):
        token_module = importlib.import_module("services.token_service")
        address = "0x0000000000000000000000000000000000000001"
        other = "0x0000000000000000000000000000000000000002"

        class TxHash:
            @staticmethod
            def hex():
                return "ab" * 32

        receive_event = {
            "args": {"from": other, "to": address, "value": 8},
            "blockNumber": 7,
            "transactionHash": TxHash(),
        }
        send_event = {
            "args": {"from": address, "to": other, "value": 3},
            "blockNumber": 7,
            "transactionHash": TxHash(),
        }

        class TransferEvent:
            @staticmethod
            def get_logs(fromBlock, toBlock):
                assert fromBlock == 0
                assert toBlock == "latest"
                return [receive_event, send_event]

        get_block = mock.Mock(return_value={"timestamp": 1_700_000_000})
        fake_chain = SimpleNamespace(
            _token=SimpleNamespace(events=SimpleNamespace(Transfer=TransferEvent())),
            w3=SimpleNamespace(
                to_checksum_address=lambda value: value,
                eth=SimpleNamespace(get_block=get_block),
            ),
        )

        with mock.patch.object(token_module, "chain_service", fake_chain):
            history = token_module.TokenService.get_transaction_history(address)

        self.assertEqual(len(history), 2)
        self.assertTrue(all(item["timestamp"] == 1_700_000_000 for item in history))
        get_block.assert_called_once_with(7)

    def test_deletion_event_matches_indexed_string_hash_without_hex_prefix(self):
        chain_module = importlib.import_module("services.chain_service")
        material_id = "MAT_DELETE_001"
        event = SimpleNamespace(
            args=SimpleNamespace(
                id=bytes(chain_module.Web3.keccak(text=material_id)),
                caller="0x0000000000000000000000000000000000000001",
                timestamp=1_700_000_000,
            )
        )

        class DeletedEvent:
            @staticmethod
            def get_logs(fromBlock, toBlock):
                return [event]

        service = chain_module.ChainService()
        service._initialized = True
        service._registry = SimpleNamespace(
            events=SimpleNamespace(MaterialDeleted=DeletedEvent())
        )
        records = service.get_deletions_by_material(material_id)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].material_id, material_id)


if __name__ == "__main__":
    unittest.main()
