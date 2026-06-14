"""
auth.py — 认证路由

端点:
  POST /api/auth/register
  POST /api/auth/login
  GET  /api/auth/me
  POST /api/auth/logout
"""

from flask import Blueprint, request, session

from config import config
from services.user_service import user_service
from services.chain_service import chain_service
from utils.response import success, bad_request, forbidden, unauthorized

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    """用户注册"""
    if not config.ALLOW_PUBLIC_REGISTRATION:
        return forbidden("当前为课程测试环境，账号已由管理员统一创建。")

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

    # 学生首次登录奖励。管理员不参与，且并发登录只会发放一次。
    from services.token_service import token_service
    edu_balance = 0
    first_login_reward = 0
    try:
        if chain_service.is_connected():
            edu_balance, first_login_reward = token_service.ensure_register_reward(
                user,
                user_service,
            )
    except Exception as exc:
        from flask import current_app
        current_app.logger.error("首次登录奖励处理失败: %s", exc)
        try:
            edu_balance = chain_service.get_edu_balance(user.eth_address)
        except Exception:
            edu_balance = 0

    data = user.to_dict()
    data["edu_balance"] = edu_balance
    data["first_login_reward"] = first_login_reward
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

    data = user.to_dict()
    try:
        data["edu_balance"] = chain_service.get_edu_balance(user.eth_address)
    except Exception:
        data["edu_balance"] = 0
    return success(data)


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """退出登录"""
    session.pop("user", None)
    return success(None, "已退出登录")
