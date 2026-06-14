"""Shared course catalog for backend validation and display."""

COURSE_CATALOG = {
    "BC401": "区块链技术及应用",
    "CS201": "数据结构",
    "CS301": "操作系统",
    "CS302": "计算机网络",
    "DB201": "数据库原理",
    "AI301": "人工智能导论",
}


def course_display(course_code: str) -> str:
    name = COURSE_CATALOG.get(course_code, "")
    return f"{course_code} {name}" if name else course_code
