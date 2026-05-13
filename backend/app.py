"""EduChain Flask 应用入口"""
import os
from flask import Flask, jsonify
from flask_cors import CORS
from config import config


def create_app() -> Flask:
    """应用工厂"""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH

    CORS(app)

    # 确保上传目录存在
    os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)

    # ---------- 初始化链服务 ----------
    from services.chain_service import chain_service

    try:
        chain_service.init_app()
        app.logger.info("✅ ChainService 初始化成功")
        app.logger.info(f"   Ganache: {config.GANACHE_URL}")
        app.logger.info(f"   Deployer: {chain_service.deployer}")
        app.logger.info(f"   EduToken: {config.EDU_TOKEN_ADDRESS}")
        app.logger.info(f"   MaterialRegistry: {config.MATERIAL_REGISTRY_ADDRESS}")
        app.logger.info(f"   DownloadLog: {config.DOWNLOAD_LOG_ADDRESS}")
    except Exception as e:
        app.logger.warning(f"⚠️  ChainService 初始化失败: {e}")
        app.logger.warning("   后端可启动，但链相关接口不可用。请确认 Ganache 已运行且合约已部署。")

    # ---------- 健康检查 ----------
    @app.route("/api/health", methods=["GET"])
    def health():
        """健康检查 & 链服务状态"""
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

        return jsonify({"code": 0, "msg": "ok", "data": data})

    # ---------- 后续会注册蓝图 ----------
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
