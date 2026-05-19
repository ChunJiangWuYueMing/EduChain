"""EduChain Flask 应用入口"""
import os
from flask import Flask
from flask_cors import CORS
from config import config
from utils.response import success, server_error


def create_app() -> Flask:
    """应用工厂"""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH

    CORS(app, supports_credentials=True)

    # 确保上传目录存在
    os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)

    # ---------- 初始化链服务 ----------
    from services.chain_service import chain_service

    chain_ok = False
    try:
        chain_service.init_app()
        chain_ok = True
        app.logger.info("✅ ChainService 初始化成功")
    except Exception as e:
        app.logger.warning(f"⚠️  ChainService 初始化失败: {e}")

    # ---------- 初始化用户服务 + 注入私钥 ----------
    from services.user_service import user_service

    if chain_ok:
        try:
            accounts = chain_service.get_ganache_accounts()
            user_service.init_users(ganache_accounts=accounts)
            user_count = len(user_service.get_all_users())
            app.logger.info(f"✅ UserService 初始化成功，加载 {user_count} 个用户")

            # 将用户私钥注入 chain_service，用于签名交易
            keys_registered = 0
            for user in user_service.get_all_users():
                if user.eth_private_key and user.eth_address:
                    chain_service.register_user_key(user.eth_address, user.eth_private_key)
                    keys_registered += 1

            summary = user_service.key_summary
            if keys_registered > 0:
                app.logger.info(
                    f"✅ 用户签名交易已就绪: "
                    f"{keys_registered}/{summary['total_users']} 个用户私钥已注入 ChainService"
                )
            else:
                app.logger.warning(
                    f"⚠️  用户签名交易不可用: 0/{summary['total_users']} 个用户拥有私钥\n"
                    f"   approve/transfer 等用户侧交易将会失败\n"
                    f"   请确保: (1) Ganache 使用固定助记词启动 (2) 已运行 deploy.py"
                )

            if summary["without_keys"]:
                app.logger.info(
                    f"   缺少私钥的用户: {summary['missing']}"
                )

        except Exception as e:
            app.logger.warning(f"⚠️  UserService 初始化失败: {e}")

    # ---------- 健康检查（统一响应格式） ----------
    @app.route("/api/health", methods=["GET"])
    def health():
        connected = chain_service.is_connected()
        data = {
            "status": "running",
            "ganache_connected": connected,
            "ganache_url": config.GANACHE_URL,
        }

        if connected:
            try:
                data["block_number"] = chain_service.get_block_number()
                data["deployer"] = chain_service.deployer
                data["contracts"] = {
                    "edu_token": config.EDU_TOKEN_ADDRESS,
                    "material_registry": config.MATERIAL_REGISTRY_ADDRESS,
                    "download_log": config.DOWNLOAD_LOG_ADDRESS,
                }
                data["material_count"] = chain_service.get_material_count()
                data["download_count"] = chain_service.get_download_count()
            except Exception as e:
                data["chain_error"] = str(e)

        return success(data)

    # ---------- 注册蓝图（第5-7步实现后取消注释） ----------
    # from routes.auth import auth_bp
    # from routes.material import material_bp
    # from routes.token import token_bp
    # from routes.audit import audit_bp
    # app.register_blueprint(auth_bp, url_prefix="/api/auth")
    # app.register_blueprint(material_bp, url_prefix="/api/material")
    # app.register_blueprint(token_bp, url_prefix="/api/token")
    # app.register_blueprint(audit_bp, url_prefix="/api/audit")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=config.DEBUG)