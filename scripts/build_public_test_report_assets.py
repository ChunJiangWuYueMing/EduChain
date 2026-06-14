"""Build report-ready images from the final public joint-test evidence."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
RESULT_DIR = (
    ROOT
    / "docs"
    / "test_results"
    / "public_joint_test_final_20260615_012041"
)
SCREENSHOT_DIR = RESULT_DIR / "screenshots"
ASSET_DIR = ROOT / "docs" / "report_assets_public_test"
RESULTS = json.loads(
    (RESULT_DIR / "joint_test_results.json").read_text(encoding="utf-8")
)

WIDTH = 1500
HEIGHT = 820
NAVY = "#063B6D"
BLUE = "#087AB8"
DARK = "#10233F"
MUTED = "#607086"
GREEN = "#159447"
RED = "#D73B3E"
PURPLE = "#6D4CC3"
BG = "#F3F7FB"
BORDER = "#D9E3EE"
WHITE = "#FFFFFF"
FONT_REGULAR = "C:/Windows/Fonts/msyh.ttc"
FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttc"
FONT_MONO = "C:/Windows/Fonts/consola.ttf"


def font(size: int, *, bold: bool = False, mono: bool = False):
    path = FONT_MONO if mono else FONT_BOLD if bold else FONT_REGULAR
    return ImageFont.truetype(path, size)


def fit_screenshot(source: Path, target: Path, size: tuple[int, int]) -> None:
    image = Image.open(source).convert("RGB")
    image.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, WHITE)
    canvas.paste(
        image,
        ((size[0] - image.width) // 2, (size[1] - image.height) // 2),
    )
    canvas.save(target, optimize=True)


def rounded_card(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    *,
    fill: str = WHITE,
    outline: str = BORDER,
) -> None:
    draw.rounded_rectangle(box, radius=16, fill=fill, outline=outline, width=2)


def draw_header(draw: ImageDraw.ImageDraw, title: str, subtitle: str) -> None:
    draw.rectangle((0, 0, WIDTH, 110), fill=NAVY)
    draw.text((48, 22), title, font=font(34, bold=True), fill=WHITE)
    draw.text((50, 70), subtitle, font=font(17), fill="#D6E9FA")
    draw.rounded_rectangle(
        (1260, 30, 1450, 80),
        radius=24,
        fill="#E7F8EE",
        outline="#A9E3BE",
    )
    draw.ellipse((1280, 47, 1298, 65), fill=GREEN)
    draw.text((1310, 41), "公网实测", font=font(19, bold=True), fill=GREEN)


def short(value: str, left: int = 18, right: int = 12) -> str:
    if len(value) <= left + right + 3:
        return value
    return f"{value[:left]}...{value[-right:]}"


def build_upload_panel() -> None:
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    material_a = RESULTS["materials"]["A"]
    duplicate = RESULTS["materials"]["B"]
    material_c = RESULTS["materials"]["C"]
    similar = material_c["similar_materials"][0]

    draw_header(
        draw,
        "资料上传、奖励与重复检测",
        "数据来源：2026-06-15 公网九账号联动测试",
    )

    cards = [
        ("成功登记", "7 份", "链上资料总数", BLUE),
        ("上传奖励", "+20 EDU", "每份成功资料", GREEN),
        ("重复拦截", "HTTP 400", "SHA-256 完全相同", RED),
        ("相似资料", "90.23%", "C 与 A 为衍生版本", PURPLE),
    ]
    x = 38
    for title, score, detail, color in cards:
        rounded_card(draw, (x, 136, x + 342, 266))
        draw.text((x + 24, 158), title, font=font(18, bold=True), fill=DARK)
        draw.text((x + 24, 195), score, font=font(29, bold=True), fill=color)
        draw.text((x + 168, 210), detail, font=font(14), fill=MUTED)
        x += 362

    rounded_card(draw, (38, 290, 942, 705))
    draw.text((68, 318), "资料 A 上传结果", font=font(24, bold=True), fill=DARK)
    upload_rows = [
        ("资料 ID", material_a["material_id"]),
        ("资料名称", material_a["name"]),
        ("SHA-256", short(material_a["sha256_hash"], 25, 20)),
        ("SimHash", short(material_a["sim_hash"], 25, 20)),
        ("交易哈希", short(material_a["tx_hash"], 25, 20)),
        ("上传者余额", "100 -> 120 EDU"),
    ]
    y = 370
    for label, value in upload_rows:
        draw.text((70, y), label, font=font(17, bold=True), fill=MUTED)
        draw.text(
            (235, y - 2),
            value,
            font=font(17, mono=label in {"SHA-256", "SimHash", "交易哈希"}),
            fill=DARK,
        )
        y += 52

    rounded_card(draw, (970, 290, 1462, 500), fill="#FFF5F5", outline="#F3B7B7")
    draw.text((1000, 318), "完全重复文件 B", font=font(23, bold=True), fill=RED)
    draw.text((1000, 365), "系统拒绝重复登记", font=font(19, bold=True), fill=DARK)
    duplicate_message = duplicate["message"]
    lines = [
        duplicate_message[:28],
        duplicate_message[28:56],
        duplicate_message[56:],
    ]
    for index, line in enumerate(filter(None, lines)):
        draw.text((1000, 410 + index * 30), line, font=font(15), fill=MUTED)

    rounded_card(draw, (970, 520, 1462, 705), fill="#F6F3FF", outline="#CFC2F5")
    draw.text((1000, 548), "内容相似文件 C", font=font(23, bold=True), fill=PURPLE)
    draw.text(
        (1000, 594),
        f"汉明距离 {similar['hamming_distance']}，相似度 {similar['similarity_percent']}%",
        font=font(17, bold=True),
        fill=DARK,
    )
    draw.text(
        (1000, 632),
        "分类：derived（衍生版本）",
        font=font(17),
        fill=MUTED,
    )
    draw.text(
        (1000, 668),
        "保留上传但返回相似性提示",
        font=font(16),
        fill=MUTED,
    )

    rounded_card(draw, (38, 730, 1462, 790), fill="#E8F8EF", outline="#AFE0C1")
    draw.text((68, 747), "结论", font=font(20, bold=True), fill=GREEN)
    draw.text(
        (150, 749),
        "完全重复文件被阻断，内容相近但不完全相同的资料保留并给出可解释提示。",
        font=font(17, bold=True),
        fill=DARK,
    )
    image.save(ASSET_DIR / "image11-upload-result.png", optimize=True)


def build_chain_panel() -> None:
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    material = RESULTS["materials"]["A"]
    health = RESULTS["health_after"]

    draw_header(
        draw,
        "链上存证与服务状态",
        "主测试结束时区块高度 41，资料 7 份，下载审计 6 条",
    )

    rounded_card(draw, (38, 138, 1018, 650))
    draw.text((68, 166), "资料 A 链上凭证", font=font(25, bold=True), fill=DARK)
    rows = [
        ("资料 ID", material["material_id"]),
        ("资料名称", material["name"]),
        ("定价", f"{material['price']} EDU"),
        ("SHA-256", short(material["sha256_hash"], 28, 22)),
        ("SimHash", short(material["sim_hash"], 28, 22)),
        ("注册交易", short(material["tx_hash"], 28, 22)),
    ]
    y = 224
    for label, value in rows:
        draw.text((70, y), label, font=font(17, bold=True), fill=MUTED)
        draw.text(
            (235, y - 2),
            value,
            font=font(17, mono=label in {"SHA-256", "SimHash", "注册交易"}),
            fill=DARK,
        )
        y += 65

    rounded_card(draw, (1045, 138, 1462, 650))
    draw.text((1075, 166), "运行状态", font=font(25, bold=True), fill=DARK)
    status_rows = [
        ("Chain ID", str(health["chain_id"])),
        ("区块高度", str(health["block_number"])),
        ("链上资料", str(health["material_count"])),
        ("下载审计", str(health["download_count"])),
        ("测试账号", "9"),
        ("钱包就绪", "9"),
    ]
    y = 224
    for label, value in status_rows:
        draw.text((1075, y), label, font=font(17), fill=MUTED)
        draw.text((1350, y - 5), value, font=font(25, bold=True), fill=BLUE)
        y += 58

    draw.text((1075, 585), "三份合约地址保持不变", font=font(17, bold=True), fill=GREEN)
    rounded_card(draw, (38, 678, 1462, 790), fill="#EDF7FF", outline="#BBDCF2")
    draw.text((68, 700), "合约地址", font=font(20, bold=True), fill=DARK)
    contracts = health["contracts"]
    contract_text = (
        f"EduToken {short(contracts['edu_token'])}    "
        f"MaterialRegistry {short(contracts['material_registry'])}    "
        f"DownloadLog {short(contracts['download_log'])}"
    )
    draw.text((68, 742), contract_text, font=font(15, mono=True), fill=MUTED)
    image.save(ASSET_DIR / "image12-chain-evidence.png", optimize=True)


def main() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    fit_screenshot(
        SCREENSHOT_DIR / "01-public-login.png",
        ASSET_DIR / "image10-login.png",
        (1309, 715),
    )
    build_upload_panel()
    build_chain_panel()
    screenshot_map = {
        "03-admin-material-market.png": "image13-market.png",
        "06-fang-wallet-history.png": "image14-wallet.png",
        "11-tampered-file-detected.png": "image15-verify-tampered.png",
        "05-admin-global-audit.png": "image16-audit.png",
        "02-admin-system-status.png": "image17-status.png",
        "00-test-summary.png": "image18-test-summary.png",
    }
    for source_name, target_name in screenshot_map.items():
        fit_screenshot(
            SCREENSHOT_DIR / source_name,
            ASSET_DIR / target_name,
            (WIDTH, HEIGHT),
        )
    print(ASSET_DIR)


if __name__ == "__main__":
    main()
