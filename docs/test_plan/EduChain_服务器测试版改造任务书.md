# EduChain服务器测试版改造任务书

## 一、任务目标

请完整阅读当前 EduChain 仓库，在不推翻现有 Vue + Flask + Web3.py + Solidity + Ganache + Docker Compose 架构的前提下，完成一套同时支持：

- 本地开发运行；
- 阿里云服务器公网部署；
- 8名成员、9个账号联合测试；
- 数据持久化；
- 课程权限测试；
- 多用户并发测试。

本次不迁移到 Sepolia、Besu、FISCO BCOS 或其他区块链平台，继续使用 Ganache 作为课程设计测试链。

## 二、账号总体设计

小组共有8名成员，但需要9个应用账号：

- 8个学生账号；
- 1个管理员账号；
- 唐昊同时拥有一个学生账号和一个管理员账号。

所有账号统一使用测试密码：

```text
123456
```

账号设计如下：

| 登录账号 | 姓名 | 性别 | 角色 | 密码 |
|---|---|---|---|---|
| 2023112379 | 唐昊 | 男 | student | 123456 |
| admin_2023112379 | 唐昊（管理员） | 男 | admin | 123456 |
| 2023112385 | 薛雨凇 | 男 | student | 123456 |
| 2023112380 | 于骐畅 | 女 | student | 123456 |
| 2023112318 | 周子皓 | 男 | student | 123456 |
| 2023112330 | 王东涵 | 男 | student | 123456 |
| 2023116100 | 谢傲宇 | 男 | student | 123456 |
| 2023112392 | 李子彤 | 女 | student | 123456 |
| 2023112317 | 方天宇 | 男 | student | 123456 |

管理员登录账号固定为：

```text
admin_2023112379
```

管理员账号和学生账号必须：

- 具有不同的登录ID；
- 分配不同的以太坊钱包；
- 拥有独立的Session；
- 拥有独立的EDU余额；
- 在权限判断中严格区分。

## 三、Ganache钱包分配

当前 Ganache 生成10个测试账户，按照以下方式固定分配：

| Ganache账户 | 用途 |
|---:|---|
| account[0] | 合约部署者、合约Owner |
| account[1] | 学生账号2023112379（唐昊） |
| account[2] | 管理员账号admin_2023112379（唐昊） |
| account[3] | 学生账号2023112385（薛雨凇） |
| account[4] | 学生账号2023112380（于骐畅） |
| account[5] | 学生账号2023112318（周子皓） |
| account[6] | 学生账号2023112330（王东涵） |
| account[7] | 学生账号2023116100（谢傲宇） |
| account[8] | 学生账号2023112392（李子彤） |
| account[9] | 学生账号2023112317（方天宇） |

要求：

1. 每次清空并重建 Ganache 后，映射顺序保持一致。
2. 后端普通重启不能改变用户钱包。
3. 每个应用账号必须拥有不同的钱包地址。
4. 私钥必须与对应地址匹配。
5. 发现地址和私钥不匹配时，后端必须拒绝启动并输出明确错误。
6. 日志中只能显示缩略地址，不能输出完整私钥。
7. 账号初始化后输出9个账号的钱包检查结果。
8. Ganache账户0不得分配给任何登录用户。

## 四、课程目录设计

请把课程代码与中文课程名称集中管理，不要分散硬编码在多个文件中。

建议统一课程目录：

```python
COURSE_CATALOG = {
    "BC401": "区块链技术及应用",
    "CS201": "数据结构",
    "CS301": "操作系统",
    "CS302": "计算机网络",
    "DB201": "数据库原理",
    "AI301": "人工智能导论"
}
```

前端、后端、筛选组件、上传页面、资料详情页和用户课程权限应使用同一份课程定义。

页面统一显示为：

```text
BC401 区块链技术及应用
CS201 数据结构
CS301 操作系统
CS302 计算机网络
DB201 数据库原理
AI301 人工智能导论
```

## 五、账号课程安排

```json
[
  {
    "student_id": "2023112379",
    "name": "唐昊",
    "gender": "男",
    "role": "student",
    "courses": ["BC401", "AI301"]
  },
  {
    "student_id": "admin_2023112379",
    "name": "唐昊（管理员）",
    "gender": "男",
    "role": "admin",
    "courses": []
  },
  {
    "student_id": "2023112385",
    "name": "薛雨凇",
    "gender": "男",
    "role": "student",
    "courses": ["BC401", "CS201"]
  },
  {
    "student_id": "2023112380",
    "name": "于骐畅",
    "gender": "女",
    "role": "student",
    "courses": ["BC401", "CS302"]
  },
  {
    "student_id": "2023112318",
    "name": "周子皓",
    "gender": "男",
    "role": "student",
    "courses": ["BC401", "CS301"]
  },
  {
    "student_id": "2023112330",
    "name": "王东涵",
    "gender": "男",
    "role": "student",
    "courses": ["CS302", "DB201"]
  },
  {
    "student_id": "2023116100",
    "name": "谢傲宇",
    "gender": "男",
    "role": "student",
    "courses": ["BC401", "DB201"]
  },
  {
    "student_id": "2023112392",
    "name": "李子彤",
    "gender": "女",
    "role": "student",
    "courses": ["BC401", "AI301"]
  },
  {
    "student_id": "2023112317",
    "name": "方天宇",
    "gender": "男",
    "role": "student",
    "courses": ["BC401", "CS201", "CS301"]
  }
]
```

管理员的 `courses` 可以为空，但管理员执行管理操作时不受课程限制。

## 六、用户数据文件设计

不要把运行后包含私钥和密码哈希的最终 `users.json` 继续作为普通代码提交。

建议拆分为：

### 1. 用户种子文件

```text
backend/config/users.seed.json
```

保存：

- student_id；
- name；
- gender；
- role；
- courses；
- account_index。

### 2. 运行时用户文件

```text
runtime/users.json
```

保存：

- student_id；
- name；
- gender；
- role；
- courses；
- password_hash；
- eth_address；
- eth_private_key；
- account_index。

运行时目录加入 `.gitignore`：

```gitignore
runtime/
.env.prod
.env.server
```

服务器模式使用：

```env
USERS_FILE=/app/runtime/users.json
USERS_SEED_FILE=/app/config/users.seed.json
```

## 七、账号初始化

实现幂等初始化脚本，例如：

```text
scripts/init_test_users.py
```

执行：

```bash
python scripts/init_test_users.py
```

统一初始密码：

```text
123456
```

初始化脚本负责：

1. 读取种子账号。
2. 检查 Ganache 连接。
3. 检查 Ganache 至少存在10个账户。
4. 按固定 account_index 分配地址和私钥。
5. 验证私钥推导地址与 Ganache 地址一致。
6. 使用 Werkzeug 生成密码哈希。
7. 写入运行时 users.json。
8. 检查登录ID不能重复。
9. 检查钱包地址不能重复。
10. 检查只能存在一个管理员账号。
11. 检查唐昊学生账号和管理员账号同时存在。
12. 输出账号初始化摘要。

第二次运行时：

- 不重新生成；
- 不覆盖现有数据；
- 不改变钱包映射；
- 输出“账号已初始化”。

重置时使用：

```bash
python scripts/init_test_users.py --force
```

`--force` 执行前必须输出警告。

## 八、登录与注册逻辑

当前学生注册校验可能要求账号必须是10位数字。由于管理员登录账号为：

```text
admin_2023112379
```

请区分：

- 学生账号格式校验；
- 预置管理员账号加载；
- 登录账号校验。

服务器模式关闭公开注册：

```env
ALLOW_PUBLIC_REGISTRATION=false
```

注册接口关闭时返回：

```text
当前为课程测试环境，账号已由管理员统一创建。
```

本地开发模式可以通过环境变量选择是否开放注册。

## 九、奖励逻辑

学生首次登录、EDU余额为0时，可获得100 EDU注册奖励。

管理员账号不得自动获得学生注册奖励。

要求：

1. 只有 `role=student` 才发放100 EDU。
2. 重复登录不能重复获得奖励。
3. 刷新页面不能重复获得奖励。
4. 并发发送多个登录请求不能获得多次奖励。
5. 奖励交易失败时，页面不能错误显示成功。
6. 唐昊学生账号可以获得奖励。
7. 唐昊管理员账号不能自动获得奖励。

## 十、双账号同时操作

唐昊需要同时操作学生账号和管理员账号。

测试文档中明确：

- Chrome普通窗口登录 `2023112379`；
- Edge、Firefox或Chrome无痕窗口登录 `admin_2023112379`。

不要在同一个浏览器普通窗口中同时保持两个账号登录。

## 十一、本地和服务器双模式

### 本地开发模式

继续支持：

```bash
docker compose up --build -d
```

本地端口：

```text
前端：8080
后端：5000
Ganache：8545
```

本地模式允许：

- Flask Debug；
- 源码目录挂载；
- 直接查看 Ganache RPC；
- 调试注册接口；
- 固定密码123456。

### 服务器测试模式

新增：

```text
docker-compose.server.yml
```

启动：

```bash
docker compose   --env-file .env.server   -f docker-compose.server.yml   up --build -d
```

服务器模式：

- 前端映射 `80:80`；
- 后端不映射5000；
- Ganache不映射8545；
- Flask Debug关闭；
- 使用Gunicorn；
- 禁止公开注册；
- 用户、链数据和上传文件使用持久化卷；
- 服务设置 `restart: unless-stopped`；
- 不挂载完整源代码目录；
- Nginx转发 `/api/` 到后端。

公网访问：

```text
http://服务器公网IP
```

## 十二、服务器安全边界

即使是课程测试系统，也必须做到：

1. 不公开8545。
2. 不公开5000。
3. 不在日志输出私钥。
4. 不在API返回私钥。
5. 不开启Flask Debug。
6. 不把运行时users.json提交到GitHub。
7. 不使用真实ETH或真实资产。
8. 阿里云安全组只开放22、80，后续可开放443。
9. 22端口尽量限制来源IP。
10. 页面标注“课程测试环境”。
11. 测试结束后关闭服务器、关闭公网端口或修改密码。

## 十三、数据持久化

服务器普通重启或容器重建后必须保留：

- Ganache链数据；
- 三个智能合约地址；
- EDU余额；
- 资料链上记录；
- 下载审计记录；
- 用户账号；
- 钱包映射；
- 密码哈希；
- 上传文件。

建议持久化：

```text
ganache_data
upload_data
user_data
contract_data
```

合约地址配置保存到持久化目录，例如：

```text
/app/runtime/contracts.env
```

普通操作：

```bash
docker compose -f docker-compose.server.yml down
docker compose -f docker-compose.server.yml up -d
```

不得丢失数据。

只有：

```bash
docker compose -f docker-compose.server.yml down -v
```

才清空测试环境。

文档中必须明确：

```text
down -v 会删除链数据、EDU余额、资料记录和上传文件。
```

## 十四、并发交易处理

8名成员可能同时登录、上传、下载和转账。

请检查：

- 多人同时领取首次登录奖励；
- 多人同时上传；
- 多人同时下载；
- 管理员奖励和扣罚；
- 同一发送钱包并发获取相同nonce。

最低要求：

```text
同一发送地址的“读取nonce—构造交易—签名—广播”过程串行化。
```

建议按钱包地址建立独立交易锁，避免：

```text
nonce too low
replacement transaction underpriced
already known
```

## 十五、服务器后端运行方式

服务器模式使用Gunicorn：

```bash
gunicorn   --workers 1   --threads 8   --timeout 120   --bind 0.0.0.0:5000   "app:create_app()"
```

暂时使用一个worker，避免：

- 多进程UserService状态不同步；
- 多进程同时写users.json；
- 多进程nonce管理冲突。

本地模式仍可使用：

```bash
python app.py
```

## 十六、健康检查

后端 `/api/health` 建议返回：

```json
{
  "status": "running",
  "network": "ganache",
  "chain_id": 1337,
  "chain_connected": true,
  "users_count": 9,
  "student_count": 8,
  "admin_count": 1,
  "wallets_ready": 9,
  "contracts_ready": true
}
```

不得返回：

- 私钥；
- 密码哈希；
- 助记词；
- SECRET_KEY。

增加检查脚本：

```text
scripts/check_test_environment.py
```

输出：

- 网络连接；
- Chain ID；
- 区块高度；
- 用户数；
- 学生数；
- 管理员数；
- 钱包缩略地址；
- 地址是否重复；
- 地址与私钥是否匹配；
- 合约地址；
- 资料数量；
- 各账号EDU余额。

## 十七、需要生成的独立文档

在仓库中创建：

```text
docs/TEST_ACCOUNT_MANUAL.md
docs/JOINT_TEST_MANUAL.md
docs/SERVER_DEPLOYMENT.md
```

三份文档必须相互独立。

- `TEST_ACCOUNT_MANUAL.md`：账号、姓名、密码、课程、钱包顺序和角色说明。
- `JOINT_TEST_MANUAL.md`：每位成员具体操作和完整测试流程。
- `SERVER_DEPLOYMENT.md`：阿里云部署、启动、停止、更新、备份和排错。

## 十八、验收要求

修改完成后必须实际验证：

1. 本地模式仍可启动。
2. 服务器模式可以启动。
3. 9个账号均可登录。
4. 唐昊学生账号和管理员账号均存在。
5. 两个账号的钱包地址不同。
6. 8个学生钱包全部唯一。
7. 管理员权限正确。
8. 学生无法调用管理员接口。
9. 统一密码123456可以登录。
10. 服务器注册接口被关闭。
11. 管理员不自动获得学生奖励。
12. 学生首次登录只获得一次奖励。
13. 课程代码与中文名称正确显示。
14. 课程访问策略有效。
15. 重复上传检测有效。
16. 相似文件检测有效。
17. 文件完整性验证有效。
18. EDU下载支付有效。
19. EDU转账有效。
20. 管理员奖励、扣罚和删除有效。
21. 后端重启后数据不丢失。
22. 容器down后重新up，数据不丢失。
23. 公网不暴露5000和8545。
24. Git改动中不出现运行时私钥。
25. 输出所有修改文件、启动命令和验证结果。

请优先保证稳定运行和测试可执行，不要迁移区块链平台，也不要随意修改前端视觉设计。
