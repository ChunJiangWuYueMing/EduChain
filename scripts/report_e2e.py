"""Run the report-oriented EduChain end-to-end verification flow."""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "http://localhost:8080"
ASSET_DIR = ROOT / "docs" / "report_assets"
ORIGINAL_FILE = next((ROOT / "demo").glob("original_*.pptx"))
TAMPERED_FILE = next((ROOT / "demo").glob("tampered_*.pptx"))


def timed(call):
    started = time.perf_counter()
    response = call()
    return response, round(time.perf_counter() - started, 3)


def json_body(response: requests.Response) -> dict:
    try:
        return response.json()
    except requests.JSONDecodeError as exc:
        raise AssertionError(
            f"Expected JSON from {response.request.method} {response.url}, "
            f"got HTTP {response.status_code}"
        ) from exc


def expect(response: requests.Response, status: int) -> dict:
    body = json_body(response)
    assert response.status_code == status, (
        f"{response.request.method} {response.url}: expected {status}, "
        f"got {response.status_code}: {body}"
    )
    return body


def login(student_id: str) -> tuple[requests.Session, dict, float]:
    session = requests.Session()
    response, elapsed = timed(
        lambda: session.post(
            f"{BASE_URL}/api/auth/login",
            json={"student_id": student_id, "password": student_id},
            timeout=30,
        )
    )
    return session, expect(response, 200)["data"], elapsed


def balance(session: requests.Session) -> int:
    response = session.get(f"{BASE_URL}/api/token/balance", timeout=30)
    return int(expect(response, 200)["data"]["balance"])


def upload(
    session: requests.Session,
    file_path: Path,
    *,
    course: str,
    price: int,
    name: str | None = None,
) -> tuple[requests.Response, float]:
    def request():
        with file_path.open("rb") as file_obj:
            return session.post(
                f"{BASE_URL}/api/material/upload",
                files={
                    "file": (
                        file_path.name,
                        file_obj,
                        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
                        if file_path.suffix.lower() == ".pptx"
                        else "text/plain",
                    )
                },
                data={
                    "name": name or file_path.name,
                    "course": course,
                    "price": str(price),
                    "policy_type": "0",
                },
                timeout=120,
            )

    return timed(request)


def verify(
    file_path: Path, material_id: str
) -> tuple[requests.Response, float]:
    def request():
        with file_path.open("rb") as file_obj:
            return requests.post(
                f"{BASE_URL}/api/material/verify",
                files={"file": (file_path.name, file_obj)},
                data={"material_id": material_id},
                timeout=120,
            )

    return timed(request)


def main() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    run_started = datetime.now().astimezone()

    health_before = expect(
        requests.get(f"{BASE_URL}/api/health", timeout=30), 200
    )["data"]

    bad_login_response, bad_login_seconds = timed(
        lambda: requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"student_id": "2023116101", "password": "incorrect"},
            timeout=30,
        )
    )
    bad_login = expect(bad_login_response, 401)

    uploader, uploader_user, login_uploader_seconds = login("2023116101")
    uploader_balance_before = balance(uploader)

    upload_response, upload_seconds = upload(
        uploader,
        ORIGINAL_FILE,
        course="CS201",
        price=5,
        name="区块链技术课件.pptx",
    )
    upload_data = expect(upload_response, 200)["data"]
    material_id = upload_data["material_id"]

    duplicate_response, duplicate_seconds = upload(
        uploader,
        ORIGINAL_FILE,
        course="CS201",
        price=5,
        name="区块链技术课件-重复上传.pptx",
    )
    duplicate_body = expect(duplicate_response, 400)

    original_response, verify_original_seconds = verify(
        ORIGINAL_FILE, material_id
    )
    original_verify = expect(original_response, 200)["data"]

    tampered_response, verify_tampered_seconds = verify(
        TAMPERED_FILE, material_id
    )
    tampered_verify = expect(tampered_response, 200)["data"]

    downloader, downloader_user, login_downloader_seconds = login("2023116102")
    downloader_balance_before = balance(downloader)

    download_response, download_seconds = timed(
        lambda: downloader.get(
            f"{BASE_URL}/api/material/{material_id}/download", timeout=120
        )
    )
    assert download_response.status_code == 200, download_response.text
    download_bytes = len(download_response.content)
    downloader_balance_after = balance(downloader)
    uploader_balance_after = balance(uploader)

    audit_material = expect(
        requests.get(
            f"{BASE_URL}/api/audit/downloads/material/{material_id}",
            timeout=30,
        ),
        200,
    )["data"]
    full_audit = expect(
        requests.get(
            f"{BASE_URL}/api/audit/full/{material_id}", timeout=30
        ),
        200,
    )["data"]

    unauthenticated_response = requests.get(
        f"{BASE_URL}/api/material/{material_id}/download", timeout=30
    )
    unauthenticated_body = expect(unauthenticated_response, 401)

    # Use a disposable third account to create an expensive material, verify
    # that a normal student cannot buy it, and soft-delete it afterwards.
    seller, seller_user, login_seller_seconds = login("2023116103")
    high_price_file = ASSET_DIR / "insufficient_balance_test.txt"
    high_price_file.write_text(
        f"EduChain insufficient-balance test {run_started.isoformat()}",
        encoding="utf-8",
    )
    high_price_response, high_price_upload_seconds = upload(
        seller,
        high_price_file,
        course="CS301",
        price=999,
        name="余额不足测试资料.txt",
    )
    high_price_data = expect(high_price_response, 200)["data"]
    high_price_id = high_price_data["material_id"]

    balance_before_rejection = balance(downloader)
    insufficient_response, insufficient_seconds = timed(
        lambda: downloader.get(
            f"{BASE_URL}/api/material/{high_price_id}/download", timeout=120
        )
    )
    insufficient_body = expect(insufficient_response, 400)
    balance_after_rejection = balance(downloader)

    delete_response = seller.delete(
        f"{BASE_URL}/api/material/{high_price_id}", timeout=120
    )
    delete_body = expect(delete_response, 200)

    active_materials = expect(
        requests.get(
            f"{BASE_URL}/api/material/list",
            params={"page": 1, "page_size": 20},
            timeout=30,
        ),
        200,
    )["data"]
    health_after = expect(
        requests.get(f"{BASE_URL}/api/health", timeout=30), 200
    )["data"]

    results = {
        "run": {
            "started_at": run_started.isoformat(timespec="seconds"),
            "finished_at": datetime.now().astimezone().isoformat(
                timespec="seconds"
            ),
            "base_url": BASE_URL,
        },
        "users": {
            "uploader": {
                "student_id": uploader_user["student_id"],
                "name": uploader_user["name"],
                "address": uploader_user["eth_address"],
            },
            "downloader": {
                "student_id": downloader_user["student_id"],
                "name": downloader_user["name"],
                "address": downloader_user["eth_address"],
            },
            "test_seller": {
                "student_id": seller_user["student_id"],
                "name": seller_user["name"],
                "address": seller_user["eth_address"],
            },
        },
        "material": {
            "material_id": material_id,
            "name": upload_data.get("name"),
            "sha256_hash": upload_data.get("sha256_hash"),
            "sim_hash": upload_data.get("sim_hash"),
            "text_length": upload_data.get("text_length"),
            "tx_hash": upload_data.get("tx_hash"),
            "upload_reward": upload_data.get("upload_reward"),
            "price": 5,
            "course": "CS201",
        },
        "verification": {
            "original": original_verify,
            "tampered": tampered_verify,
        },
        "balances": {
            "uploader_before": uploader_balance_before,
            "uploader_after": uploader_balance_after,
            "downloader_before": downloader_balance_before,
            "downloader_after": downloader_balance_after,
            "downloader_before_insufficient": balance_before_rejection,
            "downloader_after_insufficient": balance_after_rejection,
        },
        "audit": {
            "download_count_for_material": audit_material["count"],
            "records": audit_material["records"],
            "full_audit": full_audit,
        },
        "negative_tests": {
            "invalid_login": {
                "status": bad_login_response.status_code,
                "message": bad_login.get("msg"),
            },
            "duplicate_upload": {
                "status": duplicate_response.status_code,
                "message": duplicate_body.get("msg"),
            },
            "unauthenticated_download": {
                "status": unauthenticated_response.status_code,
                "message": unauthenticated_body.get("msg"),
            },
            "insufficient_balance": {
                "status": insufficient_response.status_code,
                "message": insufficient_body.get("msg"),
                "test_material_id": high_price_id,
                "test_material_deleted": delete_response.status_code == 200,
                "delete_message": delete_body.get("msg"),
            },
        },
        "timings_seconds": {
            "invalid_login": bad_login_seconds,
            "login_uploader": login_uploader_seconds,
            "upload": upload_seconds,
            "duplicate_rejection": duplicate_seconds,
            "verify_original": verify_original_seconds,
            "verify_tampered": verify_tampered_seconds,
            "login_downloader": login_downloader_seconds,
            "download": download_seconds,
            "login_test_seller": login_seller_seconds,
            "high_price_upload": high_price_upload_seconds,
            "insufficient_rejection": insufficient_seconds,
        },
        "download": {
            "http_status": download_response.status_code,
            "bytes": download_bytes,
            "content_type": download_response.headers.get("Content-Type"),
        },
        "health_before": health_before,
        "health_after": health_after,
        "active_materials": {
            "total": active_materials.get("total"),
            "item_ids": [
                item.get("material_id") or item.get("id")
                for item in active_materials.get("items", [])
            ],
        },
    }

    output = ASSET_DIR / "report_e2e_results.json"
    output.write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"\nSaved: {output}")


if __name__ == "__main__":
    main()
