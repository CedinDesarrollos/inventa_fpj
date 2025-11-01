import io
import pandas as pd
from ...models import Ruta, RutaDetalle, Local

def build_excel_bytes(rutas: list[Ruta]) -> io.BytesIO:
    rows = []
    for r in rutas:
        for det in r.detalles:
            loc = Local.query.get(det.local_id)
            rows.append({
                "Fecha": r.fecha.isoformat(),
                "Turno": r.turno,
                "N° Parada": det.orden,
                "ID Sucursal": det.local_id,
                "Nombre Sucursal": loc.name if loc else "",
                "Lat": loc.lat if loc else "",
                "Lon": loc.lon if loc else ""
            })
    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=["Fecha","Turno","N° Parada","ID Sucursal","Nombre Sucursal","Lat","Lon"])
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        df.to_excel(xw, index=False, sheet_name="Ruteo")
    buf.seek(0)
    return buf
