"""
routes/auth.py — 用户认证路由

POST /api/auth/login   — 登录（学号 + 密码）
POST /api/auth/logout  — 登出
GET  /api/auth/me      — 当前登录用户信息（含 EDU 余额）
"""

from flask import Blueprint, request, session, g

from services.user_service import user_service
from services.token_service import token_service
from utils.response import success, bad_request, unauthorized
from utils.auth import login_required

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    登录

    请求体 JSON:
        {"student_id": "2024001", "password": "2024001"}

    成功返回用户信息 + EDU 余额，同时在 session 中写入登录态。
    首次登录自动发放 100 EDU 注册奖励。
    """
    data = request.get_json(silent=True)
    if not data:
        return bad_request("请求体必须是 JSON")

    student_id = (data.get("student_id") or "").strip()
    password = (data.get("password") or "").strip()

    if not student_id or not password:
        return bad_request("学号和密码不能为空")

    user = user_service.verify_login(student_id, password)
    if user is None:
        return unauthorized("学号或密码错误")

    # 写入 session
    session["user"] = user.to_session()

    # 查询 EDU 余额
    balance = 0
    first_login_reward = None
    try:
        balance = token_service.get_balance(user.eth_address)

        # 首次登录（余额为 0）发放注册奖励
        if balance == 0:
            reward = token_service.reward_register(user.eth_address)
            balance = token_service.get_balance(user.eth_address)
            first_login_reward = reward["amount"]
    except Exception:
        pass

    result = user.to_dict()
    result["edu_balance"] = balance
    if first_login_reward:
        result["first_login_reward"] = first_login_reward

    return success(result, msg="登录成功")


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """登出，清除 session"""
    session.clear()
    return success(msg="已登出")


@auth_bp.route("/me", methods=["GET"])
@login_required
def me():
    """
    获取当前登录用户信息

    需要已登录（Cookie 中携带 session）。
    返回用户基本信息 + 实时 EDU 余额。
    """
    user_data = g.user
    eth_address = user_data.get("eth_address", "")

    balance = 0
    try:
        balance = token_service.get_balance(eth_address)
    except Exception:
        pass

    result = {
        "student_id": user_data["student_id"],
        "name": user_data["name"],
        "eth_address": eth_address,
        "courses": user_data.get("courses", []),
        "role": user_data.get("role", "student"),
        "edu_balance": balance,
    }
    return success(result)
