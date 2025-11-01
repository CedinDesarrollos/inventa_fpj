from flask import Flask,  url_for, current_app
from pathlib import Path
from .database import db, login_manager
from config import Settings
from .models import seed_default_admin

def create_app():
    base_dir = Path(__file__).resolve().parent  # .../agromax-app/app

    app = Flask(
        __name__,
        static_folder=str(base_dir / "static"),
        template_folder=str(base_dir / "templates"),
    )
    app.config.from_object(Settings)

    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        from .routes.core.auth import core_auth_bp
        from .routes.core.main import core_main_bp
        from .routes.ruteo.endpoints import ruteo_bp
        from .routes.abm_locales.endpoints import abm_locales_bp

        app.register_blueprint(core_auth_bp)
        app.register_blueprint(core_main_bp)
        app.register_blueprint(ruteo_bp, url_prefix="/ruteo")
        app.register_blueprint(abm_locales_bp, url_prefix="/locales")

        db.create_all()
        seed_default_admin()

        # Debug: ver dónde está buscando Jinja
        print("[JINJA SEARCHPATH]", app.jinja_loader.searchpath)

    @app.context_processor
    def jinja_helpers():
        def safe_url(endpoint: str, **values) -> str:
            """Devuelve url_for(endpoint) o '#' si el endpoint no existe."""
            try:
                return url_for(endpoint, **values)
            except Exception:
                return '#'

        def has_endpoint(endpoint: str) -> bool:
            """True si el endpoint está registrado en la app."""
            try:
                return endpoint in current_app.view_functions
            except Exception:
                return False

        return dict(safe_url=safe_url, has_endpoint=has_endpoint, cfg=app.config)

    return app
