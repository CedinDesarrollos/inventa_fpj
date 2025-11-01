from datetime import date, timedelta
from flask import jsonify, render_template, request, send_file
from flask_login import login_required, current_user
from sqlalchemy import select
from . import ruteo_bp
from ...database import db
from ...models import Depot, Local, Ruta, RutaDetalle
from ...utils.ruteo.excel import build_excel_bytes
from config import Settings

def week_days(d=None):
    d = d or date.today()
    # Lunes a Sábado (como tu UI)
    monday = d - timedelta(days=(d.weekday() % 7))
    days = [monday + timedelta(days=i) for i in range(6)]
    out = {}
    for di in days:
        out[di.isoformat()] = {"weekday": ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"][di.weekday()]}
    return out

@ruteo_bp.route("/mapa")
@login_required
def mapa():
    return render_template("ruteo/mapa.html", project_name=Settings.PROJECT_NAME)

@ruteo_bp.route("/map-data")
@login_required
def map_data():
    company = Settings.PROJECT_SLUG
    depot = Depot.query.filter_by(company_slug=company, active=True).first()
    all_loc = Local.query.filter_by(company_slug=company, active=True).all()

    resp = {
        "depot": ({"name": depot.name, "lat": depot.lat, "lon": depot.lon} if depot else None),
        "all_stores": [{
            "id": l.id, "name": l.name, "city": l.city,
            "lat": float(l.lat), "lon": float(l.lon),
            "rank": l.rank, "venta_por_dia": float(l.venta_por_dia or 0)
        } for l in all_loc],
        "days": week_days()
    }
    return jsonify(resp)

@ruteo_bp.route("/guardar", methods=["POST"])
@login_required
def guardar():
    """
    Espera JSON:
    {
      "fecha": "YYYY-MM-DD",
      "turno": "AM"|"PM",
      "cerrado": true|false,
      "depot_id": <id opcional>,
      "paradas": ["local_id1","local_id2", ...]
    }
    """
    data = request.get_json() or {}
    fecha = data.get("fecha")
    turno = data.get("turno","AM")
    cerrado = bool(data.get("cerrado", False))
    depot_id = data.get("depot_id")
    paradas = data.get("paradas") or []

    ruta = Ruta.query.filter_by(company_slug=Settings.PROJECT_SLUG, fecha=fecha, turno=turno).first()
    if not ruta:
        ruta = Ruta(company_slug=Settings.PROJECT_SLUG, fecha=fecha, turno=turno, creado_por=current_user.id)
        db.session.add(ruta)

    ruta.cerrado = cerrado
    if depot_id:
        ruta.depot_id = depot_id

    # limpiar detalles previos
    RutaDetalle.query.filter_by(ruta_id=ruta.id).delete() if ruta.id else None
    db.session.flush()

    for i, local_id in enumerate(paradas, start=1):
        db.session.add(RutaDetalle(ruta=ruta, orden=i, local_id=str(local_id)))

    db.session.commit()
    return jsonify({"ok": True, "ruta_id": ruta.id})

@ruteo_bp.route("/exportar")
@login_required
def exportar():
    """
    Exporta todas las rutas guardadas (AM/PM) de la semana actual.
    """
    days = list(week_days().keys())
    rutas = (
        db.session.query(Ruta)
        .filter(Ruta.company_slug==Settings.PROJECT_SLUG, Ruta.fecha.in_(days))
        .order_by(Ruta.fecha.asc(), Ruta.turno.asc())
        .all()
    )
    buf = build_excel_bytes(rutas)
    return send_file(buf, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                     as_attachment=True, download_name="ruteo_semana.xlsx")
