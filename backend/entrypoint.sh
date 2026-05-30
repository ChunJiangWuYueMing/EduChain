#!/bin/bash
set -e

GANACHE_URL="${GANACHE_URL:-http://ganache:8545}"

# ===== 1. 等待 Ganache 就绪 =====
echo "⏳ 等待 Ganache ($GANACHE_URL) 就绪..."
MAX_RETRIES=30
for i in $(seq 1 $MAX_RETRIES); do
    if python -c "
from web3 import Web3
w3 = Web3(Web3.HTTPProvider('$GANACHE_URL'))
assert w3.is_connected() and len(w3.eth.accounts) > 0
" 2>/dev/null; then
        echo "✅ Ganache 已就绪"
        break
    fi
    if [ "$i" = "$MAX_RETRIES" ]; then
        echo "❌ Ganache 未就绪，超时退出"
        exit 1
    fi
    echo "   重试 ($i/$MAX_RETRIES)..."
    sleep 2
done

# ===== 2. 检查合约是否已部署且有效 =====
NEED_DEPLOY=true

# 优先从 .env 读取已有合约地址
if [ -f /app/.env ]; then
    set -a
    source /app/.env
    set +a
fi

if [ -n "$EDU_TOKEN_ADDRESS" ]; then
    # 地址存在，验证链上合约代码是否还在
    if python -c "
from web3 import Web3
import os
w3 = Web3(Web3.HTTPProvider('$GANACHE_URL'))
addr = os.environ['EDU_TOKEN_ADDRESS']
code = w3.eth.get_code(Web3.to_checksum_address(addr))
assert len(code) > 2, 'no code'
" 2>/dev/null; then
        NEED_DEPLOY=false
        echo "✅ 合约已部署且有效 (EduToken=$EDU_TOKEN_ADDRESS)，跳过部署"
    else
        echo "⚠️  合约地址存在但链上无效，需重新部署"
    fi
fi

if [ "$NEED_DEPLOY" = true ]; then
    echo "📦 部署合约..."
    python /app/scripts/deploy.py --ganache-url "$GANACHE_URL"

    # deploy.py 写了 .env，重新加载
    if [ -f /app/.env ]; then
        set -a
        source /app/.env
        set +a
        echo "✅ 已加载 .env 环境变量"
    fi
fi

# ===== 3. 启动 Flask =====
echo "🚀 启动 EduChain 后端..."
exec python app.py