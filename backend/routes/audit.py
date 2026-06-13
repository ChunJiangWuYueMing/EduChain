"""
audit.py — 审计路由

端点:
  GET /api/audit/downloads/material/<id>
  GET /api/audit/downloads/user/<address>
  GET /api/audit/downloads/count
  GET /api/audit/materials/user/<address>
  GET /api/audit/updates/material/<id>
  GET /api/audit/deletions/material/<id>
  GET /api/audit/full/<id>
"""

from flask import Blueprint

from services.chain_service import chain_service
from services.material_service import material_service
from utils.response import success

audit_bp = Blueprint("audit", __name__)


@audit_bp.route("/downloads/material/<material_id>", methods=["GET"])
def downloads_by_material(material_id):
    """按资料 ID 查询下载记录"""
    records = chain_service.get_downloads_by_material(material_id)
    return success({
        "material_id": material_id,
        "records": [r.to_dict() for r in records],
        "count": len(records),
    })


@audit_bp.route("/downloads/user/<address>", methods=["GET"])
def downloads_by_user(address):
    """按用户地址查询下载记录"""
    records = chain_service.get_downloads_by_user(address)
    return success({
        "downloader": address,
        "records": [r.to_dict() for r in records],
        "count": len(records),
    })


@audit_bp.route("/downloads/count", methods=["GET"])
def download_count():
    """总下载记录数"""
    count = chain_service.get_download_count()
    return success({"download_count": count})


@audit_bp.route("/materials/user/<address>", methods=["GET"])
def materials_by_user(address):
    """查询某用户上传的所有资料（从资料列表中过滤）"""
    all_materials = material_service.list_materials(page_size=10000)
    user_materials = [
        m for m in all_materials["items"]
        if m["uploader"].lower() == address.lower()
    ]
    return success({
        "uploader": address,
        "materials": user_materials,
        "count": len(user_materials),
    })


@audit_bp.route("/updates/material/<material_id>", methods=["GET"])
def updates_by_material(material_id):
    """查询资料的修改记录（链上 MaterialUpdated 事件）"""
    records = chain_service.get_updates_by_material(material_id)
    return success({
        "material_id": material_id,
        "records": [r.to_dict() for r in records],
        "count": len(records),
    })


@audit_bp.route("/deletions/material/<material_id>", methods=["GET"])
def deletions_by_material(material_id):
    """查询资料的删除记录（链上 MaterialDeleted 事件）"""
    records = chain_service.get_deletions_by_material(material_id)
    return success({
        "material_id": material_id,
        "records": [r.to_dict() for r in records],
        "count": len(records),
    })


@audit_bp.route("/full/<material_id>", methods=["GET"])
def full_audit(material_id):
    """完整审计信息（资料详情 + 下载 + 修改 + 删除）"""
    data = chain_service.get_full_audit(material_id)
    return success(data)
