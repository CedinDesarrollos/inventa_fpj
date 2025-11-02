# scripts/preprocess_layers.py
import os
import zipfile
import tempfile
from pathlib import Path
import geopandas as gpd
from shapely.errors import TopologicalError

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
OUT_DIR = BASE_DIR / "build"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def convert_zip(zip_path: Path, name: str, simplify: float = 0.0006):
    print(f"Procesando {zip_path.name}...")
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(tmpdir)

        shp_files = list(Path(tmpdir).rglob("*.shp"))
        if not shp_files:
            raise FileNotFoundError(f"No se encontró shapefile en {zip_path}")
        shp = shp_files[0]

        gdf = gpd.read_file(shp)

        # Asegurar CRS WGS84 (EPSG:4326)
        if gdf.crs is None:
            gdf.set_crs(epsg=4326, inplace=True)
        elif gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(epsg=4326)

        # Corregir geometrías inválidas
        try:
            gdf["geometry"] = gdf["geometry"].buffer(0)
        except TopologicalError:
            pass

        # Versión completa
        full = OUT_DIR / f"{name}.full.geojson"
        gdf.to_file(full, driver="GeoJSON")

        # Versión liviana (simplificada)
        gdf_simpl = gdf.copy()
        gdf_simpl["geometry"] = gdf_simpl["geometry"].simplify(simplify, preserve_topology=True)
        lite = OUT_DIR / f"{name}.lite.geojson"
        gdf_simpl.to_file(lite, driver="GeoJSON")

        print(f"  ✅ {full.name} y {lite.name} generados.")

if __name__ == "__main__":
    #convert_zip(DATA_DIR / "Departamentos_Paraguay_INE_2022.zip", "departamentos", 0.0012)
    #convert_zip(DATA_DIR / "Distritos_Paraguay_INE_2022.zip", "distritos", 0.0009)
    #convert_zip(DATA_DIR / "Manzanas_Paraguay_INE_20221.zip", "manzanas", 0.0006)
    #convert_zip(DATA_DIR / "UNIDADES_ECONOMICAS_PY_2022.zip", "unidades_economicas", 0.0)
    #convert_zip(DATA_DIR / "BARLOC_2025.zip", "barloc_2025", 0.0008)
