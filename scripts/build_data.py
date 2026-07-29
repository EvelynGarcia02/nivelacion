"""
Regenera js/data.js a partir de data/curso_nivelacion_2S2026.csv.

Uso:
    python scripts/build_data.py

Requiere: pandas (pip install pandas)

Lee el CSV de resultados de Nivelacion (nivel estudiante-curso) y escribe
un unico archivo JS con "const DATA = {...};" que el dashboard carga
directamente (sin fetch, para que funcione abriendo index.html sin
necesidad de un servidor local).

Metodologia verificada contra el Informe Tecnico ITI-DIPA-NVERAV-2026-004
(y el dashboard institucional del que parte ese informe):
  - COUNT(DISTINCT cedula) trata las cedulas vacias/nulas como UN solo
    valor compartido (no como NULL ignorado ni como estudiantes distintos).
    Con esa regla se reproduce exactamente 13.266 inscritos / 11.299
    rindieron / 1.967 sin ninguna rendicion / 39.184 matriculas-curso que
    reporta el informe oficial.
"""
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "data" / "curso_nivelacion_2S2026.csv"
OUT = ROOT / "js" / "data.js"

LOWER_WORDS = {"de", "del", "la", "las", "el", "los", "y", "en", "a", "al", "con", "por", "para"}

# El CSV fuente trae tildes inconsistentes/perdidas en "carrera" y "asignatura"
# (p.ej. "ADMINISTRACION", "FISICA" sin tilde). Se corrige con la ortografia
# oficial tal como aparece en el Informe Tecnico ITI-DIPA-NVERAV-2026-004,
# para que las etiquetas del dashboard sean presentables. La clave es la
# version sin tildes en mayusculas (norm_key) para que el match sea robusto
# sin importar como haya llegado la tilde en el CSV.
_REPORT_CARRERAS = [
    "Licenciatura en Fisioterapia", "Licenciatura en Nutrición y Dietética",
    "Licenciatura en Enfermería", "Ingeniería Ambiental",
    "Licenciatura en Pedagogía de la Actividad Física y Deporte", "Ingeniería Industrial",
    "Tecnologías de la Información en Línea", "Ingeniería Civil", "Software",
    "Ingeniería en Software", "Ingeniería en Alimentos", "Educación",
    "Licenciatura en Turismo", "Psicología Clínica", "Educación Inicial en Línea",
    "Trabajo Social", "Licenciatura en Educación Inicial", "Administración de Empresas",
    "Licenciatura en Contabilidad y Auditoría", "Economía en Línea", "Trabajo Social en Línea",
    "Ingeniería en Biotecnología", "Educación Especial", "Turismo en Línea",
    "Pedagogía de las Ciencias Experimentales", "Agronegocios", "Arquitectura Sostenible",
    "Economía", "Administración de Empresas en Línea",
    "Pedagogía de los Idiomas Nacionales y Extranjeros en Línea",
    "Pedagogía de la Lengua y la Literatura", "Educación Básica en Línea", "Derecho en Línea",
    "Licenciatura en Pedagogía de los Idiomas Nacionales y Extranjeros",
    "Licenciatura en Comunicación", "Multimedia y Producción Audiovisual",
    "Comunicación en Línea", "Medicina",
]
_REPORT_ASIGNATURAS = [
    "Anatomía", "Física", "Neuroanatomía", "Matemáticas", "Química",
    "Introducción a la Pedagogía de la Actividad Física y Deporte",
    "Fisiología del Sistema Nervioso", "Biología", "Introducción a la Contabilidad",
    "Teoría de la Arquitectura Sostenible", "Introducción a la Educación Inicial",
    "Introducción a la Pedagogía de las Ciencias Experimentales", "Sociedad y Cultura",
    "Inglés", "Epistemología del Turismo", "Pensamiento Computacional",
    "Fundamentos del Análisis Económico", "Derecho Romano",
    "Prototipado Visual y Composición", "Comunicación y Lenguaje Académico",
    "Fundamentos de la Comunicación Digital", "Introducción a la Educación Especial",
    "Introducción a la Educación Básica", "Introducción a la Administración",
    "Lenguaje, Lectura Crítica y Escritura Académica",
    "Arquitectura de Contenidos y Narrativa Transmedia", "Bioquímica",
]


def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def norm_key(s):
    """Clave de normalizacion para deduplicar variantes con/sin tilde."""
    return " ".join(strip_accents(s).upper().split())


def title_es(s):
    s = " ".join(s.split())
    words = s.split(" ")
    out = []
    for i, w in enumerate(words):
        wl = w.lower()
        if i > 0 and wl in LOWER_WORDS:
            out.append(wl)
        else:
            # capitaliza preservando tildes/enies (str.capitalize funciona bien con unicode)
            out.append(wl.capitalize())
    return " ".join(out)


CARRERA_FIX = {norm_key(name): name for name in _REPORT_CARRERAS}
ASIGNATURA_FIX = {norm_key(name): name for name in _REPORT_ASIGNATURAS}


def carrera_label(raw):
    """'Nivelacion Licenciatura en Fisioterapia' (texto original, con tildes
    inconsistentes) -> 'Licenciatura en Fisioterapia' (ortografia oficial del
    informe si esta en CARRERA_FIX; si no, mejor esfuerzo sobre el texto crudo)."""
    upper_noaccent = strip_accents(raw).upper()
    if upper_noaccent.startswith("NIVELACION "):
        raw = raw[len("NIVELACION "):]
        upper_noaccent = upper_noaccent[len("NIVELACION "):]
    fixed = CARRERA_FIX.get(" ".join(upper_noaccent.split()))
    return fixed if fixed else title_es(raw)


def asignatura_label(raw):
    fixed = ASIGNATURA_FIX.get(norm_key(raw))
    return fixed if fixed else title_es(raw)


def docente_label(raw):
    return title_es(raw)


AREA_RULES = [
    (["ENFERMERIA", "FISIOTERAPIA", "NUTRICION", "MEDICINA", "PSICOLOGIA CLINICA"], "Salud y Servicios Sociales"),
    (["TRABAJO SOCIAL"], "Ciencias Sociales y Trabajo Social"),
    (["EDUCACION", "PEDAGOGIA"], "Educacion y Pedagogia"),
    (["INGENIERIA", "SOFTWARE", "TECNOLOGIAS DE LA INFORMACION", "ARQUITECTURA"], "Ingenieria y Tecnologia"),
    (["ADMINISTRACION", "CONTABILIDAD", "ECONOMIA", "AGRONEGOCIOS"], "Administrativas, Economicas y Agropecuarias"),
    (["COMUNICACION", "MULTIMEDIA"], "Comunicacion y Arte"),
    (["DERECHO"], "Juridica"),
    (["TURISMO"], "Turismo"),
]


def area_for(norm_carrera):
    for keywords, area in AREA_RULES:
        if any(k in norm_carrera for k in keywords):
            return area
    return "Otras"


def r1(x):
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    return round(float(x) + 1e-9, 1)


def main():
    df = pd.read_csv(CSV, encoding="utf-8-sig")

    # --- normalizacion de texto: fija tildes inconsistentes (mojibake) y
    # fusiona variantes de una misma carrera (p.ej. "NIVELACION EDUCACION"
    # vs "NIVELACION EDUCACI\xd3N") bajo una unica clave/etiqueta ---
    df["carrera_key"] = df["carrera"].apply(norm_key)
    df["asignatura_key"] = df["asignatura"].apply(norm_key)
    df["docente_key"] = df["docente"].apply(lambda s: " ".join(str(s).split()))

    # cedula: '' comparte un unico bucket para las 52 filas sin cedula,
    # replicando la metodologia del dashboard institucional (ver docstring)
    cedula_str = df["cedula"].apply(lambda v: "" if pd.isna(v) else str(int(v)))
    student_ids = {}
    student_idx = []
    for c in cedula_str:
        if c not in student_ids:
            student_ids[c] = len(student_ids)
        student_idx.append(student_ids[c])
    df["student_idx"] = student_idx

    # --- diccionarios ---
    carrera_keys = sorted(df["carrera_key"].unique())
    carrera_index = {k: i for i, k in enumerate(carrera_keys)}
    carrera_dict = [carrera_label(df.loc[df["carrera_key"] == k, "carrera"].iloc[0]) for k in carrera_keys]
    carrera_modalidad = []
    for k in carrera_keys:
        raw_mod = strip_accents(df.loc[df["carrera_key"] == k, "modalidad"].iloc[0]).upper()
        if raw_mod == "EN LINEA":
            carrera_modalidad.append("En línea")
        elif raw_mod == "SEMIPRESENCIAL":
            carrera_modalidad.append("Semipresencial")
        else:
            carrera_modalidad.append("Presencial")
    carrera_area = [area_for(k) for k in carrera_keys]

    asignatura_keys = sorted(df["asignatura_key"].unique())
    asignatura_index = {k: i for i, k in enumerate(asignatura_keys)}
    asignatura_dict = [asignatura_label(df.loc[df["asignatura_key"] == k, "asignatura"].iloc[0]) for k in asignatura_keys]

    docente_keys = sorted(df["docente_key"].unique())
    docente_index = {k: i for i, k in enumerate(docente_keys)}
    docente_dict = [docente_label(k) for k in docente_keys]

    ESTADO = ["APROBADO", "REPROBADO", "NO REALIZO EXAMEN FINAL"]
    estado_index = {v: i for i, v in enumerate(ESTADO)}
    estado_dict = ["Aprobado", "Reprobado", "No realizó examen"]

    HORARIO = ["Dentro de horario", "Fuera de horario", "No aplica"]
    horario_index = {v: i for i, v in enumerate(HORARIO)}
    horario_dict = ["Dentro de horario", "Fuera de horario", "No aplica"]

    df["examen_final_num"] = pd.to_numeric(df["examen_final"], errors="coerce")

    rows = []
    for r in df.itertuples(index=False):
        c_idx = carrera_index[r.carrera_key]
        a_idx = asignatura_index[r.asignatura_key]
        d_idx = docente_index[r.docente_key]
        e_idx = estado_index[r.estado_academico]
        h_idx = horario_index[r.cumplimiento_horario]
        test_prom = r1((r.test1 + r.test2 + r.test3 + r.test4) / 4.0)
        examen = r1(r.examen_final_num) if pd.notna(r.examen_final_num) else None
        nota = r1(r.nota_final)
        rows.append([r.student_idx, c_idx, a_idx, d_idx, e_idx, h_idx, nota, test_prom, examen])

    data = {
        "meta": {
            "generated": pd.Timestamp.now().strftime("%Y-%m-%d"),
            "totalRows": len(rows),
            "totalStudents": len(student_ids),
        },
        "dict": {
            "carrera": carrera_dict,
            "carreraModalidad": carrera_modalidad,
            "carreraArea": carrera_area,
            "asignatura": asignatura_dict,
            "docente": docente_dict,
            "estado": estado_dict,
            "horario": horario_dict,
        },
        # fila: [studentIdx, carreraIdx, asignaturaIdx, docenteIdx, estadoIdx, horarioIdx, notaFinal, testProm, examenFinal]
        "rows": rows,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("const DATA = ")
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")

    print(f"Escrito {OUT}")
    print(f"  {len(rows)} filas estudiante-curso, {len(student_ids)} estudiantes (incl. bucket sin cedula)")
    print(f"  {len(carrera_dict)} carreras, {len(asignatura_dict)} asignaturas, {len(docente_dict)} docentes")
    areas = Counter(carrera_area)
    for a, n in areas.most_common():
        print(f"    area '{a}': {n} carreras")


if __name__ == "__main__":
    main()
