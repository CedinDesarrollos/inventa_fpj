from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .database import db
from config import Settings

# Multi-marca por company_slug (PROJECT_SLUG por defecto)
def current_company_slug():
    return Settings.PROJECT_SLUG

class User(UserMixin, db.Model):
    __tablename__ = "usuarios"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, raw: str):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw: str) -> bool:
        return check_password_hash(self.password_hash, raw)

class Depot(db.Model):
    __tablename__ = "centros_logisticos"
    id = db.Column(db.Integer, primary_key=True)
    company_slug = db.Column(db.String(64), index=True, nullable=False, default=current_company_slug)
    name = db.Column(db.String(255), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    active = db.Column(db.Boolean, default=True)

class Local(db.Model):
    __tablename__ = "locales"
    id = db.Column(db.String(64), primary_key=True)  # admite códigos/strings
    company_slug = db.Column(db.String(64), index=True, nullable=False, default=current_company_slug)
    name = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(120))
    lat = db.Column(db.Float, nullable=False)
    lon = db.Column(db.Float, nullable=False)
    rank = db.Column(db.Integer)
    venta_por_dia = db.Column(db.Numeric(14,2))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Ruta(db.Model):
    __tablename__ = "rutas"
    id = db.Column(db.Integer, primary_key=True)
    company_slug = db.Column(db.String(64), index=True, nullable=False, default=current_company_slug)
    fecha = db.Column(db.Date, nullable=False)
    turno = db.Column(db.String(2), nullable=False)  # 'AM' | 'PM'
    cerrado = db.Column(db.Boolean, default=False)
    depot_id = db.Column(db.Integer, db.ForeignKey("centros_logisticos.id"))
    creado_por = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    detalles = db.relationship("RutaDetalle", backref="ruta", cascade="all,delete-orphan", order_by="RutaDetalle.orden")

class RutaDetalle(db.Model):
    __tablename__ = "rutas_detalles"
    id = db.Column(db.Integer, primary_key=True)
    ruta_id = db.Column(db.Integer, db.ForeignKey("rutas.id", ondelete="CASCADE"))
    orden = db.Column(db.Integer, nullable=False)  # 1..N
    local_id = db.Column(db.String(64), db.ForeignKey("locales.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def seed_default_admin():
    from .database import db
    from flask import current_app
    email = Settings.DEFAULT_ADMIN_EMAIL
    pwd = Settings.DEFAULT_ADMIN_PASSWORD
    if not User.query.filter_by(email=email).first():
        u = User(email=email)
        u.set_password(pwd)
        db.session.add(u)
        db.session.commit()
