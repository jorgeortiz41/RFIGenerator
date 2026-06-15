# ============================================================
# main.py
# Leer archivos CSV del radiómetro desde una carpeta
# y seleccionar el día que se quiere usar
# ============================================================

import os
import glob
import re
import pandas as pd


# ------------------------------------------------------------
# 1. Ruta de la carpeta donde están los CSV
# ------------------------------------------------------------
CARPETA_DATOS = "src/data/datos_radiometro"


# ------------------------------------------------------------
# 2. Buscar todos los archivos CSV del radiómetro
# ------------------------------------------------------------
def buscar_archivos():
    patron = os.path.join(CARPETA_DATOS, "*_lv1.csv")
    archivos = glob.glob(patron)
    archivos.sort()
    return archivos


# ------------------------------------------------------------
# 3. Sacar la fecha del nombre del archivo
#    ejemplo:
#    2023-04-01_00-04-09_lv1.csv -> 2023-04-01
# ------------------------------------------------------------
def extraer_fecha(nombre_archivo):
    match = re.match(r"(\d{4}-\d{2}-\d{2})_", nombre_archivo)
    if match:
        return match.group(1)
    return nombre_archivo


# ------------------------------------------------------------
# 4. Crear diccionario: fecha -> ruta del archivo
# ------------------------------------------------------------
def construir_biblioteca():
    archivos = buscar_archivos()
    biblioteca = {}

    for ruta in archivos:
        nombre = os.path.basename(ruta)
        fecha = extraer_fecha(nombre)
        biblioteca[fecha] = ruta

    return biblioteca


# ------------------------------------------------------------
# 5. Mostrar días disponibles
# ------------------------------------------------------------
def mostrar_fechas(biblioteca):
    print("\nDías disponibles:")
    fechas = list(biblioteca.keys())

    for i, fecha in enumerate(fechas, start=1):
        print(f"{i}. {fecha}")

    return fechas


# ------------------------------------------------------------
# 6. Detectar encabezado correcto en los CSV del radiómetro
#    Busca la línea: Record,Date/Time,50,...
# ------------------------------------------------------------
def obtener_header_real(ruta):
    with open(ruta, "r", encoding="utf-8", errors="replace") as f:
        lineas = f.readlines()

    for linea in lineas:
        if linea.startswith("Record,Date/Time,50,"):
            return [x.strip() for x in linea.strip().split(",")]

    return None


# ------------------------------------------------------------
# 7. Detectar dónde empieza la data numérica real
# ------------------------------------------------------------
def detectar_inicio_datos(ruta):
    with open(ruta, "r", encoding="utf-8", errors="replace") as f:
        lineas = f.readlines()

    for i, linea in enumerate(lineas):
        texto = linea.strip()
        if texto and texto[0].isdigit():
            return i

    return None


# ------------------------------------------------------------
# 8. Cargar el CSV seleccionado sin error
# ------------------------------------------------------------
def cargar_csv_radiometro(ruta):
    header = obtener_header_real(ruta)
    inicio = detectar_inicio_datos(ruta)

    if header is None:
        raise ValueError("No se encontró el encabezado correcto en el archivo.")

    if inicio is None:
        raise ValueError("No se encontró el inicio de la data en el archivo.")

    df = pd.read_csv(
        ruta,
        skiprows=inicio,
        header=None,
        names=header
    )

    df = df.dropna()
    
    # Keep only columns up to 'Ch  30.000'
    if 'Ch  30.000' in df.columns:
        cutoff_idx = df.columns.get_loc('Ch  30.000')
        df = df.iloc[:, :cutoff_idx + 1]

    return df


# ------------------------------------------------------------
# 9. Programa principal
# ------------------------------------------------------------
def main():
    biblioteca = construir_biblioteca()

    if not biblioteca:
        print("No se encontraron archivos CSV en la carpeta datos_radiometro.")
        return

    fechas = mostrar_fechas(biblioteca)

    try:
        opcion = int(input("\nSelecciona el número del día que quieres cargar: "))
        fecha_seleccionada = fechas[opcion - 1]
    except (ValueError, IndexError):
        print("Selección no válida.")
        return

    ruta_archivo = biblioteca[fecha_seleccionada]

    print(f"\nArchivo seleccionado: {ruta_archivo}")

    try:
        df = cargar_csv_radiometro(ruta_archivo)
        df.to_csv(f"src/data/datos_radiometro_procesados/{fecha_seleccionada}.csv", index=False)
    except Exception as e:
        print(f"\nError al leer el archivo: {e}")
        return

    print("\nData cargada correctamente.")
    print(df.head())
    print("\nColumnas:")
    print(df.columns.tolist())


# ------------------------------------------------------------
# Ejecutar
# ------------------------------------------------------------
if __name__ == "__main__":
    main()