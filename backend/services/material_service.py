"""
material_service.py — 资料业务服务

资料全生命周期的编排中心，是上传/下载/验证的唯一入口。
审查修正：下载主流程从 token_service 迁入此处。

下载流程固定顺序（不可打乱）：
  1. 查询资料 → 2. 校验未删除 → 3. 权限判断（课程/策略）
  → 4. 余额判断 → 5. 链下文件 SHA-256 预校验
  → 6. 通证支付 → 7. 返回文件流 → 8. 记录下载日志

职责边界：
  - material_service: 资料生命周期编排
  - token_service:    纯通证操作（余额/奖励/扣罚/交易历史）
  - chain_service:    纯链交互
"""

import json
import os
import threading
import time
import uuid
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Optional

from config import config
from course_catalog import COURSE_CATALOG, course_display
from fingerprint.verifier import compute_fingerprint, verify_file_integrity, check_similarity
from fingerprint.extractor import extract_text
from services.chain_service import chain_service, MaterialData

def _get_course_display(course_code: str) -> str:
    """返回课程的完整显示名，如 'CS201 数据结构'"""
    return course_display(course_code)


def _match_course_filter(material_course: str, filter_value: str) -> bool:
    """模糊匹配课程筛选：支持代码 'CS201'、名称 '数据结构'、或混合 'CS201 数据结构'"""
    if not filter_value:
        return True
    fv = filter_value.strip().lower()
    course_lower = material_course.lower()
    name_lower = COURSE_CATALOG.get(material_course, "").lower()
    return (fv in course_lower or fv in name_lower or
            fv in f"{course_lower} {name_lower}")


def _match_search(material_name: str, material_course: str, search_term: str) -> bool:
    """模糊搜索：匹配资料名称、课程代码、课程名称"""
    s = search_term.strip().lower()
    if not s:
        return True
    name_lower = material_name.lower()
    course_lower = material_course.lower()
    course_name_lower = COURSE_CATALOG.get(material_course, "").lower()
    return (s in name_lower or s in course_lower or s in course_name_lower or
            s in f"{course_lower} {course_name_lower}")


@dataclass
class UploadResult:
    """上传结果"""
    material_id: str
    name: str
    sha256_hex: str
    sim_hash: int
    text_length: int
    price: int
    upload_reward: int
    similar_materials: list[dict]
    tx_hash: str

    def to_dict(self) -> dict:
        return {
            "material_id": self.material_id,
            "name": self.name,
            "sha256_hash": self.sha256_hex,
            "sim_hash": hex(self.sim_hash),
            "text_length": self.text_length,
            "price": self.price,
            "upload_reward": self.upload_reward,
            "similar_materials": self.similar_materials,
            "tx_hash": self.tx_hash,
        }


@dataclass
class DownloadResult:
    """下载结果"""
    material_id: str
    file_path: str
    file_name: str
    price: int
    uploader: str
    downloader: str
    tx_hash: str

    def to_dict(self) -> dict:
        return {
            "material_id": self.material_id,
            "file_name": self.file_name,
            "price": self.price,
            "uploader": self.uploader,
            "downloader": self.downloader,
            "tx_hash": self.tx_hash,
        }


class MaterialService:
    """资料业务服务"""

    _metadata_lock = threading.RLock()
    _download_lock = threading.RLock()
    _metadata_fields = {
        "name",
        "course",
        "policy_type",
        "policy_value",
        "price",
    }

    # =============================================
    #  上传
    # =============================================

    @staticmethod
    def upload(
        file_path: str,
        original_name: str,
        course: str,
        uploader_address: str,
        policy_type: int = 0,
        policy_value: str = "",
        price: int = 10,
    ) -> UploadResult:
        """
        上传资料完整流程。

        流程:
          校验大小 → 存文件 → 提取文本 → SHA-256 + SimHash
          → 查重 → 上链 register → mint 奖励

        Args:
            file_path:        已保存到 uploads/ 的文件路径
            original_name:    原始文件名
            course:           所属课程
            uploader_address: 上传者以太坊地址
            policy_type:      访问策略 (0=公开, 1=同课程, 2=指定用户)
            policy_value:     策略参数
            price:            下载价格 (EDU)

        Returns:
            UploadResult

        Raises:
            ValueError: 文件重复 / 格式不支持
        """
        # --- 双层指纹计算 ---
        fp = compute_fingerprint(file_path)

        # --- SHA-256 查重（精确重复检测） ---
        existing_id = chain_service.get_material_by_hash(fp.sha256_hash)
        if existing_id:
            raise ValueError(f"文件已存在，与资料 {existing_id} 完全相同（SHA-256 匹配）")

        # --- SimHash 相似度检测 ---
        similar_hits = []
        if fp.sim_hash != 0:
            count = chain_service.get_material_count()
            if count > 0:
                existing_materials = MaterialService._get_all_materials_simhash()
                hits = check_similarity(fp.sim_hash, existing_materials)
                similar_hits = [h.to_dict() for h in hits]

        # --- 生成资料 ID ---
        material_id = f"MAT_{int(time.time())}_{uuid.uuid4().hex[:8]}"

        # --- 上链注册 ---
        receipt = chain_service.register_material(
            material_id=material_id,
            name=original_name,
            course=course,
            uploader=uploader_address,
            sha256_hash=fp.sha256_hash,
            sim_hash=fp.sim_hash,
            text_length=fp.text_length,
            policy_type=policy_type,
            policy_value=policy_value,
            price=price,
        )

        # --- 重命名文件：加上 material_id 前缀，使下载时能找到 ---
        ext = Path(file_path).suffix
        new_filename = f"{material_id}{ext}"
        new_path = os.path.join(config.UPLOAD_FOLDER, new_filename)
        os.rename(file_path, new_path)

        return UploadResult(
            material_id=material_id,
            name=original_name,
            sha256_hex=fp.sha256_hex,
            sim_hash=fp.sim_hash,
            text_length=fp.text_length,
            price=price,
            upload_reward=20,
            similar_materials=similar_hits,
            tx_hash=receipt["transactionHash"].hex(),
        )

    # =============================================
    #  下载（从 token_service 迁入）
    # =============================================

    @staticmethod
    def download(
        material_id: str,
        downloader_address: str,
        downloader_courses: list[str],
    ) -> DownloadResult:
        """
        下载资料完整流程。

        流程（固定顺序，不可打乱）:
          1. 查询资料
          2. 校验未删除
          3. 权限判断（不能下载自己的 + 课程策略）
          4. 余额判断
          5. 链下文件 SHA-256 预校验
          6. 通证支付
          7. 记录下载日志
          8. 返回文件信息

        Raises:
            ValueError: 资料不存在 / 已删除 / 无权限 / 余额不足 / 文件损坏
        """
        # --- 1. 查询资料 ---
        chain_material = chain_service.query_material(material_id)
        if chain_material is None:
            raise ValueError(f"资料不存在: {material_id}")
        material = MaterialService._apply_metadata_override(chain_material)

        # --- 2. 校验未删除 ---
        if material.deleted:
            raise ValueError(f"资料已被删除: {material_id}")

        # --- 3. 权限判断 ---
        is_self = downloader_address.lower() == material.uploader.lower()
        if not is_self:
            MaterialService._check_access_policy(
                material, downloader_address, downloader_courses
            )

        # --- 4. 余额判断（自己的资料免费下载，跳过扣费）---
        if not is_self and material.price > 0:
            balance = chain_service.get_edu_balance(downloader_address)
            if balance < material.price:
                raise ValueError(
                    f"EDU 余额不足: 需要 {material.price}，当前 {balance}"
                )

        # --- 5. 链下文件 SHA-256 预校验 ---
        file_path = MaterialService._find_material_file(material_id)
        if file_path is None:
            raise ValueError(f"服务端文件丢失: {material_id}")

        verification = verify_file_integrity(
            file_path, material.sha256_hash, material.sim_hash
        )
        if verification.is_tampered:
            raise ValueError("服务端文件完整性校验失败，文件可能已损坏")

        file_hash_bytes = bytes.fromhex(
            material.sha256_hash.replace("0x", "").ljust(64, "0")[:64]
        )
        log_price = 0 if is_self else material.price

        # --- 6-7. 支付与审计串行执行，并在审计失败时补偿退款 ---
        with MaterialService._download_lock:
            downloader_before = None
            uploader_before = None
            if not is_self and material.price > 0:
                downloader_before = chain_service.get_edu_balance(
                    downloader_address
                )
                uploader_before = chain_service.get_edu_balance(
                    material.uploader
                )
            records_before = len(
                chain_service.get_downloads_by_material(material_id)
            )

            paid = False
            if is_self or material.price == 0:
                receipt = {"transactionHash": bytes(32)}
            else:
                try:
                    if material.price == chain_material.price:
                        receipt = chain_service.download_material(
                            material_id,
                            downloader_address,
                        )
                    else:
                        # 旧合约不支持修改价格；元数据价格变化后直接执行链上转账。
                        receipt = chain_service.transfer_edu(
                            downloader_address,
                            material.uploader,
                            material.price,
                        )
                    paid = True
                except Exception:
                    downloader_after = chain_service.get_edu_balance(
                        downloader_address
                    )
                    uploader_after = chain_service.get_edu_balance(
                        material.uploader
                    )
                    paid = (
                        downloader_after == downloader_before - material.price
                        and uploader_after == uploader_before + material.price
                    )
                    if not paid:
                        raise
                    receipt = {"transactionHash": bytes(32)}

            try:
                chain_service.record_download(
                    material_id=material_id,
                    downloader=downloader_address,
                    uploader=material.uploader,
                    price=log_price,
                    file_hash=file_hash_bytes,
                )
            except Exception as log_error:
                records_after = []
                for _ in range(3):
                    try:
                        records_after = chain_service.get_downloads_by_material(
                            material_id
                        )
                        break
                    except Exception:
                        time.sleep(0.5)
                recorded = (
                    len(records_after) > records_before
                    and any(
                        record.downloader.lower() == downloader_address.lower()
                        and record.uploader.lower() == material.uploader.lower()
                        and record.price == log_price
                        and MaterialService._normalize_hash(record.file_hash)
                        == MaterialService._normalize_hash(material.sha256_hash)
                        for record in records_after[records_before:]
                    )
                )
                if not recorded:
                    if paid:
                        try:
                            chain_service.transfer_edu(
                                material.uploader,
                                downloader_address,
                                material.price,
                            )
                            downloader_refunded = chain_service.get_edu_balance(
                                downloader_address
                            )
                            uploader_refunded = chain_service.get_edu_balance(
                                material.uploader
                            )
                            if (
                                downloader_refunded != downloader_before
                                or uploader_refunded != uploader_before
                            ):
                                raise RuntimeError("退款后余额校验失败")
                        except Exception as refund_error:
                            raise RuntimeError(
                                "下载审计写入失败，且自动退款失败，请管理员核对链上交易"
                            ) from refund_error
                    raise RuntimeError(
                        "下载审计写入失败，支付已自动退回"
                    ) from log_error

        # --- 8. 返回文件信息 ---
        stored_ext = Path(file_path).suffix
        download_name = material.name
        if stored_ext and not Path(download_name).suffix:
            download_name = f"{download_name}{stored_ext}"

        return DownloadResult(
            material_id=material_id,
            file_path=file_path,
            file_name=download_name,
            price=log_price,
            uploader=material.uploader,
            downloader=downloader_address,
            tx_hash=MaterialService._transaction_hash(receipt),
        )

    # =============================================
    #  验证
    # =============================================

    @staticmethod
    def verify(file_path: str, material_id: str) -> dict:
        """
        独立验证：上传文件与链上记录比对。

        Args:
            file_path:    用户上传的待验证文件
            material_id:  要比对的资料 ID

        Returns:
            验证结果 dict（含关键词差异）
        """
        material = chain_service.query_material(material_id)
        if material is None:
            raise ValueError(f"资料不存在: {material_id}")

        # 尝试读取原始文件文本用于关键词对比
        original_text = ""
        orig_path = MaterialService._find_material_file(material_id)
        if orig_path:
            try:
                original_text = extract_text(orig_path)
            except Exception:
                pass

        result = verify_file_integrity(
            file_path, material.sha256_hash, material.sim_hash,
            original_text=original_text,
        )
        return result.to_dict()

    # =============================================
    #  查询
    # =============================================

    @staticmethod
    def get_material(material_id: str) -> Optional[dict]:
        """查询单个资料详情"""
        material = chain_service.query_material(material_id)
        if material is None:
            return None
        return MaterialService._apply_metadata_override(material).to_dict()

    @staticmethod
    def list_materials(
        course: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """
        资料列表（带筛选和分页）。

        注意：当前从链上逐条读取，数据量大时需要链下缓存优化。
        """
        if not chain_service.is_connected():
            return {
                "total": 0,
                "page": page,
                "page_size": page_size,
                "items": [],
            }

        count = chain_service.get_material_count()
        all_materials = []

        for i in range(count):
            try:
                mat_id = chain_service._registry.functions.materialIds(i).call()
                material = chain_service.query_material(mat_id)
                if material is None or material.deleted:
                    continue
                all_materials.append(
                    MaterialService._apply_metadata_override(material)
                )
            except Exception:
                continue

        # 模糊筛选（支持代码/名称/混合搜索）
        if course:
            all_materials = [m for m in all_materials if _match_course_filter(m.course, course)]
        if search:
            all_materials = [m for m in all_materials if _match_search(m.name, m.course, search)]

        # 分页
        total = len(all_materials)
        start = (page - 1) * page_size
        end = start + page_size
        page_data = all_materials[start:end]

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [m.to_dict() for m in page_data],
        }

    # =============================================
    #  删除
    # =============================================

    @staticmethod
    def soft_delete(material_id: str, caller_address: str) -> dict:
        """软删除资料"""
        receipt = chain_service.soft_delete_material(material_id, caller_address)
        return {
            "material_id": material_id,
            "deleted": True,
            "tx_hash": receipt["transactionHash"].hex(),
        }

    @classmethod
    def update_metadata(
        cls,
        material_id: str,
        *,
        name: str,
        course: str,
        policy_type: int,
        policy_value: str,
        price: int,
    ) -> dict:
        """持久化合约当前版本未覆盖的可编辑元数据。"""
        override = {
            "name": name,
            "course": course,
            "policy_type": policy_type,
            "policy_value": policy_value,
            "price": price,
        }
        with cls._metadata_lock:
            materials = cls._read_metadata_overrides()
            materials[material_id] = override
            cls._write_metadata_overrides(materials)
        return override

    @staticmethod
    def replace_material_file(material_id: str, temp_path: str) -> str:
        """在链上指纹更新成功后原子替换资料文件。"""
        old_path = MaterialService._find_material_file(material_id)
        suffix = Path(temp_path).suffix
        target_path = os.path.join(
            config.UPLOAD_FOLDER,
            f"{material_id}{suffix}",
        )
        os.replace(temp_path, target_path)
        if old_path and os.path.abspath(old_path) != os.path.abspath(target_path):
            os.remove(old_path)
        return target_path

    # =============================================
    #  内部方法
    # =============================================

    @classmethod
    def _read_metadata_overrides(cls) -> dict[str, dict]:
        path = Path(config.MATERIAL_METADATA_FILE)
        if not path.exists():
            return {}
        with path.open(encoding="utf-8") as file:
            data = json.load(file)
        return data.get("materials", {})

    @classmethod
    def _write_metadata_overrides(cls, materials: dict[str, dict]) -> None:
        path = Path(config.MATERIAL_METADATA_FILE)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(f"{path.suffix}.tmp")
        temporary.write_text(
            json.dumps(
                {"materials": materials},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, path)

    @classmethod
    def _apply_metadata_override(cls, material: MaterialData) -> MaterialData:
        material_id = getattr(material, "id", "")
        if not material_id:
            return material
        with cls._metadata_lock:
            override = cls._read_metadata_overrides().get(material_id, {})
        values = {
            key: value
            for key, value in override.items()
            if key in cls._metadata_fields
        }
        return replace(material, **values) if values else material

    @staticmethod
    def _transaction_hash(receipt: dict) -> str:
        tx_hash = receipt.get("transactionHash", "")
        if hasattr(tx_hash, "hex"):
            return tx_hash.hex()
        return str(tx_hash)

    @staticmethod
    def _normalize_hash(value: str) -> str:
        return str(value).lower().removeprefix("0x")

    @staticmethod
    def _check_access_policy(
        material: MaterialData,
        downloader_address: str,
        downloader_courses: list[str],
    ) -> None:
        """
        检查访问策略。

        policy_type:
          0 = 公开，任何人可下载
          1 = 同课程，下载者必须选修了该课程
          2 = 指定用户（暂不实现，预留）
        """
        if material.policy_type == 0:
            return  # 公开
        elif material.policy_type == 1:
            if material.course not in downloader_courses:
                raise ValueError(
                    f"权限不足: 该资料仅限选修 {material.course} 的学生下载"
                )
        elif material.policy_type == 2:
            allowed = _parse_whitelist(material.policy_value)
            if downloader_address.lower() not in allowed:
                raise ValueError("权限不足: 该资料仅限指定用户下载")

    @staticmethod
    def _find_material_file(material_id: str) -> Optional[str]:
        """
        在 uploads/ 目录查找资料文件。

        文件命名约定: {material_id}_{original_name}
        或: {timestamp}_{original_name}（旧格式，通过元数据映射）
        """
        uploads_dir = config.UPLOAD_FOLDER
        if not os.path.exists(uploads_dir):
            return None

        for filename in os.listdir(uploads_dir):
            if filename.startswith(material_id):
                return os.path.join(uploads_dir, filename)

        return None

    @staticmethod
    def _get_all_materials_simhash() -> list[dict]:
        """获取所有资料的 ID、名称和 SimHash（供查重用）"""
        count = chain_service.get_material_count()
        result = []
        for i in range(count):
            try:
                mat_id = chain_service._registry.functions.materialIds(i).call()
                material = chain_service.query_material(mat_id)
                if material and not material.deleted and material.sim_hash != 0:
                    result.append({
                        "id": material.id,
                        "name": material.name,
                        "sim_hash": material.sim_hash,
                    })
            except Exception:
                continue
        return result


def _parse_whitelist(policy_value: str) -> set[str]:
    """解析白名单地址列表（逗号或换行分隔，统一转小写）"""
    if not policy_value.strip():
        return set()
    addrs = []
    for part in policy_value.replace("\n", ",").split(","):
        addr = part.strip()
        if addr:
            addrs.append(addr.lower())
    return set(addrs)


# 全局单例
material_service = MaterialService()
