# EduChain

EduChain 是一个面向校园学习资料共享的区块链可信分发原型系统。它把“资料是否可信”和“共享是否有激励”放在同一条演示链路里：资料上传后生成 SHA-256 文件指纹和 256 位 SimHash 内容指纹，并把关键元数据登记到链上；学生下载资料时使用 EDU 积分完成转移，下载行为也会进入链上审计记录。

当前项目已经形成可演示闭环：合约层、Flask 后端、内容指纹引擎、Vanilla JS 前端、Docker Compose 部署和基础测试脚本都已落地。

## 当前能力

- 智能合约：`EduToken`、`MaterialRegistry`、`DownloadLog`，覆盖积分铸造、资料登记、下载扣费和审计记录。
- 后端 API：`auth`、`material`、`token`、`audit` 四组路由，统一返回 `{"code": int, "msg": str, "data": any}`。
- 服务层边界：所有链交互集中在 `backend/services/chain_service.py`，路由层不直接操作 Web3。
- 内容指纹：SHA-256 校验文件级完整性，SimHash 辅助判断内容相似度，并输出关键词差异。
- 前端 SPA：资料广场、发布资料、真伪校验、积分账户、审计追溯、系统状态。
- 积分机制：首次登录奖励 100 EDU，上传奖励 20 EDU，下载按资料价格转账，管理员可执行奖励和抄袭扣罚。
- 部署方式：Docker Compose 启动 Ganache、Flask 后端和 Nginx 前端。
- 演示资料：`demo/` 中保留原始课件和篡改课件，用于展示 SHA-256 与 SimHash 的差异判断。

## 技术栈

| 层级 | 技术 |
| :--- | :--- |
| 前端 | HTML / CSS / Vanilla JS |
| 后端 | Python / Flask |
| 区块链交互 | Web3.py |
| 智能合约 | Solidity `^0.8.20` / OpenZeppelin |
| 本地链 | Ganache，`chainId=1337` |
| 内容提取 | `python-pptx`、`python-docx`、`PyPDF2`、纯文本解析 |
| 内容指纹 | SHA-256 + 256 位 SimHash |
| 部署 | Docker Compose |

## 项目结构

```text
EduChain/
├─ contracts/                 # Solidity 合约
├─ scripts/                   # 合约编译与部署脚本
├─ backend/
│  ├─ app.py                  # Flask 应用工厂
│  ├─ routes/                 # REST API 路由
│  ├─ services/               # 业务服务层
│  ├─ fingerprint/            # 内容提取与指纹计算
│  ├─ compiled/               # 合约编译产物
│  ├─ users.json              # 开发环境用户数据
│  └─ tests/                  # 后端测试脚本
├─ frontend/
│  ├─ index.html              # 前端 SPA
│  ├─ market-filters.js       # 资料广场筛选逻辑
│  ├─ nginx.conf              # 前端容器代理配置
│  └─ tests/                  # 前端静态行为检查
├─ demo/                      # 答辩演示资料
└─ docs/                      # 演示与限制说明
```

## 快速运行

推荐使用 Docker Compose 运行。另一台电脑首次启动时，按下面顺序执行：

1. 安装 Node 依赖并编译合约：

```bash
npm install
npm run compile
```

2. 启动 Ganache、后端和前端容器：

```bash
docker compose up --build -d
```

3. 安装 Python 依赖并部署合约：

```bash
python -m pip install -r requirements.txt
python scripts/deploy.py
```

4. 重启后端，让后端读取新生成的合约地址：

```bash
docker compose restart backend
```

5. 打开系统：

```text
http://localhost:8080
```

默认端口：Ganache `8545`，后端 `5000`，前端 `8080`。

更详细的同学电脑运行步骤见 [docs/run-local.md](docs/run-local.md)。

打包源码给同学：

```bash
npm run package:source
```

生成文件：`dist/EduChain-source.zip`。

## 演示账号

| 账号 | 密码 | 角色 |
| :--- | :--- | :--- |
| `2023116101` | `2023116101` | 学生 |
| `2023116102` | `2023116102` | 学生 |
| `2023116103` | `2023116103` | 学生 |
| `admin` | `admin` | 管理员 |

## 核心演示流程

1. 学生 A 登录，首次登录自动获得 100 EDU。
2. 学生 A 发布学习资料，系统生成 SHA-256 和 SimHash，并登记链上元数据。
3. 学生 A 获得上传奖励 20 EDU。
4. 学生 B 登录并下载资料，系统完成权限检查、余额检查、积分转账和下载记录上链。
5. 在真伪校验页上传原始文件，SHA-256 与 SimHash 均应高度一致。
6. 上传篡改版本，SHA-256 不一致，SimHash 仍可给出内容相似度和关键词差异。
7. 在积分账户查看余额和流水，在审计追溯查看链上下载记录。
8. 在系统状态页查看后端状态、链连接、区块高度和合约地址。

## API 概览

| 分组 | 路径前缀 | 说明 |
| :--- | :--- | :--- |
| 认证 | `/api/auth` | 登录、注册、会话信息、退出 |
| 资料 | `/api/material` | 资料上传、列表、详情、下载、校验、更新、删除 |
| 积分 | `/api/token` | 余额、授权、转账、历史、奖励、扣罚 |
| 审计 | `/api/audit` | 下载记录、用户资料、审计统计 |
| 健康检查 | `/api/health` | 后端状态、Ganache 连接、区块高度、合约地址 |

## 测试

前端检查：

```bash
npm run test:frontend
```

后端脚本：

```bash
python -m backend.tests.test_fingerprint
python -m backend.tests.test_chain_service
python -m backend.tests.test_token_service
python -m backend.tests.test_p02_signing
```

## 当前限制

- 当前是本地 Ganache 原型，不是生产级多节点区块链环境。
- 文件本体仍存储在链下，链上保存文件指纹、内容指纹、访问策略和审计信息。
- 权限判断由后端执行，链上主要负责策略数据和操作记录的可信存证。
- SimHash 是内容相似度辅助判断，不能替代人工学术审查。
- 扫描版 PDF、图片型 PPT 等没有文本层的文件需要后续接入 OCR。
- 用户数据仍在 `backend/users.json` 中，适合开发演示，不适合生产环境。

## 项目定位

EduChain 的重点不是做一个普通文件网盘，而是展示校园资料共享中的可信证明链路：能证明资料来源，能检查文件是否被改动，能量化内容相似度，并用 EDU 积分鼓励同学共享优质资料。
