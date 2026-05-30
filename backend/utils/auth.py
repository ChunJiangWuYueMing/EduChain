"""
auth.py — 认证装饰器

所有需要登录的接口统一走 @login_required 检查。
session 中存储的数据结构见 User.to_session()。
"""

from functools import wraps
from flask import session, g
from utils.response import unauthorized


def login_required(f):
    """
    登录态检查装饰器。

    检查 session 中是否有 student_id，有则将用户信息挂到 g.user，
    没有则返回 401。

    用法:
        @app.route("/api/xxx")
        @login_required
        def xxx():
            current_user = g.user  # {"student_id": ..., "eth_address": ..., ...}
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        user_data = session.get("user")
        if not user_data or not user_data.get("student_id"):
            return unauthorized("未登录，请先调用 /api/auth/login")
        g.user = user_data
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """
    管理员权限检查装饰器（包含登录检查）。
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        user_data = session.get("user")
        if not user_data or not user_data.get("student_id"):
            return unauthorized("未登录，请先调用 /api/auth/login")
        if user_data.get("role") != "admin":
            from utils.response import forbidden
            return forbidden("需要管理员权限")
        g.user = user_data
        return f(*args, **kwargs)
    return decorated
