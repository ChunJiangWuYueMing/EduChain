"""
routes/audit.py — 审计路由（第7步实现）

GET /api/audit/downloads/<material_id>  — 资料下载记录
GET /api/audit/user/<address>           — 用户下载记录
GET /api/audit/my-downloads             — 我的下载记录
GET /api/audit/my-uploads               — 我的上传资料
GET /api/audit/all                      — 全局下载记录（管理员）
"""

from flask import Blueprint, request, g

from services.chain_service import chain_service
from services.material_service import material_service
from utils.response import success, bad_request, server_error
from utils.auth import login_required, admin_required

audit_bp = Blueprint("audit", __name__)


@audit_bp.route("/downloads/<material_id>", methods=["GET"])
@login_required
def downloads_by_material(material_id: str):
    """按资料 ID 查询下载记录"""
    try:
        records = chain_service.get_downloads_by_material(material_id)
        return success([r.to_dict() for r in records])
    except Exception as e:
        return server_error(str(e))


@audit_bp.route("/user/<address>", methods=["GET"])
@login_required
def downloads_by_user(address: str):
    """按用户地址查询下载记录"""
    try:
        records = chain_service.get_downloads_by_user(address)
        return success([r.to_dict() for r in records])
    except Exception as e:
        return server_error(str(e))


@audit_bp.route("/my-downloads", methods=["GET"])
@login_required
def my_downloads():
    """当前用户的下载记录"""
    try:
        records = chain_service.get_downloads_by_user(g.user["eth_address"])
        return success([r.to_dict() for r in records])
    except Exception as e:
        return server_error(str(e))


@audit_bp.route("/my-uploads", methods=["GET"])
@login_required
def my_uploads():
    """
    当前用户上传的资料列表（复用 material_service，按 uploader 过滤）

    Query Params:
        page      — 页码，从 1 开始（默认 1）
        page_size — 每页条数（默认 20）
    """
    try:
        page = request.args.get("page", 1, type=int)
        page_size = request.args.get("page_size", 20, type=int)

        result = material_service.list_materials(page=1, page_size=9999)
        my_addr = g.user["eth_address"].lower()
        my_items = [
            m for m in result["items"]
            if m["uploader"].lower() == my_addr
        ]

        total = len(my_items)
        start = (page - 1) * page_size
        end = start + page_size

        return success({
            "items": my_items[start:end],
            "page": page,
            "page_size": page_size,
            "total": total,
        })
    except Exception as e:
        return server_error(str(e))


@audit_bp.route("/all", methods=["GET"])
@admin_required
def all_downloads():
    """
    全局下载记录（仅管理员）

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

        total = chain_service.get_download_count()
        all_records = []
        for i in range(total):
            try:
                raw = chain_service._download_log.functions.allRecords(i).call()
                all_records.append(chain_service._parse_download_record(raw).to_dict())
            except Exception:
                continue

        start = (page - 1) * page_size
        end = start + page_size

        return success({
            "records": all_records[start:end],
            "page": page,
            "page_size": page_size,
            "total": total,
        })
    except Exception as e:
        return server_error(str(e))