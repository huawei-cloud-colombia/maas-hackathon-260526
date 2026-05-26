import pandas as pd
from datetime import datetime
from io import StringIO
from config import BECAS_REQUIRED_COLS, ESTUDIANTES_REQUIRED_COLS


def validate_columns(df, required_cols, source_name):
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"{source_name}: columnas faltantes: {', '.join(missing)}")


def parse_date(date_str):
    if pd.isna(date_str) or str(date_str).strip() == "":
        return None
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(str(date_str).strip(), fmt)
        except ValueError:
            continue
    return None


def parse_idioma(idioma_str):
    if pd.isna(idioma_str) or str(idioma_str).strip() == "":
        return []
    result = []
    for part in str(idioma_str).split(";"):
        part = part.strip()
        if "-" in part:
            lang, level = part.rsplit("-", 1)
            result.append({"idioma": lang.strip(), "nivel": level.strip().upper()})
        else:
            result.append({"idioma": part.strip(), "nivel": None})
    return result


def parse_carreras(carreras_str):
    if pd.isna(carreras_str) or str(carreras_str).strip() == "":
        return []
    return [c.strip() for c in str(carreras_str).split(";") if c.strip()]


def load_becas(csv_input):
    if isinstance(csv_input, str) and "\n" in csv_input:
        df = pd.read_csv(StringIO(csv_input))
    else:
        df = pd.read_csv(csv_input)
    validate_columns(df, BECAS_REQUIRED_COLS, "becas.csv")
    df["monto"] = pd.to_numeric(df["monto"], errors="coerce")
    df["gpa_minimo"] = pd.to_numeric(df["gpa_minimo"], errors="coerce")
    df["carreras_lista"] = df["carreras_aceptadas"].apply(parse_carreras)
    idioma_parsed = df["idioma_requerido"].apply(parse_idioma)
    df["idioma_req_lang"] = idioma_parsed.apply(lambda x: x[0]["idioma"] if x else None)
    df["idioma_req_nivel"] = idioma_parsed.apply(lambda x: x[0]["nivel"] if x else None)
    df["fecha_cierre_dt"] = df["fecha_cierre"].apply(parse_date)
    df["requiere_carta_bool"] = df["requiere_carta"].astype(str).str.strip().str.lower().isin(["si", "yes", "true", "1"])
    df["situacion_ec_norm"] = df["situacion_ec"].astype(str).str.strip().str.lower()
    df.loc[df["situacion_ec_norm"] == "nan", "situacion_ec_norm"] = ""
    return df


def load_estudiantes(csv_input):
    if isinstance(csv_input, str) and "\n" in csv_input:
        df = pd.read_csv(StringIO(csv_input))
    else:
        df = pd.read_csv(csv_input)
    validate_columns(df, ESTUDIANTES_REQUIRED_COLS, "estudiantes.csv")
    df["gpa"] = pd.to_numeric(df["gpa"], errors="coerce")
    df["idiomas_lista"] = df["idiomas"].apply(parse_idioma)
    df["situacion_ec_norm"] = df["situacion_economica"].astype(str).str.strip().str.lower()
    df.loc[df["situacion_ec_norm"] == "nan", "situacion_ec_norm"] = ""
    return df
