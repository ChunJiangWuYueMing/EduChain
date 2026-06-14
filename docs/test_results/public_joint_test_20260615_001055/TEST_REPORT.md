# EduChain 公网九账号联动测试报告

- 服务器：`http://1.95.47.47`
- 开始时间：2026-06-15T00:10:55+08:00
- 完成时间：2026-06-15T00:18:56+08:00
- 结果：42/51 通过，82.35%

## 环境基线

- 测试前区块高度：4
- 测试后区块高度：48
- 测试前资料数：0
- 测试后资料数：7
- 测试后下载记录：4

## 测试结果

| 编号 | 操作者 | 功能 | 结论 | 实际结果 | 余额变化 |
|---|---|---|---|---|---|
| FILE-01 | 测试工具 | 测试文件完整性基线 | 通过 | 文件哈希已计算 |  |
| ENV-HEALTH | 管理员 | 公网健康检查 | 通过 | {"admin_count": 1, "block_number": 4, "chain_connected": true, "chain_id": 1337, "contracts": {"download_log": "0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0", "edu_token": "0x5FbDB2315678afecb367f032d93F642f64180aa3", "material_registry": "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"}, "contracts_ready": true, "deployer": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266", "download_count": 0, "ganache_connected": true, "ganache_url": "http://ganache:8545", "material_count": 0, "network": "ganache", "status": "running", "student_count": 8, "users_count": 9, "wallets_ready": 9} |  |
| AUTH-REGISTER | 未登录用户 | 服务器关闭公开注册 | 通过 | HTTP 403: 当前为课程测试环境，账号已由管理员统一创建。 |  |
| AUTH-BAD-PASSWORD | 唐昊 | 错误密码登录 | 通过 | HTTP 401: 学号或密码错误 |  |
| LOGIN-admin_2023112379 | 唐昊（管理员） | 并发登录及首次奖励 | 通过 | HTTP 200，奖励 0 EDU，余额 0 | +0 EDU |
| LOGIN-2023112379 | 唐昊 | 并发登录及首次奖励 | 通过 | HTTP 200，奖励 100 EDU，余额 100 | +100 EDU |
| LOGIN-2023112380 | 于骐畅 | 并发登录及首次奖励 | 通过 | HTTP 200，奖励 100 EDU，余额 100 | +100 EDU |
| LOGIN-2023112385 | 薛雨凇 | 并发登录及首次奖励 | 通过 | HTTP 200，奖励 100 EDU，余额 100 | +100 EDU |
| LOGIN-2023112330 | 王东涵 | 并发登录及首次奖励 | 通过 | HTTP 200，奖励 100 EDU，余额 100 | +100 EDU |
| LOGIN-2023112318 | 周子皓 | 并发登录及首次奖励 | 通过 | HTTP 200，奖励 100 EDU，余额 100 | +100 EDU |
| LOGIN-2023112317 | 方天宇 | 并发登录及首次奖励 | 通过 | HTTP 200，奖励 100 EDU，余额 100 | +100 EDU |
| LOGIN-2023112392 | 李子彤 | 并发登录及首次奖励 | 通过 | HTTP 200，奖励 100 EDU，余额 100 | +100 EDU |
| LOGIN-2023116100 | 谢傲宇 | 并发登录及首次奖励 | 通过 | HTTP 200，奖励 100 EDU，余额 100 | +100 EDU |
| LOGIN-UNIQUE | 管理员 | 九账号钱包唯一性 | 通过 | 读取 9 个钱包，唯一值 9 |  |
| LOGIN-IDEMPOTENT | 全部账号 | 并发重复登录奖励幂等 | 通过 | {"2023112379": 0, "admin_2023112379": 0, "2023112385": 0, "2023112380": 0, "2023112318": 0, "2023112330": 0, "2023116100": 0, "2023112392": 0, "2023112317": 0} |  |
| UPLOAD-A | 唐昊 | 上传公开资料 A | 通过 | HTTP 200，资料 MAT_1781453468_0953f238，余额 100->120 | 100->120 |
| UPLOAD-B | 薛雨凇 | 完全重复文件拦截 | 通过 | HTTP 400: 文件已存在，与资料 MAT_1781453468_0953f238 完全相同（SHA-256 匹配） | 100->100 |
| UPLOAD-H | 李子彤 | 并发上传资料 H | 通过 | HTTP 200，资料 MAT_1781453476_53632f5f，余额 +20 | 100->120 |
| UPLOAD-D | 薛雨凇 | 并发上传资料 D | 通过 | HTTP 200，资料 MAT_1781453477_4b716a64，余额 +20 | 100->120 |
| UPLOAD-F | 王东涵 | 并发上传资料 F | 通过 | HTTP 200，资料 MAT_1781453477_6e119578，余额 +20 | 100->120 |
| UPLOAD-C | 于骐畅 | 并发上传资料 C | 通过 | HTTP 200，资料 MAT_1781453477_0c5a077b，余额 +20 | 100->120 |
| UPLOAD-E | 周子皓 | 并发上传资料 E | 通过 | HTTP 200，资料 MAT_1781453478_d96832b1，余额 +20 | 100->120 |
| UPLOAD-G | 谢傲宇 | 并发上传资料 G | 通过 | HTTP 200，资料 MAT_1781453478_2aef0f38，余额 +20 | 100->120 |
| VERIFY-A | 李子彤 | 资料 A 原文件完整性验证 | 通过 | {"added_keywords": [], "classification": "identical", "common_keywords": ["256", "EduChain", "SHA", "SimHash", "上传", "下载", "交易", "区块", "合约", "哈希", "完整性", "扣罚", "文件", "智能", "测试", "节点", "课程", "资料", "通证", "验证"], "hamming_distance": 0, "is_tampered": false, "removed_keywords": [], "sha256_chain": "24fcfe9f5cae438b450d7c185bd5450b1eb9d1df48b6352e5add7258913b706b", "sha256_local": "24fcfe9f5cae438b450d7c185bd5450b1eb9d1df48b6352e5add7258913b706b", "sha256_match": true, "sim_hash_chain": "0x8f30a25ce109e166d3cccd47ca2b704adf13f581e528581bda6bcc9aab8f09ca", "sim_hash_local": "0x8f30a25ce109e166d3cccd47ca2b704adf13f581e528581bda6bcc9aab8f09ca", "similarity_percent": 100.0, "text_length_chain": 0, "text_length_local": 1634} |  |
| VERIFY-I | 李子彤 | 篡改文件 I 对照资料 A | 通过 | {"added_keywords": ["BC401", "上架", "修改", "内容", "用于", "篡改", "系统", "说明"], "classification": "different", "common_keywords": ["256", "EduChain", "SHA", "上传", "区块", "哈希", "完整性", "文件", "测试", "课程", "资料", "验证"], "hamming_distance": 68, "is_tampered": true, "removed_keywords": ["SimHash", "下载", "交易", "合约", "扣罚", "智能", "节点", "通证"], "sha256_chain": "24fcfe9f5cae438b450d7c185bd5450b1eb9d1df48b6352e5add7258913b706b", "sha256_local": "1066a75b20758c1a84f4f671608be04c9c55e1f140a1738a5c58f1d08ec97525", "sha256_match": false, "sim_hash_chain": "0x8f30a25ce109e166d3cccd47ca2b704adf13f581e528581bda6bcc9aab8f09ca", "sim_hash_local": "0xb81ee34e01bad66c2594609ea2772aacd91fd02a5aa901cdb0bc8daa1ce8bda", "similarity_percent": 73.44, "text_length_chain": 0, "text_length_local": 654} |  |
| DL-F-TANG-DENY | 唐昊 | 无 CS302 权限拒绝 | 通过 | HTTP 400: 权限不足: 该资料仅限选修 CS302 的学生下载，余额 120->125 | 120->125 |
| DL-G-LI-DENY | 李子彤 | 白名单外拒绝 | 通过 | HTTP 400: 权限不足: 该资料仅限指定用户下载，余额 120->120 | 120->120 |
| DL-G-FANG | 方天宇 | 白名单允许下载 | 未通过 | HTTP 400: {'message': "VM Exception while processing transaction: the tx doesn't have the correct nonce. account has nonce of: 22 tx has nonce of: 21 (vm hf=shanghai -> block -> tx)", 'stack': "RuntimeError: VM Exception while processing transaction: the tx doesn't have the correct nonce. account has nonce of: 22 tx has nonce of: 21 (vm hf=shanghai -> block -> tx)\n    at Miner.<anonymous> (/app/dist/node/1.js:2:176352)\n    at async Miner.<anonymous> (/app/dist/node/1.js:2:174660)\n    at async Miner.<anonymous> (/app/dist/node/1.js:2:173310)\n    at async Miner.mine (/app/dist/node/1.js:2:177695)\n    at async Blockchain.mine (/app/dist/node/1.js:2:87561)\n    at async Promise.all (index 0)\n    at async TransactionPool.emit (/app/node_modules/emittery/index.js:303:3)", 'code': -32000, 'name': 'RuntimeError', 'data': {'hash': '0xaae70104dca8580c390bf144f332d129d705af56a336f09c06af4969370e1709', 'programCounter': 0, 'result': '0xaae70104dca8580c390bf144f332d129d705af56a336f09c06af4969370e1709', 'reason': None, 'message': "the tx doesn't have the correct nonce. account has nonce of: 22 tx has nonce of: 21 (vm hf=shanghai -> block -> tx)"}}，余额 100->90 | 100->90 |
| DL-E-WANG-DENY | 王东涵 | 无 CS301 权限拒绝 | 通过 | HTTP 400: 权限不足: 该资料仅限选修 CS301 的学生下载，余额 120->120 | 120->120 |
| DL-A-FANG | 方天宇 | 公开资料正常下载 | 通过 | HTTP 200，153438 bytes，余额 100->90，下载哈希一致 | 100->90 |
| DL-E-FANG | 方天宇 | CS301 同课程下载 | 未通过 | HTTP 500: 下载失败: HTTPConnectionPool(host='ganache', port=8545): Read timed out. (read timeout=10)，余额 100->90 | 100->90 |
| DL-F-YU | 于骐畅 | CS302 同课程下载 | 通过 | HTTP 200，42323 bytes，余额 120->115，下载哈希一致 | 120->115 |
| DL-A-XUE | 薛雨凇 | 公开资料正常下载 | 通过 | HTTP 200，153438 bytes，余额 120->115，下载哈希一致 | 120->115 |
| DL-A-LI | 李子彤 | 公开资料正常下载 | 未通过 | HTTP 500: 下载失败: HTTPConnectionPool(host='ganache', port=8545): Read timed out. (read timeout=10)，余额 120->120 | 120->120 |
| DL-UNAUTH | 未登录用户 | 未登录下载拦截 | 通过 | HTTP 401: 请先登录 |  |
| ACL-STUDENT-REWARD | 薛雨凇 | 学生调用管理员奖励 | 通过 | HTTP 403: 仅管理员可操作 |  |
| ACL-STUDENT-PENALTY | 薛雨凇 | 学生调用管理员扣罚 | 通过 | HTTP 403: 仅管理员可操作 |  |
| ACL-STUDENT-DELETE | 王东涵 | 学生删除他人资料 | 通过 | HTTP 403: 只能删除自己上传的资料 |  |
| OWNER-UPDATE | 周子皓 | 上传者修改自己的资料元数据 | 未通过 | 更新 HTTP 200，再次查询名称：E_操作系统进程调度复习资料.pdf |  |
| TOKEN-TRANSFER | 方天宇 | 普通用户向唐昊转账 3 EDU | 通过 | HTTP 200，方 90->87，唐 130->133 | 方 90->87; 唐 130->133 |
| ADMIN-REWARD | 管理员 | 向王东涵发放 10 EDU | 通过 | HTTP 200，余额 125->135 | 125->135 |
| ADMIN-PENALTY | 管理员 | 对于骐畅扣罚 20 EDU | 通过 | HTTP 200，余额 115->95 | 115->95 |
| ADMIN-DELETE | 管理员 | 管理员删除李子彤资料 H | 未通过 | HTTP 500: 删除失败: 交易失败: tx=0x94626021e419def25fe3d52d33257e04685bc5d88af1d61d4653b9eac34c948c，deleted=False |  |
| DL-E-FANG-RETRY | 方天宇 | CS301 同课程下载顺序补测 | 通过 | HTTP 200，余额 87->82，文件哈希一致 | 87->82 |
| DL-A-LI-RETRY | 李子彤 | 公开资料下载顺序补测 | 未通过 | HTTP 500，余额 120->120，文件哈希未验证 | 120->120 |
| TOKEN-HISTORY | 方天宇、唐昊 | 链上交易历史查询 | 未通过 | 两个账号合计返回 0 条 |  |
| AUDIT-GLOBAL | 管理员 | 全局下载审计完整性 | 未通过 | 实际仅 4 条，资料 G 的已扣款下载缺失 |  |
| ACL-STUDENT-AUDIT | 薛雨凇 | 学生查看全局审计 | 通过 | HTTP 403: 仅管理员可查看全局审计 |  |
| TOKEN-FINAL-BALANCES | 全部账号 | 最终 EDU 总账核对 | 未通过 | {"2023112379": 133, "admin_2023112379": 0, "2023112385": 115, "2023112380": 95, "2023112318": 125, "2023112330": 135, "2023116100": 125, "2023112392": 120, "2023112317": 82} |  |
| SECURITY-PORTS | 测试工具 | 后端与 Ganache 公网端口 | 通过 | {"5000": false, "8545": false} |  |
| ENV-AFTER | 管理员 | 并发故障恢复后健康检查 | 通过 | {"admin_count": 1, "block_number": 48, "chain_connected": true, "chain_id": 1337, "contracts": {"download_log": "0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0", "edu_token": "0x5FbDB2315678afecb367f032d93F642f64180aa3", "material_registry": "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"}, "contracts_ready": true, "deployer": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266", "download_count": 4, "ganache_connected": true, "ganache_url": "http://ganache:8545", "material_count": 7, "network": "ganache", "status": "running", "student_count": 8, "users_count": 9, "wallets_ready": 9} |  |

## 已发现问题

- **HIGH：资料更新结果未持久化**：资料更新接口返回成功，但再次查询仍是旧名称，链上元数据没有更新。
- **HIGH：管理员无法删除其他用户资料**：后端权限判断允许管理员，但 MaterialRegistry.softDelete 仍要求 caller 必须等于上传者，导致管理员删除交易失败。
- **CRITICAL：白名单下载出现扣款成功但接口失败**：方天宇下载资料 G 时链上已转账 5 EDU，上传者谢傲宇余额增加，但 HTTP 返回 nonce 错误，文件未返回，DownloadLog 也未写入。下载支付与审计记录不是原子操作。
- **HIGH：并发下载触发 nonce 冲突和 Ganache 超时**：9 个下载请求并发时出现 incorrect nonce、Ganache 读取超时和短暂 502。当前交易锁不能覆盖节点已接收交易但 HTTP 调用超时的情况。
- **HIGH：交易历史接口返回空列表**：余额和链上转账已经发生，但 /api/token/history 对方天宇和唐昊均返回 0 条记录，钱包页无法展示真实交易历史。
- **HIGH：李子彤公开资料下载持续超时**：并发请求和后续低并发单请求均出现 Ganache 读取超时；余额和 allowance 未变化，本轮没有扣款。

## 截图证据

本轮共生成11张截图，位于 `screenshots/`，对应关系见 `SCREENSHOT_INDEX.md`。

## 未执行项目

- 未执行后端容器重启与整套 Compose down/up 持久化测试：公网 HTTP 无法控制服务器 Docker，需要 SSH 权限。
- 未采集服务器后端与 Ganache 容器日志：需要 SSH 权限。

原始响应、完整交易哈希、钱包地址和验证结果见 `joint_test_results.json`。
