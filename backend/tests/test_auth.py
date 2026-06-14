"""
认证模块测试

覆盖:
  1. 登录成功 / 失败
  2. 首次登录注册奖励
  3. /me 需要登录态
  4. 登出后 /me 返回 401
  5. login_required 装饰器

前置条件:
  Ganache 运行中 + 合约已部署（同 test_chain_service）

用法:
  cd backend
  python -m tests.test_auth
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app


def test_all():
    student_id = "2023112379"
    password = "123456"

    print("=" * 60)
    print("  EduChain 认证模块测试")
    print("=" * 60)

    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    # ========== 1. 未登录访问 /me ==========
    print("\n[1] 未登录访问 /me...")
    resp = client.get("/api/auth/me")
    data = resp.get_json()
    assert resp.status_code == 401, f"应返回 401，实际 {resp.status_code}"
    assert "未登录" in data["msg"]
    print(f"    ✅ 返回 401: {data['msg']}")

    # ========== 2. 登录参数缺失 ==========
    print("\n[2] 登录参数缺失...")
    resp = client.post("/api/auth/login",
                       json={"student_id": student_id})
    data = resp.get_json()
    assert resp.status_code == 400
    print(f"    ✅ 返回 400: {data['msg']}")

    # ========== 3. 登录密码错误 ==========
    print("\n[3] 登录密码错误...")
    resp = client.post("/api/auth/login",
                       json={"student_id": student_id, "password": "wrong"})
    data = resp.get_json()
    assert resp.status_code == 401
    print(f"    ✅ 返回 401: {data['msg']}")

    # ========== 4. 登录成功 ==========
    print("\n[4] 登录成功（统一测试密码）...")
    resp = client.post("/api/auth/login",
                       json={"student_id": student_id, "password": password})
    data = resp.get_json()
    assert resp.status_code == 200, f"应返回 200，实际 {resp.status_code}: {data}"
    assert data["data"]["student_id"] == student_id
    assert data["data"]["eth_address"] != ""
    print(f"    ✅ 登录成功: {data['data']['name']}")
    print(f"       eth_address: {data['data']['eth_address'][:20]}...")
    print(f"       edu_balance: {data['data']['edu_balance']}")

    if data["data"].get("first_login_reward"):
        print(f"       首次登录奖励: +{data['data']['first_login_reward']} EDU")

    # ========== 5. 已登录访问 /me ==========
    print("\n[5] 已登录访问 /me...")
    resp = client.get("/api/auth/me")
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["data"]["student_id"] == student_id
    assert "edu_balance" in data["data"]
    print(f"    ✅ 返回用户信息: {data['data']['name']}, "
          f"余额={data['data']['edu_balance']} EDU")

    # ========== 6. 已登录访问 /token/balance ==========
    print("\n[6] 已登录访问 /api/token/balance...")
    resp = client.get("/api/token/balance")
    data = resp.get_json()
    assert resp.status_code == 200
    print(f"    ✅ 余额: {data['data']['balance']} EDU")

    # ========== 7. 登出 ==========
    print("\n[7] 登出...")
    resp = client.post("/api/auth/logout")
    data = resp.get_json()
    assert resp.status_code == 200
    print(f"    ✅ {data['msg']}")

    # ========== 8. 登出后 /me 返回 401 ==========
    print("\n[8] 登出后访问 /me...")
    resp = client.get("/api/auth/me")
    data = resp.get_json()
    assert resp.status_code == 401
    print(f"    ✅ 返回 401: {data['msg']}")

    # ========== 9. 登出后 /token/balance 也返回 401 ==========
    print("\n[9] 登出后访问 /api/token/balance...")
    resp = client.get("/api/token/balance")
    data = resp.get_json()
    assert resp.status_code == 401
    print(f"    ✅ 返回 401: {data['msg']}")

    # ========== 10. 不存在的用户 ==========
    print("\n[10] 不存在的用户登录...")
    resp = client.post("/api/auth/login",
                       json={"student_id": "9999999", "password": "xxx"})
    data = resp.get_json()
    assert resp.status_code == 401
    print(f"    ✅ 返回 401: {data['msg']}")

    # ========== 总结 ==========
    print("\n" + "=" * 60)
    print("  🎉 全部测试通过！认证模块工作正常")
    print("=" * 60)
    print(f"\n  已验证接口:")
    print(f"    POST /api/auth/login   — 登录（成功/失败/参数校验）")
    print(f"    POST /api/auth/logout  — 登出")
    print(f"    GET  /api/auth/me      — 当前用户（登录态校验）")
    print(f"    GET  /api/token/balance — login_required 装饰器生效")


if __name__ == "__main__":
    test_all()
