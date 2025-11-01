from decimal import Decimal, InvalidOperation
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from . import abm_locales_bp
from ...database import db
from ...models import Local
from config import Settings
import re

# ---------- Helpers ----------
def _slugify(s: str) -> str:
    s = (s or "").strip().lower()
    # quitar acentos
    s = (s.encode('ascii', 'ignore')).decode('ascii')
    # permitir solo a-z, 0-9, espacio, guion y underscore
    s = re.sub(r'[^a-z0-9\s_-]', '', s)
    # espacios a underscore y compactar múltiples
    s = re.sub(r'\s+', '_', s)
    s = re.sub(r'_+', '_', s)
    return s.strip('_')

def _unique_local_id(base_name: str) -> str:
    base = f"agromax_{_slugify(base_name)}" or "agromax_local"
    # si ya existe, agregar sufijos -1, -2, ...
    candidate = base
    i = 1
    while Local.query.get(candidate) is not None:
        candidate = f"{base}-{i}"
        i += 1
    return candidate

def _to_float(v, default=None):
    try:
        return float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return default

def _to_int(v, default=None):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default

def _to_decimal(v, default=Decimal("0")):
    try:
        # Acepta "1.234,56" y "1234.56"
        s = str(v).strip().replace(".", "").replace(",", ".")
        return Decimal(s)
    except (InvalidOperation, AttributeError):
        return default
    
# ---------- Rutas ----------

@abm_locales_bp.route("/")
@login_required
def list_locales():
    q = Local.query.filter_by(company_slug=Settings.PROJECT_SLUG).order_by(Local.name.asc())
    items = q.all()
    return render_template("abm_locales/list.html", items=items)

@abm_locales_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    # rank sugerido
    max_rank = db.session.query(func.max(Local.rank)).scalar() or 0
    next_rank = max_rank + 1

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        city = (request.form.get("city") or "").strip() or None
        lat = _to_float(request.form.get("lat"))
        lon = _to_float(request.form.get("lon"))
        # si no viene rank, usar el siguiente disponible
        rank = _to_int(request.form.get("rank"), default=next_rank)
        venta_por_dia = _to_decimal(request.form.get("venta_por_dia"), default=Decimal("0"))

        # Validación mínima
        if not name or lat is None or lon is None:
            flash("Nombre, Lat y Lon son obligatorios.", "danger")
            # reenviar lo que tipeó el usuario en un 'item' temporal
            temp_item = type("Tmp", (), dict(
                id=None, name=name, city=city, lat=lat, lon=lon, rank=rank, venta_por_dia=venta_por_dia, active=True
            ))()
            return render_template("abm_locales/edit.html", item=temp_item, next_rank=next_rank)

        # id autogenerado a partir del nombre (y asegurar unicidad)
        id_ = _unique_local_id(name)

        try:
            l = Local(
                id=id_,
                name=name,
                city=city,
                lat=lat,
                lon=lon,
                rank=rank,
                venta_por_dia=venta_por_dia,
                active=True,
            )
            db.session.add(l)
            db.session.commit()
            flash("Local creado correctamente.", "success")
            return redirect(url_for("abm_locales.list_locales"))
        except IntegrityError:
            db.session.rollback()
            flash("No se pudo crear el local (ID duplicado). Intentá nuevamente.", "danger")
            temp_item = type("Tmp", (), dict(
                id=None, name=name, city=city, lat=lat, lon=lon, rank=rank, venta_por_dia=venta_por_dia, active=True
            ))()
            return render_template("abm_locales/edit.html", item=temp_item, next_rank=next_rank)

    # GET
    return render_template("abm_locales/edit.html", item=None, next_rank=next_rank)

@abm_locales_bp.route("/editar/<id>", methods=["GET", "POST"])
@login_required
def editar(id):
    item = Local.query.get_or_404(id)

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        city = (request.form.get("city") or "").strip() or None
        lat = _to_float(request.form.get("lat"))
        lon = _to_float(request.form.get("lon"))
        rank = _to_int(request.form.get("rank"), default=item.rank)
        venta_por_dia = _to_decimal(request.form.get("venta_por_dia"), default=Decimal("0"))
        active = bool(request.form.get("active"))

        if not name or lat is None or lon is None:
            flash("Nombre, Lat y Lon son obligatorios.", "danger")
            # re-render con lo actualizado por el usuario
            item.name = name
            item.city = city
            item.lat = lat if lat is not None else item.lat
            item.lon = lon if lon is not None else item.lon
            item.rank = rank
            item.venta_por_dia = venta_por_dia
            item.active = active
            return render_template("abm_locales/edit.html", item=item)

        item.name = name
        item.city = city
        item.lat = lat
        item.lon = lon
        item.rank = rank
        item.venta_por_dia = venta_por_dia
        item.active = active

        db.session.commit()
        flash("Local actualizado.", "success")
        return redirect(url_for("abm_locales.list_locales"))

    return render_template("abm_locales/edit.html", item=item)

@abm_locales_bp.route("/eliminar/<id>", methods=["POST"])
@login_required
def eliminar(id):
    item = Local.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash("Local eliminado.", "success")
    return redirect(url_for("abm_locales.list_locales"))
