# scripts/preprocess_layers_advanced.py
import os, zipfile, tempfile, json, gzip
from pathlib import Path
import geopandas as gpd
from shapely.errors import TopologicalError
from shapely.geometry import Polygon, MultiPolygon, Point
from shapely import set_precision

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
OUT_DIR  = BASE_DIR / "build"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def _to_wgs84(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=4326)
    elif gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)
    return gdf

def _clean_topology(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    try:
        gdf["geometry"] = gdf["geometry"].buffer(0)
    except TopologicalError:
        pass
    return gdf

def _remove_small_holes_and_parts(geom, hole_area_min=1e-10, part_area_min=1e-10):
    # área en grados^2; ajusta si hace falta (≈ metros dependen de lat)
    if geom is None or geom.is_empty:
        return geom
    def _filter_poly(poly: Polygon):
        if poly.is_empty:
            return poly
        # remover agujeros pequeños
        outs = [ring for ring in poly.interiors if Polygon(ring).area >= hole_area_min]
        p = Polygon(poly.exterior, outs)
        return p if p.area >= part_area_min else None

    if isinstance(geom, Polygon):
        return _filter_poly(geom)
    if isinstance(geom, MultiPolygon):
        parts = [p for p in ( _filter_poly(pg) for pg in geom.geoms ) if p]
        if not parts:
            return None
        return MultiPolygon(parts)
    return geom

def _reduce_precision(gdf: gpd.GeoDataFrame, grid=1e-6) -> gpd.GeoDataFrame:
    # 1e-6 ≈ 0.11 m; 1e-5 ≈ 1.1 m; 1e-4 ≈ 11 m
    gdf["geometry"] = gdf["geometry"].apply(lambda g: set_precision(g, grid))
    return gdf

def _dedupe_points_by_grid(gdf: gpd.GeoDataFrame, grid=1e-5) -> gpd.GeoDataFrame:
    def snap(pt: Point):
        return round(pt.y / grid) * grid, round(pt.x / grid) * grid
    if not isinstance(gdf.geometry.iloc[0], Point):
        return gdf
    gdf = gdf.assign(_snap=gdf.geometry.apply(snap))
    gdf = gdf.drop_duplicates(subset=["_snap"])
    gdf = gdf.drop(columns=["_snap"])
    return gdf

def convert_zip(
    zip_path: Path,
    name: str,
    *,
    keep_columns: list[str] | None = None,
    simplify_tol: float = 0.0006,
    precision_grid: float = 1e-6,
    hole_area_min: float = 0.0,
    part_area_min: float = 0.0,
    is_points: bool = False,
    dedupe_grid: float = 1e-5,
    gzip_output: bool = True
):
    print(f"Procesando {zip_path.name}…")
    with tempfile.TemporaryDirectory() as td:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(td)
        shp_files = list(Path(td).rglob("*.shp"))
        if not shp_files:
            raise FileNotFoundError(f"No se encontró .shp en {zip_path}")
        gdf = gpd.read_file(shp_files[0])

    gdf = _to_wgs84(gdf)
    gdf = _clean_topology(gdf)

    # 1) columnas
    if keep_columns:
        keep = [c for c in keep_columns if c in gdf.columns] + ["geometry"]
        gdf = gdf[keep]

    # 2) precisión de coordenadas (reduce decimales → menos tamaño)
    gdf = _reduce_precision(gdf, grid=precision_grid)

    # 3) limpiar agujeros/partes minúsculas (polígonos)
    if not is_points and (hole_area_min > 0 or part_area_min > 0):
        gdf["geometry"] = gdf["geometry"].apply(
            lambda g: _remove_small_holes_and_parts(g, hole_area_min, part_area_min)
        )
        gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty]

    # 4) simplificar (para polígonos/líneas)
    if not is_points and simplify_tol > 0:
        gdf["geometry"] = gdf["geometry"].simplify(simplify_tol, preserve_topology=True)

    # 5) dedupe por grilla (para puntos densos)
    if is_points:
        gdf = _dedupe_points_by_grid(gdf, grid=dedupe_grid)

    # FULL (por si querés guardar una versión de referencia)
    full_path = OUT_DIR / f"{name}.full.geojson"
    gdf.to_file(full_path, driver="GeoJSON")

    # LITE
    lite_path = OUT_DIR / f"{name}.lite.geojson"
    gdf.to_file(lite_path, driver="GeoJSON")

    # 6) (opcional) GZIP para subir y servir más chico
    if gzip_output:
        gz_path = OUT_DIR / f"{name}.lite.geojson.gz"
        with open(lite_path, "rb") as fin, gzip.open(gz_path, "wb", compresslevel=9) as fout:
            fout.write(fin.read())
        print(f"✅ {lite_path.name} y {gz_path.name} generados.")
    else:
        print(f"✅ {lite_path.name} generado.")

if __name__ == "__main__":
    # MANZANAS (polígonos MUY densos)
    # - dejamos 3–5 campos clave (ajustá nombres reales si difieren)
    convert_zip(
        DATA_DIR / "Manzanas_Paraguay_INE_20221.zip",
        "manzanas",
        keep_columns=["COD_DEP", "COD_DIST", "COD_MANZ", "NOM_DIST", "NOM_DEP"],
        simplify_tol=0.0010,       # más agresivo que antes
        precision_grid=1e-5,       # ~1.1 m de grilla
        hole_area_min=1e-9,        # limpia agujeros tiny
        part_area_min=1e-9,
        is_points=False,
        gzip_output=True
    )

    # UNIDADES ECONÓMICAS (puntos MUY numerosos)
    convert_zip(
        DATA_DIR / "UNIDADES_ECONOMICAS_PY_2022.zip",
        "unidades_economicas",
        keep_columns=["NOMBRE", "RUBRO", "CATEGORIA", "DISTRITO", "DEPTO"],  # ajustá a tus campos disponibles
        simplify_tol=0.0,
        precision_grid=1e-5,   # ~1.1 m
        is_points=True,
        dedupe_grid=1e-5,      # colapsa puntos superpuestos/casi idénticos
        gzip_output=True
    )
