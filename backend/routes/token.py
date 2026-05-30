"""
routes/token.py — 通证路由（第7步实现）

GET  /api/token/balance       — EDU 余额
GET  /api/token/transactions  — 交易历史（支持分页）
"""

from flask import Blueprint, g, request

from services.token_service import token_service
from utils.response import success, bad_request, server_error
from utils.auth import login_required

token_bp = Blueprint("token", __name__)


@token_bp.route("/balance", methods=["GET"])
@login_required
def balance():
    """查询当前用户 EDU 余额"""
    try:
        bal = token_service.get_balance(g.user["eth_address"])
        return success({"eth_address": g.user["eth_address"], "balance": bal})
    except Exception as e:
        return server_error(str(e))


@token_bp.route("/transactions", methods=["GET"])
@login_required
def transactions():
    """
    查询当前用户交易历史（支持分页）

    Query Params:
        page      — 页码，从 1 开始（默认 1）
        page_size — 每页条数（默认 20，上限 100）
    """
    try:
        page = request.args.get("page", 1, type=int)
        page_size = request.args.get("page_size", 20, type=int)

        if page < 1:
            return bad_request("page 必须 >= 1")
        if page_size < 1 or page_size > 100:
            return bad_request("page_size 必须在 1-100 之间")

        # 先拉全量（链上事件无原生分页），再应用层切片
        all_tx = token_service.get_transaction_history(
            g.user["eth_address"], limit=500
        )
        total = len(all_tx)
        start = (page - 1) * page_size
        end = start + page_size
        page_data = all_tx[start:end]

        return success({
            "transactions": page_data,
            "page": page,
            "page_size": page_size,
            "total": total,
        })
    except Exception as e:
        return server_error(str(e))