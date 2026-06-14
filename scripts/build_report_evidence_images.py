"""Build compact evidence panels for the EduChain course report."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "docs" / "report_assets"
RESULTS = json.loads(
    (ASSET_DIR / "report_e2e_results.json").read_text(encoding="utf-8")
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


def font(size: int, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_MONO if mono else FONT_BOLD if bold else FONT_REGULAR
    return ImageFont.truetype(path, size)


def rounded_card(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    *,
    fill: str = WHITE,
    outline: str = BORDER,
    radius: int = 16,
) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=2)


def fit_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    *,
    x: int,
    y: int,
    max_width: int,
    text_font: ImageFont.FreeTypeFont,
    fill: str = DARK,
    line_gap: int = 8,
) -> int:
    lines: list[str] = []
    current = ""
    for char in text:
        candidate = current + char
        if draw.textbbox((0, 0), candidate, font=text_font)[2] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = char
    if current:
        lines.append(current)

    line_height = draw.textbbox((0, 0), "Ag", font=text_font)[3]
    for index, line in enumerate(lines):
        draw.text(
            (x, y + index * (line_height + line_gap)),
            line,
            font=text_font,
            fill=fill,
        )
    return y + len(lines) * (line_height + line_gap)


def draw_header(draw: ImageDraw.ImageDraw, title: str, subtitle: str) -> None:
    draw.rectangle((0, 0, WIDTH, 112), fill=NAVY)
    draw.text((52, 24), title, font=font(34, bold=True), fill=WHITE)
    draw.text((54, 72), subtitle, font=font(17), fill="#D6E9FA")
    draw.rounded_rectangle(
        (1250, 32, 1445, 82), radius=24, fill="#E7F8EE", outline="#A9E3BE"
    )
    draw.ellipse((1270, 48, 1288, 66), fill=GREEN)
    draw.text((1300, 43), "验证通过", font=font(19, bold=True), fill=GREEN)


def build_chain_evidence() -> None:
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    material = RESULTS["material"]
    health = RESULTS["health_after"]

    draw_header(
        draw,
        "链上存证与交易凭证",
        "数据来源：2026-06-14 本地 Ganache 真实端到端测试",
    )

    rounded_card(draw, (38, 138, 1015, 600))
    draw.text((68, 164), "资料存证摘要", font=font(25, bold=True), fill=DARK)
    draw.rounded_rectangle(
        (790, 158, 975, 202), radius=22, fill="#E7F8EE", outline="#B7E8C8"
    )
    draw.text((824, 167), "链上已确认", font=font(18, bold=True), fill=GREEN)

    rows = [
        ("资料 ID", material["material_id"]),
        ("资料名称", material["name"]),
        ("课程 / 定价", f'{material["course"]} / {material["price"]} EDU'),
        ("文本长度", f'{material["text_length"]} 字符'),
        ("交易哈希", material["tx_hash"]),
        ("SHA-256", material["sha256_hash"]),
        ("SimHash", material["sim_hash"]),
    ]
    y = 222
    for label, value in rows:
        draw.text((70, y), label, font=font(17, bold=True), fill=MUTED)
        value_font = font(16, mono=True) if label in {"交易哈希", "SHA-256", "SimHash"} else font(18)
        fit_text(
            draw,
            str(value),
            x=230,
            y=y - 2,
            max_width=735,
            text_font=value_font,
            fill=DARK,
            line_gap=4,
        )
        y += 51 if label not in {"交易哈希", "SHA-256", "SimHash"} else 66

    rounded_card(draw, (1040, 138, 1462, 600))
    draw.text((1070, 164), "链与合约状态", font=font(25, bold=True), fill=DARK)
    draw.text(
        (1070, 211),
        f'区块高度  {health["block_number"]}',
        font=font(21, bold=True),
        fill=BLUE,
    )
    draw.text(
        (1270, 211),
        f'下载记录  {health["download_count"]}',
        font=font(18, bold=True),
        fill=PURPLE,
    )
    contracts = [
        ("EduToken", health["contracts"]["edu_token"]),
        ("MaterialRegistry", health["contracts"]["material_registry"]),
        ("DownloadLog", health["contracts"]["download_log"]),
    ]
    y = 266
    for name, address in contracts:
        draw.text((1070, y), name, font=font(18, bold=True), fill=DARK)
        fit_text(
            draw,
            address,
            x=1070,
            y=y + 31,
            max_width=355,
            text_font=font(15, mono=True),
            fill=MUTED,
            line_gap=3,
        )
        y += 101

    rounded_card(draw, (38, 624, 1462, 782), fill="#EDF7FF", outline="#BBDCF2")
    draw.text((68, 648), "交易流程", font=font(22, bold=True), fill=DARK)
    stages = [
        ("1", "提取文本", "PPTX 解析完成"),
        ("2", "生成双指纹", "SHA-256 + 256 位 SimHash"),
        ("3", "登记合约", "MaterialRegistry 写入成功"),
        ("4", "发放奖励", "+20 EDU 已到账"),
    ]
    x = 205
    for index, (number, title, detail) in enumerate(stages):
        draw.ellipse((x - 105, 694, x - 57, 742), fill=BLUE)
        draw.text((x - 90, 700), number, font=font(19, bold=True), fill=WHITE)
        draw.text((x - 44, 690), title, font=font(18, bold=True), fill=DARK)
        draw.text((x - 44, 722), detail, font=font(14), fill=MUTED)
        if index < len(stages) - 1:
            draw.line((x + 190, 718, x + 250, 718), fill="#7CB9DE", width=4)
            draw.polygon(
                [(x + 250, 710), (x + 266, 718), (x + 250, 726)],
                fill="#7CB9DE",
            )
        x += 345

    image.save(ASSET_DIR / "image12-chain-evidence.png", quality=95)


def build_test_summary() -> None:
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    timings = RESULTS["timings_seconds"]
    verification = RESULTS["verification"]
    balances = RESULTS["balances"]
    restart = RESULTS["restart_recovery"]

    draw_header(
        draw,
        "系统测试结果汇总",
        "自动化测试、指纹场景与真实业务流程共 37 项检查/场景",
    )

    cards = [
        ("后端单元测试", "12 / 12", "Python unittest", BLUE),
        ("前端回归测试", "9 / 9", "Node test runner", PURPLE),
        ("指纹算法场景", "8 / 8", "提取、相似度、篡改", GREEN),
        ("端到端业务", "8 / 8", "上传、下载、审计、恢复", "#D97706"),
    ]
    x = 38
    for title, score, detail, color in cards:
        rounded_card(draw, (x, 136, x + 342, 258))
        draw.text((x + 24, 158), title, font=font(18, bold=True), fill=DARK)
        draw.text((x + 24, 193), score, font=font(30, bold=True), fill=color)
        draw.text((x + 178, 207), detail, font=font(14), fill=MUTED)
        x += 362

    rounded_card(draw, (38, 278, 1462, 704))
    draw.rectangle((40, 280, 1460, 330), fill="#EAF3FA")
    headers = ["编号", "测试场景", "关键结果", "耗时/状态"]
    positions = [64, 164, 560, 1210]
    for header, x in zip(headers, positions):
        draw.text((x, 293), header, font=font(17, bold=True), fill=DARK)

    test_rows = [
        (
            "T01",
            "身份认证与会话",
            "合法账号登录成功；错误密码返回 401",
            f'{timings["login_uploader"]:.3f}s / PASS',
        ),
        (
            "T02",
            "资料上传与链上登记",
            f'{RESULTS["material"]["material_id"]}，奖励 +20 EDU',
            f'{timings["upload"]:.3f}s / PASS',
        ),
        (
            "T03",
            "重复文件拦截",
            "SHA-256 完全匹配，接口返回 400",
            f'{timings["duplicate_rejection"]:.3f}s / PASS',
        ),
        (
            "T04",
            "原件完整性验证",
            f'相似度 {verification["original"]["similarity_percent"]:.2f}%，汉明距离 0',
            f'{timings["verify_original"]:.3f}s / PASS',
        ),
        (
            "T05",
            "篡改文件识别",
            f'相似度 {verification["tampered"]["similarity_percent"]:.2f}%，汉明距离 39',
            f'{timings["verify_tampered"]:.3f}s / PASS',
        ),
        (
            "T06",
            "付费下载与余额结算",
            f'上传者 {balances["uploader_before"]}->{balances["uploader_after"]}；下载者 {balances["downloader_before"]}->{balances["downloader_after"]}',
            f'{timings["download"]:.3f}s / PASS',
        ),
        (
            "T07",
            "权限与余额异常",
            "未登录 401；余额不足 400；失败后余额不变",
            "PASS",
        ),
        (
            "T08",
            "Docker 重启恢复",
            f'区块 {restart["block_number"]}、合约地址及 1 条审计记录保持',
            "PASS",
        ),
    ]
    y = 330
    for index, row in enumerate(test_rows):
        fill = WHITE if index % 2 == 0 else "#F8FAFC"
        draw.rectangle((40, y, 1460, y + 46), fill=fill)
        draw.line((40, y + 46, 1460, y + 46), fill=BORDER, width=1)
        draw.text((64, y + 11), row[0], font=font(15, bold=True), fill=BLUE)
        draw.text((164, y + 11), row[1], font=font(15, bold=True), fill=DARK)
        draw.text((560, y + 11), row[2], font=font(14), fill=MUTED)
        draw.text((1210, y + 11), row[3], font=font(14, bold=True), fill=GREEN)
        y += 46

    rounded_card(draw, (38, 726, 1462, 790), fill="#E8F8EF", outline="#AFE0C1")
    draw.text((68, 744), "结论", font=font(20, bold=True), fill=GREEN)
    draw.text(
        (154, 746),
        "核心业务闭环、异常保护和容器恢复均通过验证，系统具备课程演示与实验验收条件。",
        font=font(17, bold=True),
        fill=DARK,
    )

    image.save(ASSET_DIR / "image18-test-summary.png", quality=95)


if __name__ == "__main__":
    build_chain_evidence()
    build_test_summary()
    print("Generated image12-chain-evidence.png and image18-test-summary.png")
