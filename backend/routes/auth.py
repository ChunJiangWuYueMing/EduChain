"""
auth.py — 认证路由

端点:
  POST /api/auth/register
  POST /api/auth/login
  GET  /api/auth/me
  POST /api/auth/logout
"""

from flask import Blueprint, request, session

from services.user_service import user_service
from services.chain_service import chain_service
from utils.response import success, bad_request, unauthorized

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    """用户注册"""
    body = request.get_json(silent=True) or {}
    student_id = body.get("student_id", "").strip()
    name = body.get("name", "").strip()
    password = body.get("password", "").strip()

    if not student_id or not name or not password:
        return bad_request("学号、姓名、密码不能为空")

    # 学号格式校验
    err = user_service.validate_student_id(student_id)
    if err:
        return bad_request(err)

    try:
        # 分配 Ganache 账户
        accounts = chain_service.get_ganache_accounts() if chain_service.is_connected() else []
        # 跳过 account[0]（deployer），找一个未使用的账户
        existing_addrs = {u.eth_address.lower() for u in user_service.get_all_users()}
        assigned_addr = None
        for i in range(1, len(accounts)):
            if accounts[i].lower() not in existing_addrs:
                assigned_addr = accounts[i]
                break
        if assigned_addr is None:
            return bad_request("暂无可用账户，请联系管理员")

        user = user_service.register_user(
            student_id=student_id,
            name=name,
            password=password,
            eth_address=assigned_addr,
        )
        return success(user.to_dict(), "注册成功")
    except ValueError as e:
        return bad_request(str(e))


@auth_bp.route("/login", methods=["POST"])
def login():
    """用户登录"""
    body = request.get_json(silent=True) or {}
    student_id = body.get("student_id", "").strip()
    password = body.get("password", "").strip()

    if not student_id or not password:
        return bad_request("学号和密码不能为空")

    user = user_service.verify_login(student_id, password)
    if user is None:
        return unauthorized("学号或密码错误")

    session["user"] = user.to_session()

    # 自动检测并发放注册奖励（首次登录余额为 0 时 +100 EDU）
    from services.token_service import token_service
    edu_balance = 0
    try:
        if chain_service.is_connected():
            edu_balance = chain_service.get_edu_balance(user.eth_address)
            if edu_balance == 0:
                token_service.reward_register(user.eth_address)
                edu_balance = 100
    except Exception:
        pass

    data = user.to_dict()
    data["edu_balance"] = edu_balance
    return success(data, "登录成功")


@auth_bp.route("/me", methods=["GET"])
def me():
    """获取当前登录用户信息"""
    user_data = session.get("user")
    if user_data is None:
        return unauthorized("未登录")

    user = user_service.get_user(user_data["student_id"])
    if user is None:
        session.pop("user", None)
        return unauthorized("用户不存在")

    return success(user.to_dict())


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """退出登录"""
    session.pop("user", None)
    return success(None, "已退出登录")
