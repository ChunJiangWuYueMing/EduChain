# EduChain 本地运行说明

这份说明用于把项目发给同学后，在另一台电脑上重新跑起来。

## 需要先安装

- Docker Desktop
- Node.js 18 或更高版本
- Python 3.10 或更高版本
- Git Bash、PowerShell 或普通终端任选一个

## 推荐启动方式：Docker Compose

在项目根目录执行：

```bash
npm install
npm run compile
docker compose up --build -d
python -m pip install -r requirements.txt
python scripts/deploy.py
docker compose restart backend
```

然后打开：

```text
http://localhost:8080
```

说明：

- `docker compose up --build -d` 会启动 Ganache、Flask 后端和 Nginx 前端。
- `python scripts/deploy.py` 会把三个合约部署到本地 Ganache，并生成 `backend/.env`。
- 部署完成后必须重启后端一次，否则后端可能还没读到新的合约地址。

## 演示账号

| 账号 | 密码 | 角色 |
| :--- | :--- | :--- |
| `2023116101` | `2023116101` | 学生 |
| `2023116102` | `2023116102` | 学生 |
| `2023116103` | `2023116103` | 学生 |
| `admin` | `admin` | 管理员 |

## 常用命令

重新启动：

```bash
docker compose up -d
```

查看服务状态：

```bash
docker compose ps
```

查看后端日志：

```bash
docker compose logs -f backend
```

停止服务：

```bash
docker compose down
```

清空本地链数据后重新演示：

```bash
docker compose down -v
docker compose up --build -d
python scripts/deploy.py
docker compose restart backend
```

## 打包发给同学

在项目根目录执行：

```bash
npm run package:source
```

生成的文件在：

```text
dist/EduChain-source.zip
```

这个压缩包不会包含 `.git`、`node_modules`、虚拟环境、上传文件和 `backend/.env`。同学解压后按上面的 Docker Compose 步骤运行即可。

## 检查项目是否正常

前端检查：

```bash
npm run test:frontend
```

后端基础检查：

```bash
python -m py_compile backend/app.py backend/routes/material.py backend/services/material_service.py backend/services/chain_service.py
```

浏览器访问：

```text
http://localhost:8080
http://localhost:5000/api/health
```

## 常见问题

### 页面能打开，但显示链未连接

先确认 Ganache 容器正在运行：

```bash
docker compose ps
```

然后重新部署合约并重启后端：

```bash
python scripts/deploy.py
docker compose restart backend
```

### 上传或下载失败

确认后端日志里没有合约地址为空、Ganache 连接失败、文件格式不支持等错误：

```bash
docker compose logs -f backend
```

支持的文件格式是：`.docx`、`.md`、`.pdf`、`.pptx`、`.txt`。

### Docker 构建很慢

第一次构建会下载 Python 依赖和镜像，慢是正常的。之后再次启动用：

```bash
docker compose up -d
```
