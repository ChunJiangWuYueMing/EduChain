# EduChain 公网九账号联动测试报告

- 服务器：`http://1.95.47.47`
- 开始时间：2026-06-15T01:16:05+08:00
- 完成时间：2026-06-15T01:16:52+08:00
- 结果：40/46 通过，86.96%

## 环境基线

- 测试前区块高度：4
- 测试后区块高度：41
- 测试前资料数：0
- 测试后资料数：7
- 测试后下载记录：6

## 测试结果

| 编号 | 操作者 | 功能 | 结论 | 实际结果 | 余额变化 |
|---|---|---|---|---|---|
| FILE-01 | 测试工具 | 测试文件完整性基线 | 通过 | 文件哈希已计算 |  |
| ENV-HEALTH | 管理员 | 公网健康检查 | 通过 | {"admin_count": 1, "block_number": 4, "chain_connected": true, "chain_id": 1337, "contracts": {"download_log": "0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0", "edu_token": "0x5FbDB2315678afecb367f032d93F642f64180aa3", "material_registry": "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"}, "contracts_ready": true, "deployer": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266", "download_count": 0, "ganache_connected": true, "ganache_url": "http://ganache:8545", "material_count": 0, "network": "ganache", "status": "running", "student_count": 8, "users_count": 9, "wallets_ready": 9} |  |
| AUTH-REGISTER | 未登录用户 | 服务器关闭公开注册 | 通过 | HTTP 403: 当前为课程测试环境，账号已由管理员统一创建。 |  |
| AUTH-BAD-PASSWORD | 唐昊 | 错误密码登录 | 通过 | HTTP 401: 学号或密码错误 |  |
| LOGIN-2023112379 | 唐昊 | 并发登录及首次奖励 | 通过 | HTTP 200，奖励 100 EDU，余额 100 | +100 EDU |
| LOGIN-2023112385 | 薛雨凇 | 并发登录及首次奖励 | 通过 | HTTP 200，奖励 100 EDU，余额 100 | +100 EDU |
| LOGIN-admin_2023112379 | 唐昊（管理员） | 并发登录及首次奖励 | 通过 | HTTP 200，奖励 0 EDU，余额 0 | +0 EDU |
| LOGIN-2023112380 | 于骐畅 | 并发登录及首次奖励 | 通过 | HTTP 200，奖励 100 EDU，余额 100 | +100 EDU |
| LOGIN-2023112318 | 周子皓 | 并发登录及首次奖励 | 通过 | HTTP 200，奖励 100 EDU，余额 100 | +100 EDU |
| LOGIN-2023112330 | 王东涵 | 并发登录及首次奖励 | 通过 | HTTP 200，奖励 100 EDU，余额 100 | +100 EDU |
| LOGIN-2023112392 | 李子彤 | 并发登录及首次奖励 | 通过 | HTTP 200，奖励 100 EDU，余额 100 | +100 EDU |
| LOGIN-2023112317 | 方天宇 | 并发登录及首次奖励 | 通过 | HTTP 200，奖励 100 EDU，余额 100 | +100 EDU |
| LOGIN-2023116100 | 谢傲宇 | 并发登录及首次奖励 | 通过 | HTTP 200，奖励 100 EDU，余额 100 | +100 EDU |
| LOGIN-UNIQUE | 管理员 | 九账号钱包唯一性 | 通过 | 读取 9 个钱包，唯一值 9 |  |
| LOGIN-IDEMPOTENT | 全部账号 | 并发重复登录奖励幂等 | 通过 | {"2023112379": 0, "admin_2023112379": 0, "2023112385": 0, "2023112380": 0, "2023112318": 0, "2023112330": 0, "2023116100": 0, "2023112392": 0, "2023112317": 0} |  |
| UPLOAD-A | 唐昊 | 上传公开资料 A | 通过 | HTTP 200，资料 MAT_1781457372_9c3fc361，余额 100->120 | 100->120 |
| UPLOAD-B | 薛雨凇 | 完全重复文件拦截 | 通过 | HTTP 400: 文件已存在，与资料 MAT_1781457372_9c3fc361 完全相同（SHA-256 匹配） | 100->100 |
| UPLOAD-D | 薛雨凇 | 并发上传资料 D | 通过 | HTTP 200，资料 MAT_1781457380_077a0491，余额 +20 | 100->120 |
| UPLOAD-H | 李子彤 | 并发上传资料 H | 通过 | HTTP 200，资料 MAT_1781457380_e9e778f9，余额 +20 | 100->120 |
| UPLOAD-E | 周子皓 | 并发上传资料 E | 通过 | HTTP 200，资料 MAT_1781457381_e6727a29，余额 +20 | 100->120 |
| UPLOAD-F | 王东涵 | 并发上传资料 F | 通过 | HTTP 200，资料 MAT_1781457381_ddd577b1，余额 +20 | 100->120 |
| UPLOAD-G | 谢傲宇 | 并发上传资料 G | 通过 | HTTP 200，资料 MAT_1781457381_09c7867b，余额 +20 | 100->120 |
| UPLOAD-C | 于骐畅 | 并发上传资料 C | 通过 | HTTP 200，资料 MAT_1781457381_8f7a8549，余额 +20 | 100->120 |
| VERIFY-A | 李子彤 | 资料 A 原文件完整性验证 | 通过 | {"added_keywords": [], "classification": "identical", "common_keywords": ["256", "EduChain", "SHA", "SimHash", "上传", "下载", "交易", "区块", "合约", "哈希", "完整性", "扣罚", "文件", "智能", "测试", "节点", "课程", "资料", "通证", "验证"], "hamming_distance": 0, "is_tampered": false, "removed_keywords": [], "sha256_chain": "24fcfe9f5cae438b450d7c185bd5450b1eb9d1df48b6352e5add7258913b706b", "sha256_local": "24fcfe9f5cae438b450d7c185bd5450b1eb9d1df48b6352e5add7258913b706b", "sha256_match": true, "sim_hash_chain": "0x8f30a25ce109e166d3cccd47ca2b704adf13f581e528581bda6bcc9aab8f09ca", "sim_hash_local": "0x8f30a25ce109e166d3cccd47ca2b704adf13f581e528581bda6bcc9aab8f09ca", "similarity_percent": 100.0, "text_length_chain": 0, "text_length_local": 1634} |  |
| VERIFY-I | 李子彤 | 篡改文件 I 对照资料 A | 通过 | {"added_keywords": ["BC401", "上架", "修改", "内容", "用于", "篡改", "系统", "说明"], "classification": "different", "common_keywords": ["256", "EduChain", "SHA", "上传", "区块", "哈希", "完整性", "文件", "测试", "课程", "资料", "验证"], "hamming_distance": 68, "is_tampered": true, "removed_keywords": ["SimHash", "下载", "交易", "合约", "扣罚", "智能", "节点", "通证"], "sha256_chain": "24fcfe9f5cae438b450d7c185bd5450b1eb9d1df48b6352e5add7258913b706b", "sha256_local": "1066a75b20758c1a84f4f671608be04c9c55e1f140a1738a5c58f1d08ec97525", "sha256_match": false, "sim_hash_chain": "0x8f30a25ce109e166d3cccd47ca2b704adf13f581e528581bda6bcc9aab8f09ca", "sim_hash_local": "0xb81ee34e01bad66c2594609ea2772aacd91fd02a5aa901cdb0bc8daa1ce8bda", "similarity_percent": 73.44, "text_length_chain": 0, "text_length_local": 654} |  |
| DL-E-WANG-DENY | 王东涵 | 无 CS301 权限拒绝 | 未通过 | HTTP 400: 权限不足: 该资料仅限选修 CS301 的学生下载，余额 120->125 | 120->125 |
| DL-F-TANG-DENY | 唐昊 | 无 CS302 权限拒绝 | 未通过 | HTTP 400: 权限不足: 该资料仅限选修 CS302 的学生下载，余额 120->125 | 120->125 |
| DL-G-LI-DENY | 李子彤 | 白名单外拒绝 | 未通过 | HTTP 400: 权限不足: 该资料仅限指定用户下载，余额 120->115 | 120->115 |
| DL-A-LI | 李子彤 | 公开资料正常下载 | 通过 | HTTP 200，153438 bytes，余额 120->115，下载哈希一致 | 120->115 |
| DL-F-YU | 于骐畅 | CS302 同课程下载 | 通过 | HTTP 200，42323 bytes，余额 120->115，下载哈希一致 | 120->115 |
| DL-E-FANG | 方天宇 | CS301 同课程下载 | 未通过 | HTTP 200，126801 bytes，余额 100->85，下载哈希一致 | 100->85 |
| DL-A-FANG | 方天宇 | 公开资料正常下载 | 未通过 | HTTP 200，153438 bytes，余额 100->85，下载哈希一致 | 100->85 |
| DL-A-XUE | 薛雨凇 | 公开资料正常下载 | 通过 | HTTP 200，153438 bytes，余额 120->115，下载哈希一致 | 120->115 |
| DL-G-FANG | 方天宇 | 白名单允许下载 | 未通过 | HTTP 200，126327 bytes，余额 100->85，下载哈希一致 | 100->85 |
| DL-UNAUTH | 未登录用户 | 未登录下载拦截 | 通过 | HTTP 401: 请先登录 |  |
| ACL-STUDENT-REWARD | 薛雨凇 | 学生调用管理员奖励 | 通过 | HTTP 403: 仅管理员可操作 |  |
| ACL-STUDENT-PENALTY | 薛雨凇 | 学生调用管理员扣罚 | 通过 | HTTP 403: 仅管理员可操作 |  |
| ACL-STUDENT-DELETE | 王东涵 | 学生删除他人资料 | 通过 | HTTP 403: 只能删除自己上传的资料 |  |
| OWNER-UPDATE | 周子皓 | 上传者修改自己的资料元数据 | 通过 | 更新 HTTP 200，再次查询名称：E_操作系统进程调度复习资料_所有者更新测试.pdf |  |
| TOKEN-TRANSFER | 方天宇 | 普通用户向唐昊转账 3 EDU | 通过 | HTTP 200，方 85->82，唐 135->138 | 方 85->82; 唐 135->138 |
| ADMIN-REWARD | 管理员 | 向王东涵发放 10 EDU | 通过 | HTTP 200，余额 125->135 | 125->135 |
| ADMIN-PENALTY | 管理员 | 对于骐畅扣罚 20 EDU | 通过 | HTTP 200，余额 115->95 | 115->95 |
| ADMIN-DELETE | 管理员 | 管理员删除李子彤资料 H | 通过 | HTTP 200: 删除成功，deleted=True |  |
| AUDIT-GLOBAL | 管理员 | 全局下载审计 | 通过 | HTTP 200，记录 6 条 |  |
| ACL-STUDENT-AUDIT | 薛雨凇 | 学生查看全局审计 | 通过 | HTTP 403: 仅管理员可查看全局审计 |  |
| ENV-AFTER | 管理员 | 高并发操作后健康检查 | 通过 | {"admin_count": 1, "block_number": 41, "chain_connected": true, "chain_id": 1337, "contracts": {"download_log": "0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0", "edu_token": "0x5FbDB2315678afecb367f032d93F642f64180aa3", "material_registry": "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"}, "contracts_ready": true, "deployer": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266", "download_count": 6, "ganache_connected": true, "ganache_url": "http://ganache:8545", "material_count": 7, "network": "ganache", "status": "running", "student_count": 8, "users_count": 9, "wallets_ready": 9} |  |

## 已发现问题

- 本轮未发现新的功能问题。

## 未执行项目

- 未执行后端容器重启与整套 Compose down/up 持久化测试：公网 HTTP 无法控制服务器 Docker，需要 SSH 权限。
- 未采集服务器后端与 Ganache 容器日志：需要 SSH 权限。

原始响应、完整交易哈希、钱包地址和验证结果见 `joint_test_results.json`。
