"""
routes/material.py — 资料路由

POST /api/material/upload             — 上传资料（multipart/form-data）
GET  /api/material/list               — 资料列表（支持 course/search/page）
GET  /api/material/<id>               — 资料详情
POST /api/material/<id>/download      — 下载资料（通证扣费 + 文件下发）
POST /api/material/<id>/verify        — 独立验证（上传文件比对链上记录）
DELETE /api/material/<id>             — 软删除
"""

import os
import time

from flask import Blueprint, request, g, send_file

from config import config
from services.material_service import material_service
from utils.response import success, bad_request, not_found, forbidden, server_error
from utils.auth import login_required

material_bp = Blueprint("material", __name__)


def _allowed_file(filename: str) -> bool:
    """检查文件扩展名"""
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in config.ALLOWED_EXTENSIONS


# ==========================================================
#  上传
# ==========================================================

@material_bp.route("/upload", methods=["POST"])
@login_required
def upload():
    """
    上传资料

    表单字段 (multipart/form-data):
        file:         文件（必须，≤50MB，支持 pdf/docx/pptx/txt/md）
        course:       课程编号（必须）
        price:        下载价格 EDU（可选，默认 10）
        policy_type:  访问策略（可选，0=公开 1=同课程，默认 0）

    返回:
        资料 ID、SHA-256、SimHash、上传奖励、相似资料列表
    """
    # 校验文件
    if "file" not in request.files:
        return bad_request("缺少文件字段 'file'")

    file = request.files["file"]
    if file.filename == "":
        return bad_request("未选择文件")

    if not _allowed_file(file.filename):
        exts = ", ".join(config.ALLOWED_EXTENSIONS)
        return bad_request(f"不支持的文件格式，允许: {exts}")

    # 读取表单参数
    course = (request.form.get("course") or "").strip()
    if not course:
        return bad_request("课程编号 course 不能为空")

    price = request.form.get("price", "10")
    try:
        price = int(price)
    except ValueError:
        return bad_request("price 必须是整数")

    policy_type = request.form.get("policy_type", "0")
    try:
        policy_type = int(policy_type)
    except ValueError:
        return bad_request("policy_type 必须是整数")

    # 保存文件到临时路径
    original_name = file.filename
    temp_name = f"tmp_{int(time.time())}_{original_name}"
    temp_path = os.path.join(config.UPLOAD_FOLDER, temp_name)
    file.save(temp_path)

    try:
        result = material_service.upload(
            file_path=temp_path,
            original_name=original_name,
            course=course,
            uploader_address=g.user["eth_address"],
            policy_type=policy_type,
            policy_value="",
            price=price,
        )
        return success(result.to_dict(), msg="上传成功")
    except ValueError as e:
        # 清理临时文件
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        return bad_request(str(e))
    except Exception as e:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        return server_error(f"上传失败: {e}")


# ==========================================================
#  列表
# ==========================================================

@material_bp.route("/list", methods=["GET"])
def list_materials():
    """
    资料列表

    查询参数:
        course:    按课程筛选（可选）
        search:    搜索关键词（可选，匹配名称和课程）
        page:      页码（默认 1）
        page_size: 每页数量（默认 20）
    """
    course = request.args.get("course", "").strip() or None
    search = request.args.get("search", "").strip() or None
    page = request.args.get("page", "1")
    page_size = request.args.get("page_size", "20")

    try:
        page = max(1, int(page))
        page_size = max(1, min(100, int(page_size)))
    except ValueError:
        return bad_request("page 和 page_size 必须是整数")

    try:
        result = material_service.list_materials(
            course=course, search=search, page=page, page_size=page_size
        )
        return success(result)
    except Exception as e:
        return server_error(f"查询失败: {e}")


# ==========================================================
#  详情
# ==========================================================

@material_bp.route("/<material_id>", methods=["GET"])
def detail(material_id: str):
    """查询单个资料详情"""
    result = material_service.get_material(material_id)
    if result is None:
        return not_found(f"资料不存在: {material_id}")
    return success(result)


# ==========================================================
#  下载
# ==========================================================

@material_bp.route("/<material_id>/download", methods=["POST"])
@login_required
def download(material_id: str):
    """
    下载资料

    需要登录。下载者余额 >= 资料价格时自动扣费，
    扣费成功后返回文件流。
    """
    try:
        result = material_service.download(
            material_id=material_id,
            downloader_address=g.user["eth_address"],
            downloader_courses=g.user.get("courses", []),
        )
    except ValueError as e:
        return bad_request(str(e))
    except Exception as e:
        return server_error(f"下载失败: {e}")

    # 返回文件流
    return send_file(
        result.file_path,
        as_attachment=True,
        download_name=result.file_name,
    )


# ==========================================================
#  验证
# ==========================================================

@material_bp.route("/<material_id>/verify", methods=["POST"])
def verify(material_id: str):
    """
    独立验证

    表单字段 (multipart/form-data):
        file: 待验证的文件

    将上传的文件与链上记录的 SHA-256 和 SimHash 比对，
    返回完整性验证报告。
    """
    if "file" not in request.files:
        return bad_request("缺少文件字段 'file'")

    file = request.files["file"]
    if file.filename == "":
        return bad_request("未选择文件")

    # 保存到临时路径
    temp_name = f"verify_{int(time.time())}_{file.filename}"
    temp_path = os.path.join(config.UPLOAD_FOLDER, temp_name)
    file.save(temp_path)

    try:
        result = material_service.verify(temp_path, material_id)
        return success(result)
    except ValueError as e:
        return bad_request(str(e))
    except Exception as e:
        return server_error(f"验证失败: {e}")
    finally:
        # 验证完删除临时文件
        if os.path.exists(temp_path):
            os.unlink(temp_path)


# ==========================================================
#  删除
# ==========================================================

@material_bp.route("/<material_id>", methods=["DELETE"])
@login_required
def delete(material_id: str):
    """
    软删除资料

    只有上传者本人可以删除。
    """
    try:
        result = material_service.soft_delete(material_id, g.user["eth_address"])
        return success(result, msg="删除成功")
    except Exception as e:
        error_msg = str(e)
        if "only uploader" in error_msg.lower():
            return forbidden("只有上传者可以删除该资料")
        return server_error(f"删除失败: {e}")