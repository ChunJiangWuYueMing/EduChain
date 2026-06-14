"""
token.py — 通证路由

端点:
  GET  /api/token/balance
  GET  /api/token/allowance
  POST /api/token/transfer
  GET  /api/token/history
  POST /api/token/reward
"""

from flask import Blueprint, request, session, current_app

from config import config
from services.token_service import token_service
from services.chain_service import chain_service
from services.user_service import user_service
from utils.response import (
    success, bad_request, unauthorized, forbidden, server_error,
)

token_bp = Blueprint("token", __name__)


def _require_login():
    user = session.get("user")
    if user is None:
        return None, unauthorized("请先登录")
    return user, None


@token_bp.route("/balance", methods=["GET"])
def get_balance():
    """查询当前用户 EDU 余额"""
    user, err = _require_login()
    if err:
        return err

    address = request.args.get("address", "").strip() or user["eth_address"]
    balance = token_service.get_balance(address)
    return success({"address": address, "balance": balance})


@token_bp.route("/allowance", methods=["GET"])
def get_allowance():
    """查询授权额度"""
    user, err = _require_login()
    if err:
        return err

    spender = request.args.get("spender", config.MATERIAL_REGISTRY_ADDRESS)
    allowance = token_service.get_allowance(user["eth_address"], spender)
    return success({
        "owner": user["eth_address"],
        "spender": spender,
        "allowance": allowance,
    })


@token_bp.route("/transfer", methods=["POST"])
def transfer():
    """转账 EDU"""
    user, err = _require_login()
    if err:
        return err

    body = request.get_json(silent=True) or {}
    to_address = body.get("to_address", "").strip()
    try:
        amount = int(body.get("amount", 0))
    except (ValueError, TypeError):
        return bad_request("转账金额必须为整数")

    if not to_address:
        return bad_request("接收地址不能为空")
    if amount <= 0:
        return bad_request("转账金额必须大于 0")

    try:
        receipt = chain_service.transfer_edu(user["eth_address"], to_address, amount)
    except ValueError as e:
        return bad_request(str(e))
    except Exception as e:
        current_app.logger.error(f"转账失败: {e}")
        return server_error(f"转账失败: {e}")

    return success({
        "from": user["eth_address"],
        "to": to_address,
        "amount": amount,
        "tx_hash": receipt["transactionHash"].hex(),
    }, "转账成功")


@token_bp.route("/history", methods=["GET"])
def get_history():
    """获取交易历史"""
    user, err = _require_login()
    if err:
        return err

    address = request.args.get("address", "").strip() or user["eth_address"]
    limit = min(200, max(1, int(request.args.get("limit", 50))))

    history = token_service.get_transaction_history(address, limit=limit)
    return success({"address": address, "transactions": history, "count": len(history)})


@token_bp.route("/penalize", methods=["POST"])
def penalize():
    """管理员抄袭扣罚"""
    user, err = _require_login()
    if err:
        return err

    if not user_service.is_admin(user["student_id"]):
        return forbidden("仅管理员可操作")

    body = request.get_json(silent=True) or {}
    student_id = body.get("student_id", "").strip()
    try:
        amount = int(body.get("amount", config.PLAGIARISM_PENALTY))
    except (ValueError, TypeError):
        return bad_request("扣罚金额必须为整数")

    if not student_id:
        return bad_request("目标学号不能为空")
    if amount <= 0:
        return bad_request("扣罚金额必须大于 0")

    target = user_service.get_user(student_id)
    if not target:
        return bad_request("用户不存在")

    reason = str(body.get("reason") or "confirmed plagiarism").strip()[:64]

    try:
        result = token_service.penalize_plagiarism(
            target.eth_address,
            reason[:64],
            amount=amount,
        )
    except Exception as e:
        current_app.logger.error(f"扣罚失败: {e}")
        return server_error(f"扣罚失败: {e}")

    return success(result, "扣罚成功")


@token_bp.route("/reward", methods=["POST"])
def reward():
    """管理员发放 EDU 奖励"""
    user, err = _require_login()
    if err:
        return err

    if not user_service.is_admin(user["student_id"]):
        return forbidden("仅管理员可操作")

    body = request.get_json(silent=True) or {}
    student_id = body.get("student_id", "").strip()
    target_address = body.get("address", "").strip()
    if student_id:
        target = user_service.get_user(student_id)
        if not target:
            return bad_request("用户不存在")
        target_address = target.eth_address

    if not target_address:
        return bad_request("目标学号或地址不能为空")

    try:
        amount = int(body.get("amount", 10))
    except (ValueError, TypeError):
        return bad_request("奖励金额必须为整数")
    if amount <= 0:
        return bad_request("奖励金额必须大于 0")
    reason = str(body.get("reason") or "admin_reward").strip()[:64] or "admin_reward"

    try:
        result = token_service.reward(target_address, amount, reason)
    except Exception as e:
        current_app.logger.error(f"发放奖励失败: {e}")
        return server_error(f"发放奖励失败: {e}")

    return success(result, "奖励发放成功")
