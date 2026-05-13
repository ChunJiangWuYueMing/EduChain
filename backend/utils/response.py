"""
response.py — 统一 API 响应格式

所有接口必须使用 success() / error() 返回，
保证响应结构一致: {"code": int, "msg": str, "data": any}
"""

from flask import jsonify
from typing import Any, Optional


def success(data: Any = None, msg: str = "success", code: int = 200):
    """
    成功响应

    Args:
        data: 返回数据
        msg:  提示信息
        code: HTTP 状态码
    """
    return jsonify({"code": code, "msg": msg, "data": data}), code


def error(code: int, msg: str, data: Any = None):
    """
    错误响应

    Args:
        code: HTTP 状态码 (400/401/403/404/500...)
        msg:  错误描述
        data: 附加信息（可选）
    """
    return jsonify({"code": code, "msg": msg, "data": data}), code


def bad_request(msg: str = "请求参数错误", data: Any = None):
    return error(400, msg, data)


def unauthorized(msg: str = "未登录"):
    return error(401, msg)


def forbidden(msg: str = "无权限"):
    return error(403, msg)


def not_found(msg: str = "资源不存在"):
    return error(404, msg)


def server_error(msg: str = "服务器内部错误", data: Any = None):
    return error(500, msg, data)
