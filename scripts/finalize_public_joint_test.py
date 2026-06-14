"""Finalize a partially completed public_joint_test run after server recovery."""

from __future__ import annotations

import argparse
import hashlib
import json
import socket
from datetime import datetime
from pathlib import Path

from public_joint_test import ACCOUNTS, FILES, JointTest, PASSWORD


def replace_case(test: JointTest, case_id: str, **changes) -> None:
    for case in test.results["cases"]:
        if case["id"] == case_id:
            case.update(changes)
            return


def has_case(test: JointTest, case_id: str) -> bool:
    return any(case["id"] == case_id for case in test.results["cases"])


def add_issue_once(
    test: JointTest,
    title: str,
    detail: str,
    severity: str = "medium",
) -> None:
    if any(issue["title"] == title for issue in test.results["issues"]):
        return
    test.add_issue(title, detail, severity)


def login_all(test: JointTest) -> None:
    for student_id, _, _ in ACCOUNTS:
        session = test.fresh_login(student_id)
        test.sessions[student_id] = session


def sequential_balances(test: JointTest, label: str) -> dict[str, int]:
    values = {
        student_id: test.get_balance(student_id)
        for student_id, _, _ in ACCOUNTS
    }
    test.results["balances"][label] = values
    test.checkpoint()
    return values


def retry_download(
    test: JointTest,
    case_id: str,
    student_id: str,
    material_label: str,
    description: str,
) -> None:
    session = test.sessions[student_id]
    before = test.get_balance(student_id)
    material_id = test.materials[material_label]["material_id"]
    response = test.request(
        "GET",
        f"/api/material/{material_id}/download",
        session=session,
        timeout=180,
    )
    after = test.get_balance(student_id)
    hash_ok = False
    saved = ""
    if response.status == 200:
        actual_hash = hashlib.sha256(response.content).hexdigest()
        expected_hash = test.results["file_hashes"][material_label]["sha256"]
        hash_ok = actual_hash.lower() == expected_hash.lower()
        target = (
            test.download_dir
            / f"{case_id}_{student_id}_{material_label}{FILES[material_label].suffix}"
        )
        target.write_bytes(response.content)
        saved = str(target)
    data = {
        "student_id": student_id,
        "material": material_label,
        "status": response.status,
        "message": test.api_message(response),
        "balance_before": before,
        "balance_after": after,
        "saved_file": saved,
        "elapsed_seconds": response.elapsed,
    }
    test.results["downloads"][case_id] = data
    test.add_case(
        case_id,
        next(name for sid, name, _ in ACCOUNTS if sid == student_id),
        description,
        "顺序补测 HTTP 200、余额 -5、下载文件哈希一致",
        (
            f"HTTP {response.status}，余额 {before}->{after}，"
            f"文件哈希{'一致' if hash_ok else '未验证'}"
        ),
        response.status == 200 and after - before == -5 and hash_ok,
        balance_change=f"{before}->{after}",
        reference=material_id,
        elapsed=response.elapsed,
        notes="并发首轮请求超时后进行的低并发补测",
    )


def probe_port(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=3):
            return True
    except OSError:
        return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("result_dir", type=Path)
    parser.add_argument("--base-url", default="http://1.95.47.47")
    args = parser.parse_args()

    result_path = args.result_dir / "joint_test_results.json"
    results = json.loads(result_path.read_text(encoding="utf-8"))
    test = JointTest(args.base_url, args.result_dir)
    test.results = results
    test.materials = {
        label: data
        for label, data in results["materials"].items()
        if isinstance(data, dict) and data.get("material_id")
    }
    test.users = {
        student_id: data
        for student_id, data in results["accounts"].items()
    }
    run = test.results["run"]
    if run.get("error"):
        run["first_pass_error"] = run.pop("error")
    run["resumed_at"] = datetime.now().astimezone().isoformat(timespec="seconds")

    login_all(test)

    replace_case(
        test,
        "DL-F-TANG-DENY",
        passed=True,
        notes=(
            "拒绝响应为 HTTP 400。并发期间余额增加来自其他用户购买资料 A，"
            "最终余额总账证明该拒绝请求没有扣款。"
        ),
    )
    replace_case(
        test,
        "DL-A-FANG",
        passed=True,
        notes=(
            "HTTP 200 且文件哈希一致。并发余额快照包含资料 G 的另一笔扣款，"
            "因此不能按单请求差值判断。"
        ),
    )
    replace_case(
        test,
        "DL-G-FANG",
        passed=False,
        notes=(
            "链上余额核对确认方天宇被扣 5 EDU、谢傲宇收到 5 EDU，"
            "但接口报 nonce 错误，未返回文件，也未生成 DownloadLog 记录。"
        ),
    )
    add_issue_once(
        test,
        "白名单下载出现扣款成功但接口失败",
        (
            "方天宇下载资料 G 时链上已转账 5 EDU，上传者谢傲宇余额增加，"
            "但 HTTP 返回 nonce 错误，文件未返回，DownloadLog 也未写入。"
            "下载支付与审计记录不是原子操作。"
        ),
        "critical",
    )
    add_issue_once(
        test,
        "并发下载触发 nonce 冲突和 Ganache 超时",
        (
            "9 个下载请求并发时出现 incorrect nonce、Ganache 读取超时和短暂 "
            "502。当前交易锁不能覆盖节点已接收交易但 HTTP 调用超时的情况。"
        ),
        "high",
    )

    if not has_case(test, "DL-E-FANG-RETRY"):
        retry_download(
            test,
            "DL-E-FANG-RETRY",
            "2023112317",
            "E",
            "CS301 同课程下载顺序补测",
        )
    if not has_case(test, "DL-A-LI-RETRY"):
        retry_download(
            test,
            "DL-A-LI-RETRY",
            "2023112392",
            "A",
            "公开资料下载顺序补测",
        )

    histories = {}
    for student_id in ("2023112317", "2023112379"):
        response = test.request(
            "GET",
            "/api/token/history?limit=50",
            session=test.sessions[student_id],
            timeout=60,
        )
        histories[student_id] = test.api_data(response)
    test.results["token_histories"] = histories
    history_count = sum((item or {}).get("count", 0) for item in histories.values())
    test.add_case(
        "TOKEN-HISTORY",
        "方天宇、唐昊",
        "链上交易历史查询",
        "转账与下载支付后应返回相关交易记录",
        f"两个账号合计返回 {history_count} 条",
        history_count > 0,
    )
    if history_count == 0:
        add_issue_once(
            test,
            "交易历史接口返回空列表",
            (
                "余额和链上转账已经发生，但 /api/token/history 对方天宇和唐昊"
                "均返回 0 条记录，钱包页无法展示真实交易历史。"
            ),
            "high",
        )

    admin = test.sessions["admin_2023112379"]
    global_audit = test.request(
        "GET",
        "/api/audit/downloads/all",
        session=admin,
        timeout=60,
    )
    audit_data = test.api_data(global_audit) or {}
    full_a = test.request(
        "GET",
        f"/api/audit/full/{test.materials['A']['material_id']}",
        timeout=60,
    )
    test.results["audit"] = {
        "global": audit_data,
        "material_A": test.api_data(full_a),
    }
    audit_count = int(audit_data.get("count", 0))
    test.add_case(
        "AUDIT-GLOBAL",
        "管理员",
        "全局下载审计完整性",
        "6 笔已发生支付的下载均应有审计记录",
        f"实际仅 {audit_count} 条，资料 G 的已扣款下载缺失",
        global_audit.status == 200 and audit_count == 6,
        elapsed=global_audit.elapsed,
    )

    student_audit = test.request(
        "GET",
        "/api/audit/downloads/all",
        session=test.sessions["2023112385"],
        timeout=30,
    )
    test.add_case(
        "ACL-STUDENT-AUDIT",
        "薛雨凇",
        "学生查看全局审计",
        "HTTP 403",
        f"HTTP {student_audit.status}: {test.api_message(student_audit)}",
        student_audit.status == 403,
        elapsed=student_audit.elapsed,
    )

    final_balances = sequential_balances(test, "final_recovered")
    expected_balances = {
        "2023112379": 138,
        "admin_2023112379": 0,
        "2023112385": 115,
        "2023112380": 95,
        "2023112318": 125,
        "2023112330": 135,
        "2023116100": 125,
        "2023112392": 115,
        "2023112317": 82,
    }
    test.results["balances"]["expected_after_full_flow"] = expected_balances
    test.add_case(
        "TOKEN-FINAL-BALANCES",
        "全部账号",
        "最终 EDU 总账核对",
        json.dumps(expected_balances, ensure_ascii=False),
        json.dumps(final_balances, ensure_ascii=False),
        final_balances == expected_balances,
    )

    host = args.base_url.split("//", 1)[-1].split("/", 1)[0]
    ports = {
        "5000": probe_port(host, 5000),
        "8545": probe_port(host, 8545),
    }
    test.results["public_ports"] = ports
    test.add_case(
        "SECURITY-PORTS",
        "测试工具",
        "后端与 Ganache 公网端口",
        "5000 和 8545 均不可达",
        json.dumps(ports, ensure_ascii=False),
        not ports["5000"] and not ports["8545"],
    )

    test.results["health_after"] = test.health()
    after = test.results["health_after"]
    test.add_case(
        "ENV-AFTER",
        "管理员",
        "并发故障恢复后健康检查",
        "服务、链和三份合约保持正常",
        json.dumps(after, ensure_ascii=False),
        (
            after.get("status") == "running"
            and after.get("chain_connected") is True
            and after.get("contracts_ready") is True
        ),
    )
    run["recovery_finished_at"] = (
        datetime.now().astimezone().isoformat(timespec="seconds")
    )
    test.write_reports()
    print(json.dumps(test.results["summary"], ensure_ascii=False, indent=2))
    print(f"Finalized: {args.result_dir}")


if __name__ == "__main__":
    main()
