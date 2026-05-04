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

    # ---------- 健康检查 ----------
    @app.route("/api/health", methods=["GET"])
    def health():
        """健康检查 & Ganache 连通性测试"""
        from web3 import Web3

        w3 = Web3(Web3.HTTPProvider(config.GANACHE_URL))
        connected = w3.is_connected()

        return jsonify({
            "code": 0,
            "msg": "ok",
            "data": {
                "status": "running",
                "ganache_connected": connected,
                "ganache_url": config.GANACHE_URL,
                "block_number": w3.eth.block_number if connected else None,
            },
        })

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