"""
Material management routes.

Endpoints:
  POST /api/material/upload
  GET  /api/material/list
  GET  /api/material/<id>
  GET  /api/material/<id>/download
  POST /api/material/verify
  POST /api/material/<id>/update
  DELETE /api/material/<id>
"""

import os
import time
import uuid

from flask import Blueprint, current_app, request, send_file, session

from config import config
from course_catalog import COURSE_CATALOG
from services.material_service import material_service
from utils.response import (
    bad_request,
    forbidden,
    not_found,
    server_error,
    success,
    unauthorized,
)

material_bp = Blueprint("material", __name__)


def _require_login():
    user = session.get("user")
    if user is None:
        return None, unauthorized("请先登录")
    return user, None


def _allowed_file(filename: str) -> bool:
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in config.ALLOWED_EXTENSIONS


def _stored_material_extension(material_id: str) -> str:
    if not os.path.exists(config.UPLOAD_FOLDER):
        return ""

    for filename in os.listdir(config.UPLOAD_FOLDER):
        if filename.startswith(material_id):
            ext = os.path.splitext(filename)[1].lower()
            if ext.lstrip(".") in config.ALLOWED_EXTENSIONS:
                return ext
    return ""


def _positive_int_arg(name: str, default: int, max_value: int | None = None) -> tuple[int | None, tuple | None]:
    raw = request.args.get(name, default)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None, bad_request(f"{name} 必须是正整数")

    value = max(1, value)
    if max_value is not None:
        value = min(max_value, value)
    return value, None


def _save_temp_file(file_storage, prefix: str, fallback_ext: str = "") -> tuple[str | None, tuple]:
    filename = file_storage.filename
    if fallback_ext and not os.path.splitext(filename)[1]:
        filename = f"{filename}{fallback_ext}"

    temp_name = f"{prefix}_{int(time.time())}_{uuid.uuid4().hex[:8]}_{filename}"
    temp_path = os.path.join(config.UPLOAD_FOLDER, temp_name)
    try:
        file_storage.save(temp_path)
    except Exception as exc:
        return None, server_error(f"文件保存失败: {exc}")

    if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return None, bad_request("上传失败：文件内容为空，请重新选择本地文件或重新导出后再试")

    return temp_path, None


@material_bp.route("/upload", methods=["POST"])
def upload():
    user, err = _require_login()
    if err:
        return err

    if "file" not in request.files:
        return bad_request("请选择要上传的文件")

    file = request.files["file"]
    if file.filename == "":
        return bad_request("文件名不能为空")

    if not _allowed_file(file.filename):
        return bad_request(
            f"不支持的文件格式，允许: {', '.join(sorted(config.ALLOWED_EXTENSIONS))}"
        )

    material_name = request.form.get("name", "").strip() or file.filename
    course = request.form.get("course", "").strip()
    if not course:
        return bad_request("所属课程不能为空")
    if course not in COURSE_CATALOG:
        return bad_request("课程编号无效")

    try:
        policy_type = int(request.form.get("policy_type", 0))
        price = int(request.form.get("price", 5))
    except (TypeError, ValueError):
        return bad_request("访问策略和价格必须是整数")

    if policy_type not in (0, 1, 2):
        return bad_request("访问策略类型无效")
    if price < 0:
        return bad_request("价格不能为负数")

    policy_value = request.form.get("policy_value", "").strip()

    temp_path, save_err = _save_temp_file(file, "upload")
    if save_err:
        return save_err

    try:
        result = material_service.upload(
            file_path=temp_path,
            original_name=material_name,
            course=course,
            uploader_address=user["eth_address"],
            policy_type=policy_type,
            policy_value=policy_value,
            price=price,
        )
    except ValueError as exc:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        return bad_request(str(exc))
    except Exception as exc:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        current_app.logger.error("上传失败: %s", exc)
        return server_error(f"上传失败: {exc}")

    return success(result.to_dict(), "上传成功")


@material_bp.route("/list", methods=["GET"])
def list_materials():
    course = request.args.get("course", "").strip() or None
    search = request.args.get("search", "").strip() or None
    page, err = _positive_int_arg("page", 1)
    if err:
        return err
    page_size, err = _positive_int_arg("page_size", 20, max_value=100)
    if err:
        return err

    result = material_service.list_materials(
        course=course, search=search, page=page, page_size=page_size
    )
    return success(result)


@material_bp.route("/<material_id>", methods=["GET"])
def get_material(material_id):
    material = material_service.get_material(material_id)
    if material is None:
        return not_found("资料不存在")
    return success(material)


@material_bp.route("/<material_id>/download", methods=["GET"])
def download_material(material_id):
    user, err = _require_login()
    if err:
        return err

    try:
        result = material_service.download(
            material_id=material_id,
            downloader_address=user["eth_address"],
            downloader_courses=user.get("courses", []),
        )
    except ValueError as exc:
        return bad_request(str(exc))
    except Exception as exc:
        current_app.logger.error("下载失败: %s", exc)
        return server_error(f"下载失败: {exc}")

    return send_file(
        result.file_path,
        as_attachment=True,
        download_name=result.file_name,
    )


@material_bp.route("/verify", methods=["POST"])
def verify():
    if "file" not in request.files:
        return bad_request("请选择要验证的文件")

    file = request.files["file"]
    material_id = request.form.get("material_id", "").strip()

    if not material_id:
        return bad_request("资料 ID 不能为空")
    if file.filename == "":
        return bad_request("文件名不能为空")

    temp_path, save_err = _save_temp_file(
        file,
        "verify",
        fallback_ext=_stored_material_extension(material_id),
    )
    if save_err:
        return save_err

    try:
        result = material_service.verify(file_path=temp_path, material_id=material_id)
    except ValueError as exc:
        return not_found(str(exc))
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

    return success(result)


@material_bp.route("/<material_id>/update", methods=["POST"])
def update_material(material_id):
    user, err = _require_login()
    if err:
        return err

    material = material_service.get_material(material_id)
    if material is None:
        return not_found("资料不存在")
    if material["uploader"].lower() != user["eth_address"].lower():
        return forbidden("只能修改自己上传的资料")

    body = (
        request.get_json(silent=True) or {}
        if request.is_json
        else request.form
    )
    name = str(body.get("name", "")).strip() or material["name"]
    course = str(body.get("course", "")).strip() or material["course"]
    if course not in COURSE_CATALOG:
        return bad_request("课程编号无效")
    try:
        policy_type = int(body.get("policy_type", material["policy_type"]))
        price = int(body.get("price", material["price"]))
    except (TypeError, ValueError):
        return bad_request("访问策略和价格必须是整数")
    policy_value = str(
        body.get("policy_value", material["policy_value"])
    ).strip()

    if policy_type not in (0, 1, 2):
        return bad_request("访问策略类型无效")
    if price < 0:
        return bad_request("价格不能为负数")

    temp_path = None
    try:
        if "file" in request.files and request.files["file"].filename:
            file = request.files["file"]
            if not _allowed_file(file.filename):
                return bad_request("不支持的文件格式")
            temp_path, save_err = _save_temp_file(file, "update")
            if save_err:
                return save_err

            from fingerprint.verifier import compute_fingerprint
            from services.chain_service import chain_service

            fp = compute_fingerprint(temp_path)
            chain_service.update_material(
                material_id, fp.sha256_hash, fp.sim_hash, fp.text_length
            )
            material_service.replace_material_file(material_id, temp_path)
            temp_path = None

        updated = material_service.update_metadata(
            material_id,
            name=name,
            course=course,
            policy_type=policy_type,
            policy_value=policy_value,
            price=price,
        )

        return success(
            {
                "material_id": material_id,
                **updated,
            },
            "更新成功",
        )
    except Exception as exc:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        current_app.logger.error("更新失败: %s", exc)
        return server_error(f"更新失败: {exc}")


@material_bp.route("/<material_id>", methods=["DELETE"])
def delete_material(material_id):
    user, err = _require_login()
    if err:
        return err

    material = material_service.get_material(material_id)
    if material is None:
        return not_found("资料不存在")

    from services.user_service import user_service

    is_admin = user_service.is_admin(user["student_id"])
    is_owner = material["uploader"].lower() == user["eth_address"].lower()
    if not is_admin and not is_owner:
        return forbidden("只能删除自己上传的资料")

    try:
        contract_caller = (
            material["uploader"] if is_admin else user["eth_address"]
        )
        result = material_service.soft_delete(material_id, contract_caller)
    except Exception as exc:
        current_app.logger.error("删除失败: %s", exc)
        return server_error(f"删除失败: {exc}")

    return success(result, "删除成功")
