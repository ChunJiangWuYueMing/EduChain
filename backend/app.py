"""EduChain Flask application entrypoint."""

import os

from flask import Flask, send_from_directory
from flask_cors import CORS

from config import config
from utils.response import success


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH

    CORS(app, supports_credentials=True)
    os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)

    from services.chain_service import chain_service

    chain_ok = False
    try:
        chain_service.init_app()
        chain_ok = True
        app.logger.info("ChainService initialized")
    except Exception as exc:
        app.logger.warning(f"ChainService init failed: {exc}")

    from services.user_service import user_service

    try:
        accounts = chain_service.get_ganache_accounts() if chain_ok else []
        user_service.init_users(ganache_accounts=accounts)
        user_count = len(user_service.get_all_users())
        app.logger.info(f"UserService initialized with {user_count} users")

        keys_registered = 0
        for user in user_service.get_all_users():
            if user.eth_private_key and user.eth_address:
                chain_service.register_user_key(user.eth_address, user.eth_private_key)
                keys_registered += 1

        summary = user_service.key_summary
        if keys_registered > 0:
            app.logger.info(
                "Loaded signing keys for %s/%s users",
                keys_registered,
                summary["total_users"],
            )
        elif summary["total_users"] > 0:
            app.logger.warning(
                "No user signing keys are available; user-initiated chain transactions will fail"
            )

        if summary["without_keys"]:
            app.logger.info("Users without private keys: %s", summary["missing"])
    except Exception as exc:
        app.logger.warning(f"UserService init failed: {exc}")

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
                data["chain_id"] = chain_service.get_chain_id()
                data["deployer"] = chain_service.deployer
                data["contracts"] = {
                    "edu_token": config.EDU_TOKEN_ADDRESS,
                    "material_registry": config.MATERIAL_REGISTRY_ADDRESS,
                    "download_log": config.DOWNLOAD_LOG_ADDRESS,
                }
                data["material_count"] = chain_service.get_material_count()
                data["download_count"] = chain_service.get_download_count()
            except Exception as exc:
                data["chain_error"] = str(exc)

        return success(data)

    from routes.auth import auth_bp
    from routes.material import material_bp
    from routes.token import token_bp
    from routes.audit import audit_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(material_bp, url_prefix="/api/material")
    app.register_blueprint(token_bp, url_prefix="/api/token")
    app.register_blueprint(audit_bp, url_prefix="/api/audit")

    frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path: str):
        if path.startswith("api/"):
            return success(None, "API route not found", 404)
        if path and os.path.exists(os.path.join(frontend_dir, path)):
            return send_from_directory(frontend_dir, path)
        return send_from_directory(frontend_dir, "index.html")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=config.DEBUG)
