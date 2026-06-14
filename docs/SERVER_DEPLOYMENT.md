# EduChain 阿里云课程测试部署

## 服务器要求

- 建议 Ubuntu 22.04 或更高版本。
- 安装 Docker Engine 与 Docker Compose Plugin。
- 安全组仅开放 `22`、`80`；不要开放 `5000` 和 `8545`。
- 本环境使用固定Ganache测试助记词和统一弱密码，只能用于短期课程测试。

## 首次部署

```bash
git clone <仓库地址> EduChain
cd EduChain
cp .env.server.example .env.server
```

修改 `.env.server` 中的 `SECRET_KEY`：

```bash
openssl rand -hex 32
```

将输出写入 `SECRET_KEY=` 后启动：

```bash
docker compose \
  --env-file .env.server \
  -f docker-compose.server.yml \
  up --build -d
```

访问 `http://服务器公网IP`。服务器模式只映射前端 `80:80`，后端和Ganache仅在Docker网络内可见。

## 启动检查

```bash
docker compose --env-file .env.server -f docker-compose.server.yml ps
docker compose --env-file .env.server -f docker-compose.server.yml logs --tail=100 backend
docker compose --env-file .env.server -f docker-compose.server.yml exec backend \
  python scripts/check_test_environment.py
```

健康检查应显示9个账号、8个学生、1个管理员、9个可用钱包和3个合约地址。

## 日常停止与启动

```bash
docker compose --env-file .env.server -f docker-compose.server.yml down
docker compose --env-file .env.server -f docker-compose.server.yml up -d
```

普通 `down` 不删除命名卷，链数据、合约地址、账号、钱包和上传文件会保留。

## 更新代码

```bash
git pull
docker compose --env-file .env.server -f docker-compose.server.yml \
  up --build -d
```

更新后再次执行环境检查脚本。

## 重置账号

仅在确实需要恢复统一测试密码和固定钱包映射时执行：

```bash
docker compose --env-file .env.server -f docker-compose.server.yml exec backend \
  python scripts/init_test_users.py --force
```

该操作覆盖运行时用户文件，但不会自动清空已有链上余额。

## 备份

先查看卷名：

```bash
docker volume ls | grep educhain
```

至少备份Ganache、运行时账号/合约配置和上传文件三个命名卷。备份前建议短暂停止服务，避免得到不一致快照。

## 危险操作

```bash
docker compose --env-file .env.server -f docker-compose.server.yml down -v
```

`down -v` 会删除链数据、EDU余额、资料记录、账号钱包映射、合约地址和上传文件。联动测试期间不要执行。

## 测试结束

至少完成一项：关闭服务器、关闭公网80端口、更换账号密码、限制访问IP或删除测试环境。不得上传真实隐私文件或真实资产。
